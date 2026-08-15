"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { cls, crores, dateShort, inr, riskColor } from "@/lib/format";
import { Alert, Badge, Button, Card, EmptyState, Spinner, Stat } from "@/components/ui";
import { PortfolioRow } from "@/components/PortfolioRow";
import type { ImplementationPlan, Portfolio } from "@/lib/types";

export default function PortfoliosPage() {
  const router = useRouter();
  const { result, selectedPortfolioId } = useApp();
  const [portfolios, setPortfolios] = useState<Portfolio[]>(result?.optimization.top_portfolios ?? []);
  const [loading, setLoading] = useState(result ? result.optimization.top_portfolios.length === 0 : true);
  const [error, setError] = useState<string | null>(null);

  // Show the pipeline's top portfolios instantly, then swap in the full
  // Pareto frontier from /portfolio/pareto once it arrives.
  useEffect(() => {
    let ignore = false;
    api.pareto()
      .then((r) => {
        if (!ignore) setPortfolios(r.portfolios);
      })
      .catch((e) => {
        if (!ignore && portfolios.length === 0) setError(errMsg(e));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = portfolios.find((p) => p.id === selectedPortfolioId) ?? null;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Portfolios & implementation plan</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">
          Compare Pareto-optimal plans across cost, water security, jobs and SDG alignment — then
          generate a phased implementation plan with stakeholder allocation and monitoring indicators.
        </p>
      </div>

      {portfolios.length === 0 && !loading && !error && (
        <Card>
          <EmptyState
            title="No portfolios yet"
            body="Run the analysis pipeline (or the optimizer) to generate Pareto-optimal portfolios."
          />
          <div className="mt-4 flex gap-2">
            <Button onClick={() => router.push("/app/analysis")}>Run analysis →</Button>
            <Button variant="secondary" onClick={() => router.push("/app/feasibility")}>Optimizer</Button>
          </div>
        </Card>
      )}
      {loading && <div className="flex items-center gap-2 text-sm text-slate-400"><Spinner /> Loading Pareto portfolios…</div>}
      {error && <Alert tone="error">{error}</Alert>}

      {portfolios.length > 0 && (
        <Card
          title={`Pareto-optimal portfolios (${portfolios.length})`}
          subtitle="Click a portfolio to select it — the implementation plan and provenance load below"
          icon={<span>📊</span>}
          actions={<Badge color="teal">{result?.optimization.pareto_solutions_count ?? portfolios.length} solutions on frontier</Badge>}
        >
          <div className="max-h-[420px] space-y-2 overflow-y-auto pr-1">
            {portfolios.map((p) => <PortfolioRow key={p.id} p={p} />)}
          </div>
        </Card>
      )}

      {selected && (
        <>
          <PortfolioDetail p={selected} />
          <ImplementationPlanView portfolioId={selected.id} />
        </>
      )}
    </div>
  );
}

// ---------- Portfolio detail ----------

function PortfolioDetail({ p }: { p: Portfolio }) {
  return (
    <Card
      title={p.name}
      subtitle={p.focus}
      icon={<span>💼</span>}
      actions={<Badge color="teal">{p.id}</Badge>}
    >
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Total cost" value={crores(p.cost_crores)} sub={inr(p.total_cost_inr)} accent />
        <Stat label="Water security" value={p.water_security_score} sub="cumulative score" />
        <Stat label="Jobs created" value={p.jobs_created} sub="direct + indirect" />
        <Stat label="SDG coverage" value={p.sdg_count} sub={p.sdg_alignments.join(" · ")} />
      </div>

      <div className="mt-5 grid gap-6 lg:grid-cols-2">
        <div>
          <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Interventions ({p.intervention_count})
          </div>
          <ul className="space-y-2">
            {p.interventions.map((it) => (
              <li key={it.id} className="rounded-lg border border-slate-200 px-3 py-2.5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="font-mono text-[10px] text-slate-400">{it.id}</span>
                    <span className="ml-2 text-sm font-medium text-slate-800">{it.name}</span>
                  </div>
                  <Badge className={riskColor(it.risk_level)}>{it.risk_level}</Badge>
                </div>
                <div className="mt-1.5 flex flex-wrap gap-1.5 text-[11px]">
                  <Badge color="amber">{inr(it.cost_inr, true)}</Badge>
                  <Badge color="blue">{it.water_security_score} score</Badge>
                  <Badge color="violet">{it.jobs_created} jobs</Badge>
                  <Badge>{it.implementation_time_months} mo</Badge>
                  <Badge>maturity {it.technology_maturity_lvl}/10</Badge>
                </div>
                {it.description && <p className="mt-1.5 text-xs text-slate-500">{it.description}</p>}
              </li>
            ))}
          </ul>
        </div>

        <div className="space-y-4">
          <div>
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">Co-benefits</div>
            {p.co_benefits.length === 0 ? (
              <p className="text-xs text-slate-400">None listed</p>
            ) : (
              <ul className="flex flex-wrap gap-1.5">
                {p.co_benefits.map((c, i) => <Badge key={i} color="emerald">{c}</Badge>)}
              </ul>
            )}
          </div>
          <div>
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">Applicable conditions</div>
            <dl className="space-y-1.5">
              {Object.entries(p.applicable_conditions ?? {}).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-slate-100 pb-1 text-xs">
                  <dt className="text-slate-500">{k.replace(/_/g, " ")}</dt>
                  <dd className="font-medium text-slate-700">{String(v)}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div>
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">Method</div>
            <p className="text-xs text-slate-500">{String(p.provenance?.method ?? "pymoo NSGA-II multi-objective genetic algorithm")}</p>
          </div>
        </div>
      </div>
    </Card>
  );
}

// ---------- Implementation plan ----------

function ImplementationPlanView({ portfolioId }: { portfolioId: string }) {
  const { token } = useApp();
  const [plan, setPlan] = useState<ImplementationPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prevId, setPrevId] = useState(portfolioId);

  // Render-time adjustment: reset when switching portfolios.
  if (prevId !== portfolioId) {
    setPrevId(portfolioId);
    setPlan(null);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let ignore = false;
    api.implementationPlan(portfolioId, token)
      .then((p) => {
        if (!ignore) setPlan(p);
      })
      .catch((e) => {
        if (!ignore) setError(errMsg(e));
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [portfolioId, token]);

  if (loading) return <div className="flex items-center gap-2 text-sm text-slate-400"><Spinner /> Generating implementation plan…</div>;
  if (error) return <Alert tone="error">{error}</Alert>;
  if (!plan) return null;

  const maxPhase = Math.max(...plan.intervention_sequence.map((s) => s.phase), 1);
  const totalCost = plan.total_cost_inr;

  return (
    <Card
      title="Implementation plan"
      subtitle={`${plan.portfolio_name} · generated ${dateShort(plan.created_at)}`}
      icon={<span>🗓️</span>}
      actions={
        <div className="flex gap-2">
          <Badge color="teal">{plan.total_duration_months} months</Badge>
          <Badge color="amber">{crores(totalCost / 1e7)}</Badge>
        </div>
      }
    >
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <div className="mb-3 text-[11px] font-medium uppercase tracking-wide text-slate-500">Phased intervention sequence</div>
          <div className="space-y-0">
            {Array.from({ length: maxPhase }, (_, i) => i + 1).map((phase) => {
              const steps = plan.intervention_sequence.filter((s) => s.phase === phase);
              if (steps.length === 0) return null;
              return (
                <div key={phase} className="relative border-l-2 border-teal-200 pb-5 pl-5 last:pb-0">
                  <span className="absolute -left-[9px] top-0 flex h-4 w-4 items-center justify-center rounded-full bg-teal-500 text-[8px] font-bold text-white">
                    {phase}
                  </span>
                  <div className="text-xs font-semibold text-slate-700">{steps[0].phase_name}</div>
                  <ul className="mt-2 space-y-2">
                    {steps.map((s) => (
                      <li key={s.intervention_id} className="rounded-lg border border-slate-200 bg-slate-50/50 px-3 py-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-[13px] font-medium text-slate-800">{s.intervention_name}</span>
                          <div className="flex gap-1.5">
                            <Badge color="amber">{inr(s.estimated_cost_inr, true)}</Badge>
                            <Badge>{s.duration_months} mo</Badge>
                          </div>
                        </div>
                        <div className="mt-1 text-[11px] text-slate-500">
                          {s.responsible_stakeholder}
                          {s.dependencies.length > 0 && <span className="ml-2">· depends on {s.dependencies.join(", ")}</span>}
                        </div>
                        {s.key_milestones.length > 0 && (
                          <div className="mt-1.5 flex flex-wrap gap-1">
                            {s.key_milestones.map((m, j) => <Badge key={j} color="blue">{m}</Badge>)}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>

        <div className="space-y-5">
          <div>
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">Stakeholder allocation</div>
            <ul className="space-y-2">
              {Object.entries(plan.stakeholder_allocation).map(([k, v]) => (
                <li key={k}>
                  <div className="flex items-baseline justify-between gap-3 text-[13px]">
                    <span className="text-slate-600">{k}</span>
                    <span className="font-semibold text-slate-800">{inr(v, true)}</span>
                  </div>
                  <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-500"
                      style={{ width: `${totalCost ? (v / totalCost) * 100 : 0}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">Monitoring indicators</div>
            <ul className="space-y-2">
              {plan.monitoring_indicators.map((m, i) => (
                <li key={i} className="rounded-lg border border-slate-200 px-3 py-2">
                  <div className="text-[13px] font-medium text-slate-800">{m.indicator}</div>
                  <div className="mt-0.5 flex gap-2 text-[11px] text-slate-500">
                    <Badge color="violet">every {m.frequency.toLowerCase()}</Badge>
                    <Badge color="emerald">target {m.target}</Badge>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className={cls("rounded-lg border border-teal-200 bg-teal-50/60 px-4 py-3 text-xs text-teal-800")}>
            <span className="font-semibold">Total:</span> {crores(totalCost / 1e7)} across {plan.total_duration_months} months ·
            new satellite & environmental data can be re-ingested to monitor progress against these indicators.
          </div>
        </div>
      </div>
    </Card>
  );
}
