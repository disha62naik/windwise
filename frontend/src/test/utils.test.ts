import { toCsv } from "../utils/csv";
import { fmtMw, fmtPct, fmtSigned } from "../utils/format";
import { filterAndSort } from "../utils/table";
import type { IntervalRecord } from "../types/api";

const rec = (t: string, f: number | null, a: number | null, e: number | null): IntervalRecord => ({
  delivery_start_utc: t, delivery_start_local: t, delivery_date: "2026-01-15", forecast_mw: f, actual_mw: a,
  signed_error_mw: e, absolute_error_mw: e === null ? null : Math.abs(e), selected_publish_time_utc: null,
  selection_status: "SELECTED", data_quality_status: e === null ? "MISSING_ACTUAL" : "OK",
  n_eligible_revisions: 1, n_later_revisions: 0,
});

describe("formatting", () => {
  it("shows an em dash for missing values, never zero", () => {
    expect(fmtMw(null)).toBe("—");
    expect(fmtPct(null)).toBe("—");
    expect(fmtSigned(undefined)).toBe("—");
  });
  it("formats MW and signed values", () => {
    expect(fmtMw(1234.5, 1)).toBe("1,234.5 MW");
    expect(fmtSigned(10)).toBe("+10 MW");
    expect(fmtSigned(-10)).toBe("-10 MW");
  });
});

describe("csv", () => {
  it("exports header, MW values and blanks for missing", () => {
    const csv = toCsv([rec("2026-01-15T00:00:00Z", 110, 100, 10), rec("2026-01-15T01:00:00Z", 5, null, null)]);
    const lines = csv.split("\n");
    expect(lines[0]).toContain("signed_error_mw");
    expect(lines[1]).toBe("2026-01-15T00:00:00Z,2026-01-15T00:00:00Z,110,100,10,10,,OK");
    expect(lines[2]).toBe("2026-01-15T01:00:00Z,2026-01-15T01:00:00Z,5,,,,,MISSING_ACTUAL");
  });
});

describe("table", () => {
  const rows = [rec("a", 1, 1, 5), rec("b", 2, null, null), rec("c", 3, 1, -9)];
  it("sorts and keeps nulls last in both directions", () => {
    expect(filterAndSort(rows, "", "signed_error_mw", "asc").map((r) => r.delivery_start_utc)).toEqual(["c", "a", "b"]);
    expect(filterAndSort(rows, "", "signed_error_mw", "desc").map((r) => r.delivery_start_utc)).toEqual(["a", "c", "b"]);
  });
  it("filters by status text", () => {
    expect(filterAndSort(rows, "missing", "delivery_start_utc", "asc")).toHaveLength(1);
  });
});
