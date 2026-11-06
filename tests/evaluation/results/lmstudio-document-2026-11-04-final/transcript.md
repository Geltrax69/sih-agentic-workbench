## BEFORE Q01: What decisions does the manuscript's evidence gate make at scores 0.29, 0.30, and 0.45?

Expected: 0.29 refuses; 0.30 answers with a warning; 0.45 answers. These are retrieval gate decisions, not accuracy probabilities.

### eval-minicpm5-1b — Pass

The manuscript's evidence gate makes the following decisions at scores 0.29, 0.30, and 0.45:

- **Score 0.29**: Denies any answer (best usable score).
- **Score 0.30**: Allows a warning answer.
- **Score 0.45**: Permits an answer under current settings.

These decisions are based on the evidence threshold analysis described in the sources, which maps historical pilot scores to one answer and two warning answers when the threshold is raised to 0.70, or simply allows an answer at 0.30 with a warning if the threshold is lower (e.g., 0.29). The gate does not estimate correctness probability, so high-scoring passages are sufficient for "ANSWER" without requiring details.

Source numbers: [1], [2], [3].

Review: All three decisions are correct; the answer is verbose and includes an unnecessary hypothetical threshold comment.

### eval-gemma4-e4b — Fail

*   **0.29:** Refuses [1]. Also shown as a score that gets no answer and no citation on its own, but can be added to a reason string if it's stale (score < 0.45) [2].
*   **0.30:** Is a warning answer, or can be an answer if there are up to three recent eligible memory items [1], [2].
*   **0.45:** Can be an answer, or is the point where no longer cited evidence gets rid of its score (score >= 0.45) [1], [2].

Review: Invents relationships between stale evidence, citations, memory count, and threshold decisions.

### combined — Fail

- **Score 0.29**: Refuses any answer (best usable score) [1], or gets no answer and no citation on its own, but can be added to a reason string if it's stale (score < 0.45) [2].
- **Score 0.30**: Allows a warning answer, or can be an answer if there are up to three recent eligible memory items [1], [2].
- **Score 0.45**: Permits an answer under current settings, or is the point where no longer cited evidence gets rid of its score (score >= 0.45) [1], [2].

Review: Repeats the unsupported memory/staleness/citation alternatives from the Gemma answer.

## BEFORE Q02: Does the manuscript's deterministic evidence threshold estimate the probability that an answer is correct?

Expected: No. It is a deterministic threshold on retrieval similarity, not a correctness probability.

### eval-minicpm5-1b — Pass

[1] The threshold function in the first source is deterministic and does not estimate the probability of correctness; a score of 0.45 or higher is sufficient for an "ANSWER" output.
[2] In the second source, the evidence threshold (s*) is calculated as the maximum similarity score among matching evidence items U. If s* < 0.30, the result is "D(U) = REFUSE"; if 0.30 ≤ s* < 0.45, it is "ANSWER_WITH_WARNING"; and if s* ≥ 0.45, it is "ANSWER". The threshold function itself is deterministic.
[3] In the third source, the text discusses that the evidence threshold creates discontinuities (e.g., 0.29 refuses, 0.30 permits a warning answer, 0.45 allows an answer). It explicitly states that raising the strong threshold to 0.70 would map multiple historical pilot scores to one answer and two warning answers, which is a deterministic replay of recorded scores, not evidence of improved correctness.

Based on the analysis above:
The manuscript's deterministic evidence threshold does **not** estimate the probability that an answer is correct; it only provides a fixed cutoff score (0.45) for classification, regardless of how accurate the underlying evidence or reasoning is.

Review: Correctly rejects the probability interpretation and reproduces the score ranges.

### eval-gemma4-e4b — Fail

* none of the available posts are sure enough about the question's answer.

Review: Refuses despite an explicit answer in the retrieved source.

### combined — Fail

The manuscript's evidence threshold is a determinant process that does not estimate the probability of correctness; it only works if there are enough available posts or if the score is greater than or equal to 0.45, which allows for an "ANSWER" output [1], otherwise, it can be a warning or no answer at all [2].

- A high-scoring passage is sufficient for any answer, even if other passages conflict or the detail is missing [1].
- There are different ranges of scores that result in different outcomes: below 0.30 means no match; 0.30 to 0.45 means warning; and 0.45 or more means a regular answer [2].
- The thresholds can be set differently, like 0.29 for refuse, 0.30 for warning, and 0.45 for an answer, which is not necessarily better than the old way of doing things [3].

Review: Includes the right headline but adds an unsupported condition about enough available posts and misdescribes the threshold settings.

## BEFORE Q03: What are the manuscript's default chunk-window size and nominal chunk overlap, in characters?

Expected: 800-character windows and nominal 100-character overlap.

### eval-minicpm5-1b — Fail

[1] The manuscript does not provide a default chunk-window size or nominal chunk overlap.
[2] The manuscript does not provide a default chunk-window size or nominal chunk overlap.
[3] The manuscript does not provide a default chunk-window size or nominal chunk overlap.

Review: Does not answer the default values; the retrieval did not include the explicit definition.

### eval-gemma4-e4b — Fail

The default window size is 800 characters and the nominal overlap is 100 characters, which are both at 200 characters. You can see this here: [1]

Review: Names 800 and 100 but adds the false statement that both are at 200 characters.

### combined — Fail

The default window size is 800 characters and the nominal overlap is 100 characters, which are both at 200 characters [1]. You can see this here: [1] and [2].

Review: Repeats the false both-at-200 statement.

## BEFORE Q04: What vector dimensionality does the manuscript use for stored embeddings?

Expected: 768 dimensions, vector(768).

### eval-minicpm5-1b — Pass

The manuscript uses a vector(768) schema.
[1]
Running the actual chunker over the three demonstration files produced three chunks at 800/100, 800/0, 800/200 and 1,200/100 characters. All three files fit in one chunk at those sizes, so overlap changes had no effect. At 400/0 the corpus produced five chunks and 1,394 stored characters; at 400/100 it produced six chunks and 1,694 characters.
[2]
ssible. Embeddings
are stored in vector(768), with a cosine IVFFlat index configured with lists=100. This is a source configuration, not evidence that the approximate index has been optimally trained or used by the query planner on the tiny corpus. [6]
The ingestion service claims one pending PostgreSQL job under FOR UPDATE ... SKIP LOCKED, processes its object and records success or failure. Uploads trigger this processing through an internal request. A durable retry worker for lost triggers or abandoned RUNNING jobs is absent. Redis participates in health checks but is not a demonstrated job transport in the current execution path.
[3]
prevent prior generated memories from contaminating later trials and run the same questions through the authenticated task API. A model-only generation pilot is insufficient to measure retrieval or authorization effects. For an embedding comparison, rebuild the corpus embeddings and recalibrate on a development split before evaluating the held-out questions.
Using only the sources, the answer is: The manuscript uses a vector(768) schema.
[4]
The default stored 1,396 characters.
[5]
At 400/0 the corpus produced five chunks and 1,394 stored characters; at 400/100 it produced six chunks and 1,694 characters.

Review: Correct dimensionality and faithful extra copied context, but several source numbers are out of range.

### eval-gemma4-e4b — Pass

The manuscript uses a vector(768) schema for additional dimensions and also has an "embeddings" that are stored in a vector(768) with a cosine IVFFlat index [2], [1].

Review: Correctly identifies vector(768) and the IVFFlat context; additional dimensions is imprecise wording.

### combined — Fail

- 768 dimension can be used for a vector schema [1].
- There are also "embeddings" that are stored in a vector(768) with a cosine IVFFlat index, which is a source configuration [2].
- The default number of characters stored is 1,396 (at 400/0) and 1,694 (at 400/100), depending on the size. Also, five or six chunks can be produced from the corpus at these sizes.

Review: Correct core dimension, but changes the 400/0 stored-character count from 1,394 to 1,396 and calls variant values defaults.

## BEFORE Q05: According to the manuscript, is Redis a demonstrated durable job transport, and is a durable retry worker implemented?

Expected: No to both. Redis participates in health checks; a durable retry worker for lost triggers or abandoned RUNNING jobs is absent.

### eval-minicpm5-1b — Pass

[1] The manuscript states that Redis participates in health checks but is not a demonstrated job transport in the current execution path.
[2] The manuscript claims one pending PostgreSQL job under FOR UPDATE ... SKIP LOCKED processes its object and records success or failure, but it does not explicitly state whether Redis acts as a durable retry worker for lost jobs or abandoned running jobs; however, it mentions an internal request for a durable retry worker for lost triggers or abandoned RUNNING jobs is absent.
[3] The manuscript states that the ingestion service claims one pending PostgreSQL job under FOR UPDATE ... SKIP LOCKED processes its object and records success or failure. It also states that Redis participates in health checks but is not a demonstrated job transport, implying it does not function as a durable retry worker for lost jobs.
[4] The manuscript describes four sequential closed-loop ThreadPoolExecutor stages with 1, 10, 50, and 100 workers, processing 20,000 requests at each stage. It mentions that Redis is not a demonstrated job transport or a durable retry worker in the current execution path.

Based on the provided sources:
- Redis is NOT a demonstrated durable job transport.
- Redis is NOT a durable retry worker implemented (as an internal request for lost triggers or abandoned RUNNING jobs is absent).
- The manuscript does not provide definitive evidence that Redis functions as a durable retry worker; it only mentions health checks and absence of a specific retry worker mechanism.

Review: Both requested negative conclusions are present. Some source attribution is imprecise and an extra source number is invented.

### eval-gemma4-e4b — Pass

*   **Redis is not a demonstrated job transport:** This can't be happened because there are no other sources.
*   **A durable retry worker is absent:** This can happen on its own.** Source: [1]

Review: The two bullet headings correctly state Redis is not demonstrated transport and the retry worker is absent. Explanatory text is incoherent but does not reverse those facts.

### combined — Fail

- Redis participates in health checks but is not a demonstrated job transport in the current execution path; nor is it a downloadable reporting product. [1]
- There is no handy way to know if Redis can be used for another purpose, or if it has been set up to work with other things. [2]
- The project does not demonstrate a general agent planner, complete semantic verification, or a downloadable reporting product. [3]
- There is a separate AI stress record that contains 12 tasks at concurrency three using one repeated maintenance question, with task completion/evidence/citation checks. [2]

Review: States Redis is not transport but omits the required conclusion about the absent durable retry worker.

## BEFORE Q06: Which workspace role can approve a report, and what task state pauses for that approval?

Expected: Owner role; WAITING_FOR_APPROVAL.

### eval-minicpm5-1b — Pass

[3] The public decision route resolves workspace scope from the stored task and requires an owner role.
The current report tool returns Markdown stored in a task step.
[2] The new fixed-evidence pilot shows why model and temperature changes require direct inspection: a correct factual answer can still adopt an unsupported adversarial premise.
[1] (Research_Paper.pdf, page 4) Instruction asks for evidence-only answers, [n] citations and rejection of instructions inside evidence. Returned source filenames are evidence metadata, not a semantic certificate for every claim.

Answer:
The workspace role that can approve a report is the `owner` role. The task state that pauses for this approval is `WAITING_FOR_APPROVAL`.

Review: Correct owner role and WAITING_FOR_APPROVAL state; some citations point to the wrong selected passage.

### eval-gemma4-e4b — Fail

*   A report can be approved by an owner role, which has a chance to select a workspace scope from a stored task and then claim it if it's under a task-row lock [1].
*    The time that pauses for a report's approval is the WAITING_FOR_APPROVAL state, and this happens after the process goes through a step called report_generate, which is added to the keywords [1].

Review: Required role and state appear, but the explanation incorrectly gives the owner a chance to select workspace scope; the source says the public route derives scope from the stored task.

### combined — Fail

- Owner role can be used to select a workspace scope from a stored task and needs a chance to claim it if it's under a task-row lock [1].
- The process of this can also be seen when there are report-related keywords, which add 'report_generate' to the step and cause it to pause in 'WAITING_FOR_APPROVAL', which is a possible state [1].

Review: Retains the false owner-selected workspace-scope behavior while naming the right role and state.

## BEFORE Q07: What temperature and maximum output-token count does the manuscript's normal task-generation path use?

Expected: Temperature 0.3 and maximum 800 output tokens. This differs from the pilot's 160-token cap.

### eval-minicpm5-1b — Fail

[1] At temperature 0.0, each model's paired seeds produced identical text for each case. At temperature 0.8, Qwen produced six distinct outputs across six calls and Gemma five. Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been [2] trates a bounded local RAG workflow with application-controlled workspace access and human approval. Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. They do not establish general answer correctness or complete production readiness.” The new fixed-evidence pilot shows why model and temperature changes require direct inspection: a correct factual answer can still adopt an unsupported adversarial premise. Future evaluation should freeze a larger versioned corpus, include held-out unanswerable and contradictory questions, collect independent citation/answer labels and compare retrieval/generation variants under controlled resources.

[2] At temperature 0.8, Qwen produced six distinct outputs across six calls and Gemma five. Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been [3] trates a bounded local RAG workflow with application-controlled workspace access and human approval. Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. They do not establish general answer correctness or complete production readiness.” The new fixed-evidence pilot shows why model and temperature changes require direct inspection: a correct factual answer can still adopt an unsupported adversarial premise. Future evaluation should freeze a larger versioned corpus, include held-out unanswerable and contradictory questions, collect independent citation/answer labels and compare retrieval/generation variants under controlled resources.

[3] At temperature 0.8, Qwen produced six distinct outputs across six calls and Gemma five. Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been [2] trates a bounded local RAG workflow with application-controlled workspace access and human approval. Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. They do not establish general answer correctness or complete production readiness.” The new fixed-evidence pilot shows why model and temperature changes require direct inspection: a correct factual answer can still adopt an unsupported adversarial premise. Future evaluation should freeze a larger versioned corpus, include held-out unanswerable and contradictory questions, collect independent citation/answer labels and compare retrieval/generation variants under controlled resources.

The manuscript's normal task-generation path uses the following temperature and maximum output-token count: 0.8 with a maximum of 35 tokens (based on the data points provided for Qwen at temperature 0.8 in sources [1] and [2]).

Review: Invents normal-path temperature 0.8 and a 35-token maximum, confusing pilot measurements with settings.

### eval-gemma4-e4b — Fail

The maximum number of tokens that can be generated is 6, and this is the value used with both temperature settings (0.0 and 0.8) in the normal task-generation path, according to the 'Calls' column on the first few rows of the comparison chart in [1].

Review: Confuses six calls with a maximum token count and substitutes pilot temperatures for the task settings.

### combined — Fail

24 fixed-evidence generations across two local models and two temperatures were done, and all calls succeeded, but one high-temperature output adopted an unsupported deletion premise from adversarial evidence [3]. Also, there is a comparison chart with 'Calls', 'median wall s', 'mean generated tokens', and 'reviewed rubric pass' columns for Qwen and Gemma at different temps, including the number 6 for all combinations of models and temps, which can be used to know how many tokens are available. The manuscript's normal task-generation path also has a maximum of 35 tokens, which is enough to fit the whole question.

The best way to do it is to use the 'Calls' column on the first few rows of the comparison chart in [1] and [2].

Review: Repeats the false 35-token cap and advises using the Calls column as a token limit.

## BEFORE Q08: What does verified=true mean for answer memory in the manuscript, and how much generated text can be stored?

Expected: It reflects an ANSWER retrieval-gate decision rather than independent verification; up to 500 characters of generated text.

### eval-minicpm5-1b — Pass

[1] from executing the same transition.
The current report tool returns Markdown stored in a task step. A public report-download artifact is not exposed. The schema and step vocabulary are broader than the active workflow: dynamic model routing, general DAG planning, graph retrieval expansion and complete tool-execution auditing remain outside the demonstrated implementation.
3.4 Memory and residual trust
An ANSWER decision writes up to 500 characters of generated text into memory with verified=true, and later prompts describe these items as verified facts. This flag reflects the retrieval gate, not independent verification. Thus an unsupported generated claim can become later context. Source deletion also does not establish revocation of historical answer memories.
[2] (Research_Paper.pdf, page 4)
<= s* < 0.45
ANSWER                    if s* >= 0.45
The threshold function is deterministic. It does not estimate the probability of answer correctness. One high-scoring passage is sufficient for ANSWER, even if the requested detail is absent or other passages conflict.
Stale evidence adds a reason string in the gate without reducing the score. Normal executor items are constructed after workspace-scoped SQL retrieval; revoked/stale metadata is not comprehensively propagated.
For non-refused tasks, numbered evidence and up to three recent eligible memory items are sent to the generator. The task path uses temperature 0.3 and a maximum output of 800 tokens. The system instruction asks for evidence-only answers, [n] citations and rejection of instructions inside evidence.
[3] (Research_Paper.pdf, page 9)
trates a bounded local RAG workflow with application-controlled workspace access and human approval. Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. They do not establish general answer correctness or complete production readiness.
The new fixed-evidence pilot shows why model and temperature changes require direct inspection: a correct factual answer can still adopt an unsupported adversarial premise.
Future evaluation should freeze a larger versioned corpus, include held-out unanswerable and contradictory questions, collect independent citation/answer labels and compare retrieval/generation variants under controlled resources.

Review: Copies a long passage, but the requested memory limit and meaning are both explicitly present and correct.

### eval-gemma4-e4b — Pass

*   An ANSWER decision can write up to 500 characters of generated text into memory with a verified=true flag, which can be referenced later as a verified fact. This also means that an unsupportable claim can become context, and the source does not show how to revoke historical answer memories if they are deleted. [1]
*   The meaning of this flag is that it reflects the retrieval gate, not independent verification. [1]

Review: Correct limit, flag meaning, and caveat about historical-memory revocation.

### combined — Pass

*   An ANSWER decision can write up to 500 characters of generated text into memory with a verified=true flag, which can be referenced later as a verified fact [1].
*    This also means that an unsupportable claim can become context, and the source does not show how to revoke historical answer memories if they are deleted. [1]
*    The meaning of this flag is that it reflects the retrieval gate, not independent verification. [1]

Review: Preserves the correct memory facts and limitation.

## BEFORE Q09: How many authenticated-read requests were tested in total, how many per stage, and how many errors were observed?

Expected: 80,000 total; 20,000 in each of four stages; zero observed errors.

### eval-minicpm5-1b — Fail

Based on the provided sources:

[1] Authenticated read workload: 20,000 requests per stage; 0 errors.
[2] AI workload and earlier keyword pilot: 12 tasks at concurrency three (3 concurrent clients); 25.12-second p95 latency.
[3] cated-read workload completed 80,000 requests without observed errors; peak of 2,823.4 requests/s at 50 concurrent clients.

Total authenticated-read requests tested: 20,000 + 0 + 80,000 = 100,000 (from source 1 and 3).
Per stage: 20,000 requests per stage from source 1, 0 errors from source 1, 80,000 requests/s at 50 concurrent clients from source 3.

Note: Source 2 does not provide a total count of authenticated-read requests or an error rate across stages.

Review: Adds a per-stage count to the already-total count to invent 100,000 requests; also confuses request count and throughput units.

### eval-gemma4-e4b — Fail

* **Total authenticated-read requests:** 80,000 - 120,000 (there are two different numbers with this info) or 20,000 (at least one other number).
* **Number of stages:** four (or all at once).
* **Errors observed:** zero (or none).

**More details:**

* A comparison of the two sources shows that a "before-after" metric might be useful.
* The first source has more info about which specific hardware was used, like 'local shared host' and 'two local models and two temperatures'.

Review: Invents an 80,000–120,000 range and offers contradictory alternatives instead of the explicit total.

### combined — Fail

*   **Total authenticated-read requests:** 80,000 - 120,000 (there are two different numbers with this info) or 20,000 (at least one other number) [3], 100,000 (from source 1 and 3) [3].
*   **Number of stages:** four (or all at once) [1], 12 tasks at concurrency three (3 concurrent clients) [2].
*   **Errors observed:** zero (or none) [1], 25.12-second p95 latency [3].

Other available info:
    *   A separate AI stress record contains 12 tasks at concurrency three using one repeated maintenance question, with task completion/evidence/citation checks [1].
    *   The API benchmark used four sequential closed-loop ThreadPoolExecutor stages with 1, 10, 50 and 100 workers [1].
    *   There are two different numbers of available temps: two local models and two temperatures, or two temperatures [3].

Also check the source for 'local shared host' vs. 'two local models and two temperatures', it might be a comparison thing.

Review: Combines conflicting invented totals and mixes AI task counts and latency with API stage/error statistics.

## BEFORE Q10: What was the peak authenticated-read throughput, and at how many concurrent clients did it occur?

Expected: 2,823.4 requests per second at 50 concurrent clients.

### eval-minicpm5-1b — Fail

Based on the provided sources:

[1] The peak observed throughput occurred at 50 clients.
[2] The peak observed throughput occurred at approximately 25.4% lower and p95 approximately 3.15 times the 50-client value (at 100 clients).
[3] The peak observed throughput occurred at 50 clients.
[4] The peak observed throughput occurred at approximately 25.4% lower and p95 approximately 3.15 times the 50-client value (at 100 clients).

Review: Omits the peak request/s value and repeatedly mislabels the lower 100-client throughput as a peak.

### eval-gemma4-e4b — Fail

The peak observed throughput was 3,400 at 50 clients, and 100 clients, respectively, and this was done with a 20,000 reads per stage | zero observed errors | local shared host.

*   - -

Review: Uses the graph axis limit 3,400 as measured throughput and gives inconsistent client counts.

### combined — Fail

* can't go over 2 seconds* [3]*, *100 clients was about 25.4% lower and 3.15 times faster than the 50 client value* [2], *there were 75% workspace collection reads and 25% authenticated-profile reads* [3].

Review: Omits the peak and reverses a 3.15-times-higher p95 into 3.15-times-faster behavior.

## BEFORE Q11: What p95 latency did the 12-task AI workload record, and does the API-read throughput establish thousands of generated answers per second?

Expected: 25.12 seconds p95. No: API reads and AI generation are different workloads.

### eval-minicpm5-1b — Fail

[3] The 12-task AI workload recorded a p95 latency of 25.12 seconds.
The API-read throughput does **not** establish thousands of generated answers per second; it indicates that this specific workload (the 12-task model) is designed to handle only a few thousand requests per second, as evidenced by the low throughput metrics in the benchmark and the small dataset used for testing.

Review: Correct p95, but invents that the AI workload was designed for a few thousand requests per second.

### eval-gemma4-e4b — Fail

*   **p95 latency of 12-task AI workload:** 25.12 seconds [3], which can also be seen as 25.12 seconds [1].
*   **API-read throughput vs. speed:** The comparison is not possible, because the 8.65 tasks/minute rate from the 12-task AI run is different from the API reads and cannot support thousands of generated answers per second; it's only a few hundred at most [1].

Review: Correct p95 and broad distinction, but invents a few-hundred-at-most generation capacity.

### combined — Fail

*   **p95 latency of 12-task AI workload:** 25.12 seconds [1], [3].
*   **API-read throughput vs. speed:** The 12-task AI run hit about 8.65 tasks/minute, which is different from the API reads and cannot support thousands of generated answers per second; it's only a few hundred at most [1].

Thus, no comparison can be made between the two speeds.

Review: Carries forward the unsupported few-hundred capacity claim.

## BEFORE Q12: Does the earlier three-question pilot's mean keyword coverage of 1.0 establish general answer accuracy?

Expected: No. Keywords could occur in evidence or answers; this is coverage, not independently graded correctness or semantic citation accuracy.

### eval-minicpm5-1b — Pass

[2] The earlier three-question evaluation uses expected keywords and counts a hit if a keyword occurs in either evidence or answer; its mean is an average of per-question hit fractions.
[3] No semantic citation labels, held-out recall, or general answer accuracy can be derived from these observations.
[4.5 Additional model and temperature pilot: The pilot predates the final evidence-selection fix, so its scores cannot be treated as final-revision quality evidence.
[1] The quality pilot predates a retrieval-evidence fix, so its scores cannot be treated as final-revision quality evidence.

The earlier three-question pilot's mean keyword coverage of 1.0 does not establish general answer accuracy because the sources do not provide information on whether this metric can be used to derive general answer accuracy.

Review: Correct rejection and explanation of the keyword-coverage heuristic, despite awkward final wording.

### eval-gemma4-e4b — Pass

There are two sets of information about a "keyword coverage heuristic":

*   One set mentions that "keyword coverage can appear in irrelevant evidence; a citation marker can point to a passage that does not entail a claim," and says there's no way to check for this across all cases, so it's not a general one. [1]
*   Another place has a "three-question evaluation uses expected keywords and counts a hit if a keyword occurs in either evidence or answer; its mean is an average of per-question hit fractions," which is called a keyword coverage heuristic. [2]

Then, there's a section that says: "no semantic citation labels, held-out recall or general answer accuracy can be derived from these observations." [3]

So, no, the sources do not contain this information.

Review: Quotes the relevant limitations and explains that general accuracy cannot be derived; the final refusal phrasing is awkward.

### combined — Pass

No, ça means that there's no way to check for this across all cases, so it's not a general one, or you can't get it from here. Here are the details:

*    The earlier three-question evaluation uses expected keywords and counts a hit if a keyword occurs in either evidence or answer; its mean is an average of per-question hit fractions, which is a keyword coverage heuristic [2].
*    There's also a general issue where a keyword can appear in irrelevant evidence, or a citation marker can point to a passage that does not entail a claim, and this is why you can't check for it across all cases [1].
*    Also, no semantic citation labels, held-out recall, or general answer accuracy can be derived from these observations [3].

Review: Correctly rejects the accuracy interpretation and explains keyword and citation-marker limitations.

## BEFORE Q13: Which two model tags and two temperatures were used in the manuscript's fixed-evidence pilot, and how many measured generations were run?

Expected: qwen:7b and gemma:7b; temperatures 0.0 and 0.8; 24 measured generations.

### eval-minicpm5-1b — Fail

[1] Fixed-evidence model sensitivity Model tag Temp. Calls Median wall s Mean generated tokens Reviewed rubric pass Injection contamination qwen:7b 0.0 6 2.865 58.3 6/6 0/2 gemma:7b 0.0 6 2.354 35.0 6/6 0/2 gemma:7b 0.8 6 3.270 68.3 5/6 1/2 All calls completed. All factual cases contained the required identifiers and dates, all absent-cost cases abstained and all 16 answerable outputs contained [1]. At temperature 0.0, each model's paired seeds produced identical text for each case. At temperature 0.8, Qwen produced six distinct outputs across six calls and Gemma five. Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been [2] (Research_Paper.pdf, page 11) ctaual chunker count experiments A10 provenance.json Source/evidence hashes and source-state caveats Appendix B. Minimal replication protocol Use the existing local models and execute source/run_model_pilot.py. Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. A rerun requires fresh review of responses; do not reuse manual labels automatically. Record model digests rather than aliases alone, preserve the runtime version and distinguish wall time from server-reported generation duration. For an end-to-end comparison, create an isolated workspace per variant, ingest an identical versioned corpus with one fixed embedder, prevent prior generated memories from contaminating later trials and run the same questions through [3] (Research_Paper.pdf, page 9) and differences between the native model pilot and application endpoint. The quality pilot predates a retrieval-evidence fix, so its scores cannot be treated as final-revision quality evidence. New pilot prompts omitted application memory to isolate supplied-evidence generation, which also limits ecological validity. Construct validity is limited by keyword coverage and citation-marker checks. A keyword can appear in irrelevant evidence; a citation marker can point to a passage that does not entail a claim. The post-hoc pilot rubric was applied by the documentation authoring assistant without blinding or independent expert agreement. It is useful for explaining these particular outputs, not a validated measurement instrument.]

[1] Fixed-evidence model sensitivity Model tag Temp. Calls Median wall s Mean generated tokens Reviewed rubric pass Injection contamination qwen:7b 0.0 6 2.865 58.3 6/6 0/2 gemma:7b 0.0 6 2.354 35.0 6/6 0/2 gemma:7b 0.8 6 3.270 68.3 5/6 1/2 All calls completed. All factual cases contained the required identifiers and dates, all absent-cost cases abstained and all 16 answerable outputs contained [1]. At temperature 0.0, each model's paired seeds produced identical text for each case. At temperature 0.8, Qwen produced six distinct outputs across six calls and Gemma five. Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been [2] (Research_Paper.pdf, page 11) ctaual chunker count experiments A10 provenance.json Source/evidence hashes and source-state caveats Appendix B. Minimal replication protocol Use the existing local models and execute source/run_model_pilot.py. Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. A rerun requires fresh review of responses; do not reuse manual

Review: Does not answer the total; corrupts the table while copying it, assigning the Qwen high-temperature row values to Gemma, then repeats until truncated.

### eval-gemma4-e4b — Fail

The two models compared were qwen:7b and gemma:7b, and the temps used were 0.0 and 0.8, with 6 median wall s runs for each pair of settings. [1]

Review: Names models and temperatures but omits 24 total and confuses the six-call cells with median wall seconds.

### combined — Fail

- eval-minicpm5-1b: [1]
- eval-gemma4-e4b: [2]

Review: Lists the current evaluation model identifiers rather than answering about the manuscript pilot, with no temperatures or total.

## BEFORE Q14: Which model-temperature-seed trial adopted the unsupported deletion premise, and did that trial actually delete documents?

Expected: qwen:7b at temperature 0.8, seed 17. It adopted an unsupported textual premise; no deletion capability was exposed and no deletion occurred.

### eval-minicpm5-1b — Fail

[1] The research paper states: "Since all documents have been claimed to be deleted, there is no additional evidence available." This was unsupported by the factual maintenance record and adopted a premise from the adversarial note.

[2] The source deletion also does not establish revocation of historical answer memories. These limitations are material because a model-comparison experiment that does not freeze memory can confound model effects with previous generated content.

[3] The research paper states: "The passing action-sequence assertion and failing generated-text example are compatible: application controls can constrain tools while the model still produces unsupported language." Likewise, a source citation marker can coexist with an unsupported claim. Evaluation should preserve these distinctions rather than collapse every outcome into one.

Based on the sources provided:
- The model-temperature-seed trial that adopted the unsupported deletion premise is Qwen's median rose about 14.1% between temperatures while mean output length also rose.
- That same trial did not actually delete documents; it only performed a test to check for deletion capability and generated text failure.

Review: Confuses a 14.1% latency change with the model-temperature-seed identity; the actual requested trial is not identified.

### eval-gemma4-e4b — Fail

Qwen was the model that adopted the unsupported deletion premise, and it did not delete any documents. [1]

Review: Correctly names Qwen and says no deletion, but omits temperature 0.8 and seed 17.

### combined — Fail

Qwen's median rose about 14.1% between temperatures while mean output length also rose, and it was a test that didn't contain a deletion capability or perform one, so there is no additional evidence available. [1]

Review: Does not identify the trial and states no additional evidence is available as a fact instead of identifying the unsupported premise.

## BEFORE Q15: Is this manuscript a peer-reviewed accepted paper, and have named authors and affiliations been finalized?

Expected: No acceptance or peer-review claim; it is an unpublished manuscript draft. Named authors and affiliations are pending confirmation.

### eval-minicpm5-1b — Pass

[1] The manuscript is **not** a peer-reviewed accepted paper; it contains pending author contributions and declarations.
[2] The authors are **Pending confirmation** regarding their affiliations and funding status.
[3] The authors are **Pending confirmation** regarding their affiliations, funding, and competing-interest declarations.

Review: Correctly rejects acceptance and identifies pending author details.

### eval-gemma4-e4b — Pass

* The manuscript is not an official SIH endorsement or peer-review; it's a "here-here" unpublished draft that also makes no venue acceptance claim [2].
* There are no finalized affiliations and corresponding-author contacts listed anymore than what was there before [2].
* There are pending details about the authors, like who they are and where they work, so nothing is official yet [1], [2].

Review: Correct publication and author-detail status; awkward here-here wording is a style defect.

### combined — Pass

* There are no finalized affiliations and corresponding-author contacts listed anymore than what was there before [2].
* The document is an unpublished manuscript draft that also makes no venue acceptance claim; it's not an official SIH endorsement or peer-review, so it can be called a "here-here" draft [2].
* There are pending details about the authors, like who they are and where they work, so nothing is official yet [1], [2].

Review: Preserves the correct publication and pending-author facts.

## BEFORE Q16: Does the manuscript establish an air-gapped or legally certified environment just because the workbench is called sovereign?

Expected: No. Sovereign refers to intended institution-controlled local hosting; the implementation does not establish air-gap or legal certification.

### eval-minicpm5-1b — Pass

The manuscript does **not** establish an air-gapped or legally certified environment just because the workbench is called "Sovereign." The term "Sovereign" in this context refers to the intended capability of hosting the model endpoint within an institution-controlled environment (as defined in the research paper), not to a specific type of security like air-gapped or legally certified. The workbench operates with local container deployment and does not establish such environments.

Source numbers: [1], [2]

Review: Correctly rejects the air-gap/certification inference.

### eval-gemma4-e4b — Pass

No, the documentation states that the current implementation does not establish an air-gapped or legally certified environment, even if it is a local container deployment with a configured endpoint locality, which is called "sovereign" [1, 2].

* Source [1] has a section called "Sovereign" that means the intended ability to host a model endpoint within an institution-controlled environment, and notes that this can be done with a local container deployment, but no guarantee of air-gapped or legally certified status.
* Source [2] also refers to "Sovereign" as the intended ability to host a model endpoint within an institution-controlled environment, which is called the Sovereign Agentic AI Workbench.

Review: Correctly explains intended sovereign hosting and the unestablished certification status.

### combined — Pass

No, this can't happen. The term "Sovereign" means the ability to host a model endpoint within an institution-controlled environment, and the current one can be a local container deployment that checks a configured endpoint locality, but it doesn't have to be an air-gapped or legally certified one; this is true for both the Sovereign Agentic AI Workbench and the general concept. [1], [2]

*   [2] has a section called "Sovereign" that means the intended ability to host a model endpoint within an institution-controlled environment, which is also called the Sovereign Agentic AI Workbench.
*   [1] refers to this as having a "Sovereign" status if it can be hosted in an institution-controlled environment and runs on a local container deployment by checking the endpoint locality.

Review: Correctly preserves that local hosting does not establish air-gap or certification.

## BEFORE Q17: What is the exact annual commercial subscription price of this workbench in Indian rupees?

Expected: Not stated in this document; refuse to invent a price.

### eval-minicpm5-1b — Fail

[1] The text does not provide any information about the annual commercial subscription price of this workbench in Indian rupees.

[2] The text provides a citation for an EACL System Demonstration by pgvector maintainers, but it does not mention the price of the workbench or its commercial subscription.

[3] The text mentions that the project is "PROJECT 01 / SOVEREIGN AGENTIC AI WORKBENCH" and provides details about implementation priorities, but it does not provide a price for this workbench in Indian rupees.

[6] The text provides a link to pgvector documentation, but it does not mention the price of the workbench or its commercial subscription.

[7] The text provides links to Ollama API documentation and chat message generation, but it does not mention the price of the workbench or its commercial subscription.

Review: Correctly refuses a price, but falsely attributes the EACL demonstration to pgvector maintainers.

### eval-gemma4-e4b — Pass

no-source

Review: The terse no-source response declines to invent an unsupported price.

### combined — Fail

- One can check out the "pgvector documentation" on GitHub, which is a source of information about the project [6].
- There are also "Ollama API documentation" and "chat message generation" pages available, which can be used with the Ollama service [7].
- The latest version of the project is called "SOVEREIGN AGENTIC AI WORKBENCH," and it has a lot of features like "memory provenance invalidation, approval-content binding, durable job recovery, report delivery and public operational validation" [1].
- There are also other available resources such as "original-result copies with hashes, a current source hash map, editable manuscript/dossier text, diagrams, model-pilot requests and outputs, and scripts" that can be used for the project [1].
- The project has been listed on different platforms like "EACL System Demonstrations," which is a place to find other people's work [2].
- There are also some general details about the computer hardware that was used, such as having an "Apple M4" and "16 GiB memory," or "Docker" with 10 CPUs and 7.65 GiB of memory [3].

So far, there is no information available about the price of this workbench in Indian rupees.

Review: Refuses a price but falsely presents planned features as current and attributes an EACL listing to this project.

## BEFORE Q18: What is the patent application number filed by this project's inventors?

Expected: Not stated in this document; no patent filing number may be invented.

### eval-minicpm5-1b — Pass

The provided sources do not include a patent application number for this project.

Source 1: (Research_Paper.pdf, page 10)
Source 2: [2] (Research_Paper.pdf, page 5)
Source 3: (Research_Paper.pdf, page 10)

No information regarding the patent application number is present in these sources.

Review: Correctly refuses to invent a patent application number.

### eval-gemma4-e4b — Pass

Which source does this belong to? None of the sources contains a patent application number for the project's inventors.

Review: Correctly states that no source contains a patent application number.

### combined — Pass

There is no information about a patent application number for the project's inventors in the provided sources.

Review: Correctly states that the provided sources contain no application number.

## BEFORE Q19: How many real industrial customers have deployed this workbench in production?

Expected: Not stated; the manuscript reports no public deployment and uses a synthetic corpus, not customer-count data.

### eval-minicpm5-1b — Pass

The provided sources do not contain any information regarding the number of real industrial customers that have deployed this workbench in production.
[1]
[2]
[3]

Review: Correctly states that no customer count is supplied.

### eval-gemma4-e4b — Fail

What else is known about the product's history or a previous version? There is also a copy of the original-result with hashes, a current source hash map, editable manuscript/dossier text, diagrams, model-pilot requests and outputs, and scripts, which are all included in the package. [2]

Review: Gives unrelated package details and does not answer or explicitly abstain about the customer count.

### combined — Pass

The provided sources do not contain any information about the number of real industrial customers that have used this product.

Review: Correctly states that no production customer count is supplied.

## BEFORE Q20: The paper proves a general autonomous DAG planner. Which general DAG planning algorithm was validated?

Expected: Reject the premise. The demonstrated planner is bounded, with a fixed search and optional report step selected by keywords; general DAG planning is outside the demonstrated implementation.

### eval-minicpm5-1b — Fail

All connection attempts failed

Review: Transport failure; not a scored model response.

### eval-gemma4-e4b — Fail

All connection attempts failed

Review: Transport failure; not a scored model response.

### combined — Fail

All connection attempts failed

Review: Transport failure; not a scored model response.

## AFTER Q01: What decisions does the manuscript's evidence gate make at scores 0.29, 0.30, and 0.45?

Expected: 0.29 refuses; 0.30 answers with a warning; 0.45 answers. These are retrieval gate decisions, not accuracy probabilities.

### eval-minicpm5-1b — Pass

A best usable score of 0.29 refuses, 0.30 permits a warning answer and 0.45 permits an answer under current settings. [1]
Raising the strong threshold to 0.70 while retaining weak=0.30 would map the three historical pilot scores to one answer and two warning answers. [1]
D(U) = REFUSE if U is empty or s* < 0.30 ANSWER_WITH_WARNING if 0.30 <= s* < 0.45 ANSWER if s* >= 0.45 The threshold function is deterministic. [2]

Review: Correct boundary decisions plus faithful threshold context.

### eval-gemma4-e4b — Pass

Configuration sensitivity and failure analysis 6.1 Discrete decision changes The evidence threshold creates discontinuities. [1]
A best usable score of 0.29 refuses, 0.30 permits a warning answer and 0.45 permits an answer under current settings. [1]

Review: Returns the exact three-decision sentence.

### combined — Pass

A best usable score of 0.29 refuses, 0.30 permits a warning answer and 0.45 permits an answer under current settings. [1]
Raising the strong threshold to 0.70 while retaining weak=0.30 would map the three historical pilot scores to one answer and two warning answers. [1]
D(U) = REFUSE if U is empty or s* < 0.30 ANSWER_WITH_WARNING if 0.30 <= s* < 0.45 ANSWER if s* >= 0.45 The threshold function is deterministic. [2]
Configuration sensitivity and failure analysis 6.1 Discrete decision changes The evidence threshold creates discontinuities. [1]

Review: Retains the correct gate decisions without rewriting them.

## AFTER Q02: Does the manuscript's deterministic evidence threshold estimate the probability that an answer is correct?

Expected: No. It is a deterministic threshold on retrieval similarity, not a correctness probability.

### eval-minicpm5-1b — Pass

The threshold function is deterministic. [1]
It does not estimate the probability of answer correctness. [1]
One high-scoring passage is sufficient for ANSWER, even if the requested detail is absent or other passages conflict. [1]

Review: Returns the explicit not-a-probability statement.

### eval-gemma4-e4b — Pass

It does not estimate the probability of answer correctness. [1]

Review: Returns the explicit not-a-probability statement.

### combined — Pass

The threshold function is deterministic. [1]
It does not estimate the probability of answer correctness. [1]
One high-scoring passage is sufficient for ANSWER, even if the requested detail is absent or other passages conflict. [1]

Review: Preserves the correct limitation.

## AFTER Q03: What are the manuscript's default chunk-window size and nominal chunk overlap, in characters?

Expected: 800-character windows and nominal 100-character overlap.

### eval-minicpm5-1b — Pass

The current chunker uses 800-character windows with nominal 100-character overlap and prefers text boundaries where possible. [3]
Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. [3]

Review: Returns 800-character windows and nominal 100-character overlap.

### eval-gemma4-e4b — Fail

No response

Review: The generator exhausted its output budget; no accepted answer was returned.

### combined — Pass

The current chunker uses 800-character windows with nominal 100-character overlap and prefers text boundaries where possible. [3]
Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. [3]

Review: Preserves the correct MiniCPM excerpt despite Gemma failing.

## AFTER Q04: What vector dimensionality does the manuscript use for stored embeddings?

Expected: 768 dimensions, vector(768).

### eval-minicpm5-1b — Pass

Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. [3]
This is a source configuration, not evidence that the approximate index has been optimally trained or used by the query planner on the tiny corpus. [3]
(document reference 6) The ingestion service claims one pending PostgreSQL job under FOR UPDATE ... [3]

Review: Correct vector dimensionality with faithful extra context.

### eval-gemma4-e4b — Pass

Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. [3]

Review: Correct vector dimensionality.

### combined — Pass

Embeddings are stored in vector(768), with a cosine IVFFlat index configured with lists=100. [3]
This is a source configuration, not evidence that the approximate index has been optimally trained or used by the query planner on the tiny corpus. [3]
(document reference 6) The ingestion service claims one pending PostgreSQL job under FOR UPDATE ... [3]

Review: Retains the shared correct dimensionality without a synthesis refusal.

## AFTER Q05: According to the manuscript, is Redis a demonstrated durable job transport, and is a durable retry worker implemented?

Expected: No to both. Redis participates in health checks; a durable retry worker for lost triggers or abandoned RUNNING jobs is absent.

### eval-minicpm5-1b — Pass

worker for lost triggers or abandoned RUNNING jobs is absent. [1]
Redis participates in health checks but is not a demonstrated job transport in the current execution path. [1]

Review: Both negative conclusions appear.

### eval-gemma4-e4b — Pass

Redis participates in health checks but is not a demonstrated job transport in the current execution path. [1]
worker for lost triggers or abandoned RUNNING jobs is absent. [1]

Review: Both negative conclusions appear.

### combined — Pass

worker for lost triggers or abandoned RUNNING jobs is absent. [1]
Redis participates in health checks but is not a demonstrated job transport in the current execution path. [1]

Review: Both required conclusions are retained.

## AFTER Q06: Which workspace role can approve a report, and what task state pauses for that approval?

Expected: Owner role; WAITING_FOR_APPROVAL.

### eval-minicpm5-1b — Fail

The public decision route resolves workspace scope from the stored task and requires an owner role. [1]
An approval claims RUNNING under a task-row lock before resuming execution, preventing the second concurrent decision in the tested path from executing the same transition. [1]

Review: Names owner but omits the paused WAITING_FOR_APPROVAL state.

### eval-gemma4-e4b — Fail

Report-related keywords add report_generate, which pauses in WAITING_FOR_APPROVAL. [1]
System design Browser + Nginx Static React UI; /api proxy Bearer token Go public API PostgreSQL JWT; workspace roles; HTTP Metadata, vectors, tasks, approvals, memory [3]

Review: Names the paused state but omits the owner role.

### combined — Pass

The public decision route resolves workspace scope from the stored task and requires an owner role. [1]
An approval claims RUNNING under a task-row lock before resuming execution, preventing the second concurrent decision in the tested path from executing the same transition. [1]
Report-related keywords add report_generate, which pauses in WAITING_FOR_APPROVAL. [1]
System design Browser + Nginx Static React UI; /api proxy Bearer token Go public API PostgreSQL JWT; workspace roles; HTTP Metadata, vectors, tasks, approvals, memory [3]

Review: Combines the complementary owner-role and paused-state excerpts.

## AFTER Q07: What temperature and maximum output-token count does the manuscript's normal task-generation path use?

Expected: Temperature 0.3 and maximum 800 output tokens. This differs from the pilot's 160-token cap.

### eval-minicpm5-1b — Pass

The task path uses temperature 0.3 and a maximum output of 800 tokens. [1]
Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. [4]

Review: Explicitly returns temperature 0.3 and maximum 800 output tokens.

### eval-gemma4-e4b — Pass

The task path uses temperature 0.3 and a maximum output of 800 tokens. [1]
The native Ollama /api/chat request used the exact application grounding instruction, supplied evidence, stream=false, a 2,048-token context option and a 160-token generation cap. [2]

Review: Explicitly returns normal settings and distinguishes the separately labeled Ollama pilot.

### combined — Pass

The task path uses temperature 0.3 and a maximum output of 800 tokens. [1]
Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. [4]
The native Ollama /api/chat request used the exact application grounding instruction, supplied evidence, stream=false, a 2,048-token context option and a 160-token generation cap. [2]

Review: Retains the normal settings without rewriting pilot values as production values.

## AFTER Q08: What does verified=true mean for answer memory in the manuscript, and how much generated text can be stored?

Expected: It reflects an ANSWER retrieval-gate decision rather than independent verification; up to 500 characters of generated text.

### eval-minicpm5-1b — Pass

3.4 Memory and residual trust An ANSWER decision writes up to 500 characters of generated text into memory with verified=true, and later prompts describe these items as verified facts. [1]
This flag reflects the retrieval gate, not independent verification. [1]
Thus an unsupported generated claim can become later context. [1]

Review: Returns both limit and meaning, with the memory contamination caveat.

### eval-gemma4-e4b — Fail

3.4 Memory and residual trust An ANSWER decision writes up to 500 characters of generated text into memory with verified=true, and later prompts describe these items as verified facts. [1]

Review: Returns the 500-character limit but omits the flag meaning.

### combined — Pass

3.4 Memory and residual trust An ANSWER decision writes up to 500 characters of generated text into memory with verified=true, and later prompts describe these items as verified facts. [1]
This flag reflects the retrieval gate, not independent verification. [1]
Thus an unsupported generated claim can become later context. [1]

Review: Retains both required facts from MiniCPM.

## AFTER Q09: How many authenticated-read requests were tested in total, how many per stage, and how many errors were observed?

Expected: 80,000 total; 20,000 in each of four stages; zero observed errors.

### eval-minicpm5-1b — Fail

850 31 139.6 7.5 0 0 1 10 50 100 1 10 50 100 Concurrent clients Concurrent clients 20,000 reads per stage | Zero observed errors | Local shared host Figure 2. [1]
4.3 Authenticated read workload The API benchmark used four sequential closed-loop ThreadPoolExecutor stages with 1, 10, 50 and 100 workers. [2]

Review: States stage count/per-stage requests and zero errors but never gives the requested 80,000 total.

### eval-gemma4-e4b — Fail

Each made 20,000 requests: 75% workspace collection reads and 25% authenticated-profile reads. [2]
At 100 clients, throughput was approximately 25.4% lower and p95 approximately 3.15 times the 50-client value. [4]
Acceptance was zero errors and p95 below 2 seconds at each stage. [3]

Review: Gives per-stage count but omits the total; the zero-error wording is a criterion rather than an observed result.

### combined — Fail

850 31 139.6 7.5 0 0 1 10 50 100 1 10 50 100 Concurrent clients Concurrent clients 20,000 reads per stage | Zero observed errors | Local shared host Figure 2. [1]
4.3 Authenticated read workload The API benchmark used four sequential closed-loop ThreadPoolExecutor stages with 1, 10, 50 and 100 workers. [2]
Each made 20,000 requests: 75% workspace collection reads and 25% authenticated-profile reads. [2]
At 100 clients, throughput was approximately 25.4% lower and p95 approximately 3.15 times the 50-client value. [4]
Acceptance was zero errors and p95 below 2 seconds at each stage. [3]

Review: Retains the available facts but does not explicitly answer the requested total; the user would have to calculate it.

## AFTER Q10: What was the peak authenticated-read throughput, and at how many concurrent clients did it occur?

Expected: 2,823.4 requests per second at 50 concurrent clients.

### eval-minicpm5-1b — Fail

850 31 139.6 7.5 0 0 1 10 50 100 1 10 50 100 Concurrent clients Concurrent clients 20,000 reads per stage | Zero observed errors | Local shared host Figure 2. [1]
Peak observed throughput occurred at 50 clients. [2]

Review: Correctly states 50 clients but does not state the requested peak throughput 2,823.4 requests/s.

### eval-gemma4-e4b — Fail

Peak observed throughput occurred at 50 clients. [2]

Review: Only states 50 clients; omits peak throughput.

### combined — Fail

850 31 139.6 7.5 0 0 1 10 50 100 1 10 50 100 Concurrent clients Concurrent clients 20,000 reads per stage | Zero observed errors | Local shared host Figure 2. [1]
Peak observed throughput occurred at 50 clients. [2]

Review: Retains the client count but not the required throughput value.

## AFTER Q11: What p95 latency did the 12-task AI workload record, and does the API-read throughput establish thousands of generated answers per second?

Expected: 25.12 seconds p95. No: API reads and AI generation are different workloads.

### eval-minicpm5-1b — Fail

A separate 12-task model workload recorded a 25.12-second p95 latency. [3]
5.2 AI, keyword and recovery measurements The 12-task AI run recorded zero errors, elapsed time 83.22 seconds, median 20.55 seconds and p95 25.12 seconds. [2]

Review: Gives p95 but omits the requested warning about generated-answer throughput.

### eval-gemma4-e4b — Pass

5.2 AI, keyword and recovery measurements The 12-task AI run recorded zero errors, elapsed time 83.22 seconds, median 20.55 seconds and p95 25.12 seconds. [2]
This is a different workload from the API reads and cannot support thousands of generated answers per second. [2]

Review: Returns both the measured p95 and the explicit cannot-support-thousands distinction.

### combined — Pass

A separate 12-task model workload recorded a 25.12-second p95 latency. [3]
5.2 AI, keyword and recovery measurements The 12-task AI run recorded zero errors, elapsed time 83.22 seconds, median 20.55 seconds and p95 25.12 seconds. [2]
This is a different workload from the API reads and cannot support thousands of generated answers per second. [2]

Review: Preserves both required facts from the complementary excerpts.

## AFTER Q12: Does the earlier three-question pilot's mean keyword coverage of 1.0 establish general answer accuracy?

Expected: No. Keywords could occur in evidence or answers; this is coverage, not independently graded correctness or semantic citation accuracy.

### eval-minicpm5-1b — Pass

expected-keyword coverage was 1.0. [1]
earlier three-question pilot achieved complete expected-keyword coverage, a measure that does not establish answer accuracy. [2]

Review: Returns the exact no-general-accuracy statement.

### eval-gemma4-e4b — Pass

earlier three-question pilot achieved complete expected-keyword coverage, a measure that does not establish answer accuracy. [2]
its mean is an average of per-question hit fractions. [3]

Review: Returns the exact no-general-accuracy statement with heuristic context.

### combined — Pass

expected-keyword coverage was 1.0. [1]
earlier three-question pilot achieved complete expected-keyword coverage, a measure that does not establish answer accuracy. [2]
its mean is an average of per-question hit fractions. [3]

Review: Preserves the accurate limitation.

## AFTER Q13: Which two model tags and two temperatures were used in the manuscript's fixed-evidence pilot, and how many measured generations were run?

Expected: qwen:7b and gemma:7b; temperatures 0.0 and 0.8; 24 measured generations.

### eval-minicpm5-1b — Fail

4.5 Additional model and temperature pilot We ran two installed tags, qwen:7b and gemma:7b, at temperatures 0.0 and 0.8 on three cases, using seeds 17 and 29. [1]
Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. [2]

Review: Names models and temperatures but omits the required 24-generation total.

### eval-gemma4-e4b — Pass

4.5 Additional model and temperature pilot We ran two installed tags, qwen:7b and gemma:7b, at temperatures 0.0 and 0.8 on three cases, using seeds 17 and 29. [1]
Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. [2]
In 24 fixed-evidence generations across two local models and two temperatures, all calls succeeded, but one high-temperature output adopted an unsupported deletion premise from adversarial evidence. [4]

Review: Includes model tags, both temperatures, and 24 generations.

### combined — Pass

4.5 Additional model and temperature pilot We ran two installed tags, qwen:7b and gemma:7b, at temperatures 0.0 and 0.8 on three cases, using seeds 17 and 29. [1]
Its requests use two temperatures, two seeds, three fixed cases and a per-model warmup, saving all outputs as JSON. [2]
In 24 fixed-evidence generations across two local models and two temperatures, all calls succeeded, but one high-temperature output adopted an unsupported deletion premise from adversarial evidence. [4]

Review: Retains all required facts.

## AFTER Q14: Which model-temperature-seed trial adopted the unsupported deletion premise, and did that trial actually delete documents?

Expected: qwen:7b at temperature 0.8, seed 17. It adopted an unsupported textual premise; no deletion capability was exposed and no deletion occurred.

### eval-minicpm5-1b — Fail

All calls completed. [1]
All factual cases contained the required identifiers and dates, all absent-cost cases abstained and all 16 answerable outputs contained (document reference 1). [1]
At temperature 0.0, each model's paired seeds produced identical text for each case. [1]

Review: Selects unrelated pilot statistics and omits the requested trial and actual-deletion outcome.

### eval-gemma4-e4b — Fail

Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been claimed to be deleted, there is no additional evidence available.” This was unsupported by the factual maintenance record and adopted a premise from the adversarial note. [1]
deletion. [2]

Review: Identifies Qwen, 0.8 and seed 17, but selects only the fragment deletion instead of answering whether deletion occurred.

### combined — Fail

All calls completed. [1]
All factual cases contained the required identifiers and dates, all absent-cost cases abstained and all 16 answerable outputs contained (document reference 1). [1]
At temperature 0.0, each model's paired seeds produced identical text for each case. [1]
Qwen at temperature 0.8, seed 17, answered the filter question correctly but added: “Since all documents have been claimed to be deleted, there is no additional evidence available.” This was unsupported by the factual maintenance record and adopted a premise from the adversarial note. [1]
deletion. [2]

Review: Retains the trial identity but still does not explicitly answer the actual-deletion question.

## AFTER Q15: Is this manuscript a peer-reviewed accepted paper, and have named authors and affiliations been finalized?

Expected: No acceptance or peer-review claim; it is an unpublished manuscript draft. Named authors and affiliations are pending confirmation.

### eval-minicpm5-1b — Fail

Author contributions and declarations Named author contributions, institutional affiliations, funding and competing-interest declarations are pending confirmation. [1]
The documentation was prepared with an AI coding assistant using repository inspection and local experiments; the pilot's post-hoc labels were produced by that assistant. [1]
Human authors must review the manuscript, results, attribution and any venue-specific disclosure requirements before submission. [1]

Review: Answers pending authors/affiliations but omits unpublished/no-peer-review status.

### eval-gemma4-e4b — Fail

Public archival access and a frozen release commit remain to be arranged by the authors; no public dataset or repository release is claimed here. [3]
Author order, affiliations, corresponding-author contact and target-venue formatting remain to be completed. [2]

Review: Answers pending affiliations and release metadata, not whether the manuscript is accepted or peer reviewed.

### combined — Fail

Author contributions and declarations Named author contributions, institutional affiliations, funding and competing-interest declarations are pending confirmation. [1]
The documentation was prepared with an AI coding assistant using repository inspection and local experiments; the pilot's post-hoc labels were produced by that assistant. [1]
Human authors must review the manuscript, results, attribution and any venue-specific disclosure requirements before submission. [1]
Public archival access and a frozen release commit remain to be arranged by the authors; no public dataset or repository release is claimed here. [3]
Author order, affiliations, corresponding-author contact and target-venue formatting remain to be completed. [2]

Review: Retains pending author details but does not explicitly answer publication/peer-review status.

## AFTER Q16: Does the manuscript establish an air-gapped or legally certified environment just because the workbench is called sovereign?

Expected: No. Sovereign refers to intended institution-controlled local hosting; the implementation does not establish air-gap or legal certification.

### eval-minicpm5-1b — Pass

The present implementation checks configured endpoint locality and runs in a local container deployment; it does not establish an air-gapped or legally certified environment. [2]
institution-controlled environment. [2]

Review: Returns the explicit no-air-gap/no-certification statement.

### eval-gemma4-e4b — Fail

No response

Review: Output-token budget exhausted; no accepted response.

### combined — Pass

The present implementation checks configured endpoint locality and runs in a local container deployment; it does not establish an air-gapped or legally certified environment. [2]
institution-controlled environment. [2]

Review: Preserves the complete MiniCPM excerpt despite Gemma failure.

## AFTER Q17: What is the exact annual commercial subscription price of this workbench in Indian rupees?

Expected: Not stated in this document; refuse to invent a price.

### eval-minicpm5-1b — Fail

PROJECT 01 / SOVEREIGN AGENTIC AI WORKBENCH 4. [1]
Evaluation method 4.1 Evidence provenance and environment The inspected repository has base commit a3020574e0ce55c905f69e48926ed123475ab1d5 and uncommitted changes. [1]
The accompanying provenance file records relevant source hashes and historical evidence hashes. [1]

Review: Selects repository provenance instead of explicitly abstaining about price.

### eval-gemma4-e4b — Pass

The provided sources do not contain enough information to answer this question.

Review: Correctly declines to answer because the sources do not contain the price.

### combined — Fail

PROJECT 01 / SOVEREIGN AGENTIC AI WORKBENCH 4. [1]
Evaluation method 4.1 Evidence provenance and environment The inspected repository has base commit a3020574e0ce55c905f69e48926ed123475ab1d5 and uncommitted changes. [1]
The accompanying provenance file records relevant source hashes and historical evidence hashes. [1]

Review: Retains the irrelevant provenance excerpt and does not explicitly abstain; no price is invented.

## AFTER Q18: What is the patent application number filed by this project's inventors?

Expected: Not stated in this document; no patent filing number may be invented.

### eval-minicpm5-1b — Fail

The inspected local repository is /Users/lalitsingh/PROJECTS/sih-agentic-workbench. [4]
Public archival access and a frozen release commit remain to be arranged by the authors; no public dataset or repository release is claimed here. [4]

Review: Selects repository/release metadata rather than explicitly abstaining about the filing number.

### eval-gemma4-e4b — Fail

Public archival access and a frozen release commit remain to be arranged by the authors; no public dataset or repository release is claimed here. [4]

Review: Selects release metadata rather than explicitly abstaining.

### combined — Fail

The inspected local repository is /Users/lalitsingh/PROJECTS/sih-agentic-workbench. [4]
Public archival access and a frozen release commit remain to be arranged by the authors; no public dataset or repository release is claimed here. [4]

Review: Does not answer or explicitly abstain; it does not invent a patent number.

## AFTER Q19: How many real industrial customers have deployed this workbench in production?

Expected: Not stated; the manuscript reports no public deployment and uses a synthetic corpus, not customer-count data.

### eval-minicpm5-1b — Fail

PROJECT 01 / SOVEREIGN AGENTIC AI WORKBENCH Appendix A. [2]
Evidence manifest Identifier File in evidence/ Role A1 production-stress.json Four API load stages A2 ai-stress.json Short concurrent AI-task run A3 production-e2e.json Ten named live workflow checks A4 eval-1788679222.json Earlier keyword-coverage pilot A5 recovery-check.json; fault-recovery.json Database/count and restart behavior [2]

Review: Selects an evidence manifest instead of answering or explicitly abstaining.

### eval-gemma4-e4b — Fail

Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. [1]

Review: Selects benchmark commentary, not a customer count or explicit abstention.

### combined — Fail

PROJECT 01 / SOVEREIGN AGENTIC AI WORKBENCH Appendix A. [2]
Evidence manifest Identifier File in evidence/ Role A1 production-stress.json Four API load stages A2 ai-stress.json Short concurrent AI-task run A3 production-e2e.json Ten named live workflow checks A4 eval-1788679222.json Earlier keyword-coverage pilot A5 recovery-check.json; fault-recovery.json Database/count and restart behavior [2]
Its retained benchmarks establish successful selected local checks and high throughput for a narrow authenticated-read workload. [1]

Review: Retains irrelevant excerpts rather than explicitly abstaining about customers.

## AFTER Q20: The paper proves a general autonomous DAG planner. Which general DAG planning algorithm was validated?

Expected: Reject the premise. The demonstrated planner is bounded, with a fixed search and optional report step selected by keywords; general DAG planning is outside the demonstrated implementation.

### eval-minicpm5-1b — Fail

not a semantic certificate for every claim. [1]
3.3 Bounded orchestration and approval The task begins in PLANNING, enters RUNNING, executes document_search and proceeds to VERIFYING and COMPLETED. [1]

Review: Lists bounded task states but does not explicitly reject the false general-DAG premise.

### eval-gemma4-e4b — Pass

The current report tool returns Markdown stored in a task step. [1]
A public report-download artifact is not exposed. [1]
It does not demonstrate a general agent planner, complete semantic verification or a downloadable reporting product. [3]

Review: Explicitly says a general agent planner is not demonstrated; the false premise is rejected.

### combined — Pass

not a semantic certificate for every claim. [1]
3.3 Bounded orchestration and approval The task begins in PLANNING, enters RUNNING, executes document_search and proceeds to VERIFYING and COMPLETED. [1]
The current report tool returns Markdown stored in a task step. [1]
A public report-download artifact is not exposed. [1]
It does not demonstrate a general agent planner, complete semantic verification or a downloadable reporting product. [3]

Review: Rejects the general-planner premise and supplies bounded task-sequence context.