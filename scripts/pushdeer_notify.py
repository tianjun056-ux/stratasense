import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List


def _load_diff(path: Path) -> Dict[str, dict] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _has_real_change(diff: Dict[str, dict]) -> List[str]:
    """
    只要任一层存在 added / removed 即视为“结构变化”
    """
    changed_layers: List[str] = []
    for layer, d in diff.items():
        if d.get("added") or d.get("removed"):
            changed_layers.append(layer)
    return changed_layers


def _pushdeer_notify(key: str, text: str) -> None:
    url = f"https://api2.pushdeer.com/message/push?pushkey={key}"
    data = json.dumps({
        "text": text,
        "type": "text"
    }).encode("utf-8")

    req = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def main() -> int:
    key = os.getenv("PUSHDEER_KEY", "").strip()
    if not key:
        # 没有 key，直接沉默退出（避免误报）
        return 0

    diff_path = Path("outputs") / "latest" / "diff.json"
    diff = _load_diff(diff_path)
    if not diff:
        return 0

    changed_layers = _has_real_change(diff)
    if not changed_layers:
        return 0

    layers = ", ".join(changed_layers)
    msg = f"StrataSense：结构发生变化（{layers}），请查看 diff"

    _pushdeer_notify(key, msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
