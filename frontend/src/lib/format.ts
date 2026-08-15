/** Formatting helpers for INR, crores, percents, dates. */

export function inr(n: number | null | undefined, compact = false): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const v = Math.round(n);
  if (compact) {
    if (v >= 1e7) return `₹${(v / 1e7).toFixed(1)} Cr`;
    if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`;
    if (v >= 1e3) return `₹${(v / 1e3).toFixed(1)} K`;
  }
  return `₹${v.toLocaleString("en-IN")}`;
}

export function crores(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 2 })} Cr`;
}

export function pct(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

export function dateShort(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function cls(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}

export function severityColor(sev: string): string {
  const s = sev.toUpperCase();
  if (s.includes("CRITICAL")) return "bg-red-100 text-red-700 border-red-200";
  if (s.includes("HIGH") || s.includes("SEVERE")) return "bg-orange-100 text-orange-700 border-orange-200";
  if (s.includes("ELEVATED") || s.includes("MODERATE")) return "bg-amber-100 text-amber-700 border-amber-200";
  if (s.includes("LOW")) return "bg-emerald-100 text-emerald-700 border-emerald-200";
  return "bg-slate-100 text-slate-700 border-slate-200";
}

export function riskColor(risk: string): string {
  const r = risk.toUpperCase();
  if (r.includes("LOW")) return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (r.includes("MEDIUM")) return "bg-amber-50 text-amber-700 border-amber-200";
  if (r.includes("HIGH")) return "bg-red-50 text-red-700 border-red-200";
  return "bg-slate-50 text-slate-600 border-slate-200";
}
