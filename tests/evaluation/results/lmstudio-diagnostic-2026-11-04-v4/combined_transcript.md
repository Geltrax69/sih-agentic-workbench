## H01 PASS — What lists setting is configured for the cosine IVFFlat index?

Expected: lists=100.

Ingestion supports text-bearing PDF, DOCX, XLSX, TXT, Markdown and CSV inputs. [1]
The current chunker uses 800-character windows with nominal 100-character overlap and prefers text boundaries where possible. [1]
Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. This is a source configuration, not evidence that the approximate index has been optimally trained or used by the query planner on the tiny corpus. [1]
(document reference 6) [1]

Review: Explicit lists=100 index setting.

## H02 PASS — Where are original uploaded document bytes stored?

Expected: MinIO stores the uploaded original bytes.

MinIO Python AI service Original uploaded bytes Ingestion; retrieval; task flow Redis [1]
Nginx serves a compiled React frontend and proxies requests to a Go API. [1]
The API authenticates bearer tokens and checks workspace roles before calling an internal Python FastAPI service. [1]
PostgreSQL stores users, memberships, document metadata, chunks, tasks, steps, approvals and memory. [1]
MinIO stores uploaded bytes. [1]
A model adapter [1]

Review: Includes the unambiguous narrative sentence MinIO stores uploaded bytes.

## H03 PASS — What median latency and elapsed time were measured in the 12-task AI run?

Expected: Median 20.55 seconds and elapsed 83.22 seconds.

The 12-task AI run recorded zero errors, elapsed time 83.22 seconds, median 20.55 seconds and p95 25.12 seconds. [2]
Dividing count by elapsed time yields approximately 8.65 tasks/minute for that run. [2]
This is a different workload from the API reads and cannot support thousands of generated answers per second. [2]
Institutional document assistants must connect natural-language answers to accessible evidence while controlling actions that affect organizational workflows. [3]
We describe a local AI workbench integrating workspace-scoped document retrieval, a deterministic evidence threshold, persisted task execution and owner approval for a report tool. [3]
The implementation uses a Go API, Python AI service, PostgreSQL/pgvector, object storage and a locally configured model endpoint. [3]
Its planner implements a bounded search/report sequence rather than a general autonomous agent. [3]
We analyze retained local validation and conduct an additional controlled generation pilot. [3]
A historical authenticated-read workload completed 80,000 requests without observed errors and reached a peak of 2,823.4 requests/s at 50 concurrent clients. [3]
A separate 12-task model workload recorded a 25.12-second p95 latency. [3]
An [3]

Review: Includes 20.55-second median and 83.22-second elapsed time.

## H04 PASS — Which hospital purchased the first commercial deployment?

Expected: No hospital purchaser is identified; explicitly state the information is not supplied.

The provided sources do not contain enough information to answer this question.

Review: Explicitly abstains about an unreported hospital purchaser.

## H05 PASS — Is the reported 1.75-second database restoration check a measured service recovery-time objective?

Expected: No; it is not a measured service RTO or object-store restore.

Database restoration compared counts for 19 tables from a 53,270-byte dump and passed, reporting 1.75 seconds for the check. [1]
This is not a measured service RTO or object-store restore. [1]
The fault record passed database pause/resume and API restart checks without quantitative recovery timing. [1]
The recovery check restored a database dump into a scratch database and compared table row counts. [2]
The fault test paused/resumed the database and restarted the API. [2]
These are bounded functional checks rather than a complete disaster-recovery or availability study. [2]

Review: Explicitly rejects interpreting the 1.75-second check as measured service RTO.

## H06 PASS — What happens to the three historical pilot scores when the strong threshold is raised to 0.70 with weak=0.30, and does that prove better correctness?

Expected: One answer and two warning answers; this replay does not establish improved correctness.

The evidence threshold creates discontinuities. [1]
A best usable score of 0.29 refuses, 0.30 permits a warning answer and 0.45 permits an answer under current settings. [1]
Raising the strong threshold to 0.70 while retaining weak=0.30 would map the three historical pilot scores to one answer and two warning answers. [1]
This is a deterministic replay of recorded scores, not evidence of improved correctness. [1]

Review: Includes one answer, two warnings, and no improved-correctness conclusion.

## H07 FAIL — At 100 concurrent clients, what authenticated-read throughput and p95 latency were reported?

Expected: 2,107.3 requests/s and p95 102.2 milliseconds.

Table row: Clients = 50; Requests = 20,000; Errors = 0; Requests/s = 2,823.4; p50 ms = 15.9; p95 ms = 32.4; p99 ms = 46.3. [1]
Table row: Clients = 10; Requests = 20,000; Errors = 0; Requests/s = 2,510.7; p50 ms = 3.3; p95 ms = 7.5; p99 ms = 15.2. [1]
Table row: Clients = 1; Requests = 20,000; Errors = 0; Requests/s = 139.6; p50 ms = 2.2; p95 ms = 29.0; p99 ms = 75.3. [1]

Review: Returns rows for 50, 10 and 1 clients, not the requested 100-client values; this failure prompted the subsequent row-condition guard.

## H08 PASS — What fraction of API benchmark reads targeted the workspace collection and what fraction targeted authenticated profiles?

Expected: 75 percent workspace collection and 25 percent authenticated profiles.

The API benchmark used four sequential closed-loop ThreadPoolExecutor stages with 1, 10, 50 and 100 workers. [1]
Each made 20,000 requests: 75% workspace collection reads and 25% authenticated-profile reads. [1]
The same QA identity and small dataset were used. [1]
Throughput is request count divided by elapsed stage time. [1]
Per-request latency excludes executor waiting before a worker starts the call, and percentiles use nearest-rank selection. [1]
Acceptance was zero errors and p95 below 2 seconds at each stage. [1]
The workbench demonstrates a bounded local RAG workflow with application-controlled workspace access and human approval. [2]
Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. [2]
They do not establish general answer correctness or complete production readiness. [2]
The new fixed-evidence pilot shows why model and temperature changes require direct inspection: a correct factual answer can still adopt an unsupported adversarial premise. [2]

Review: Includes 75 percent collection reads and 25 percent profile reads.

## H09 PASS — Does the current report tool expose a public downloadable report artifact?

Expected: No. It returns Markdown stored in a task step; a public report-download artifact is not exposed.

The current report tool returns Markdown stored in a task step. [1]
A public report-download artifact is not exposed. [1]
The schema and step vocabulary are broader than the active workflow: dynamic model routing, general DAG planning, [1]

Review: Includes Markdown in a task step and no public download artifact.

## H10 PASS — What parameter counts did local metadata report for qwen:7b and gemma:7b despite their aliases?

Expected: qwen:7b reports 8B and gemma:7b reports 9B.

Qwen's median rose about 14.1% between temperatures while mean output length also rose. [1]
Gemma's median fell about 3.5%. [1]
Small, sequential groups with different output lengths do not support broad causal latency or safety rankings. [1]
Local model metadata also warrants care: qwen:7b reports family qwen2 and 8B, while gemma:7b reports family gemma and 9B. [1]
Full artifact digests in the bundle identify the tested models more reliably than aliases. [1]

Review: Includes actual metadata counts 8B and 9B.

## H11 PASS — How many kilowatt-hours did the experiment consume?

Expected: Energy consumption is not measured/reported; do not invent a value.

The provided sources do not contain enough information to answer this question.

Review: Explicitly abstains from an unmeasured energy value.

## H12 PASS — Which two random seeds were used in the extra fixed-evidence model pilot?

Expected: 17 and 29.

We ran two installed tags, qwen:7b and gemma:7b, at temperatures 0.0 and 0.8 on three cases, using seeds 17 and 29. Cases asked for a bearing/date, an absent repair cost, and a filter incident accompanied by adversarial deletion instructions. [4]
The 24 serial measured calls followed one excluded warmup per model, with shuffled order within each model. [4]
Qwen's block preceded Gemma's; order across models was not counterbalanced. [4]

Review: Includes the actual seeds 17 and 29, not merely a protocol saying two seeds.