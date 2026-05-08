# Personal Wiki — 第二大脑模板

一个让 **AI agent 跨会话记住你**的本地 markdown wiki 模板。

把它放在你电脑上，新会话开始时 AI 自动读到你的画像、项目、人际、关键决策——不用每次重新解释一遍。

---

## 这套系统能做什么

- **跨会话记忆**：新会话的 AI 一开始就知道你是谁、在做什么、谁是谁
- **结构化沉淀**：决策、想法、人物画像不靠聊天记录搜索，按主题归档
- **可视化**：用 Obsidian 打开就是知识图谱
- **健康检查**：`tools/lint_wiki.py` 一键找断链 / 过期 / 孤立页

**仅 Claude Code 用户额外有：**
- 8 个 slash commands（`/today` `/update-wiki` `/challenge` `/trace` `/connect` `/drift` `/emerge` `/lint-wiki`）
- 会话结束自动归档（SessionEnd hook）
- 每晚定时同步会话到 raw/

---

## 谁该用

✅ 你和 AI 长时间合作（每周 5+ 小时），不希望每次重新解释一遍背景  
✅ 你有跨多项目/多人际的协作（运营总监、PM、创业者、研究者）  
✅ 你想留下一份"决策来龙去脉"的档案，而不是只在聊天记录里找

❌ 你只是偶尔用 AI 问点小问题（杀鸡用牛刀）  
❌ 你的工作完全在团队 Notion / 飞书里，不想加一层个人 wiki

---

## 在哪些 agent 上能用

| Agent | 自动加载工作规则 | slash commands | 自动归档会话 |
|---|---|---|---|
| **Claude Code** | ✅ `CLAUDE.md` → `AGENTS.md` | ✅ 自动装 | ✅ SessionEnd hook |
| **OpenAI Codex CLI** | ✅ `AGENTS.md` | ⚠️ 手动复制 | ❌ |
| **Cursor** | ✅ `AGENTS.md` | ⚠️ 手动复制 | ❌ |
| **OpenClaw** | ✅ `AGENTS.md` / `SOUL.md` | ✅ 可适配为 skill | 取决于用法 |
| **Hermes Agent** | ✅ `AGENTS.md` | ✅ 内置 skill 系统 | ✅ 内置 |
| **腾讯 WorkBuddy** | ✅（基于 OpenClaw + Hermes 架构） | 取决于版本 | 取决于版本 |
| **DeepSeek 网页版 / 豆包 / KIMI 网页版** | ❌ 需手动 paste | ❌ | ❌ |

**核心通用部分**（schema / wiki 结构 / 工作流）所有 agent 都能用。**只有 Claude Code 能跑全套自动化**。

---

## 前置要求

**核心安装（所有用户）**：
- **OS**：Windows 10/11 / macOS / Linux（setup 脚本目前只测了 Win，其他 OS 手动跟着 README 装）
- **Python 3.10+**（仅在你想用 lint / redact_secrets 这俩工具时需要）
- **Obsidian**（可选但强推）：https://obsidian.md/download

**可选 — 仅 Claude Code 用户**：
- **Claude Code**：`npm install -g @anthropic-ai/claude-code`
- **PowerShell 5.0+**（Windows 自带）—— `setup.ps1` 用这个

---

## 安装

### 路径 A：Claude Code 用户（自动化）

1. 把整个目录复制到你的机器
2. 打开 PowerShell，cd 进去
3. 跑：
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1
   ```
4. 按提示选：
   - 装到哪个目录（默认 `F:\my-wiki`）
   - 是否注册每日定时任务（建议选 y）
   - 是否装 slash commands（建议选 y）

`setup.ps1` 做的事：
- 在你选的路径下建起目录结构
- 替换 `{{WIKI_ROOT}}` 占位符
- 装 8 个 slash commands 到 `~/.claude/commands/`
- 在 `~/.claude/settings.json` 加 SessionEnd hook
- 注册 Windows 任务 `SyncLlmWikiDaily`（如果选了）

### 路径 B：其他 agent 用户（手动）

如果你用 WorkBuddy / OpenClaw / Hermes / Cursor / Codex 等：

1. 把整个目录复制到你想放的位置（比如 `F:\my-wiki\`）
2. **删除** `tools/optional-claude-code/` 目录（你用不到）
3. **删除** `commands/` 目录（这是 Claude Code slash commands，对你没用——但里面的 prompt 内容可以作为模板复制粘贴，看 [Q3](#q3-非-claude-code-用户怎么用-commands-里的-prompt)）
4. **删除** `setup.ps1`（仅 Claude Code 自动化用）
5. 在 wiki 目录初始化 git（推荐推到 GitHub 私有仓做跨设备同步——`.gitignore` 已设置好）
6. 让你的 agent 进入这个目录工作。`AGENTS.md` 大多数 agent 会自动加载

> WorkBuddy 用户：基于 OpenClaw + Hermes 架构，理论上自动加载 `AGENTS.md`。第一次会话开头如果 AI 没主动读 `wiki/index.md`，手动让它读一遍即可。

---

## 第一次和 AI 开口怎么说

📍 **复制 [`prompts/first-time.md`](./prompts/first-time.md) 里的提示词，发给你的 AI**。它会用 20 分钟自动帮你搭起 `about-me.md` + `jarvis-persona.md` + 第一个项目页 + 第一个人物页。

---

## 第一周怎么用（5 个具体场景）

如果你跳过了上面那个"第一次提示词"，下面是 5 个**最值得做的入门场景**，按强度从轻到重排：

### 场景 1：花 5 分钟填 `wiki/about-me.md`

这是最低门槛、价值最高的事。打开文件按提示填：

- 你是谁、做什么
- 工作风格（喜欢被挑战还是被支持？喜欢长讨论还是简短直接？）
- 禁忌（什么话题/什么风格 AI 一碰你就烦？）

**做完之后**：下次和 AI 开会话，让它先读一下 `about-me.md`。它的回答风格会立刻不一样。

### 场景 2：开会前让 AI 写一个人物画像

下周要见某个甲方/合作方/医生？开会前对 AI 说：

> "我下周要见 X。我知道的关于他的事：[列几条]。
> 帮我建一个 wiki/people/X.md，按 schema.md 的 person 模板填。
> 我开会前读一遍。"

AI 写一份初稿。你审过、补充几条，存进去。**会议结束后**让 AI 加一段"会上观察到的新事实"。

第二次再见这个人时——你不需要回忆任何事。

### 场景 3：决策时让 AI 帮你写决策记录

你正在选方案 A / B / C，纠结。打开新会话：

> "我在 [背景描述] 选 A 还是 B。把这次讨论沉淀成 wiki/decisions/X.md。"

聊完后对 AI 说"更新 wiki"，它按 schema 生成决策页（含**拒绝的备选**和**监控复盘**）。

**3 个月后回看**：你不会记得当初为什么选了 A，但你会记得当初为什么没选 B——这才是真正值钱的部分。

### 场景 4：每周五用 30 分钟"沉淀本周"

固定时间。打开 AI，对它说：

> "本周我做了 [简单列] 这些事，按 wiki schema 帮我看哪些应该沉淀。
> 涉及的项目页要不要更新？有没有该建的新决策页？"

AI 给一个清单。你 yes/no/skip 它写。一周一次，半小时。

### 场景 5（仅 Claude Code 用户）：装 `/today` slash command

每天早上打开 Claude Code，输入 `/today`：

> AI 读 update-log + ideas-backlog，告诉你今天最该做的 1-3 件事。

这是把 wiki 用成"晨间执行助手"——不是新增信息，是从已有信息里挖出最该做的。

---

## 文件结构

```
{wiki-root}/
├── AGENTS.md                 ← AI agent 通用工作规则（主指令）
├── CLAUDE.md                 ← Claude Code 兼容兜底（指向 AGENTS.md）
├── schema.md                 ← 结构规则（页面模板 / 增量更新流程）
├── update-log.md             ← 每次更新的 diff
├── README.md                 ← 本文件
├── setup.ps1                 ← Claude Code 用户用的自动化安装脚本
├── .gitignore
├── .obsidian/                ← Obsidian 预配置
│
├── wiki/                     ← 结构化记忆（你和 AI 共同维护）
│   ├── index.md              ← 导航入口
│   ├── about-me.md           ← 你自己的画像
│   ├── jarvis-persona.md     ← 你和你的 AI 的约定
│   ├── ideas-backlog.md
│   ├── people/               ← 包含 _example- 示例文件
│   ├── projects/             ← 包含 _example- 示例文件
│   └── decisions/            ← 包含 _example- 示例文件
│
├── raw/                      ← 原始对话归档（永不入 git）
│   ├── YYYY-MM/              ← 手动归档
│   ├── sessions/             ← Claude Code 自动归档的 jsonl
│   ├── transcripts/          ← 自动生成的可读 md
│   └── daily-logs/           ← Claude Code SessionEnd hook 追加的摘要
│
├── commands/                 ← Claude Code slash commands 源文件（setup.ps1 装到 ~/.claude/commands/）
│
└── tools/
    ├── _config.py
    ├── config.json           ← 本机配置（setup.ps1 生成，不入 git）
    ├── lint_wiki.py          ← wiki 健康检查（所有用户可用）
    ├── redact_secrets.py     ← 敏感信息脱敏扫描（所有用户可用）
    ├── logs/                 ← 运行日志
    └── optional-claude-code/ ← 仅 Claude Code 用户用
        ├── README.md
        ├── sync_sessions.py / .ps1
        └── extract_session.py / .ps1
```

---

## 安全说明（重要）

`raw/` 目录里的数据**可能含敏感信息**：

- **Claude Code 用户**：`raw/sessions/*.jsonl` 里包含 Anthropic OAuth token（`sk-ant-oat01-...` / `sk-ant-ort01-...`）。**泄露 = Claude 账号被接管**
- **所有用户**：`raw/YYYY-MM/` 手动归档可能含未脱敏的 API key、密码、客户信息

**护栏**：

1. **`raw/` 永远不入 git**（`.gitignore` 已设置好——但 commit 前肉眼扫一眼）
2. **不要把 `raw/` 上传到云盘 / 同步到不可控位置**
3. 怀疑泄露：
   - Claude OAuth → 登录 claude.ai → Settings → 重新登录即可 rotate
   - 其他 API key → 立即去对应平台 revoke
4. 定期跑：`python tools/redact_secrets.py` 扫一遍

---

## 推 GitHub 做跨设备同步

强烈建议把 wiki 推到 **GitHub 私有仓**，这样换电脑/出差/换公司都能继续用。

```bash
cd <你的 wiki 根>
git init
git add .
git status        # 确认 raw/ 没被加进去（应该被 .gitignore 排除）
git commit -m "Initial wiki"
gh repo create my-wiki --private --source=. --push
```

新设备：

```bash
git clone https://github.com/<你的用户名>/my-wiki.git
```

日常：开始 `git pull` / 结束 `git add . && git commit -m "..." && git push`。

**重要**：GitHub 账号务必开 2FA。Wiki 里有人物画像、决策细节，账号被攻破代价很高。

---

## 排错

### slash commands 不识别（仅 Claude Code）
- 重启 Claude Code（slash commands 只在启动时扫一次）
- 确认 `~/.claude/commands/` 里有 8 个 md 文件

### SessionEnd hook 没跑（仅 Claude Code）
- 看 `tools/logs/hook_trigger.log`（PowerShell 触发日志）
- 看 `tools/logs/extract_session_errors.log`（Python 错误日志）
- 确认 `~/.claude/settings.json` 里有 `hooks.SessionEnd` 配置
- 确认 `claude` CLI 在 PATH（`claude --version` 能跑）

### 定时任务没跑（仅 Claude Code）
- `Get-ScheduledTask -TaskName SyncLlmWikiDaily`
- 手动触发：`Start-ScheduledTask -TaskName SyncLlmWikiDaily`

### Obsidian 慢
- `.obsidian/app.json` 里 `userIgnoreFilters` 应已排除 `raw/` 和 `tools/`
- 第一次打开要扫描所有文件是正常的，扫完就快

### AI 不读 AGENTS.md
- 用的是不支持 `AGENTS.md` 自动加载的 agent？会话开头手动 paste 一次即可
- 用 Claude Code 但 AI 没读？检查 wiki 根目录有没有 `CLAUDE.md`（应该有，且指向 AGENTS.md）

### 我不是 Claude Code 用户，不知道怎么"会话结束归档"
- 自己手动写 `raw/YYYY-MM/{项目}_YYYY-MM-DD.md` —— 让 AI 写摘要给你，你贴进去
- 或者干脆只用结构化 wiki，不做 raw 归档（损失"原话回查"能力，但 wiki 主体仍然有价值）

---

## FAQ

### Q1：我必须用 Claude Code 吗？
不必。核心 wiki 结构（AGENTS.md / schema / wiki/ / tools/lint / tools/redact）所有 agent 都能用。Claude Code 只是有一套**自动化脚本**让会话归档不需要你手动做。

### Q2：我用 WorkBuddy / OpenClaw / Hermes，能用得起来吗？
能。这些 agent 都支持读取 `AGENTS.md` 自动加载工作规则，也都能读写本地 markdown 文件。会话结束归档需要手动让 AI 写一段摘要到 `raw/YYYY-MM/`，比 Claude Code 的自动化路径多一步操作。

### Q3：非 Claude Code 用户怎么用 commands/ 里的 prompt？
打开 `commands/today.md` 复制内容（删除 frontmatter 那几行），把 `{{WIKI_ROOT}}` 替换成你的 wiki 路径，作为对 AI 的指令直接发出去。例：

```
（粘贴 today.md 内容，把 {{WIKI_ROOT}} 替换成 F:/my-wiki）
```

每个 command 都可以这么用。

### Q4：能多人共用一个 wiki 吗？
**不建议**。这个模板设计是"个人 second brain"。多人共享场景（团队知识库）需要不同设计：权限、并发写、谁负责审核——超出本模板范围。

如果你想做**家庭/小团队共享**：每人维护自己的 wiki，再额外建一个 `team-wiki` 仓库专门放共享内容。两层并存。

### Q5：wiki 越来越大怎么办？
不会真的"太大"。
- `wiki/` 全是 markdown，1000 个页面也就几 MB
- `raw/` 会大（jsonl + 原始对话），但它**不入 git**，本地存就好
- Obsidian 索引几千个文件没问题

### Q6：AI 写 wiki 写错了怎么办？
- 立即让它说明改了哪些文件
- 不满意：`git checkout -- <文件>` 回滚
- **每次让 AI 改 wiki 前 commit 一下**，方便回滚

---

## 卸载

```powershell
# 仅 Claude Code 用户
Unregister-ScheduledTask -TaskName SyncLlmWikiDaily -Confirm:$false

# 从 ~/.claude/settings.json 手动删除 hooks.SessionEnd 段
# 删除 ~/.claude/commands/ 下安装的 8 个 md（today/challenge/...）
```

```bash
# 所有用户
rm -rf <你的 wiki 根>
```

---

## 设计来源

- 启发自 Andrej Karpathy 2026-04 的 LLM Wiki 思路
- 扩展：跨项目全局 wiki / 自动归档 / SessionEnd 自进化 / 安全脱敏 / 批判性 slash commands / agent-agnostic（AGENTS.md 标准）

如果你用得不错或者发现哪里别扭，欢迎反馈。这个模板会持续迭代。
