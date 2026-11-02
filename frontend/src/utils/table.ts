import type { IntervalRecord } from "../types/api";

export type SortKey = "delivery_start_utc" | "forecast_mw" | "actual_mw" | "signed_error_mw" | "absolute_error_mw";

export function filterAndSort(rows: IntervalRecord[], query: string, key: SortKey, dir: "asc" | "desc"): IntervalRecord[] {
  const q = query.trim().toLowerCase();
  const filtered = q
    ? rows.filter((r) => `${r.delivery_start_local} ${r.data_quality_status} ${r.selection_status}`.toLowerCase().includes(q))
    : rows;
  const sign = dir === "asc" ? 1 : -1;
  return [...filtered].sort((a, b) => {
    const x = a[key], y = b[key];
    if (x === null && y === null) return 0;
    if (x === null) return 1; // nulls always last
    if (y === null) return -1;
    return (x < y ? -1 : x > y ? 1 : 0) * sign;
  });
}
