import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Evidence, type Task, type Workspace } from "./api";

type Session = { token: string; email: string };

export default function Workbench({
  session,
  onLogout,
}: {
  session: Session;
  onLogout: () => void;
}) {
  const qc = useQueryClient();
  const [wsId, setWsId] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsQuery = useQuery({
    queryKey: ["workspaces", session.token],
    queryFn: () => api.workspaces(session.token),
  });
  const docsQuery = useQuery({
    queryKey: ["documents", session.token, wsId],
    queryFn: () => api.documents(session.token, wsId!),
    enabled: !!wsId,
  });

  const createOrg = useMutation({
    mutationFn: () => api.createOrg(session.token, "My Organization"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workspaces"] }),
  });
  const createWs = useMutation({
    mutationFn: () =>
      api.createWorkspace(
        session.token,
        wsQuery.data?.workspaces[0]?.organization_id ?? "",
        "Workspace " + new Date().toISOString().slice(0, 10),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workspaces"] }),
  });
  const upload = useMutation({
    mutationFn: (file: File) => api.upload(session.token, wsId!, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
    onError: (e) => setError(String(e)),
  });
  const ask = useMutation({
    mutationFn: () => api.ask(session.token, wsId!, question),
    onSuccess: (t) => {
      setTask(t);
      setError(null);
    },
    onError: (e) => setError(String(e)),
  });
  const decide = useMutation({
    mutationFn: (p: { taskId: string; approved: boolean }) =>
      api.decide(session.token, p.taskId, p.approved),
    onSuccess: (t) => setTask(t),
  });

  const workspaces = wsQuery.data?.workspaces ?? [];

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <header className="border-b border-neutral-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="font-semibold">Sovereign Agentic AI Workbench</h1>
          <p className="text-xs text-neutral-500">
            {session.email} · local-only · audit enabled
          </p>
        </div>
        <button
          onClick={onLogout}
          className="text-sm px-3 py-1.5 rounded border border-neutral-700 hover:bg-neutral-800"
        >
          Sign out
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6 p-6">
        {/* left: workspaces + documents */}
        <aside className="space-y-6">
          <section>
            <h2 className="text-sm font-medium text-neutral-400 mb-2">Workspaces</h2>
            {wsQuery.isLoading ? (
              <p className="text-sm text-neutral-600">loading…</p>
            ) : workspaces.length === 0 ? (
              <button
                onClick={() => createOrg.mutate()}
                className="text-sm px-3 py-2 rounded bg-indigo-600 hover:bg-indigo-500"
              >
                Create organization
              </button>
            ) : (
              <ul className="space-y-1">
                {workspaces.map((w: Workspace) => (
                  <li key={w.id}>
                    <button
                      onClick={() => {
                        setWsId(w.id);
                        setTask(null);
                      }}
                      className={
                        "w-full text-left text-sm px-3 py-2 rounded " +
                        (wsId === w.id
                          ? "bg-indigo-950 text-indigo-200"
                          : "hover:bg-neutral-900 text-neutral-300")
                      }
                    >
                      {w.name}
                    </button>
                  </li>
                ))}
                <li>
                  <button
                    onClick={() => createWs.mutate()}
                    className="text-xs text-neutral-500 hover:text-neutral-300 px-3 py-1"
                  >
                    + new workspace
                  </button>
                </li>
              </ul>
            )}
          </section>

          {wsId && (
            <section>
              <h2 className="text-sm font-medium text-neutral-400 mb-2">
                Sources ({docsQuery.data?.documents.length ?? 0})
              </h2>
              <input
                type="file"
                onChange={(e) => e.target.files?.[0] && upload.mutate(e.target.files[0])}
                className="text-xs text-neutral-400 file:mr-2 file:px-2 file:py-1 file:rounded file:border-0 file:bg-neutral-800"
              />
              <ul className="mt-2 space-y-1">
                {(docsQuery.data?.documents ?? []).map((d) => (
                  <li key={d.id} className="text-xs flex justify-between gap-2">
                    <span className="truncate text-neutral-300">{d.filename}</span>
                    <StatusPill status={d.status} />
                  </li>
                ))}
              </ul>
            </section>
          )}
        </aside>

        {/* right: conversation */}
        <main className="space-y-4">
          {!wsId ? (
            <Empty title="Select a workspace" hint="Create one to start ingesting documents." />
          ) : (
            <>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (question.trim()) ask.mutate();
                }}
                className="flex gap-2"
              >
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask about your documents…"
                  className="flex-1 bg-neutral-900 border border-neutral-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-600"
                />
                <button
                  disabled={ask.isPending}
                  className="px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-sm disabled:opacity-50"
                >
                  {ask.isPending ? "thinking…" : "Ask"}
                </button>
              </form>

              {error && (
                <p className="text-sm text-red-400 border border-red-900 rounded p-3">{error}</p>
              )}

              {task && <TaskView task={task} onDecide={(a) => decide.mutate({ taskId: task.task_id, approved: a })} />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function TaskView({ task, onDecide }: { task: Task; onDecide: (approved: boolean) => void }) {
  return (
    <div className="space-y-3">
      <div className="text-xs text-neutral-500 flex gap-3">
        <span>task {task.task_id.slice(0, 8)}</span>
        <span>·</span>
        <span>{task.status}</span>
      </div>

      {task.steps.map((s) => (
        <div key={s.key} className="text-xs text-neutral-500">
          {s.action} — {s.status}
        </div>
      ))}

      {task.status === "WAITING_FOR_APPROVAL" && (
        <div className="border border-amber-800 bg-amber-950/40 rounded p-4 space-y-3">
          <p className="text-sm text-amber-200">
            Approval required: <b>{task.approvals[0]?.tool}</b>
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => onDecide(true)}
              className="text-sm px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600"
            >
              Approve
            </button>
            <button
              onClick={() => onDecide(false)}
              className="text-sm px-3 py-1.5 rounded bg-neutral-700 hover:bg-neutral-600"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {task.result?.answer && (
        <div className="bg-neutral-900 border border-neutral-800 rounded p-4 space-y-3">
          <p className="text-sm whitespace-pre-wrap">{task.result.answer}</p>
          {typeof task.result.confidence === "number" && (
            <p className="text-xs text-neutral-500">
              confidence {(task.result.confidence * 100).toFixed(0)}% ·{" "}
              {task.result.decision}
            </p>
          )}
          <EvidenceList evidence={task.result.evidence ?? []} />
        </div>
      )}
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) return null;
  return (
    <details className="text-xs">
      <summary className="cursor-pointer text-neutral-400">
        sources ({evidence.length})
      </summary>
      <ul className="mt-2 space-y-2">
        {evidence.map((e, i) => (
          <li key={e.chunk_id} className="border-l-2 border-neutral-700 pl-3">
            <span className="text-neutral-500">
              [{i + 1}] {e.filename} · {(e.score * 100).toFixed(0)}%
            </span>
            <p className="text-neutral-400 mt-1 line-clamp-3">{e.content}</p>
          </li>
        ))}
      </ul>
    </details>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === "INDEXED"
      ? "text-emerald-400"
      : status === "FAILED"
        ? "text-red-400"
        : status === "PROCESSING"
          ? "text-amber-400"
          : "text-neutral-500";
  return <span className={color}>{status.toLowerCase()}</span>;
}

function Empty({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <h2 className="text-lg font-medium text-neutral-300">{title}</h2>
      <p className="text-sm text-neutral-500 mt-1">{hint}</p>
    </div>
  );
}
