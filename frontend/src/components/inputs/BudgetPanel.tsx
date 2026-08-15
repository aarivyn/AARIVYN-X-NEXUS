"use client";

import { useEffect, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { inr } from "@/lib/format";
import { Alert, Badge, Button, Card, Field, KV, NumberInput, TextArea, TextInput } from "@/components/ui";

export function BudgetPanel() {
  const { token, budget, setBudget } = useApp();
  const [loading, setLoading] = useState(!budget);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    name: "",
    target_budget: "100000000",
    maximum_budget: "150000000",
    intensity: "7",
    details: "",
  });

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const b = await api.getBudget(token);
        if (ignore) return;
        setBudget(b);
        setForm({
          name: b.name ?? "",
          target_budget: String(Math.round(b.target_budget)),
          maximum_budget: String(Math.round(b.maximum_budget)),
          intensity: String(b.intensity),
          details: b.details ?? "",
        });
      } catch {
        /* 404 = not set yet — fine */
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [token, setBudget]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    try {
      const b = await api.putBudget(
        {
          name: form.name || undefined,
          target_budget: Number(form.target_budget),
          maximum_budget: Number(form.maximum_budget),
          intensity: Number(form.intensity),
          details: form.details || undefined,
        },
        token
      );
      setBudget(b);
      setSaved(true);
    } catch (e) {
      setError(errMsg(e));
    }
  }

  if (loading) return <div className="text-sm text-slate-400">Loading budget…</div>;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card
        title="Budget envelope"
        subtitle="Singleton — the latest save overrides budget_limit_inr in every pipeline request"
        icon={<span>💰</span>}
      >
        <form onSubmit={save} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Target budget (INR)" hint="Feasibility & optimization cap">
              <NumberInput
                value={form.target_budget}
                onChange={(e) => setForm((s) => ({ ...s, target_budget: e.target.value }))}
                min={1}
              />
            </Field>
            <Field label="Maximum budget (INR)" hint="Hard ceiling">
              <NumberInput
                value={form.maximum_budget}
                onChange={(e) => setForm((s) => ({ ...s, maximum_budget: e.target.value }))}
                min={1}
              />
            </Field>
            <Field label="Intensity (1–10)">
              <NumberInput
                value={form.intensity}
                onChange={(e) => setForm((s) => ({ ...s, intensity: e.target.value }))}
                min={1}
                max={10}
              />
            </Field>
            <Field label="Name">
              <TextInput value={form.name} onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))} placeholder="Q3 budget" />
            </Field>
          </div>
          <Field label="Details">
            <TextArea value={form.details} onChange={(e) => setForm((s) => ({ ...s, details: e.target.value }))} />
          </Field>
          {error && <Alert tone="error">{error}</Alert>}
          {saved && <Alert tone="success">Budget saved — downstream modules will use it as the cap.</Alert>}
          <Button type="submit">Save budget</Button>
        </form>
      </Card>

      <Card title="Current budget record" icon={<span>📋</span>}>
        {budget ? (
          <div>
            <div className="mb-3 flex items-center gap-2">
              <Badge color="teal">ingested</Badge>
              {budget.name && <Badge>{budget.name}</Badge>}
            </div>
            <KV k="Target budget" v={inr(budget.target_budget)} />
            <KV k="Maximum budget" v={inr(budget.maximum_budget)} />
            <KV k="Intensity" v={`${budget.intensity} / 10`} />
            <KV k="Details" v={budget.details ?? "—"} />
            <KV k="Updated" v={new Date(budget.updated_at).toLocaleString()} />
          </div>
        ) : (
          <p className="text-sm text-slate-400">No budget record yet — save one to the left.</p>
        )}
      </Card>
    </div>
  );
}
