#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PushDeer notification (human-friendly CN)

- Reads outputs/latest/report.json and outputs/latest/diff.md
- Generates a short Chinese summary
- Sends via PushDeer
"""

import os
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATEST = ROOT / "outputs" / "latest"
REPORT_JSON = LATEST / "report.json"
DIFF_MD = LATEST / "diff.md"

PUSHDEER_API = "https://api2.pushdeer.com/message/push"


def _read_text(p: Path) -> str:
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _read_json(p: Path) -> dict:
    if not p.exists():
        return {}
    try:
        return json.loads(_read_text(p))
    except Exception:
        return {}


def _parse_diff_sections(diff_md: str) -> dict:
    """
    Parse diff.md roughly:
    expects headings: added / removed / changed / notes (optional)
    """
    lines = diff_md.splitlines()
    sections = {"added": [], "removed": [], "changed": [], "notes": []}
    cur = None
    for ln in lines:
        s = ln.strip()
        if s.lower() in sections:
            cur = s.lower()
            continue
        if cur is None:
            continue
        # bullet items like "- xxx" or "• xxx"
        if s.startswith(("-", "•", "*")):
            item = s.lstrip("-•*").strip()
            if item:
                sections[cur].append(item)
        # plain "(none)" style
        if s.lower() == "(none)":
            # do nothing
            pass
    return sections


def _summarize_cn(report: dict, diff_sections: dict) -> tuple[str, str]:
    """
    Returns (title, body) in Chinese.
    """
    meta = report.get("meta", {}) if isinstance(report, dict) else {}
    as_of = meta.get("as_of") or report.get("as_of") or ""
    event = meta.get("event") or report.get("event") or ""
    has_change = meta.get("has_change")
    if has_change is None:
        has_change = report.get("has_change")

    # ★ 人话规则兜底：diff 全空 = 无变化
    if has_change is None:
        if (
            len(diff_sections.get("added", [])) == 0
            and len(diff_sections.get("removed", [])) == 0
            and len(diff_sections.get("changed", [])) == 0
        ):
            has_change = False


    # change counts
    a = len(diff_sections.get("added", []))
    r = len(diff_sections.get("removed", []))
    c = len(diff_sections.get("changed", []))
    notes = diff_sections.get("notes", [])

    # Title
    if has_change is True:
        title = f"StrataSense：发现变化（+{a}/-{r}/~{c}）"
    elif has_change is False:
        title = "StrataSense：无变化"
    else:
        title = "StrataSense：扫描完成"

    # Body (human)
    parts = []
    if as_of:
        parts.append(f"时间：{as_of}")
    if event:
        parts.append(f"触发：{event}")

    # Main conclusion
    if has_change is True:
        parts.append(f"结果：有变化（新增 {a}，移除 {r}，变更 {c}）")
        # include a few items for readability
        def take(xs, n=5):
            return xs[:n] if xs else []

        if a:
            parts.append("新增： " + "；".join(take(diff_sections["added"])))
        if r:
            parts.append("移除： " + "；".join(take(diff_sections["removed"])))
        if c:
            parts.append("变更： " + "；".join(take(diff_sections["changed"])))
    elif has_change is False:
        parts.append("结果：没有检测到变化（本次只是例行扫描）")
    else:
        parts.append("结果：扫描完成（未提供 has_change 字段）")

    # Notes / warnings (keep short)
    if notes:
        # compress typical ERR lines
        show = notes[:5]
        parts.append("备注： " + "；".join(show))

    body = "\n".join(parts)
    return title, body


def _pushdeer_send(key: str, title: str, body: str) -> None:
    data = {
        "pushkey": key,
        "text": title,
        "desp": body,
        "type": "markdown",
    }
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(PUSHDEER_API, data=encoded, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    # minimal validation
    if '"success"' not in raw and '"code":0' not in raw:
        raise RuntimeError(f"PushDeer response not OK: {raw[:200]}")


def main() -> int:
    key = os.environ.get("PUSHDEER_KEY", "").strip()
    if not key:
        print("WARN: PUSHDEER_KEY missing, cannot notify")
        return 0

    report = _read_json(REPORT_JSON)
    diff_md = _read_text(DIFF_MD)
    diff_sections = _parse_diff_sections(diff_md) if diff_md else {"added": [], "removed": [], "changed": [], "notes": []}

    title, body = _summarize_cn(report, diff_sections)

    # avoid too long (PushDeer sometimes truncates)
    if len(body) > 3500:
        body = body[:3500] + "\n\n（内容过长已截断）"

    _pushdeer_send(key, title, body)
    print("OK: notified via PushDeer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
