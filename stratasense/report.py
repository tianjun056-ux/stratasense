from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from .state import State, diff_state


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Report:
    meta: Dict[str, Any]
    values: Dict[str, float]
    notes: List[str]
    changes: Dict[str, Any]


def build_report(prev: State, cur: State, meta: Dict[str, Any], notes: List[str]) -> Report:
    added, removed, changed = diff_state(prev, cur)
    has_change = bool(added or removed or changed)
    changes = {
        "has_change": has_change,
        "added": added,
        "removed": removed,
        "changed": {k: {"old": ov, "new": nv} for k, (ov, nv) in changed.items()},
    }
    return Report(meta=meta, values=cur.last, notes=notes, changes=changes)


def render_diff_md(rep: Report) -> str:
    ch = rep.changes
    lines: List[str] = []
    lines.append("# StrataSense diff")
    lines.append("")
    lines.append(f"- as_of: {rep.meta.get('as_of')}")
    lines.append(f"- run_id: {rep.meta.get('run_id')}")
    lines.append(f"- event: {rep.meta.get('event')}")
    lines.append(f"- notify: {rep.meta.get('notify')}")
    lines.append(f"- has_change: {ch.get('has_change')}")
    lines.append("")

    def section(title: str, body_lines: List[str]) -> None:
        lines.append(f"## {title}")
        if not body_lines:
            lines.append("(none)")
        else:
            lines.extend(body_lines)
        lines.append("")

    # added
    added = ch.get("added", {}) or {}
    section("added", [f"- {k}: {v}" for k, v in sorted(added.items())])

    # removed
    removed = ch.get("removed", {}) or {}
    section("removed", [f"- {k}: {v}" for k, v in sorted(removed.items())])

    # changed
    changed = ch.get("changed", {}) or {}
    changed_lines: List[str] = []
    for k in sorted(changed.keys()):
        row = changed[k] or {}
        changed_lines.append(f"- {k}: {row.get('old')} -> {row.get('new')}")
    section("changed", changed_lines)

    # notes
    if rep.notes:
        section("notes", [f"- {n}" for n in rep.notes])

    return "\n".join(lines)
