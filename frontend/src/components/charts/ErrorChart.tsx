import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { IntervalRecord } from "../../types/api";
import { fmtDateTimeLondon, fmtSigned, fmtTimeLondon } from "../../utils/format";

export function ErrorChart({ records }: { records: IntervalRecord[] }) {
  const data = records.filter((r) => r.signed_error_mw !== null)
    .map((r) => ({ t: r.delivery_start_utc, e: r.signed_error_mw as number }));
  return (
    <figure>
      <p className="mb-1 text-xs text-slate-600">
        <strong>Error = forecast − actual.</strong> Bars above zero (▲ amber) = over-forecast; below zero (▼ blue) = under-forecast.
      </p>
      <div role="img" aria-label={`Signed forecast error in MW for ${data.length} matched intervals`} className="h-64 w-full">
        <ResponsiveContainer>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="t" tickFormatter={fmtTimeLondon} minTickGap={32} />
            <YAxis unit=" MW" width={80} />
            <Tooltip labelFormatter={(l) => fmtDateTimeLondon(String(l))} formatter={(v) => { const n = Number(v); return [`${fmtSigned(n)} (${n > 0 ? "over" : n < 0 ? "under" : "exact"}-forecast)`, "Error"]; }} />
            <ReferenceLine y={0} stroke="#475569" />
            <Bar dataKey="e">{data.map((d) => <Cell key={d.t} fill={d.e >= 0 ? "#b45309" : "#1d4ed8"} />)}</Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  );
}
