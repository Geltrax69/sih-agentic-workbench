
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
  content: string;
  score: number;
};
export type TaskResult = {
  answer?: string;
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
  documents: (token: string, wsId: string) =>
    req<{ documents: Document[] }>("GET", `/api/v1/workspaces/${wsId}/documents`, undefined, token),
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
  ask: (token: string, wsId: string, question: string) =>
    req<Task>("POST", `/api/v1/workspaces/${wsId}/tasks`, { question }, token),
  task: (token: string, taskId: string) =>
    req<Task>("GET", `/api/v1/tasks/${taskId}`, undefined, token),
  decide: (token: string, taskId: string, approved: boolean) =>
    req<Task>("POST", `/api/v1/tasks/${taskId}/approval`, { approved }, token),
};
