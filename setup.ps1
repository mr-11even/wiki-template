# setup.ps1 — Personal Wiki 模板安装脚本
#
# 用法（PowerShell 里跑）：
#   powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1
#
# 做的事（按 agent 类型分支）：
# 通用（所有用户）：
#   1. 问目标路径
#   2. 复制模板过去（除了 setup.ps1 / README.md）
#   3. 批量替换占位符 {{WIKI_ROOT}} → 用户选的路径
#   4. 生成 tools/config.json
#
# 仅 Claude Code 用户额外：
#   5. 把 commands/*.md 装到 ~/.claude/commands/（slash commands）
#   6. 改 ~/.claude/settings.json 加 SessionEnd hook
#   7. 注册 Windows 任务计划 SyncLlmWikiDaily（可选）
#
# 非 Claude Code 用户：跳过 5-7

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$TEMPLATE_DIR = $PSScriptRoot

function Ask($prompt, $default) {
    if ($default) {
        $reply = Read-Host "$prompt [默认 $default]"
        if (-not $reply) { return $default }
        return $reply
    }
    return Read-Host $prompt
}

function Confirm($prompt) {
    $reply = Read-Host "$prompt (y/n)"
    return $reply -match '^(y|yes)$'
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  Personal Wiki 安装向导" -ForegroundColor Cyan
Write-Host "  (跨 Agent 通用第二大脑模板)" -ForegroundColor DarkCyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# Step 0: 预检
# ------------------------------------------------------------
Write-Host "预检环境..." -ForegroundColor Yellow

$pythonOk = $null
try { $pythonOk = (python --version 2>&1) } catch {}
if (-not $pythonOk) {
    Write-Host "⚠ 找不到 python。lint_wiki / redact_secrets 这些工具需要 Python 3.10+" -ForegroundColor Yellow
    Write-Host "  装：https://www.python.org/downloads/  （勾选 'Add to PATH'）"
    if (-not (Confirm "继续安装？（wiki 主体仍可用，但少了健康检查）")) { exit 1 }
} else {
    Write-Host "  ✓ $pythonOk" -ForegroundColor Green
}

$claudeOk = $null
try { $claudeOk = (claude --version 2>&1) } catch {}
$claudeAvailable = -not [string]::IsNullOrEmpty($claudeOk) -and $claudeOk -notmatch 'not recognized|not found'

if ($claudeAvailable) {
    Write-Host "  ✓ Claude Code CLI 已安装：$claudeOk" -ForegroundColor Green
} else {
    Write-Host "  ⓘ 未检测到 Claude Code CLI（这没问题）" -ForegroundColor DarkCyan
}

Write-Host ""

# ------------------------------------------------------------
# Step 0.5: Agent 类型选择
# ------------------------------------------------------------
Write-Host "你主要用哪个 AI agent 配合这个 wiki？" -ForegroundColor Yellow
Write-Host "  1. Claude Code（slash commands + SessionEnd 自动归档 + 每日同步）"
Write-Host "  2. 其他（WorkBuddy / OpenClaw / Hermes / Cursor / Codex / 网页 AI）—— 只装文件，不装自动化"
Write-Host ""

$agentDefault = if ($claudeAvailable) { "1" } else { "2" }
$agentChoice = Ask "选择 (1/2)" $agentDefault
$installClaudeAutomation = $agentChoice -eq "1"

if ($installClaudeAutomation -and -not $claudeAvailable) {
    Write-Host ""
    Write-Host "  ⚠ 你选了 Claude Code 但没检测到 CLI。" -ForegroundColor Yellow
    Write-Host "    自动化部分会装上但不能用，直到你装好 Claude Code。"
    Write-Host "    装：npm install -g @anthropic-ai/claude-code"
    if (-not (Confirm "继续？")) { exit 1 }
}

Write-Host ""

# ------------------------------------------------------------
# Step 1: 问目标路径
# ------------------------------------------------------------
$defaultTarget = "F:\my-wiki"
$target = Ask "把 wiki 装到哪个目录？" $defaultTarget
$target = $target.TrimEnd('\').TrimEnd('/')

if (Test-Path $target) {
    if ((Get-ChildItem $target -Force | Measure-Object).Count -gt 0) {
        Write-Host "⚠ $target 已存在且非空" -ForegroundColor Yellow
        if (-not (Confirm "继续？会合并到现有目录，可能覆盖同名文件")) { exit 1 }
    }
}

$projectsParent = ""
if ($installClaudeAutomation) {
    $projectsParent = Ask "你的项目一般放在哪个父目录？（用于自动识别项目名，可选，回车跳过）" ""
}

Write-Host ""

# ------------------------------------------------------------
# Step 2: 复制模板 + 替换占位符
# ------------------------------------------------------------
Write-Host "复制模板到 $target ..." -ForegroundColor Yellow

$excludes = @("setup.ps1", "README.md", "commands")

New-Item -ItemType Directory -Force -Path $target | Out-Null

Get-ChildItem -Path $TEMPLATE_DIR -Force | Where-Object { $excludes -notcontains $_.Name } | ForEach-Object {
    $dest = Join-Path $target $_.Name
    if ($_.PSIsContainer) {
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
    } else {
        Copy-Item -Path $_.FullName -Destination $dest -Force
    }
}

New-Item -ItemType Directory -Force -Path (Join-Path $target "raw\daily-logs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $target "tools\logs") | Out-Null

# 替换 {{WIKI_ROOT}} 占位符（仅 .md 文件需要）
$targetForward = $target -replace '\\','/'
Get-ChildItem -Path $target -Filter "*.md" -Recurse | ForEach-Object {
    $content = Get-Content -Path $_.FullName -Raw -Encoding utf8
    if ($content -match '\{\{WIKI_ROOT\}\}') {
        $content = $content -replace '\{\{WIKI_ROOT\}\}', $targetForward
        Set-Content -Path $_.FullName -Value $content -Encoding utf8 -NoNewline
    }
}

Write-Host "  ✓ 模板复制完成" -ForegroundColor Green

# ------------------------------------------------------------
# Step 3: 生成 tools/config.json
# ------------------------------------------------------------
$configPath = Join-Path $target "tools\config.json"
$config = @{
    wiki_root = $targetForward
    claude_projects_dir = (Join-Path $env:USERPROFILE ".claude\projects") -replace '\\','/'
}
if ($projectsParent) {
    $config.projects_parent_dir = ($projectsParent -replace '\\','/')
}
$config | ConvertTo-Json | Set-Content -Path $configPath -Encoding utf8
Write-Host "  ✓ config.json 写入 $configPath" -ForegroundColor Green

# ------------------------------------------------------------
# Step 4-6: Claude Code 自动化（仅 Claude Code 用户）
# ------------------------------------------------------------
if ($installClaudeAutomation) {

    # Step 4: 装 slash commands
    $commandsSrc = Join-Path $TEMPLATE_DIR "commands"
    $commandsDst = Join-Path $env:USERPROFILE ".claude\commands"
    New-Item -ItemType Directory -Force -Path $commandsDst | Out-Null

    Write-Host ""
    Write-Host "装 slash commands 到 $commandsDst ..." -ForegroundColor Yellow

    Get-ChildItem -Path $commandsSrc -Filter "*.md" | ForEach-Object {
        $dst = Join-Path $commandsDst $_.Name
        if (Test-Path $dst) {
            Write-Host "  ⚠ 已存在：$($_.Name)" -ForegroundColor Yellow
            if (Confirm "  覆盖 $($_.Name)？") {
                $content = Get-Content -Path $_.FullName -Raw -Encoding utf8
                $content = $content -replace '\{\{WIKI_ROOT\}\}', $targetForward
                Set-Content -Path $dst -Value $content -Encoding utf8 -NoNewline
                Write-Host "    ✓ 覆盖" -ForegroundColor Green
            } else {
                Write-Host "    跳过" -ForegroundColor DarkGray
            }
        } else {
            $content = Get-Content -Path $_.FullName -Raw -Encoding utf8
            $content = $content -replace '\{\{WIKI_ROOT\}\}', $targetForward
            Set-Content -Path $dst -Value $content -Encoding utf8 -NoNewline
            Write-Host "  ✓ $($_.Name)" -ForegroundColor Green
        }
    }

    # Step 5: 注册 SessionEnd hook
    Write-Host ""
    Write-Host "注册 SessionEnd hook..." -ForegroundColor Yellow

    $settingsPath = Join-Path $env:USERPROFILE ".claude\settings.json"
    if (Test-Path $settingsPath) {
        $raw = Get-Content -Path $settingsPath -Raw -Encoding utf8
        $settings = $raw | ConvertFrom-Json
    } else {
        $settings = [PSCustomObject]@{}
    }

    # 注意：脚本现在在 tools/optional-claude-code/ 里
    $hookScriptPath = (Join-Path $target "tools\optional-claude-code\extract_session.ps1") -replace '\\','/'

    if (-not ($settings.PSObject.Properties.Name -contains 'hooks')) {
        $settings | Add-Member -NotePropertyName hooks -NotePropertyValue ([PSCustomObject]@{})
    }
    $hooksEntry = [PSCustomObject]@{
        matcher = "*"
        hooks   = @(
            [PSCustomObject]@{
                type    = "command"
                command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $hookScriptPath"
                timeout = 30
            }
        )
    }
    $settings.hooks | Add-Member -NotePropertyName SessionEnd -NotePropertyValue @($hooksEntry) -Force

    $settings | ConvertTo-Json -Depth 10 | Set-Content -Path $settingsPath -Encoding utf8
    Write-Host "  ✓ hook 注册到 $settingsPath" -ForegroundColor Green

    # Step 6: 注册 Windows 定时任务（可选）
    Write-Host ""
    if (Confirm "注册每日 03:15 自动归档 session 的 Windows 定时任务？") {
        $syncScriptPath = Join-Path $target "tools\optional-claude-code\sync_sessions.ps1"
        $action = New-ScheduledTaskAction -Execute 'powershell.exe' `
                                          -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$syncScriptPath`""
        $trigger = New-ScheduledTaskTrigger -Daily -At '03:15AM'
        $settingsCfg = New-ScheduledTaskSettingsSet -StartWhenAvailable `
                                                 -DontStopIfGoingOnBatteries `
                                                 -AllowStartIfOnBatteries

        $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settingsCfg `
                                  -Description "Nightly sync of Claude Code sessions to $target\raw\"
        try {
            Register-ScheduledTask -TaskName 'SyncLlmWikiDaily' -InputObject $task -Force | Out-Null
            Write-Host "  ✓ 任务 SyncLlmWikiDaily 注册成功（下次触发：明天 03:15）" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠ 注册失败：$($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "    可手动用 Windows 任务计划程序注册"
        }
    }

} else {
    Write-Host ""
    Write-Host "ⓘ 跳过 Claude Code 自动化（slash commands / SessionEnd hook / 定时任务）" -ForegroundColor DarkCyan
    Write-Host "  这些只对 Claude Code 用户有意义。" -ForegroundColor DarkGray
    Write-Host "  你的 agent 应该会自动加载 $target\AGENTS.md 作为工作规则。" -ForegroundColor DarkGray
}

# ------------------------------------------------------------
# 收尾
# ------------------------------------------------------------
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步："
Write-Host "  1. 打开 Obsidian，Open folder as vault → $target"
Write-Host "  2. 编辑 $target\wiki\about-me.md 写你自己的画像"
Write-Host "  3. 编辑 $target\wiki\jarvis-persona.md 写你和 AI 的约定"
Write-Host "  4. 看一下 wiki/people/_example-* / wiki/projects/_example-* / wiki/decisions/_example-*"
Write-Host "     这是示例文件，看完可删可留"
if ($installClaudeAutomation) {
    Write-Host "  5. 重启 Claude Code 让 slash commands 加载"
    Write-Host "  6. 开始用！下次 session 结束时 hook 会自动归档摘要"
} else {
    Write-Host "  5. 在你的 agent 里打开 $target，让它读 AGENTS.md"
    Write-Host "  6. 开始用！会话结束时让 AI 写一段摘要到 raw/YYYY-MM/"
}
Write-Host ""
Write-Host "强烈建议：把 wiki 推到 GitHub 私有仓做跨设备同步。看 README.md 的「推 GitHub」章节"
Write-Host ""
Write-Host "有问题看 README.md。"
