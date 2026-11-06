# LM Studio document test: before and after fixes

Prepared 4 November 2026. Document: `Research_Paper.pdf` (11 pages). Same 20 questions and document hash in both runs.

**These are assistant-reviewed development-set results, not independent or general model-accuracy estimates.** Earlier responses informed the fixes. The repaired system returns model-selected source excerpts rather than freely rewritten answers.

| Model / output | Before: correct / 20 | After: correct / 20 |
|---|---:|---:|
| MiniCPM5 1B Q8_0 | 11/20 (55%) | 9/20 (45%) |
| Gemma 4 E4B Q4_K_M (7.5B total) | 8/20 (40%) | 10/20 (50%) |
| Combined output | 6/20 (30%) | 13/20 (65%) |

The baseline completed 19 requests; Q20 failed to connect. Its conditional correctness denominators are 19, not 20. The table counts that request as unsuccessful. No incorrect-answer cases were removed. The final run returned all 20 combined responses; two Gemma selections hit their output-token limit, and the combined responses retained the valid MiniCPM excerpts in those cases.

## What changed

- PDF extraction retains table layout. Chunk overlap begins at a line or word boundary. Existing indexed PDFs need reingestion to obtain the improved extraction.
- Multi-model retrieval adds a lexical candidate channel and fuses vector/BM25 ranks; cosine scores remain separate from selection ranks. Both database candidate channels retain workspace and non-deleted-document filters.
- Models select evidence-span IDs through constrained JSON. The application renders the original source text and inserts its source citations. The default combiner revalidates and deduplicates the selected source spans without another model call. An explicitly requested synthesizer can still select source spans. Invalid selections fail closed.
- Verification binds each claim to its cited passages. Exact excerpts are checked directly; other claims have a 64-token, 15-second judge budget and exact-verdict parsing. Failed generators cannot seed an invented synthesis.

## Scope and limits

The live test used both existing LM Studio checkpoints and the existing Nomic embedder on the local machine. It used application extraction, chunking, evidence selection, generation, synthesis and (after repairs) verification, with an isolated in-memory cosine index. The database hybrid SQL path, Go authentication, MinIO, persistence and full deployment were not exercised. In-memory lexical candidate ranking approximates the database channel; it is not a PostgreSQL performance test.

The baseline used temperature 0.3, up to 800/900 output tokens, three selected chunks and free-text generation. The repaired run used temperature 0.0, at most 128 output tokens for span IDs, four selected chunks, improved extraction/retrieval and source-excerpt rendering. This bundled change is not an ablation and cannot attribute improvement to one component. The final run includes cheap exact-source verification; the baseline answer batch excluded the stalled verifier. Thus wall times are not isolated model speed comparisons.

Gemma is the downloaded OBLITERATUS community E4B checkpoint; LM Studio reports 7.5B total parameters, not a second 1B model. Results do not generalize to other checkpoints, corpora or languages. A source match is not proof that the source is true, relevant, complete or current.

## Every question

| ID | Question | Before Mini / Gemma / combined | After Mini / Gemma / combined |
|---|---|---|---|
| Q01 | What decisions does the manuscript's evidence gate make at scores 0.29, 0.30, and 0.45? | Pass / Fail / Fail | Pass / Pass / Pass |
| Q02 | Does the manuscript's deterministic evidence threshold estimate the probability that an answer is correct? | Pass / Fail / Fail | Pass / Pass / Pass |
| Q03 | What are the manuscript's default chunk-window size and nominal chunk overlap, in characters? | Fail / Fail / Fail | Pass / Fail / Pass |
| Q04 | What vector dimensionality does the manuscript use for stored embeddings? | Pass / Pass / Fail | Pass / Pass / Pass |
| Q05 | According to the manuscript, is Redis a demonstrated durable job transport, and is a durable retry worker implemented? | Pass / Pass / Fail | Pass / Pass / Pass |
| Q06 | Which workspace role can approve a report, and what task state pauses for that approval? | Pass / Fail / Fail | Fail / Fail / Pass |
| Q07 | What temperature and maximum output-token count does the manuscript's normal task-generation path use? | Fail / Fail / Fail | Pass / Pass / Pass |
| Q08 | What does verified=true mean for answer memory in the manuscript, and how much generated text can be stored? | Pass / Pass / Pass | Pass / Fail / Pass |
| Q09 | How many authenticated-read requests were tested in total, how many per stage, and how many errors were observed? | Fail / Fail / Fail | Fail / Fail / Fail |
| Q10 | What was the peak authenticated-read throughput, and at how many concurrent clients did it occur? | Fail / Fail / Fail | Fail / Fail / Fail |
| Q11 | What p95 latency did the 12-task AI workload record, and does the API-read throughput establish thousands of generated answers per second? | Fail / Fail / Fail | Fail / Pass / Pass |
| Q12 | Does the earlier three-question pilot's mean keyword coverage of 1.0 establish general answer accuracy? | Pass / Pass / Pass | Pass / Pass / Pass |
| Q13 | Which two model tags and two temperatures were used in the manuscript's fixed-evidence pilot, and how many measured generations were run? | Fail / Fail / Fail | Fail / Pass / Pass |
| Q14 | Which model-temperature-seed trial adopted the unsupported deletion premise, and did that trial actually delete documents? | Fail / Fail / Fail | Fail / Fail / Fail |
| Q15 | Is this manuscript a peer-reviewed accepted paper, and have named authors and affiliations been finalized? | Pass / Pass / Pass | Fail / Fail / Fail |
| Q16 | Does the manuscript establish an air-gapped or legally certified environment just because the workbench is called sovereign? | Pass / Pass / Pass | Pass / Fail / Pass |
| Q17 | What is the exact annual commercial subscription price of this workbench in Indian rupees? | Fail / Pass / Fail | Fail / Pass / Fail |
| Q18 | What is the patent application number filed by this project's inventors? | Pass / Pass / Pass | Fail / Fail / Fail |
| Q19 | How many real industrial customers have deployed this workbench in production? | Pass / Fail / Pass | Fail / Fail / Fail |
| Q20 | The paper proves a general autonomous DAG planner. Which general DAG planning algorithm was validated? | Fail / Fail / Fail | Fail / Pass / Pass |

## Evidence files

- Baseline: `tests/evaluation/results/lmstudio-document-2026-11-03/`
- Final: `tests/evaluation/results/lmstudio-document-2026-11-04-final/`
- Each folder retains per-question JSON, exact requests/responses, evidence, an embedding index, model identities, settings, document/question/source hashes, and explicit review rationales.
- The initial stalled verifier and preliminary quote-copy repair attempt remain in their own folders; neither is mixed into the before/after scores.
- Reproduce with `services/ai/.venv/bin/python tests/evaluation/run_document_pilot.py --out <new-directory>`. Existing experiment directories cannot be overwritten.
