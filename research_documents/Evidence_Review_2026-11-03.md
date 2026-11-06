# Evidence review and project status

Prepared 3 November 2026.


## Evidence review & project status


### 3 November 2026 | Sovereign Agentic AI Workbench

This review replaces unsupported conclusions in the 30 October novelty summaries. It separates published evidence, inspected implementation, retained historical results, and experiments still needed. It is a research and engineering assessment, not a patentability or freedom-to-operate opinion.


### Patent: disclosure draft; novelty unestablished

An invention disclosure exists. No filing receipt, application number, examination report, or grant evidence for this project was supplied. Broad claims to retrieval followed by multiple answering models and fusion face substantial published overlap. An IBM patent family and an Intuit application are relevant screening leads [P1, P2]. A feature combination alone is insufficient evidence of inventive step.


### Research paper: unpublished systems manuscript

Research_Paper.pdf is an 11-page draft dated 8 September 2026. Authors and affiliations remain pending. It describes the earlier evidence-gated single-model workflow and a small exploratory evaluation. The later multi-model feature needs a revised methods section and a controlled comparison. The existing load figures do not measure multi-model answer quality.


### UI build: implemented and locally demonstrated

The React interface now uses light surfaces, blue accents, lime actions, labeled inputs, responsive layouts, and a separate sample-data preview. Normal authenticated API behavior remains available. The local Docker daemon is unavailable, so the browser demonstration is a frontend preview rather than a verified full-stack deployment.


### What this folder now supplies

Fifteen original PDFs: thirteen research papers, one published patent application, and the Indian Patent Office CRI guidelines. The JSON source register records origin URLs, retrieval date, PDF page count, file size, and SHA-256 hashes. Research conclusions below are interpretations, with source locators and limitations exposed.


## Corrections to the existing claims


### The most consequential overlap [R4]

Revisiting RAG Ensemble, Section 4.7 (PDF page 8), fixes the reference documents, varies the answer-generating models, and aggregates their outputs. The existing assertion that it only ensembles different retrieval pipelines is incorrect. Shared-evidence generator fusion is already studied. The possible contribution must be narrower: deployment constraints, inspectability, and rigorously measured behavior.


### Do not label lexical overlap as truth

The implementation uses pairwise Jaccard overlap over token sets. Two answers can share vocabulary while contradicting one another; two faithful paraphrases can have low overlap. Shared evidence can also make all models repeat the same source error. Report this as lexical agreement, not calibrated confidence or independent evidence of correctness. This conclusion follows from the metric definition in services/ai/app/multi_model.py.


### Prompted citations are not citation enforcement

The prompt requests numbered citations and extract_citations maps valid indices to source locations. That does not establish that each claim is entailed by the particular cited passage. The verifier currently checks against the complete evidence block, and records the first citation marker. A claim may be supported somewhere while its attached citation is wrong. Citation precision and completeness require their own evaluation [R5].


### Local serving and concurrency require measurement

asyncio.gather issues requests concurrently. A single local model server can serialize requests, swap weights, run out of memory, or limit simultaneous loaded models. Parallel Python requests do not prove parallel GPU execution or lower latency. No commodity-hardware advantage over the strongest single model has been demonstrated for this feature.


### Correct wording for the disclosure

Use: "An implemented on-premise integration of shared-evidence generator ensembling, lexical-agreement inspection, and post-generation checking; comparative reliability and resource efficiency remain hypotheses." Remove claims of proven superiority, universal novelty, ungamable agreement, cloud-only prior methods, and guaranteed citation correctness.


## Related work: retrieval and ensembles


### R1 | Lewis et al. | RAG | 2020

Foundational work combines a retriever and a generator for knowledge-intensive tasks. Use it to explain why external evidence is supplied to generation. It does not validate this repository's access controls, confidence thresholds, or performance. Locator: abstract and architecture/method section.


### R2 | Wang et al. | Mixture-of-Agents | 2024

Layered proposer and aggregator models use earlier answers as auxiliary input. Relevant to independent model responses followed by synthesis. Its instruction-following benchmark results cannot be transferred to document-grounded local workloads. Open-source models do not imply a cloud-only architecture. Locator: abstract and MoA methodology.


### R3 | Jiang, Ren and Lin | LLM-Blender | ACL 2023

PairRanker and GenFuser rank and combine candidate model outputs. This establishes earlier model-ensemble and fusion mechanisms. Our token overlap is a different measurement, not an equivalent ranking model or demonstrated replacement. Locator: framework and model descriptions.


### R4 | Chen et al. | Revisiting RAG Ensemble | 2025

The closest research comparator for the central fan-out and synthesis mechanism. Include its generator-level setting as a baseline, with the same retrieved context and a matched synthesis model. Locator: Section 4.7, PDF page 8, and Table 2. Peer-review status is not established by the arXiv record.


### R10 | Ram et al. | In-Context RALM | 2023

Grounding documents can be prepended to an unchanged language model without additional model training. This narrows claims that training-free grounded generation is new. Relevant to off-the-shelf model adapters. Locator: abstract and in-context retrieval-augmented language modeling method.


### How these papers should be used

Treat them as design lineage and direct comparators. A published gain belongs to that paper's models, datasets, prompts, and budgets. It is not a result for this workbench. Where a paper does not discuss enterprise RBAC or audit, record "not evaluated in this paper" rather than asserting the method cannot support them.


## Related work: citations and reliability


### R5 | Gao et al. | ALCE | EMNLP 2023

A benchmark for generated answers with citations, separating answer quality from citation quality. It motivates explicit attribution precision and coverage measurements. Locator: evaluation framework and citation metrics. A visible citation marker alone is not a successful attribution.


### R6 | Asai et al. | Self-RAG | 2023

Trains a model to retrieve and reflect using special tokens. Relevant to grounding and verification, but distinct from this workbench's off-the-shelf fan-out. Locator: framework and training/inference description. It is a comparator, not evidence that cross-model agreement is more reliable.


### R7 | Es et al. | RAGAs | EACL 2024

Separates retrieval-context relevance, answer faithfulness, and answer relevance in automatic evaluation. Use as diagnostic metrics alongside human labels. Locator: metric definitions. Automated judges must be checked for errors and must fit the intended local deployment boundary.


### R8 | Liu et al. | Lost in the Middle | 2023

Demonstrates sensitivity to where relevant evidence appears in a long context. Use beginning/middle/end evidence placement as a stress test. Locator: multi-document QA experiments. A context-size limit alone does not establish effective evidence use.


### R9 | Wang et al. | Self-Consistency | 2022/2023

Samples multiple reasoning paths and selects consistent answers. Include repeated sampling of the same model as a budget-aware alternative to heterogeneous generators. Locator: self-consistency decoding method. Free-text lexical overlap is not the paper's canonical-answer voting.


### R13 | Niu et al. | RAGTruth | ACL 2024

Provides human-annotated unsupported and contradictory content in RAG responses. Useful for evaluating hallucination detection separately from answer similarity. Locator: corpus construction and annotation protocol. External test data still requires compatibility checks with the intended confidential domain.


## Recent evidence & search boundaries


### R11 | Xiao et al. | MASS-RAG | April 2026

Processes retrieved evidence through role-specialized summarization, extraction, and reasoning agents before synthesis. Relevant overlap is multiple evidence-processing views combined in a final answer. The distinction from this project is role diversity versus generator-model diversity. Locator: abstract and method. This downloaded arXiv preprint is not treated as a peer-reviewed result.


### R12 | Akay et al. | SPD-RAG | March 2026

Uses document-level agents and centralized, token-bounded synthesis for cross-document QA. Relevant to the coordination and synthesis design space. Different document scopes make it distinct from fixed shared evidence, but do not establish novelty for model fusion. Locator: abstract and architecture. The workbench has not been tested on its reported benchmark.


### Search protocol

Searched the web on 3 November 2026 for shared-evidence multi-model RAG, generator ensembles, answer fusion, citation evaluation, hallucination corpora, ensemble-QA patents, and Indian CRI examination guidance. Read primary arXiv and ACL records, inspected downloaded paper text, and checked patent claim text and the official IP India guidance index. Secondary search results were discovery aids, not the basis for technical conclusions.


### Coverage and exclusions

This is a targeted literature and patent screening, not an exhaustive systematic review. No complete forward/backward citation expansion, multilingual patent-family search, prosecution-history review, or Indian claim search was completed. The additional 2026 papers improve recency without proving that every relevant current work has been found. Older references in the supplied summaries that were not reverified are excluded from the new bibliography.


### Traceability and original documents

source_register.json identifies each original PDF, its download URL, page count, byte count, and content hash. P1 is a scanned patent PDF; keyword search may require OCR. P2 is a web-source screening lead, linked in the bibliography; no original PDF was downloaded for P2. Earlier project PDFs remain historical drafts and should be read with this review.


## Patent landscape: screening findings


### P1 | IBM | US20230023958A1

Published 26 January 2023, with a 23 July 2021 filing/priority date. The family concerns retrieved passages, selectable QA models, ensembling, and displaying component answers. The official USPTO gazette identifies the later US12664183B2 grant dated 23 June 2026. This is a substantial overlap lead for broad retrieve-many-answers-and-display claims. Inspect all claims and the relevant family before drafting.


### P2 | Intuit | US20260105091A1

Published 16 April 2026, with a recorded filing/priority date of 15 October 2024. Its claims concern improving a RAG language-model ensemble through context, generated questions/answers, prompts, and scoring. This is related prior disclosure, not evidence of infringement by this repository. Source: Google Patents claim text; legal status requires the official register.


### G1 | Indian Patent Office | CRI guidelines 2025

The current official index links the final CRI guidelines, including novelty, inventive step, disclosure sufficiency, section 3(k), and AI/ML examination. Use the final document rather than a draft. Relevant locators: Sections 4.1, 4.2, 4.4, 4.5 and 5.2. A computer implementation or AI label alone does not establish eligibility.


### A defensible next invention review

Build a feature-by-feature claim chart against the full IBM family, Intuit claims, and additional retrieved patents. Identify an actual technical mechanism and measurable technical effect beyond routine fusion, RBAC, audit, or local deployment. Candidate investigations include evidence binding and resource scheduling, but these are proposals, not implemented inventions or patent claims.


### Disclosure and ownership facts need confirmation

The supplied form marks public disclosures and external inventors as NO and leaves personal fields blank. Repository contents cannot confirm these declarations. The inventor must verify publications, demonstrations, collaborators, ownership, and dates. No filing action was taken. Novelty, inventive step, eligibility, and freedom to operate are separate questions; this screening decides none of them conclusively.


## What the code demonstrates today


### Implemented mechanism

services/ai/app/multi_model.py performs workspace-scoped retrieval, independent generation requests, lexical-overlap computation, source-index extraction, synthesis, and post-generation verification. The Go multi-model handler exposes a member-authorized route and records a completion audit event. React exposes combined answers, sources, overlaps, and per-model answers.


### Verification boundary

grounding/verifier.py splits sentences in code, checks numbers and topic overlap against the evidence block, then asks a configured model for support. The confidence field is a proportion of passing factual sentences, adjusted for weak evidence in applicable paths; it is not a calibrated probability. The multi-model path currently supplies weak_evidence=False.


### Failure and persistence gaps

A failed individual generator is retained as an error while other generators continue. Synthesis is still attempted when no generator succeeds. The full multi-model run is not persisted in the same task-step workflow, and the pipeline is not connected to the single-model approval flow. A model-based verifier may share the answerer's mistakes, especially when configured to use the same model.


### Evidence inspected, not an additional security certification

The repository contains role checks, workspace-scoped retrieval, local-endpoint configuration checks, and audit code. These are implementation observations. No complete security audit, egress capture, adversarial tenant-isolation campaign, or production deployment validation was performed in this task. Source prompts that label documents as data are useful defenses but not a proof of injection resistance.


### Fresh targeted verification

The six multi-model unit tests and four fake-endpoint integration tests passed on 3 November 2026. Run from services/ai with INTERNAL_API_SECRET=sih-test-secret .venv/bin/python -m pytest --import-mode=importlib tests/unit/test_multi_model.py tests/integration/test_multi_model.py -q. These tests stub retrieval and model behavior; they establish plumbing behavior, not live-model reliability or comparative accuracy.


## Evaluation needed for a stronger paper


### Primary question and controlled baselines

Test whether heterogeneous local generators plus synthesis improve source-supported correctness over the strongest single local model at an acceptable resource cost. Compare: (A) single-model RAG; (B) multiple samples from that same model plus synthesis; (C) heterogeneous generators plus synthesis; (D) C plus the current verifier. Hold retrieval and evidence fixed for the generator comparison. Separately test end-to-end retrieval behavior.


### Dataset and labels

Create an initial 200-question evaluation set across four workspaces: 80 direct lookups, 40 multi-document questions, 30 unanswerable queries, 25 conflicting/obsolete-source cases, and 25 document-injection or citation attacks. Split development and final test questions by source document. Human annotators record required facts and supporting passage IDs; use two annotators and resolve disagreements. These counts are a proposed protocol, not completed data.


### Measure outcomes separately

Report claim correctness and source support, citation precision and completeness, retrieval recall, abstention precision/recall, and contradiction rate. Measure whether lexical agreement predicts correctness with calibration plots and error analysis. Report p50/p95 end-to-end latency, tokens, requests, peak RAM/VRAM, failures, and model-load time. API read throughput must remain separate from generation throughput.


### Ablations and resource fairness

Vary generator count, model family, evidence ordering, verifier identity, and synthesis choice. Match token or wall-clock budgets where possible. Log hardware, quantization, context length, server scheduler limits, model hashes, seeds, temperatures, and exact prompts. Concurrent API submission is not evidence of simultaneous execution; observe actual server behavior.


### Analysis and release evidence

Use paired comparisons and question-level bootstrap confidence intervals. Predefine a meaningful quality gain and acceptable latency/memory budget before seeing test results. Retain raw responses, citation mappings, anonymized labels, failures, and run manifests. Publish negative results and disagreement counterexamples. No new quality scores, confidence intervals, or hardware-efficiency results are claimed in this review.


## Manuscript, disclosure & UI next steps


### Paper revision

Retain the systems-prototype framing. Add the actual multi-model algorithm and trust boundaries to Methods; separate historical API, earlier generation pilot, and new ensemble results. Related Work should include the direct generator-ensemble comparator and citation metrics. Until the evaluation above is run, describe reliability improvements as hypotheses. Complete author order, affiliations, corpus description, model versions, limitations, and target-venue formatting.


### Disclosure revision

Use the narrower implemented-integration description from page 2. Replace unsupported distinctions about RAG Ensemble. Explain token overlap accurately and distinguish requested citations from source-specific entailment checks. Confirm all disclosure declarations and inventorship. Obtain a claim-level novelty and eligibility review before deciding filing scope. Downloaded open-source or open-access material is not evidence of freedom to operate.


### UI delivered

The sign-in surface uses a blue brand panel, white form area, and lime primary action inspired by the user's reference. The workbench uses a light library sidebar, clear document/question hierarchy, starter questions, pale status treatments, and preserved answer/evidence/model controls. Switching workspaces clears stale outputs. API errors remain visible even before a workspace is selected.


### Preview and checks

Open http://localhost:3000/?preview=1 for the sample-data interface and http://localhost:3000/ for sign-in. The preview uses a separate fixture API adapter: it makes no /api requests, does not sign in, and cannot upload or mutate real data. Browser checks covered desktop (1440px) and mobile (390px), starter questions, sample answers, multi-model results, unsupported-action errors, and exit to sign-in. No horizontal overflow or browser runtime errors were observed.


### Remaining readiness gates

The frontend production build passes. A real authenticated full-stack UI run still needs Docker services and a reachable local model server. The targeted fake-model tests pass; live ensemble quality is unmeasured. Patent filing and paper submission have not been performed. The original September manuscript and October reports remain preserved for history; this evidence review supplies the current qualifications.


## Source register / 1


### R1 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

19 PDF pages. Local: sources/RAG_Lewis_2020.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2005.11401


### R2 | Mixture-of-Agents Enhances Large Language Model Capabilities

15 PDF pages. Local: sources/Mixture_of_Agents_2024.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2406.04692


### R3 | LLM-Blender: Ensembling Large Language Models with Pairwise Ranking and Generative Fusion

14 PDF pages. Local: sources/LLM_Blender_ACL_2023.pdf. Accessed 3 November 2026.

https://aclanthology.org/2023.acl-long.792/


### R4 | Revisiting RAG Ensemble: A Theoretical and Mechanistic Analysis of Multi-RAG System Collaboration

13 PDF pages. Local: sources/RAG_Ensemble_2025.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2508.13828


### R5 | Enabling Large Language Models to Generate Text with Citations

24 PDF pages. Local: sources/ALCE_Citation_Evaluation_EMNLP_2023.pdf. Accessed 3 November 2026.

https://aclanthology.org/2023.emnlp-main.398/


### R6 | Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection

30 PDF pages. Local: sources/Self_RAG_2023.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2310.11511


### R7 | RAGAs: Automated Evaluation of Retrieval Augmented Generation

9 PDF pages. Local: sources/RAGAS_EACL_2024.pdf. Accessed 3 November 2026.

https://aclanthology.org/2024.eacl-demo.16/


### R8 | Lost in the Middle: How Language Models Use Long Contexts

18 PDF pages. Local: sources/Lost_in_the_Middle_2023.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2307.03172


## Source register / 2


### R9 | Self-Consistency Improves Chain of Thought Reasoning in Language Models

24 PDF pages. Local: sources/Self_Consistency_2022.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2203.11171


### R10 | In-Context Retrieval-Augmented Language Models

15 PDF pages. Local: sources/In_Context_RALM_2023.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2302.00083


### P1 | Online question answering, using reading comprehension with an ensemble of models

18 PDF pages. Local: sources/IBM_US20230023958A1.pdf. Accessed 3 November 2026.

https://patents.google.com/patent/US20230023958A1/en


### G1 | Guidelines for Examination of Computer Related Inventions (CRIs) - 2025

67 PDF pages. Local: sources/IP_India_CRI_Guidelines_2025.pdf. Accessed 3 November 2026.

https://ipindia.gov.in/resource/patents-resources-guidelines


### R11 | MASS-RAG: Multi-Agent Synthesis Retrieval-Augmented Generation

19 PDF pages. Local: sources/MASS_RAG_2026.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2604.18509


### R12 | SPD-RAG: Sub-Agent Per Document Retrieval-Augmented Generation

12 PDF pages. Local: sources/SPD_RAG_2026.pdf. Accessed 3 November 2026.

https://arxiv.org/abs/2603.08329


### R13 | RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models

17 PDF pages. Local: sources/RAGTruth_ACL_2024.pdf. Accessed 3 November 2026.

https://aclanthology.org/2024.acl-long.585/


### P2 | Intuit ensemble-RAG application | web source only

https://patents.google.com/patent/US20260105091A1/en


### P1 grant record | official USPTO gazette

https://patentsgazette.uspto.gov/week25/OG/html/1547-4/US12664183-20260623.html
