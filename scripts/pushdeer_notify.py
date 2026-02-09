from __future__ import annotations

import os
import sys
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple


def _read_json(p: Path) -> Dict[str, Any]:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _resolve_root() -> Path:
    # No Hard Path Rule: ENV > CWD (workflow 中通常就是 repo root)
    env = (os.getenv("STRATASENSE_ROOT") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def _should_notify(report: Dict[str, Any]) -> Tuple[bool, str]:
    meta = report.get("meta") or {}
    changes = report.get("changes") or {}
    notify_flag = bool(meta.get("notify"))
    has_change = bool(changes.get("has_change"))

    # 规则：
    # - 手动触发（notify=true） => 必推送
    # - 否则只有 has_change => 推送
    if notify_flag:
        return True, "manual_or_forced"
    if has_change:
        return True, "changed"
    return False, "no_change"


def _pushdeer_send(key: str, text: str, desp: str) -> None:
    # PushDeer API: https://api2.pushdeer.com/message/push
    url = "https://api2.pushdeer.com/message/push"
    payload = {"pushkey": key, "text": text, "desp": desp, "type": "markdown"}
    data = urllib.parse.urlencode(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read().decode("utf-8", errors="replace")

    # 尽量解析返回，失败也不抛太多
    try:
        j = json.loads(raw)
    except Exception:
        raise RuntimeError("PushDeer response not json")

    code = j.get("code")
    if code not in (0, "0"):
        raise RuntimeError(f"PushDeer code={code} raw={raw[:200]}")


def main() -> int:
    root = _resolve_root()
    latest = root / "outputs" / "latest"
    report_path = latest / "report.json"
    diff_path = latest / "diff.md"

    report = _read_json(report_path)
    if not report:
        print(f"WARN: missing report.json at {report_path.as_posix()}")
        return 0

    ok, reason = _should_notify(report)
    if not ok:
        # 默认沉默：不该推送就不推送，但给 CI 一行可审计信息
        print(f"OK: skip notify ({reason})")
        return 0

    key = (os.getenv("PUSHDEER_KEY") or "").strip()
    if not key:
        print("WARN: PUSHDEER_KEY missing, cannot notify")
        return 0

    meta = report.get("meta") or {}
    as_of = meta.get("as_of")
    event = meta.get("event")
    has_change = (report.get("changes") or {}).get("has_change")

    title = f"StrataSense | {reason} | change={has_change}"
    desp_lines = []
    desp_lines.append(f"- as_of: {as_of}")
    desp_lines.append(f"- event: {event}")
    desp_lines.append("")
    # 附上 diff.md（如果存在）
    if diff_path.exists():
        try:
            desp_lines.append(diff_path.read_text(encoding="utf-8"))
        except Exception:
            desp_lines.append("(WARN: diff.md read failed)")
    else:
        desp_lines.append("(no diff.md)")

    try:
        _pushdeer_send(key, title, "\n".join(desp_lines))
        print("OK: notified via PushDeer")
    except Exception as e:
        print(f"WARN: notify failed: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
