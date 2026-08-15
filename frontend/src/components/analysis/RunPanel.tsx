"use client";

import { useEffect, useRef, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { cls } from "@/lib/format";
import { Alert, Badge, Button, Card, Field, NumberInput, Select, TextInput } from "@/components/ui";
import { PIPELINE_STAGES, type NexusJobStatus } from "@/lib/types";

/** Months between now and an ISO deadline, clamped to [3, 36]. Computed at
 *  submit time (event handlers may be impure; render must stay pure). */
function monthsUntil(deadlineIso: string | undefined): number | null {
  if (!deadlineIso) return null;
  const ms = new Date(deadlineIso).getTime() - Date.now();
  if (Number.isNaN(ms)) return null;
  return Math.max(3, Math.min(36, Math.round(ms / (1000 * 60 * 60 * 24 * 30))));
}

export function RunPanel({ onDone }: { onDone: (job: NexusJobStatus) => void }) {
  const { token, workspace, budget, timeline, job, setJob } = useApp();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const bbox = workspace?.bbox ?? [81.1, 24.4, 81.5, 24.8];
  const budgetCap = budget?.target_budget ?? 200000000;

  const [form, setForm] = useState({
    geography_id: "rewa",
    date_range_start: "2024-01-01",
    date_range_end: "2026-08-01",
    data_sources: "Sentinel-2, Sentinel-1, Landsat",
    budget_limit_inr: String(Math.round(budgetCap)),
    time_horizon_months: "36",
    max_risk_level: "HIGH",
  });

  // Poll the active job.
  const jobId = job?.job_id;
  const jobStatus = job?.status;
  useEffect(() => {
    if (!jobId || jobStatus !== "PROCESSING") return;
    pollRef.current = setInterval(async () => {
      try {
        const j = await api.nexusJob(jobId, token);
        setJob(j);
        if (j.status !== "PROCESSING") {
          if (pollRef.current) clearInterval(pollRef.current);
          if (j.status === "COMPLETED") onDone(j);
        }
      } catch {
        /* transient — keep polling */
      }
    }, 1500);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [jobId, jobStatus, token, setJob, onDone]);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      // Ingested site data takes precedence server-side; still, pass the
      // tighter deadline-derived horizon when an ingested timeline exists.
      const deadlineMonths = monthsUntil(timeline?.deadline);
      const j = await api.nexusAnalyze(
        {
          geography_id: form.geography_id,
          bbox: bbox as [number, number, number, number],
          date_range_start: form.date_range_start,
          date_range_end: form.date_range_end,
          data_sources: form.data_sources.split(",").map((s) => s.trim()).filter(Boolean),
          budget_limit_inr: Number(form.budget_limit_inr),
          time_horizon_months: deadlineMonths ?? Number(form.time_horizon_months),
          max_risk_level: form.max_risk_level,
        },
        token
      );
      setJob(j);
      setBusy(false);
    } catch (e) {
      setError(errMsg(e));
      setBusy(false);
    }
  }

  const running = job?.status === "PROCESSING";
  const done = job?.status === "COMPLETED";
  const failed = job?.status === "FAILED";

  return (
    <div className="space-y-6">
      <Card
        title="Pipeline configuration"
        subtitle="Modules 2→7 run end-to-end in a background job: EO → signals → graph → feasibility → NSGA-II → implementation plan"
        icon={<span>⚙️</span>}
      >
        <form onSubmit={run} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Geography ID">
            <TextInput value={form.geography_id} onChange={(e) => setForm((s) => ({ ...s, geography_id: e.target.value }))} />
          </Field>
          <Field label="Bounding box (from workspace)" hint={bbox.map((v) => v.toFixed(2)).join(", ")}>
            <TextInput value={`${bbox.map((v) => v.toFixed(2)).join(", ")}`} disabled className="opacity-60" />
          </Field>
          <Field label="Data sources (comma separated)">
            <TextInput value={form.data_sources} onChange={(e) => setForm((s) => ({ ...s, data_sources: e.target.value }))} />
          </Field>
          <Field label="Date range start">
            <TextInput type="date" value={form.date_range_start} onChange={(e) => setForm((s) => ({ ...s, date_range_start: e.target.value }))} />
          </Field>
          <Field label="Date range end">
            <TextInput type="date" value={form.date_range_end} onChange={(e) => setForm((s) => ({ ...s, date_range_end: e.target.value }))} />
          </Field>
          <Field label="Budget limit (INR)" hint={budget ? "from ingested budget" : "default"}>
            <NumberInput value={form.budget_limit_inr} onChange={(e) => setForm((s) => ({ ...s, budget_limit_inr: e.target.value }))} />
          </Field>
          <Field label="Time horizon (months)" hint={timeline ? "from ingested timeline" : "default"}>
            <NumberInput value={form.time_horizon_months} onChange={(e) => setForm((s) => ({ ...s, time_horizon_months: e.target.value }))} />
          </Field>
          <Field label="Max risk level">
            <Select value={form.max_risk_level} onChange={(e) => setForm((s) => ({ ...s, max_risk_level: e.target.value }))}>
              <option>HIGH</option>
              <option>MEDIUM</option>
              <option>LOW</option>
            </Select>
          </Field>
          <div className="flex items-end">
            <Button type="submit" size="lg" loading={busy} disabled={running} className="w-full">
              {running ? "Running…" : done ? "Re-run analysis" : "Run NEXUS analysis"}
            </Button>
          </div>
        </form>
        {error && <Alert tone="error" className="mt-4">{error}</Alert>}
      </Card>

      {job && (
        <Card
          title={`Job ${job.job_id}`}
          subtitle={`${job.status} · updated ${new Date(job.updated_at).toLocaleTimeString()}`}
          icon={<span>{running ? "🔄" : done ? "✅" : failed ? "❌" : "📦"}</span>}
          actions={
            done ? <Badge color="emerald">COMPLETED</Badge> : failed ? <Badge color="red">FAILED</Badge> : <Badge color="blue">PROCESSING</Badge>
          }
        >
          <StageProgress job={job} />
          {failed && job.error_message && <Alert tone="error" className="mt-4">Job failed: {job.error_message}</Alert>}
          {done && job.result && (
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge color="teal">orchestration {job.result.orchestration_id}</Badge>
              <Badge color="teal">{job.result.geography_id}</Badge>
              <Badge>{job.result.optimization.pareto_solutions_count} Pareto plans</Badge>
              <Badge>{job.result.implementation_plan.total_duration_months} mo plan</Badge>
            </div>
          )}
        </Card>
      )}

      {running && (
        <Alert tone="info" title="Pipeline running in the background">
          You can leave this page — the job keeps executing server-side. Return to this step or jump to
          “Feasibility & Optimize” once it completes.
        </Alert>
      )}
    </div>
  );
}

function StageProgress({ job }: { job: NexusJobStatus }) {
  const stageIdx = Math.min(
    PIPELINE_STAGES.length - 1,
    Math.floor((job.progress_percent / 100) * PIPELINE_STAGES.length)
  );
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-xs">
        <span className="font-medium text-slate-700">{job.stage ?? "Queued"}</span>
        <span className="font-mono text-slate-500">{job.progress_percent}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-500 transition-all duration-500"
          style={{ width: `${job.progress_percent}%` }}
        />
      </div>
      <div className="mt-4 grid gap-1.5 sm:grid-cols-2 lg:grid-cols-4">
        {PIPELINE_STAGES.map((s, i) => {
          const state = job.status === "COMPLETED" || (job.status === "PROCESSING" && i < stageIdx)
            ? "done"
            : job.status === "PROCESSING" && i === stageIdx
              ? "active"
              : "pending";
          return (
            <div
              key={s}
              className={cls(
                "flex items-center gap-2 rounded-lg border px-2.5 py-2 text-[11px]",
                state === "done" && "border-emerald-200 bg-emerald-50 text-emerald-700",
                state === "active" && "border-teal-300 bg-teal-50 text-teal-800",
                state === "pending" && "border-slate-200 bg-white text-slate-400"
              )}
            >
              <span className={cls("flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[9px] font-bold", state === "done" && "bg-emerald-500 text-white", state === "active" && "bg-teal-500 text-white", state === "pending" && "bg-slate-200 text-slate-500")}>
                {state === "done" ? "✓" : state === "active" ? "…" : i + 1}
              </span>
              <span className="truncate">{s.replace("Stage ", "")}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
