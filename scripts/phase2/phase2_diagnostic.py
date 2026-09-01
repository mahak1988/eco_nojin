#!/usr/bin/env python3
"""
Phase 2 - Diagnostic Tool
==========================
Deep analysis of 7 target files with anti-React patterns.

For each file, detects:
- useEffect with setState (data fetching anti-pattern)
- Math.random() in render body
- fetch/axios without cleanup
- any types
- console.log statements
- missing loading/error states
- inline styles count
- import complexity

Outputs:
- Console report (human-readable)
- JSON file (for next scripts)
- Priority ranking
"""

import structlog

logger = structlog.get_logger()
import re
import json
import sys
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend" / "src"

# 7 target files (will be searched in src/)
TARGET_FILES = [
    "pages/ContentStudio.tsx",
    "pages/EcoWalletDashboard.tsx",
    "pages/MarketplaceDashboard.tsx",
    "pages/SecurityAdvanced.tsx",
    "components/CryptoPaymentWidget.tsx",
    "components/LiveFeed.tsx",
    "components/TelegramManager.tsx",
]

# Alternative paths to try
ALT_PATHS = [
    FRONTEND,
    FRONTEND / "pages",
    FRONTEND / "components",
    FRONTEND / "features",
]


class C:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def ok(m): print(f"{C.GREEN}✓{C.RESET}  {m}")
def info(m): print(f"{C.BLUE}ℹ{C.RESET}  {m}")
def warn(m): print(f"{C.YELLOW}⚠{C.RESET}  {m}")
def err(m): print(f"{C.RED}✗{C.RESET}  {m}")
def header(m):
    logger.info(f"\n{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}")
    logger.info(f"{C.BOLD}{C.CYAN}  {m}{C.RESET}")
    logger.info(f"{C.BOLD}{C.CYAN}{'═' * 70}{C.RESET}\n")


def find_file(rel_path: str) -> Path | None:
    """یافتن فایل در مسیرهای مختلف"""
    # مسیر مستقیم
    direct = FRONTEND / rel_path
    if direct.exists():
        return direct

    # جستجو بر اساس نام فایل
    filename = Path(rel_path).name
    for base in ALT_PATHS:
        if not base.exists():
            continue
        # جستجوی recursive
        matches = list(base.rglob(filename))
        if matches:
            return matches[0]

    return None


def analyze_file(file_path: Path) -> dict:
    """تحلیل عمیق یک فایل"""
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    analysis = {
        "file": str(file_path.relative_to(PROJECT_ROOT)),
        "filename": file_path.name,
        "total_lines": len(lines),
        "total_chars": len(text),
        "issues": [],
        "severity_score": 0,
        "priority": "low",
    }

    # ─────────────────────────────────────────
    # 1. شمارش hooks
    # ─────────────────────────────────────────
    use_state_count = len(re.findall(r'\buseState\s*[<(]', text))
    use_effect_count = len(re.findall(r'\buseEffect\s*\(', text))
    use_memo_count = len(re.findall(r'\buseMemo\s*\(', text))
    use_callback_count = len(re.findall(r'\buseCallback\s*\(', text))
    use_query_count = len(re.findall(r'\buseQuery\s*[<(]', text))
    use_mutation_count = len(re.findall(r'\buseMutation\s*[<(]', text))

    analysis["hooks"] = {
        "useState": use_state_count,
        "useEffect": use_effect_count,
        "useMemo": use_memo_count,
        "useCallback": use_callback_count,
        "useQuery": use_query_count,
        "useMutation": use_mutation_count,
    }

    # ─────────────────────────────────────────
    # 2. شناسایی anti-patterns
    # ─────────────────────────────────────────

    # Anti-pattern 1: setState inside useEffect
    # الگو: useEffect(() => { ... setSomething(...) ... })
    effect_blocks = re.findall(
        r'useEffect\s*\(\s*\(\s*\)\s*=>\s*\{([\s\S]*?)\}\s*,\s*\[',
        text
    )
    setstate_in_effect = 0
    for block in effect_blocks:
        setstate_matches = re.findall(r'\bset[A-Z]\w*\s*\(', block)
        setstate_in_effect += len(setstate_matches)

    if setstate_in_effect > 0:
        analysis["issues"].append({
            "type": "setState_in_useEffect",
            "count": setstate_in_effect,
            "severity": "high",
            "description": f"{setstate_in_effect} setState call(s) inside useEffect",
            "solution": "Use React Query (useQuery) for data fetching",
        })
        analysis["severity_score"] += setstate_in_effect * 10

    # Anti-pattern 2: Math.random() in render body
    # اگر Math.random خارج از useCallback/useMemo باشد
    math_random_count = len(re.findall(r'Math\.random\s*\(', text))
    if math_random_count > 0:
        # بررسی اینکه آیا در useMemo/useCallback هست یا نه
        # ساده‌سازی: اگر تعداد useState/useMemo کم است، احتمالاً مشکل دارد
        if use_memo_count < math_random_count:
            analysis["issues"].append({
                "type": "Math_random_in_render",
                "count": math_random_count,
                "severity": "high",
                "description": f"{math_random_count} Math.random() call(s) - may cause non-deterministic renders",
                "solution": "Wrap in useMemo or use seed-based random",
            })
            analysis["severity_score"] += math_random_count * 15

    # Anti-pattern 3: fetch/axios بدون cleanup
    fetch_count = len(re.findall(r'\bfetch\s*\(', text))
    axios_count = len(re.findall(r'\baxios\.', text))
    has_abort_controller = 'AbortController' in text
    has_cleanup = re.search(r'return\s*\(\s*\)\s*=>', text) is not None

    if (fetch_count > 0 or axios_count > 0) and not has_abort_controller:
        analysis["issues"].append({
            "type": "fetch_without_abort",
            "count": fetch_count + axios_count,
            "severity": "medium",
            "description": f"{fetch_count + axios_count} fetch/axios call(s) without AbortController",
            "solution": "Use AbortController or React Query's automatic cancellation",
        })
        analysis["severity_score"] += (fetch_count + axios_count) * 5

    # Anti-pattern 4: WebSocket/EventSource بدون cleanup
    websocket_count = len(re.findall(r'new\s+WebSocket\s*\(', text))
    eventsource_count = len(re.findall(r'new\s+EventSource\s*\(', text))
    if (websocket_count > 0 or eventsource_count > 0) and not has_cleanup:
        analysis["issues"].append({
            "type": "subscription_without_cleanup",
            "count": websocket_count + eventsource_count,
            "severity": "high",
            "description": f"{websocket_count + eventsource_count} subscription(s) without cleanup",
            "solution": "Add cleanup function in useEffect return",
        })
        analysis["severity_score"] += (websocket_count + eventsource_count) * 20

    # Anti-pattern 5: any types
    any_count = len(re.findall(r':\s*any\b', text))
    if any_count > 0:
        analysis["issues"].append({
            "type": "any_types",
            "count": any_count,
            "severity": "medium",
            "description": f"{any_count} 'any' type(s) - weakens type safety",
            "solution": "Define proper TypeScript interfaces",
        })
        analysis["severity_score"] += any_count * 2

    # Anti-pattern 6: console.log
    console_count = len(re.findall(r'console\.(log|warn|error|debug|info)', text))
    if console_count > 5:
        analysis["issues"].append({
            "type": "excessive_console",
            "count": console_count,
            "severity": "low",
            "description": f"{console_count} console.* call(s)",
            "solution": "Use proper logging service or remove",
        })
        analysis["severity_score"] += console_count

    # Anti-pattern 7: inline styles
    inline_styles = len(re.findall(r'style\s*=\s*\{\{', text))
    if inline_styles > 30:
        analysis["issues"].append({
            "type": "excessive_inline_styles",
            "count": inline_styles,
            "severity": "low",
            "description": f"{inline_styles} inline style object(s)",
            "solution": "Extract to CSS modules or Tailwind classes",
        })
        analysis["severity_score"] += inline_styles // 10

    # Anti-pattern 8: missing loading/error states
    has_loading = 'loading' in text.lower() or 'isLoading' in text
    has_error = 'error' in text.lower() or 'isError' in text
    if (fetch_count > 0 or axios_count > 0) and not (has_loading and has_error):
        analysis["issues"].append({
            "type": "missing_loading_error_states",
            "count": 1,
            "severity": "medium",
            "description": "Data fetching without proper loading/error states",
            "solution": "Add loading spinner and error boundary",
        })
        analysis["severity_score"] += 10

    # ─────────────────────────────────────────
    # 3. تعیین اولویت
    # ─────────────────────────────────────────
    score = analysis["severity_score"]
    if score >= 50:
        analysis["priority"] = "critical"
    elif score >= 25:
        analysis["priority"] = "high"
    elif score >= 10:
        analysis["priority"] = "medium"
    else:
        analysis["priority"] = "low"

    # ─────────────────────────────────────────
    # 4. imports و dependencies
    # ─────────────────────────────────────────
    imports = re.findall(
        r"import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]",
        text
    )
    analysis["imports_count"] = len(imports)
    analysis["external_deps"] = list(set(
        imp.split('/')[0] if not imp.startswith('.') and not imp.startswith('@')
        else '/'.join(imp.split('/')[:2]) if imp.startswith('@')
        else imp
        for imp in imports
    ))

    return analysis


def print_analysis(analysis: dict):
    """چاپ نتایج تحلیل یک فایل"""
    # رنگ بر اساس اولویت
    priority_colors = {
        "critical": C.RED,
        "high": C.MAGENTA,
        "medium": C.YELLOW,
        "low": C.GREEN,
    }
    color = priority_colors.get(analysis["priority"], C.RESET)

    logger.info(f"\n{C.BOLD}📄 {analysis['filename']}{C.RESET}")
    logger.info(f"   مسیر: {analysis['file']}")
    logger.info(f"   خطوط: {analysis['total_lines']:,} | کاراکترها: {analysis['total_chars']:,}")
    logger.info(f"   {C.BOLD}اولویت:{C.RESET} {color}{analysis['priority'].upper()}{C.RESET} (امتیاز: {analysis['severity_score']})")

    # hooks
    hooks = analysis["hooks"]
    print(f"   {C.BOLD}Hooks:{C.RESET} useState={hooks['useState']} useEffect={hooks['useEffect']} "
          f"useMemo={hooks['useMemo']} useQuery={hooks['useQuery']}")

    # issues
    if analysis["issues"]:
        logger.info(f"   {C.BOLD}مشکلات ({len(analysis['issues'])}):{C.RESET}")
        for issue in analysis["issues"]:
            sev_color = {
                "high": C.RED,
                "medium": C.YELLOW,
                "low": C.BLUE,
            }.get(issue["severity"], C.RESET)
            logger.info(f"      {sev_color}●{C.RESET} [{issue['severity']}] {issue['description']}")
            logger.info(f"        {C.GREEN}→ {issue['solution']}{C.RESET}")
    else:
        logger.info(f"   {C.GREEN}✓ هیچ مشکل مهمی یافت نشد{C.RESET}")


def main():
    logger.info(f"\n{C.BOLD}{'═' * 70}{C.RESET}")
    logger.info(f"{C.BOLD}  🔬 Phase 2 - Diagnostic Tool{C.RESET}")
    logger.info(f"{C.BOLD}{'═' * 70}{C.RESET}")
    logger.info(f"\n{C.BOLD}هدف:{C.RESET} تحلیل عمیق ۷ فایل با الگوهای ضد React")
    logger.info(f"{C.BOLD}خروجی:{C.RESET} گزارش کنسول + فایل JSON برای اسکریپت‌های بعدی\n")

    analyses = []
    not_found = []

    # تحلیل هر فایل
    for rel_path in TARGET_FILES:
        file_path = find_file(rel_path)
        if not file_path:
            warn(f"فایل یافت نشد: {rel_path}")
            not_found.append(rel_path)
            continue

        info(f"تحلیل: {file_path.name}")
        analysis = analyze_file(file_path)
        analyses.append(analysis)

    if not analyses:
        err("هیچ فایلی برای تحلیل یافت نشد!")
        err(f"مسیرهای جستجو شده: {[str(p) for p in ALT_PATHS]}")
        return 1

    # مرتب‌سازی بر اساس اولویت
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    analyses.sort(key=lambda a: (priority_order.get(a["priority"], 4), -a["severity_score"]))

    # چاپ گزارش تفصیلی
    header("📋 گزارش تفصیلی فایل‌ها")
    for analysis in analyses:
        print_analysis(analysis)

    # خلاصه آماری
    header("📊 خلاصه آماری")

    total_issues = sum(len(a["issues"]) for a in analyses)
    total_lines = sum(a["total_lines"] for a in analyses)
    priority_counts = {
        "critical": sum(1 for a in analyses if a["priority"] == "critical"),
        "high": sum(1 for a in analyses if a["priority"] == "high"),
        "medium": sum(1 for a in analyses if a["priority"] == "medium"),
        "low": sum(1 for a in analyses if a["priority"] == "low"),
    }

    logger.info(f"  {C.BOLD}تعداد فایل‌های تحلیل شده:{C.RESET} {len(analyses)}")
    logger.info(f"  {C.BOLD}مجموع خطوط:{C.RESET} {total_lines:,}")
    logger.info(f"  {C.BOLD}مجموع مشکلات:{C.RESET} {total_issues}")
    logger.info()
    logger.info(f"  {C.BOLD}توزیع اولویت:{C.RESET}")
    logger.info(f"    {C.RED}● Critical:{C.RESET} {priority_counts['critical']}")
    logger.info(f"    {C.MAGENTA}● High:{C.RESET}     {priority_counts['high']}")
    logger.info(f"    {C.YELLOW}● Medium:{C.RESET}   {priority_counts['medium']}")
    logger.info(f"    {C.GREEN}● Low:{C.RESET}      {priority_counts['low']}")

    if not_found:
        logger.info()
        warn(f"فایل‌های یافت نشده ({len(not_found)}):")
        for f in not_found:
            logger.info(f"    ✗ {f}")

    # ذخیره JSON
    header("💾 ذخیره نتایج")

    output_dir = PROJECT_ROOT / "scripts" / "phase2"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = output_dir / f"diagnostic_{timestamp}.json"

    output_data = {
        "timestamp": timestamp,
        "total_files": len(analyses),
        "total_lines": total_lines,
        "total_issues": total_issues,
        "priority_counts": priority_counts,
        "not_found": not_found,
        "analyses": analyses,
    }

    json_file.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    ok(f"JSON ذخیره شد: {json_file.relative_to(PROJECT_ROOT)}")

    # همچنین یک latest copy
    latest_file = output_dir / "diagnostic_latest.json"
    latest_file.write_text(
        json.dumps(output_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    ok(f"Latest copy: {latest_file.relative_to(PROJECT_ROOT)}")

    # پیشنهاد برنامه
    header("🎯 برنامه پیشنهادی فاز ۲")

    logger.info(f"  {C.BOLD}ترتیب پیشنهادی بازنویسی:{C.RESET}\n")
    for i, analysis in enumerate(analyses, 1):
        priority_colors = {
            "critical": C.RED,
            "high": C.MAGENTA,
            "medium": C.YELLOW,
            "low": C.GREEN,
        }
        color = priority_colors.get(analysis["priority"], C.RESET)
        print(f"  {i}. {color}[{analysis['priority'].upper()}]{C.RESET} "
              f"{analysis['filename']} ({analysis['total_lines']} lines, "
              f"{len(analysis['issues'])} issues)")

        # نمایش اولین راه‌حل
        if analysis["issues"]:
            logger.info(f"     {C.GREEN}→ {analysis['issues'][0]['solution']}{C.RESET}")

    logger.info()
    logger.info(f"  {C.BOLD}تخمین زمان:{C.RESET}")
    logger.info(f"    • Critical files: 2 days each")
    logger.info(f"    • High files: 1-2 days each")
    logger.info(f"    • Medium files: 1 day each")
    logger.info(f"    • Low files: 0.5 day each")
    logger.info()

    # اقدام بعدی
    logger.info(f"{C.BOLD}{'═' * 70}{C.RESET}")
    logger.info(f"{C.GREEN}{C.BOLD}  ✅ Diagnostic کامل شد!{C.RESET}")
    logger.info(f"{C.BOLD}{'═' * 70}{C.RESET}\n")

    logger.info(f"  {C.BOLD}اقدام بعدی:{C.RESET}")
    logger.info(f"  1. نتایج بالا را بررسی کنید")
    logger.info(f"  2. اگر با اولویت‌بندی موافقید، بفرمایید:")
    logger.info(f"     {C.CYAN}'شروع بازنویسی [filename].tsx'{C.RESET}")
    logger.info(f"  3. یا اگر فایل دیگری اولویت دارد، مشخص کنید")
    logger.info()

    return 0


if __name__ == "__main__":
    sys.exit(main())