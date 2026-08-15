"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useApp, useAuthed } from "@/lib/store";
import { cls } from "@/lib/format";

const STEPS = [
  { id: "workspace", n: 1, label: "Workspace", path: "/app/workspace", blurb: "Persona & region" },
  { id: "inputs", n: 2, label: "Inputs", path: "/app/inputs", blurb: "Budget · locations · social · timeline · maps" },
  { id: "analysis", n: 3, label: "Analysis", path: "/app/analysis", blurb: "EO · water intelligence · problems · knowledge graph" },
  { id: "feasibility", n: 4, label: "Feasibility & Optimize", path: "/app/feasibility", blurb: "Constraints · NSGA-II · provenance" },
  { id: "portfolios", n: 5, label: "Portfolios & Plan", path: "/app/portfolios", blurb: "Compare plans · implementation" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, workspace, result, logout } = useApp();
  const authed = useAuthed();

  useEffect(() => {
    if (!authed) router.replace("/login");
  }, [authed, router]);

  if (!authed) return null;

  const currentIdx = STEPS.findIndex((s) => pathname.startsWith(s.path));
  const activeIdx = currentIdx === -1 ? 0 : currentIdx;

  return (
    <div className="flex min-h-screen bg-slate-100">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-20 flex w-64 flex-col bg-slate-900 text-slate-300">
        <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-teal-400 to-emerald-600 text-sm font-bold text-white">
            NX
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide text-white">NEXUS</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">Water Intelligence</div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {STEPS.map((s, i) => {
            const done = i < activeIdx;
            const active = i === activeIdx;
            return (
              <Link
                key={s.id}
                href={s.path}
                className={cls(
                  "group flex items-start gap-3 rounded-lg px-3 py-2.5 transition-colors",
                  active ? "bg-teal-600/15 text-white" : "hover:bg-slate-800/70 hover:text-white"
                )}
              >
                <span
                  className={cls(
                    "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold",
                    active ? "bg-teal-500 text-white" : done ? "bg-emerald-600/80 text-white" : "bg-slate-700 text-slate-400"
                  )}
                >
                  {done ? "✓" : s.n}
                </span>
                <span className="min-w-0">
                  <span className={cls("block text-[13px] font-medium", active ? "text-white" : "")}>{s.label}</span>
                  <span className="block truncate text-[10px] text-slate-500">{s.blurb}</span>
                </span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 px-5 py-4">
          {workspace ? (
            <div className="mb-3 rounded-lg bg-slate-800/70 px-3 py-2">
              <div className="truncate text-xs font-medium text-slate-200">{workspace.geography_name}</div>
              <div className="text-[10px] text-slate-500">
                bbox {workspace.bbox.map((v) => v.toFixed(2)).join(", ")}
              </div>
            </div>
          ) : null}
          <div className="flex items-center justify-between">
            <div className="min-w-0">
              <div className="truncate text-xs font-medium text-slate-200">{user?.name ?? "Officer"}</div>
              <div className="truncate text-[10px] text-slate-500">{user?.email}</div>
            </div>
            <button
              onClick={() => { logout(); router.replace("/login"); }}
              className="rounded-md px-2 py-1 text-[11px] text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="ml-64 flex-1">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white/90 px-8 py-3 backdrop-blur">
          <div>
            <h1 className="text-sm font-semibold text-slate-800">
              {STEPS[activeIdx]?.label ?? "NEXUS"}
            </h1>
            <p className="text-[11px] text-slate-500">
              {result ? "Analysis complete — results available below" : "Community Development Intelligence"}
            </p>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-slate-500">
            <span className="hidden items-center gap-1.5 sm:flex">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              API online
            </span>
            <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 font-mono">v2.0.0</span>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-8 py-8">{children}</main>
      </div>
    </div>
  );
}
