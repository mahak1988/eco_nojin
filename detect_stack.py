# -*- coding: utf-8 -*-
"""
detect_stack.py — شناسایی فناوری‌ها و فایل‌های فرانت‌اند پروژه
اجرا:  python detect_stack.py  [مسیر اختیاری پروژه]
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict

# پوشه‌هایی که نباید بررسی شوند
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".next", ".nuxt", ".output",
    "coverage", "staticfiles", "media", "migrations", ".pytest_cache",
}

# پسوندهای فرانت‌اند
FRONTEND_EXT = {
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "Sass", ".less": "Less",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".jsx": "React (JSX)", ".tsx": "React (TSX)",
    ".vue": "Vue", ".svelte": "Svelte", ".ejs": "EJS", ".hbs": "Handlebars",
}

# فریمورک‌های پایتون
PY_FRAMEWORKS = {
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "tornado": "Tornado", "pyramid": "Pyramid",
}

# نگاشت پکیج‌های npm به نام فناوری
JS_TECH_MAP = {
    "react": "React", "react-dom": "React", "next": "Next.js",
    "vue": "Vue.js", "nuxt": "Nuxt.js", "@angular/core": "Angular",
    "svelte": "Svelte", "express": "Express.js",
    "tailwindcss": "Tailwind CSS", "bootstrap": "Bootstrap",
    "vite": "Vite", "webpack": "Webpack", "jquery": "jQuery",
    "typescript": "TypeScript", "alpinejs": "Alpine.js", "htmx.org": "HTMX",
    "axios": "Axios", "gsap": "GSAP", "three": "Three.js",
}

# فایل‌های کانفیگ معرف فناوری
CONFIG_FILES = {
    "tailwind.config.js": "Tailwind CSS", "tailwind.config.ts": "Tailwind CSS",
    "vite.config.js": "Vite", "vite.config.ts": "Vite",
    "next.config.js": "Next.js", "angular.json": "Angular",
    "svelte.config.js": "Svelte", "webpack.config.js": "Webpack",
    "tsconfig.json": "TypeScript", "postcss.config.js": "PostCSS",
}

# الگوهای CDN داخل فایل‌های HTML
CDN_PATTERNS = [
    (r"<script[^>]+tailwind", "Tailwind CSS (CDN)"),
    (r"<(?:script|link)[^>]+bootstrap", "Bootstrap (CDN)"),
    (r"<script[^>]+jquery", "jQuery (CDN)"),
    (r"<script[^>]+vue[^>]*\.js", "Vue (CDN)"),
    (r"<script[^>]+react", "React (CDN)"),
    (r"<script[^>]+htmx", "HTMX (CDN)"),
    (r"<link[^>]+fonts\.googleapis", "Google Fonts"),
]

MAX_LIST = 15  # حداکثر تعداد فایل نمایش‌داده‌شده در هر دسته


def iter_files(root: Path, exts: set):
    """پیمایش پروژه با پرش از پوشه‌های سیستمی و وابستگی‌ها"""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if os.path.splitext(fname)[1].lower() in exts:
                yield Path(dirpath, fname)


def read_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


# ------------------- تشخیص فناوری‌ها -------------------
def detect_python(root: Path, techs: set):
    text = ""
    for name in ("requirements.txt", "pyproject.toml", "Pipfile"):
        if (root / name).exists():
            text += read_safe(root / name).lower() + "\n"
    if text:
        techs.add("Python")
        for pkg, label in PY_FRAMEWORKS.items():
            if re.search(rf"\b{pkg}\b", text):
                techs.add(label)
    else:
        # اگر requirements نبود، import ها را جستجو کن
        for i, py in enumerate(iter_files(root, {".py"})):
            if i >= 150:
                break
            content = read_safe(py).lower()
            for pkg, label in PY_FRAMEWORKS.items():
                if f"import {pkg}" in content or f"from {pkg}" in content:
                    techs.update({"Python", label})
    if (root / "manage.py").exists():
        techs.update({"Python", "Django"})


def detect_node(root: Path, techs: set):
    pkg_file = root / "package.json"
    if not pkg_file.exists():
        return
    techs.add("Node.js")
    try:
        data = json.loads(read_safe(pkg_file))
    except Exception:
        return
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    for dep, label in JS_TECH_MAP.items():
        if dep in deps:
            techs.add(label)


def detect_configs(root: Path, techs: set):
    for fname, label in CONFIG_FILES.items():
        if (root / fname).exists():
            techs.add(label)


def detect_html_cdns(root: Path, techs: set):
    for i, html in enumerate(iter_files(root, {".html", ".htm"})):
        if i >= 50:
            break
        content = read_safe(html)
        for pattern, label in CDN_PATTERNS:
            if re.search(pattern, content, re.I):
                techs.add(label)


# ------------------- اسکن فایل‌های فرانت‌اند -------------------
def scan_frontend(root: Path):
    found = defaultdict(list)
    for f in iter_files(root, set(FRONTEND_EXT)):
        found[FRONTEND_EXT[f.suffix.lower()]].append(f.relative_to(root).as_posix())
    return found


# ------------------- گزارش -------------------
def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    out("=" * 62)
    out(f"🔍 بررسی پروژه: {root}")
    out("=" * 62)

    techs = set()
    detect_python(root, techs)
    detect_node(root, techs)
    detect_configs(root, techs)
    detect_html_cdns(root, techs)

    out("\n🧩 فناوری‌های شناسایی‌شده:")
    for t in sorted(techs) or ["(هیچ فناوری شناخته‌شده‌ای پیدا نشد)"]:
        out(f"   • {t}")

    files = scan_frontend(root)
    out("\n📂 فایل‌های فرانت‌اند:")
    if not files:
        out("   (فایل فرانت‌اندی پیدا نشد)")
    for cat in sorted(files):
        items = sorted(files[cat])
        out(f"\n   ── {cat} ({len(items)} فایل) ──")
        for p in items[:MAX_LIST]:
            out(f"      {p}")
        if len(items) > MAX_LIST:
            out(f"      ... و {len(items) - MAX_LIST} فایل دیگر")

    total = sum(len(v) for v in files.values())
    out("\n" + "=" * 62)
    out(f"📊 جمع کل فایل‌های فرانت‌اند: {total}")
    out("=" * 62)

    Path("tech_report.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n💾 گزارش کامل در فایل tech_report.txt ذخیره شد.")


if __name__ == "__main__":
    main()