import { useState } from "react";
import { MetricCard } from "../../components/cards/MetricCard";
import { ErrorChart } from "../../components/charts/ErrorChart";
import { ForecastChart } from "../../components/charts/ForecastChart";
import { EmptyState, ErrorState, Loading, WarningBanner } from "../../components/feedback/States";
import { useDayForecast, useErrors, useRevisions } from "../../hooks/useApi";
import { fmtDateTimeLondon, fmtMw, fmtPct, fmtSigned } from "../../utils/format";

function Revisions({ date, options }: { date: string; options: string[] }) {
  const [sel, setSel] = useState<string | null>(null);
  const q = useRevisions(date, sel);
  return (
    <section aria-labelledby="rev-h" className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 id="rev-h" className="font-semibold">Forecast publication history (audit)</h3>
      <p className="text-xs text-slate-500">Shows which revision was selected at the cutoff, earlier ones, and later ones that were NOT available.</p>
      <label className="mt-2 block text-sm">
        <span className="text-slate-600">Delivery interval</span>{" "}
        <select value={sel ?? ""} onChange={(e) => setSel(e.target.value || null)} className="rounded border border-slate-300 px-2 py-1">
          <option value="">Select…</option>
          {options.map((o) => <option key={o} value={o}>{fmtDateTimeLondon(o)}</option>)}
        </select>
      </label>
      {q.isLoading && <Loading label="Loading revisions (fetches post-cutoff data)…" />}
      {q.error && <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />}
      {q.data && (
        <table className="mt-3 w-full text-left text-sm">
          <thead><tr><th scope="col">Role</th><th scope="col">Published</th><th scope="col">Forecast</th><th scope="col">Lead time</th></tr></thead>
          <tbody>
            {q.data.revisions.map((r) => (
              <tr key={r.publish_time_utc} className={r.role === "SELECTED" ? "bg-green-50 font-medium" : r.role === "LATER_UNAVAILABLE" ? "text-slate-400 line-through" : ""}>
                <td>{r.role.replace("_", " ")}</td><td>{fmtDateTimeLondon(r.publish_time_utc)}</td>
                <td>{fmtMw(r.forecast_mw)}</td><td>{r.lead_time_hours === null ? "—" : `${r.lead_time_hours.toFixed(1)} h`}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export function Dashboard({ date }: { date: string }) {
  const day = useDayForecast(date);
  const errs = useErrors(date);
  if (day.isLoading) return <Loading />;
  if (day.error) return <ErrorState message={(day.error as Error).message} onRetry={() => day.refetch()} />;
  const d = day.data!;
  const m = d.metrics;
  const options = d.records.filter((r) => r.forecast_mw !== null).map((r) => r.delivery_start_utc);

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">
        Delivery date <strong>{d.delivery_date}</strong> · decision cutoff <strong>{fmtDateTimeLondon(d.decision_cutoff_utc)}</strong> ({d.cutoff_rule})
      </p>
      {d.resolution && <p className="text-xs text-slate-500">Evaluation resolution: {d.resolution.minutes} min — {d.resolution.method}</p>}
      <WarningBanner title={d.status === "partial" ? "Partial data" : "Data-quality notes"} items={d.warnings} />
      {d.status === "empty" ? (
        <EmptyState>No interval has both a forecast available at the cutoff and an actual. Metrics are not shown rather than shown as zero.</EmptyState>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard id="m-pub" label="Latest eligible forecast published" value={fmtDateTimeLondon(d.latest_selected_publish_time_utc)} hint="Newest publication at or before the cutoff." />
            <MetricCard id="m-fc" label="Avg forecast" value={fmtMw(d.mean_forecast_mw)} hint="Mean of selected forecasts over intervals that have one." />
            <MetricCard id="m-ac" label="Avg actual (matched)" value={fmtMw(d.mean_actual_matched_mw)} hint="Mean actual over matched intervals only." />
            <MetricCard id="m-cov" label="Coverage" value={`${d.coverage.matched_intervals} / ${d.coverage.expected_intervals}`} hint="Matched intervals / expected half-hours." tone={d.status === "partial" ? "warn" : "default"} />
            <MetricCard id="m-mae" label="MAE" value={fmtMw(m.mae_mw, 1)} hint="Mean |forecast − actual|. Lower is better." />
            <MetricCard id="m-rmse" label="RMSE" value={fmtMw(m.rmse_mw, 1)} hint="Penalises large errors more than MAE." />
            <MetricCard id="m-bias" label="Bias" value={fmtSigned(m.bias_mw, 1)} hint="Mean (forecast − actual). Positive = over-forecast on average." />
            <MetricCard id="m-mape" label="MAPE" value={fmtPct(m.mape_pct)} hint={`Non-zero actuals only; ${m.mape_excluded_zero_actual} excluded.`} />
          </div>
          <section aria-labelledby="fc-h" className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 id="fc-h" className="mb-2 font-semibold">Forecast vs actual</h3>
            <ForecastChart records={d.records} date={d.delivery_date} />
          </section>
          <section aria-labelledby="er-h" className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 id="er-h" className="mb-2 font-semibold">Forecast error</h3>
            <ErrorChart records={d.records} />
            {errs.data && errs.data.distribution.n > 0 && (
              <div className="mt-3 grid gap-4 text-sm md:grid-cols-2">
                <div>
                  <p>Over-forecast intervals: <strong>{errs.data.distribution.over_forecast_intervals}</strong> · under-forecast: <strong>{errs.data.distribution.under_forecast_intervals}</strong></p>
                  {errs.data.distribution.abs_error_percentiles_mw && (
                    <p className="text-slate-600">Absolute error median {fmtMw(errs.data.distribution.abs_error_percentiles_mw.p50)}, p90 {fmtMw(errs.data.distribution.abs_error_percentiles_mw.p90)}, max {fmtMw(errs.data.distribution.abs_error_percentiles_mw.p100)}</p>
                  )}
                </div>
                <div>
                  <p className="font-medium">Largest absolute errors</p>
                  <ol className="list-decimal pl-5">
                    {errs.data.distribution.largest_errors.slice(0, 5).map((r) => (
                      <li key={r.delivery_start_utc}>{fmtDateTimeLondon(r.delivery_start_utc)} — {fmtSigned(r.signed_error_mw)}</li>
                    ))}
                  </ol>
                </div>
              </div>
            )}
          </section>
        </>
      )}
      <Revisions date={date} options={options} />
    </div>
  );
}
