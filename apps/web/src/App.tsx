import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import Workbench from "./Workbench";

type Session = { token: string; email: string };

export default function App() {
  const [session, setSession] = useState<Session | null>(() => {
    const raw = localStorage.getItem("session");
    return raw ? JSON.parse(raw) : null;
  });
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  // keep API honest: verify token on mount
  useQuery({
    queryKey: ["workspaces", session?.token],
    queryFn: () => api.workspaces(session!.token),
    enabled: !!session,
    retry: false,
  });

  if (session) {
    return (
      <Workbench
        session={session}
        onLogout={() => {
          localStorage.removeItem("session");
          setSession(null);
        }}
      />
    );
  }

  const login = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const r = await api.login(email, password);
      const s = { token: r.token, email: r.user.email };
      localStorage.setItem("session", JSON.stringify(s));
      setSession(s);
    } catch {
      setError("Invalid email or password");
    }
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center px-6">
      <form onSubmit={login} className="w-full max-w-sm space-y-4">
        <div className="text-center space-y-1 mb-8">
          <h1 className="text-2xl font-semibold tracking-tight">
            Sovereign Agentic AI Workbench
          </h1>
          <p className="text-sm text-neutral-500">
            Local models. Your data never leaves the building.
          </p>
        </div>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full bg-neutral-900 border border-neutral-800 rounded px-3 py-2 text-sm"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full bg-neutral-900 border border-neutral-800 rounded px-3 py-2 text-sm"
          required
        />
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button className="w-full py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-sm font-medium">
          Sign in
        </button>
        <p className="text-xs text-neutral-600 text-center">
          Dev bootstrap: admin@example.com / Admin#Dev1 (from .env)
        </p>
      </form>
    </main>
  );
}
