# extract_session.ps1 — SessionEnd hook wrapper
# 从 stdin 读 JSON (含 session_id + cwd)，异步后台跑 Python 提炼，立即退出
# 全程带调试日志，失败可查

$ErrorActionPreference = "SilentlyContinue"

$logDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$hookLog = Join-Path $logDir "hook_trigger.log"

function Write-HookLog($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $hookLog -Value "[$ts] $msg" -Encoding utf8 -ErrorAction SilentlyContinue
}

try {
    Write-HookLog "hook invoked"

    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) {
        Write-HookLog "empty stdin, exit"
        exit 0
    }
    Write-HookLog ("stdin len=" + $raw.Length)

    # 注意：不要用 $input 这个自动变量名
    try {
        # 注意：必须用 -InputObject，PS5 的 `$raw | ConvertFrom-Json` 在某些情况下会返回空对象
        $payload = ConvertFrom-Json -InputObject $raw -ErrorAction Stop
    } catch {
        Write-HookLog ("ConvertFrom-Json failed: " + $_.Exception.Message)
        exit 0
    }

    $sessionId = $payload.session_id
    $cwd = $payload.cwd

    if (-not $sessionId -or -not $cwd) {
        Write-HookLog ("missing session_id or cwd, skip. sid='" + $sessionId + "' cwd='" + $cwd + "'")
        exit 0
    }
    Write-HookLog "session_id=$sessionId cwd=$cwd"

    $scriptPath = Join-Path $PSScriptRoot "extract_session.py"
    $pyStdout = Join-Path $logDir "extract_py_stdout.log"
    $pyStderr = Join-Path $logDir "extract_py_stderr.log"

    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUTF8 = "1"

    # 异步启动 Python，不等待
    $proc = Start-Process -FilePath "python" `
                          -ArgumentList @($scriptPath, $sessionId, $cwd) `
                          -WindowStyle Hidden `
                          -WorkingDirectory $PSScriptRoot `
                          -RedirectStandardOutput $pyStdout `
                          -RedirectStandardError $pyStderr `
                          -PassThru

    if ($proc) {
        Write-HookLog ("python spawned pid=" + $proc.Id)
    } else {
        Write-HookLog "Start-Process returned null"
    }
} catch {
    Write-HookLog ("exception: " + $_.Exception.Message)
}

exit 0
