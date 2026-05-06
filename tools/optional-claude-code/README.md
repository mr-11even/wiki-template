# tools/optional-claude-code/ — 仅 Claude Code 用户用

这个子目录里的脚本**只对使用 Claude Code 的用户有用**。如果你用的是 WorkBuddy、OpenClaw、Hermes、Cursor、Codex 或其他 agent，可以直接忽略整个目录。

## 这些脚本做什么

| 脚本 | 作用 | 依赖 |
|---|---|---|
| `sync_sessions.py` / `.ps1` | 把 `~/.claude/projects/*.jsonl` 里的会话归档到 `raw/sessions/{项目}/{月}/`，同时生成可读 transcript 到 `raw/transcripts/`。增量同步（按 mtime） | Python 3.10+，能读 `~/.claude/projects/` |
| `extract_session.py` / `.ps1` | Claude Code `SessionEnd` hook 的处理器：会话结束时被自动调用，跑 `claude -p` 让 Claude 提炼这段对话的要点，追加到 `raw/daily-logs/YYYY-MM-DD.md` | Python 3.10+，`claude` CLI 在 PATH，Anthropic 账号已登录 |

## 为什么这是 Claude Code 专属

- 这两个脚本都依赖 `~/.claude/projects/{编码后cwd}/{session_id}.jsonl` 这个目录结构
- 这是 Claude Code CLI 自己的存储格式，其他 agent 不一样
- WorkBuddy / OpenClaw / Hermes 等大多数 agent **不暴露**自己的 session 文件，或格式完全不同

## 不用 Claude Code 的话怎么办

不用着急，wiki 的核心价值不依赖这两个脚本。它们只是**自动化**了"会话结束 → 写 raw"这一步。

手动方式同样可行（其实更可控）：

- 会话结束时让你的 agent **自己**写 `raw/YYYY-MM/{项目}_YYYY-MM-DD.md` 摘要 —— `commands/update-wiki.md` 里就是这个工作流
- 第二天打开新会话时 agent 会先读 `wiki/index.md` + 相关 raw 摘要，承接上下文

## 装这些脚本

如果你确实在用 Claude Code 且想启用自动归档：

参见根目录的 `README-setup.md` "可选：Claude Code 用户的自动化设置" 章节。`setup.ps1` 会引导你完成。

## 安全提醒

`raw/sessions/*.jsonl` 包含 **Anthropic OAuth token**（`sk-ant-oat01-...` / `sk-ant-ort01-...`）。

- 永远不要 `git add` `raw/`（`.gitignore` 已排除，但每次 commit 前肉眼扫一眼）
- 怀疑泄露：`claude.ai` 重新登录即可 rotate
- 用 `python tools/redact_secrets.py` 定期扫
