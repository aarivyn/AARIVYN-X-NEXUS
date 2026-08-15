"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { cls, pct, riskColor, severityColor } from "@/lib/format";
import { Alert, Badge, Card, EmptyState, Spinner, Tabs } from "@/components/ui";
import type { NexusResult } from "@/lib/types";

export function ResultTabs({ result }: { result: NexusResult }) {
  const [tab, setTab] = useState("overview");
  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "eo", label: "Earth Observation" },
    { id: "water", label: "Water Intelligence" },
    { id: "context", label: "Problems & Context" },
    { id: "graph", label: "Knowledge Graph" },
    { id: "layers", label: "EO Layers" },
  ];

  return (
    <div className="space-y-4">
      <Tabs tabs={tabs} active={tab} onChange={setTab} />
      {tab === "overview" && <OverviewTab result={result} />}
      {tab === "eo" && <EOTab result={result} />}
      {tab === "water" && <WaterTab result={result} />}
      {tab === "context" && <ContextTab result={result} />}
      {tab === "graph" && <GraphTab result={result} />}
      {tab === "layers" && <LayersTab />}
    </div>
  );
}

// ---------- Overview ----------

function OverviewTab({ result }: { result: NexusResult }) {
  const sd = result.site_data as Record<string, unknown>;
  const budget = sd.budget as { name?: string; target_budget: number; maximum_budget: number } | undefined;
  const timeline = sd.timeline as { urgency: number; expected_duration: string; deadline: string } | undefined;
  const social = sd.social_groups as { group_count: number; profile_count: number; names: string[] } | undefined;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title="Pipeline summary" icon={<span>🧭</span>}>
        <dl className="space-y-2 text-sm">
          <Row k="Orchestration ID" v={<span className="font-mono">{result.orchestration_id}</span>} />
          <Row k="Geography" v={result.geography_id} />
          <Row k="EO observations" v={result.earth_observation.observations_count} />
          <Row k="Problem categories" v={result.water_intelligence.problem_categories.join(", ")} />
          <Row k="Knowledge graph" v={`${result.intervention_graph.discovered_nodes_count} nodes · ${result.intervention_graph.discovered_edges_count} edges`} />
          <Row k="Feasibility" v={`${result.feasibility.viable_candidates_count} / ${result.feasibility.total_candidates} viable`} />
          <Row k="Pareto portfolios" v={result.optimization.pareto_solutions_count} />
          <Row k="Implementation duration" v={`${result.implementation_plan.total_duration_months} months`} />
          <Row k="Orchestration engine" v={String(result.provenance.orchestration_engine ?? "—")} />
        </dl>
      </Card>

      <div className="space-y-6">
        <Card title="Site data applied (precedence)" icon={<span>📋</span>}>
          {budget ? (
            <p className="text-sm">
              Budget cap <Badge color="teal">₹{(budget.target_budget / 1e7).toFixed(1)} Cr</Badge>
              {budget.name && <span className="ml-1 text-slate-400">({budget.name})</span>} · hard ceiling ₹
              {(budget.maximum_budget / 1e7).toFixed(1)} Cr
            </p>
          ) : (
            <p className="text-sm text-slate-400">No ingested budget — request value used.</p>
          )}
          {timeline && (
            <p className="mt-2 text-sm">
              Timeline urgency <Badge color="amber">{timeline.urgency}/10</Badge> · {timeline.expected_duration} · deadline{" "}
              {timeline.deadline}
            </p>
          )}
          {social && (
            <p className="mt-2 text-sm">
              Social context: {social.group_count} group(s), {social.profile_count} profile(s)
              {social.names?.length ? ` · ${social.names.join(", ")}` : ""}
            </p>
          )}
        </Card>

        <Card title="Confidence & honesty notes" icon={<span>🎯</span>}>
          <ul className="space-y-2 text-xs text-slate-600">
            {Object.entries(result.earth_observation.confidence ?? {}).map(([k, v]) => {
              if (typeof v === "object" || v === null || v === undefined) return null;
              return (
                <li key={k} className="flex justify-between gap-4 border-b border-slate-100 pb-1.5 last:border-0">
                  <span className="text-slate-500">{k.replace(/_/g, " ")}</span>
                  <span className="text-right font-medium text-slate-700">{String(v)}</span>
                </li>
              );
            })}
          </ul>
          <p className="mt-3 text-[11px] text-slate-400">
            All signals are spectral proxies (direct_measurement: false). Groundwater depth and chemical contamination are not
            directly measured.
          </p>
        </Card>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-slate-100 pb-1.5 last:border-0">
      <dt className="text-xs text-slate-500">{k}</dt>
      <dd className="text-right text-[13px] font-medium text-slate-800">{v}</dd>
    </div>
  );
}

// ---------- Earth Observation ----------

function EOTab({ result }: { result: NexusResult }) {
  const indicators = result.earth_observation.indicators ?? [];
  return (
    <Card title={`Indicators (${indicators.length})`} subtitle="Spectral proxies from satellite sources" icon={<span>🛰️</span>} padded={false}>
      {indicators.length === 0 ? (
        <div className="p-5"><EmptyState title="No indicators returned" /></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2.5 font-semibold">Indicator</th>
                <th className="px-3 py-2.5 font-semibold">Value</th>
                <th className="px-3 py-2.5 font-semibold">Source</th>
                <th className="px-3 py-2.5 font-semibold">Confidence</th>
                <th className="px-3 py-2.5 font-semibold">Pedigree</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {indicators.map((ind, i) => (
                <tr key={i}>
                  <td className="px-3 py-2.5 font-medium text-slate-800">{String(ind.indicator_name)}</td>
                  <td className="px-3 py-2.5 font-mono text-slate-700">{String(ind.value)}{ind.unit ? ` ${ind.unit}` : ""}</td>
                  <td className="max-w-[260px] truncate px-3 py-2.5 text-slate-500" title={String(ind.source)}>{String(ind.source)}</td>
                  <td className="px-3 py-2.5">{ind.confidence !== undefined && <Badge color={Number(ind.confidence) > 0.9 ? "emerald" : "amber"}>{pct(Number(ind.confidence))}</Badge>}</td>
                  <td className="px-3 py-2.5 text-xs text-slate-500">{String(ind.pedigree)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

// ---------- Water Intelligence ----------

function WaterTab({ result }: { result: NexusResult }) {
  const wi = result.water_intelligence;
  return (
    <div className="space-y-6">
      <Card title={`Detected signals (${wi.detected_signals.length})`} icon={<span>📡</span>}>
        {wi.detected_signals.length === 0 ? (
          <EmptyState title="No signals detected" />
        ) : (
          <ul className="space-y-3">
            {wi.detected_signals.map((s, i) => (
              <li key={i} className="rounded-lg border border-slate-200 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11px] text-slate-400">{String(s.id)}</span>
                  <Badge className={severityColor(String(s.severity))}>{String(s.severity)}</Badge>
                  <Badge color="blue">{String(s.domain)}</Badge>
                  {s.affected_villages_count !== undefined && <Badge color="violet">{String(s.affected_villages_count)} villages</Badge>}
                  <Badge>{String(s.provenance_tag)}</Badge>
                </div>
                {Boolean(s.title || s.description) && (
                  <p className="mt-2 text-[13px] text-slate-600">
                    {String(s.title ?? "")}{Boolean(s.title && s.description) ? " — " : ""}{String(s.description ?? "")}
                  </p>
                )}
                {Boolean(s.source) && <p className="mt-1 text-[11px] text-slate-400">source: {String(s.source)}</p>}
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Problem categories" icon={<span>⚠️</span>}>
          <div className="flex flex-wrap gap-2">
            {wi.problem_categories.map((c) => <Badge key={c} color="red">{c}</Badge>)}
          </div>
        </Card>
        <Card title={`Evidence used (${wi.evidence.length})`} icon={<span>🔎</span>}>
          <ul className="space-y-2 text-xs text-slate-600">
            {wi.evidence.map((ev, i) => (
              <li key={i} className="flex items-start justify-between gap-3 border-b border-slate-100 pb-2 last:border-0">
                <span className="max-w-[70%] truncate" title={ev.citation}>{ev.citation}</span>
                <span className="shrink-0"><Badge color="blue">{ev.type}</Badge></span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}

// ---------- Problems & Context ----------

function ContextTab({ result }: { result: NexusResult }) {
  const { token } = useApp();
  const [ctx, setCtx] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.contextSignals(result.geography_id, token)
      .then((d) => setCtx(d as unknown as Record<string, unknown>))
      .catch((e) => setErr(errMsg(e)))
      .finally(() => setLoading(false));
  }, [result.geography_id, token]);

  const signals = Array.isArray(ctx?.signals) ? (ctx.signals as Array<Record<string, unknown>>) : [];

  return (
    <div className="space-y-6">
      <Card title="Problem detection & context" subtitle={`Signals for ${result.geography_id} (GET /context/{id}/signals)`} icon={<span>🧠</span>}>
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-400"><Spinner /> Loading context…</div>
        ) : err ? (
          <Alert tone="error">{err}</Alert>
        ) : (
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Metric label="Water stress index" value={ctx?.water_stress_index} />
            <Metric label="Vegetation condition" value={ctx?.vegetation_condition_index} />
            <Metric label="Flood risk score" value={ctx?.flood_risk_score} />
            <Metric label="GW drawdown" value={ctx?.groundwater_drawdown_rate_m_yr} unit="m/yr" />
          </div>
        )}
      </Card>

      <Card title={`Context signals (${signals.length})`} icon={<span>📡</span>}>
        {signals.length === 0 ? (
          <EmptyState title="No context signals" />
        ) : (
          <ul className="space-y-2">
            {signals.map((s, i) => (
              <li key={i} className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <span className="font-mono text-[11px] text-slate-400">{String(s.id)}</span>
                <span className="font-medium text-slate-800">{String(s.title ?? s.domain ?? "")}</span>
                <Badge className={severityColor(String(s.severity))}>{String(s.severity)}</Badge>
                <span className="text-xs text-slate-500">{String(s.description ?? "")}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function Metric({ label, value, unit }: { label: string; value: unknown; unit?: string }) {
  const v = typeof value === "number" ? value : null;
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/60 px-4 py-3">
      <div className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={cls("mt-1 text-xl font-semibold text-slate-800", v === null && "text-slate-300")}>
        {v !== null ? v.toFixed(2) : "—"}
        {v !== null && unit && <span className="ml-1 text-xs font-normal text-slate-400">{unit}</span>}
      </div>
      {v !== null && (
        <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
          <div className={cls("h-full rounded-full", v > 0.7 ? "bg-red-400" : v > 0.4 ? "bg-amber-400" : "bg-emerald-400")} style={{ width: `${Math.min(100, v * 100)}%` }} />
        </div>
      )}
    </div>
  );
}

// ---------- Knowledge Graph ----------

function GraphTab({ result }: { result: NexusResult }) {
  const { token } = useApp();
  const [cards, setCards] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.interventions("Water", token)
      .then((d) => setCards(d as unknown as Array<Record<string, unknown>>))
      .catch((e) => setErr(errMsg(e)))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="space-y-6">
      <Card
        title="Discovery result"
        subtitle={`POST /graph/discover for ${result.geography_id} — reachable interventions from detected problems`}
        icon={<span>🕸️</span>}
      >
        <div className="flex flex-wrap gap-2">
          <Badge color="teal">{result.intervention_graph.discovered_nodes_count} discovered nodes</Badge>
          <Badge color="blue">{result.intervention_graph.discovered_edges_count} edges</Badge>
        </div>
      </Card>

      <Card title={`Intervention cards — domain Water (${cards.length})`} subtitle="Feasibility & optimizer operate over these" icon={<span>🧩</span>}>
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-slate-400"><Spinner /> Loading…</div>
        ) : err ? (
          <Alert tone="error">{err}</Alert>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {cards.map((c) => (
              <div key={String(c.id)} className="rounded-lg border border-slate-200 p-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="font-mono text-[10px] text-slate-400">{String(c.id)}</span>
                    <div className="text-sm font-medium text-slate-800">{String(c.name)}</div>
                  </div>
                  <Badge className={riskColor(String(c.risk_level))}>{String(c.risk_level)} risk</Badge>
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                  <Badge color="slate">{String(c.category)}</Badge>
                  <Badge color="teal">₹{Number(c.cost_inr).toLocaleString("en-IN")}</Badge>
                  <Badge color="blue">{String(c.water_security_score)} score</Badge>
                  <Badge color="violet">{String(c.jobs_created)} jobs</Badge>
                  <Badge>{String(c.implementation_time_months)} mo</Badge>
                </div>
                {Array.isArray(c.sdg_alignments) && (c.sdg_alignments as string[]).length > 0 && (
                  <div className="mt-2 text-[11px] text-slate-500">SDG {(c.sdg_alignments as string[]).join(" · ")}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

// ---------- EO Layers ----------

function LayersTab() {
  const { token } = useApp();
  const [layers, setLayers] = useState<Record<string, { layer: Record<string, unknown>; url: string }>>({});
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all(
      (["ndvi", "ndwi", "groundwater"] as const).map(async (t) => {
        const layer = await api.eoLayer(t, undefined, token);
        return [t, { layer: layer as unknown as Record<string, unknown>, url: api.overlayUrl(t) }];
      })
    )
      .then((entries) => setLayers(Object.fromEntries(entries)))
      .catch((e) => setErr(errMsg(e)))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <div className="flex items-center gap-2 text-sm text-slate-400"><Spinner /> Fetching EO layers…</div>;
  if (err) return <Alert tone="error">{err}</Alert>;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {Object.entries(layers).map(([t, { layer, url }]) => {
        const meta = (layer.stac_metadata ?? {}) as Record<string, unknown>;
        return (
          <Card key={t} title={String(layer.layer_type).toUpperCase()} subtitle="PNG overlay for the workspace bbox" icon={<span>🛰️</span>}>
            <Image
              src={url}
              alt={`${String(layer.layer_type)} overlay`}
              width={900}
              height={900}
              unoptimized
              className="w-full rounded-lg border border-slate-200"
              onError={() => undefined}
            />
            <div className="mt-3 space-y-1 text-[11px] text-slate-500">
              <div>scene: <span className="font-mono">{String(meta.scene_id ?? "—")}</span></div>
              <div>acquired: {String(meta.acquisition_date ?? "—")}</div>
              <div>cloud cover: {meta.cloud_cover_percent !== undefined ? `${Number(meta.cloud_cover_percent) * 100}%` : "—"}</div>
              <div>source: {String(meta.source_api ?? "—")}</div>
              <div>provenance: <Badge>{String(layer.provenance_tag ?? meta.provenance_tag ?? "—")}</Badge></div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
