# Wiki Schema — 个人全局记忆系统

这个 wiki 是你这台电脑上所有 AI agent 项目共享的记忆库。**不绑定任何单一 agent**——Claude Code / WorkBuddy / OpenClaw / Hermes / Cursor / Codex 都能用，只要它能读取本地 markdown 和按 `AGENTS.md` 指令工作。

---

## 一、目录结构

```
{你的 wiki 根}/
├── raw/                      ← 原始对话备份，不可变（只增不改）
│   ├── YYYY-MM/              ← 按月分组的手动归档
│   │   ├── {项目}_YYYY-MM-DD.md         ← 会话提炼（summary）
│   │   └── {项目}_YYYY-MM-DD_full.md    ← 会话全文（可选）
│   ├── sessions/             ← sync_sessions.py 自动归档的 jsonl
│   ├── transcripts/          ← sync_sessions.py 生成的可读 md
│   └── daily-logs/           ← SessionEnd hook 自动追加的摘要
│
├── wiki/                     ← 结构化记忆，可变
│   ├── index.md              ← 导航入口
│   ├── about-me.md           ← 你自己的画像
│   ├── jarvis-persona.md     ← 你和你的 AI 的约定（称呼 / 风格 / 默契）
│   ├── ideas-backlog.md      ← 想法/todo/待探索
│   ├── people/               ← 所有人物一人一页
│   ├── projects/             ← 每个项目/大事一页
│   └── decisions/            ← 跨项目决策
│
├── schema.md                 ← 本文件
├── update-log.md             ← 每次增量 Ingest 的 diff
├── AGENTS.md                 ← AI agent 通用工作规则（Claude Code/WorkBuddy/OpenClaw/Cursor/...）
└── CLAUDE.md                 ← Claude Code 兼容兜底（指向 AGENTS.md）
```

---

## 二、页面模板

每个 wiki 页面必须有 frontmatter:

```yaml
---
title: 标题
type: person | project | decision | user | persona | backlog
updated: YYYY-MM-DD
sources: [raw/2026-04/xxx.md, ...]   ← 出处
projects: [项目A, 项目B]   ← 可选，人物/决策涉及哪些项目
---
```

### person 模板
```markdown
## 基本信息
## 核心特征
## 和我的关系
## 涉及项目
## 关键事件（时间线）
## 注意事项
```

### project 模板
```markdown
## 一句话定位
## 当前状态（YYYY-MM-DD）
## 架构 / 模式 / 关系结构
## 关键决策历史（链到 decisions/）
## 未完事项
## 关联人物（链到 people/）
```

### decision 模板
```markdown
## 背景
## 备选方案
## 最终选择 + 理由
## 决策日期
## 后续验证
## 拒绝的备选（可选）   ← 写清楚"为什么不选 X"，比"选了 Y"更值钱
## 监控与复盘（可选）   ← 多久回看一次？什么信号说明决策需要修订？
```

**经验**：用一段时间后会发现，**"拒绝的备选"** 这一段最有价值——以后回看决策时，最先忘的不是"为什么选了这个"，而是"当初为什么没选那个"。强烈建议每个非显然的决策都填这一段。

---

## 三、什么信息归到哪个文件

| 信息类型 | 归档位置 |
|---|---|
| 你自己的身份/特质/偏好 | `about-me.md` |
| 你和 AI 的默契 | `jarvis-persona.md` |
| 任何人物（家人/朋友/同事/合作方） | `people/{姓名}-{角色}.md` |
| 产品/项目/业务线全景 | `projects/{项目名}.md` |
| 一次关键决策的来龙去脉 | `decisions/{标题}.md` |
| 想法/暂未做的探索 | `ideas-backlog.md` |

**判断规则**：
- 一个事实只写一次，其他地方用链接引用
- 涉及"为什么"的讨论 → decisions/
- 涉及"是什么/现状" → 对应实体页面
- 跨项目的人 → people/ 里一页，页面里列"涉及项目"

---

## 四、更新规则（增量 Ingest）

### 触发
你说"更新 wiki"、"备份会话"、"存记忆"时执行：

1. **写 raw**：当天对话备份到 `raw/YYYY-MM/{项目}_YYYY-MM-DD.md`
2. **识别受影响页面**：读新 raw，对照 wiki/，列出需要改的页面
3. **增量更新**：
   - 新事实 → 追加
   - 事实变化 → 旧值移到页底 `## 历史变更` + 时间戳，正文改新值
   - 新实体 → 按模板新建
4. **写 update-log.md 顶部**
5. **更新 index.md**（如有新页面）

### 冲突
默认新覆盖旧，旧移到页底 `## 历史变更`。不确定时**问用户**。

### 什么不写入 wiki
- 纯技术调试过程 → 只写结论到 decisions
- 一次性 chat 闲聊
- 能从 git/代码里看到的事实

---

## 五、新会话启动规则

1. 先读 `wiki/index.md`
2. 按任务相关度读具体页面
3. 需要精确细节时翻 `raw/`
4. wiki 可能已过时 → 和用户确认关键信息再行动

---

## 五·二、index.md 怎么组织

**积累到 5+ 条目后**：按主题/优先级分组，不要扁平列。例如 decisions/ 下可以分：「项目 A 相关」「人际战略」「跨项目教训」「方法论」等子标题。

每条链接尽量带**一句话摘要**，让用户（和 AI）扫 index 就能判断要不要点进去。

---

## 六、项目-local 补充记忆

每个项目目录下**可以**有自己的 `memory/` 或 `CLAUDE.md` 存项目-local 状态（如某个服务的端口、API 版本）。但所有跨项目的信息（人物、决策、个人画像）只在全局 wiki 里。

项目-local vs 全局的判断：
- "别的项目会不会关心这个事实" → 会 = 全局；不会 = local
