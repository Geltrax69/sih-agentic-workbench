"""Explicit, unblinded labels for the frozen repaired-run outputs."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[3]
out=root/'tests/evaluation/results/lmstudio-document-2026-11-04-final'
review={'reviewer':'Authoring assistant; unblinded development-set regression review, not independent validation', 'rubric':'tests/evaluation/document_pilot/rubric.md', 'cases':{}}
def add(id,coverage,coverage_reason,mini,gemma,combined):
 def r(v):return {'correct':v[0],'unsupported_material':v[1],'reason':v[2]}
 review['cases'][id]={'retrieval_coverage':coverage,'coverage_reason':coverage_reason,'responses':{'eval-minicpm5-1b':r(mini),'eval-gemma4-e4b':r(gemma),'combined':r(combined)}}
add('Q01','complete','Selected pages 8 and 4 explicitly contain all three gate decisions.',
 (True,False,'Correct boundary decisions plus faithful threshold context.'),
 (True,False,'Returns the exact three-decision sentence.'),
 (True,False,'Retains the correct gate decisions without rewriting them.'))
add('Q02','complete','Page 4 explicitly distinguishes deterministic retrieval gating from correctness probability.',
 (True,False,'Returns the explicit not-a-probability statement.'),
 (True,False,'Returns the explicit not-a-probability statement.'),
 (True,False,'Preserves the correct limitation.'))
add('Q03','complete','The explicit default chunk definition on page 3 is now retrieved.',
 (True,False,'Returns 800-character windows and nominal 100-character overlap.'),
 (False,False,'The generator exhausted its output budget; no accepted answer was returned.'),
 (True,False,'Preserves the correct MiniCPM excerpt despite Gemma failing.'))
add('Q04','complete','Pages 3 and 8 specify vector(768).',
 (True,False,'Correct vector dimensionality with faithful extra context.'),
 (True,False,'Correct vector dimensionality.'),
 (True,False,'Retains the shared correct dimensionality without a synthesis refusal.'))
add('Q05','complete','Page 3 contains the worker absence and Redis transport limitation.',
 (True,False,'Both negative conclusions appear.'),
 (True,False,'Both negative conclusions appear.'),
 (True,False,'Both required conclusions are retained.'))
add('Q06','complete','Page 4 contains both the owner role and WAITING_FOR_APPROVAL.',
 (False,False,'Names owner but omits the paused WAITING_FOR_APPROVAL state.'),
 (False,False,'Names the paused state but omits the owner role.'),
 (True,False,'Combines the complementary owner-role and paused-state excerpts.'))
add('Q07','complete','Page 4 now supplies the normal task settings; pilot settings are separately described.',
 (True,False,'Explicitly returns temperature 0.3 and maximum 800 output tokens.'),
 (True,False,'Explicitly returns normal settings and distinguishes the separately labeled Ollama pilot.'),
 (True,False,'Retains the normal settings without rewriting pilot values as production values.'))
add('Q08','complete','Page 4 supplies the 500-character limit and retrieval-gate interpretation.',
 (True,False,'Returns both limit and meaning, with the memory contamination caveat.'),
 (False,False,'Returns the 500-character limit but omits the flag meaning.'),
 (True,False,'Retains both required facts from MiniCPM.'))
add('Q09','partial','Four 20,000-request stages and zero observed errors are present, but the explicit 80,000 total in the abstract is absent.',
 (False,False,'States stage count/per-stage requests and zero errors but never gives the requested 80,000 total.'),
 (False,False,'Gives per-stage count but omits the total; the zero-error wording is a criterion rather than an observed result.'),
 (False,False,'Retains the available facts but does not explicitly answer the requested total; the user would have to calculate it.'))
add('Q10','complete','The selected page 6 evidence includes the table and explicit peak-client statement, but row layout is difficult.',
 (False,False,'Correctly states 50 clients but does not state the requested peak throughput 2,823.4 requests/s.'),
 (False,False,'Only states 50 clients; omits peak throughput.'),
 (False,False,'Retains the client count but not the required throughput value.'))
add('Q11','complete','Pages 7 and 1 give p95 25.12 seconds and page 7 explicitly separates generation from API reads.',
 (False,False,'Gives p95 but omits the requested warning about generated-answer throughput.'),
 (True,False,'Returns both the measured p95 and the explicit cannot-support-thousands distinction.'),
 (True,False,'Preserves both required facts from the complementary excerpts.'))
add('Q12','complete','Several selected passages explicitly state keyword coverage does not establish accuracy.',
 (True,False,'Returns the exact no-general-accuracy statement.'),
 (True,False,'Returns the exact no-general-accuracy statement with heuristic context.'),
 (True,False,'Preserves the accurate limitation.'))
add('Q13','complete','Selected pages 5 and 1 specify both model tags, temperatures, and 24 total generations.',
 (False,False,'Names models and temperatures but omits the required 24-generation total.'),
 (True,False,'Includes model tags, both temperatures, and 24 generations.'),
 (True,False,'Retains all required facts.'))
add('Q14','complete','The selected pages 7 passages contain the trial identity and explicit no-deletion statement.',
 (False,False,'Selects unrelated pilot statistics and omits the requested trial and actual-deletion outcome.'),
 (False,False,'Identifies Qwen, 0.8 and seed 17, but selects only the fragment deletion instead of answering whether deletion occurred.'),
 (False,False,'Retains the trial identity but still does not explicitly answer the actual-deletion question.'))
add('Q15','complete','Pages 1 and 10 include unpublished status and pending authors/affiliations.',
 (False,False,'Answers pending authors/affiliations but omits unpublished/no-peer-review status.'),
 (False,False,'Answers pending affiliations and release metadata, not whether the manuscript is accepted or peer reviewed.'),
 (False,False,'Retains pending author details but does not explicitly answer publication/peer-review status.'))
add('Q16','complete','Page 2 explicitly says local deployment does not establish air-gap or legal certification.',
 (True,False,'Returns the explicit no-air-gap/no-certification statement.'),
 (False,False,'Output-token budget exhausted; no accepted response.'),
 (True,False,'Preserves the complete MiniCPM excerpt despite Gemma failure.'))
add('Q17','not_applicable','The document contains no subscription price.',
 (False,False,'Selects repository provenance instead of explicitly abstaining about price.'),
 (True,False,'Correctly declines to answer because the sources do not contain the price.'),
 (False,False,'Retains the irrelevant provenance excerpt and does not explicitly abstain; no price is invented.'))
add('Q18','not_applicable','The document contains no patent application number for the project.',
 (False,False,'Selects repository/release metadata rather than explicitly abstaining about the filing number.'),
 (False,False,'Selects release metadata rather than explicitly abstaining.'),
 (False,False,'Does not answer or explicitly abstain; it does not invent a patent number.'))
add('Q19','not_applicable','The document contains no production customer count.',
 (False,False,'Selects an evidence manifest instead of answering or explicitly abstaining.'),
 (False,False,'Selects benchmark commentary, not a customer count or explicit abstention.'),
 (False,False,'Retains irrelevant excerpts rather than explicitly abstaining about customers.'))
add('Q20','complete','Selected pages 4 and 9 describe the bounded workflow and reject a general agent planner.',
 (False,False,'Lists bounded task states but does not explicitly reject the false general-DAG premise.'),
 (True,False,'Explicitly says a general agent planner is not demonstrated; the false premise is rejected.'),
 (True,False,'Rejects the general-planner premise and supplies bounded task-sequence context.'))
assert len(review['cases']) == 20
for id, case in review['cases'].items():
 assert (out/f'{id}.json').exists()
(out/'review.json').write_text(json.dumps(review,indent=2))
for model in ['eval-minicpm5-1b','eval-gemma4-e4b','combined']:
 print(model, sum(c['responses'][model]['correct'] for c in review['cases'].values()), '/20')
