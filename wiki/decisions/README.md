---
title: Decisions 目录说明
type: readme
updated: 2026-04-18
---

# decisions/ — 关键选择的来龙去脉

**命名**：`{决策标题}.md`，动词开头更好，例如 `选A不选B.md` / `用X替代Y.md`。

**什么时候建页**：
- 遇到"为什么这么选"的讨论
- 选了某个非显而易见的方案
- 以后可能要回看"当初是怎么想的"

**模板**：
```yaml
---
title: ...
type: decision
updated: YYYY-MM-DD
sources: [raw/...]
projects: [相关项目]
---

## 背景
## 备选方案
## 最终选择 + 理由
## 决策日期
## 后续验证
```

**重要**：decisions 的 "后续验证" 区要回来填。如果决策证明错了，**不要删**——把修订写在"后续验证"里，保留思考痕迹。
