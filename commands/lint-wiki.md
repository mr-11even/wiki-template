---
description: 跑 wiki 健康检查脚本（断链/过期/孤立页/frontmatter 缺失）
---

运行 wiki lint，报告健康问题：

!`python {{WIKI_ROOT}}/tools/lint_wiki.py`

以上是 lint 原始报告。

**你的任务**：
1. 把结果按严重度重新排序（broken link > stale > orphan > missing-frontmatter）
2. 给出修复建议：
   - 断链：改路径还是删链接？
   - 过期：内容是否还准？ 需不需要更新 frontmatter 的 updated 时间
   - 孤立：要不要加 backlink，或者这个页是不是应该并入别的页
   - frontmatter 缺：补上必要字段
3. 如果数量可控（<10），列每一项具体修哪里
4. 如果多（>10），告诉 用户优先处理哪 3-5 条

不要自动修，交给 用户拍板或下一轮会话里做。
