# Research evidence library

Updated **4 November 2026**. Start with [Evidence Review (PDF)](Evidence_Review_2026-11-03.pdf) or its [editable Markdown](Evidence_Review_2026-11-03.md).

The review covers patent readiness, research-paper readiness, implementation limitations, a proposed comparative evaluation, and the light UI build. It distinguishes published findings from implementation observations and untested hypotheses.

## Latest combined-model repair — 4 November 2026

[Latest validation report (PDF)](Combined_QA_Validation_2026-11-04.pdf) · [Editable report](Combined_QA_Validation_2026-11-04.md)

The latest v5 combined output passes **17/20 (85%)** original PDF questions with real PostgreSQL/pgvector retrieval, **9/10 (90%)** additional questions on that PDF, and **8/8** maintenance-document development checks. Three targeted table regressions also pass. These small cohorts are reviewed without blinding and must not be pooled as a general accuracy estimate. The original questions and diagnostic cases informed repairs. The maintenance document is Markdown, not another PDF.

Both downloaded models now select cited paragraphs, with improved table parsing, English hybrid retrieval, contextual expansion and fail-closed selection. Compose forwards both model aliases. Source matching verifies quoted text, not answer completeness. Q09, Q11, Q15 and V09 remain incomplete or off-target; the report lists them explicitly. Existing PDFs require reingestion for the new parser.

57 service tests, real PostgreSQL isolation/lexical/context checks, the frontend production build and AI image build pass. The full authenticated Go/MinIO application lifecycle remains untested. Raw v5 answers, prompts and review rationales are in `tests/evaluation/results/`; the report identifies each cohort folder.

## Earlier LM Studio test — 4 November 2026

[Before/after report (PDF)](LM_Studio_Document_Test_2026-11-04.pdf) · [Editable report](LM_Studio_Document_Test_2026-11-04.md)

Tested the downloaded MiniCPM5 1B Q8_0 and Gemma 4 E4B OBLITERATUS Q4_K_M (LM Studio reports 7.5B total) against `Research_Paper.pdf` on 20 fixed development questions. The combined strict pass count improved from 6/20 to 13/20. MiniCPM individually moved from 11/20 to 9/20, and Gemma from 8/20 to 10/20. The baseline had one connection failure; the final combined path completed 20 requests, with two Gemma generation-budget failures handled by retaining valid MiniCPM excerpts.

These are unblinded development-set labels; the same questions informed the fixes. They are not held-out or general model accuracy. The repaired mode returns validated source excerpts and a default source union, rather than freely rewritten answers. Seven combined responses still missed facts or failed to abstain explicitly. Source-match verification does not establish answer completeness. The full authenticated deployment and PostgreSQL hybrid SQL path remain untested in this pilot.

Raw outputs, prompts, source hashes, evidence, labels and transcript are retained under `tests/evaluation/results/lmstudio-document-2026-11-04-final/` in the repository. Earlier failed repair attempts remain in separate sibling folders. Existing database-indexed PDFs require reingestion to use the improved extraction. The repaired multi-model mode requires a local endpoint supporting constrained JSON-schema responses; this was tested with LM Studio.

## Original source PDFs

`sources/` contains **15 original PDFs**: 13 research papers (including two 2026 preprints), an IBM patent publication, and the final Indian Patent Office CRI guidelines. These are downloaded originals, not AI-written replacement papers. The source register lists their landing pages, PDF URLs, retrieval date, page counts, file sizes, and SHA-256 hashes.

- [Source register](source_register.json)
- [Annotated index](SOURCE_INDEX.md)
- `python3 fetch_sources.py` verifies existing PDFs and downloads missing files. A changed remote PDF is reported for review rather than silently replacing the recorded version.
- `python3 build_evidence_review.py` regenerates the review PDF and Markdown using ReportLab and the local register.

## Important corrections to earlier drafts

The October reports are historical drafts, **not established proof of novelty**. `Internet_Research_Report.pdf`, `Novelty_and_System_Report.pdf`, their DOCX counterparts, and older detailed descriptions must be read alongside the new evidence review.

1. RAG Ensemble Section 4.7 (PDF page 8) already studies different generators over fixed reference documents. The earlier contrary distinction is incorrect.
2. Word overlap is a lexical statistic, not truth, source entailment, or calibrated confidence.
3. Prompting for citations and parsing their numbers does not guarantee correct claim-to-citation attribution.
4. Local deployment, RBAC, and audit do not by themselves establish a patentable inventive step. Patent-family claim review remains open.
5. The 3 November evidence review contained no new comparative quality experiment. The later local-model pilots above add limited document-QA evidence, not a hardware-efficiency study. Existing manuscript results concern earlier workloads.
6. Inventorship, ownership, public-disclosure declarations, and any filing status require confirmation from records; they cannot be inferred from these drafts.

The existing PDFs and DOCX files are preserved. The new review supersedes their unsupported novelty and superiority conclusions; it does not assert that a patent has been filed or a paper accepted.

## UI and validation

Run `npm run dev -- --host 127.0.0.1` in `apps/web`, then visit `http://localhost:3000/?preview=1` for a clearly labeled sample-data preview. Normal sign-in is at `/`. The preview does not call the live API. Screenshots and browser-check results are in `output/ui/` at the repository root.

The frontend production build and 57 service tests pass. Docker was started for isolated PostgreSQL validation and the AI image build. Real local-model results are documented above; the full authenticated application deployment remains unverified. The 3 November evidence review describes the earlier state.
