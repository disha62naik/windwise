interface Props { label: string; value: string; hint: string; id: string; tone?: "default" | "warn" }

export function MetricCard({ label, value, hint, id, tone = "default" }: Props) {
  return (
    <div className={`rounded-lg border bg-white p-4 shadow-sm ${tone === "warn" ? "border-amber-300" : "border-slate-200"}`}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p aria-describedby={id} className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      <p id={id} className="mt-1 text-xs text-slate-500" title={hint}>{hint}</p>
    </div>
  );
}
