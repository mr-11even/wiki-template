"""
lint_wiki.py — Wiki 健康检查

检查：
- 断链：markdown [text](path) 指向不存在的文件
- 过期：frontmatter updated 距今 > 30 天
- 孤立：wiki 里某 md 没被任何其他 wiki md 引用（排除 index / about-me / jarvis-persona / ideas-backlog）
- 缺 frontmatter：md 没有 --- ... --- 块
- sources 引用失效：frontmatter 的 sources: [...] 指向的 raw 文件不存在

用法：
    python lint_wiki.py           # 输出文本报告
    python lint_wiki.py --json    # 输出 JSON（供其他脚本使用）
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import _config

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WIKI_ROOT = _config.wiki_root()
WIKI_DIR = WIKI_ROOT / "wiki"
RAW_DIR = WIKI_ROOT / "raw"

STALE_THRESHOLD_DAYS = 30

# 允许的孤立页（本身就是入口/元页）
ORPHAN_WHITELIST = {
    "index.md",
    "about-me.md",
    "jarvis-persona.md",
    "ideas-backlog.md",
    "README.md",  # 各子目录的说明页
}

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)\)")
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
UPDATED_PATTERN = re.compile(r"^updated:\s*(\S+)\s*$", re.MULTILINE)
SOURCES_PATTERN = re.compile(r"^sources:\s*\[([^\]]*)\]\s*$", re.MULTILINE)


def parse_frontmatter(content: str) -> dict | None:
    m = FRONTMATTER_PATTERN.match(content)
    if not m:
        return None
    fm_text = m.group(1)
    data = {}
    # 简单 yaml 解析（只处理 key: value 和 key: [list]）
    for line in fm_text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def check_broken_links(md_file: Path, content: str) -> list[dict]:
    """检查 md 里的相对链接是否指向存在的文件"""
    issues = []
    for m in LINK_PATTERN.finditer(content):
        text, target = m.group(1), m.group(2)
        # 忽略外部链接 / 锚点
        if target.startswith(("http://", "https://", "#")):
            continue
        # 忽略绝对路径（可能是 F:/... 的硬编码）
        if target.startswith(("F:", "C:", "/", "\\")):
            # 真实存在就 OK，不存在就报
            p = Path(target)
            if not p.exists():
                issues.append({
                    "type": "broken_abs_link",
                    "target": target,
                    "text": text,
                })
            continue
        # 相对路径：从 md_file 所在目录解析
        resolved = (md_file.parent / target).resolve()
        if not resolved.exists():
            issues.append({
                "type": "broken_link",
                "target": target,
                "text": text,
                "resolved": str(resolved),
            })
    return issues


def check_stale(md_file: Path, fm: dict | None) -> dict | None:
    if not fm:
        return None
    updated = fm.get("updated")
    if not updated:
        return None
    try:
        dt = datetime.fromisoformat(updated)
    except ValueError:
        return {"type": "bad_updated_format", "value": updated}
    age = datetime.now() - dt
    if age.days > STALE_THRESHOLD_DAYS:
        return {"type": "stale", "updated": updated, "days": age.days}
    return None


def check_sources(md_file: Path, content: str) -> list[dict]:
    """检查 frontmatter sources: [...] 里引用的 raw 文件是否存在"""
    issues = []
    m = SOURCES_PATTERN.search(content)
    if not m:
        return issues
    sources_str = m.group(1)
    # 粗解析：按逗号切，去引号和空白
    sources = [s.strip().strip('"').strip("'") for s in sources_str.split(",")]
    for src in sources:
        if not src:
            continue
        # 跳过非文件的引用（memorydir 式或 CLAUDE.md-global 等标签）
        if not src.endswith(".md") and not src.endswith(".log"):
            continue
        # 相对于 WIKI_ROOT 解析
        if src.startswith(("F:", "C:", "/", "\\")):
            p = Path(src)
        else:
            p = (WIKI_ROOT / src).resolve()
        if not p.exists():
            issues.append({"type": "missing_source", "source": src})
    return issues


def build_link_graph() -> dict[str, set[str]]:
    """扫 wiki/ 构建"谁引用了谁"的映射: target_relative_path -> set of referring files"""
    referrers = {}
    for md in WIKI_DIR.rglob("*.md"):
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in LINK_PATTERN.finditer(content):
            target = m.group(2)
            if target.startswith(("http://", "https://", "#")):
                continue
            if target.startswith(("F:", "C:", "/", "\\")):
                continue
            resolved = (md.parent / target).resolve()
            try:
                rel = resolved.relative_to(WIKI_DIR)
                key = str(rel).replace("\\", "/")
            except ValueError:
                continue
            referrers.setdefault(key, set()).add(md.name)
    return referrers


def find_orphans(referrers: dict[str, set[str]]) -> list[str]:
    """找 wiki/ 里没被任何其他 md 引用的 md"""
    orphans = []
    for md in WIKI_DIR.rglob("*.md"):
        rel = str(md.relative_to(WIKI_DIR)).replace("\\", "/")
        if md.name in ORPHAN_WHITELIST:
            continue
        if not referrers.get(rel):
            orphans.append(rel)
    return orphans


def lint():
    if not WIKI_DIR.exists():
        print(f"❌ {WIKI_DIR} 不存在")
        return {}

    report = {
        "broken_links": [],
        "stale": [],
        "missing_frontmatter": [],
        "missing_sources": [],
        "orphans": [],
        "bad_updated": [],
    }

    all_md = list(WIKI_DIR.rglob("*.md"))

    for md in all_md:
        rel = str(md.relative_to(WIKI_DIR)).replace("\\", "/")
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            continue

        fm = parse_frontmatter(content)
        if fm is None:
            report["missing_frontmatter"].append({"file": rel})
            continue  # 没 frontmatter 的就不检查其他了

        # Broken links
        for issue in check_broken_links(md, content):
            report["broken_links"].append({"file": rel, **issue})

        # Stale
        stale = check_stale(md, fm)
        if stale and stale["type"] == "stale":
            report["stale"].append({"file": rel, **stale})
        elif stale and stale["type"] == "bad_updated_format":
            report["bad_updated"].append({"file": rel, **stale})

        # Missing sources
        for issue in check_sources(md, content):
            report["missing_sources"].append({"file": rel, **issue})

    # Orphans（需要全局扫描）
    referrers = build_link_graph()
    report["orphans"] = find_orphans(referrers)

    return report


def print_report(report: dict):
    total = (
        len(report["broken_links"])
        + len(report["stale"])
        + len(report["missing_frontmatter"])
        + len(report["missing_sources"])
        + len(report["orphans"])
        + len(report["bad_updated"])
    )
    print(f"# Wiki Lint Report")
    print(f"生成时间: {datetime.now().isoformat()}")
    print(f"Wiki 根: {WIKI_DIR}")
    print(f"")
    print(f"## 总览")
    print(f"- 断链: {len(report['broken_links'])}")
    print(f"- 过期 (>{STALE_THRESHOLD_DAYS}天): {len(report['stale'])}")
    print(f"- 孤立页: {len(report['orphans'])}")
    print(f"- 缺 frontmatter: {len(report['missing_frontmatter'])}")
    print(f"- sources 引用失效: {len(report['missing_sources'])}")
    print(f"- updated 日期格式错: {len(report['bad_updated'])}")
    print(f"- **合计: {total}**")
    print(f"")

    if report["broken_links"]:
        print(f"## 🔗 断链 ({len(report['broken_links'])})")
        for i in report["broken_links"]:
            print(f"  `{i['file']}` → `{i['target']}`  [{i.get('text','')[:30]}]")
        print()

    if report["stale"]:
        print(f"## ⏰ 过期 ({len(report['stale'])})")
        for i in report["stale"]:
            print(f"  `{i['file']}`  updated={i['updated']}  ({i['days']}天前)")
        print()

    if report["orphans"]:
        print(f"## 🏝️ 孤立页 ({len(report['orphans'])})")
        for f in report["orphans"]:
            print(f"  `{f}`")
        print()

    if report["missing_frontmatter"]:
        print(f"## 📋 缺 frontmatter ({len(report['missing_frontmatter'])})")
        for i in report["missing_frontmatter"]:
            print(f"  `{i['file']}`")
        print()

    if report["missing_sources"]:
        print(f"## 📄 sources 引用失效 ({len(report['missing_sources'])})")
        for i in report["missing_sources"]:
            print(f"  `{i['file']}` → `{i['source']}`")
        print()

    if report["bad_updated"]:
        print(f"## ⚠️  updated 日期格式错 ({len(report['bad_updated'])})")
        for i in report["bad_updated"]:
            print(f"  `{i['file']}` updated=`{i['value']}`（应该是 YYYY-MM-DD）")

    if total == 0:
        print("✅ 全部干净。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()
    report = lint()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)
