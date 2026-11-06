"""Explicit combined-answer labels; no model judge or keyword-based pass scores."""
from pathlib import Path
import json, math, statistics
ROOT=Path(__file__).resolve().parents[3]
RESULTS=ROOT/'tests/evaluation/results'

def record(folder, labels, role):
 path=RESULTS/folder
 questions=json.loads((path/'questions.json').read_text())
 assert set(labels)=={q['id'] for q in questions}
 entries=[]
 for q in questions:
  raw=json.loads((path/(q['id']+'.json')).read_text())
  correct,reason=labels[q['id']]
  assert not correct or 'result' in raw
  entries.append({'id':q['id'],'question':q['question'],'expected':q['expected'],
                  'correct':correct,'reason':reason,'wall_seconds':raw['wall_seconds']})
 times=[e['wall_seconds'] for e in entries]
 answered=[e['wall_seconds'] for e,q in zip(entries,questions) if q['category']!='unanswerable']
 summary={'role':role,'reviewer':'Authoring assistant, unblinded; strict factual completeness and no material false additions.',
          'scored_output':'combined_answer only; individual outputs retained but not separately graded in this revision',
          'correct':sum(e['correct'] for e in entries),'total':len(entries),
          'median_seconds':statistics.median(times),'p95_nearest_rank_seconds':sorted(times)[math.ceil(.95*len(times))-1],
          'answerable_median_seconds':statistics.median(answered) if answered else None,
          'passes_above_80_percent':sum(e['correct'] for e in entries)/len(entries)>.8,'cases':entries}
 (path/'combined_review.json').write_text(json.dumps(summary,indent=2))
 transcript=[]
 for entry in entries:
  raw=json.loads((path/(entry['id']+'.json')).read_text())
  transcript.extend([f"## {entry['id']} {'PASS' if entry['correct'] else 'FAIL'} — {entry['question']}",
                     'Expected: '+entry['expected'],raw.get('result',{}).get('combined_answer',raw.get('error','No output')),
                     'Review: '+entry['reason']])
 (path/'combined_transcript.md').write_text('\n\n'.join(transcript))
 print(folder,summary['correct'],'/',summary['total'],'median',round(summary['median_seconds'],2),'s')
 return summary

PRIMARY={
 'Q01':(True,'All three score boundaries and decisions are explicit.'),
 'Q02':(True,'Explicitly states deterministic thresholding is not correctness probability.'),
 'Q03':(True,'Includes 800-character windows and nominal 100-character overlap.'),
 'Q04':(True,'Explicit vector(768) storage.'),
 'Q05':(True,'Includes absent durable retry worker and Redis not being demonstrated transport.'),
 'Q06':(True,'Includes owner role and WAITING_FOR_APPROVAL.'),
 'Q07':(True,'Includes normal task temperature 0.3 and 800-token cap, with pilot settings separately labeled.'),
 'Q08':(True,'Includes 500-character memory and retrieval-gate rather than independent verification.'),
 'Q09':(False,'Gives four 20,000-request stages and zero-error rows but omits the explicit 80,000 total; user would have to calculate it.'),
 'Q10':(True,'Includes measured peak 2,823.4 requests/s at 50 clients.'),
 'Q11':(True,'Includes p95 25.12 seconds and separates API reads from generated answers.'),
 'Q12':(True,'Explicitly rejects keyword coverage as general answer accuracy.'),
 'Q13':(True,'Includes both model tags, both temperatures, and 24 calls.'),
 'Q14':(True,'Includes Qwen at 0.8/seed 17 and explicitly no deletion capability or actual deletion.'),
 'Q15':(False,'Gives pending authors/affiliations and exploratory evaluation status but omits unpublished/no-peer-review manuscript status.'),
 'Q16':(True,'Explicitly says locality does not establish air-gap or legal certification.'),
 'Q17':(True,'Explicitly abstains from inventing subscription price.'),
 'Q18':(True,'Explicitly abstains from inventing the patent number.'),
 'Q19':(True,'Explicitly abstains about an absent production customer count.'),
 'Q20':(True,'Explicitly rejects a general agent planner and describes implemented bounded workflow.')}

if __name__=='__main__':
 record('lmstudio-document-2026-11-04-v4',PRIMARY,'Original 20-question development regression set, unchanged')

VALIDATION={
 'V01':(True,'Rejects dimension-only compatibility and includes reindexing and threshold recalibration.'),
 'V02':(True,'Explicitly identifies Markdown stored in a task step.'),
 'V03':(True,'Includes the actual FOR UPDATE ... SKIP LOCKED clause.'),
 'V04':(True,'Includes 19 tables and 53,270 dump bytes.'),
 'V05':(True,'Explicit up-to-three recent eligible memory items.'),
 'V06':(True,'Includes one HTTP 200 and one HTTP 400 approval decision.'),
 'V07':(True,'Associates 400/100 with six chunks and 1,694 stored characters.'),
 'V08':(True,'Explicitly abstains rather than inventing a corresponding-author email.'),
 'V09':(False,'Returns segmentation experiments and storage/chunk settings, not the requested default retrieval limit of six.'),
 'V10':(True,'Explicitly abstains rather than inventing a supplier address.')}

if __name__=='__main__':
 record('lmstudio-validation-2026-11-04-v4',VALIDATION,'Ten additional questions authored before the v4 fixes and not used to tune them; same PDF, unblinded review')

POSTGRES={**PRIMARY,'Q11':(False,'Returns AI p95 25.12 seconds but omits the requested distinction from API-read generation throughput.')}
MAINTENANCE={
 'M01':(True,'Includes BRG-4210 and 45 Nm.'),'M02':(True,'Includes depressurizing and locking out before guard removal.'),
 'M03':(True,'Includes 50 percent load for 10 minutes and temperature check.'),'M04':(True,'Includes reliability engineer and coolant loop.'),
 'M05':(True,'Includes blocked cooling fins, bearing wear, and low coolant.'),'M06':(True,'Explicitly abstains about unreported bearing cost.'),
 'M07':(True,'Explicitly abstains about unreported service date.'),'M08':(True,'Specifies 45 Nm, contradicting the false 90 Nm premise.')}
DIAGNOSTIC={
 'H01':(True,'Explicit lists=100 index setting.'),'H02':(True,'Includes the unambiguous narrative sentence MinIO stores uploaded bytes.'),
 'H03':(True,'Includes 20.55-second median and 83.22-second elapsed time.'),'H04':(True,'Explicitly abstains about an unreported hospital purchaser.'),
 'H05':(True,'Explicitly rejects interpreting the 1.75-second check as measured service RTO.'),'H06':(True,'Includes one answer, two warnings, and no improved-correctness conclusion.'),
 'H07':(False,'Returns rows for 50, 10 and 1 clients, not the requested 100-client values; this failure prompted the subsequent row-condition guard.'),
 'H08':(True,'Includes 75 percent collection reads and 25 percent profile reads.'),'H09':(True,'Includes Markdown in a task step and no public download artifact.'),
 'H10':(True,'Includes actual metadata counts 8B and 9B.'),'H11':(True,'Explicitly abstains from an unmeasured energy value.'),
 'H12':(True,'Includes the actual seeds 17 and 29, not merely a protocol saying two seeds.')}
if __name__=='__main__':
 record('lmstudio-postgres-2026-11-04-v4',POSTGRES,'Production PostgreSQL/pgvector retrieval; original development set')
 record('lmstudio-diagnostic-2026-11-04-v4',DIAGNOSTIC,'Additional diagnostic set used to guide repairs; not held out')
 record('maintenance-2026-11-04-v4',MAINTENANCE,'Second-document Markdown regression; used in development')
