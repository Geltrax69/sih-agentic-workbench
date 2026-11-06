import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import Workbench from "./Workbench";
import { previewApi } from "./preview";

type Session = { token: string; email: string };

export default function App() {
  const [preview, setPreview] = useState(new URLSearchParams(location.search).has("preview"));
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
    enabled: !!session && !preview,
    retry: false,
  });

  if (session || preview) {
    return (
      <Workbench
        session={preview ? { token: "preview", email: "Preview workspace" } : session!}
        apiClient={preview ? previewApi : api}
        preview={preview}
        onLogout={() => {
          if (preview) { setPreview(false); history.replaceState(null, "", location.pathname); return; }
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
    <main className="login-shell">
      <section className="login-story">
        <a className="brand" href="/" aria-label="Sovereign home"><BrandMark /> sovereign<span className="brand-tag">WORKBENCH</span></a>
        <div className="login-story-copy"><h1>Your knowledge.<br />A little more<br /><span>intelligent.</span></h1>
        <p>A private space to turn your organization’s documents into answers you can trace.</p>
        <div className="story-pipeline"><span>Retrieve</span><span>Compare</span><span>Verify</span></div></div>
        <p className="story-footer">Built for local models. Designed for human oversight.</p>
      </section>
      <section className="login-panel"><form onSubmit={login} className="login-form">
        <span className="private-badge"><span /> Your private workspace</span>
        <h2>Good to have you back.</h2>
        <p className="login-description">Sign in to work with your documents and local AI models.</p>
        <label htmlFor="email">Email address</label>
        <input
          id="email" autoComplete="username"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm"
          required
        />
        <label htmlFor="password">Password</label>
        <input
          id="password" autoComplete="current-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full bg-white border border-slate-200 rounded px-3 py-2 text-sm"
          required
        />
        {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
        <button type="submit" className="w-full py-2 rounded bg-sky-700 hover:bg-sky-800 text-sm font-medium">
          Open workbench <span aria-hidden="true">↗</span>
        </button>
        <div className="login-divider"><span>Take a look around</span></div>
        <button type="button" className="preview-button" onClick={() => { history.replaceState(null, "", "?preview=1"); setPreview(true); }}>Explore the UI preview <span aria-hidden="true">→</span></button>
        <p className="login-note">Preview uses sample data. No account or model connection needed.</p>
      </form><p className="login-bottom">Sovereign Agentic AI Workbench · Local by design</p></section>
    </main>
  );
}

export function BrandMark() {
  return <svg width="27" height="27" viewBox="0 0 27 27" fill="none" aria-hidden="true"><path d="M3 17 10 4h7l-7 13H3Zm7 6 7-13h7l-7 13h-7Z" fill="currentColor" /></svg>;
}
