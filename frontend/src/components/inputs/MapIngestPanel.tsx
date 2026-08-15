"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, errMsg } from "@/lib/api";
import { useApp } from "@/lib/store";
import { Alert, Badge, Button, Card, EmptyState, Field, Select, Table } from "@/components/ui";
import { MAP_CATEGORIES, type IngestRecordMeta, type MapsHealth } from "@/lib/types";

export function MapIngestPanel() {
  const { token } = useApp();
  const [health, setHealth] = useState<MapsHealth | null>(null);
  const [records, setRecords] = useState<IngestRecordMeta[]>([]);
  const [category, setCategory] = useState<string>("base_maps");
  const [name, setName] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      const [h, r] = await Promise.all([api.mapsHealth(token), api.listMaps(token)]);
      setHealth(h);
      setRecords(r);
    } catch (e) {
      setError(errMsg(e));
    }
  }, [token]);

  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const [h, r] = await Promise.all([api.mapsHealth(token), api.listMaps(token)]);
        if (ignore) return;
        setHealth(h);
        setRecords(r);
      } catch (e) {
        if (!ignore) setError(errMsg(e));
      }
    })();
    return () => {
      ignore = true;
    };
  }, [token]);

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    if (!files || files.length === 0) {
      setError("Select at least one file to upload.");
      return;
    }
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      const form = new FormData();
      for (const f of Array.from(files)) form.append("files", f);
      form.append("category", category);
      if (name) form.append("name", name);
      const res = await api.uploadMaps(form, token);
      setOk(
        `Uploaded ${res.summary.uploaded} file(s) → ${res.summary.records} record(s): ${res.summary.representations.join(", ")}` +
          (res.summary.errors.length ? ` · errors: ${res.summary.errors.join("; ")}` : "")
      );
      if (fileRef.current) fileRef.current.value = "";
      setFiles(null);
      refresh();
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    await api.deleteMap(id, token);
    refresh();
  }

  return (
    <div className="space-y-6">
      {health && (
        <Alert tone="info" title={`Ingest service ${health.status} — v${health.version}`}>
          Supported types: {health.supported_types.join(", ")} · shapefile sets merge into a single record · rasters, point clouds,
          tabular and documents are converted to a common representation (GeoJSON EPSG:4326, normalized rasters, extracted text).
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Upload map data" subtitle="Vector, raster, point-cloud, tabular, document or bundle (.zip)" icon={<span>🗂️</span>}>
          <form onSubmit={upload} className="space-y-4">
            <Field label="Category">
              <Select value={category} onChange={(e) => setCategory(e.target.value)}>
                {MAP_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c.replace("_", " ")}</option>
                ))}
              </Select>
            </Field>
            <Field label="Name (optional)">
              <input
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="village_boundary"
              />
            </Field>
            <Field label="Files (multi-select)">
              <input
                ref={fileRef}
                type="file"
                multiple
                onChange={(e) => setFiles(e.target.files)}
                className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-teal-50 file:px-3 file:py-2 file:text-xs file:font-medium file:text-teal-700 hover:file:bg-teal-100"
              />
            </Field>
            {error && <Alert tone="error">{error}</Alert>}
            {ok && <Alert tone="success">{ok}</Alert>}
            <Button type="submit" loading={busy}>
              {busy ? "Uploading & converting…" : "Upload & ingest"}
            </Button>
          </form>
        </Card>

        <Card title={`Ingested records (${records.length})`} subtitle="Heavy payloads trimmed in list view" icon={<span>📚</span>}>
          {records.length === 0 ? (
            <EmptyState title="No ingested records yet" body="Upload a GeoJSON, shapefile, raster, CSV or PDF above — NEXUS converts it to a common representation." />
          ) : (
            <ul className="max-h-[420px] space-y-2 overflow-y-auto pr-1">
              {records.map((r) => (
                <li key={r.id} className="rounded-lg border border-slate-200 px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-slate-800">{r.name}</div>
                      <div className="text-[11px] text-slate-500">
                        {r.category} · {r.source_type} → {r.representation} · {(r.size_bytes / 1024).toFixed(1)} KB
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <Badge color={r.confidence === "high" ? "emerald" : "amber"}>{r.confidence}</Badge>
                      <button onClick={() => remove(r.id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                    </div>
                  </div>
                  {r.feature_count !== null && (
                    <div className="mt-1 text-[11px] text-slate-400">features: {r.feature_count} · CRS {r.target_crs}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {records.length > 0 && (
        <Card title="Ingest registry" padded={false}>
          <Table head={["Name", "Category", "Source", "Representation", "CRS", "Features", "Confidence"]}>
            {records.map((r) => (
              <tr key={r.id}>
                <td className="max-w-[220px] truncate px-3 py-2 font-medium text-slate-800">{r.name}</td>
                <td className="px-3 py-2 text-slate-500">{r.category}</td>
                <td className="px-3 py-2 text-slate-500">{r.source_type}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-600">{r.representation}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-600">{r.target_crs}</td>
                <td className="px-3 py-2 text-slate-500">{r.feature_count ?? "—"}</td>
                <td className="px-3 py-2"><Badge color={r.confidence === "high" ? "emerald" : "amber"}>{r.confidence}</Badge></td>
              </tr>
            ))}
          </Table>
        </Card>
      )}
    </div>
  );
}
