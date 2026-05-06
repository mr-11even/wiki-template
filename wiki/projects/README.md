---
title: Projects 目录说明
type: readme
updated: 2026-04-18
---

# projects/ — 每个项目/大事一页

**命名**：`{项目名}.md`。用你自己习惯的叫法。

**什么时候建页**：
- 一个事情持续时间 > 1 周
- 涉及多次会话/多个人/多个决策
- 你希望新会话的 AI 能快速接上 context

**不建页的情况**：
- 一次性完成的小任务
- 纯探索性的想法（放 `ideas-backlog.md`）

**模板字段**（frontmatter + 正文）：
```yaml
---
title: 项目名
type: project
updated: YYYY-MM-DD
sources: [raw/...]
---

## 一句话定位
## 当前状态（日期）
## 架构 / 模式 / 关系结构
## 关键决策历史（链到 decisions/）
## 未完事项
## 关联人物（链到 people/）
```

建好一个页面后，在 `wiki/index.md` 里加一条链接。
