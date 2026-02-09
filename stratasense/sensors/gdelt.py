from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

from ..httpu import get_json


@dataclass(frozen=True)
class GdeltQuery:
    key: str
    query: str
    label: str


def _fmt(d: datetime) -> str:
    return d.strftime("%Y%m%d%H%M%S")


def fetch_counts(items: List[GdeltQuery]) -> Tuple[Dict[str, float], List[str]]:
    """
    Shadow signal only:
    compare last 7d vs previous 7d article counts (ratio).
    """
    notes: List[str] = []
    out: Dict[str, float] = {}

    base = "https://api.gdeltproject.org/api/v2/doc/doc"
    now = datetime.now(timezone.utc)
    t1 = now
    t0 = now - timedelta(days=7)
    t_1 = now - timedelta(days=14)

    for it in items:
        j1 = get_json(
            base,
            {
                "query": it.query,
                "mode": "ArtList",
                "format": "json",
                "maxrecords": 1,
                "startdatetime": _fmt(t0),
                "enddatetime": _fmt(t1),
            },
        )
        j0 = get_json(
            base,
            {
                "query": it.query,
                "mode": "ArtList",
                "format": "json",
                "maxrecords": 1,
                "startdatetime": _fmt(t_1),
                "enddatetime": _fmt(t0),
            },
        )

        c1 = float(len(j1.get("articles", []) or []))
        c0 = float(len(j0.get("articles", []) or []))

        out[it.key] = (c1 / c0) if c0 > 0 else c1

    return out, notes


def default_queries() -> List[GdeltQuery]:
    # Low weight, anomaly hint only
    return [
        GdeltQuery(
            "L1.GDELT.CONFLICT_RATIO",
            "conflict OR war OR military",
            "Global conflict news ratio (7d/prev7d)",
        ),
        GdeltQuery(
            "L1.GDELT.PROTEST_RATIO",
            "protest OR strike OR riot",
            "Global protest news ratio (7d/prev7d)",
        ),
    ]
