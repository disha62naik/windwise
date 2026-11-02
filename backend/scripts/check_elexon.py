"""Verify the Elexon assumptions from a networked machine:  python -m scripts.check_elexon 2026-01-10"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import date, timedelta

import pandas as pd

from app.clients.elexon_client import ElexonClient
from app.config import Settings
from app.services.data_loader import forecast_publish_window


def main(day: date) -> None:
    s = Settings.from_env()
    c = ElexonClient(s)
    acts = c.fetch_actuals(day, day)
    print(f"FUELHH rows: {len(acts)}  fields: {sorted(acts[0]) if acts else None}")
    print("fuelTypes:", Counter(r.get("fuelType") for r in acts))
    a_starts = pd.to_datetime([r["startTime"] for r in acts], utc=True)
    print("actual minutes-of-hour:", Counter(a_starts.minute))
    lo, hi = forecast_publish_window(day, day, s, include_later=True)
    fcs = c.fetch_forecasts(lo, hi)
    print(f"WINDFOR rows: {len(fcs)}  fields: {sorted(fcs[0]) if fcs else None}  window {lo} .. {hi}")
    f_starts = pd.to_datetime([r["startTime"] for r in fcs], utc=True)
    pubs = pd.to_datetime([r["publishTime"] for r in fcs], utc=True)
    print("forecast minutes-of-hour:", Counter(f_starts.minute))
    print("distinct publish times:", sorted({p.isoformat() for p in pubs})[:12])
    lead = (f_starts - pubs).total_seconds() / 3600
    print(f"lead time hours min/median/max: {lead.min():.1f}/{pd.Series(lead).median():.1f}/{lead.max():.1f}")
    vals = [r["generation"] for r in fcs if r.get("generation") is not None]
    print("forecast MW range:", min(vals), max(vals))


if __name__ == "__main__":
    main(date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date(2026, 1, 10) + timedelta(0))
