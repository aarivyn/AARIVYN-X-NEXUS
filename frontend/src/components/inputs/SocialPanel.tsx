"use client";

import { useCallback, useEffect, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { Alert, Badge, Button, Card, Field, NumberInput, Select, TextArea, TextInput } from "@/components/ui";
import type { SocialGroup, SocialTaxonomy, TaxonomyEntry } from "@/lib/types";

/** Taxonomy entries arrive from the backend as {key, label} objects. Normalize
 *  plain-string fallbacks into the same shape so rendering is uniform. */
function taxonomyOptions(
  entries: TaxonomyEntry[] | undefined,
  fallback: string[]
): TaxonomyEntry[] {
  const src = entries && entries.length > 0 ? entries : fallback.map((f) => ({ key: f, label: f }));
  return src.map((e) => ({ key: e.key, label: e.label ?? e.key }));
}

const FALLBACKS = {
  genders: ["male", "female", "other"],
  income_groups: ["BPL", "LIG", "MIG", "HIG"],
  // Must match the backend EmploymentStatus enum exactly — these are the keys
  // served by /api/v1/social/taxonomy (labels shown in the UI).
  employment_statuses: [
    "salaried_government",
    "salaried_private",
    "self_employed",
    "daily_wage",
    "unemployed",
    "student",
    "homemaker",
    "retired",
    "agricultural",
  ],
};

export function SocialPanel() {
  const { token } = useApp();
  const [groups, setGroups] = useState<SocialGroup[]>([]);
  const [taxonomy, setTaxonomy] = useState<SocialTaxonomy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    intensity: "4",
    details: "",
    gender: "male",
    income_group: "BPL",
    employment_status: "salaried_private",
    caste: "",
    area_type: "",
    religion: "",
  });

  const refresh = useCallback(async () => {
    try {
      const [g, t] = await Promise.all([api.listSocialGroups(token), api.socialTaxonomy(token)]);
      setGroups(g.items);
      setTaxonomy(t);
    } catch (e) {
      setError(errMsg(e));
    }
  }, [token]);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [g, t] = await Promise.all([api.listSocialGroups(token), api.socialTaxonomy(token)]);
        if (ignore) return;
        setGroups(g.items);
        setTaxonomy(t);
      } catch (e) {
        if (!ignore) setError(errMsg(e));
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [token]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const profile: Record<string, string> = {};
    for (const k of ["gender", "income_group", "employment_status", "caste", "area_type", "religion"] as const) {
      if (form[k]) profile[k] = form[k];
    }
    try {
      await api.createSocialGroup(
        { name: form.name, intensity: Number(form.intensity), details: form.details || undefined, profiles: [profile] },
        token
      );
      setForm((s) => ({ ...s, name: "", details: "" }));
      refresh();
    } catch (e) {
      setError(errMsg(e));
    }
  }

  async function remove(id: string) {
    await api.deleteSocialGroup(id, token);
    refresh();
  }

  const genderOpts = taxonomyOptions(taxonomy?.genders, FALLBACKS.genders);
  const incomeOpts = taxonomyOptions(taxonomy?.income_groups, FALLBACKS.income_groups);
  const employmentOpts = taxonomyOptions(taxonomy?.employment_statuses, FALLBACKS.employment_statuses);
  const casteOpts = taxonomyOptions(taxonomy?.caste_categories, []);
  const areaOpts = taxonomyOptions(taxonomy?.area_types, []);
  const religionOpts = taxonomyOptions(taxonomy?.religions, []);

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card
        title="Add a social group"
        subtitle="Demographic profiles inform affected-village estimates, applicability and monitoring"
        icon={<span>👥</span>}
      >
        <form onSubmit={create} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Group name">
              <TextInput value={form.name} onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))} placeholder="Village A" />
            </Field>
            <Field label="Intensity (1–10)">
              <NumberInput min={1} max={10} value={form.intensity} onChange={(e) => setForm((s) => ({ ...s, intensity: e.target.value }))} />
            </Field>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Gender">
              <Select value={form.gender} onChange={(e) => setForm((s) => ({ ...s, gender: e.target.value }))}>
                {genderOpts.map((g) => <option key={g.key} value={g.key}>{g.label}</option>)}
              </Select>
            </Field>
            <Field label="Income group">
              <Select value={form.income_group} onChange={(e) => setForm((s) => ({ ...s, income_group: e.target.value }))}>
                {incomeOpts.map((g) => <option key={g.key} value={g.key}>{g.label}</option>)}
              </Select>
            </Field>
            <Field label="Employment status">
              <Select value={form.employment_status} onChange={(e) => setForm((s) => ({ ...s, employment_status: e.target.value }))}>
                {employmentOpts.map((g) => <option key={g.key} value={g.key}>{g.label}</option>)}
              </Select>
            </Field>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Caste category (optional)">
              <Select value={form.caste} onChange={(e) => setForm((s) => ({ ...s, caste: e.target.value }))}>
                <option value="">—</option>
                {casteOpts.map((g) => <option key={g.key} value={g.key}>{g.label}</option>)}
              </Select>
            </Field>
            <Field label="Area type (optional)">
              <Select value={form.area_type} onChange={(e) => setForm((s) => ({ ...s, area_type: e.target.value }))}>
                <option value="">—</option>
                {areaOpts.map((g) => <option key={g.key} value={g.key}>{g.label}</option>)}
              </Select>
            </Field>
            <Field label="Religion (optional)">
              <Select value={form.religion} onChange={(e) => setForm((s) => ({ ...s, religion: e.target.value }))}>
                <option value="">—</option>
                {religionOpts.map((g) => <option key={g.key} value={g.key}>{g.label}</option>)}
              </Select>
            </Field>
          </div>
          <Field label="Details">
            <TextArea value={form.details} onChange={(e) => setForm((s) => ({ ...s, details: e.target.value }))} />
          </Field>
          {error && <Alert tone="error">{error}</Alert>}
          <Button type="submit">Add group</Button>
        </form>
      </Card>

      <Card title={`Social groups (${groups.length})`} icon={<span>🧑‍🤝‍🧑</span>}>
        {loading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : groups.length === 0 ? (
          <p className="text-sm text-slate-400">No groups yet.</p>
        ) : (
          <ul className="space-y-2">
            {groups.map((g) => (
              <li key={g.id} className="rounded-lg border border-slate-200 px-3 py-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-800">{g.name}</span>
                  <div className="flex items-center gap-2">
                    <Badge color="teal">intensity {g.intensity}/10</Badge>
                    <button onClick={() => remove(g.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                  </div>
                </div>
                {g.profiles.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {Object.entries(g.profiles[0])
                      .filter(([, v]) => v !== null && v !== undefined && v !== "")
                      .map(([k, v]) => (
                        <Badge key={k}>{k.replace(/_/g, " ")}: {String(v)}</Badge>
                      ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
