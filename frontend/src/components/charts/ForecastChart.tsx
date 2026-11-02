import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { IntervalRecord } from "../../types/api";
import { fmtDateTimeLondon, fmtTimeLondon } from "../../utils/format";

export function ForecastChart({ records, date }: { records: IntervalRecord[]; date: string }) {
  const data = records.map((r) => ({ t: r.delivery_start_utc, forecast: r.forecast_mw, actual: r.actual_mw }));
  const nF = data.filter((d) => d.forecast !== null).length;
  const nA = data.filter((d) => d.actual !== null).length;
  return (
    <figure>
      <div role="img" aria-label={`Forecast versus actual wind generation in MW for ${date}. ${nF} forecast points and ${nA} actual points; gaps show missing data.`} className="h-80 w-full">
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="t" tickFormatter={fmtTimeLondon} minTickGap={32} />
            <YAxis unit=" MW" width={80} />
            <Tooltip labelFormatter={(l) => fmtDateTimeLondon(String(l))} formatter={(v, name) => [v == null ? "missing" : `${Number(v).toLocaleString("en-GB")} MW`, name]} />
            <Legend />
            {/* Forecast is published hourly, so its line joins hourly points; actuals are NOT joined across gaps. */}
            <Line name="Forecast (selected at cutoff)" dataKey="forecast" stroke="#15803d" strokeWidth={2} dot={{ r: 2 }} connectNulls />
            <Line name="Actual" dataKey="actual" stroke="#0b1b33" strokeWidth={2} dot={false} connectNulls={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="mt-1 text-xs text-slate-500">Times in Europe/London. Forecast points are connected only because WINDFOR is hourly; missing actuals leave gaps.</figcaption>
    </figure>
  );
}
