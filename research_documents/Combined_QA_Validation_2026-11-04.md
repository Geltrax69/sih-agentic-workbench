# Combined document QA: repair and validation

Prepared 4 November 2026. Latest v5 results; earlier reports and failed attempts are preserved.

**The combined pipeline clears 80% on the tested PDF questions: 17/20 (85%) on the original set and 9/10 (90%) on ten additional questions. This is a small, unblinded evaluation, not a guarantee for arbitrary documents.**

## Measured results

| Cohort | Strict correct | Warm median | Scope |
|---|---:|---:|---|
| Original PDF questions | 17/20 (85%) | 1.84 s | PostgreSQL / development |
| Additional PDF questions | 9/10 (90%) | 3.49 s | PostgreSQL / additional |
| Maintenance document | 8/8 (100%) | 2.15 s | In-memory / development |
| Targeted table checks | 3/3 (100%) | 4.43 s | PostgreSQL / regression |

The previous combined result was 13/20 (65%) with an in-memory index. The current original PDF run uses real PostgreSQL 16/pgvector and the application retrieval SQL. Extraction, retrieval, ranking, model prompting and combination changed together; this is not a controlled component ablation. The original-set warm p95 was 4.35 seconds. Latency excludes cold model loading, upload, PDF ingestion and indexing. These measurements are not an isolated model-speed benchmark.

## Models and answer behavior

The existing LM Studio downloads were used: MiniCPM5 1B Q8_0 (eval-minicpm5-1b) and Gemma 4 E4B OBLITERATUS Q4_K_M (eval-gemma4-e4b; LM Studio reports 7.5B total parameters). The existing Nomic embedder produced 768-dimensional vectors. No model training, new weight downloads or cloud inference was used.

Both generators independently select source paragraph IDs through constrained JSON, with temperature 0 and an 80-token output budget. The combiner validates and deduplicates their selected original excerpts. It returns cited source text rather than a freely rewritten answer. This can be verbose. Individual model outputs are retained but have not been separately scored in this revision.

## Errors found and repaired

- Retrieval missed relevant passages and qualifiers: combine lexical and vector candidates, use English stemming consistently in Python and PostgreSQL, diversify pages, and expand context within the same document and page.
- PDF tables were flattened or selected from the wrong row: preserve layout, label aligned numeric rows, add metric aliases and reject a mismatched table row when the question specifies one unambiguous numeric row condition.
- Relevant candidates were ranked but rendered in their original order: show the highest-ranked evidence first and preserve full paragraphs, including qualifications.
- Questions about absent prices, identifiers and dates could select unrelated numbers: require the requested attribute and otherwise return an explicit insufficient-evidence response.
- Structured selections could repeat until the token limit: use two fixed selection fields, reject truncated/invalid outputs and retain a valid other-model response.
- Source citations could be confused with bibliography markers: sanitize document reference numbers and check each excerpt against its cited source. Source matching does not establish truth or completeness.
- Docker configuration could omit the second model: forward AI_MULTI_MODELS in Compose and configure both loaded aliases in the local environment.

## Remaining failed cases

| Case | Why it is still a failure |
|---|---|
| Q09 | Gives four stages of 20,000 requests but does not explicitly answer the required total of 80,000. |
| Q11 | Gives 25.12-second p95 latency but omits the required distinction between API-read throughput and generated-answer throughput. |
| Q15 | Mentions pending authors and affiliations but does not explicitly identify the manuscript as unpublished and not peer reviewed. |
| V09 | Returns chunking/storage settings instead of the requested default retrieval limit of six. |

Partial answers count as failures even if all quoted text matches a source. The remaining work is semantic completeness and multi-part question coverage. The system does not yet guarantee correct answers for every written PDF, scanned document, language or table layout.

## Evaluation and engineering checks

The unchanged original 20 questions are development regressions and informed repairs. Twelve diagnostic questions and the maintenance/table cohorts also informed development; their scores are not independent evidence. The ten additional questions were authored before the paragraph/ranking fixes and were not used to tune those fixes, but concern the same PDF and were reviewed by the same assistant without blinding. One run per question and small samples limit confidence. No overall pooled accuracy is claimed.

The PDF evaluation uses the unchanged 11-page Research_Paper.pdf, now extracted into 55 chunks. The maintenance cohort uses scripts/demo/maintenance_manual.md; it is not a second PDF evaluation. Strict review requires all requested facts and no material false additions. Expected answers, labels, rationales and complete responses remain inspectable.

57 service unit/integration tests passed. Real PostgreSQL checks passed for workspace isolation, deleted-document exclusion, lexical-only hits, same-page context and vector-only scope. The frontend production build and AI Docker image build passed. A disposable container imported the updated modules, confirmed English stemming and resolved both configured models. Docker-to-LM-Studio connectivity returned HTTP 200. The full Go authentication, MinIO upload and deployed workspace lifecycle have not been tested in this run.

## Applying the repair

The updated AI image is built and Compose now forwards both model aliases. After restarting LM Studio, reload both checkpoints under eval-minicpm5-1b and eval-gemma4-e4b before using the configured combination. Previously indexed PDFs must be reingested to obtain the improved extraction and table labels. The main user application stack has not been started or migrated as part of this validation; only disposable test databases were used.

## Retained evidence

- Original PDF questions: tests/evaluation/results/lmstudio-postgres-2026-11-04-v5/ (combined_review.json, combined_transcript.md, per-question JSON, requests/responses and manifest).
- Additional PDF questions: tests/evaluation/results/lmstudio-validation-2026-11-04-v5/ (combined_review.json, combined_transcript.md, per-question JSON, requests/responses and manifest).
- Maintenance document: tests/evaluation/results/maintenance-2026-11-04-v5/ (combined_review.json, combined_transcript.md, per-question JSON, requests/responses and manifest).
- Targeted table checks: tests/evaluation/results/lmstudio-tables-2026-11-04-v5/ (combined_review.json, combined_transcript.md, per-question JSON, requests/responses and manifest).
- Engineering logs: tests/evaluation/results/qa-v5-validation/; SQL checks: tests/evaluation/results/qa-v3-validation/database.json.
- Reproducible labels: tests/evaluation/document_pilot/review_v5.py. Test runner: tests/evaluation/run_document_pilot.py. Earlier attempts remain in separate results folders.
- Previous 65% report: research_documents/LM_Studio_Document_Test_2026-11-04.pdf.
