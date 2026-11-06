"""Live LM Studio pilot on one document using application extraction and ensemble functions.

Run from the repository root with services/ai/.venv/bin/python.
Uses an isolated in-memory cosine index in place of Postgres/MinIO/Go;
no authorization, persistence, or full-stack correctness is inferred.
"""
from __future__ import annotations
import argparse
import asyncio
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'services/ai'))
from app import models_client, multi_model
from app.config import settings
from app.extraction import extract_segments, chunk_text, CHUNK_SIZE, CHUNK_OVERLAP
from app.orchestration.executor import focus_evidence


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cosine(a, b):
    denom = math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    return sum(x*y for x, y in zip(a, b, strict=True)) / denom if denom else 0.0


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--document', default='Research_Paper.pdf')
    parser.add_argument('--out', default='tests/evaluation/results/lmstudio-document-2026-11-03')
    args = parser.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    document = ROOT / args.document
    dataset_path = ROOT / 'tests/evaluation/document_pilot/questions.json'
    questions = json.loads(dataset_path.read_text())
    models = ['eval-minicpm5-1b', 'eval-gemma4-e4b']
    settings.ai_base_url = 'http://127.0.0.1:1234/v1'
    settings.ai_model = models[1]
    settings.ai_verifier_model = models[1]
    settings.ai_embedding_model = 'eval-nomic'
    settings.ai_reasoning_effort = 'none'
    settings.ai_allow_cloud = False

    # Preserve exact local HTTP requests/responses, excluding headers and credentials.
    original_client = models_client._local_client
    async def capture(response):
        await response.aread()
        body = json.loads(response.request.content)
        data = response.json()
        if response.request.url.path.endswith('/embeddings'):
            data = {'embedding_count': len(data.get('data', [])), 'usage': data.get('usage')}
        record = {'timestamp': datetime.now().astimezone().isoformat(), 'url': str(response.request.url), 'status': response.status_code, 'request': body, 'response': data}
        with (out / 'http_calls.jsonl').open('a') as f:
            f.write(json.dumps(record) + '\n')
    def recording_client(timeout=60.0):
        client = original_client(timeout)
        client.event_hooks['response'].append(capture)
        return client
    models_client._local_client = recording_client

    metadata = json.loads(subprocess.check_output(['lms', 'ps', '--json'], text=True))
    inventory = json.loads(subprocess.check_output(['lms', 'ls', '--json'], text=True))
    source_paths = ['services/ai/app/multi_model.py', 'services/ai/app/models_client.py', 'services/ai/app/grounding/verifier.py', 'services/ai/app/extraction.py', 'services/ai/app/orchestration/executor.py']
    manifest = {
        'started_at': datetime.now().astimezone().isoformat(), 'document': args.document,
        'document_sha256': sha(document.read_bytes()), 'questions_sha256': sha(dataset_path.read_bytes()),
        'question_count': len(questions), 'dataset_created_before_generation': True,
        'model_inventory': inventory, 'loaded_models': metadata,
        'hardware': {'platform': platform.platform(), 'machine': platform.machine(), 'memory_bytes': int(subprocess.check_output(['sysctl','-n','hw.memsize']))},
        'lms_version': subprocess.check_output(['lms','--version'], text=True).strip(),
        'settings': {'generator_models': models, 'synthesizer': models[1], 'verifier': models[1], 'embedding_model': 'eval-nomic', 'temperature': 0.3, 'reasoning_effort': 'none', 'verifier_reasoning_effort': 'low', 'generator_max_tokens': 800, 'synthesis_max_tokens': 900, 'verifier_max_tokens': 2000, 'context_length': 8192, 'chunk_size_chars': CHUNK_SIZE, 'chunk_overlap_chars': CHUNK_OVERLAP, 'retrieval_limit': 8, 'focus_keep': 3, 'focus_margin': 0.15},
        'source_hashes': {p: sha((ROOT/p).read_bytes()) for p in source_paths},
        'verification': 'Not run in the main answer-accuracy batch. The separate initial full-pipeline smoke attempt was interrupted during degenerate verification; see sibling -initial-smoke directory.',
        'scope': 'Application PDF extraction/chunking, live local embeddings, in-memory exact cosine retrieval, production evidence focusing, independent local generations, Jaccard agreement, and production synthesis. Bypasses PostgreSQL/MinIO/Go authentication, task approval and persistence. No memory is supplied. One trial per question; order fixed; response wall times share fan-out contention.',
    }
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (out/'questions.json').write_text(json.dumps(questions,indent=2))
    chunks=[]
    for location, text in extract_segments('application/pdf', document.read_bytes()):
        for content in chunk_text(text):
            i=len(chunks)
            chunks.append({'chunk_id': f'pilot-{i}', 'document_id': manifest['document_sha256'], 'filename': document.name, 'chunk_index': i, 'location': location, 'content': content})
    print(f'Extracted {len(chunks)} chunks; embedding document with live LM Studio.',flush=True)
    vectors=[]
    for offset in range(0,len(chunks),12):
        vectors.extend(await models_client.embed([c['content'] for c in chunks[offset:offset+12]]))
    if len(vectors)!=len(chunks):raise RuntimeError('Embedding count mismatch')
    (out/'index.json').write_text(json.dumps({'chunks':chunks,'vectors':vectors}))
    print(f'Embedded {len(vectors)} chunks, {len(vectors[0])} dimensions.',flush=True)
    async def retrieve(workspace_id, question, limit=8):
        if workspace_id != 'isolated-document-pilot':raise ValueError('Unexpected pilot workspace')
        q=(await models_client.embed([question]))[0]
        rows=sorted([{**c,'score':cosine(v,q)} for c,v in zip(chunks,vectors,strict=True)],key=lambda x:x['score'],reverse=True)[:limit]
        return focus_evidence(rows)
    try:
        for number, case in enumerate(questions,1):
            target=out/f"{case['id']}.json"
            if target.exists():
                print(case['id'],'already recorded; skipping',flush=True)
                continue
            started=time.monotonic()
            try:
                evidence=await retrieve('isolated-document-pilot',case['question'])
                if evidence:
                    block=multi_model.evidence_block(evidence)
                    answers=list(await asyncio.gather(*(multi_model.answer_with_model(m,block,case['question']) for m in models)))
                    for answer in answers:
                        answer.citations=multi_model.extract_citations(answer.answer,evidence)
                    combined=await multi_model.synthesize(models[1],block,case['question'],answers)
                    result=multi_model.MultiModelResult(question=case['question'],evidence=evidence,answers=answers,agreement=multi_model.agreement_matrix(answers),combined_answer=combined,synthesizer=models[1],verification={'decision':'not_run_answer_accuracy_pilot'})
                else:
                    result=multi_model.MultiModelResult(question=case['question'],evidence=[],answers=[],agreement={'pairs':[],'mean_overlap':0.0,'n_answered':0},combined_answer='No relevant evidence was found in this document.',synthesizer=models[1],verification={'decision':'not_run_answer_accuracy_pilot'})
                record={'case':case,'wall_seconds':time.monotonic()-started,'result':asdict(result)}
            except Exception as exc:
                record={'case':case,'wall_seconds':time.monotonic()-started,'error':str(exc)}
            target.write_text(json.dumps(record,indent=2))
            print(f"{number}/{len(questions)} {case['id']} {record['wall_seconds']:.1f}s", 'ERROR' if 'error' in record else f"evidence={len(record['result']['evidence'])} verdict={record['result']['verification'].get('decision')}",flush=True)
    finally:
        models_client._local_client=original_client
    manifest['finished_at']=datetime.now().astimezone().isoformat()
    manifest['chunks']=len(chunks)
    manifest['embedding_dimensions']=len(vectors[0])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Saved',out,flush=True)

if __name__=='__main__':
    asyncio.run(main())
