#!/usr/bin/env python3
"""
Segment CryptoPaymentWidget.tsx for Refactoring
================================================
Reads the file and creates structured analysis.
"""

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
    print("\n" + "=" * 70)
    print("  📄 ساختار CryptoPaymentWidget.tsx")
    print("=" * 70 + "\n")

    print(f"  📏 تعداد خطوط: {analysis['total_lines']}")
    print()

    # State variables
    print(f"  🎣 State Variables ({len(analysis['state_vars'])}):")
    for name, setter in analysis['state_vars']:
        print(f"      • {name} (set{setter})")
    print()

    # Effects
    print(f"  ⚡ useEffect Hooks ({len(analysis['effects'])}):")
    for effect in analysis['effects']:
        print(f"      ── Effect {effect['index']} ──")
        print(f"      Dependencies: {effect['dependencies']}")
        print(f"      setState calls: {effect['setState_calls']}")
        print(f"      fetch/axios calls: {effect['fetch_calls']}")
        print(f"      Preview: {effect['body_preview'][:100]}...")
        print()

    # Math.random calls
    print(f"  🎲 Math.random() Calls ({len(analysis['random_calls'])}):")
    for call in analysis['random_calls']:
        print(f"      Line {call['line']:4d}: {call['content']}")
    print()

    # Imports
    print(f"  📦 Imports ({len(analysis['imports'])}):")
    for imp in analysis['imports'][:20]:
        print(f"      • {imp}")
    if len(analysis['imports']) > 20:
        print(f"      ... +{len(analysis['imports']) - 20} more")


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

    print(f"\n  💾 فایل‌های ذخیره شده:")
    print(f"      • {full_file.relative_to(PROJECT_ROOT)}")
    print(f"      • {analysis_file.relative_to(PROJECT_ROOT)}")


def main():
    if not TARGET.exists():
        print(f"\033[91m✗\033[0m  فایل یافت نشد: {TARGET}")
        return 1

    print("\n\033[1m🔍 Segmenting CryptoPaymentWidget.tsx...\033[0m\n")

    analysis = analyze_file(TARGET)
    print_analysis(analysis)
    save_segments(analysis)

    # چاپ محتوای خطوط کلیدی
    print("\n" + "=" * 70)
    print("  🎯 اقدام بعدی")
    print("=" * 70 + "\n")

    print("  لطفاً محتوای کامل فایل را بفرستید:")
    print(f"  \033[96mGet-Content {TARGET}\033[0m")
    print()
    print("  سپس من بازنویسی ساختاری را انجام می‌دهم:")
    print("    1. ایجاد features/crypto-payment/")
    print("    2. استخراج types و hooks")
    print("    3. حذف Math.random از render")
    print("    4. جایگزینی useState+useEffect با React Query")
    print("    5. تست‌نویسی")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())