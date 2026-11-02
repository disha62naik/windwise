import type {
  AccuracyResponse, DataQualityResponse, DayForecastResponse, ErrorsResponse, RevisionsResponse,
} from "../types/api";

// Empty string = same origin (Vite dev proxy / nginx proxy). Set VITE_API_URL for a separate host.
export const API_BASE: string = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function get<T>(path: string, params: Record<string, string>): Promise<T> {
  const url = `${API_BASE}/api/${path}?${new URLSearchParams(params).toString()}`;
  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new ApiError("Cannot reach the WindWise API. Is the backend running?", 0);
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch { /* keep default */ }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

export const api = {
  forecast: (date: string) => get<DayForecastResponse>("forecast", { date }),
  errors: (date: string) => get<ErrorsResponse>("forecast-errors", { date }),
  overview: (month: string) => get<AccuracyResponse>("overview", { month }),
  quality: (month: string) => get<DataQualityResponse>("data-quality", { month }),
  revisions: (date: string, intervalStart: string) =>
    get<RevisionsResponse>("revisions", { date, interval_start: intervalStart }),
};
