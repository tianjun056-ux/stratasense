from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 25,
) -> Dict[str, Any]:
    if params:
        q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
        url = url + ("&" if "?" in url else "?") + q

    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    return json.loads(raw)
