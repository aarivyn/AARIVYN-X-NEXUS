"use client";

import { useCallback, useEffect, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { Alert, Badge, Button, Card, Field, NumberInput, TextArea, TextInput } from "@/components/ui";
import type { LocationRecord } from "@/lib/types";

export function LocationsPanel() {
  const { token } = useApp();
  const [items, setItems] = useState<LocationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", state: "Madhya Pradesh", district: "Rewa", city: "Rewa", intensity: "5", details: "" });

  const refresh = useCallback(async () => {
    try {
      const r = await api.listLocations(token);
      setItems(r.items);
    } catch (e) {
      setError(errMsg(e));
    }
  }, [token]);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const r = await api.listLocations(token);
        if (!ignore) setItems(r.items);
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
    try {
      await api.createLocation(
        {
          name: form.name || undefined,
          state: form.state,
          district: form.district,
          city: form.city,
          intensity: Number(form.intensity),
          details: form.details || undefined,
        },
        token
      );
      setForm({ ...form, name: "", details: "" });
      refresh();
    } catch (e) {
      setError(errMsg(e));
    }
  }

  async function remove(id: string) {
    await api.deleteLocation(id, token);
    refresh();
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title="Add a location" subtitle="Named community units — no coordinates required" icon={<span>📍</span>}>
        <form onSubmit={create} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Name (optional label)">
              <TextInput value={form.name} onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))} placeholder="Rewa cluster" />
            </Field>
            <Field label="State">
              <TextInput value={form.state} onChange={(e) => setForm((s) => ({ ...s, state: e.target.value }))} />
            </Field>
            <Field label="District">
              <TextInput value={form.district} onChange={(e) => setForm((s) => ({ ...s, district: e.target.value }))} />
            </Field>
            <Field label="City / town">
              <TextInput value={form.city} onChange={(e) => setForm((s) => ({ ...s, city: e.target.value }))} />
            </Field>
            <Field label="Intensity (1–10)">
              <NumberInput min={1} max={10} value={form.intensity} onChange={(e) => setForm((s) => ({ ...s, intensity: e.target.value }))} />
            </Field>
          </div>
          <Field label="Details">
            <TextArea value={form.details} onChange={(e) => setForm((s) => ({ ...s, details: e.target.value }))} />
          </Field>
          {error && <Alert tone="error">{error}</Alert>}
          <Button type="submit">Add location</Button>
        </form>
      </Card>

      <Card title={`Locations (${items.length})`} subtitle="Used as community-unit fallback for signal counts" icon={<span>🗂️</span>}>
        {loading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-400">No locations yet.</p>
        ) : (
          <ul className="space-y-2">
            {items.map((it) => (
              <li key={it.id} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium text-slate-800">
                    {it.name || it.city}
                    {it.name && <span className="ml-1.5 text-xs font-normal text-slate-400">{it.city}</span>}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {it.state} · {it.district} · intensity {it.intensity}/10
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge color="blue">{it.district}</Badge>
                  <button onClick={() => remove(it.id)} className="text-xs text-red-500 hover:text-red-700">
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
