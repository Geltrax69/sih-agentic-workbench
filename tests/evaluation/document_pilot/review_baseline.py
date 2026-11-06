import json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
out=root/'tests/evaluation/results/lmstudio-document-2026-11-03'
review={
 'reviewer':'Authoring assistant; unblinded exploratory review, not an independent human adjudication',
 'rubric':'tests/evaluation/document_pilot/rubric.md',
 'scoring':'Strict correct = complete response to required facts with no material false addition. Citation formatting scored separately. Minor wording/style defects are not failures.',
 'cases':{}
}
def add(id,coverage,coverage_reason,mini,gemma,combined):
 def r(v):return {'correct':v[0],'unsupported_material':v[1],'reason':v[2]}
 review['cases'][id]={'retrieval_coverage':coverage,'coverage_reason':coverage_reason,'responses':{'eval-minicpm5-1b':r(mini),'eval-gemma4-e4b':r(gemma),'combined':r(combined)}}
add('Q01','complete','Page 8 explicitly lists all three requested boundary decisions.',
 (True,False,'All three decisions are correct; the answer is verbose and includes an unnecessary hypothetical threshold comment.'),
 (False,True,'Invents relationships between stale evidence, citations, memory count, and threshold decisions.'),
 (False,True,'Repeats the unsupported memory/staleness/citation alternatives from the Gemma answer.'))
add('Q02','complete','Page 4 explicitly says the deterministic threshold does not estimate correctness probability.',
 (True,False,'Correctly rejects the probability interpretation and reproduces the score ranges.'),
 (False,False,'Refuses despite an explicit answer in the retrieved source.'),
 (False,True,'Includes the right headline but adds an unsupported condition about enough available posts and misdescribes the threshold settings.'))
add('Q03','partial','The retrieved page 8 discusses chunk experiments but the explicit default 800/100 definition on page 3 is absent.',
 (False,False,'Does not answer the default values; the retrieval did not include the explicit definition.'),
 (False,True,'Names 800 and 100 but adds the false statement that both are at 200 characters.'),
 (False,True,'Repeats the false both-at-200 statement.'))
add('Q04','complete','Two selected passages explicitly state vector(768).',
 (True,False,'Correct dimensionality and faithful extra copied context, but several source numbers are out of range.'),
 (True,False,'Correctly identifies vector(768) and the IVFFlat context; additional dimensions is imprecise wording.'),
 (False,True,'Correct core dimension, but changes the 400/0 stored-character count from 1,394 to 1,396 and calls variant values defaults.'))
add('Q05','complete','Page 3 explicitly states both the missing retry worker and Redis health-check role.',
 (True,False,'Both requested negative conclusions are present. Some source attribution is imprecise and an extra source number is invented.'),
 (True,False,'The two bullet headings correctly state Redis is not demonstrated transport and the retry worker is absent. Explanatory text is incoherent but does not reverse those facts.'),
 (False,False,'States Redis is not transport but omits the required conclusion about the absent durable retry worker.'))
add('Q06','complete','Page 4 gives the owner role, WAITING_FOR_APPROVAL state, and server-derived task scope.',
 (True,False,'Correct owner role and WAITING_FOR_APPROVAL state; some citations point to the wrong selected passage.'),
 (False,True,'Required role and state appear, but the explanation incorrectly gives the owner a chance to select workspace scope; the source says the public route derives scope from the stored task.'),
 (False,True,'Retains the false owner-selected workspace-scope behavior while naming the right role and state.'))
add('Q07','missing','The selected passages discuss the pilot table and abstract, not the normal task settings (0.3 and 800) on page 4.',
 (False,True,'Invents normal-path temperature 0.8 and a 35-token maximum, confusing pilot measurements with settings.'),
 (False,True,'Confuses six calls with a maximum token count and substitutes pilot temperatures for the task settings.'),
 (False,True,'Repeats the false 35-token cap and advises using the Calls column as a token limit.'))
add('Q08','complete','Page 4 explicitly states the 500-character limit and retrieval-gate meaning of verified=true.',
 (True,False,'Copies a long passage, but the requested memory limit and meaning are both explicitly present and correct.'),
 (True,False,'Correct limit, flag meaning, and caveat about historical-memory revocation.'),
 (True,False,'Preserves the correct memory facts and limitation.'))
add('Q09','complete','Selected pages 1, 5 and 6 state 80,000 total, four stages of 20,000, and zero errors.',
 (False,True,'Adds a per-stage count to the already-total count to invent 100,000 requests; also confuses request count and throughput units.'),
 (False,True,'Invents an 80,000–120,000 range and offers contradictory alternatives instead of the explicit total.'),
 (False,True,'Combines conflicting invented totals and mixes AI task counts and latency with API stage/error statistics.'))
add('Q10','complete','The selected page 6 table contains 2,823.4 at 50 clients and the surrounding prose confirms the client count.',
 (False,True,'Omits the peak request/s value and repeatedly mislabels the lower 100-client throughput as a peak.'),
 (False,True,'Uses the graph axis limit 3,400 as measured throughput and gives inconsistent client counts.'),
 (False,True,'Omits the peak and reverses a 3.15-times-higher p95 into 3.15-times-faster behavior.'))
add('Q11','complete','Pages 1 and 7 give the 25.12-second p95, and page 7 distinguishes generation throughput from API reads.',
 (False,True,'Correct p95, but invents that the AI workload was designed for a few thousand requests per second.'),
 (False,True,'Correct p95 and broad distinction, but invents a few-hundred-at-most generation capacity.'),
 (False,True,'Carries forward the unsupported few-hundred capacity claim.'))
add('Q12','complete','All three passages explicitly distinguish keyword coverage from answer accuracy.',
 (True,False,'Correct rejection and explanation of the keyword-coverage heuristic, despite awkward final wording.'),
 (True,False,'Quotes the relevant limitations and explains that general accuracy cannot be derived; the final refusal phrasing is awkward.'),
 (True,False,'Correctly rejects the accuracy interpretation and explains keyword and citation-marker limitations.'))
add('Q13','complete','The selected table lists both model tags, both temperatures, and four rows of six calls (24 total).',
 (False,True,'Does not answer the total; corrupts the table while copying it, assigning the Qwen high-temperature row values to Gemma, then repeats until truncated.'),
 (False,True,'Names models and temperatures but omits 24 total and confuses the six-call cells with median wall seconds.'),
 (False,True,'Lists the current evaluation model identifiers rather than answering about the manuscript pilot, with no temperatures or total.'))
add('Q14','partial','Temperature 0.8, seed 17 and no actual deletion are explicit, but the leading model-name clause is clipped; Qwen is mentioned later.',
 (False,True,'Confuses a 14.1% latency change with the model-temperature-seed identity; the actual requested trial is not identified.'),
 (False,False,'Correctly names Qwen and says no deletion, but omits temperature 0.8 and seed 17.'),
 (False,True,'Does not identify the trial and states no additional evidence is available as a fact instead of identifying the unsupported premise.'))
add('Q15','complete','Pages 1 and 10 explicitly say unpublished draft, no acceptance claim, and pending named authors/affiliations.',
 (True,False,'Correctly rejects acceptance and identifies pending author details.'),
 (True,False,'Correct publication and author-detail status; awkward here-here wording is a style defect.'),
 (True,False,'Preserves the correct publication and pending-author facts.'))
add('Q16','complete','Page 2 explicitly distinguishes local hosting from air-gap and legal certification.',
 (True,False,'Correctly rejects the air-gap/certification inference.'),
 (True,False,'Correctly explains intended sovereign hosting and the unestablished certification status.'),
 (True,False,'Correctly preserves that local hosting does not establish air-gap or certification.'))
add('Q17','not_applicable','The document contains no subscription price.',
 (False,True,'Correctly refuses a price, but falsely attributes the EACL demonstration to pgvector maintainers.'),
 (True,False,'The terse no-source response declines to invent an unsupported price.'),
 (False,True,'Refuses a price but falsely presents planned features as current and attributes an EACL listing to this project.'))
add('Q18','not_applicable','The document contains no patent filing number for the project.',
 (True,False,'Correctly refuses to invent a patent application number.'),
 (True,False,'Correctly states that no source contains a patent application number.'),
 (True,False,'Correctly states that the provided sources contain no application number.'))
add('Q19','not_applicable','The document contains no production customer count.',
 (True,False,'Correctly states that no customer count is supplied.'),
 (False,False,'Gives unrelated package details and does not answer or explicitly abstain about the customer count.'),
 (True,False,'Correctly states that no production customer count is supplied.'))
add('Q20','not_run','The LM Studio connection failed before any response was recorded.',
 (False,False,'Transport failure; not a scored model response.'),
 (False,False,'Transport failure; not a scored model response.'),
 (False,False,'Transport failure; not a scored model response.'))
assert len(review['cases']) == 20
(out/'review.json').write_text(json.dumps(review,indent=2))
for model in ['eval-minicpm5-1b','eval-gemma4-e4b','combined']:
 correct=sum(c['responses'][model]['correct'] for c in review['cases'].values())
 print(model, f'{correct}/20 requests; {correct}/19 completed questions')
