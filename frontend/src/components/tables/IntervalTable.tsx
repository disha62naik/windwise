import { useMemo, useState } from "react";
import type { IntervalRecord } from "../../types/api";
import { downloadCsv } from "../../utils/csv";
import { fmtDateTimeLondon, fmtMw, fmtSigned } from "../../utils/format";
import { filterAndSort, type SortKey } from "../../utils/table";

const COLS: { key: SortKey; label: string }[] = [
  { key: "delivery_start_utc", label: "Delivery time" },
  { key: "forecast_mw", label: "Forecast" },
  { key: "actual_mw", label: "Actual" },
  { key: "signed_error_mw", label: "Signed error (F − A)" },
  { key: "absolute_error_mw", label: "Absolute error" },
];

export function IntervalTable({ records, date }: { records: IntervalRecord[]; date: string }) {
  const [query, setQuery] = useState("");
  const [key, setKey] = useState<SortKey>("delivery_start_utc");
  const [dir, setDir] = useState<"asc" | "desc">("asc");
  const rows = useMemo(() => filterAndSort(records, query, key, dir), [records, query, key, dir]);

  const toggle = (k: SortKey) => {
    if (k === key) setDir(dir === "asc" ? "desc" : "asc");
    else { setKey(k); setDir("asc"); }
  };

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-end gap-3">
        <label className="text-sm">
          <span className="block text-slate-600">Search</span>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="time or status, e.g. MISSING" className="rounded border border-slate-300 px-2 py-1" />
        </label>
        <button onClick={() => downloadCsv(rows, `windwise-${date}.csv`)} className="rounded bg-green-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-800">
          Export CSV ({rows.length} rows)
        </button>
      </div>
      <div className="max-h-[32rem] overflow-auto rounded border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-slate-50">
            <tr>
              {COLS.map((c) => (
                <th key={c.key} scope="col" aria-sort={key === c.key ? (dir === "asc" ? "ascending" : "descending") : "none"} className="px-3 py-2">
                  <button onClick={() => toggle(c.key)} className="font-semibold">
                    {c.label} {key === c.key ? (dir === "asc" ? "▲" : "▼") : ""}
                  </button>
                </th>
              ))}
              <th scope="col" className="px-3 py-2 font-semibold">Forecast published</th>
              <th scope="col" className="px-3 py-2 font-semibold">Data quality</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.delivery_start_utc} className="border-t border-slate-100">
                <td className="px-3 py-1.5 whitespace-nowrap">{fmtDateTimeLondon(r.delivery_start_utc)}</td>
                <td className="px-3 py-1.5">{fmtMw(r.forecast_mw)}</td>
                <td className="px-3 py-1.5">{fmtMw(r.actual_mw)}</td>
                <td className="px-3 py-1.5">{r.signed_error_mw === null ? "—" : `${r.signed_error_mw > 0 ? "▲ " : r.signed_error_mw < 0 ? "▼ " : ""}${fmtSigned(r.signed_error_mw)}`}</td>
                <td className="px-3 py-1.5">{fmtMw(r.absolute_error_mw)}</td>
                <td className="px-3 py-1.5 whitespace-nowrap">{fmtDateTimeLondon(r.selected_publish_time_utc)}</td>
                <td className="px-3 py-1.5">{r.data_quality_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
