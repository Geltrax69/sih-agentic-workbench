import type { api, Evidence, MultiModelResult, Task } from "./api";

// Separate fixture adapter: preview never sends credentials, files, or questions to an API.
const evidence: Evidence[] = [{ chunk_id: "sample-1", document_id: "sample-doc", filename: "Workspace guide (sample).pdf", chunk_index: 0, location: "Page 1", content: "This sample workspace demonstrates document questions, source citations, and independent local-model comparisons. Review original sources before acting on generated answers.", score: 0.86 }];
const answer = "This sample workspace demonstrates document questions, source citations, and local-model comparisons. [1]\n\nReview the original sources before acting on a generated answer. [1]\n\nThis is a fixed illustrative response, not a live model result.";
const unavailable = async (): Promise<never> => { throw new Error("This action needs a live connection. Exit the preview and sign in to your running workbench."); };
const sampleTask = (question: string): Task => ({ task_id: "sample-task", status: "COMPLETED", input: question, result: { answer, evidence, citations: ["Workspace guide (sample).pdf · Page 1"], decision: "illustrative_preview", answer_model: "Sample model" }, steps: [], approvals: [] });
export const previewApi: typeof api = {
  login: unavailable,
  workspaces: async () => ({ workspaces: [{ id: "sample-workspace", name: "Research workspace", organization_id: "sample-org" }] }),
  documents: async () => ({ documents: [
    { id: "sample-doc", filename: "Workspace guide (sample).pdf", mime_type: "application/pdf", size_bytes: 2048, status: "INDEXED" },
    { id: "sample-notes", filename: "Research notes (sample).md", mime_type: "text/markdown", size_bytes: 1024, status: "INDEXED" },
  ] }),
  models: async () => ({ active: "Sample local model", verifier: "", models: [{ id: "Sample local model", type: "llm", state: "preview" }], can_switch: false }),
  createOrg: unavailable, createWorkspace: unavailable, upload: unavailable, setModel: unavailable, decide: unavailable,
  ask: async (_token, _workspace, question) => sampleTask(question),
  task: async () => sampleTask("Sample document question"),
  multiModel: async (_token, _workspace, question): Promise<MultiModelResult> => ({ question, models_used: ["Sample A", "Sample B"], synthesizer: "Sample synthesizer", combined_answer: answer, individual_answers: ["Sample A", "Sample B"].map(model => ({ model, answer, citations: ["Workspace guide (sample).pdf · Page 1"], latency_ms: 0, error: "" })), agreement: { pairs: [{ a: "Sample A", b: "Sample B", overlap: 1 }], mean_overlap: 1, n_answered: 2 }, verification: { decision: "illustrative_preview" }, evidence }),
};
