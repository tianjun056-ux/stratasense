from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..httpu import get_json


@dataclass(frozen=True)
class EiaSeries:
    key: str
    route: str
    facets: Dict[str, str]
    value_field: str
    label: str


def fetch_latest(api_key: str, items: List[EiaSeries]) -> Tuple[Dict[str, float], List[str]]:
    notes: List[str] = []
    out: Dict[str, float] = {}

    base = "https://api.eia.gov/v2/"

    for s in items:
        url = base + s.route
        params = {
            "api_key": api_key,
            "data[0]": s.value_field,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 5,
        }
        for k, v in (s.facets or {}).items():
            params[f"facets[{k}][]"] = v

        j = get_json(url, params=params)
        data = (j.get("response") or {}).get("data") or []

        v: Optional[float] = None
        for row in data:
            try:
                v = float(row.get(s.value_field))
                break
            except Exception:
                continue

        if v is None:
            notes.append(f"EIA:{s.route} no numeric data")
            continue

        out[s.key] = v

    return out, notes


def default_series() -> List[EiaSeries]:
    # US crude oil stocks (weekly) – structural bottleneck proxy
    return [
        EiaSeries(
            key="L2.EIA.WCESTUS1",
            route="petroleum/stoc/wstk/data/",
            facets={"series": "WCESTUS1"},
            value_field="value",
            label="US Crude Oil Stocks (weekly)",
        )
    ]
