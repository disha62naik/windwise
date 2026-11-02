import type { IntervalRecord } from "../types/api";

const HEADER = [
  "delivery_start_utc", "delivery_start_local", "forecast_mw", "actual_mw", "signed_error_mw",
  "absolute_error_mw", "selected_publish_time_utc", "data_quality_status",
];

function cell(v: string | number | null): string {
  if (v === null) return "";
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

/** Same units (MW), sign convention (forecast - actual) and rows as the on-screen table. */
export function toCsv(rows: IntervalRecord[]): string {
  const lines = rows.map((r) =>
    [r.delivery_start_utc, r.delivery_start_local, r.forecast_mw, r.actual_mw, r.signed_error_mw,
      r.absolute_error_mw, r.selected_publish_time_utc, r.data_quality_status].map(cell).join(","));
  return [HEADER.join(","), ...lines].join("\n");
}

export function downloadCsv(rows: IntervalRecord[], filename: string): void {
  const url = URL.createObjectURL(new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
