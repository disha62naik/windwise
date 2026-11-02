const TZ = "Europe/London";

export function fmtMw(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits })} MW`;
}

export function fmtPct(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : `${value.toFixed(1)}%`;
}

export function fmtSigned(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return "—";
  const s = value.toLocaleString("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  return value > 0 ? `+${s} MW` : `${s} MW`;
}

export function fmtTimeLondon(iso: string): string {
  return new Intl.DateTimeFormat("en-GB", { timeZone: TZ, hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
}

/** e.g. "14 Jan 2026, 09:20 GMT" — always names the zone to avoid ambiguity. */
export function fmtDateTimeLondon(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: TZ, day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", timeZoneName: "short",
  }).format(new Date(iso));
}
