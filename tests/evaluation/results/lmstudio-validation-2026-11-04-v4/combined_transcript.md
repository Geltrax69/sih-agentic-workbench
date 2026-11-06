## V01 PASS — Can embeddings from a replacement model be treated as compatible merely because their vector dimensions match?

Expected: No. Changing embedder requires compatible corpus/query embeddings, reindexing and threshold recalibration; equal dimensions alone are insufficient.

A new generator changes conditional text behavior while fixed evidence scores leave the gate unchanged. [1]
An embedding-model replacement changes retrieval geometry and requires compatible corpus/query embeddings, reindexing and threshold recalibration. [1]
Matching vector dimensionality alone does not make embeddings from different models comparable. [1]
The current vector(768) schema additionally requires a migration if the new dimension differs. [1]

Review: Rejects dimension-only compatibility and includes reindexing and threshold recalibration.

## V02 PASS — In what format and location does the report tool currently store its output?

Expected: Markdown stored in a task step.

The current report tool returns Markdown stored in a task step. [1]
A public report-download artifact is not exposed. [1]
The schema and step vocabulary are broader than the active workflow: dynamic model routing, general DAG planning, [1]

Review: Explicitly identifies Markdown stored in a task step.

## V03 PASS — Which PostgreSQL locking clause claims pending ingestion jobs?

Expected: FOR UPDATE ... SKIP LOCKED.

The ingestion service claims one pending PostgreSQL job under FOR UPDATE ... [1]
SKIP LOCKED, processes its object and records success or failure. [1]
Uploads trigger this processing through an internal request. [1]
A durable retry worker for lost triggers or abandoned RUNNING jobs is absent. [1]
Redis participates in health checks but is not a demonstrated job transport in the current execution path. [1]
The task begins in PLANNING, enters RUNNING, executes document_search and proceeds to VERIFYING and COMPLETED. [2]
Report-related keywords add report_generate, which pauses in WAITING_FOR_APPROVAL. [2]
The public decision route resolves workspace scope from the stored task and requires an owner role. [2]
An approval claims RUNNING under a task-row lock before resuming execution, preventing the second concurrent decision in the tested path from executing the same transition. [2]

Review: Includes the actual FOR UPDATE ... SKIP LOCKED clause.

## V04 PASS — How many tables and how many dump bytes were involved in the database restoration count check?

Expected: 19 tables and 53,270-byte dump.

Database restoration compared counts for 19 tables from a 53,270-byte dump and passed, reporting 1.75 seconds for the check. [2]
This is not a measured service RTO or object-store restore. [2]
The fault record passed database pause/resume and API restart checks without quantitative recovery timing. [2]
The recovery check restored a database dump into a scratch database and compared table row counts. [1]
The fault test paused/resumed the database and restarted the API. [1]
These are bounded functional checks rather than a complete disaster-recovery or availability study. [1]

Review: Includes 19 tables and 53,270 dump bytes.

## V05 PASS — How many recent eligible memory items can be added to a non-refused task prompt?

Expected: Up to three.

For non-refused tasks, numbered evidence and up to three recent eligible memory items are sent to the generator. [1]
The task path uses temperature 0.3 and a maximum output of 800 tokens. [1]
The system instruction asks for evidence-only answers, [n] citations and rejection of instructions inside evidence. [1]
Returned source filenames are evidence metadata, [1]

Review: Explicit up-to-three recent eligible memory items.

## V06 PASS — What HTTP statuses did the two concurrent public report-approval decisions return in the recorded test?

Expected: One HTTP 200 and one HTTP 400.

The task begins in PLANNING, enters RUNNING, executes document_search and proceeds to VERIFYING and COMPLETED. [2]
Report-related keywords add report_generate, which pauses in WAITING_FOR_APPROVAL. [2]
The public decision route resolves workspace scope from the stored task and requires an owner role. [2]
An approval claims RUNNING under a task-row lock before resuming execution, preventing the second concurrent decision in the tested path from executing the same transition. [2]
The E2E artifact lists ten passing checks. [1]
In the concurrent approval test, one decision returned HTTP 200 and the other HTTP 400 through the public proxy, and the accepted task completed. [1]
The tested malicious document remained [1]

Review: Includes one HTTP 200 and one HTTP 400 approval decision.

## V07 PASS — With chunking at 400 characters and 100-character overlap, how many chunks and stored characters were produced?

Expected: Six chunks and 1,694 stored characters.

Running the actual chunker over the three demonstration files produced three chunks at 800/100, 800/0, 800/200 and 1,200/100 characters. [1]
All three files fit in one chunk at those sizes, so overlap changes had no effect. [1]
At 400/0 the corpus produced five chunks and 1,394 stored characters; at 400/100 it produced six chunks and 1,694 characters. [1]
The default stored 1,396 characters. [1]

Review: Associates 400/100 with six chunks and 1,694 stored characters.

## V08 PASS — What is the corresponding author's email address?

Expected: Not supplied; corresponding-author contact remains to be completed/pending.

The provided sources do not contain enough information to answer this question.

Review: Explicitly abstains rather than inventing a corresponding-author email.

## V09 FAIL — What is the default number of chunks returned by the manuscript's retrieval query?

Expected: Six.

Running the actual chunker over the three demonstration files produced three chunks at 800/100, 800/0, 800/200 and 1,200/100 characters. [2]
All three files fit in one chunk at those sizes, so overlap changes had no effect. [2]
At 400/0 the corpus produced five chunks and 1,394 stored characters; at 400/100 it produced six chunks and 1,694 characters. [2]
The default stored 1,396 characters. [2]
Ingestion supports text-bearing PDF, DOCX, XLSX, TXT, Markdown and CSV inputs. [3]
The current chunker uses 800-character windows with nominal 100-character overlap and prefers text boundaries where possible. [3]
Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. This is a source configuration, not evidence that the approximate index has been optimally trained or used by the query planner on the tiny corpus. [3]
(document reference 6) [3]

Review: Returns segmentation experiments and storage/chunk settings, not the requested default retrieval limit of six.

## V10 PASS — What is the pump supplier's postal address?

Expected: The document does not supply a pump supplier postal address; explicitly abstain.

The provided sources do not contain enough information to answer this question.

Review: Explicitly abstains rather than inventing a supplier address.