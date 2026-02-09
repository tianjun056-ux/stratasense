from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from ..httpu import get_json


@dataclass(frozen=True)
class FredSeries:
    key: str
    series_id: str
    label: str


def _iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def fetch_latest(api_key: str, items: List[FredSeries]) -> Tuple[Dict[str, float], List[str]]:
    """
    Pull latest numeric observation within recent window.
    Output is STRUCTURAL values, not signals.
    """
    notes: List[str] = []
    out: Dict[str, float] = {}

    base = "https://api.stlouisfed.org/fred/series/observations"
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=21)

    for s in items:
        j = get_json(
            base,
            {
                "api_key": api_key,
                "file_type": "json",
                "series_id": s.series_id,
                "observation_start": _iso(start),
                "sort_order": "desc",
                "limit": 10,
            },
        )
        obs = j.get("observations", [])
        v: Optional[float] = None
        for o in obs:
            try:
                v = float(o.get("value"))
                break
            except Exception:
                continue

        if v is None:
            notes.append(f"FRED:{s.series_id} no numeric observation")
            continue

        out[s.key] = v

    return out, notes


def default_series() -> List[FredSeries]:
    # Minimal, stable, structural
    return [
        FredSeries("L3.FRED.DGS10", "DGS10", "US 10Y Treasury"),
        FredSeries("L3.FRED.DGS2", "DGS2", "US 2Y Treasury"),
        FredSeries("L3.FRED.T10Y2Y", "T10Y2Y", "10Y-2Y Spread"),
    ]
