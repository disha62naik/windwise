export function Methodology() {
  return (
    <article className="prose max-w-3xl space-y-3 text-sm leading-relaxed">
      <h3 className="text-lg font-semibold">Methodology</h3>
      <p><strong>Sources.</strong> Elexon BMRS Insights API: FUELHH (actual wind, half-hourly MW, filtered to WIND) and WINDFOR (wind forecasts with publishTime). Delivery time (startTime) and publication time (publishTime) are different fields and never interchanged.</p>
      <p><strong>Forecast selection.</strong> For each delivery interval, the latest forecast with publishTime ≤ the decision cutoff is used. Later revisions are never used, avoiding look-ahead bias. Forecasts published before the month (e.g. December) are included.</p>
      <p><strong>Decision cutoff.</strong> Assumed 09:20 Europe/London on the day before delivery. This is a configurable assumption, not a market rule confirmed by the brief.</p>
      <p><strong>Metrics.</strong> error = forecast − actual (MW). MAE = mean|error|; RMSE = √mean(error²); Bias = mean(error); MAPE = mean(|error|/|actual|)×100 over non-zero actuals only. All use matched intervals only; nothing is imputed.</p>
      <p><strong>Missing data.</strong> Missing values stay missing (never zero). Intervals without a forecast or actual are excluded from metrics and counted in the data-quality panel.</p>
      <p><strong>Time.</strong> Instants are UTC internally; days and display are Europe/London, so DST days have 46 or 50 half-hours.</p>
      <p><strong>Limitations.</strong> One month does not establish long-term performance. WINDFOR appears hourly, so half-hour intervals without a forecast are reported as unmatched, not interpolated. This tool supports decisions; it does not compute an optimal procurement position.</p>
    </article>
  );
}
