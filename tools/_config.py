"""
_config.py — 所有脚本共用的配置加载器

读 config.json（在 tools/ 同级），返回绝对路径 Path。
setup.ps1 会生成 config.json。
"""

import json
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).resolve().parent
_CONFIG_PATH = _TOOLS_DIR / "config.json"


def load_config() -> dict:
    if not _CONFIG_PATH.exists():
        print(f"❌ 找不到 {_CONFIG_PATH}。请先跑 setup.ps1。", file=sys.stderr)
        sys.exit(1)
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def wiki_root() -> Path:
    """返回 wiki 根目录（包含 wiki/ raw/ tools/ 的那个）"""
    cfg = load_config()
    return Path(cfg["wiki_root"])


def claude_projects_dir() -> Path:
    """Claude Code 的 session jsonl 所在根目录"""
    cfg = load_config()
    p = cfg.get("claude_projects_dir")
    if p:
        return Path(p)
    # 默认 ~/.claude/projects
    import os
    return Path(os.path.expanduser("~/.claude/projects"))
