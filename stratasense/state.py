from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass
class State:
    # key -> last numeric value
    last: Dict[str, float]

    @staticmethod
    def from_obj(obj: Dict[str, Any]) -> "State":
        last = obj.get("last", {}) if isinstance(obj, dict) else {}
        out: Dict[str, float] = {}
        if isinstance(last, dict):
            for k, v in last.items():
                try:
                    out[str(k)] = float(v)
                except Exception:
                    continue
        return State(last=out)

    def to_obj(self) -> Dict[str, Any]:
        return {"last": self.last}


def diff_state(prev: State, cur: State) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, Tuple[float, float]]]:
    """
    returns:
      added   : key -> new
      removed : key -> old
      changed : key -> (old, new)
    """
    added: Dict[str, float] = {}
    removed: Dict[str, float] = {}
    changed: Dict[str, Tuple[float, float]] = {}

    for k, nv in cur.last.items():
        if k not in prev.last:
            added[k] = nv
        else:
            ov = prev.last[k]
            if ov != nv:
                changed[k] = (ov, nv)

    for k, ov in prev.last.items():
        if k not in cur.last:
            removed[k] = ov

    return added, removed, changed
