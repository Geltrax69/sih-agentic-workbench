"""Generate a reviewable before/after report from retained outputs and explicit labels."""
from pathlib import Path
from collections import Counter
from math import ceil
import json, html, statistics, re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tests/evaluation/results/lmstudio-document-2026-11-03'
AFTER=ROOT/'tests/evaluation/results/lmstudio-document-2026-11-04-final'
MODELS=['eval-minicpm5-1b','eval-gemma4-e4b','combined']
LABELS=['MiniCPM5 1B Q8_0','Gemma 4 E4B Q4_K_M (7.5B total)','Combined output']

def load(directory):
 review=json.loads((directory/'review.json').read_text())
 records=[json.loads((directory/f'Q{i:02}.json').read_text()) for i in range(1,21)]
 manifest=json.loads((directory/'manifest.json').read_text())
 assert len(review['cases'])==20
 return records, review, manifest

before,br,bm=load(BASE);after,ar,am=load(AFTER)
assert bm['document_sha256']==am['document_sha256'] and bm['questions_sha256']==am['questions_sha256']
metrics={}
for label,directory,records,review in [('before',BASE,before,br),('after',AFTER,after,ar)]:
 completed=sum('result' in r for r in records)
 metrics[label]={'completed_requests':completed,'transport_or_pipeline_failures':20-completed,'models':{},'retrieval_coverage':dict(Counter(c['retrieval_coverage'] for c in review['cases'].values()))}
 for model in MODELS:
  correct=sum(c['responses'][model]['correct'] for c in review['cases'].values())
  unsupported=sum(c['responses'][model]['unsupported_material'] for c in review['cases'].values())
  generator_errors=sum(bool(a.get('error')) for r in records for a in r.get('result',{}).get('answers',[]) if a['model']==model)
  metrics[label]['models'][model]={'generator_errors':generator_errors,'correct':correct,'requests':20,'correct_request_fraction':correct/20,'completed_response_fraction':correct/completed,'unsupported_material_responses':unsupported}
 times=[r['wall_seconds'] for r in records if 'result'in r]
 metrics[label]['pipeline_wall_seconds']={'median':statistics.median(times),'p95_nearest_rank':sorted(times)[ceil(.95*len(times))-1]}
 calls=[json.loads(x) for x in (directory/'http_calls.jsonl').read_text().splitlines()]
 generations=[c for c in calls if c['url'].endswith('/chat/completions')]
 metrics[label]['http_generations']=len(generations)
 metrics[label]['length_capped_responses']=sum(c['response'].get('choices',[{}])[0].get('finish_reason')=='length' for c in generations)
summary={'method':'Unblinded 20-question development-set comparison; strict completeness with no material false additions. One trial per request. Raw source excerpts replace free-text answers in the after run.', 'before':metrics['before'],'after':metrics['after']}
(AFTER/'summary.json').write_text(json.dumps(summary,indent=2))

lines=['# LM Studio document test: before and after fixes\n','Prepared 4 November 2026. Document: `Research_Paper.pdf` (11 pages). Same 20 questions and document hash in both runs.\n',
'**These are assistant-reviewed development-set results, not independent or general model-accuracy estimates.** Earlier responses informed the fixes. The repaired system returns model-selected source excerpts rather than freely rewritten answers.\n',
'| Model / output | Before: correct / 20 | After: correct / 20 |\n|---|---:|---:|']
for model,name in zip(MODELS,LABELS):
 b=metrics['before']['models'][model]['correct'];a=metrics['after']['models'][model]['correct'];lines.append(f'| {name} | {b}/20 ({b/20:.0%}) | {a}/20 ({a/20:.0%}) |')
lines.extend(['\nThe baseline completed 19 requests; Q20 failed to connect. Its conditional correctness denominators are 19, not 20. The table counts that request as unsuccessful. No incorrect-answer cases were removed. The final run returned all 20 combined responses; two Gemma selections hit their output-token limit, and the combined responses retained the valid MiniCPM excerpts in those cases.\n',
'## What changed\n',
'- PDF extraction retains table layout. Chunk overlap begins at a line or word boundary. Existing indexed PDFs need reingestion to obtain the improved extraction.\n- Multi-model retrieval adds a lexical candidate channel and fuses vector/BM25 ranks; cosine scores remain separate from selection ranks. Both database candidate channels retain workspace and non-deleted-document filters.\n- Models select evidence-span IDs through constrained JSON. The application renders the original source text and inserts its source citations. The default combiner revalidates and deduplicates the selected source spans without another model call. An explicitly requested synthesizer can still select source spans. Invalid selections fail closed.\n- Verification binds each claim to its cited passages. Exact excerpts are checked directly; other claims have a 64-token, 15-second judge budget and exact-verdict parsing. Failed generators cannot seed an invented synthesis.\n',
'## Scope and limits\n',
'The live test used both existing LM Studio checkpoints and the existing Nomic embedder on the local machine. It used application extraction, chunking, evidence selection, generation, synthesis and (after repairs) verification, with an isolated in-memory cosine index. The database hybrid SQL path, Go authentication, MinIO, persistence and full deployment were not exercised. In-memory lexical candidate ranking approximates the database channel; it is not a PostgreSQL performance test.\n',
'The baseline used temperature 0.3, up to 800/900 output tokens, three selected chunks and free-text generation. The repaired run used temperature 0.0, at most 128 output tokens for span IDs, four selected chunks, improved extraction/retrieval and source-excerpt rendering. This bundled change is not an ablation and cannot attribute improvement to one component. The final run includes cheap exact-source verification; the baseline answer batch excluded the stalled verifier. Thus wall times are not isolated model speed comparisons.\n',
'Gemma is the downloaded OBLITERATUS community E4B checkpoint; LM Studio reports 7.5B total parameters, not a second 1B model. Results do not generalize to other checkpoints, corpora or languages. A source match is not proof that the source is true, relevant, complete or current.\n',
'## Every question\n', '| ID | Question | Before Mini / Gemma / combined | After Mini / Gemma / combined |\n|---|---|---|---|'])
for old,new in zip(before,after):
 id=old['case']['id'];bits=lambda rev:' / '.join('Pass' if rev['cases'][id]['responses'][m]['correct'] else 'Fail' for m in MODELS)
 lines.append(f"| {id} | {old['case']['question']} | {bits(br)} | {bits(ar)} |")
lines.append('\n## Evidence files\n\n- Baseline: `tests/evaluation/results/lmstudio-document-2026-11-03/`\n- Final: `tests/evaluation/results/lmstudio-document-2026-11-04-final/`\n- Each folder retains per-question JSON, exact requests/responses, evidence, an embedding index, model identities, settings, document/question/source hashes, and explicit review rationales.\n- The initial stalled verifier and preliminary quote-copy repair attempt remain in their own folders; neither is mixed into the before/after scores.\n- Reproduce with `services/ai/.venv/bin/python tests/evaluation/run_document_pilot.py --out <new-directory>`. Existing experiment directories cannot be overwritten.\n')
md='\n'.join(lines)
report=ROOT/'research_documents/LM_Studio_Document_Test_2026-11-04.md';report.write_text(md)
# Full transcript remains editable and machine-readable, not buried behind aggregate scores.
transcript=[]
for label,records,review in [('BEFORE',before,br),('AFTER',after,ar)]:
 for record in records:
  id=record['case']['id'];transcript.extend([f'## {label} {id}: {record["case"]["question"]}',f'Expected: {record["case"]["expected"]}'])
  outputs={a['model']:a['answer'] for a in record.get('result',{}).get('answers',[])};outputs['combined']=record.get('result',{}).get('combined_answer','')
  for m in MODELS:
   r=review['cases'][id]['responses'][m]
   transcript.extend([f'### {m} — {"Pass" if r["correct"] else "Fail"}',outputs.get(m) or record.get('error','No response'),f'Review: {r["reason"]}'])
(AFTER/'transcript.md').write_text('\n\n'.join(transcript))

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='T',fontName='Helvetica',fontSize=24,leading=28,textColor=colors.HexColor('#17445a'),spaceAfter=18))
styles.add(ParagraphStyle(name='H',fontName='Helvetica-Bold',fontSize=12,leading=16,textColor=colors.HexColor('#126b94'),spaceBefore=15,spaceAfter=8,keepWithNext=True))
styles.add(ParagraphStyle(name='B',fontName='Helvetica',fontSize=10,leading=15,spaceAfter=10))
styles.add(ParagraphStyle(name='C',fontName='Helvetica',fontSize=8,leading=11,spaceAfter=3))
def p(text,kind='B'):return Paragraph(html.escape(text).replace('\n','<br/>'),styles[kind])
def table(data,widths):
 t=Table([[p(str(c),'C')for c in row]for row in data],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f4fa')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#abcddd')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#e0e8ec')),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));return t
story=[p('Local model accuracy\nBefore & after fixes','T'),p('4 November 2026 | Research_Paper.pdf | 20 fixed development questions'),p('Exploratory, unblinded development-set regression test. These counts describe this document and question set, not general model accuracy.'),p('Strictly correct answers','H')]
data=[['Model / output','Before / 20','After / 20']]
for m,name in zip(MODELS,LABELS):
 b=metrics['before']['models'][m]['correct'];a=metrics['after']['models'][m]['correct'];data.append([name,f'{b}/20 ({b/20:.0%})',f'{a}/20 ({a/20:.0%})'])
story.extend([table(data,[275,100,100]),Spacer(1,14),p('The final run returned all 20 combined responses. Two Gemma selections exhausted their output-token limit; the combined outputs retained valid MiniCPM excerpts. The baseline completed 19 requests; one connection failure is counted unsuccessful in the table. Completed-response baseline rates: '+', '.join(f"{metrics['before']['models'][m]['correct']}/19" for m in MODELS)+'.'),p('Interpretation','H'),p('The output policy changed: the repaired system selects original source excerpts rather than freely rewriting model answers. This prevents invented rewrites, but irrelevant selections, missing facts and unnecessary refusals still fail the rubric. Verification means cited text matched, not that the question was answered correctly.')])
story.extend([PageBreak(),p('Changes and test scope','T')])
for heading,body in [
('Retrieval and extraction','Preserved PDF table layout, fixed overlap boundaries, and added lexical candidates plus vector/BM25 rank fusion. Existing stored documents require reingestion. Workspace and deletion predicates remain in both SQL candidate channels.'),
('Grounding and synthesis','Each model selects evidence span IDs using a constrained JSON response. Code renders source text and attaches citations. The default combiner revalidates and deduplicates the selected source spans without a third model call. Invalid responses are rejected; failed candidates do not supply facts.'),
('Bounded verification','Exact source excerpts are matched directly to their cited passages. Other claims have a 64-token / 15-second judge limit. Ambiguous, repetitive, failed or incorrectly cited verdicts cannot pass. The initial 2,000-token repetitive-verifier attempt is preserved separately.'),
('What actually ran','Two downloaded LM Studio checkpoints, the local Nomic embedder, and application extraction, chunking, evidence selection, generators, synthesis and corrected verification. The retrieval index was isolated in memory. Go auth, PostgreSQL hybrid SQL execution, MinIO and full deployment were not tested.'),
('Comparison limits','The same questions informed repair work: this is a development regression set, not held-out validation. Multiple settings changed together, including 0.3 to 0.0 temperature, three to four evidence chunks, and free text to extractive answers. One trial per question, with unblinded assistant scoring. No claim of causal attribution or general superiority is justified.'),
('Runtime','Baseline median/p95 question wall time: '+f"{metrics['before']['pipeline_wall_seconds']['median']:.1f}s / {metrics['before']['pipeline_wall_seconds']['p95_nearest_rank']:.1f}s. "+'After: '+f"{metrics['after']['pipeline_wall_seconds']['median']:.1f}s / {metrics['after']['pipeline_wall_seconds']['p95_nearest_rank']:.1f}s. "+'These include shared fan-out and synthesis; model loading and indexing are excluded. The baseline omitted verification; the corrected run includes it.')]:story.extend([p(heading,'H'),p(body)])
for first,last in [(0,10),(10,20)]:
 story.extend([PageBreak(),p(f'Question-level results / {1 if first==0 else 2}','T')]);rows=[['ID / question','Before\nM / G / C','After\nM / G / C']]
 for record in before[first:last]:
  id=record['case']['id'];bits=lambda rv:' / '.join('Yes' if rv['cases'][id]['responses'][m]['correct'] else 'No' for m in MODELS)
  rows.append([id+' '+record['case']['question'],bits(br),bits(ar)])
 story.append(table(rows,[315,80,80]));story.append(Spacer(1,12));story.append(p('M = MiniCPM5 1B; G = Gemma E4B (7.5B total); C = combined source selection. Yes means all requested facts are correct with no material false additions. Citation formatting alone is not a pass.'))
story.extend([PageBreak(),p('Review and reproducibility','T'),p('What remains unresolved','H')])
for record in after:
 id=record['case']['id'];r=ar['cases'][id]['responses']['combined']
 if not r['correct']:story.append(p(id+': '+r['reason']))
story.extend([p('Files and model identities','H'),p('Baseline folder: tests/evaluation/results/lmstudio-document-2026-11-03\nFinal folder: tests/evaluation/results/lmstudio-document-2026-11-04-final\nFull answers and review notes: transcript.md and review.json in the final folder. Exact prompts and responses: http_calls.jsonl. Source/document/question hashes: manifest.json.'),p('MiniCPM5-1B Q8_0 (openbmb) and gemma-4-E4B-it-OBLITERATED Q4_K_M (OBLITERATUS). LM Studio reports the latter as 7.5B total parameters. The existing Nomic Embed Text v1.5 Q4_K_M embedder was used. These exact downloaded checkpoints were tested, not every model in their families.'),p('A second document and independently labeled held-out questions are needed before a broader accuracy claim. Source accuracy, recall, completeness and answer relevance still require evaluation. The database SQL path and a full authenticated deployment remain separate checks.')])
def footer(c,d):
 c.setFont('Helvetica',8);c.setFillColor(colors.HexColor('#617c89'));c.drawString(45,817,'SOVEREIGN / LOCAL MODEL EVALUATION');c.drawRightString(550,25,str(d.page));c.drawString(45,25,'Development-set results; source attribution is not general answer accuracy.')
pdf=ROOT/'research_documents/LM_Studio_Document_Test_2026-11-04.pdf'
SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),leftMargin=45,rightMargin=45,topMargin=55,bottomMargin=48,title='LM Studio document test - before and after fixes').build(story,onFirstPage=footer,onLaterPages=footer)
print(json.dumps(summary,indent=2));print(pdf)
