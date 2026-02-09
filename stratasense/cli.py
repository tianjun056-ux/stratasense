import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

VERSION = "0.1"


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _run_id() -> str:
    return datetime.now().strftime("run_%Y%m%d_%H%M%S")


def _resolve_root(root_arg: str | None) -> Path:
    # No Hard Path Rule：CLI > ENV > CWD
    if root_arg:
        return Path(root_arg).expanduser()
    env = os.getenv("STRATASENSE_ROOT", "").strip()
    if env:
        return Path(env).expanduser()
    return Path.cwd()


def _sources_v01() -> Dict[str, List[dict]]:
    return {
        "L1": [
            {"name": "The Economist", "kind": "media", "note": "只看 Leaders/Briefing/Special Report"},
            {"name": "Financial Times", "kind": "media", "note": "优先 Big Read，避免 breaking news"},
            {"name": "CFR (Council on Foreign Relations)", "kind": "think_tank", "note": "Backgrounders 作为结构校准"},
        ],
        "L2": [
            {"name": "IEA (International Energy Agency)", "kind": "org", "note": "能源约束：WEO/月报摘要"},
            {"name": "USGS (Mineral Commodity Summaries)", "kind": "gov", "note": "矿产供给集中度/产地分布"},
            {"name": "ASML Updates", "kind": "company", "note": "算力瓶颈：技术/产能/限制"},
        ],
        "L3": [
            {"name": "FRED", "kind": "dataset", "note": "宏观数据验证器"},
            {"name": "BlackRock Investment Outlook", "kind": "institution", "note": "大资金可执行世界观"},
            {"name": "OECD / MSCI", "kind": "institution", "note": "跨地区/指数层对照"},
        ],
        "L4": [
            {"name": "Bloomberg Markets / Odd Lots", "kind": "media", "note": "情绪温度计"},
            {"name": "X/Twitter (严格白名单)", "kind": "social", "note": "只关注数据派"},
            {"name": "Reddit (r/investing 等)", "kind": "social", "note": "反向指标"},
        ],
        "L5": [
            {"name": "Execution (外部系统)", "kind": "boundary", "note": "不负责交易执行"},
        ],
    }


def _render_md(report: dict) -> str:
    lines: List[str] = []
    lines.append(f"# StrataSense 扫描报告（v{report['version']}）")
    lines.append("")
    lines.append(f"- run_id: `{report['run_id']}`")
    lines.append(f"- ts_utc: `{report['ts_utc']}`")
    lines.append(f"- root: `{report['root']}`")
    lines.append("")
    lines.append("## 分层信息源清单")
    lines.append("")
    for layer, items in report["sources"].items():
        lines.append(f"### {layer}")
        for s in items:
            lines.append(f"- **{s['name']}**（{s['kind']}）：{s['note']}")
        lines.append("")
    return "\n".join(lines)


def _key(s: dict) -> Tuple[str, str]:
    # 稳定键：name + kind
    return (s.get("name", ""), s.get("kind", ""))


def _diff_sources(prev: Dict[str, List[dict]] | None,
                  curr: Dict[str, List[dict]]) -> Dict[str, dict]:
    diff: Dict[str, dict] = {}
    prev = prev or {}
    for layer, curr_items in curr.items():
        prev_items = prev.get(layer, [])
        prev_set = {_key(s) for s in prev_items}
        curr_set = {_key(s) for s in curr_items}
        added = [s for s in curr_items if _key(s) not in prev_set]
        removed = [s for s in prev_items if _key(s) not in curr_set]
        unchanged = [s for s in curr_items if _key(s) in prev_set]
        diff[layer] = {
            "added": added,
            "removed": removed,
            "unchanged": unchanged,
        }
    return diff


def _render_diff_md(diff: Dict[str, dict]) -> str:
    lines: List[str] = []
    lines.append("# StrataSense 结构差分（diff）")
    lines.append("")
    for layer, d in diff.items():
        lines.append(f"## {layer}")
        for k in ("added", "removed", "unchanged"):
            items = d.get(k, [])
            if not items:
                continue
            lines.append(f"### {k}")
            for s in items:
                lines.append(f"- **{s['name']}**（{s['kind']}）")
            lines.append("")
    return "\n".join(lines)


def _write_outputs(root: Path, report: dict, diff: Dict[str, dict] | None) -> None:
    out_root = root / "outputs"
    run_dir = out_root / "runs" / report["run_id"]
    latest_dir = out_root / "latest"
    run_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    # report
    json_bytes = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
    md_text = _render_md(report)
    (run_dir / "report.json").write_bytes(json_bytes)
    (run_dir / "report.md").write_text(md_text, encoding="utf-8")
    (latest_dir / "report.json").write_bytes(json_bytes)
    (latest_dir / "report.md").write_text(md_text, encoding="utf-8")

    # diff（如果存在）
    if diff is not None:
        diff_json = json.dumps(diff, ensure_ascii=False, indent=2).encode("utf-8")
        diff_md = _render_diff_md(diff)
        (run_dir / "diff.json").write_bytes(diff_json)
        (run_dir / "diff.md").write_text(diff_md, encoding="utf-8")
        (latest_dir / "diff.json").write_bytes(diff_json)
        (latest_dir / "diff.md").write_text(diff_md, encoding="utf-8")


def _load_prev_sources(latest_report: Path) -> Dict[str, List[dict]] | None:
    if not latest_report.exists():
        return None
    try:
        data = json.loads(latest_report.read_text(encoding="utf-8"))
        return data.get("sources")
    except Exception:
        return None


def cmd_scan(root_arg: str | None) -> int:
    root = _resolve_root(root_arg).resolve()
    latest_report = root / "outputs" / "latest" / "report.json"
    prev_sources = _load_prev_sources(latest_report)

    report = {
        "version": VERSION,
        "run_id": _run_id(),
        "ts_utc": _now_iso_utc(),
        "root": str(root),
        "sources": _sources_v01(),
    }

    diff = _diff_sources(prev_sources, report["sources"]) if prev_sources else None
    _write_outputs(root, report, diff)

    # 最少输出（CI 友好）
    print(f"OK: {(root / 'outputs' / 'latest' / 'report.json').as_posix()}")
    if diff is not None:
        print(f"OK: {(root / 'outputs' / 'latest' / 'diff.md').as_posix()}")
    return 0


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="stratasense", add_help=True)
    p.add_argument("--root", default=None, help="项目根目录（可选；默认用 ENV/CWD）")
    p.add_argument("--version", action="store_true", help="显示版本信息")
    args = p.parse_args(argv)

    if args.version:
        print(f"StrataSense v{VERSION}")
        return 0

    # 默认行为：scan（含 diff）
    return cmd_scan(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
