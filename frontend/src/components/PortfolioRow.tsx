"use client";

import { useApp } from "@/lib/store";
import { cls } from "@/lib/format";
import { Badge } from "@/components/ui";
import type { Portfolio } from "@/lib/types";

export function PortfolioRow({ p }: { p: Portfolio }) {
  const { selectedPortfolioId, selectPortfolio } = useApp();
  const selected = selectedPortfolioId === p.id;
  return (
    <button
      onClick={() => selectPortfolio(selected ? null : p.id)}
      className={cls(
        "w-full rounded-lg border px-4 py-3 text-left transition-colors",
        selected ? "border-teal-500 bg-teal-50/70 ring-1 ring-teal-500" : "border-slate-200 bg-white hover:border-slate-300"
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-slate-400">{p.id}</span>
          <span className="text-sm font-medium text-slate-800">{p.name}</span>
          {selected && <Badge color="teal">selected</Badge>}
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Badge color="amber">{p.cost_crores.toFixed(1)} Cr</Badge>
          <Badge color="blue">{p.water_security_score} water score</Badge>
          <Badge color="violet">{p.jobs_created} jobs</Badge>
          <Badge>{p.intervention_count} interventions</Badge>
        </div>
      </div>
      <p className="mt-1 text-xs text-slate-500">{p.focus}</p>
      {p.sdg_alignments.length > 0 && (
        <div className="mt-1.5 text-[11px] text-slate-400">SDG {p.sdg_alignments.join(" · ")}</div>
      )}
    </button>
  );
}
