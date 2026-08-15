"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { Alert, Button, Field, TextInput } from "@/components/ui";
import { PERSONAS } from "@/lib/types";
import { cls } from "@/lib/format";

export default function LoginPage() {
  const router = useRouter();
  const { setAuth, persona, setWorkspace } = useApp();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("officer@mp.gov.in");
  const [password, setPassword] = useState("secret");
  const [name, setName] = useState("District Officer");
  const [selectedPersona, setSelectedPersona] = useState(persona ?? "GOVERNMENT");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") {
        await api.register({ email, password, name });
      }
      const login = await api.login({ email, password });
      const me = await api.me(login.access_token);
      setAuth(login.access_token, me, selectedPersona);
      // Pre-load workspace context so the next step has data instantly.
      try {
        const ws = await api.workspaceCurrent(selectedPersona, login.access_token);
        setWorkspace(ws);
      } catch {
        /* workspace will be set in step 2 */
      }
      router.replace("/app/workspace");
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-slate-900 p-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              "radial-gradient(600px 300px at 20% 10%, rgba(45,212,191,.35), transparent), radial-gradient(500px 400px at 90% 80%, rgba(16,185,129,.3), transparent)",
          }}
        />
        <div className="relative flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-emerald-600 font-bold">
            NX
          </div>
          <div>
            <div className="text-lg font-semibold tracking-wide">NEXUS</div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-teal-300/80">
              Community Development Intelligence
            </div>
          </div>
        </div>

        <div className="relative max-w-md">
          <h1 className="text-3xl font-semibold leading-snug">
            From satellite signals to an actionable water plan.
          </h1>
          <p className="mt-4 text-sm leading-relaxed text-slate-300">
            NEXUS fuses Earth observation, water intelligence, intervention knowledge
            graphs, feasibility filtering and NSGA-II multi-objective optimization into
            explainable portfolios — so officers can compare cost, impact, time and risk
            trade-offs before committing public funds.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-3 text-center">
            {[
              ["7", "pipeline stages"],
              ["39", "Pareto plans"],
              ["4", "objectives"],
            ].map(([v, l]) => (
              <div key={l} className="rounded-xl border border-white/10 bg-white/5 px-3 py-3">
                <div className="text-xl font-semibold text-teal-300">{v}</div>
                <div className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-400">{l}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative text-[11px] text-slate-500">
          Demo instance · backend v2.0.0 · mock auth store — no real credentials required.
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex w-full items-center justify-center bg-slate-50 px-6 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-emerald-600 font-bold text-white">
                NX
              </div>
              <div>
                <div className="font-semibold">NEXUS</div>
                <div className="text-[10px] uppercase tracking-widest text-slate-500">Water Intelligence</div>
              </div>
            </div>
          </div>

          <h2 className="text-xl font-semibold text-slate-900">
            {mode === "login" ? "Sign in to your workspace" : "Create an account"}
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {mode === "login"
              ? "Continue as a government officer or pick a persona below."
              : "Register, then choose the persona that fits your role."}
          </p>

          <div className="mt-5 grid grid-cols-3 gap-2">
            {PERSONAS.map((p) => (
              <button
                key={p.value}
                type="button"
                onClick={() => setSelectedPersona(p.value)}
                title={p.blurb}
                className={cls(
                  "rounded-lg border px-2 py-2 text-[11px] font-medium transition-colors",
                  selectedPersona === p.value
                    ? "border-teal-500 bg-teal-50 text-teal-700"
                    : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                )}
              >
                {p.label}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="mt-6 space-y-4">
            <Field label="Email">
              <TextInput
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@mp.gov.in"
              />
            </Field>
            <Field label="Password">
              <TextInput
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </Field>
            {mode === "register" && (
              <Field label="Full name">
                <TextInput required value={name} onChange={(e) => setName(e.target.value)} />
              </Field>
            )}

            {error && <Alert tone="error">{error}</Alert>}

            <Button type="submit" size="lg" loading={busy} className="w-full">
              {mode === "login" ? "Sign in" : "Register & sign in"}
            </Button>
          </form>

          <button
            onClick={() => setMode(mode === "login" ? "register" : "login")}
            className="mt-4 w-full text-center text-xs text-slate-500 hover:text-teal-600"
          >
            {mode === "login" ? "New here? Create an account" : "Already registered? Sign in"}
          </button>

          <p className="mt-6 text-center text-[11px] text-slate-400">
            Pre-filled demo credentials work out of the box (mock auth backend).
          </p>
        </div>
      </div>
    </div>
  );
}
