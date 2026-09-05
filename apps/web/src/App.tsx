import { useQuery } from "@tanstack/react-query";

type Health = { status: string; components: Record<string, { status: string }> };

async function fetchHealth(): Promise<Health> {
  const res = await fetch("/healthz");
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  return res.json();
}

export default function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
  });

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col">
      <header className="border-b border-neutral-800 px-8 py-5 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">
            Sovereign Agentic AI Workbench
          </h1>
          <p className="text-sm text-neutral-400">
            Local models. Your data never leaves the building.
          </p>
        </div>
        <HealthBadge data={data} isLoading={isLoading} isError={isError} />
      </header>

      <section className="flex-1 flex items-center justify-center px-8">
        <div className="max-w-xl text-center space-y-4">
          <h2 className="text-3xl font-semibold tracking-tight">
            Grounded answers from your own documents
          </h2>
          <p className="text-neutral-400">
            Sign in to create a workspace, ingest PDFs, spreadsheets and code,
            then ask questions that cite only internal evidence — every tool
            call and approval is audited on-premise.
          </p>
          <p className="text-sm text-neutral-500">
            Authentication and workspaces arrive with the next build
            increments (P1-F-001…004).
          </p>
        </div>
      </section>

      <footer className="border-t border-neutral-800 px-8 py-3 text-xs text-neutral-500">
        Project 1 of 5 — SIH 2026 · local-only mode enforced by policy
      </footer>
    </main>
  );
}

function HealthBadge({
  data,
  isLoading,
  isError,
}: {
  data?: Health;
  isLoading: boolean;
  isError: boolean;
}) {
  if (isLoading) {
    return (
      <span className="text-sm px-3 py-1 rounded-full bg-neutral-800 text-neutral-400">
        checking…
      </span>
    );
  }
  if (isError || !data) {
    return (
      <span className="text-sm px-3 py-1 rounded-full bg-red-950 text-red-300">
        API unreachable
      </span>
    );
  }
  const ok = data.status === "ok";
  return (
    <span
      className={
        "text-sm px-3 py-1 rounded-full " +
        (ok ? "bg-emerald-950 text-emerald-300" : "bg-amber-950 text-amber-300")
      }
    >
      API {data.status}
    </span>
  );
}
