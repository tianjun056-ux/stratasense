import argparse
from pathlib import Path

FILES_TEXT = {
    "README.md": "",
    "docs/00_工程规范.md": "",
    "docs/01_L1_世界结构层.md": "",
    "docs/02_L2_资源与瓶颈层.md": "",
    "docs/03_L3_资产映射层.md": "",
    "docs/04_L4_行为与情绪层.md": "",
    "docs/05_L5_执行层.md": "",
    "stratasense/__init__.py": "",
    "stratasense/__main__.py": """\
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
""",
    "stratasense/cli.py": """\
import argparse

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="stratasense", add_help=True)
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("version", help="显示版本信息（占位）")
    sub.add_parser("scan", help="执行一次分层扫描（占位）")

    args = p.parse_args(argv)

    # Default Silence：默认不输出；只有显式命令才输出最少信息
    if args.cmd == "version":
        print("StrataSense v0.1")
        return 0
    if args.cmd == "scan":
        print("TODO: scan")
        return 0

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
""",
}

DIRS = [
    "docs",
    "stratasense",
]

def _safe_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="项目根目录（建议传入你的目标路径）")
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    for rel, text in FILES_TEXT.items():
        _safe_write(root / rel, text)

    # 默认沉默：不打印路径、不打印列表
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
