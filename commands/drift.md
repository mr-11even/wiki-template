---
description: 对比 用户的 stated intentions（ideas-backlog）vs 近期实际行为（digest+update-log）
---

用户要看自己有没有**意图漂移**。

工作流：
1. 读 `{{WIKI_ROOT}}/wiki/ideas-backlog.md` 的"在做中"+"待启动"+"探索中"三栏
2. 读 `{{WIKI_ROOT}}/update-log.md` 最近 4-6 条（过去 2-4 周的变更）
3. 读 `{{WIKI_ROOT}}/raw/digests/*.md` 找最近的活动主线
4. 做三个对比：
   - **"说要做但没动过"**：ideas-backlog 里明确说待做，但 update-log 和 digest 里过去几周没任何相关动作的条目
   - **"没说要做但在狂做"**：最近在搞但 ideas-backlog 里压根没列/列了在底下的（可能是临时进来的方向）
   - **"说要做 + 已经做了但没更新 ideas-backlog"**：需要打勾归档的漏项
5. 输出格式：
   ```
   ## 意图 vs 行为漂移报告（过去 N 周）

   🚫 说了没做（可能需要下决心砍或真做）：
     - X：backlog 里 M 天前加的，未见动作
     - ...

   🤷 没说在做（临时起意 or 真痛点？）：
     - Y：{具体工作}，强度不低，该上 backlog
     - ...

   ✅ 做完没登记：
     - Z：update-log 显示完成，backlog 里还挂着
   ```
6. 最后**一句话提醒**：这个漂移里最值得 用户停下来决策的是哪一项
