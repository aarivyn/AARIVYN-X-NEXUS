"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { cls } from "@/lib/format";
import { Alert, Badge, Button, Card, EmptyState, Field, NumberInput, Spinner, Table } from "@/components/ui";
import { PortfolioRow } from "@/components/PortfolioRow";
import type { FeasibilityFilterRequest, Portfolio, ProvenanceAudit } from "@/lib/types";

export default function FeasibilityPage() {
  const { result } = useApp();
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Feasibility, optimization & provenance</h2>
        <p className="mt-1 max-w-3xl text-sm text-slate-500">
          The 4-stage filter (geographic · budget · time · risk) removes infeasible interventions; the
          NSGA-II solver then explores the Pareto frontier across cost ↓, water security ↑, jobs ↑ and
          SDG alignment ↑. Every output carries an explainability audit trail.
        </p>
      </div>

      {!result ? (
        <Card>
          <EmptyState
            title="Run the analysis pipeline first"
            body="Feasibility, optimization and provenance build on the pipeline result. Go to the Analysis step and run the master pipeline."
          />
          <div className="mt-4">
            <Button onClick={() => router.push("/app/analysis")}>Go to Analysis →</Button>
          </div>
        </Card>
      ) : (
        <>
          <FeasibilityMatrix />
          <OptimizerRunner />
          <ProvenanceCard />
        </>
      )}
    </div>
  );
}

// ---------- Feasibility ----------

function FeasibilityMatrix() {
  const { result } = useApp();
  const [matrix, setMatrix] = useState(result?.feasibility.filter_matrix ?? []);
  const [summary, setSummary] = useState({
    total: result?.feasibility.total_candidates ?? 0,
    viable: result?.feasibility.viable_candidates_count ?? 0,
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(true);

  async function refilter() {
    setBusy(true);
    setError(null);
    try {
      const req: FeasibilityFilterRequest = {
        candidate_intervention_ids: [],
        geography_id: result?.geography_id ?? "rewa",
        budget_limit_inr: 200000000,
        time_horizon_months: 36,
        max_risk_level: "HIGH",
      };
      const r = await api.feasibility(req);
      setMatrix(r.filter_matrix);
      setSummary({ total: r.total_candidates, viable: r.viable_candidates_count });
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  }

  const rows = showAll ? matrix : matrix.filter((m) => m.passed_all);

  return (
    <Card
      title="Feasibility filter matrix"
      subtitle="Per-intervention pass/fail across the four constraint stages"
      icon={<span>🔍</span>}
      actions={
        <div className="flex items-center gap-2">
          <Badge color="slate">{summary.total} candidates</Badge>
          <Badge color="emerald">{summary.viable} viable</Badge>
          <Button variant="secondary" size="sm" onClick={refilter} loading={busy}>Re-run filter</Button>
        </div>
      }
    >
      {error && <Alert tone="error" className="mb-3">{error}</Alert>}
      <div className="mb-3 flex items-center gap-4 text-xs text-slate-500">
        <label className="flex items-center gap-1.5">
          <input type="checkbox" checked={showAll} onChange={(e) => setShowAll(e.target.checked)} className="accent-teal-600" />
          Show all candidates
        </label>
      </div>
      <Table head={["Intervention", "Geographic", "Budget", "Time", "Risk", "Verdict", "Failure reasons"]}>
        {rows.map((m) => (
          <tr key={m.intervention_id} className={cls(!m.passed_all && "bg-red-50/40")}>
            <td className="px-3 py-2.5">
              <span className="font-mono text-[10px] text-slate-400">{m.intervention_id}</span>
              <div className="font-medium text-slate-800">{m.intervention_name}</div>
            </td>
            <PassCell ok={m.geographic_filter_pass} />
            <PassCell ok={m.budget_filter_pass} />
            <PassCell ok={m.time_filter_pass} />
            <PassCell ok={m.risk_filter_pass} />
            <td className="px-3 py-2.5">
              {m.passed_all ? <Badge color="emerald">viable</Badge> : <Badge color="red">rejected</Badge>}
            </td>
            <td className="px-3 py-2.5 text-xs text-red-600">
              {m.failure_reasons?.length ? m.failure_reasons.join("; ") : "—"}
            </td>
          </tr>
        ))}
      </Table>
    </Card>
  );
}

function PassCell({ ok }: { ok: boolean }) {
  return (
    <td className="px-3 py-2.5">
      <span className={cls("inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold", ok ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-600")}>
        {ok ? "✓" : "✗"}
      </span>
    </td>
  );
}

// ---------- Optimizer ----------

function OptimizerRunner() {
  const { result, token } = useApp();
  const [portfolios, setPortfolios] = useState<Portfolio[]>(result?.optimization.top_portfolios ?? []);
  const [paretoCount, setParetoCount] = useState(result?.optimization.pareto_solutions_count ?? 0);
  const [budget, setBudget] = useState("200000000");
  const [horizon, setHorizon] = useState("36");
  const [weights, setWeights] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const r = await api.optimize(
        {
          geography_id: result?.geography_id ?? "rewa",
          budget_limit_inr: Number(budget),
          time_horizon_months: Number(horizon),
          objective_weights: weights.trim() ? weights.split(",").map((w) => Number(w.trim())) : null,
        },
        token
      );
      setPortfolios(r.portfolios);
      setParetoCount(r.pareto_solutions_count);
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card
      title="NSGA-II multi-objective optimizer"
      subtitle="4 objectives: cost ↓ · water security ↑ · jobs ↑ · SDG alignment ↑ (budget-constrained)"
      icon={<span>🧬</span>}
      actions={portfolios.length > 0 ? <Badge color="teal">{paretoCount} Pareto solutions</Badge> : undefined}
    >
      <form onSubmit={run} className="mb-5 grid gap-4 sm:grid-cols-3">
        <Field label="Budget limit (INR)">
          <NumberInput value={budget} onChange={(e) => setBudget(e.target.value)} />
        </Field>
        <Field label="Time horizon (months)">
          <NumberInput value={horizon} onChange={(e) => setHorizon(e.target.value)} />
        </Field>
        <Field label="Objective weights (optional)" hint="cost, water, jobs, sdg — e.g. 1,1,0.5,1">
          <input
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-mono text-slate-800 placeholder:text-slate-400 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
            value={weights}
            onChange={(e) => setWeights(e.target.value)}
            placeholder="1,1,0.5,1"
          />
        </Field>
        <div className="sm:col-span-3">
          <Button type="submit" loading={busy}>Run optimizer</Button>
        </div>
      </form>
      {error && <Alert tone="error" className="mb-4">{error}</Alert>}

      {portfolios.length === 0 ? (
        <EmptyState title="No portfolios generated" body="Run the optimizer (or the full pipeline) to see the Pareto-optimal portfolio set." />
      ) : (
        <div className="space-y-2">
          <div className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            Pareto-optimal portfolios ({portfolios.length} shown)
          </div>
          {portfolios.map((p) => (
            <PortfolioRow key={p.id} p={p} />
          ))}
        </div>
      )}
    </Card>
  );
}

// ---------- Provenance ----------

function ProvenanceCard() {
  const { token, selectedPortfolioId } = useApp();
  const [audit, setAudit] = useState<ProvenanceAudit | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prevPortfolioId, setPrevPortfolioId] = useState<string | null>(selectedPortfolioId);

  // Reset state when the selected portfolio changes (render-time adjustment —
  // the canonical React pattern for syncing state to a prop change).
  if (prevPortfolioId !== selectedPortfolioId) {
    setPrevPortfolioId(selectedPortfolioId);
    setAudit(null);
    setLoading(true);
    setError(null);
  }

  useEffect(() => {
    let ignore = false;
    if (!selectedPortfolioId) return;
    api.provenance(selectedPortfolioId, token)
      .then((a) => {
        if (!ignore) setAudit(a);
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
  }, [selectedPortfolioId, token]);

  return (
    <Card
      title="Provenance & explainability audit"
      subtitle="Select a portfolio above to inspect its audit trail"
      icon={<span>🛡️</span>}
    >
      {!selectedPortfolioId ? (
        <EmptyState
          title="No portfolio selected"
          body="Select one of the Pareto portfolios above (or in Portfolios & Plan) to load its explainability audit."
        />
      ) : loading ? (
        <div className="flex items-center gap-2 text-sm text-slate-400"><Spinner /> Loading audit…</div>
      ) : error ? (
        <Alert tone="error">{error}</Alert>
      ) : audit ? (
        <div className="grid gap-6 lg:grid-cols-2">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <span className="font-mono text-[11px] text-slate-400">{audit.portfolio_id}</span>
              <Badge color="teal">{audit.confidence_score}</Badge>
            </div>
            <p className="text-sm text-slate-700">{audit.portfolio_name}</p>
            <dl className="mt-4 space-y-2 text-sm">
              <AuditRow k="Optimizer engine" v={audit.optimizer_engine} />
              <AuditRow
                k="Objective weights"
                v={audit.objective_weights_applied ? Object.entries(audit.objective_weights_applied).map(([k, v]) => `${k}: ${v}`).join(" · ") : "defaults"}
              />
              <AuditRow k="EO scene IDs" v={audit.earth_observation_scene_ids.join(", ") || "—"} mono />
              <AuditRow k="STAC provenance" v={audit.satellite_stac_provenance ? Object.keys(audit.satellite_stac_provenance).join(", ") : "—"} />
            </dl>
          </div>
          <div>
            <div className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">Feasibility filter audit</div>
            <ul className="space-y-2">
              {audit.feasibility_filter_audit.map((f, i) => (
                <li key={i} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm">
                  <span className="text-slate-600">{f.stage}</span>
                  <span className="flex items-center gap-2">
                    <Badge color="emerald">{f.passed_candidates} passed</Badge>
                    {f.rejections > 0 && <Badge color="red">{f.rejections} rejected</Badge>}
                  </span>
                </li>
              ))}
            </ul>
            {audit.knowledge_graph_chain_sources.length > 0 && (
              <div className="mt-4">
                <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-slate-500">Knowledge graph chain sources</div>
                <p className="text-xs text-slate-500">{JSON.stringify(audit.knowledge_graph_chain_sources).slice(0, 300)}</p>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </Card>
  );
}

function AuditRow({ k, v, mono }: { k: string; v: string; mono?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-slate-100 pb-1.5">
      <dt className="shrink-0 text-xs text-slate-500">{k}</dt>
      <dd className={cls("text-right text-[13px] font-medium text-slate-800", mono && "font-mono text-xs")}>{v}</dd>
    </div>
  );
}
