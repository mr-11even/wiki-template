---
description: 触发"更新 wiki" 标准流程，把当前会话的要点沉淀到 {{WIKI_ROOT}}/
argument-hint: "[可选：要强调的主题或项目]"
---

按 `{{WIKI_ROOT}}/schema.md` 的增量 Ingest 规则处理本次会话：

1. **回顾当前会话**：识别今天讨论/决策/发现的要点。焦点：$ARGUMENTS（为空时覆盖整个会话）
2. **写 raw 摘要**：如果本次会话有独立价值，在 `{{WIKI_ROOT}}/raw/YYYY-MM/{项目}_YYYY-MM-DD.md` 写提炼摘要（不是整个对话复制）
3. **识别受影响的 wiki 页**：对照 `{{WIKI_ROOT}}/wiki/` 现有页面，列出需要改的
4. **增量更新**：
   - 新事实追加
   - 事实变化 → 旧值移到页底 `## 历史变更` + 时间戳
   - 新实体 → 按 schema 新建页面
5. **记 update-log**：在 `{{WIKI_ROOT}}/update-log.md` 顶部加一条 diff 记录
6. **更新 index.md**：如新增页面

不要擅自覆盖冲突，不确定就问 用户。对话里没有价值沉淀的话，明确说"本次会话无需更新"不要强塞。
