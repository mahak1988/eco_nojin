#!/usr/bin/env python3
"""
Segment File for Analysis
==========================
فایل بزرگ را به قطعات قابل مدیریت تقسیم می‌کند
و اطلاعات ساختاری آن را استخراج می‌کند.

استفاده:
  python scripts/phase1/segment_file.py <path-to-file> [segment-size]

مثال:
  python scripts/phase1/segment_file.py frontend/src/pages/HyDroMaCenter.tsx 500
"""

import structlog

logger = structlog.get_logger()
import re
import sys
from pathlib import Path
from collections import Counter


def analyze_file(file_path: Path) -> dict:
    """تحلیل ساختار فایل"""
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    analysis = {
        "total_lines": len(lines),
        "total_chars": len(text),
        "imports": [],
        "hooks_used": [],
        "components_defined": [],
        "state_variables": [],
        "effects": [],
        "functions": [],
        "any_types": 0,
        "console_logs": 0,
        "jsx_depth_max": 0,
        "dependencies": set(),
        "errors": [],
    }

    # شمارش imports
    import_pattern = re.compile(
        r"^import\s+(?:.*?\s+from\s+)?['\"]([^'\"]+)['\"]", re.MULTILINE
    )
    for match in import_pattern.finditer(text):
        analysis["imports"].append(match.group(1))

    # شمارش hooks
    hooks = ["useState", "useEffect", "useMemo", "useCallback", "useRef",
             "useQuery", "useMutation", "useNavigate", "useParams"]
    for hook in hooks:
        count = len(re.findall(rf"\b{hook}\s*\(", text))
        if count > 0:
            analysis["hooks_used"].append((hook, count))

    # state variables
    state_pattern = re.compile(
        r"const\s+\[\s*(\w+)\s*,\s*set(\w+)\s*\]\s*=\s*useState"
    )
    for match in state_pattern.finditer(text):
        analysis["state_variables"].append(match.group(1))

    # effects
    analysis["effects"] = len(re.findall(r"useEffect\s*\(", text))

    # functions
    func_pattern = re.compile(
        r"(?:const|let|function)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*(?:=>|:)"
    )
    for match in func_pattern.finditer(text):
        analysis["functions"].append(match.group(1))

    # components (PascalCase function names)
    comp_pattern = re.compile(r"(?:const|function)\s+([A-Z][a-zA-Z0-9]+)\s*=")
    for match in comp_pattern.finditer(text):
        name = match.group(1)
        if name not in ["React", "Promise", "Error"]:
            analysis["components_defined"].append(name)

    # any types
    analysis["any_types"] = len(re.findall(r":\s*any\b", text))

    # console.log
    analysis["console_logs"] = len(re.findall(r"console\.", text))

    # JSX nesting depth (approximate)
    current_depth = 0
    max_depth = 0
    for char in text:
        if char == '{':
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char == '}':
            current_depth -= 1
    analysis["jsx_depth_max"] = max_depth

    # dependencies from imports
    for imp in analysis["imports"]:
        if not imp.startswith('.') and not imp.startswith('@'):
            pkg = imp.split('/')[0]
            if pkg and pkg[0] != '/':
                analysis["dependencies"].add(pkg)
        elif imp.startswith('@'):
            parts = imp.split('/')
            if len(parts) >= 2:
                analysis["dependencies"].add(f"{parts[0]}/{parts[1]}")

    # تشخیص خطاهای احتمالی
    if analysis["total_lines"] > 500:
        analysis["errors"].append(f"⚠️ God Component: {analysis['total_lines']} lines")
    if analysis["any_types"] > 5:
        analysis["errors"].append(f"⚠️ {analysis['any_types']} استفاده از 'any'")
    if analysis["state_variables"] and len(analysis["state_variables"]) > 10:
        analysis["errors"].append(f"⚠️ {len(analysis['state_variables'])} state variable - نیاز به store")
    if analysis["effects"] > 5:
        analysis["errors"].append(f"⚠️ {analysis['effects']} useEffect - احتمال anti-pattern")

    return analysis


def print_analysis(analysis: dict, file_path: Path):
    """چاپ نتایج تحلیل"""
    logger.info("=" * 70)
    logger.info(f"  📊 تحلیل ساختاری فایل")
    logger.info("=" * 70)
    logger.info(f"\n  📄 فایل: {file_path.name}")
    logger.info(f"  📏 مسیر: {file_path}")
    logger.info(f"\n  ─────────────────────────────────────")
    logger.info(f"  📐 تعداد خطوط:     {analysis['total_lines']:,}")
    logger.info(f"  📦 حجم:            {analysis['total_chars']:,} کاراکتر")
    logger.info(f"  🧩 عمق JSX:        {analysis['jsx_depth_max']}")

    logger.info(f"\n  ─────────────────────────────────────")
    logger.info(f"  📥 Imports:        {len(analysis['imports'])}")
    logger.info(f"  🎣 Hooks:          {sum(c for _, c in analysis['hooks_used'])}")
    logger.info(f"  🧩 Components:     {len(analysis['components_defined'])}")
    logger.info(f"  💾 State vars:     {len(analysis['state_variables'])}")
    logger.info(f"  ⚡ Effects:        {analysis['effects']}")
    logger.info(f"  🔧 Functions:      {len(analysis['functions'])}")

    logger.info(f"\n  ─────────────────────────────────────")
    logger.info(f"  ⚠️  any types:      {analysis['any_types']}")
    logger.info(f"  📢 console.*:      {analysis['console_logs']}")

    if analysis["hooks_used"]:
        logger.info(f"\n  ─────────────────────────────────────")
        logger.info(f"  🎣 Hooks استفاده شده:")
        for hook, count in sorted(analysis["hooks_used"], key=lambda x: -x[1]):
            logger.info(f"      • {hook}: {count}")

    if analysis["components_defined"]:
        logger.info(f"\n  ─────────────────────────────────────")
        logger.info(f"  🧩 Components تعریف شده:")
        for comp in analysis["components_defined"][:15]:
            logger.info(f"      • {comp}")
        if len(analysis["components_defined"]) > 15:
            logger.info(f"      ... و {len(analysis['components_defined']) - 15} دیگر")

    if analysis["state_variables"]:
        logger.info(f"\n  ─────────────────────────────────────")
        logger.info(f"  💾 State variables:")
        for state in analysis["state_variables"][:15]:
            logger.info(f"      • {state}")
        if len(analysis["state_variables"]) > 15:
            logger.info(f"      ... و {len(analysis['state_variables']) - 15} دیگر")

    if analysis["dependencies"]:
        logger.info(f"\n  ─────────────────────────────────────")
        logger.info(f"  📦 External dependencies ({len(analysis['dependencies'])}):")
        for dep in sorted(analysis["dependencies"])[:20]:
            logger.info(f"      • {dep}")

    if analysis["errors"]:
        logger.info(f"\n  ─────────────────────────────────────")
        logger.info(f"  🚨 مشکلات شناسایی شده:")
        for err in analysis["errors"]:
            logger.info(f"      {err}")

    logger.info("\n" + "=" * 70)


def segment_file(file_path: Path, segment_size: int = 500):
    """تقسیم فایل به قطعات"""
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    total_lines = len(lines)

    num_segments = (total_lines + segment_size - 1) // segment_size

    logger.info(f"\n  ─────────────────────────────────────")
    logger.info(f"  📤 برنامه ارسال محتوا:")
    logger.info(f"  ─────────────────────────────────────")
    logger.info(f"  تعداد کل خطوط: {total_lines}")
    logger.info(f"  اندازه هر قطعه: {segment_size}")
    logger.info(f"  تعداد قطعات: {num_segments}")
    logger.info()

    segments_dir = file_path.parent / f".segments_{file_path.stem}"
    segments_dir.mkdir(exist_ok=True)

    for i in range(num_segments):
        start = i * segment_size + 1
        end = min((i + 1) * segment_size, total_lines)
        segment_lines = lines[i * segment_size : (i + 1) * segment_size]
        segment_text = "\n".join(segment_lines)

        segment_file = segments_dir / f"segment_{i+1:02d}_lines_{start}-{end}.txt"
        header = f"""{'=' * 70}
SEGMENT {i+1}/{num_segments} | Lines {start}-{end}
FILE: {file_path.name}
{'=' * 70}

"""
        segment_file.write_text(header + segment_text, encoding="utf-8")

        logger.info(f"  ✓ {segment_file.name}")

    logger.info(f"\n  📂 همه قطعات در: {segments_dir}")
    logger.info(f"\n  💡 حالا هر قطعه را یکی‌یکی برایم ارسال کنید")
    logger.info(f"     یا اگر ترجیح می‌دهید، فایل اصلی را یکجا بفرستید")


def main():
    if len(sys.argv) < 2:
        logger.info("Usage: python segment_file.py <file-path> [segment-size]")
        logger.info("Example: python segment_file.py frontend/src/pages/HyDroMaCenter.tsx 500")
        return 1

    file_path = Path(sys.argv[1])
    segment_size = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    if not file_path.exists():
        logger.info(f"✗ فایل یافت نشد: {file_path}")
        return 1

    analysis = analyze_file(file_path)
    print_analysis(analysis, file_path)
    segment_file(file_path, segment_size)

    # ذخیره تحلیل به صورت JSON برای استفاده بعدی
    analysis_file = file_path.parent / f".analysis_{file_path.stem}.json"
    import json
    serializable = {k: list(v) if isinstance(v, set) else v
                    for k, v in analysis.items()}
    analysis_file.write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logger.info(f"\n  💾 تحلیل ذخیره شد: {analysis_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())