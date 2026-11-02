export type Status = "ok" | "partial" | "empty";

export interface Metrics {
  n_matched: number;
  mae_mw: number | null;
  rmse_mw: number | null;
  bias_mw: number | null;
  median_abs_error_mw: number | null;
  mape_pct: number | null;
  mape_n: number;
  mape_excluded_zero_actual: number;
}

export interface Coverage {
  expected_intervals: number;
  actual_intervals: number;
  forecast_intervals: number;
  matched_intervals: number;
  missing_forecast_intervals: number;
  missing_actual_intervals: number;
  intervals_with_only_later_forecasts: number;
}

export interface IntervalRecord {
  delivery_start_utc: string;
  delivery_start_local: string;
  delivery_date: string;
  forecast_mw: number | null;
  actual_mw: number | null;
  signed_error_mw: number | null;
  absolute_error_mw: number | null;
  selected_publish_time_utc: string | null;
  selection_status: string;
  data_quality_status: string;
  n_eligible_revisions: number;
  n_later_revisions: number;
}

export interface DayForecastResponse {
  status: Status;
  delivery_date: string;
  timezone: string;
  decision_cutoff_utc: string;
  decision_cutoff_local: string;
  cutoff_rule: string;
  resolution?: { minutes: number; method: string };
  latest_selected_publish_time_utc: string | null;
  mean_forecast_mw: number | null;
  mean_actual_matched_mw: number | null;
  metrics: Metrics;
  coverage: Coverage;
  warnings: string[];
  data_retrieved_at: string | null;
  records: IntervalRecord[];
}

export interface ErrorDistribution {
  n: number;
  over_forecast_intervals: number;
  under_forecast_intervals: number;
  exact_intervals: number;
  abs_error_percentiles_mw: Record<string, number> | null;
  signed_error_histogram: { bin_edges_mw: number[]; counts: number[] } | null;
  largest_errors: IntervalRecord[];
}

export interface ErrorsResponse {
  status: Status;
  delivery_date: string;
  coverage: Coverage;
  distribution: ErrorDistribution;
  records: IntervalRecord[];
}

export interface DailySummary extends Metrics, Coverage {
  delivery_date: string;
}

export interface AccuracyResponse {
  status: Status;
  start: string;
  end: string;
  cutoff_rule: string;
  metrics: Metrics;
  coverage: Coverage;
  daily: DailySummary[];
  caveat: string;
  data_retrieved_at: string | null;
}

export interface DataQualityResponse extends Coverage {
  status: Status;
  start: string;
  end: string;
  retrieval_status: string;
  data_retrieved_at: string | null;
  forecast_publish_window_utc: (string | null)[];
  source_actual_rows: number;
  source_forecast_rows: number;
  invalid_actual_records: number;
  invalid_forecast_records: number;
  duplicate_actual_records_collapsed: number;
  duplicate_forecast_records_collapsed: number;
  conflicting_forecast_duplicates: number;
  non_wind_records_ignored: number;
  warnings: string[];
}

export interface Revision {
  publish_time_utc: string | null;
  forecast_mw: number | null;
  lead_time_hours: number | null;
  role: "SELECTED" | "EARLIER_ELIGIBLE" | "LATER_UNAVAILABLE";
}

export interface RevisionsResponse {
  delivery_start_utc: string;
  decision_cutoff_utc: string;
  includes_post_cutoff_revisions: boolean;
  revisions: Revision[];
}
