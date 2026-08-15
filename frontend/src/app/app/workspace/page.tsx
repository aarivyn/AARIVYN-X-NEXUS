"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { Alert, Badge, Button, Card, Field, Select, TextInput } from "@/components/ui";
import { PERSONAS, type Persona, type WorkspaceContext } from "@/lib/types";
import { cls } from "@/lib/format";

const PERSONA_HELP: Record<Persona, string> = {
  GOVERNMENT: "District / state water department planning an intervention.",
  CSR_FUNDER: "Corporate funder allocating CSR budget to water programs.",
  NGO: "Non-profit planning implementation in operating regions.",
  STUDENT: "Academic coursework on a region of interest.",
  RESEARCHER: "Academic research on a region of interest.",
  COMMUNITY: "Community reporting a local water problem.",
};

export default function WorkspacePage() {
  const router = useRouter();
  const { token, persona, setPersona, workspace, setWorkspace } = useApp();

  const [p, setP] = useState<Persona>(persona ?? "GOVERNMENT");
  const [form, setForm] = useState<Record<string, string>>({
    organization: "MPWRD",
    department_agency: "Water Resources",
    admin_level: "District",
    role: "District Officer",
    target_district: "Rewa",
    target_geography: "Rewa District",
    operating_regions: "Rewa, Satna",
    implementation_capacity: "High",
    institution: "IIT Delhi",
    region_of_interest: "Rewa",
    problem_category: "water_stress",
  });
  const [focusAreas, setFocusAreas] = useState("water, sanitation");
  const [budget, setBudget] = useState("100000000");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set(f: string, v: string) {
    setForm((s) => ({ ...s, [f]: v }));
  }

  async function onboard(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { persona: p };
      switch (p) {
        case "GOVERNMENT":
          body.government = {
            organization: form.organization,
            department_agency: form.department_agency,
            admin_level: form.admin_level,
            role: form.role,
            target_district: form.target_district,
          };
          break;
        case "CSR_FUNDER":
          body.csr_funder = {
            organization: form.organization,
            focus_areas: focusAreas.split(",").map((s) => s.trim()).filter(Boolean),
            target_geography: form.target_geography,
            budget: budget ? Number(budget) : undefined,
          };
          break;
        case "NGO":
          body.ngo = {
            organization: form.organization,
            operating_regions: form.operating_regions.split(",").map((s) => s.trim()).filter(Boolean),
            focus_areas: focusAreas.split(",").map((s) => s.trim()).filter(Boolean),
            implementation_capacity: form.implementation_capacity,
          };
          break;
        case "STUDENT":
        case "RESEARCHER":
          body[p === "STUDENT" ? "student" : "researcher"] = {
            name: form.organization || "Student",
            institution: form.institution,
            region_of_interest: form.region_of_interest,
          };
          break;
        case "COMMUNITY":
          body.community = { problem_category: form.problem_category, location: form.target_geography };
          break;
      }
      await api.onboarding(body as never, token);
      setPersona(p);
      const ws = await api.workspaceCurrent(p, token);
      setWorkspace(ws);
      router.push("/app/inputs");
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Workspace & region context</h2>
        <p className="mt-1 max-w-2xl text-sm text-slate-500">
          Choose the persona that matches your role. NEXUS resolves the workspace —
          geography, bounding box and permission scope — that drives every downstream module.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card title="Persona" subtitle="Select the role you act as" className="lg:col-span-2" padded={false}>
          <div className="space-y-1 p-3">
            {PERSONAS.map((item) => (
              <button
                key={item.value}
                onClick={() => setP(item.value)}
                className={cls(
                  "w-full rounded-lg border px-4 py-3 text-left transition-colors",
                  p === item.value
                    ? "border-teal-500 bg-teal-50/70"
                    : "border-slate-200 bg-white hover:border-slate-300"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-800">{item.label}</span>
                  {p === item.value && <Badge color="teal">selected</Badge>}
                </div>
                <div className="mt-0.5 text-xs text-slate-500">{item.blurb}</div>
              </button>
            ))}
          </div>
          <div className="border-t border-slate-100 px-4 py-3 text-[11px] text-slate-400">
            {PERSONA_HELP[p]}
          </div>
        </Card>

        <div className="space-y-6 lg:col-span-3">
          <form onSubmit={onboard} className="space-y-6">
            <Card title={`${p} onboarding`} subtitle="These details define the workspace context">
              <div className="grid gap-4 sm:grid-cols-2">
                {(p === "GOVERNMENT" || p === "CSR_FUNDER" || p === "NGO") && (
                  <Field label="Organization" className="sm:col-span-2">
                    <TextInput value={form.organization} onChange={(e) => set("organization", e.target.value)} />
                  </Field>
                )}
                {p === "GOVERNMENT" && (
                  <>
                    <Field label="Department / agency">
                      <TextInput value={form.department_agency} onChange={(e) => set("department_agency", e.target.value)} />
                    </Field>
                    <Field label="Admin level">
                      <Select value={form.admin_level} onChange={(e) => set("admin_level", e.target.value)}>
                        <option>State</option>
                        <option>District</option>
                        <option>Block</option>
                        <option>Village</option>
                      </Select>
                    </Field>
                    <Field label="Role">
                      <TextInput value={form.role} onChange={(e) => set("role", e.target.value)} />
                    </Field>
                    <Field label="Target district">
                      <TextInput value={form.target_district} onChange={(e) => set("target_district", e.target.value)} />
                    </Field>
                  </>
                )}
                {p === "CSR_FUNDER" && (
                  <>
                    <Field label="Target geography">
                      <TextInput value={form.target_geography} onChange={(e) => set("target_geography", e.target.value)} />
                    </Field>
                    <Field label="Budget (INR)">
                      <TextInput type="number" value={budget} onChange={(e) => setBudget(e.target.value)} />
                    </Field>
                    <Field label="Focus areas (comma separated)" className="sm:col-span-2">
                      <TextInput value={focusAreas} onChange={(e) => setFocusAreas(e.target.value)} />
                    </Field>
                  </>
                )}
                {p === "NGO" && (
                  <>
                    <Field label="Operating regions (comma separated)" className="sm:col-span-2">
                      <TextInput value={form.operating_regions} onChange={(e) => set("operating_regions", e.target.value)} />
                    </Field>
                    <Field label="Implementation capacity">
                      <Select value={form.implementation_capacity} onChange={(e) => set("implementation_capacity", e.target.value)}>
                        <option>High</option>
                        <option>Medium</option>
                        <option>Low</option>
                      </Select>
                    </Field>
                    <Field label="Focus areas (comma separated)">
                      <TextInput value={focusAreas} onChange={(e) => setFocusAreas(e.target.value)} />
                    </Field>
                  </>
                )}
                {(p === "STUDENT" || p === "RESEARCHER") && (
                  <>
                    <Field label="Institution">
                      <TextInput value={form.institution} onChange={(e) => set("institution", e.target.value)} />
                    </Field>
                    <Field label="Region of interest">
                      <TextInput value={form.region_of_interest} onChange={(e) => set("region_of_interest", e.target.value)} />
                    </Field>
                  </>
                )}
                {p === "COMMUNITY" && (
                  <>
                    <Field label="Problem category">
                      <TextInput value={form.problem_category} onChange={(e) => set("problem_category", e.target.value)} />
                    </Field>
                    <Field label="Location (optional)">
                      <TextInput value={form.target_geography} onChange={(e) => set("target_geography", e.target.value)} />
                    </Field>
                  </>
                )}
              </div>
              {error && <Alert tone="error" className="mt-4">{error}</Alert>}
              <div className="mt-5 flex justify-end">
                <Button type="submit" loading={busy}>
                  Resolve workspace →
                </Button>
              </div>
            </Card>
          </form>

          {workspace && <WorkspaceSummary ws={workspace} />}
        </div>
      </div>
    </div>
  );
}

function WorkspaceSummary({ ws }: { ws: WorkspaceContext }) {
  const ps = ws.permission_scope;
  return (
    <Card
      title="Resolved workspace"
      subtitle={ws.geography_name}
      icon={<span className="text-lg">🗺️</span>}
    >
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MiniStat label="Persona" value={ws.persona} />
        <MiniStat label="Bounding box" value={ws.bbox.map((v) => v.toFixed(2)).join(" · ")} mono />
        <MiniStat label="Center" value={`${ws.center[0].toFixed(2)}, ${ws.center[1].toFixed(2)}`} mono />
        <MiniStat label="Zoom" value={String(ws.zoom)} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {ps.read_map && <Badge color="teal">read_map</Badge>}
        {ps.run_optimization && <Badge color="emerald">run_optimization</Badge>}
        {ps.view_provenance && <Badge color="blue">view_provenance</Badge>}
        {ps.admin_level && <Badge>{ps.admin_level}</Badge>}
        {ps.role && <Badge>{ps.role}</Badge>}
      </div>
    </Card>
  );
}

function MiniStat({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2">
      <div className="text-[10px] font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-0.5 truncate text-[13px] font-semibold text-slate-800 ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}
