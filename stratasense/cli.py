from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .paths import ensure_dir, resolve_root
from .iojson import read_json, write_json, write_text
from .state import State
from .report import build_report, render_diff_md, now_iso
from .sensors.fred import default_series as fred_defaults, fetch_latest as fred_fetch
from .sensors.eia import default_series as eia_defaults, fetch_latest as eia_fetch
from .sensors.gdelt import default_queries as gdelt_defaults, fetch_counts as gdelt_fetch


def _run_id() -> str:
    return datetime.utcnow().strftime("run_%Y%m%d_%H%M%S")


def _load_prev_state(latest_dir: Path) -> State:
    state_path = latest_dir / "state.json"
    if state_path.exists():
        return State.from_obj(read_json(state_path))
    # 兼容旧版：如果没有 state.json，但有 report.json，就从 report.values 构造
    rep = read_json(latest_dir / "report.json")
    vals = rep.get("values", {}) if isinstance(rep, dict) else {}
    return State.from_obj({"last": vals})


def _collect_values() -> Tuple[Dict[str, float], List[str]]:
    notes: List[str] = []
    values: Dict[str, float] = {}

    fred_key = (os.getenv("FRED_API_KEY") or "").strip()
    eia_key = (os.getenv("EIA_API_KEY") or "").strip()

    if not fred_key:
        notes.append("ERR: missing FRED_API_KEY")
    else:
        v, n = fred_fetch(fred_key, fred_defaults())
        values.update(v)
        notes.extend(n)

    if not eia_key:
        notes.append("ERR: missing EIA_API_KEY")
    else:
        v, n = eia_fetch(eia_key, eia_defaults())
        values.update(v)
        notes.extend(n)

    # GDELT：无 key（失败也不阻塞）
    try:
        v, n = gdelt_fetch(gdelt_defaults())
        values.update(v)
        notes.extend(n)
    except Exception as e:
        notes.append(f"GDELT_ERR: {type(e).__name__}")

    return values, notes


def cmd_scan(args: argparse.Namespace) -> int:
    root = resolve_root(args.root)
    out_root = root / "outputs"
    latest = out_root / "latest"
    runs = out_root / "runs" / _run_id()
    ensure_dir(latest)
    ensure_dir(runs)

    prev = _load_prev_state(latest)
    values, notes = _collect_values()
    cur = State(last=values)

    gh_event = (os.getenv("GITHUB_EVENT_NAME") or "").strip()
    notify = bool(args.force_notify) or (gh_event == "workflow_dispatch")

    meta = {
        "as_of": now_iso(),
        "run_id": runs.name,
        "event": gh_event or "local",
        "notify": notify,
    }

    rep = build_report(prev, cur, meta, notes)
    diff_md = render_diff_md(rep)

    # 写 runs（归档）
    write_json(runs / "state.json", cur.to_obj())
    write_json(runs / "report.json", {"meta": rep.meta, "values": rep.values, "notes": rep.notes, "changes": rep.changes})
    write_text(runs / "diff.md", diff_md)

    # 写 latest（指针）
    write_json(latest / "state.json", cur.to_obj())
    write_json(latest / "report.json", {"meta": rep.meta, "values": rep.values, "notes": rep.notes, "changes": rep.changes})
    write_text(latest / "diff.md", diff_md)

    # 默认沉默：只输出必要 OK
    print(f"OK: {str((latest / 'report.json').as_posix())}")
    print(f"OK: {str((latest / 'diff.md').as_posix())}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="stratasense", add_help=True)
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("scan", help="run weekly scan (FRED+EIA+GDELT) -> outputs/")
    s.add_argument("--root", default=None, help="root dir (CLI > ENV STRATASENSE_ROOT > CWD)")
    s.add_argument("--force-notify", action="store_true", help="manual trigger must notify (flag only recorded)")
    s.set_defaults(func=cmd_scan)

    return p


def main(argv: List[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)

    if not getattr(args, "cmd", None):
        # 默认行为：等价于 scan（保持单入口好用）
        args = p.parse_args(["scan"])
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
