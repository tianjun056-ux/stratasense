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


def _changed_layers(diff: Dict[str, dict]) -> List[str]:
    layers: List[str] = []
    for layer, d in diff.items():
        if d.get("added") or d.get("removed"):
            layers.append(layer)
    return layers


def _pushdeer(key: str, text: str) -> None:
    url = f"https://api2.pushdeer.com/message/push?pushkey={key}"
    data = json.dumps({"text": text, "type": "text"}).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        r.read()


def main() -> int:
    key = os.getenv("PUSHDEER_KEY", "").strip()
    if not key:
        return 0

    # GitHub Actions 会注入这个变量
    event_name = os.getenv("GITHUB_EVENT_NAME", "").strip()

    diff_path = Path("outputs") / "latest" / "diff.json"
    diff = _load_diff(diff_path)

    # 1) 手动触发：一定通知（健康确认）
    if event_name == "workflow_dispatch":
        if diff:
            layers = _changed_layers(diff)
            if layers:
                msg = f"StrataSense（手动）：结构变化 {', '.join(layers)}"
            else:
                msg = "StrataSense（手动）：系统正常，结构无变化"
        else:
            msg = "StrataSense（手动）：系统运行完成（无 diff 文件）"

        _pushdeer(key, msg)
        return 0

    # 2) 定时触发：只有结构变化才通知
    if not diff:
        return 0

    layers = _changed_layers(diff)
    if not layers:
        return 0

    msg = f"StrataSense：结构发生变化（{', '.join(layers)}）"
    _pushdeer(key, msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
