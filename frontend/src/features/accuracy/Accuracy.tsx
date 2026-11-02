import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { MetricCard } from "../../components/cards/MetricCard";
import { EmptyState, ErrorState, Loading } from "../../components/feedback/States";
import { useOverview } from "../../hooks/useApi";
import { fmtMw, fmtPct, fmtSigned } from "../../utils/format";

export function Accuracy({ month, onPickDate }: { month: string; onPickDate: (d: string) => void }) {
  const q = useOverview(month);
  if (q.isLoading) return <Loading label="Loading the month (first load may take a minute while Elexon data is fetched)…" />;
  if (q.error) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  const a = q.data!;
  if (a.status === "empty") return <EmptyState>No matched intervals in {month}.</EmptyState>;
  const chart = a.daily.map((d) => ({ date: d.delivery_date.slice(8), mae: d.mae_mw }));
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">{a.start} → {a.end} · {a.cutoff_rule}</p>
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-5">
        <MetricCard id="a-mae" label="MAE" value={fmtMw(a.metrics.mae_mw, 1)} hint="Mean absolute error" />
        <MetricCard id="a-rmse" label="RMSE" value={fmtMw(a.metrics.rmse_mw, 1)} hint="Root mean squared error" />
        <MetricCard id="a-bias" label="Bias" value={fmtSigned(a.metrics.bias_mw, 1)} hint="Forecast − actual, mean" />
        <MetricCard id="a-mape" label="MAPE" value={fmtPct(a.metrics.mape_pct)} hint={`${a.metrics.mape_excluded_zero_actual} zero-actual excluded`} />
        <MetricCard id="a-n" label="Matched intervals" value={`${a.coverage.matched_intervals} / ${a.coverage.expected_intervals}`} hint="Used for every metric" />
      </div>
      <section aria-labelledby="dm" className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 id="dm" className="mb-2 font-semibold">Daily MAE (MW)</h3>
        <div role="img" aria-label="Bar chart of daily mean absolute error in MW" className="h-56">
          <ResponsiveContainer><BarChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis width={70} /><Tooltip /><Bar dataKey="mae" fill="#15803d" /></BarChart></ResponsiveContainer>
        </div>
      </section>
      <div className="overflow-auto rounded border border-slate-200 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50"><tr>{["Date", "MAE", "RMSE", "Bias", "MAPE", "Matched"].map((h) => <th key={h} scope="col" className="px-3 py-2">{h}</th>)}</tr></thead>
          <tbody>
            {a.daily.map((d) => (
              <tr key={d.delivery_date} className="border-t border-slate-100">
                <td className="px-3 py-1.5"><button className="text-green-800 underline" onClick={() => onPickDate(d.delivery_date)}>{d.delivery_date}</button></td>
                <td className="px-3 py-1.5">{fmtMw(d.mae_mw, 1)}</td><td className="px-3 py-1.5">{fmtMw(d.rmse_mw, 1)}</td>
                <td className="px-3 py-1.5">{fmtSigned(d.bias_mw, 1)}</td><td className="px-3 py-1.5">{fmtPct(d.mape_pct)}</td>
                <td className="px-3 py-1.5">{d.matched_intervals}/{d.expected_intervals}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-500">{a.caveat}</p>
    </div>
  );
}
