import { ErrorState, Loading, WarningBanner } from "../../components/feedback/States";
import { useQuality } from "../../hooks/useApi";
import { fmtDateTimeLondon } from "../../utils/format";

export function DataQuality({ month }: { month: string }) {
  const q = useQuality(month);
  if (q.isLoading) return <Loading />;
  if (q.error) return <ErrorState message={(q.error as Error).message} onRetry={() => q.refetch()} />;
  const d = q.data!;
  const rows: [string, string | number][] = [
    ["Retrieval status", d.retrieval_status], ["Data retrieved", fmtDateTimeLondon(d.data_retrieved_at)],
    ["Forecast publish window (UTC)", d.forecast_publish_window_utc.join(" → ")],
    ["Expected intervals", d.expected_intervals], ["Actual intervals", d.actual_intervals],
    ["Forecast intervals (selected at cutoff)", d.forecast_intervals], ["Matched intervals", d.matched_intervals],
    ["Missing forecast intervals", d.missing_forecast_intervals], ["Missing actual intervals", d.missing_actual_intervals],
    ["Intervals with only post-cutoff forecasts", d.intervals_with_only_later_forecasts],
    ["Source actual rows (WIND)", d.source_actual_rows], ["Source forecast rows", d.source_forecast_rows],
    ["Invalid actual records", d.invalid_actual_records], ["Invalid forecast records", d.invalid_forecast_records],
    ["Duplicate actuals collapsed", d.duplicate_actual_records_collapsed],
    ["Duplicate forecasts collapsed", d.duplicate_forecast_records_collapsed],
    ["Conflicting forecast duplicates", d.conflicting_forecast_duplicates],
    ["Non-wind records ignored", d.non_wind_records_ignored],
  ];
  return (
    <div className="space-y-4">
      <WarningBanner title="Warnings" items={d.warnings} />
      <dl className="grid gap-px overflow-hidden rounded border border-slate-200 bg-slate-200 sm:grid-cols-2">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between bg-white px-3 py-2 text-sm"><dt className="text-slate-600">{k}</dt><dd className="font-medium">{v}</dd></div>
        ))}
      </dl>
    </div>
  );
}
