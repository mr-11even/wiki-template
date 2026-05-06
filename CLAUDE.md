# CLAUDE.md

**Claude Code 用户**：本文件是为了让 Claude Code 自动加载到工作规则保留的兜底入口。所有指令的权威来源在 [`AGENTS.md`](./AGENTS.md)。

请读 `AGENTS.md`，按那里的规则工作。

---

## Claude Code 专属补充（其他 agent 用户忽略此节）

- `~/.claude/commands/` 里的 8 个 slash commands（`/today` `/update-wiki` `/challenge` `/trace` `/connect` `/drift` `/emerge` `/lint-wiki`）由 `setup.ps1` 自动安装
- `SessionEnd` hook 由 `setup.ps1` 注册到 `~/.claude/settings.json`，会话结束时自动调用 `tools/optional-claude-code/extract_session.ps1`，把会话提炼追加到 `raw/daily-logs/{今天}.md`
- 自动归档脚本在 `tools/optional-claude-code/sync_sessions.py`（`setup.ps1` 可注册为 Windows 每日 03:15 任务）

非 Claude Code 用户（WorkBuddy / OpenClaw / Hermes / Cursor / Codex / 其他）：忽略本文件，直接看 [`AGENTS.md`](./AGENTS.md)。
