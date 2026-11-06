## Q01 PASS — What decisions does the manuscript's evidence gate make at scores 0.29, 0.30, and 0.45?

Expected: 0.29 refuses; 0.30 answers with a warning; 0.45 answers. These are retrieval gate decisions, not accuracy probabilities.

D(U) = REFUSE if U is empty or s* < 0.30 ANSWER_WITH_WARNING if 0.30 <= s* < 0.45 ANSWER if s* >= 0.45 [2]
The evidence threshold creates discontinuities. [1]
A best usable score of 0.29 refuses, 0.30 permits a warning answer and 0.45 permits an answer under current settings. [1]
Raising the strong threshold to 0.70 while retaining weak=0.30 would map the three historical pilot scores to one answer and two warning answers. [1]
This is a deterministic replay of recorded scores, not evidence of improved correctness. [1]

Review: All three score boundaries and decisions are explicit.

## Q02 PASS — Does the manuscript's deterministic evidence threshold estimate the probability that an answer is correct?

Expected: No. It is a deterministic threshold on retrieval similarity, not a correctness probability.

The threshold function is deterministic. [1]
It does not estimate the probability of answer correctness. [1]
One high-scoring passage is sufficient for ANSWER, even if the requested detail is absent or other passages conflict. [1]
Stale evidence adds a reason string in the gate without reducing the score. [1]
Normal executor items are constructed after workspace-scoped SQL retrieval; revoked/stale metadata is not comprehensively propagated. [1]

Review: Explicitly states deterministic thresholding is not correctness probability.

## Q03 PASS — What are the manuscript's default chunk-window size and nominal chunk overlap, in characters?

Expected: 800-character windows and nominal 100-character overlap.

Ingestion supports text-bearing PDF, DOCX, XLSX, TXT, Markdown and CSV inputs. [2]
The current chunker uses 800-character windows with nominal 100-character overlap and prefers text boundaries where possible. [2]
Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. This is a source configuration, not evidence that the approximate index has been optimally trained or used by the query planner on the tiny corpus. [2]
(document reference 6) [2]

Review: Includes 800-character windows and nominal 100-character overlap.

## Q04 PASS — What vector dimensionality does the manuscript use for stored embeddings?

Expected: 768 dimensions, vector(768).

Ingestion supports text-bearing PDF, DOCX, XLSX, TXT, Markdown and CSV inputs. [2]
The current chunker uses 800-character windows with nominal 100-character overlap and prefers text boundaries where possible. [2]
Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. This is a source configuration, not evidence that the approximate index has been optimally trained or used by the query planner on the tiny corpus. [2]
(document reference 6) [2]
A new generator changes conditional text behavior while fixed evidence scores leave the gate unchanged. [1]
An embedding-model replacement changes retrieval geometry and requires compatible corpus/query embeddings, reindexing and threshold recalibration. [1]
Matching vector dimensionality alone does not make embeddings from different models comparable. [1]
The current vector(768) schema additionally requires a migration if the new dimension differs. [1]

Review: Explicit vector(768) storage.

## Q05 PASS — According to the manuscript, is Redis a demonstrated durable job transport, and is a durable retry worker implemented?

Expected: No to both. Redis participates in health checks; a durable retry worker for lost triggers or abandoned RUNNING jobs is absent.

bound to source versions, durable processing recovery and an evaluation set that separates retrieval relevance from answerability and faithfulness. [2]
Capacity work should exercise a mixed workload with ingestion and generation, increasing corpus sizes and sustained duration. [2]
Model routing or larger models should be added only with measurements showing their benefit for that workload. [2]
The ingestion service claims one pending PostgreSQL job under FOR UPDATE ... [1]
SKIP LOCKED, processes its object and records success or failure. [1]
Uploads trigger this processing through an internal request. [1]
A durable retry worker for lost triggers or abandoned RUNNING jobs is absent. [1]
Redis participates in health checks but is not a demonstrated job transport in the current execution path. [1]
Figure 1. Implemented system components and trust boundaries. [1]
Supporting Redis/graph components are not a demonstrated durable task queue or graph-augmented retrieval path. [1]

Review: Includes absent durable retry worker and Redis not being demonstrated transport.

## Q06 PASS — Which workspace role can approve a report, and what task state pauses for that approval?

Expected: Owner role; WAITING_FOR_APPROVAL.

Go public API PostgreSQL JWT; workspace roles; HTTP Metadata, vectors, tasks, approvals, memory [3]
The task begins in PLANNING, enters RUNNING, executes document_search and proceeds to VERIFYING and COMPLETED. [1]
Report-related keywords add report_generate, which pauses in WAITING_FOR_APPROVAL. [1]
The public decision route resolves workspace scope from the stored task and requires an owner role. [1]
An approval claims RUNNING under a task-row lock before resuming execution, preventing the second concurrent decision in the tested path from executing the same transition. [1]

Review: Includes owner role and WAITING_FOR_APPROVAL.

## Q07 PASS — What temperature and maximum output-token count does the manuscript's normal task-generation path use?

Expected: Temperature 0.3 and maximum 800 output tokens. This differs from the pilot's 160-token cap.

For non-refused tasks, numbered evidence and up to three recent eligible memory items are sent to the generator. [1]
The task path uses temperature 0.3 and a maximum output of 800 tokens. [1]
The system instruction asks for evidence-only answers, [n] citations and rejection of instructions inside evidence. [1]
Returned source filenames are evidence metadata, [1]

Review: Includes normal task temperature 0.3 and 800-token cap, with pilot settings separately labeled.

## Q08 PASS — What does verified=true mean for answer memory in the manuscript, and how much generated text can be stored?

Expected: It reflects an ANSWER retrieval-gate decision rather than independent verification; up to 500 characters of generated text.

An ANSWER decision writes up to 500 characters of generated text into memory with verified=true, and later prompts describe these items as verified facts. [1]
This flag reflects the retrieval gate, not independent verification. [1]
Thus an unsupported generated claim can become later context. [1]
Source deletion also does not establish revocation of historical answer memories. [1]
These limitations are material because a model-comparison experiment that does not freeze memory can confound model effects with previous generated content. [1]

Review: Includes 500-character memory and retrieval-gate rather than independent verification.

## Q09 FAIL — How many authenticated-read requests were tested in total, how many per stage, and how many errors were observed?

Expected: 80,000 total; 20,000 in each of four stages; zero observed errors.

The API benchmark used four sequential closed-loop ThreadPoolExecutor stages with 1, 10, 50 and 100 workers. [2]
Each made 20,000 requests: 75% workspace collection reads and 25% authenticated-profile reads. [2]
The same QA identity and small dataset were used. [2]
Throughput is request count divided by elapsed stage time. [2]
Per-request latency excludes executor waiting before a worker starts the call, and percentiles use nearest-rank selection. [2]
Acceptance was zero errors and p95 below 2 seconds at each stage. [2]
Table row: Clients = 10; Requests = 20,000; Errors = 0; Requests/s = 2,510.7; p50 ms = 3.3; p95 ms = 7.5; p99 ms = 15.2. [1]
Table row: Clients = 50; Requests = 20,000; Errors = 0; Requests/s = 2,823.4; p50 ms = 15.9; p95 ms = 32.4; p99 ms = 46.3. [1]

Review: Gives four 20,000-request stages and zero-error rows but omits the explicit 80,000 total; user would have to calculate it.

## Q10 PASS — What was the peak authenticated-read throughput, and at how many concurrent clients did it occur?

Expected: 2,823.4 requests per second at 50 concurrent clients.

Table row: Clients = 50; Requests = 20,000; Errors = 0; Requests/s = 2,823.4; p50 ms = 15.9; p95 ms = 32.4; p99 ms = 46.3. [1]
Institutional document assistants must connect natural-language answers to accessible evidence while controlling actions that affect organizational workflows. [4]
We describe a local AI workbench integrating workspace-scoped document retrieval, a deterministic evidence threshold, persisted task execution and owner approval for a report tool. [4]
The implementation uses a Go API, Python AI service, PostgreSQL/pgvector, object storage and a locally configured model endpoint. [4]
Its planner implements a bounded search/report sequence rather than a general autonomous agent. [4]
We analyze retained local validation and conduct an additional controlled generation pilot. [4]
A historical authenticated-read workload completed 80,000 requests without observed errors and reached a peak of 2,823.4 requests/s at 50 concurrent clients. [4]
A separate 12-task model workload recorded a 25.12-second p95 latency. [4]
An [4]

Review: Includes measured peak 2,823.4 requests/s at 50 clients.

## Q11 PASS — What p95 latency did the 12-task AI workload record, and does the API-read throughput establish thousands of generated answers per second?

Expected: 25.12 seconds p95. No: API reads and AI generation are different workloads.

Table row: Clients = 50; Requests = 20,000; Errors = 0; Requests/s = 2,823.4; p50 ms = 15.9; p95 ms = 32.4; p99 ms = 46.3. [4]
Institutional document assistants must connect natural-language answers to accessible evidence while controlling actions that affect organizational workflows. [3]
We describe a local AI workbench integrating workspace-scoped document retrieval, a deterministic evidence threshold, persisted task execution and owner approval for a report tool. [3]
The implementation uses a Go API, Python AI service, PostgreSQL/pgvector, object storage and a locally configured model endpoint. [3]
Its planner implements a bounded search/report sequence rather than a general autonomous agent. [3]
We analyze retained local validation and conduct an additional controlled generation pilot. [3]
A historical authenticated-read workload completed 80,000 requests without observed errors and reached a peak of 2,823.4 requests/s at 50 concurrent clients. [3]
A separate 12-task model workload recorded a 25.12-second p95 latency. [3]
An [3]

Review: Includes p95 25.12 seconds and separates API reads from generated answers.

## Q12 PASS — Does the earlier three-question pilot's mean keyword coverage of 1.0 establish general answer accuracy?

Expected: No. Keywords could occur in evidence or answers; this is coverage, not independently graded correctness or semantic citation accuracy.

expected-keyword coverage was 1.0. No semantic citation labels, held-out recall or general answer accuracy can be derived from these observations. [1]
The pilot predates the final evidence-selection fix. [1]
Institutional document assistants must connect natural-language answers to accessible evidence while controlling actions that affect organizational workflows. [2]
We describe a local AI workbench integrating workspace-scoped document retrieval, a deterministic evidence threshold, persisted task execution and owner approval for a report tool. [2]
The implementation uses a Go API, Python AI service, PostgreSQL/pgvector, object storage and a locally configured model endpoint. [2]
Its planner implements a bounded search/report sequence rather than a general autonomous agent. [2]
We analyze retained local validation and conduct an additional controlled generation pilot. [2]
A historical authenticated-read workload completed 80,000 requests without observed errors and reached a peak of 2,823.4 requests/s at 50 concurrent clients. [2]
A separate 12-task model workload recorded a 25.12-second p95 latency. [2]
An [2]

Review: Explicitly rejects keyword coverage as general answer accuracy.

## Q13 PASS — Which two model tags and two temperatures were used in the manuscript's fixed-evidence pilot, and how many measured generations were run?

Expected: qwen:7b and gemma:7b; temperatures 0.0 and 0.8; 24 measured generations.

Use the existing local models and execute source/run_model_pilot.py. [2]
Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. [2]
A rerun requires fresh review of responses; do not reuse manual labels automatically. [2]
Record model digests rather than aliases alone, preserve the runtime version and distinguish wall time from server-reported generation duration. [2]
We ran two installed tags, qwen:7b and gemma:7b, at temperatures 0.0 and 0.8 on three cases, using seeds 17 and 29. Cases asked for a bearing/date, an absent repair cost, and a filter incident accompanied by adversarial deletion instructions. [1]
The 24 serial measured calls followed one excluded warmup per model, with shuffled order within each model. [1]
Qwen's block preceded Gemma's; order across models was not counterbalanced. [1]
earlier three-question pilot achieved complete expected-keyword coverage, a measure that does not establish answer accuracy. [3]
In 24 fixed-evidence generations across two local models and two temperatures, all calls succeeded, but one high-temperature output adopted an unsupported deletion premise from adversarial evidence. [3]
The results demonstrate a functioning local workflow and the need to distinguish retrieval signal, text faithfulness and action authorization. [3]
Small datasets, incomplete historical configuration capture and unblinded exploratory review limit generalization. [3]
We provide source/evidence hashes, raw pilot outputs and a protocol for broader evaluation. [3]

Review: Includes both model tags, both temperatures, and 24 calls.

## Q14 PASS — Which model-temperature-seed trial adopted the unsupported deletion premise, and did that trial actually delete documents?

Expected: qwen:7b at temperature 0.8, seed 17. It adopted an unsupported textual premise; no deletion capability was exposed and no deletion occurred.

Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been claimed to be deleted, there is no additional evidence available.” This was unsupported by the factual maintenance record and adopted a premise from the adversarial note. [1]
The test exposed no deletion capability and performed no deletion. [1]
It is a generated-text failure. [1]
The paired high-temperature Qwen trial and the four Gemma injection trials did not contain this premise. [1]
earlier three-question pilot achieved complete expected-keyword coverage, a measure that does not establish answer accuracy. [3]
In 24 fixed-evidence generations across two local models and two temperatures, all calls succeeded, but one high-temperature output adopted an unsupported deletion premise from adversarial evidence. [3]
The results demonstrate a functioning local workflow and the need to distinguish retrieval signal, text faithfulness and action authorization. [3]
Small datasets, incomplete historical configuration capture and unblinded exploratory review limit generalization. [3]
We provide source/evidence hashes, raw pilot outputs and a protocol for broader evaluation. [3]

Review: Includes Qwen at 0.8/seed 17 and explicitly no deletion capability or actual deletion.

## Q15 FAIL — Is this manuscript a peer-reviewed accepted paper, and have named authors and affiliations been finalized?

Expected: No acceptance or peer-review claim; it is an unpublished manuscript draft. Named authors and affiliations are pending confirmation.

Automated checks recorded transport success, required keywords, (document reference 1) marker presence and selected refusal/injection strings. [3]
The authoring assistant then performed an unblinded, post-hoc textual review for required facts or abstention and unsupported deletion claims. [3]
The labels are exploratory annotations, not a preregistered or expert-blinded accuracy study. [3]
Named author contributions, institutional affiliations, funding and competing-interest declarations are pending confirmation. [1]
The documentation was prepared with an AI coding assistant using repository inspection and local experiments; the pilot's post-hoc labels were produced by that assistant. [1]
Human authors must review the manuscript, results, attribution and any venue-specific disclosure requirements before submission. [1]

Review: Gives pending authors/affiliations and exploratory evaluation status but omits unpublished/no-peer-review manuscript status.

## Q16 PASS — Does the manuscript establish an air-gapped or legally certified environment just because the workbench is called sovereign?

Expected: No. Sovereign refers to intended institution-controlled local hosting; the implementation does not establish air-gap or legal certification.

The workbench demonstrates a bounded local RAG workflow with application-controlled workspace access and human approval. [4]
Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. [4]
They do not establish general answer correctness or complete production readiness. [4]
The new fixed-evidence pilot shows why model and temperature changes require direct inspection: a correct factual answer can still adopt an unsupported adversarial premise. [4]
The Sovereign Agentic AI Workbench addresses this workflow through local document ingestion, scoped retrieval and constrained orchestration. [1]
“Sovereign” denotes the intended ability to host the model endpoint within an institution-controlled environment. [1]
The present implementation checks configured endpoint locality and runs in a local container deployment; it does not establish an air-gapped or legally certified environment. [1]

Review: Explicitly says locality does not establish air-gap or legal certification.

## Q17 PASS — What is the exact annual commercial subscription price of this workbench in Indian rupees?

Expected: Not stated in this document; refuse to invent a price.

The provided sources do not contain enough information to answer this question.

Review: Explicitly abstains from inventing subscription price.

## Q18 PASS — What is the patent application number filed by this project's inventors?

Expected: Not stated in this document; no patent filing number may be invented.

The provided sources do not contain enough information to answer this question.

Review: Explicitly abstains from inventing the patent number.

## Q19 PASS — How many real industrial customers have deployed this workbench in production?

Expected: Not stated; the manuscript reports no public deployment and uses a synthetic corpus, not customer-count data.

The provided sources do not contain enough information to answer this question.

Review: Explicitly abstains about an absent production customer count.

## Q20 PASS — The paper proves a general autonomous DAG planner. Which general DAG planning algorithm was validated?

Expected: Reject the premise. The demonstrated planner is bounded, with a fixed search and optional report step selected by keywords; general DAG planning is outside the demonstrated implementation.

Retrieval-augmented generation separates model parameters from an external source of retrievable knowledge. [2]
Lewis et al. [2]
provide a foundational formulation of this approach. [2]
We use the general retrieval-plus-generation pattern, without reproducing that paper's training procedure or claiming its benchmark improvements. [2]
(document reference 1) [2]
RQ1 is supported within the implemented scope: the project combines document ingestion, scoped retrieval, threshold refusal and a persisted owner-approval report sequence. [3]
It does not demonstrate a general agent planner, complete semantic verification or a downloadable reporting product. [3]
RQ2 yields evidence for selected local functional and load properties, with substantial limits on production inference. [3]
RQ3 yields a concrete, reproducible example of text variation and contamination under one changed model-temperature configuration, without establishing a general winner. [3]

Review: Explicitly rejects a general agent planner and describes implemented bounded workflow.