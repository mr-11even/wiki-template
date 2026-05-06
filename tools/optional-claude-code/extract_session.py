"""
extract_session.py — SessionEnd hook 的后台处理器

被 extract_session.ps1 调用。职责：
1. 收 session_id + cwd 作为参数
2. 找到对应的 jsonl（~/.claude/projects/{encoded_cwd}/{session_id}.jsonl）
3. 读 jsonl，提取最后 N 条 user/assistant 消息作为"会话尾巴"
4. 用 claude CLI subprocess 让 Claude 提炼这段对话的要点
5. 追加到 {wiki_root}/raw/daily-logs/YYYY-MM-DD.md

设计原则：
- 全程异步（被 ps1 Start-Process 后台调用）
- 失败静默（写错误日志，不打扰用户）
- 仅处理"有实质对话"的 session（少于 5 条 user 消息直接跳过）
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import _config

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WIKI_ROOT = _config.wiki_root()
DAILY_LOGS_DIR = WIKI_ROOT / "raw" / "daily-logs"
ERROR_LOG = WIKI_ROOT / "tools" / "logs" / "extract_session_errors.log"
PROJECTS_ROOT = _config.claude_projects_dir()

MIN_USER_MESSAGES = 5  # 少于这个数视为"没什么要提炼的"

EXTRACT_PROMPT = """你是 AI，正在对一次 Claude Code 会话结束时做记忆归档。

以下是这次会话的**完整对话摘要**（user/assistant 交替，工具调用已简化）。
请按下面格式提炼一段 300-500 字的会话摘要，用中文：

---
### {YYYY-MM-DD HH:MM} · {一句话主题}（{项目名}）
**做了什么**：1-3 个bullet，重点结果（不是过程）
**关键决策**：如有，列出来；没有就不写此节
**待办/遗留**：如有，1-3 条；没有就不写此节
**用户 的洞察 / 独特表达**：如有特别值得留存的原话或判断；没有不写
---

不要写工具调用流水账。不要讨好、不要废话。用户 要求简练。
如果这次会话没有任何值得归档的价值（纯 debug / 失败重试 / 闲聊），直接回复：`SKIP: <一行理由>`。
"""


def log_error(msg: str):
    ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")


def encode_cwd(cwd: str) -> str:
    """把 cwd 转成 Claude Code projects 目录下的编码名。
    规则：替换 [:/\\] 和非 ASCII 字符为 -"""
    import re
    # Claude Code 实际的编码：/\: → -，中文/其他非 ASCII → -
    result = re.sub(r"[\\/:]|[^\x00-\x7f]", "-", cwd)
    # 前导可能不需要特殊处理，直接返回
    return result


def find_jsonl(session_id: str, cwd: str) -> Path | None:
    """根据 cwd + session_id 找 jsonl 文件"""
    # 先用 cwd 编码定位目录
    encoded = encode_cwd(cwd)
    candidate = PROJECTS_ROOT / encoded / f"{session_id}.jsonl"
    if candidate.exists():
        return candidate
    # 回退：遍历所有 project 目录找 session_id
    for proj_dir in PROJECTS_ROOT.iterdir():
        if not proj_dir.is_dir():
            continue
        candidate = proj_dir / f"{session_id}.jsonl"
        if candidate.exists():
            return candidate
    return None


def extract_messages(jsonl_path: Path) -> tuple[str, str, int, str]:
    """返回 (对话文本, cwd, user消息数, 首末时间)"""
    lines_out = []
    user_count = 0
    cwd = ""
    first_ts = ""
    last_ts = ""

    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue

            if not cwd and o.get("cwd"):
                cwd = o["cwd"]
            ts = o.get("timestamp")
            if ts:
                if not first_ts:
                    first_ts = ts
                last_ts = ts

            t = o.get("type")
            if t == "user":
                msg = o.get("message", {})
                content = msg.get("content", "") if isinstance(msg, dict) else ""
                text = _content_to_text(content)
                # 跳过 tool_result（user-type 但其实是工具返回）
                if isinstance(content, list) and all(
                    isinstance(i, dict) and i.get("type") == "tool_result" for i in content
                ):
                    continue
                # 跳过系统 caveat/scheduled-task 这类非真实用户话语
                if "<local-command-caveat>" in text or "<scheduled-task" in text:
                    continue
                if text.strip():
                    user_count += 1
                    lines_out.append(f"### 👤 User\n{text[:2000]}\n")
            elif t == "assistant":
                msg = o.get("message", {})
                content = msg.get("content", "") if isinstance(msg, dict) else ""
                text = _content_to_text(content)
                if text.strip():
                    # assistant 消息只保留前 1500 字符避免爆
                    lines_out.append(f"### 🤖 AI\n{text[:1500]}\n")

    return "\n".join(lines_out), cwd, user_count, f"{first_ts} → {last_ts}"


def _content_to_text(content) -> str:
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
                parts.append(f"[🛠 {item.get('name','?')}(...)]")
            elif t == "thinking":
                parts.append(f"[💭 {item.get('thinking', '')[:100]}...]")
            # 不包含 tool_result 因为太长
        return "\n".join(parts)
    return str(content)


def call_claude_cli(prompt: str, conversation: str) -> str:
    """用 claude CLI subprocess 调 Claude 做提炼。走 Max 订阅，不烧 API。"""
    full_input = f"{prompt}\n\n---\n\n{conversation[:30000]}"  # 限量避免过长

    try:
        # claude -p --print 让它只输出结果，非交互式
        result = subprocess.run(
            ["claude", "-p", "--output-format", "text"],
            input=full_input,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,  # 5 分钟上限
        )
        if result.returncode != 0:
            log_error(f"claude CLI 失败: {result.stderr[:500]}")
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        log_error("claude CLI 找不到，确认 PATH")
        return ""
    except subprocess.TimeoutExpired:
        log_error("claude CLI 超时（5min）")
        return ""
    except Exception as e:
        log_error(f"claude CLI 异常: {e}")
        return ""


def project_shortname(cwd: str) -> str:
    if not cwd:
        return "unknown"
    cwd = cwd.replace("\\", "/").rstrip("/")
    if "/项目开发/" in cwd:
        return cwd.split("/项目开发/", 1)[1].replace("/", "_")
    if cwd.endswith("/Administrator"):
        return "home"
    parts = cwd.split("/")
    return "_".join(parts[-2:]) if len(parts) >= 2 else parts[-1]


def main():
    if len(sys.argv) < 3:
        log_error(f"参数不足: {sys.argv}")
        sys.exit(1)

    session_id = sys.argv[1]
    cwd = sys.argv[2]

    try:
        jsonl = find_jsonl(session_id, cwd)
        if not jsonl:
            log_error(f"找不到 jsonl session_id={session_id} cwd={cwd}")
            return

        conversation, actual_cwd, user_count, ts_range = extract_messages(jsonl)
        if user_count < MIN_USER_MESSAGES:
            log_error(f"跳过 session {session_id[:8]}: 只有 {user_count} 条 user 消息")
            return

        summary = call_claude_cli(EXTRACT_PROMPT, conversation)
        if not summary:
            log_error(f"提炼失败 session {session_id[:8]}")
            return
        if summary.strip().startswith("SKIP:"):
            log_error(f"Claude 判定跳过 session {session_id[:8]}: {summary.strip()[:200]}")
            return

        # 追加到 daily log
        today = datetime.now().strftime("%Y-%m-%d")
        proj = project_shortname(actual_cwd or cwd)
        log_path = DAILY_LOGS_DIR / f"{today}.md"
        DAILY_LOGS_DIR.mkdir(parents=True, exist_ok=True)

        entry = f"\n\n<!-- session={session_id} cwd={actual_cwd or cwd} ts={ts_range} -->\n{summary}\n"

        with open(log_path, "a", encoding="utf-8") as f:
            # 如是新文件加个 title
            if log_path.stat().st_size == 0:
                f.write(f"# Daily Log · {today}\n\n自动归档自 Claude Code SessionEnd hook。\n")
            f.write(entry)

    except Exception as e:
        import traceback
        log_error(f"主流程异常: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
