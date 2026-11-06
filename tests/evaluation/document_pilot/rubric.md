# Single-document exploratory grading protocol

Dataset: `questions.json`, authored from `Research_Paper.pdf` before the primary batch. Twenty questions, one generation per model and one synthesis per question. No performance-based question removal or prompt tuning within the primary batch.

Each of the 60 outputs will receive an explicit assistant review against the document and the retained retrieved passages. Review is unblinded, by the same assistant that authored the questions; these are exploratory labels, not independent human ground truth.

- **Correct:** answers every requested fact accurately, or appropriately refuses an unanswerable question; rejects misleading premises; adds no materially false claims. Incomplete answers fail this strict binary metric. Merely repeating the question, a source marker, or an expected keyword does not pass.
- **Unsupported material:** record factual additions not supported by the document or material falsehoods, separately from omissions/abstention. Correctness cannot be established by the model verifier or token overlap.
- **Retrieval coverage:** complete / partial / missing for answerable questions, based on whether the selected passages contain all required facts. This is an assistant review, not held-out retrieval recall over an independently annotated corpus. Unanswerable cases are marked not applicable.
- **Citation marker compliance:** mechanical check for at least one in-range `[n]` marker for answerable outputs and no out-of-range numbered markers. This is formatting only, not semantic citation precision or entailment. Refusals do not require a marker.
- **Latency:** retain per-generator wall time during a shared fan-out, and retrieval + generation + synthesis wall time per question. These are not isolated single-model serving benchmarks. Exclude initial model loading and indexing from per-question timing; report them as setup behavior.

Report counts and denominators, answer-level errors, retrieval gaps, and the exact checkpoint/quantization. Do not call this general accuracy, cross-domain validation, or proof that an ensemble improves reliability. The initial full-pipeline verifier smoke attempt is retained separately and excluded from the primary batch after a verifier output degenerated and hit its 2,000-token cap. The main batch uses the same production generation and synthesis functions but omits verification, since that stage flags results and does not rewrite answers.
