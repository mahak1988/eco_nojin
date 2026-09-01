#!/usr/bin/env python3
"""
Segment CryptoPaymentWidget.tsx for Refactoring
================================================
Reads the file and creates structured analysis.
"""

import structlog

logger = structlog.get_logger()
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend" / "src"
TARGET = FRONTEND / "pages" / "admin" / "crypto" / "CryptoPaymentWidget.tsx"


def analyze_file(path: Path) -> dict:
    """تحلیل ساختاری فایل"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # شناسایی useState ها
    state_vars = re.findall(
        r'const\s+\[(\w+),\s*set(\w+)\]\s*=\s*useState[^;]*;',
        text
    )

    # شناسایی useEffect ها
    effects = []
    effect_pattern = re.compile(
        r'useEffect\s*\(\s*\(\s*\)\s*=>\s*\{([\s\S]*?)\}\s*,\s*\[([^\]]*)\]',
        re.DOTALL
    )
    for i, match in enumerate(effect_pattern.finditer(text)):
        body = match.group(1)
        deps = match.group(2).strip()
        setstate_calls = re.findall(r'set(\w+)\s*\(', body)
        fetch_calls = len(re.findall(r'\bfetch\s*\(', body)) + len(re.findall(r'\baxios\.', body))
        effects.append({
            "index": i + 1,
            "dependencies": deps or "[]",
            "setState_calls": setstate_calls,
            "fetch_calls": fetch_calls,
            "body_preview": body.strip()[:200],
        })

    # شناسایی Math.random calls
    random_calls = []
    for i, line in enumerate(lines, 1):
        if 'Math.random()' in line:
            random_calls.append({
                "line": i,
                "content": line.strip()[:100],
            })

    # شناسایی imports
    imports = re.findall(
        r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
        text
    )

    return {
        "total_lines": len(lines),
        "state_vars": state_vars,
        "effects": effects,
        "random_calls": random_calls,
        "imports": imports,
        "text": text,
        "lines": lines,
    }


def print_analysis(analysis: dict):
    """چاپ نتایج"""
    logger.info("\n" + "=" * 70)
    logger.info("  📄 ساختار CryptoPaymentWidget.tsx")
    logger.info("=" * 70 + "\n")

    logger.info(f"  📏 تعداد خطوط: {analysis['total_lines']}")
    logger.info()

    # State variables
    logger.info(f"  🎣 State Variables ({len(analysis['state_vars'])}):")
    for name, setter in analysis['state_vars']:
        logger.info(f"      • {name} (set{setter})")
    logger.info()

    # Effects
    logger.info(f"  ⚡ useEffect Hooks ({len(analysis['effects'])}):")
    for effect in analysis['effects']:
        logger.info(f"      ── Effect {effect['index']} ──")
        logger.info(f"      Dependencies: {effect['dependencies']}")
        logger.info(f"      setState calls: {effect['setState_calls']}")
        logger.info(f"      fetch/axios calls: {effect['fetch_calls']}")
        logger.info(f"      Preview: {effect['body_preview'][:100]}...")
        logger.info()

    # Math.random calls
    logger.info(f"  🎲 Math.random() Calls ({len(analysis['random_calls'])}):")
    for call in analysis['random_calls']:
        logger.info(f"      Line {call['line']:4d}: {call['content']}")
    logger.info()

    # Imports
    logger.info(f"  📦 Imports ({len(analysis['imports'])}):")
    for imp in analysis['imports'][:20]:
        logger.info(f"      • {imp}")
    if len(analysis['imports']) > 20:
        logger.info(f"      ... +{len(analysis['imports']) - 20} more")


def save_segments(analysis: dict):
    """ذخیره محتوای فایل به صورت ساختاریافته"""
    output_dir = PROJECT_ROOT / "scripts" / "phase2" / "segments"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ذخیره کل فایل
    full_file = output_dir / "CryptoPaymentWidget_full.tsx"
    full_file.write_text(analysis['text'], encoding='utf-8')

    # ذخیره تحلیل ساختاری
    import json
    analysis_file = output_dir / "CryptoPaymentWidget_analysis.json"
    analysis_data = {
        k: v for k, v in analysis.items()
        if k not in ['text', 'lines']
    }
    analysis_file.write_text(
        json.dumps(analysis_data, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    logger.info(f"\n  💾 فایل‌های ذخیره شده:")
    logger.info(f"      • {full_file.relative_to(PROJECT_ROOT)}")
    logger.info(f"      • {analysis_file.relative_to(PROJECT_ROOT)}")


def main():
    if not TARGET.exists():
        logger.info(f"\033[91m✗\033[0m  فایل یافت نشد: {TARGET}")
        return 1

    logger.info("\n\033[1m🔍 Segmenting CryptoPaymentWidget.tsx...\033[0m\n")

    analysis = analyze_file(TARGET)
    print_analysis(analysis)
    save_segments(analysis)

    # چاپ محتوای خطوط کلیدی
    logger.info("\n" + "=" * 70)
    logger.info("  🎯 اقدام بعدی")
    logger.info("=" * 70 + "\n")

    logger.info("  لطفاً محتوای کامل فایل را بفرستید:")
    logger.info(f"  \033[96mGet-Content {TARGET}\033[0m")
    logger.info()
    logger.info("  سپس من بازنویسی ساختاری را انجام می‌دهم:")
    logger.info("    1. ایجاد features/crypto-payment/")
    logger.info("    2. استخراج types و hooks")
    logger.info("    3. حذف Math.random از render")
    logger.info("    4. جایگزینی useState+useEffect با React Query")
    logger.info("    5. تست‌نویسی")
    logger.info()

    return 0


if __name__ == "__main__":
    sys.exit(main())