"use client";

import { useEffect, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { Alert, Badge, Button, Card, Field, KV, NumberInput, TextArea, TextInput } from "@/components/ui";

export function TimelinePanel() {
  const { token, timeline, setTimeline } = useApp();
  const [loading, setLoading] = useState(!timeline);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState({
    name: "",
    urgency: "9",
    expected_duration: "6 months",
    deadline: "2027-06-30",
    details: "",
  });

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const t = await api.getTimeline(token);
        if (ignore) return;
        setTimeline(t);
        setForm({
          name: t.name ?? "",
          urgency: String(t.urgency),
          expected_duration: t.expected_duration,
          deadline: t.deadline,
          details: t.details ?? "",
        });
      } catch {
        /* 404 = not set — fine */
      } finally {
        if (!ignore) setLoading(false);
      }
    })();
    return () => {
      ignore = true;
    };
  }, [token, setTimeline]);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaved(false);
    try {
      const t = await api.putTimeline(
        {
          name: form.name || undefined,
          urgency: Number(form.urgency),
          expected_duration: form.expected_duration,
          deadline: form.deadline,
          details: form.details || undefined,
        },
        token
      );
      setTimeline(t);
      setSaved(true);
    } catch (e) {
      setError(errMsg(e));
    }
  }

  if (loading) return <div className="text-sm text-slate-400">Loading timeline…</div>;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card
        title="Timeline"
        subtitle="Expected duration & deadline derive the effective time horizon (tighter of the two wins)"
        icon={<span>⏱️</span>}
      >
        <form onSubmit={save} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Urgency (1–10)" hint="Surfaced in provenance; does not stretch the horizon">
              <NumberInput min={1} max={10} value={form.urgency} onChange={(e) => setForm((s) => ({ ...s, urgency: e.target.value }))} />
            </Field>
            <Field label="Expected duration">
              <TextInput value={form.expected_duration} onChange={(e) => setForm((s) => ({ ...s, expected_duration: e.target.value }))} placeholder="6 months" />
            </Field>
            <Field label="Deadline (YYYY-MM-DD)">
              <TextInput type="date" value={form.deadline} onChange={(e) => setForm((s) => ({ ...s, deadline: e.target.value }))} />
            </Field>
            <Field label="Name">
              <TextInput value={form.name} onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))} placeholder="Monsoon timeline" />
            </Field>
          </div>
          <Field label="Details">
            <TextArea value={form.details} onChange={(e) => setForm((s) => ({ ...s, details: e.target.value }))} />
          </Field>
          {error && <Alert tone="error">{error}</Alert>}
          {saved && <Alert tone="success">Timeline saved — effective horizon recalculated downstream.</Alert>}
          <Button type="submit">Save timeline</Button>
        </form>
      </Card>

      <Card title="Current timeline record" icon={<span>📋</span>}>
        {timeline ? (
          <div>
            <div className="mb-3 flex gap-2">
              <Badge color="amber">urgency {timeline.urgency}/10</Badge>
              {timeline.name && <Badge>{timeline.name}</Badge>}
            </div>
            <KV k="Expected duration" v={timeline.expected_duration} />
            <KV k="Deadline" v={timeline.deadline} />
            <KV k="Details" v={timeline.details ?? "—"} />
            <KV k="Updated" v={new Date(timeline.updated_at).toLocaleString()} />
          </div>
        ) : (
          <p className="text-sm text-slate-400">No timeline yet — save one to the left.</p>
        )}
      </Card>
    </div>
  );
}
