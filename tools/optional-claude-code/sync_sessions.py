"""
sync_sessions.py — 归档+转换 Claude Code 会话记录

功能：
1. 扫描 ~/.claude/projects/ 下所有 .jsonl 会话
2. 通过读每个jsonl第一行的 cwd 字段自动识别项目
3. 无损归档 jsonl 到 raw/sessions/{项目}/{YYYY-MM}/{YYYY-MM-DD}_{sessionid[:8]}.jsonl
4. 生成人类可读 markdown transcript 到 raw/transcripts/{项目}/{YYYY-MM}/*.md
5. 只处理新文件（按 mtime 增量），已归档的跳过

用法：
    python sync_sessions.py           # 增量同步
    python sync_sessions.py --full    # 强制全量重跑
    python sync_sessions.py --stats   # 只看统计不做事
"""

import json
import os
import shutil
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Windows 终端默认 GBK，强制 stdout 为 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import _config

PROJECTS_DIR = _config.claude_projects_dir()
WIKI_ROOT = _config.wiki_root()
SESSIONS_DIR = WIKI_ROOT / "raw" / "sessions"
TRANSCRIPTS_DIR = WIKI_ROOT / "raw" / "transcripts"

# 可选：用户可在 config.json 加 "projects_parent_dir" 字段（如 "F:/项目开发"）
# 让脚本从 cwd 提取子目录名作为项目名。没配就用 cwd 最后一段。
_CFG = _config.load_config()
_PROJECTS_PARENT = _CFG.get("projects_parent_dir", "")


def project_shortname(cwd: str | None) -> str:
    """从 cwd 反推一个可读的项目短名。"""
    if not cwd:
        return "unknown"
    cwd = cwd.replace("\\", "/").rstrip("/")
    # 优先用配置的 projects_parent_dir 作前缀匹配
    if _PROJECTS_PARENT:
        normalized_parent = _PROJECTS_PARENT.replace("\\", "/").rstrip("/") + "/"
        if normalized_parent.lower() in cwd.lower():
            # 找到前缀后取后面的部分
            idx = cwd.lower().index(normalized_parent.lower())
            rest = cwd[idx + len(normalized_parent):]
            return rest.replace("/", "_") if rest else "unknown"
    # 退化：Home / Desktop 特判
    if cwd.lower().endswith(("/administrator", "/users")):
        return "home"
    if "/Desktop/" in cwd or cwd.endswith("/Desktop"):
        tail = cwd.split("/Desktop", 1)[1].strip("/")
        return f"desktop_{tail}" if tail else "desktop"
    # 退化：用最后两段
    parts = cwd.split("/")
    return "_".join(parts[-2:]) if len(parts) >= 2 else parts[-1]


def inspect_jsonl(jsonl_path: Path):
    """读jsonl提取元数据：cwd, session_id, 首末时间, 消息统计。"""
    meta = {
        "cwd": None,
        "session_id": None,
        "first_ts": None,
        "last_ts": None,
        "user_msgs": 0,
        "assistant_msgs": 0,
        "tool_uses": 0,
        "lines": 0,
    }
    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            meta["lines"] += 1
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not meta["cwd"] and o.get("cwd"):
                meta["cwd"] = o["cwd"]
            if not meta["session_id"] and o.get("sessionId"):
                meta["session_id"] = o["sessionId"]
            ts = o.get("timestamp")
            if ts:
                if not meta["first_ts"]:
                    meta["first_ts"] = ts
                meta["last_ts"] = ts
            t = o.get("type")
            if t == "user":
                meta["user_msgs"] += 1
            elif t == "assistant":
                meta["assistant_msgs"] += 1
                msg = o.get("message", {})
                if isinstance(msg, dict):
                    for item in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            meta["tool_uses"] += 1
    return meta


def extract_content_text(content) -> str:
    """从 message.content 提取纯文本（忽略tool call/result的细节）。"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            t = item.get("type")
            if t == "text":
                parts.append(item.get("text", ""))
            elif t == "tool_use":
                name = item.get("name", "?")
                inp = item.get("input", {})
                # 简化 tool args
                arg_preview = json.dumps(inp, ensure_ascii=False)[:150]
                parts.append(f"[🛠 {name}({arg_preview}...)]")
            elif t == "tool_result":
                res = item.get("content", "")
                if isinstance(res, list):
                    res = " ".join(
                        i.get("text", "") for i in res if isinstance(i, dict) and i.get("type") == "text"
                    )
                res_str = str(res)[:200]
                parts.append(f"[📤 tool_result: {res_str}...]")
            elif t == "thinking":
                parts.append(f"[💭 thinking: {item.get('thinking', '')[:200]}...]")
        return "\n".join(parts)
    return str(content)


def jsonl_to_markdown(jsonl_path: Path, meta: dict) -> str:
    """把jsonl转成可读markdown transcript。"""
    lines = [
        f"# Claude Code Session Transcript",
        "",
        f"- **Session ID**: `{meta.get('session_id', '?')}`",
        f"- **cwd**: `{meta.get('cwd', '?')}`",
        f"- **时间**: {meta.get('first_ts', '?')} → {meta.get('last_ts', '?')}",
        f"- **消息数**: user={meta['user_msgs']} / assistant={meta['assistant_msgs']} / tool_use={meta['tool_uses']}",
        "",
        "---",
        "",
    ]
    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = o.get("type")
            if t == "user":
                msg = o.get("message", {})
                content = msg.get("content") if isinstance(msg, dict) else msg
                text = extract_content_text(content)
                # 跳过纯tool_result（那是user发来的工具结果，不是真user发言）
                if isinstance(content, list) and all(
                    isinstance(i, dict) and i.get("type") == "tool_result" for i in content
                ):
                    continue
                if text.strip():
                    lines.append(f"### 👤 User\n\n{text}\n")
            elif t == "assistant":
                msg = o.get("message", {})
                content = msg.get("content") if isinstance(msg, dict) else msg
                text = extract_content_text(content)
                if text.strip():
                    lines.append(f"### 🤖 AI\n\n{text}\n")
            elif t == "summary":
                summary = o.get("summary", "")
                lines.append(f"### 📋 Summary\n\n{summary}\n")
    return "\n".join(lines)


def sync(full: bool = False, stats_only: bool = False):
    if not PROJECTS_DIR.exists():
        print(f"❌ {PROJECTS_DIR} 不存在")
        return

    all_proj_dirs = sorted([d for d in PROJECTS_DIR.iterdir() if d.is_dir()])
    print(f"🔍 扫到 {len(all_proj_dirs)} 个项目目录\n")

    summary_by_proj = {}
    new_count = 0
    skipped = 0

    for proj_dir in all_proj_dirs:
        jsonls = sorted(proj_dir.glob("*.jsonl"))
        if not jsonls:
            continue

        # 读第一个jsonl推断项目名（所有session通常同cwd）
        first_meta = inspect_jsonl(jsonls[0])
        shortname = project_shortname(first_meta.get("cwd"))

        summary_by_proj[shortname] = {
            "encoded_dir": proj_dir.name,
            "cwd": first_meta.get("cwd"),
            "sessions": len(jsonls),
            "total_size_mb": sum(j.stat().st_size for j in jsonls) / 1024 / 1024,
        }

        if stats_only:
            continue

        for jsonl in jsonls:
            meta = inspect_jsonl(jsonl)
            sid = meta.get("session_id") or jsonl.stem
            ts = meta.get("first_ts") or datetime.fromtimestamp(jsonl.stat().st_mtime).isoformat()
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.fromtimestamp(jsonl.stat().st_mtime)
            ym = dt.strftime("%Y-%m")
            ymd = dt.strftime("%Y-%m-%d")
            sid_short = sid[:8]

            # 归档路径
            archive_dir = SESSIONS_DIR / shortname / ym
            archive_path = archive_dir / f"{ymd}_{sid_short}.jsonl"
            transcript_dir = TRANSCRIPTS_DIR / shortname / ym
            transcript_path = transcript_dir / f"{ymd}_{sid_short}.md"

            # 增量：已归档且源文件未变则跳过
            if not full and archive_path.exists():
                src_mtime = jsonl.stat().st_mtime
                dst_mtime = archive_path.stat().st_mtime
                if src_mtime <= dst_mtime:
                    skipped += 1
                    continue

            archive_dir.mkdir(parents=True, exist_ok=True)
            transcript_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(jsonl, archive_path)
            transcript_path.write_text(jsonl_to_markdown(jsonl, meta), encoding="utf-8")
            new_count += 1

    print("📊 项目统计\n" + "=" * 60)
    for name, info in sorted(summary_by_proj.items(), key=lambda x: -x[1]["sessions"]):
        print(
            f"  {name:35s}  sessions={info['sessions']:4d}  size={info['total_size_mb']:6.1f}MB  cwd={info['cwd']}"
        )
    print()

    if not stats_only:
        print(f"✅ 归档: {new_count} 个新/更新 session, {skipped} 个跳过")
        print(f"📁 归档目录: {SESSIONS_DIR}")
        print(f"📝 Transcript 目录: {TRANSCRIPTS_DIR}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="强制全量重跑")
    ap.add_argument("--stats", action="store_true", help="只看统计不做事")
    args = ap.parse_args()
    sync(full=args.full, stats_only=args.stats)
