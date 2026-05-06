# Wiki 更新日志（倒序）

每次"更新 wiki"执行后在顶部加一条。格式：

```
## YYYY-MM-DD — 一句话摘要

### 触发
什么事件 / 用户说了什么触发了这次更新。

### 新增/修改
- `wiki/xxx.md` — 做了什么改动
- ...

### 未做 / 遗留
- （如有）
```

---

## 2026-05-07 — 初始化（来自 wiki-template v2，agent-agnostic）

用 `setup.ps1` 从 wiki-template v2 初始化。

**v2 相对 v1（2026-04-18）的变化**：
- 新增 `AGENTS.md` 作为主指令文件（OpenAI Codex / Cursor / OpenClaw / Hermes / WorkBuddy 都自动读）
- `CLAUDE.md` 简化为指向 `AGENTS.md` 的兜底（保 Claude Code 兼容）
- Claude-Code 专属的 `sync_sessions` / `extract_session` 移到 `tools/optional-claude-code/`
- `setup.ps1` 加入 agent 类型选择，非 Claude Code 用户自动跳过 hook / 定时任务
- `decision` 模板加 `## 拒绝的备选`（可选）/ `## 监控与复盘`（可选）两段
- `wiki/index.md` 加分类组织指引（积累 5+ 条目后按主题分组）
- 新增 3 个 `_example-*` 示例文件（people / projects / decisions），用运营场景，看完可删

目录结构 + 工具 + slash commands + SessionEnd hook 已就位（如选了 Claude Code 自动化）。
wiki/ 下大部分是空模板，等待第一次真实会话沉淀。

---

## 2026-04-18 — 初始化（来自 llm-wiki-template v1）

用 setup.ps1 从模板初始化。目录结构 + 工具 + slash commands + SessionEnd hook 已就位。
wiki/ 下大部分是空模板，等待第一次真实会话沉淀。
