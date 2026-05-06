# 第一次和 AI 开口怎么说

刚把这个 wiki 模板 clone 下来，**第一次**打开 AI agent（WorkBuddy / Claude Code / OpenClaw / Hermes / Cursor / Codex 等）时，把下面这段直接发给它。

它会：
1. 自己读懂这个 wiki 的工作规则
2. 用 5 个问题采访你
3. 把你的答案填进 `wiki/about-me.md` 和 `wiki/jarvis-persona.md`
4. 帮你建第一个项目页

完成大约 20 分钟，你的"第二大脑"就开张了。

---

## 复制下面整段发给你的 AI

```
你好。这是我的「第二大脑」wiki 模板，刚从 GitHub clone 下来到这个目录。

请帮我做这些事，按顺序：

1. 读项目根目录的 AGENTS.md，理解你接下来的工作规则。如果你没有读文件的权限或工具，
   告诉我，我把内容贴给你。

2. 读 wiki/index.md 看导航。

3. 读 wiki/about-me.md 和 wiki/jarvis-persona.md（这两个目前都是空模板）。

4. 扫一眼这三个示例文件，理解 wiki 的填写格式：
   - wiki/people/_example-小红书代运营对接人.md
   - wiki/projects/_example-周更内容发布流水线.md
   - wiki/decisions/_example-周报改用飞书文档不用Word.md

5. 读 schema.md 知道每种页面的模板结构。

读完之后，开始**采访我**。一次问一个，等我答完再问下一个：

   Q1. 你的名字、角色、主要在做的工作是什么？
   Q2. 你的工作风格：喜欢被批判挑战还是被支持？喜欢长讨论还是简短直接？
       有没有特别讨厌的对话方式（比如废话、过度委婉、一味认同）？
   Q3. 你想给我（AI）起什么名字？有没有特定的"人设期望"？
       （灵感参考：钢铁侠的 Jarvis、Friday；或随便起一个）
   Q4. 你最近 1-3 个月在追的主要项目是什么？挑 1 个最重要的告诉我。
   Q5. 这个项目里有没有反复出现的关键人物？（同事 / 合作方 / 客户 / 家人都算）

采访完之后：

A. 把答案**整理**填进 wiki/about-me.md（按 schema.md 的 user 模板 + frontmatter）。
   不要把我的话原样复制粘贴，要提炼成"画像"形式。

B. 把"AI 的名字 + 我的工作风格期望 + 不要做的事"填进 wiki/jarvis-persona.md。

C. 基于 Q4，建一个 wiki/projects/{项目名}.md，按 schema.md 的 project 模板填。
   信息不全的章节标 "TODO 待补"，不要瞎编。

D. 基于 Q5，如果有具体人物，建一个 wiki/people/{姓名}-{角色}.md。

E. 更新 wiki/index.md，把新建的页面加进导航；删掉示例文件的链接（或保留也行，
   等我决定）。

F. 在 update-log.md 顶部加一条本次的 diff 记录。

完成后展示给我看，我审核 OK 后再继续聊。如果某一步你不确定怎么做，**先问我** 不要
猜测——尤其是涉及我个人偏好或人物画像的部分。
```

---

## 之后的日常使用

**每次新会话**：直接说事就行，AI 会自动读 AGENTS.md 知道你的画像和项目状态。
不需要再 paste 上面那段长的。

**会话结束想沉淀**：直接说 "更新 wiki"。AI 按 AGENTS.md 的"更新 wiki"流程处理。

**特定任务**：
- "帮我建一个 person 页给 [名字]，他是 [关系]，最近 [事件]"
- "我在 A 和 B 之间纠结，把这次讨论沉淀成 decision 页"
- "帮我看一下 wiki/projects/{项目} 是不是该更新了"

---

## 如果你的 AI 不读文件

少数轻量 agent / 网页版 AI 不能直接读取本地文件。这时候：

1. 把 AGENTS.md 的全部内容**手动 paste** 到对话里，作为"系统提示词"
2. 让 AI 一次只处理一个文件 —— 你贴内容，AI 给修改后的内容，你保存
3. 比有原生文件工具的 agent 慢 3-5 倍，但仍然能用

考虑换一个有文件操作能力的 agent（Claude Code / Cursor / WorkBuddy / OpenClaw / Hermes），体验会好很多。
