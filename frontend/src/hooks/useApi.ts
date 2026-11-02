import { useQuery } from "@tanstack/react-query";
import { api } from "../services/api";

const opts = { staleTime: 5 * 60_000, retry: 1 } as const;

export const useDayForecast = (date: string) =>
  useQuery({ queryKey: ["forecast", date], queryFn: () => api.forecast(date), ...opts });
export const useErrors = (date: string) =>
  useQuery({ queryKey: ["errors", date], queryFn: () => api.errors(date), ...opts });
export const useOverview = (month: string) =>
  useQuery({ queryKey: ["overview", month], queryFn: () => api.overview(month), ...opts });
export const useQuality = (month: string) =>
  useQuery({ queryKey: ["quality", month], queryFn: () => api.quality(month), ...opts });
export const useRevisions = (date: string, intervalStart: string | null) =>
  useQuery({
    queryKey: ["revisions", date, intervalStart],
    queryFn: () => api.revisions(date, intervalStart as string),
    enabled: intervalStart !== null, ...opts,
  });
