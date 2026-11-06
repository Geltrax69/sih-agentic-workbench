
export type Workspace = { id: string; name: string; organization_id: string };
export type Document = {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: string;
};
export type Evidence = {
  chunk_id: string;
  document_id: string;
  filename: string;
  chunk_index: number;
  location?: string;
  content: string;
  score: number;
};
export type LocalModel = { id: string; type: string; state: string };
export type ModelList = { active: string; verifier: string; models: LocalModel[]; can_switch: boolean };
export type Claim = { claim: string; supported: boolean; source: number };
export type TaskResult = {
  answer?: string;
  error?: string;
  retrieval_score?: number;
  answer_model?: string;
  verification?: { model?: string; claims: Claim[]; error?: string };
  confidence?: number;
  decision?: string;
  citations?: string[];
  evidence?: Evidence[];
};
export type Task = {
  task_id: string;
  status: string;
  input: string;
  result: TaskResult | null;
  steps: { key: string; action: string; status: string }[];
  approvals: { id: string; tool: string; status: string }[];
};

async function req<T>(
  method: string,
  path: string,
  body?: unknown,
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    req<{ token: string; user: { email: string; display_name: string } }>(
      "POST",
      "/api/v1/auth/login",
      { email, password },
    ),
  workspaces: (token: string) =>
    req<{ workspaces: Workspace[] }>("GET", "/api/v1/workspaces", undefined, token),
  createWorkspace: (token: string, orgId: string, name: string) =>
    req<Workspace>("POST", `/api/v1/organizations/${orgId}/workspaces`, { name }, token),
  createOrg: (token: string, name: string) =>
    req<{ id: string }>("POST", "/api/v1/organizations", { name }, token),
  // Go encodes an empty slice as null
  documents: async (token: string, wsId: string) => {
    const r = await req<{ documents: Document[] | null }>("GET", `/api/v1/workspaces/${wsId}/documents`, undefined, token);
    return { documents: r.documents ?? [] };
  },
  upload: async (token: string, wsId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`/api/v1/workspaces/${wsId}/documents`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) throw new Error((await res.text()) || `${res.status}`);
    return res.json() as Promise<Document>;
  },
  models: (token: string) => req<ModelList>("GET", "/api/v1/models", undefined, token),
  setModel: (token: string, model: string, role: "answerer" | "verifier" = "answerer") =>
    req<{ active: string; verifier: string }>("POST", "/api/v1/models/active", { model, role }, token),
  ask: (token: string, wsId: string, question: string) =>
    req<Task>("POST", `/api/v1/workspaces/${wsId}/tasks`, { question }, token),
  task: (token: string, taskId: string) =>
    req<Task>("GET", `/api/v1/tasks/${taskId}`, undefined, token),
  decide: (token: string, taskId: string, approved: boolean) =>
    req<Task>("POST", `/api/v1/tasks/${taskId}/approval`, { approved }, token),
  multiModel: (
    token: string,
    wsId: string,
    question: string,
    models: string[],
    synthesizer: string,
  ) =>
    req<MultiModelResult>("POST", `/api/v1/workspaces/${wsId}/ask/multi-model`, {
      question,
      models,
      synthesizer,
    }, token),
};

export type MultiModelAnswer = {
  model: string;
  answer: string;
  citations: string[];
  latency_ms: number;
  error: string;
};

export type MultiModelResult = {
  question: string;
  models_used: string[];
  individual_answers: MultiModelAnswer[];
  agreement: { pairs: { a: string; b: string; overlap: number }[]; mean_overlap: number; n_answered: number };
  combined_answer: string;
  synthesizer: string;
  verification?: { model?: string; confidence?: number; decision?: string; error?: string; method?: string };
  evidence: Evidence[];
};
