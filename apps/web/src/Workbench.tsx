import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api as liveApi, type Evidence, type LocalModel, type MultiModelResult, type Task, type TaskResult, type Workspace } from "./api";

type Session = { token: string; email: string };

export default function Workbench({
  session,
  onLogout,
  apiClient = liveApi,
  preview = false,
}: {
  session: Session;
  onLogout: () => void;
  apiClient?: typeof liveApi;
  preview?: boolean;
}) {
  const api = apiClient;
  const qc = useQueryClient();
  const [wsId, setWsId] = useState<string | null>(preview ? "sample-workspace" : null);
  const [question, setQuestion] = useState("");
  const [task, setTask] = useState<Task | null>(null);
  const [multi, setMulti] = useState<MultiModelResult | null>(null);
  const [multiMode, setMultiMode] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsQuery = useQuery({
    queryKey: ["workspaces", session.token],
    queryFn: () => api.workspaces(session.token),
  });
  const docsQuery = useQuery({
    queryKey: ["documents", session.token, wsId],
    queryFn: () => api.documents(session.token, wsId!),
    enabled: !!wsId,
    // keep polling until every upload has finished ingesting
    refetchInterval: (q) =>
      q.state.data?.documents.some((d) => d.status !== "INDEXED" && d.status !== "FAILED")
        ? 2000
        : false,
  });

  const createOrg = useMutation({
    // an org alone shows nothing (the list is workspaces), so create its first workspace too
    mutationFn: async () => {
      const org = await api.createOrg(session.token, "My Organization");
      return api.createWorkspace(session.token, org.id, "My Workspace");
    },
    onSuccess: (ws) => {
      setWsId(ws.id);
      qc.invalidateQueries({ queryKey: ["workspaces"] });
    },
    onError: (e) => setError(String(e)),
  });
  const createWs = useMutation({
    mutationFn: () =>
      api.createWorkspace(
        session.token,
        wsQuery.data?.workspaces[0]?.organization_id ?? "",
        "Workspace " + new Date().toISOString().slice(0, 10),
      ),
    onSuccess: (ws) => {
      setWsId(ws.id);
      qc.invalidateQueries({ queryKey: ["workspaces"] });
    },
    onError: (e) => setError(String(e)),
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
    onError: (e) => setError(String(e)),
  });
  const askMulti = useMutation({
    mutationFn: () => api.multiModel(session.token, wsId!, question, [], ""),
    onSuccess: (r) => {
      setMulti(r);
      setError(null);
    },
    onError: (e) => setError(String(e)),
  });

  const workspaces = wsQuery.data?.workspaces ?? [];

  return (
    <div className="workbench-shell min-h-screen bg-stone-50 text-slate-900">
      {preview && <div className="preview-notice">UI preview · Illustrative documents and responses · No backend connected <button onClick={onLogout}>Go to sign in →</button></div>}
      <header className="workbench-header border-b border-slate-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="brand font-semibold"><svg width="27" height="27" viewBox="0 0 27 27" fill="none" aria-hidden="true"><path d="M3 17 10 4h7l-7 13H3Zm7 6 7-13h7l-7 13h-7Z" fill="currentColor" /></svg> sovereign <span className="brand-tag">WORKBENCH</span></h1>
          <p className="text-xs text-slate-500">
            {session.email} · local-only · audit enabled
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ModelPicker token={session.token} apiClient={api} />
          <button
            onClick={onLogout}
            className="text-sm px-3 py-1.5 rounded border border-slate-200 hover:bg-slate-100"
          >
            {preview ? "Exit preview" : "Sign out"}
          </button>
        </div>
      </header>

      <div className="workspace-layout grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6 p-6">
        {/* left: workspaces + documents */}
        <aside className="workspace-sidebar space-y-6">
          <div className="sidebar-heading">Your library <span>Workspace-scoped</span></div>
          <section>
            <h2 className="text-sm font-medium text-slate-600 mb-2">Workspaces</h2>
            {wsQuery.isError ? <p role="alert" className="text-sm text-red-700">Could not load workspaces. Check the API connection and try again.</p> : wsQuery.isLoading ? (
              <p className="text-sm text-slate-600">loading…</p>
            ) : workspaces.length === 0 ? (
              <button
                onClick={() => createOrg.mutate()}
                disabled={createOrg.isPending}
                className="text-sm px-3 py-2 rounded bg-sky-700 hover:bg-sky-800 disabled:opacity-50"
              >
                {createOrg.isPending ? "Creating…" : "Create organization"}
              </button>
            ) : (
              <ul className="space-y-1">
                {workspaces.map((w: Workspace) => (
                  <li key={w.id}>
                    <button
                      onClick={() => {
                        setWsId(w.id);
                        setTask(null);
                        setMulti(null);
                        setError(null);
                      }}
                      className={
                        "w-full text-left text-sm px-3 py-2 rounded " +
                        (wsId === w.id
                          ? "bg-sky-50 text-sky-800"
                          : "hover:bg-white text-slate-700")
                      }
                    >
                      {w.name}
                    </button>
                  </li>
                ))}
                <li>
                  <button
                    onClick={() => createWs.mutate()}
                    className="text-xs text-slate-500 hover:text-slate-700 px-3 py-1"
                  >
                    + new workspace
                  </button>
                </li>
              </ul>
            )}
          </section>

          {wsId && (
            <section>
              <h2 className="text-sm font-medium text-slate-600 mb-2">
                Sources ({docsQuery.data?.documents.length ?? 0})
              </h2>
              <input
                type="file"
                aria-label="Upload a source document"
                disabled={preview || upload.isPending}
                accept=".pdf,.docx,.xlsx,.pptx,.csv,.txt,.md"
                onChange={(e) => e.target.files?.[0] && upload.mutate(e.target.files[0])}
                className="text-xs text-slate-600 file:mr-2 file:px-2 file:py-1 file:rounded file:border-0 file:bg-slate-100"
              />
              {docsQuery.isError && <p role="alert" className="text-sm text-red-700">Could not load sources. Check the connection and retry.</p>}
              {upload.isPending && <p role="status" className="text-xs text-slate-500">Uploading document…</p>}
              <ul className="mt-2 space-y-1">
                {(docsQuery.data?.documents ?? []).map((d) => (
                  <li key={d.id} className="text-xs flex justify-between gap-2">
                    <span className="truncate text-slate-700">{d.filename}</span>
                    <StatusPill status={d.status} />
                  </li>
                ))}
              </ul>
            </section>
          )}
          <div className="sidebar-footnote"><span className="status-dot" /> Local by design<p>Answers stay connected to your sources. You stay in control.</p></div>
        </aside>

        {/* right: conversation */}
        <main className="conversation-main space-y-4">
          <div className="workspace-breadcrumb">Workspace <span>/</span> {workspaces.find(w => w.id === wsId)?.name ?? "Overview"}</div>
          <section className="workspace-welcome">
            <span className="welcome-symbol" aria-hidden="true"><svg width="38" height="38" viewBox="0 0 38 38" fill="none"><path d="M19 4v30M4 19h30M8.4 8.4l21.2 21.2M8.4 29.6 29.6 8.4" stroke="currentColor" strokeWidth="2.5" /></svg></span>
            <h2>A clearer view of<br /><span>what you know.</span></h2>
            <p>Ask a question. Explore the evidence. Make your next move.</p>
          </section>
          {!wsId ? (
            <Empty title="Select a workspace" hint="Create one to start ingesting documents." />
          ) : (
            <>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!question.trim()) return;
                  if (multiMode) askMulti.mutate();
                  else ask.mutate();
                }}
                className="question-composer space-y-2"
              >
                <div className="flex gap-2">
                  <input
                    aria-label="Question about your documents"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask about your documents…"
                    className="flex-1 bg-white border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:border-sky-600"
                  />
                  <button
                    disabled={ask.isPending || askMulti.isPending || !question.trim()}
                    className="px-4 py-2 rounded bg-sky-700 hover:bg-sky-800 text-sm disabled:opacity-50"
                  >
                    {ask.isPending || askMulti.isPending
                      ? "thinking…"
                      : multiMode
                        ? "Ask all models"
                        : "Ask"}
                  </button>
                </div>
                <label className="text-xs text-slate-500 flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={multiMode}
                    onChange={(e) => setMultiMode(e.target.checked)}
                    className="accent-sky-700"
                  />
                  Compare local models <span className="mode-help">Independent answers, one synthesis</span>
                </label>
              </form>
              {!task && !multi && <div className="starter-area"><p>Start with a question</p><div className="starter-questions">{["Summarize the key points in my documents", "Which claims are supported by the sources?", "What needs a closer look?"].map(prompt => <button type="button" key={prompt} onClick={() => setQuestion(prompt)}>{prompt}<span aria-hidden="true">↗</span></button>)}</div><p className="evidence-note">AI can make mistakes. Review the cited evidence before acting.</p></div>}

              {task && <TaskView task={task} onDecide={(a) => decide.mutate({ taskId: task.task_id, approved: a })} />}
              {multi && <MultiModelView result={multi} />}
            </>
          )}
          {error && <p role="alert" className="text-sm text-red-700 border border-red-200 rounded p-3">{error}</p>}
        </main>
      </div>
    </div>
  );
}

function MultiModelView({ result }: { result: MultiModelResult }) {
  const pct = (n?: number) => `${((n ?? 0) * 100).toFixed(0)}%`;
  return (
    <div className="space-y-3">
      {/* combined answer first */}
      <div className="bg-white border border-sky-200 rounded p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span className="px-2 py-0.5 rounded border border-sky-200 bg-sky-50 text-sky-800 font-medium">
            Combined · {result.models_used.length} models
          </span>
          <span>{result.synthesizer === "source_union" ? "Combined source excerpts" : `synthesizer: ${result.synthesizer}`}</span>
          {result.verification?.decision && (
            <span>
              · {result.verification.method === "source_excerpt_match" ? "Cited text matched" : result.verification.decision}
              {result.verification.confidence !== undefined && ` · ${pct(result.verification.confidence)} source checks passed`}
            </span>
          )}
        </div>
        <p className="text-sm whitespace-pre-wrap">{result.combined_answer}</p>
        {result.verification?.method === "source_excerpt_match" && <p className="text-xs text-slate-500">Source matches confirm attribution. Review whether the excerpts fully answer your question.</p>}
        <EvidenceList evidence={result.evidence ?? []} />
      </div>

      {/* agreement */}
      <div className="bg-white border border-slate-200 rounded p-4 text-xs space-y-1">
        <p className="text-slate-600 font-medium">Lexical overlap between answers</p>
        <p className="text-slate-500">
          mean overlap {pct(result.agreement.mean_overlap)} · {result.agreement.n_answered} answered
        </p>
        {result.agreement.pairs.map((p) => (
          <p key={p.a + p.b} className="text-slate-500">
            {p.a} ↔ {p.b}: {pct(p.overlap)}
          </p>
        ))}
      </div>

      {/* individual answers */}
      <div className="space-y-2">
        {result.individual_answers.map((a) => (
          <details key={a.model} className="bg-white border border-slate-200 rounded p-3">
            <summary className="text-xs text-slate-600 cursor-pointer flex gap-3 items-center">
              <span className="font-medium text-slate-800">{a.model}</span>
              <span>{a.latency_ms} ms</span>
              {a.error && <span className="text-red-700">failed</span>}
              {!a.error && a.citations.length > 0 && (
                <span className="text-slate-600">{a.citations.length} citations</span>
              )}
            </summary>
            <p className="text-sm whitespace-pre-wrap mt-2 text-slate-700">
              {a.error ? <span className="text-red-700">{a.error}</span> : a.answer}
            </p>
            {a.citations.length > 0 && (
              <p className="text-xs text-slate-600 mt-2">cites: {a.citations.join(" · ")}</p>
            )}
          </details>
        ))}
      </div>
    </div>
  );
}

function TaskView({ task, onDecide }: { task: Task; onDecide: (approved: boolean) => void }) {
  return (
    <div className="space-y-3">
      <div className="text-xs text-slate-500 flex gap-3">
        <span>task {task.task_id.slice(0, 8)}</span>
        <span>·</span>
        <span>{task.status}</span>
      </div>

      {task.steps.map((s) => (
        <div key={s.key} className="text-xs text-slate-500">
          {s.action} — {s.status}
        </div>
      ))}

      {task.status === "WAITING_FOR_APPROVAL" && (
        <div className="border border-amber-200 bg-amber-50 rounded p-4 space-y-3">
          <p className="text-sm text-amber-900">
            Approval required: <b>{task.approvals[0]?.tool}</b>
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => onDecide(true)}
              className="text-sm px-3 py-1.5 rounded bg-emerald-700 text-white hover:bg-emerald-600"
            >
              Approve
            </button>
            <button
              onClick={() => onDecide(false)}
              className="text-sm px-3 py-1.5 rounded bg-slate-100 hover:bg-slate-200"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {task.result?.error && (
        <p className="text-sm text-red-700 border border-red-200 rounded p-3">{task.result.error}</p>
      )}

      {task.result?.answer && (
        <div className="bg-white border border-slate-200 rounded p-4 space-y-3">
          <p className="text-sm whitespace-pre-wrap">{task.result.answer}</p>
          <Verification result={task.result} />
          <EvidenceList evidence={task.result.evidence ?? []} />
        </div>
      )}
    </div>
  );
}

const VERDICT: Record<string, { label: string; className: string }> = {
  verified: { label: "Verified", className: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  partially_verified: { label: "Partly verified", className: "bg-amber-50 text-amber-800 border-amber-200" },
  unverified: { label: "Not verified", className: "bg-red-50 text-red-800 border-red-200" },
  illustrative_preview: { label: "Sample response", className: "bg-sky-50 text-sky-800 border-sky-200" },
  not_found: { label: "Not in your documents", className: "bg-slate-100 text-slate-700 border-slate-200" },
};

function Verification({ result }: { result: TaskResult }) {
  const verdict = VERDICT[result.decision ?? ""];
  const v = result.verification;
  const pct = (n?: number) => `${((n ?? 0) * 100).toFixed(0)}%`;
  return (
    <div className="space-y-2 text-xs">
      <div className="flex flex-wrap items-center gap-2 text-slate-500">
        {verdict && (
          <span className={`px-2 py-0.5 rounded border font-medium ${verdict.className}`}>
            {verdict.label}
            {result.confidence !== undefined && result.decision !== "not_found" && ` · ${pct(result.confidence)} confidence`}
          </span>
        )}
        {result.retrieval_score !== undefined && <span>retrieval match {pct(result.retrieval_score)}</span>}
        {result.answer_model && <span>· answered by {result.answer_model}</span>}
        {v?.model && <span>· checked by {v.model}</span>}
      </div>
      {v?.error && <p className="text-red-700">verification failed: {v.error}</p>}
      {(v?.claims ?? []).length > 0 && (
        <ul className="space-y-1">
          {v!.claims.map((c, i) => (
            <li key={i} className={c.supported ? "text-emerald-700" : "text-red-700"}>
              {c.supported ? "✓" : "✗"} {c.claim}
              {c.source > 0 && <span className="text-slate-500"> [{c.source}]</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) return null;
  return (
    <details open className="text-xs">
      <summary className="cursor-pointer text-slate-600">
        sources ({evidence.length})
      </summary>
      <ul className="mt-2 space-y-2">
        {evidence.map((e, i) => (
          <li key={e.chunk_id} className="border-l border-slate-200 pl-3">
            <span className="text-slate-500">
              [{i + 1}] <span className="text-slate-700">{e.filename}</span>
              {e.location ? ` · ${e.location}` : ""} · match {(e.score * 100).toFixed(0)}%
            </span>
            <p className="text-slate-600 mt-1 line-clamp-3">{e.content}</p>
          </li>
        ))}
      </ul>
    </details>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === "INDEXED"
      ? "text-emerald-700"
      : status === "FAILED"
        ? "text-red-700"
        : status === "PROCESSING"
          ? "text-amber-700"
          : "text-slate-500";
  return <span className={color}>{status.toLowerCase()}</span>;
}

function Empty({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <h2 className="text-lg font-medium text-slate-700">{title}</h2>
      <p className="text-sm text-slate-500 mt-1">{hint}</p>
    </div>
  );
}

function ModelPicker({ token, apiClient: api = liveApi }: { token: string; apiClient?: typeof liveApi }) {
  const qc = useQueryClient();
  const models = useQuery({ queryKey: ["models", token], queryFn: () => api.models(token) });
  const switchModel = useMutation({
    mutationFn: (p: { role: "answerer" | "verifier"; model: string }) =>
      api.setModel(token, p.model, p.role),
    onSettled: () => qc.invalidateQueries({ queryKey: ["models"] }),
  });

  if (models.isError) return <span className="text-xs text-red-700">model server offline</span>;
  if (!models.data) return <span className="text-xs text-slate-500">loading models…</span>;

  // embedding models are fixed (changing them would invalidate indexed documents);
  // LM Studio reports vision models (Gemma 4, Qwen-VL…) as "vlm" and they chat fine
  const chat = models.data.models.filter((m) => m.type !== "embeddings");
  const { active, verifier, can_switch } = models.data;
  const pending = switchModel.isPending ? switchModel.variables : null;
  return (
    <div className="flex items-center gap-3 text-xs">
      <ModelSelect
        label="Answer"
        models={chat}
        value={pending?.role === "answerer" ? pending.model : active}
        disabled={!can_switch || switchModel.isPending}
        onChange={(model) => switchModel.mutate({ role: "answerer", model })}
      />
      <ModelSelect
        label="Verify"
        models={chat}
        value={pending?.role === "verifier" ? pending.model : verifier}
        sameAs={active}
        disabled={!can_switch || switchModel.isPending}
        onChange={(model) => switchModel.mutate({ role: "verifier", model })}
      />
      {switchModel.isPending && <span className="text-amber-700">loading model…</span>}
      {switchModel.isError && (
        <span className="text-red-700 max-w-48 truncate" title={String(switchModel.error)}>
          switch failed
        </span>
      )}
    </div>
  );
}

function ModelSelect({
  label,
  models,
  value,
  sameAs,
  disabled,
  onChange,
}: {
  label: string;
  models: LocalModel[];
  value: string;
  sameAs?: string;
  disabled: boolean;
  onChange: (model: string) => void;
}) {
  const id = `model-${label}`;
  return (
    <span className="flex items-center gap-1.5">
      <label htmlFor={id} className="text-slate-500">
        {label}
      </label>
      <select
        id={id}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="bg-white border border-slate-200 rounded px-2 py-1.5 text-slate-800 disabled:opacity-60 max-w-56"
      >
        {sameAs !== undefined && <option value="">same as answer model</option>}
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {m.id}
            {m.state === "preview" ? " (preview)" : m.state === "loaded" ? " (loaded)" : m.state ? " (on disk)" : ""}
          </option>
        ))}
        {value && !models.some((m) => m.id === value) && (
          <option value={value}>{value} (not found)</option>
        )}
      </select>
    </span>
  );
}
