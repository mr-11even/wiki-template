"""
redact_secrets.py — 扫描并脱敏 raw/ 下的 API key 和敏感值

设计原则：
- 默认 dry-run，只报告，不改文件
- --redact 模式会把原文件复制到 raw-redacted/ 下（平行目录），原 raw/ 保留
- 脱敏是不可逆的（替换成 [REDACTED-TYPE]）
- 发现的 secret 按类型统计 + 脱敏前后 diff 落到 scan_report.md

用法：
    python redact_secrets.py                    # 只扫描，报告到 scan_report.md
    python redact_secrets.py --redact           # 生成 raw-redacted/
    python redact_secrets.py --include-known    # 也脱敏已知的非密钥敏感值（战绩数字、电话等）
    python redact_secrets.py --file <path>      # 只扫一个文件
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

import _config

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WIKI_ROOT = _config.wiki_root()
RAW_DIR = WIKI_ROOT / "raw"
REDACTED_DIR = WIKI_ROOT / "raw-redacted"
REPORT_PATH = WIKI_ROOT / "tools" / "scan_report.md"

# ===========================================================
# Secret 模式库
# ===========================================================
# 每条包含：type（便于归类）、pattern（正则）、placeholder（替换为）
# 顺序重要：更具体的放前面（sk-ant-> sk-）

SECRET_PATTERNS = [
    # Anthropic API key: sk-ant-api03-xxxx
    {
        "type": "anthropic_api_key",
        "pattern": r"sk-ant-[a-zA-Z0-9_\-]{32,}",
        "placeholder": "[REDACTED-ANTHROPIC-KEY]",
    },
    # OpenAI / DeepSeek API key: sk-xxxx (32+ chars alphanumeric)
    {
        "type": "openai_or_deepseek_key",
        "pattern": r"sk-[a-zA-Z0-9]{32,}",
        "placeholder": "[REDACTED-SK-KEY]",
    },
    # Alpaca key: starts with PK + 18 uppercase alnum chars
    {
        "type": "alpaca_key",
        "pattern": r"\bPK[A-Z0-9]{18}\b",
        "placeholder": "[REDACTED-ALPACA-KEY]",
    },
    # Alpaca secret (40+ chars base64-ish)
    # (较难精确匹配，只在附近有 ALPACA_SECRET 字样时触发)
    {
        "type": "alpaca_secret",
        "pattern": r"(ALPACA_SECRET[_A-Z]*[\s=:\"']*)([A-Za-z0-9/+]{30,})",
        "placeholder": r"\1[REDACTED-ALPACA-SECRET]",
        "is_contextual": True,
    },
    # Tavily key: tvly-dev-xxxx or tvly-xxxx
    {
        "type": "tavily_key",
        "pattern": r"tvly-(?:dev-)?[a-zA-Z0-9]{20,}",
        "placeholder": "[REDACTED-TAVILY-KEY]",
    },
    # OKX credentials (通常是 UUID 格式，但 UUID 本身不一定是秘钥；只在附近有 OKX/API_KEY 字样时触发)
    {
        "type": "okx_credential",
        "pattern": r"(OKX_[A-Z_]+|apiKey|secretKey|passphrase)[\s=:\"']*([a-zA-Z0-9\-]{16,})",
        "placeholder": r"\1=[REDACTED-OKX-CRED]",
        "is_contextual": True,
    },
    # 注：如有你个人的固定敏感字符串（如特定 App Secret / 服务器密码 / 授权码）
    # 可在这里增加 literal pattern。留空表示暂无。
]

# 非 API-key 的敏感信息（需要 --include-known 才会脱敏）
KNOWN_SENSITIVE = [
    # 具体手机号（中国大陆 11 位）
    {
        "type": "phone_cn",
        "pattern": r"\b1[3-9]\d{9}\b",
        "placeholder": "[REDACTED-PHONE]",
    },
    # 身份证（18 位）
    {
        "type": "id_cn",
        "pattern": r"\b\d{17}[\dXx]\b",
        "placeholder": "[REDACTED-ID]",
    },
]

# ===========================================================
# 扫描逻辑
# ===========================================================

def scan_file(content: str, patterns) -> list:
    """Return list of (type, match_text, start_pos, line_no)."""
    findings = []
    for rule in patterns:
        flags = re.IGNORECASE if not rule.get("literal") else 0
        for m in re.finditer(rule["pattern"], content, flags=flags):
            start = m.start()
            line_no = content.count("\n", 0, start) + 1
            matched = m.group(0)
            # 过长就截
            preview = matched if len(matched) < 80 else matched[:40] + "..." + matched[-20:]
            findings.append({
                "type": rule["type"],
                "match": preview,
                "line": line_no,
            })
    return findings


def redact_content(content: str, patterns) -> tuple[str, int]:
    """Return (redacted_content, num_replacements)."""
    total = 0
    for rule in patterns:
        flags = re.IGNORECASE if not rule.get("literal") else 0
        if rule.get("is_contextual"):
            # 带 backref 的替换（保留 context 前缀）
            new_content, n = re.subn(rule["pattern"], rule["placeholder"], content, flags=flags)
        else:
            new_content, n = re.subn(rule["pattern"], rule["placeholder"], content, flags=flags)
        if n > 0:
            total += n
            content = new_content
    return content, total


def walk_raw(include_known: bool = False):
    """迭代 raw/ 下所有文件（不含 raw-redacted/），返回 (path, content, findings)"""
    if not RAW_DIR.exists():
        print(f"❌ {RAW_DIR} 不存在")
        return

    patterns = SECRET_PATTERNS + (KNOWN_SENSITIVE if include_known else [])

    for f in RAW_DIR.rglob("*"):
        if not f.is_file():
            continue
        # 跳过二进制
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf", ".docx", ".xlsx", ".zip"}:
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"⚠️  读不了 {f}: {e}")
            continue
        findings = scan_file(content, patterns)
        yield f, content, findings


def do_scan(include_known: bool):
    """扫描 + 生成报告，不改文件。"""
    print(f"🔍 扫描 {RAW_DIR} ...\n")

    stats_by_type = {}
    stats_by_file = {}
    total_findings = 0
    scanned_files = 0

    for path, _, findings in walk_raw(include_known):
        scanned_files += 1
        if findings:
            rel = path.relative_to(WIKI_ROOT)
            stats_by_file[str(rel)] = len(findings)
            for fd in findings:
                stats_by_type[fd["type"]] = stats_by_type.get(fd["type"], 0) + 1
                total_findings += 1

    # 打印 + 写报告
    lines = [
        "# raw/ 敏感信息扫描报告",
        f"生成时间: {__import__('datetime').datetime.now().isoformat()}",
        f"包含非 API-key 敏感项: {include_known}",
        "",
        f"## 总览",
        f"- 扫描文件数: {scanned_files}",
        f"- 发现敏感项次数（含重复）: {total_findings}",
        f"- 涉及文件数: {len(stats_by_file)}",
        "",
        "## 按类型统计",
    ]
    for t, n in sorted(stats_by_type.items(), key=lambda x: -x[1]):
        lines.append(f"- **{t}**: {n} 次")
    lines.append("")
    lines.append("## 按文件排名 (top 20)")
    lines.append("| 文件 | 命中次数 |")
    lines.append("|---|---|")
    for path, n in sorted(stats_by_file.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"| `{path}` | {n} |")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    for line in lines:
        print(line)
    print(f"\n📄 完整报告: {REPORT_PATH}")


def do_redact(include_known: bool):
    """生成 raw-redacted/ 镜像目录（复制原结构 + 脱敏）"""
    patterns = SECRET_PATTERNS + (KNOWN_SENSITIVE if include_known else [])

    print(f"🛡️  生成脱敏镜像 {REDACTED_DIR} ...\n")

    files_written = 0
    total_replacements = 0

    for path, content, _ in walk_raw(include_known):
        redacted, n = redact_content(content, patterns)
        rel = path.relative_to(RAW_DIR)
        dest = REDACTED_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(redacted, encoding="utf-8")
        files_written += 1
        total_replacements += n

    print(f"✅ {files_written} 个文件已脱敏复制到 {REDACTED_DIR}")
    print(f"📝 总替换次数: {total_replacements}")
    print(f"\n⚠️  下一步:")
    print(f"   1. 人工抽检 {REDACTED_DIR} 确认没漏")
    print(f"   2. 如要 git，只把 raw-redacted/ 和 wiki/ + schema.md + CLAUDE.md 入版本")
    print(f"   3. 原 raw/ 保持本地永不入版本控制")


def do_scan_single(file_path: str, include_known: bool):
    patterns = SECRET_PATTERNS + (KNOWN_SENSITIVE if include_known else [])
    p = Path(file_path)
    if not p.exists():
        print(f"❌ {p} 不存在")
        return
    content = p.read_text(encoding="utf-8", errors="replace")
    findings = scan_file(content, patterns)
    if not findings:
        print(f"✅ {p}: 干净")
        return
    print(f"⚠️  {p}: {len(findings)} 处敏感")
    for fd in findings:
        print(f"  line {fd['line']:5d}  [{fd['type']:25s}]  {fd['match']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--redact", action="store_true", help="实际生成 raw-redacted/（默认只扫描）")
    ap.add_argument("--include-known", action="store_true", help="也脱敏非 API-key 敏感信息")
    ap.add_argument("--file", help="只扫描一个文件")
    args = ap.parse_args()

    if args.file:
        do_scan_single(args.file, args.include_known)
    elif args.redact:
        do_redact(args.include_known)
    else:
        do_scan(args.include_known)
