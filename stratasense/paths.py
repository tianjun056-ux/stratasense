from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def resolve_root(root_arg: Optional[str]) -> Path:
    # No Hard Path Rule: CLI > ENV > CWD
    if root_arg:
        return Path(root_arg).expanduser().resolve()
    env = os.getenv("STRATASENSE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path.cwd().resolve()


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)
