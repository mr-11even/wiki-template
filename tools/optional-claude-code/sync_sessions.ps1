# sync_sessions.ps1 - nightly Claude Code session archive
# Called by Windows Task Scheduler: SyncLlmWikiDaily
# Uses $PSScriptRoot to avoid hardcoded non-ASCII paths (PowerShell 5 UTF-8 bug)

$ErrorActionPreference = "Continue"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$tools = $PSScriptRoot
$logdir = Join-Path $tools "logs"
if (-not (Test-Path $logdir)) { New-Item -ItemType Directory -Path $logdir -Force | Out-Null }

$ym = Get-Date -Format "yyyy-MM"
$logfile = Join-Path $logdir "sync_$ym.log"

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logfile -Value "" -Encoding utf8
Add-Content -Path $logfile -Value "========================================" -Encoding utf8
Add-Content -Path $logfile -Value "[$ts] sync started" -Encoding utf8

# Run with UTF-8 to avoid GBK encoding issues on Chinese Windows
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$script = Join-Path $tools "sync_sessions.py"
& python $script 2>&1 | Out-File -FilePath $logfile -Append -Encoding utf8

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logfile -Value "[$ts] sync finished" -Encoding utf8
