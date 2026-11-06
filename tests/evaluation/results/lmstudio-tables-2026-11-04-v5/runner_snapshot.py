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
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import os
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'services/ai'))
from app import models_client, multi_model
from app.config import settings
from app.extraction import extract_segments, chunk_text, CHUNK_SIZE, CHUNK_OVERLAP
from app.retrieval import expand_context, select_evidence, terms


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cosine(a, b):
    denom = math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    return sum(x*y for x, y in zip(a, b, strict=True)) / denom if denom else 0.0


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--document', default='Research_Paper.pdf')
    parser.add_argument('--out', default='tests/evaluation/results/lmstudio-document-2026-11-04-v2')
    parser.add_argument('--questions', default='tests/evaluation/document_pilot/questions.json')
    parser.add_argument('--postgres', action='store_true', help='Use production retrieval in a disposable database; PILOT_POSTGRES_ADMIN_DSN is required')
    args = parser.parse_args()
    out = ROOT / args.out
    if out.exists() and any(out.iterdir()):
        raise SystemExit('Use a new --out directory; existing experiment results are immutable.')
    out.mkdir(parents=True, exist_ok=True)
    (out/'runner_snapshot.py').write_bytes(Path(__file__).read_bytes())
    document = ROOT / args.document
    dataset_path = ROOT / args.questions
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
        'library_versions': {name: importlib.metadata.version(name) for name in ['pypdf','snowballstemmer','httpx','psycopg']},
        'lms_version': subprocess.check_output(['lms','--version'], text=True).strip(),
        'settings': {'output_policy': 'ranked paragraph context; two fixed paragraph IDs; source union; answerability gate', 'generator_models': models, 'synthesizer': 'source_union', 'verifier': models[1], 'embedding_model': 'eval-nomic', 'temperature': 0.0, 'reasoning_effort': 'none', 'verifier_reasoning_effort': 'none', 'generator_max_tokens': 80, 'synthesis_max_tokens': 80, 'verifier_max_tokens': 64, 'context_length': 8192, 'chunk_size_chars': CHUNK_SIZE, 'chunk_overlap_chars': CHUNK_OVERLAP, 'retrieval_limit_per_channel': 16, 'selected_evidence': 4, 'context_expansion': 'up to four adjacent chunks per side within same document/page; 14000-character total context budget', 'ranking': 'cosine + lexical BM25 reciprocal ranks'},
        'source_hashes': {p: sha((ROOT/p).read_bytes()) for p in source_paths + ['services/ai/app/grounding/excerpts.py','services/ai/app/retrieval.py','services/ai/app/ingestion.py','tests/evaluation/run_document_pilot.py','services/ai/requirements.txt']},
        'verification': 'Full corrected pipeline enabled; exact source excerpts are checked against their cited passages without a model judge. Other claims use bounded verification.',
        'scope': 'Application PDF extraction/chunking, live local embeddings, in-memory exact cosine retrieval, production evidence focusing, independent local generations, Jaccard agreement, source-excerpt selection, source-checked synthesis and verification. This is an extractive output policy rather than the baseline free-text policy. Bypasses PostgreSQL/MinIO/Go authentication, task approval and persistence. No memory is supplied. One trial per question; order fixed; response wall times share fan-out contention.',
    }
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    (out/'questions.json').write_text(json.dumps(questions,indent=2))
    chunks=[]
    for location, text in extract_segments('application/pdf' if document.suffix.lower() == '.pdf' else 'text/markdown', document.read_bytes()):
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
        rows=[{**c,'score':cosine(v,q)} for c,v in zip(chunks,vectors,strict=True)]
        vector_hits=sorted(rows,key=lambda x:x['score'],reverse=True)[:16]
        query=set(terms(question))
        lexical_hits=sorted(rows,key=lambda x:sum(1 for t in terms(x['content']) if t in query),reverse=True)[:16]
        pool={r['chunk_id']:r for r in vector_hits+lexical_hits}
        return expand_context(select_evidence(question,list(pool.values())), rows)
    original_retrieve=multi_model.retrieve
    database=None
    workspace='isolated-document-pilot'
    if args.postgres:
        import psycopg
        admin_dsn=os.environ['PILOT_POSTGRES_ADMIN_DSN']
        database='codex_eval_'+uuid.uuid4().hex
        with psycopg.connect(admin_dsn,autocommit=True) as conn:
            conn.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(psycopg.sql.Identifier(database)))
        info=psycopg.conninfo.conninfo_to_dict(admin_dsn)
        info['dbname']=database
        settings.database_url=psycopg.conninfo.make_conninfo(**info)
        workspace=str(uuid.uuid4())
        doc_id=str(uuid.uuid5(uuid.NAMESPACE_URL,manifest['document_sha256']))
        with psycopg.connect(settings.database_url,autocommit=True) as conn:
            conn.execute('CREATE EXTENSION vector')
            conn.execute('CREATE TABLE documents(id uuid PRIMARY KEY, filename text, deleted_at timestamptz)')
            conn.execute(f'CREATE TABLE document_chunks(id uuid PRIMARY KEY, document_id uuid REFERENCES documents(id), workspace_id uuid, embedding vector({len(vectors[0])}), chunk_index integer, location text, content text)')
            conn.execute('INSERT INTO documents VALUES(%s,%s,NULL)',(doc_id,document.name))
            for chunk,vector in zip(chunks,vectors,strict=True):
                conn.execute('INSERT INTO document_chunks VALUES(%s,%s,%s,%s::vector,%s,%s,%s)',(str(uuid.uuid4()),doc_id,workspace,json.dumps(vector),chunk['chunk_index'],chunk['location'],chunk['content']))
        manifest['retrieval_backend']='PostgreSQL + pgvector; actual app.ingestion.search_workspace and app.multi_model.retrieve'
        manifest['database_document_id']=doc_id
        manifest['database_workspace_id']=workspace
        manifest['scope']='Live production retrieval and multi-model answering against a disposable PostgreSQL/pgvector index. Application extraction, local embeddings, candidate SQL, context, generation, combination and verification exercised. Go auth, MinIO upload and deployed task persistence are not exercised.'
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    else:
        manifest['retrieval_backend']='isolated in-memory exact cosine index'
        multi_model.retrieve=retrieve
    try:
        for number, case in enumerate(questions,1):
            target=out/f"{case['id']}.json"
            if target.exists():
                print(case['id'],'already recorded; skipping',flush=True)
                continue
            started=time.monotonic()
            try:
                result=await multi_model.run_multi_model_pipeline(workspace,case['question'],models=models)
                record={'case':case,'wall_seconds':time.monotonic()-started,'result':asdict(result)}
            except Exception as exc:
                record={'case':case,'wall_seconds':time.monotonic()-started,'error':str(exc)}
            target.write_text(json.dumps(record,indent=2))
            print(f"{number}/{len(questions)} {case['id']} {record['wall_seconds']:.1f}s", 'ERROR' if 'error' in record else f"evidence={len(record['result']['evidence'])} verdict={record['result']['verification'].get('decision')}",flush=True)
    finally:
        multi_model.retrieve=original_retrieve
        models_client._local_client=original_client
        if database:
            with psycopg.connect(admin_dsn,autocommit=True) as conn:
                conn.execute(psycopg.sql.SQL('DROP DATABASE {}').format(psycopg.sql.Identifier(database)))
    manifest['finished_at']=datetime.now().astimezone().isoformat()
    manifest['chunks']=len(chunks)
    manifest['embedding_dimensions']=len(vectors[0])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Saved',out,flush=True)

if __name__=='__main__':
    asyncio.run(main())
