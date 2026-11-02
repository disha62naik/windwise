"""Fetch real data from Elexon, verify it, compute metrics and write a results report.

    python -m scripts.generate_results --start 2026-01-01 --end 2026-01-31 --out-dir ../docs/results --save-raw

Requires network access. Nothing is simulated: if the fetch or the checks fail, it exits with an error.
"""
from __future__ import annotations

import argparse
import gzip
import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from app.clients.elexon_client import ElexonClient
from app.config import Settings
from app.services.analysis import build_range_records, quality_report, summarise
from app.services.data_loader import forecast_publish_window
from app.services.normalization import normalize_actuals, normalize_forecasts
from app.services.report import render_markdown
from app.services.resolution import describe, resolve_resolution


def _minutes(rows: list[dict]) -> list[int]:
    return sorted({int(m) for m in pd.to_datetime([r["startTime"] for r in rows], utc=True).minute})


def _range(rows: list[dict]) -> list[float] | None:
    v = [float(r["generation"]) for r in rows if r.get("generation") is not None]
    return [min(v), max(v)] if v else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-01-01")
    ap.add_argument("--end", default="2026-01-31")
    ap.add_argument("--out-dir", default="../docs/results")
    ap.add_argument("--save-raw", action="store_true", help="save gzip'd raw responses under data/raw/ (gitignored)")
    a = ap.parse_args()
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    s = Settings.from_env()
    client = ElexonClient(s)

    raw_a = client.fetch_actuals(start - timedelta(days=1), end + timedelta(days=1))
    p_from, p_to = forecast_publish_window(start, end, s)
    raw_f = client.fetch_forecasts(p_from, p_to)
    if not raw_a or not raw_f:
        raise SystemExit(f"Elexon returned no data (actuals={len(raw_a)}, forecasts={len(raw_f)}); not generating results.")
    retrieved = pd.Timestamp.now(tz="UTC")

    if a.save_raw:
        raw_dir = Path("data/raw"); raw_dir.mkdir(parents=True, exist_ok=True)
        for name, rows in (("fuelhh_wind", raw_a), ("windfor", raw_f)):
            with gzip.open(raw_dir / f"{name}_{start}_{end}.json.gz", "wt") as fh:
                json.dump(rows, fh)

    an, fn = normalize_actuals(raw_a), normalize_forecasts(raw_f)
    minutes = resolve_resolution(s.evaluation_resolution, fn.frame)
    rec = build_range_records(an.frame, fn.frame, start, end, s.cutoff_local_time, s.cutoff_days_before, minutes)
    summary, quality = summarise(rec), quality_report(rec, an, fn)

    sel = rec.dropna(subset=["selected_publish_time_utc"])
    lead_h = (sel["delivery_start_utc"] - sel["selected_publish_time_utc"]).dt.total_seconds() / 3600
    lead = {"min": float(lead_h.min()), "median": float(lead_h.median()), "max": float(lead_h.max())} if len(lead_h) else None

    verification = {
        "actual_rows": len(raw_a), "actual_fields": sorted(raw_a[0]), "actual_fuel_types": sorted({r.get("fuelType") for r in raw_a}),
        "actual_start_minutes": _minutes(raw_a), "actual_range_mw": _range(raw_a),
        "forecast_rows": len(raw_f), "forecast_fields": sorted(raw_f[0]),
        "forecast_start_minutes": _minutes(raw_f), "forecast_range_mw": _range(raw_f),
        "publish_range": [str(fn.frame["publish_time_utc"].min()), str(fn.frame["publish_time_utc"].max())],
    }
    params = {"start": a.start, "end": a.end, "retrieved_at": retrieved.isoformat(), "publish_from": str(p_from),
              "publish_to": str(p_to), "cutoff_local_time": s.cutoff_local_time.strftime("%H:%M"),
              "cutoff_days_before": s.cutoff_days_before, "resolution": describe(minutes)}

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    stem = f"results-{a.start}_{a.end}"
    (out / f"{stem}.json").write_text(json.dumps(
        {"params": params, "verification": verification, "summary": summary, "quality": quality, "lead_time_hours": lead}, indent=2))
    (out / f"{stem}.md").write_text(render_markdown(params, verification, summary, quality, lead))
    print(f"Wrote {out / (stem + '.md')} and .json")
    print(f"Resolution: {minutes} min | matched {summary['coverage']['matched_intervals']}/{summary['coverage']['expected_intervals']}")


if __name__ == "__main__":
    main()
