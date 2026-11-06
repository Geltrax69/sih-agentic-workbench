"""Build the latest report from retained, explicitly reviewed experiments."""
from pathlib import Path
import hashlib
import html
import json
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'tests/evaluation/results'
COHORTS = [
 ('Original PDF questions', 'lmstudio-postgres-2026-11-04-v5', 'PostgreSQL / development'),
 ('Additional PDF questions', 'lmstudio-validation-2026-11-04-v5', 'PostgreSQL / additional'),
 ('Maintenance document', 'maintenance-2026-11-04-v5', 'In-memory / development'),
 ('Targeted table checks', 'lmstudio-tables-2026-11-04-v5', 'PostgreSQL / regression'),
]
reviews = [(title, folder, scope, json.loads((RESULTS / folder / 'combined_review.json').read_text())) for title, folder, scope in COHORTS]
lines = ['# Combined document QA: repair and validation', '', 'Prepared 4 November 2026. Latest v5 results; earlier reports and failed attempts are preserved.', '',
 '**The combined pipeline clears 80% on the tested PDF questions: 17/20 (85%) on the original set and 9/10 (90%) on ten additional questions. This is a small, unblinded evaluation, not a guarantee for arbitrary documents.**', '',
 '## Measured results', '', '| Cohort | Strict correct | Warm median | Scope |', '|---|---:|---:|---|']
for title, folder, scope, review in reviews:
 lines.append(f"| {title} | {review['correct']}/{review['total']} ({review['correct']/review['total']:.0%}) | {review['median_seconds']:.2f} s | {scope} |")
lines += ['', 'The previous combined result was 13/20 (65%) with an in-memory index. The current original PDF run uses real PostgreSQL 16/pgvector and the application retrieval SQL. Extraction, retrieval, ranking, model prompting and combination changed together; this is not a controlled component ablation. The original-set warm p95 was 4.35 seconds. Latency excludes cold model loading, upload, PDF ingestion and indexing. These measurements are not an isolated model-speed benchmark.', '',
 '## Models and answer behavior', '',
 'The existing LM Studio downloads were used: MiniCPM5 1B Q8_0 (eval-minicpm5-1b) and Gemma 4 E4B OBLITERATUS Q4_K_M (eval-gemma4-e4b; LM Studio reports 7.5B total parameters). The existing Nomic embedder produced 768-dimensional vectors. No model training, new weight downloads or cloud inference was used.', '',
 'Both generators independently select source paragraph IDs through constrained JSON, with temperature 0 and an 80-token output budget. The combiner validates and deduplicates their selected original excerpts. It returns cited source text rather than a freely rewritten answer. This can be verbose. Individual model outputs are retained but have not been separately scored in this revision.', '',
 '## Errors found and repaired', '',
 '- Retrieval missed relevant passages and qualifiers: combine lexical and vector candidates, use English stemming consistently in Python and PostgreSQL, diversify pages, and expand context within the same document and page.',
 '- PDF tables were flattened or selected from the wrong row: preserve layout, label aligned numeric rows, add metric aliases and reject a mismatched table row when the question specifies one unambiguous numeric row condition.',
 '- Relevant candidates were ranked but rendered in their original order: show the highest-ranked evidence first and preserve full paragraphs, including qualifications.',
 '- Questions about absent prices, identifiers and dates could select unrelated numbers: require the requested attribute and otherwise return an explicit insufficient-evidence response.',
 '- Structured selections could repeat until the token limit: use two fixed selection fields, reject truncated/invalid outputs and retain a valid other-model response.',
 '- Source citations could be confused with bibliography markers: sanitize document reference numbers and check each excerpt against its cited source. Source matching does not establish truth or completeness.',
 '- Docker configuration could omit the second model: forward AI_MULTI_MODELS in Compose and configure both loaded aliases in the local environment.', '',
 '## Remaining failed cases', '',
 '| Case | Why it is still a failure |', '|---|---|',
 '| Q09 | Gives four stages of 20,000 requests but does not explicitly answer the required total of 80,000. |',
 '| Q11 | Gives 25.12-second p95 latency but omits the required distinction between API-read throughput and generated-answer throughput. |',
 '| Q15 | Mentions pending authors and affiliations but does not explicitly identify the manuscript as unpublished and not peer reviewed. |',
 '| V09 | Returns chunking/storage settings instead of the requested default retrieval limit of six. |', '',
 'Partial answers count as failures even if all quoted text matches a source. The remaining work is semantic completeness and multi-part question coverage. The system does not yet guarantee correct answers for every written PDF, scanned document, language or table layout.', '',
 '## Evaluation and engineering checks', '',
 'The unchanged original 20 questions are development regressions and informed repairs. Twelve diagnostic questions and the maintenance/table cohorts also informed development; their scores are not independent evidence. The ten additional questions were authored before the paragraph/ranking fixes and were not used to tune those fixes, but concern the same PDF and were reviewed by the same assistant without blinding. One run per question and small samples limit confidence. No overall pooled accuracy is claimed.', '',
 'The PDF evaluation uses the unchanged 11-page Research_Paper.pdf, now extracted into 55 chunks. The maintenance cohort uses scripts/demo/maintenance_manual.md; it is not a second PDF evaluation. Strict review requires all requested facts and no material false additions. Expected answers, labels, rationales and complete responses remain inspectable.', '',
 '57 service unit/integration tests passed. Real PostgreSQL checks passed for workspace isolation, deleted-document exclusion, lexical-only hits, same-page context and vector-only scope. The frontend production build and AI Docker image build passed. A disposable container imported the updated modules, confirmed English stemming and resolved both configured models. Docker-to-LM-Studio connectivity returned HTTP 200. The full Go authentication, MinIO upload and deployed workspace lifecycle have not been tested in this run.', '',
 '## Applying the repair', '',
 'The updated AI image is built and Compose now forwards both model aliases. After restarting LM Studio, reload both checkpoints under eval-minicpm5-1b and eval-gemma4-e4b before using the configured combination. Previously indexed PDFs must be reingested to obtain the improved extraction and table labels. The main user application stack has not been started or migrated as part of this validation; only disposable test databases were used.', '',
 '## Retained evidence', '']
for title, folder, scope, review in reviews:
 lines += [f'- {title}: tests/evaluation/results/{folder}/ (combined_review.json, combined_transcript.md, per-question JSON, requests/responses and manifest).']
lines += ['- Engineering logs: tests/evaluation/results/qa-v5-validation/; SQL checks: tests/evaluation/results/qa-v3-validation/database.json.', '- Reproducible labels: tests/evaluation/document_pilot/review_v5.py. Test runner: tests/evaluation/run_document_pilot.py. Earlier attempts remain in separate results folders.', '- Previous 65% report: research_documents/LM_Studio_Document_Test_2026-11-04.pdf.', '']
md = '\n'.join(lines)
out = ROOT/'research_documents/Combined_QA_Validation_2026-11-04'
out.with_suffix('.md').write_text(md)
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyQA', fontName='Helvetica', fontSize=9.5, leading=14, spaceAfter=8))
styles['Title'].textColor=colors.HexColor('#123b51')
styles['Heading2'].textColor=colors.HexColor('#123b51')
styles['Heading2'].spaceBefore=13
story=[]
def para(s, style='BodyQA'):
 return Paragraph(html.escape(s).replace('**','').replace('`',''), styles[style])
rows=[]
def flush_table():
 global rows
 if not rows:return
 widths=[160,85,80,174] if len(rows[0])==4 else [45,454]
 table=Table([[para(c) for c in row] for row in rows], colWidths=widths, repeatRows=1, hAlign='LEFT')
 table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f1f5')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#8daab6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f8fa')])]))
 story.append(table);story.append(Spacer(1,8));rows=[]
for line in lines:
 if line.startswith('|'):
  if line.startswith('|---'):continue
  rows.append([s.strip() for s in line.strip('|').split('|')]);continue
 flush_table()
 if not line:continue
 if line.startswith('# '):story.append(para(line[2:],'Title'))
 elif line.startswith('## '):story.append(para(line[3:],'Heading2'))
 else:story.append(para(line))
flush_table()
def footer(canvas, doc):
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#536776'))
 canvas.drawString(48,28,'SIH workbench | Local two-model QA | 4 November 2026')
 canvas.drawRightString(547,28,str(doc.page))
SimpleDocTemplate(str(out.with_suffix('.pdf')),pagesize=(595,842),leftMargin=48,rightMargin=48,topMargin=44,bottomMargin=44,title='Combined document QA validation - 4 November 2026').build(story,onFirstPage=footer,onLaterPages=footer)
config_path=RESULTS/'qa-v5-validation/configuration.json'
config=json.loads(config_path.read_text());config.update(ai_image_build_passed=True,ai_image_imports_and_two_model_resolution_passed=True)
config_path.write_text(json.dumps(config,indent=2)+'\n')
paths=['services/ai/app/extraction.py','services/ai/app/retrieval.py','services/ai/app/ingestion.py','services/ai/app/grounding/excerpts.py','services/ai/app/grounding/verifier.py','services/ai/app/multi_model.py','services/ai/app/models_client.py','services/ai/requirements.txt','docker-compose.yml','tests/evaluation/document_pilot/questions.json','tests/evaluation/document_pilot/validation_questions.json','tests/evaluation/document_pilot/review_v5.py']
manifest={'date':'2026-11-04','scope':'Post-repair v5 combined-output evaluation; unblinded assistant review','sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'results':{folder:{k:v for k,v in review.items() if k!='cases'} for _,folder,_,review in reviews}}
(RESULTS/'qa-v5-validation/summary.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(out.with_suffix('.pdf'))
