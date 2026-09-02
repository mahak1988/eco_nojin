# -*- coding: utf-8 -*-
"""
analyze_project.py — تحلیل جامع پروژه و تولید گزارش کامل (نسخهٔ ۲)

اجرا:
    python analyze_project.py [مسیر پروژه] [--depth 3] [--no-dupes] [--out PREFIX]

خروجی:
    PROJECT_REPORT.md  +  project_report.json

لایه‌های تحلیل:
    ۱) Git: شاخه، کامیت‌ها، مشارکت‌کنندگان، فعالیت ۳۰ روز، اولین کامیت
    ۲) ساختار درختی + آمار حجم/نوع/تازگی فایل‌ها
    ۳) اسکن عمیق کد: خطوط، TODO، endpointها (FastAPI/Flask/Django/Express)،
       console.log/print، localhost هاردکد، هوک‌ها و Routeها
    ۴) امنیت: کلید/توکن هاردکد، eval/exec، shell=True، SQLi، DEBUG، CORS، XSS، …
    ۵) کیفیت پایتون با AST: پیچیدگی، docstring، type hint، except خام، خطای parse
    ۶) کیفیت TypeScript: any، ts-ignore، eslint-disable، inline-style
    ۷) پایگاه‌داده/ORM و مهاجرت‌ها
    ۸) تکرار کد (هش پنجره‌ای — تقریبی)
    ۹) مستندات: README، LICENSE، docs، CHANGELOG
    ۱۰) معماری و نقاط ورود
    ۱۱) امتیاز سلامت ۰–۱۰۰ با ریز اقلام کسر امتیاز

نیازمندی: فقط کتابخانهٔ استاندارد پایتون (structlog اختیاری است)
"""

import os
import re
import ast
import sys
import json
import time
import argparse
import hashlib
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

# structlog اگر نصب بود استفاده می‌شود؛ وگرنه جایگزین استاندارد (بدون pip install)
try:
    import structlog
    logger = structlog.get_logger()
except ImportError:
    class _FallbackLogger:
        def info(self, msg="", *a, **k): print(msg)
        def warning(self, msg="", *a, **k): print(f"⚠️  {msg}")
        def error(self, msg="", *a, **k): print(f"❌  {msg}")
    logger = _FallbackLogger()

# ---------------- تنظیمات ----------------
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".next", ".nuxt", ".output",
    "coverage", "htmlcov", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "staticfiles", "media", "artifacts", ".cache", "target", "out",
}

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".scss",
            ".less", ".html", ".htm", ".vue", ".svelte"}

PY_FRAMEWORKS = {
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "tornado": "Tornado", "pyramid": "Pyramid", "starlette": "Starlette",
    "sanic": "Sanic", "aiohttp": "aiohttp", "celery": "Celery",
    "sqlalchemy": "SQLAlchemy", "pydantic": "Pydantic", "pytest": "Pytest",
}

CONFIG_FILES = {
    "tailwind.config.js": "Tailwind CSS", "tailwind.config.ts": "Tailwind CSS",
    "vite.config.js": "Vite", "vite.config.ts": "Vite", "vite.config.mts": "Vite",
    "tsconfig.json": "TypeScript", "postcss.config.js": "PostCSS",
    "next.config.js": "Next.js", "angular.json": "Angular",
    "svelte.config.js": "Svelte", "webpack.config.js": "Webpack",
    "vitest.config.ts": "Vitest", "jest.config.js": "Jest",
    "eslint.config.js": "ESLint", "hardhat.config.js": "Hardhat (بلاکچین)",
}

JS_TECH_MAP = {
    "react": "React", "react-dom": "React", "next": "Next.js",
    "vue": "Vue.js", "nuxt": "Nuxt.js", "@angular/core": "Angular",
    "svelte": "Svelte", "three": "Three.js",
    "@react-three/fiber": "React Three Fiber", "@deck.gl/core": "Deck.gl",
    "maplibre-gl": "MapLibre GL", "echarts": "ECharts", "recharts": "Recharts",
    "d3": "D3.js", "tailwindcss": "Tailwind CSS", "bootstrap": "Bootstrap",
    "ethers": "Ethers.js", "viem": "Viem", "wagmi": "Wagmi",
    "@web3modal/wagmi": "Web3Modal", "zustand": "Zustand",
    "@tanstack/react-query": "TanStack Query", "zod": "Zod",
    "i18next": "i18next", "framer-motion": "Framer Motion", "gsap": "GSAP",
    "antd": "Ant Design", "@mui/material": "MUI", "typescript": "TypeScript",
    "vite": "Vite", "express": "Express.js",
    "axios": "Axios", "@reduxjs/toolkit": "Redux Toolkit",
    "react-router-dom": "React Router", "@playwright/test": "Playwright",
}

CDN_PATTERNS = [
    (re.compile(r"<script[^>]+tailwind", re.I), "Tailwind CSS (CDN)"),
    (re.compile(r"<(?:script|link)[^>]+bootstrap", re.I), "Bootstrap (CDN)"),
    (re.compile(r"<script[^>]+jquery", re.I), "jQuery (CDN)"),
    (re.compile(r"<script[^>]+vue[^>]*\.js", re.I), "Vue (CDN)"),
    (re.compile(r"<script[^>]+htmx", re.I), "HTMX (CDN)"),
    (re.compile(r"<link[^>]+fonts\.googleapis", re.I), "Google Fonts"),
]

PY_DB_MAP = {
    "sqlalchemy": "SQLAlchemy", "psycopg2": "PostgreSQL", "psycopg": "PostgreSQL",
    "asyncpg": "PostgreSQL", "pymysql": "MySQL", "mysqlclient": "MySQL",
    "pymongo": "MongoDB", "mongoengine": "MongoDB", "redis": "Redis",
    "celery": "Celery (صف کار)", "tortoise": "Tortoise ORM", "peewee": "Peewee",
    "alembic": "Alembic", "sqlite3": "SQLite", "django": "Django ORM",
}

# ---------------- قوانین امنیتی ----------------
SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "کلید دسترسی AWS (AKIA…)", "بالا"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----"),
     "کلید خصوصی داخل کد", "بالا"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "Google API Key", "بالا"),
    (re.compile(r"\bsk_(?:live|test)_[0-9a-zA-Z]{12,}"), "کلید مخفی Stripe", "بالا"),
    (re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36,}"), "توکن GitHub", "بالا"),
    (re.compile(r"(?i)\b(?:mysql|postgres(?:ql)?|mongodb(?:\+srv)?|redis|amqp)"
                r"://[^/\s:\"']+:[^@\s\"']+@"), "رمز عبور داخل Connection String", "بالا"),
    (re.compile(r"(?i)\b(SECRET_KEY|API_KEY|APIKEY|API_SECRET|AUTH_TOKEN|ACCESS_TOKEN|"
                r"PASSWORD|PASSWD|DB_PASS(?:WORD)?|PRIVATE_KEY)\b\s*[:=]\s*[\"'][^\"']{6,}[\"']"),
     "مقدار محرمانهٔ هاردکد", "متوسط"),
]

SECURITY_RULES = [
    ((".py",), re.compile(r"\beval\s*\("), "استفاده از eval()", "متوسط"),
    ((".py",), re.compile(r"\bexec\s*\("), "استفاده از exec()", "متوسط"),
    ((".py",), re.compile(r"shell\s*=\s*True"), "subprocess با shell=True", "بالا"),
    ((".py",), re.compile(r"verify\s*=\s*False"), "غیرفعال‌سازی تأیید SSL (verify=False)", "متوسط"),
    ((".py",), re.compile(r"\bexecute\s*\(\s*f[\"']"), "کوئری SQL با f-string (خطر تزریق SQL)", "بالا"),
    ((".py",), re.compile(r"(?im)^\s*DEBUG\s*=\s*True\b"), "DEBUG=True (افشای اطلاعات در پروداکشن)", "متوسط"),
    ((".py",), re.compile(r"allow_origins\s*=\s*\[\s*[\"']\*[\"']"), "CORS باز برای همه ('*')", "متوسط"),
    ((".py",), re.compile(r"ALLOWED_HOSTS\s*=\s*\[\s*[\"']\*[\"']"), "ALLOWED_HOSTS = ['*']", "متوسط"),
    ((".py",), re.compile(r"\bpickle\.loads?\s*\("), "pickle (deserialization نامطمئن)", "کم"),
    ((".py",), re.compile(r"\bhashlib\.(?:md5|sha1)\b"), "هش ضعیف (md5/sha1)", "کم"),
    ((".py",), re.compile(r"^\s*except\s*:\s*(?:pass|\.\.\.)\s*$", re.M), "except خام (بلع خطا)", "کم"),
    ((".tsx", ".ts", ".jsx", ".js"), re.compile(r"dangerouslySetInnerHTML"),
     "dangerouslySetInnerHTML (ریسک XSS)", "متوسط"),
    ((".tsx", ".ts", ".jsx", ".js"),
     re.compile(r"(?i)\blocalStorage\.setItem\(\s*[\"'][^\"']*(?:token|password|secret)"),
     "ذخیرهٔ احتمالی توکن در localStorage", "کم"),
]

COMPLEXITY_NODES = tuple(
    n for n in (ast.If, ast.For, ast.While, ast.AsyncFor, ast.IfExp,
                ast.With, ast.AsyncWith, getattr(ast, "Match", None)) if n)

# ---------------- ابزارهای کمکی ----------------
def human_size(n: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i, v = 0, float(n)
    while v >= 1024 and i < len(units) - 1:
        v /= 1024
        i += 1
    return f"{int(v)} B" if i == 0 else f"{v:.1f} {units[i]}"


def read_safe(path: Path, limit: int = 2_000_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def walk_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield Path(dirpath) / name


def run_git(root: Path, args: list):
    try:
        r = subprocess.run(["git"] + args, cwd=str(root), capture_output=True,
                           text=True, errors="ignore", timeout=15)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


# ---------------- ۱) اطلاعات Git ----------------
def git_info(root: Path) -> dict:
    check = run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if check is None or "true" not in check.strip().lower():
        return {}
    info = {}
    info["branch"] = (run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "").strip()
    info["last_commit"] = (run_git(root, ["log", "-1", "--format=%h | %ad | %an: %s",
                                          "--date=short"]) or "").strip()
    info["total_commits"] = (run_git(root, ["rev-list", "--count", "HEAD"]) or "").strip()
    info["remote"] = (run_git(root, ["remote", "get-url", "origin"]) or "").strip()
    st = run_git(root, ["status", "--porcelain"]) or ""
    info["uncommitted"] = len([l for l in st.splitlines() if l.strip()])
    log = run_git(root, ["log", "--reverse", "--format=%ad", "--date=short"]) or ""
    lines = [l for l in log.splitlines() if l.strip()]
    info["first_commit"] = lines[0] if lines else ""
    info["commits_30d"] = (run_git(root, ["rev-list", "--count",
                                          "--since=30 days ago", "HEAD"]) or "?").strip()
    contrib = []
    short = run_git(root, ["shortlog", "-sn", "HEAD"]) or ""
    for l in short.splitlines():
        m = re.match(r"\s*(\d+)\s+(.+)", l)
        if m:
            contrib.append((int(m.group(1)), m.group(2).strip()))
    info["contributors"] = contrib
    return info


def git_tracked_bad(root: Path) -> dict:
    """پوشه/فایل‌هایی که نباید در گیت باشند ولی track شده‌اند"""
    out = {}
    candidates = ["htmlcov", "node_modules", ".venv", "venv", "dist",
                  "frontend/dist", "frontend/node_modules",
                  ".env", ".env.local", ".env.production",
                  "backend/.env", "frontend/.env", "*.pem", "*.key"]
    for d in candidates:
        r = run_git(root, ["ls-files", "--", d])
        if r:
            n = len([x for x in r.splitlines() if x.strip()])
            if n:
                out[d] = n
    return out


# ---------------- ۲) ساختار درختی ----------------
def count_files_in(d: Path) -> int:
    n = 0
    for _, dirnames, filenames in os.walk(d):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS]
        n += len(filenames)
    return n


def build_tree(root: Path, max_depth: int = 3):
    lines, truncated = [], []
    try:
        root_files = [e for e in root.iterdir() if e.is_file()]
    except OSError:
        root_files = []
    lines.append(f"{root.name}/  ({len(root_files)} فایل در ریشه)")

    def walk(d: Path, prefix: str, depth: int):
        try:
            subdirs = sorted([e for e in d.iterdir()
                              if e.is_dir() and e.name not in SKIP_DIRS],
                             key=lambda e: e.name.lower())
        except (PermissionError, OSError):
            return
        for i, e in enumerate(subdirs):
            last = i == len(subdirs) - 1
            lines.append(f"{prefix}{'└── ' if last else '├── '}"
                         f"{e.name}/ ({count_files_in(e)} فایل)")
            if depth < max_depth:
                walk(e, prefix + ("    " if last else "│   "), depth + 1)
            else:
                try:
                    if any(x.is_dir() and x.name not in SKIP_DIRS for x in e.iterdir()):
                        truncated.append(e.relative_to(root).as_posix())
                except OSError:
                    pass

    walk(root, "", 0)
    return lines, truncated


# ---------------- ۳) آمار حجم و تازگی فایل‌ها ----------------
def count_empty_dirs(root: Path) -> int:
    n = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if not dirnames and not filenames:
            n += 1
    return n


def scan_sizes(root: Path):
    ext_count, ext_size = Counter(), Counter()
    total_files = total_size = empty_files = 0
    largest = []
    now = time.time()
    fresh7 = fresh30 = 0
    newest = (0.0, "")
    for f in walk_files(root):
        try:
            st = f.stat()
            size, mtime = st.st_size, st.st_mtime
        except OSError:
            continue
        ext = f.suffix.lower() or "(بدون پسوند)"
        ext_count[ext] += 1
        ext_size[ext] += size
        total_files += 1
        total_size += size
        if size == 0:
            empty_files += 1
        age = now - mtime
        if age < 7 * 86400:
            fresh7 += 1
        elif age < 30 * 86400:
            fresh30 += 1
        if mtime > newest[0]:
            newest = (mtime, f.relative_to(root).as_posix())
        largest.append((size, f.relative_to(root).as_posix()))
    largest.sort(reverse=True)
    extra = {"empty_files": empty_files, "empty_dirs": count_empty_dirs(root),
             "fresh7": fresh7, "fresh30": fresh30, "newest": newest[1]}
    return ext_count, ext_size, total_files, total_size, largest, extra


# ---------------- ۴) اسکن عمیق کد ----------------
def deep_scan(root: Path) -> dict:
    lang = defaultdict(lambda: {"files": 0, "lines": 0, "code": 0,
                                "comment": 0, "blank": 0})
    todo_total, todo_samples = 0, []
    console_files, print_files, localhost_files = Counter(), Counter(), Counter()
    endpoints, ws_endpoints = [], []
    lazy_count = suspense_count = route_count = 0
    cdn_techs = Counter()
    models_count = 0
    # لایهٔ کیفیت TypeScript/JS
    ts_q = {"any": 0, "ts_skip": 0, "eslint_disable": 0,
            "useEffect": 0, "useState": 0, "inline_style": 0}

    for f in walk_files(root):
        ext = f.suffix.lower()
        if ext not in CODE_EXT:
            continue
        text = read_safe(f)
        if not text:
            continue
        rel = f.relative_to(root).as_posix()
        is_py = ext == ".py"

        # --- آمار خطوط ---
        row = lang[ext]
        row["files"] += 1
        for line in text.splitlines():
            s = line.strip()
            row["lines"] += 1
            if not s:
                row["blank"] += 1
            elif (is_py and s.startswith("#")) or s.startswith("//") \
                    or s.startswith("/*") or s.startswith("*") or s.startswith("<!--"):
                row["comment"] += 1
            else:
                row["code"] += 1

        # --- TODO / FIXME ---
        if ext in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            for m in re.finditer(r"\b(TODO|FIXME|HACK|XXX)\b[^\n]*", text):
                todo_total += 1
                if len(todo_samples) < 6:
                    ln = text.count("\n", 0, m.start()) + 1
                    snippet = m.group(0).strip()[:90].replace("|", "/")
                    todo_samples.append(f"`{rel}:{ln}` — {snippet}")

        # --- فرانت‌اند ---
        if ext in {".ts", ".tsx", ".js", ".jsx"}:
            n = len(re.findall(r"\bconsole\.log\(", text))
            if n:
                console_files[rel] += n
            lazy_count += len(re.findall(r"\blazy\(\s*\(\)\s*=>", text))
            route_count += len(re.findall(r"<Route\b", text))
            ts_q["eslint_disable"] += len(re.findall(r"eslint-disable", text))
            ts_q["useEffect"] += len(re.findall(r"\buseEffect\s*\(", text))
            ts_q["useState"] += len(re.findall(r"\buseState\s*[<(]", text))
            ts_q["inline_style"] += len(re.findall(r"style\s*=\s*\{\{", text))
        if ext == ".tsx":
            suspense_count += len(re.findall(r"<Suspense\b", text))
        if ext in {".ts", ".tsx"}:
            ts_q["any"] += len(re.findall(r":\s*any\b|\bas\s+any\b", text))
            ts_q["ts_skip"] += len(re.findall(r"@ts-(?:ignore|nocheck|expect-error)", text))

        # --- بک‌اند پایتون ---
        if is_py:
            n = len(re.findall(r"(?<![\w.])print\(", text))
            if n:
                print_files[rel] += n
            for m in re.finditer(r"@\w+\.(get|post|put|delete|patch|head|options)"
                                 r"\(\s*[\"']([^\"']*)[\"']", text):
                endpoints.append((m.group(1).upper(), m.group(2) or "/", rel))
            for m in re.finditer(r"@\w+\.route\(\s*[\"']([^\"']*)[\"']", text):
                endpoints.append(("ROUTE", m.group(1) or "/", rel))
            for m in re.finditer(r"@\w+\.websocket\(\s*[\"']([^\"']*)[\"']", text):
                ws_endpoints.append((m.group(1), rel))
            models_count += len(re.findall(
                r"class\s+\w+\s*\(\s*(?:models\.Model|BaseModel|Base)\b[^)]*\):", text))

        # --- مسیرهای Django ---
        if "urls" in f.name and ext == ".py":
            for m in re.finditer(r"\b(?:path|re_path)\(\s*r?[\"']([^\"']+)[\"']", text):
                endpoints.append(("DJANGO", m.group(1), rel))

        # --- اندپوینت‌های Express (خارج از پوشهٔ frontend) ---
        if ext in {".js", ".ts"} and not rel.lower().startswith(
                ("frontend/", "client/", "src/client")):
            for m in re.finditer(r"\b(?:app|router|server|api)\."
                                 r"(get|post|put|delete|patch|all)\(\s*[\"'`]([^\"'`\s]+)[\"'`]",
                                 text):
                endpoints.append((m.group(1).upper(), m.group(2), rel))

        # --- localhost هاردکد ---
        for m in re.finditer(r"https?://(?:localhost|127\.0\.0\.1)[^\s\"'<>]*", text):
            localhost_files[rel] += 1

        # --- CDN در HTML ---
        if ext in {".html", ".htm"}:
            for pat, label in CDN_PATTERNS:
                if pat.search(text):
                    cdn_techs[label] += 1

    return {"lang": dict(lang), "todo_total": todo_total,
            "todo_samples": todo_samples, "console_files": console_files,
            "print_files": print_files, "localhost_files": localhost_files,
            "endpoints": endpoints, "ws_endpoints": ws_endpoints,
            "lazy_count": lazy_count, "suspense_count": suspense_count,
            "route_count": route_count, "cdn_techs": cdn_techs,
            "models_count": models_count, "ts": ts_q}


# ---------------- ۵) امنیت ----------------
def scan_secrets(root: Path) -> list:
    findings = []
    scan_exts = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml",
                 ".yaml", ".html", ".htm", ".sh", ".cfg", ".ini", ".toml"}
    for f in walk_files(root):
        name, rel = f.name, f.relative_to(root).as_posix()
        if name.startswith(".env"):
            # فقط «نام کلیدها» گزارش می‌شود، نه مقادیر
            text = read_safe(f, limit=200_000)
            keys = sorted({m.group(1).upper()
                           for m in re.finditer(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]{2,})\s*=", text)})
            risky = [k for k in keys
                     if re.search(r"SECRET|TOKEN|PASSWORD|PASSWD|_KEY|DSN|CREDENTIAL", k)]
            if risky:
                findings.append({"file": rel, "line": 0, "severity": "اطلاع",
                                 "rule": "کلیدهای حساس در فایل env: " + ", ".join(risky[:8])})
            continue
        ext = f.suffix.lower()
        if ext not in scan_exts:
            continue
        text = read_safe(f)
        if not text:
            continue
        for pat, label, sev in SECRET_PATTERNS:
            m = pat.search(text)
            if m:
                findings.append({"file": rel, "severity": sev, "rule": label,
                                 "line": text.count("\n", 0, m.start()) + 1})
        for exts, pat, label, sev in SECURITY_RULES:
            if ext in exts:
                m = pat.search(text)
                if m:
                    findings.append({"file": rel, "severity": sev, "rule": label,
                                     "line": text.count("\n", 0, m.start()) + 1})
    return findings


# ---------------- ۶) کیفیت پایتون با AST ----------------
def python_deep_scan(root: Path) -> dict:
    st = {"files": 0, "parse_errors": [], "functions": 0, "classes": 0,
          "max_args": (0, ""), "longest_func": (0, ""), "complexity_top": [],
          "doc_present": 0, "doc_missing": 0, "typed": 0,
          "imports": Counter(), "bare_except": 0}
    for f in walk_files(root):
        if f.suffix != ".py":
            continue
        text = read_safe(f)
        if not text:
            continue
        rel = f.relative_to(root).as_posix()
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            st["parse_errors"].append(f"{rel}:{e.lineno} — {e.msg}")
            continue
        st["files"] += 1
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                st["functions"] += 1
                nargs = len(node.args.args) + len(node.args.kwonlyargs)
                if nargs > st["max_args"][0]:
                    st["max_args"] = (nargs, f"{rel}:{node.lineno} → {node.name}()")
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                if length > st["longest_func"][0]:
                    st["longest_func"] = (length, f"{rel}:{node.lineno} → {node.name}()")
                if ast.get_docstring(node):
                    st["doc_present"] += 1
                else:
                    st["doc_missing"] += 1
                if node.returns is not None:
                    st["typed"] += 1
            elif isinstance(node, ast.ClassDef):
                st["classes"] += 1
                if ast.get_docstring(node):
                    st["doc_present"] += 1
                else:
                    st["doc_missing"] += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
                if node.type is None:
                    st["bare_except"] += 1
            elif isinstance(node, COMPLEXITY_NODES):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += max(0, len(node.values) - 1)
            elif isinstance(node, ast.comprehension):
                complexity += 1 + len(node.ifs)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    st["imports"][a.name.split(".")[0]] += 1
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    st["imports"][node.module.split(".")[0]] += 1
        st["complexity_top"].append((complexity, rel))
    st["complexity_top"].sort(reverse=True)
    return st


# ---------------- ۷) پایگاه‌داده و ORM ----------------
def detect_database(root: Path, py_imports: Counter) -> dict:
    dbs = {label for mod, label in PY_DB_MAP.items() if mod in py_imports}
    for p in ("prisma/schema.prisma", "frontend/prisma/schema.prisma"):
        if (root / p).exists():
            dbs.add("Prisma")
            break
    migrations = 0
    for f in walk_files(root):
        if f.suffix == ".py" and any(p in {"migrations", "alembic", "versions"}
                                     for p in f.parts[:-1]):
            migrations += 1
    return {"systems": sorted(dbs), "migrations": migrations}


# ---------------- ۸) تکرار کد (تقریبی) ----------------
def find_duplicates(root: Path, min_block: int = 8, max_windows: int = 800):
    window_map = defaultdict(list)
    for f in walk_files(root):
        if f.suffix not in {".py", ".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = read_safe(f)
        if not text:
            continue
        kept = [l.strip() for l in text.splitlines()
                if len(l.strip()) >= 6
                and not l.strip().startswith(("#", "//", "import ", "from ",
                                              "*", "<", "{", "}"))]
        if len(kept) < min_block:
            continue
        rel = f.relative_to(root).as_posix()
        step = max(1, min_block // 2)
        count = 0
        for s in range(0, len(kept) - min_block + 1, step):
            h = hashlib.md5("\n".join(kept[s:s + min_block]).encode("utf-8")).hexdigest()
            lst = window_map[h]
            if sum(1 for r, _ in lst if r == rel) < 2:
                lst.append((rel, s + 1))
            count += 1
            if count >= max_windows:
                break
    groups = [(h, locs) for h, locs in window_map.items() if len(locs) > 1]
    groups.sort(key=lambda x: len(x[1]), reverse=True)
    return groups, len(groups)


# ---------------- ۹) مستندات و لایسنس ----------------
def analyze_docs(root: Path) -> dict:
    out = {"readme": None, "license": None, "has_docs_dir": False,
           "docs_files": 0, "changelog": False, "contributing": False}
    for name in ("README.md", "readme.md", "Readme.md", "README.rst",
                 "README.fa.md", "README.en.md"):
        p = root / name
        if p.exists():
            text = read_safe(p)
            out["readme"] = {
                "file": name, "lines": len(text.splitlines()),
                "headings": len(re.findall(r"(?m)^#{1,6}\s+\S", text)),
                "code_blocks": text.count("```") // 2,
                "sections": [s for s, rx in
                             (("نصب", r"(?im)^#+\s*.*(install|نصب|راه.?اندازی)"),
                              ("اجرا", r"(?im)^#+\s*.*(usage|run|اجرا|شروع)"),
                              ("تست", r"(?im)^#+\s*.*(test|تست)"),
                              ("مشارکت", r"(?im)^#+\s*.*(contribut|مشارکت)"))
                             if re.search(rx, text)],
            }
            break
    for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "licence"):
        p = root / name
        if p.exists():
            head = read_safe(p, limit=4000).lower()
            for lic, rx in (("MIT", r"\bmit license\b"), ("Apache-2.0", r"apache license"),
                            ("GPL", r"gnu general public license"), ("BSD", r"\bbsd\b"),
                            ("MPL", r"mozilla public license"), ("ISC", r"\bisc license\b")):
                if re.search(rx, head):
                    out["license"] = lic
                    break
            else:
                out["license"] = "موجود (نوع نامشخص)"
            break
    docs = root / "docs"
    if docs.is_dir():
        out["has_docs_dir"] = True
        out["docs_files"] = sum(1 for _ in walk_files(docs))
    out["changelog"] = any((root / n).exists() for n in ("CHANGELOG.md", "CHANGES.md"))
    out["contributing"] = any((root / n).exists()
                              for n in ("CONTRIBUTING.md", ".github/CONTRIBUTING.md"))
    return out


# ---------------- ۱۰) معماری و نقاط ورود ----------------
def detect_entry_points(root: Path) -> list:
    names = ["manage.py", "main.py", "app.py", "server.py", "wsgi.py", "asgi.py",
             "run.py", "cli.py", "index.tsx", "index.ts", "index.js",
             "server.js", "main.ts"]
    found = []
    for n in names:
        for cand in (root / n, root / "backend" / n,
                     root / "frontend" / "src" / n, root / "src" / n):
            if cand.exists():
                found.append(cand.relative_to(root).as_posix())
                break
    return sorted(set(found))


def detect_architecture(root: Path) -> dict:
    try:
        top_dirs = sorted(d.name for d in root.iterdir()
                          if d.is_dir() and d.name not in SKIP_DIRS)
    except OSError:
        top_dirs = []
    s = set(top_dirs)
    if {"backend", "frontend"} <= s:
        style = "تک‌ریپو با جداسازی backend/frontend"
    elif {"apps", "packages"} & s:
        style = "monorepo (apps/packages)"
    elif "services" in s:
        style = "میکروسرویس"
    else:
        style = "ساده / تک‌پوشه"
    return {"style": style, "top_dirs": top_dirs,
            "entry_points": detect_entry_points(root)}


# ---------------- ۱۱) فناوری‌ها و وابستگی‌ها ----------------
def detect_techs(root: Path) -> set:
    techs = set()
    text = ""
    for name in ("requirements.txt", "pyproject.toml", "Pipfile",
                 "backend/requirements.txt"):
        p = root / name
        if p.exists():
            text += read_safe(p).lower() + "\n"
    if text:
        techs.add("Python")
        for pkg, label in PY_FRAMEWORKS.items():
            if re.search(rf"\b{pkg}\b", text):
                techs.add(label)
    if (root / "manage.py").exists():
        techs.update({"Python", "Django"})

    for base in (root, root / "frontend"):
        pkg = base / "package.json"
        if pkg.exists():
            techs.add("Node.js")
            try:
                data = json.loads(read_safe(pkg))
                deps = {**data.get("dependencies", {}),
                        **data.get("devDependencies", {})}
            except Exception:
                deps = {}
            for d, label in JS_TECH_MAP.items():
                if d in deps:
                    techs.add(label)
        for fname, label in CONFIG_FILES.items():
            if (base / fname).exists():
                techs.add(label)
    return techs


def analyze_deps(root: Path) -> dict:
    out = {"npm": None, "scripts": {}, "requirements": [], "unpinned": [],
           "lockfile": None, "pyproject": False}
    pkg = root / "frontend" / "package.json"
    if not pkg.exists():
        pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            out["npm"] = {"name": data.get("name", "?"),
                          "dependencies": data.get("dependencies", {}),
                          "devDependencies": data.get("devDependencies", {})}
            out["scripts"] = data.get("scripts", {})
        except Exception:
            pass
    fe = root / "frontend"
    for lf in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
        if (fe / lf).exists() or (root / lf).exists():
            out["lockfile"] = lf
            break
    for req_name in ("requirements.txt", "backend/requirements.txt"):
        p = root / req_name
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                s = line.strip()
                if s and not s.startswith(("#", "-")):
                    out["requirements"].append(s)
            out["unpinned"] = [s for s in out["requirements"]
                               if not re.search(r"(==|>=|~=|<=|!=|\[)", s)]
            break
    out["pyproject"] = (root / "pyproject.toml").exists()
    return out


def analyze_devops(root: Path) -> list:
    found = []
    checks = [
        ("Dockerfile", "Dockerfile"), ("backend/Dockerfile", "Dockerfile (backend)"),
        ("frontend/Dockerfile", "Dockerfile (frontend)"),
        ("docker-compose.yml", "Docker Compose"), ("docker-compose.yaml", "Docker Compose"),
        ("alembic.ini", "Alembic (مهاجرت DB)"), ("backend/alembic.ini", "Alembic (مهاجرت DB)"),
        ("Makefile", "Makefile"), ("nginx.conf", "Nginx"),
        ("README.md", "README.md"), (".env.example", "نمونه .env"),
        ("Procfile", "Procfile (Heroku/Railway)"), ("fly.toml", "Fly.io"),
        ("contracts/hardhat.config.js", "Hardhat (قرارداد هوشمند)"),
    ]
    for path, label in checks:
        if (root / path).exists():
            found.append(label)
    wf = root / ".github" / "workflows"
    if wf.is_dir():
        n = len(list(wf.glob("*.y*ml")))
        if n:
            found.append(f"GitHub Actions ({n} workflow)")
    if (root / ".gitlab-ci.yml").exists():
        found.append("GitLab CI")
    return found


def find_env_files(root: Path) -> list:
    return sorted({f.relative_to(root).as_posix()
                   for f in walk_files(root)
                   if f.name == ".env" or f.name.startswith(".env.")})


def detect_tests(root: Path):
    be = 0
    for tname in ("tests", "backend/tests", "test", "app/tests"):
        d = root / tname
        if d.is_dir():
            be = sum(1 for f in walk_files(d)
                     if f.suffix == ".py" and f.name.startswith("test_"))
            break
    fe = 0
    fe_dir = root / "frontend"
    if fe_dir.is_dir():
        for f in walk_files(fe_dir):
            if f.name.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
                fe += 1
    return be, fe


def check_gitignore(root: Path):
    gi = root / ".gitignore"
    if not gi.exists():
        return False, ["فایل .gitignore اصلاً وجود ندارد!"]
    content = gi.read_text(encoding="utf-8", errors="ignore").lower()
    needed = ["node_modules", "dist", ".venv", "__pycache__", ".env", "htmlcov"]
    return True, [x for x in needed if x not in content]


# ---------------- گزارش ----------------
def parse_args():
    ap = argparse.ArgumentParser(
        description="تحلیل جامع پروژه → PROJECT_REPORT.md + project_report.json",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("path", nargs="?", default=".", help="مسیر پروژه")
    ap.add_argument("--depth", type=int, default=3, help="عمق درخت پوشه‌ها")
    ap.add_argument("--no-dupes", action="store_true",
                    help="غیرفعال‌کردن تحلیل تکرار کد")
    ap.add_argument("--out", default=None, help="پیشوند نام فایل‌های خروجی")
    return ap.parse_args()


def main():
    t0 = datetime.now()
    args = parse_args()
    root = Path(args.path).resolve()
    if not root.is_dir():
        logger.error(f"❌ مسیر پیدا نشد: {root}")
        sys.exit(1)

    logger.info(f"🔍 در حال تحلیل: {root} ...")
    data = {"meta": {"path": str(root),
                     "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     "python": platform.python_version(),
                     "os": f"{platform.system()} {platform.release()}"}}

    git = git_info(root)
    ext_count, ext_size, total_files, total_size, largest, sz_extra = scan_sizes(root)
    scan = deep_scan(root)
    py = python_deep_scan(root)
    findings = scan_secrets(root)
    deps = analyze_deps(root)
    devops = analyze_devops(root)
    envs = find_env_files(root)
    gi_ok, gi_missing = check_gitignore(root)
    tracked_bad = git_tracked_bad(root)
    be_tests, fe_tests = detect_tests(root)
    techs = detect_techs(root) | set(scan["cdn_techs"].keys())
    docs = analyze_docs(root)
    db = detect_database(root, py["imports"])
    dupes, dupe_groups = ([], 0)
    if not args.no_dupes:
        dupes, dupe_groups = find_duplicates(root)
    arch = detect_architecture(root)

    # ---------- محاسبات جمعی ----------
    cl_total = sum(scan["console_files"].values())
    pr_total = sum(scan["print_files"].values())
    lh_total = sum(scan["localhost_files"].values())
    loc_code = sum(r["code"] for r in scan["lang"].values())
    methods = Counter(m for m, _, _ in scan["endpoints"])
    sec_high = [f for f in findings if f["severity"] == "بالا"]
    sec_med = [f for f in findings if f["severity"] == "متوسط"]
    has_fe = ext_count.get(".tsx", 0) > 0 or (root / "frontend").is_dir()
    doc_total = py["doc_present"] + py["doc_missing"]
    doc_pct = round(100 * py["doc_present"] / doc_total) if doc_total else 100
    typed_pct = round(100 * py["typed"] / py["functions"]) if py["functions"] else 0

    # ---------- امتیاز سلامت ----------
    deductions = []
    def deduct(pts, reason):
        deductions.append((pts, reason))

    if not docs["readme"]:
        deduct(5, "README وجود ندارد")
    if not gi_ok:
        deduct(10, "فایل .gitignore وجود ندارد")
    elif gi_missing:
        deduct(min(5, len(gi_missing)), "موارد جاافتاده در .gitignore: " + ", ".join(gi_missing))
    for d, n in tracked_bad.items():
        if ".env" in d:
            deduct(10, f"«{d}» در گیت track شده است")
        else:
            deduct(8, f"پوشه/فایل build در گیت: {d} ({n} فایل)")
    if sec_high:
        deduct(min(30, 6 * len(sec_high)), f"{len(sec_high)} یافتهٔ امنیتی با شدت بالا")
    if sec_med:
        deduct(min(10, 2 * len(sec_med)), f"{len(sec_med)} یافتهٔ امنیتی با شدت متوسط")
    if be_tests == 0:
        deduct(8, "تست بک‌اند یافت نشد")
    if has_fe and fe_tests == 0:
        deduct(6, "تست فرانت‌اند وجود ندارد")
    if cl_total:
        deduct(min(8, cl_total // 25), f"console.log ({cl_total} مورد)")
    if pr_total:
        deduct(min(6, pr_total // 25), f"print() ({pr_total} مورد)")
    if scan["todo_total"]:
        deduct(min(5, scan["todo_total"] // 20), f"TODO/FIXME ({scan['todo_total']} مورد)")
    if py["parse_errors"]:
        deduct(min(10, 2 * len(py["parse_errors"])),
               f"خطای parse پایتون ({len(py['parse_errors'])} فایل)")
    if doc_total and doc_pct < 10:
        deduct(6, f"پوشش docstring خیلی پایین ({doc_pct}٪)")
    elif doc_total and doc_pct < 30:
        deduct(3, f"پوشش docstring پایین ({doc_pct}٪)")
    if deps["npm"] and not deps["lockfile"]:
        deduct(3, "lockfile فرانت‌اند کامیت نشده")

    score = max(0, 100 - sum(p for p, _ in deductions))
    grade = ("A" if score >= 90 else "B" if score >= 75 else
             "C" if score >= 60 else "D" if score >= 40 else "F")
    grade_emoji = {"A": "🟢", "B": "🟢", "C": "🟡", "D": "🟠", "F": "🔴"}[grade]

    data.update({
        "techs": sorted(techs), "git": git,
        "stats": {"total_files": total_files, "total_size": total_size,
                  "loc_code": loc_code, "endpoints": len(scan["endpoints"]),
                  "models": scan["models_count"],
                  "tests_backend": be_tests, "tests_frontend": fe_tests,
                  "fresh7": sz_extra["fresh7"], "fresh30": sz_extra["fresh30"]},
        "endpoints": scan["endpoints"],
        "ws_endpoints": scan["ws_endpoints"],
        "dependencies": deps, "devops": devops, "env_files": envs,
        "langs": scan["lang"], "cdn_techs": dict(scan["cdn_techs"]),
        "security": {"findings": findings, "high": len(sec_high),
                     "medium": len(sec_med), "low": len(findings) - len(sec_high) - len(sec_med)},
        "python_quality": {"parse_errors": py["parse_errors"],
                           "functions": py["functions"], "classes": py["classes"],
                           "docstring_pct": doc_pct, "typed_pct": typed_pct,
                           "bare_except": py["bare_except"],
                           "complexity_top": py["complexity_top"][:15],
                           "longest_func": list(py["longest_func"]),
                           "max_args": list(py["max_args"]),
                           "imports": py["imports"].most_common(20)},
        "ts_quality": scan["ts"],
        "database": db, "docs": docs, "freshness": sz_extra,
        "duplicates": {"groups": dupe_groups,
                       "samples": [[{"file": r, "line": l} for r, l in locs[:4]]
                                   for _, locs in dupes[:10]]},
        "architecture": arch,
        "health": {"score": score, "grade": grade, "deductions": deductions,
                   "gitignore_missing": gi_missing if gi_ok else None,
                   "tracked_build_dirs": tracked_bad,
                   "todo_total": scan["todo_total"],
                   "console_log_total": cl_total, "print_total": pr_total,
                   "localhost_total": lh_total},
    })

    # ---------- ساخت مارک‌داون ----------
    md = []
    A = md.append
    A(f"# 📊 گزارش جامع پروژه — {root.name}")
    A("")
    A(f"- **تاریخ تولید:** {data['meta']['generated']}")
    A(f"- **مسیر:** `{root}`")
    A(f"- **محیط:** Python {data['meta']['python']} | {data['meta']['os']}")
    A(f"- **مدت اسکن:** {(datetime.now() - t0).total_seconds():.1f} ثانیه")
    A(f"- **⭐ امتیاز سلامت:** **{score}/100** (گرید {grade} {grade_emoji})")
    A("")

    # ۱) خلاصه اجرایی
    A("## ۱) خلاصه اجرایی")
    A("")
    A("| مورد | مقدار |")
    A("|---|---|")
    A(f"| کل فایل‌ها | {total_files:,} |")
    A(f"| حجم کل | {human_size(total_size)} |")
    A(f"| خطوط کد واقعی | {loc_code:,} |")
    A(f"| اندپوینت‌های API | {len(scan['endpoints'])} |")
    A(f"| کامپوننت‌های React (tsx) | {ext_count.get('.tsx', 0)} |")
    A(f"| کلاس‌های Model (تقریبی) | {scan['models_count']} |")
    A(f"| تست بک‌اند / فرانت‌اند | {be_tests} / {fe_tests} فایل |")
    A(f"| یافته‌های امنیتی (بالا/متوسط) | {len(sec_high)} / {len(sec_med)} |")
    A("")
    A("**استک:** " + " · ".join(sorted(techs)))
    if devops:
        A("")
        A("**ابزارها:** " + " · ".join(devops))
    A("")

    # ۲) Git
    A("## ۲) وضعیت Git")
    A("")
    if git:
        A(f"- شاخه: `{git.get('branch')}`")
        A(f"- آخرین کامیت: {git.get('last_commit')}")
        A(f"- تعداد کامیت‌ها: {git.get('total_commits')}")
        if git.get("first_commit"):
            A(f"- اولین کامیت: {git['first_commit']}")
        A(f"- کامیت‌های ۳۰ روز اخیر: {git.get('commits_30d')}")
        A(f"- ریموت: `{git.get('remote')}`")
        A(f"- تغییرات کامیت‌نشده: {git.get('uncommitted')} فایل")
        contrib = git.get("contributors") or []
        if contrib:
            A("- مشارکت‌کنندگان اصلی: "
              + ", ".join(f"{name} ({n})" for n, name in contrib[:5]))
    else:
        A("- ریپازیتوری Git یافت نشد.")
    A("")

    # ۳) ساختار پوشه‌ها
    A(f"## ۳) ساختار پوشه‌ها (تا عمق {args.depth})")
    A("")
    A("```text")
    tree_lines, truncated = build_tree(root, max_depth=args.depth)
    md.extend(tree_lines)
    if truncated:
        A(f"… و {len(truncated)} زیرپوشه در عمق بیشتر")
    A("```")
    A("")

    # ۴) آمار نوع فایل‌ها
    A("## ۴) آمار فایل‌ها بر اساس نوع")
    A("")
    A("| پسوند | تعداد | حجم |")
    A("|---|---:|---:|")
    for ext_k, cnt in ext_count.most_common(25):
        A(f"| `{ext_k}` | {cnt:,} | {human_size(ext_size[ext_k])} |")
    A("")

    # ۵) بزرگ‌ترین فایل‌ها
    A("## ۵) بزرگ‌ترین فایل‌ها")
    A("")
    A("| حجم | فایل |")
    A("|---:|---|")
    for size_b, rel_path in largest[:15]:
        A(f"| {human_size(size_b)} | `{rel_path}`{' ⚠️' if size_b > 1_000_000 else ''} |")
    A("")

    # ۶) وابستگی‌ها
    A("## ۶) وابستگی‌ها")
    A("")
    if deps["npm"]:
        A("### فرانت‌اند — package.json")
        A("")
        A("| پکیج | نسخه | نوع |")
        A("|---|---|---|")
        for name, ver in sorted(deps["npm"]["dependencies"].items()):
            A(f"| {name} | {ver} | runtime |")
        for name, ver in sorted(deps["npm"]["devDependencies"].items()):
            A(f"| {name} | {ver} | dev |")
        A("")
    if deps["scripts"]:
        A("### اسکریپت‌های npm")
        A("")
        A("| دستور | اسکریپت |")
        A("|---|---|")
        for k, v in deps["scripts"].items():
            A(f"| `{k}` | `{v}` |")
        A("")
    A("### بک‌اند — requirements.txt")
    A("")
    if deps["requirements"]:
        for r in deps["requirements"]:
            A(f"- {r}")
        if deps["unpinned"]:
            A(f"- ⚠️ {len(deps['unpinned'])} پکیج بدون پین نسخه: "
              + ", ".join(f"`{u}`" for u in deps["unpinned"][:10]))
    else:
        A("- یافت نشد")
    A(f"- pyproject.toml: {'✅ موجود' if deps['pyproject'] else '—'}")
    A(f"- lockfile فرانت‌اند: {('✅ ' + deps['lockfile']) if deps['lockfile'] else '❌ یافت نشد'}")
    A("")

    # ۷) بک‌اند
    A("## ۷) بک‌اند (API)")
    A("")
    A(f"- تعداد اندپوینت‌ها: **{len(scan['endpoints'])}** — "
      + " · ".join(f"{k}×{v}" for k, v in sorted(methods.items())))
    if scan["ws_endpoints"]:
        A(f"- WebSocket: {len(scan['ws_endpoints'])} اندپوینت — "
          + ", ".join(f"`{p}`" for p, _ in scan["ws_endpoints"][:5]))
    A("")
    A("| متد | مسیر | فایل |")
    A("|---|---|---|")
    for m_, p_, f_ in scan["endpoints"][:40]:
        A(f"| {m_} | `{p_}` | `{f_}` |")
    if len(scan["endpoints"]) > 40:
        A(f"| … | … | و {len(scan['endpoints']) - 40} مورد دیگر |")
    A("")

    # ۸) فرانت‌اند
    A("## ۸) فرانت‌اند")
    A("")
    A(f"- کامپوننت‌های TSX: {ext_count.get('.tsx', 0)}")
    pages = root / "frontend" / "src" / "pages"
    if pages.is_dir():
        n_pages = sum(1 for f in walk_files(pages) if f.suffix in {".tsx", ".ts"})
        A(f"- صفحات (src/pages): {n_pages}")
    A(f"- lazy(): {scan['lazy_count']} | Suspense: {scan['suspense_count']} | Route: {scan['route_count']}")
    A(f"- کیفیت TS: `any`×{scan['ts']['any']} | ts-ignore×{scan['ts']['ts_skip']}"
      f" | eslint-disable×{scan['ts']['eslint_disable']} | inline-style×{scan['ts']['inline_style']}")
    A(f"- هوک‌ها: useEffect×{scan['ts']['useEffect']} | useState×{scan['ts']['useState']}")
    A(f"- فایل‌های تست فرانت‌اند: {fe_tests}")
    A("")

    # ۹) امنیت
    A("## ۹) امنیت")
    A("")
    if findings:
        sev_order = {"بالا": 0, "متوسط": 1, "کم": 2, "اطلاع": 3}
        findings.sort(key=lambda x: sev_order.get(x["severity"], 9))
        A("| شدت | قانون | فایل:خط |")
        A("|---|---|---|")
        for fd in findings[:40]:
            loc = f"`{fd['file']}:{fd['line']}`" if fd["line"] else f"`{fd['file']}`"
            A(f"| {fd['severity']} | {fd['rule']} | {loc} |")
        if len(findings) > 40:
            A(f"| … | و {len(findings) - 40} مورد دیگر | |")
        A("")
        A("> 🔐 مقادیر محرمانه به متغیر محیطی منتقل و از تاریخچهٔ گیت پاک‌سازی شوند. "
          "این اسکن جایگزین ابزارهای تخصصی (`gitleaks`, `bandit`, `trufflehog`) نیست.")
    else:
        A("- ✅ الگوی مشکوک شناخته‌شده‌ای یافت نشد (جایگزین gitleaks/bandit نیست).")
    A("")

    # ۱۰) کیفیت پایتون
    A("## ۱۰) کیفیت کد پایتون (AST)")
    A("")
    A(f"- فایل‌های تحلیل‌شده: {py['files']} | توابع: {py['functions']} | کلاس‌ها: {py['classes']}")
    if py["parse_errors"]:
        A(f"- ❌ خطای سینتکس در {len(py['parse_errors'])} فایل:")
        for e in py["parse_errors"][:8]:
            A(f"  - `{e}`")
    A(f"- پوشش docstring: **{doc_pct}٪** ({py['doc_present']}/{doc_total})")
    A(f"- توابع دارای return annotation: **{typed_pct}٪**")
    if py["bare_except"]:
        A(f"- ⚠️ except خام: {py['bare_except']} مورد")
    if py["max_args"][0]:
        A(f"- بیشترین آرگومان تابع: {py['max_args'][0]} → `{py['max_args'][1]}`")
    if py["longest_func"][0]:
        A(f"- طولانی‌ترین تابع: {py['longest_func'][0]} خط → `{py['longest_func'][1]}`")
    if py["complexity_top"]:
        A("")
        A("### پیچیدگی شناختی برتر (تقریبی)")
        A("")
        A("| پیچیدگی | فایل |")
        A("|---:|---|")
        for c, rel_c in py["complexity_top"][:10]:
            A(f"| {c} | `{rel_c}` |")
    if py["imports"]:
        A("")
        A("### پرتکرارترین ماژول‌های importشده (شامل ماژول‌های داخلی)")
        A("")
        A(", ".join(f"`{k}`×{v}" for k, v in py["imports"].most_common(15)))
    A("")

    # ۱۱) پایگاه‌داده
    A("## ۱۱) پایگاه‌داده و ORM")
    A("")
    A("- سیستم‌های شناسایی‌شده: " + (", ".join(db["systems"]) if db["systems"] else "—"))
    A(f"- کلاس‌های Model (تقریبی): {scan['models_count']}")
    A(f"- فایل‌های مهاجرت (migrations): {db['migrations']}")
    A("")

    # ۱۲) تکرار کد
    if not args.no_dupes:
        A("## ۱۲) تکرار کد (تقریبی)")
        A("")
        A(f"- گروه‌های بلوک تکراری (≥۸ خط یکسان): **{dupe_groups}**")
        for _, locs in dupes[:8]:
            A("  - " + " · ".join(f"`{r}:{ln}`" for r, ln in locs[:4]))
        A("")

    # ۱۳) مستندات
    A("## ۱۳) مستندات و لایسنس")
    A("")
    r = docs["readme"]
    if r:
        A(f"- README (`{r['file']}`): {r['lines']} خط، {r['headings']} سرفصل، "
          f"{r['code_blocks']} بلوک کد")
        if r["sections"]:
            A(f"- بخش‌های یافت‌شده: {', '.join(r['sections'])}")
        else:
            A("- ⚠️ بخش‌های استاندارد (نصب/اجرا) در README دیده نشد.")
    else:
        A("- ❌ README یافت نشد.")
    A(f"- لایسنس: {docs['license'] or '❌ یافت نشد'}")
    A(f"- پوشهٔ docs: {'✅ ' + str(docs['docs_files']) + ' فایل' if docs['has_docs_dir'] else '—'}")
    A(f"- CHANGELOG: {'✅' if docs['changelog'] else '—'} | "
      f"CONTRIBUTING: {'✅' if docs['contributing'] else '—'}")
    A("")

    # ۱۴) فعالیت و تازگی
    A("## ۱۴) فعالیت و تازگی")
    A("")
    A(f"- فایل‌های تغییر‌کرده در ۷ روز اخیر: {sz_extra['fresh7']:,}")
    A(f"- فایل‌های تغییر‌کرده در ۳۰ روز اخیر: {sz_extra['fresh30']:,}")
    A(f"- جدیدترین فایل: `{sz_extra['newest']}`")
    A(f"- فایل‌های خالی: {sz_extra['empty_files']:,} | پوشه‌های خالی: {sz_extra['empty_dirs']}")
    A("")

    # ۱۵) معماری
    A("## ۱۵) معماری و نقاط ورود")
    A("")
    A(f"- سبک شناسایی‌شده: **{arch['style']}**")
    A("- پوشه‌های سطح بالا: " + (", ".join(f"`{d}`" for d in arch["top_dirs"]) or "—"))
    A("- نقاط ورود: " + (", ".join(f"`{e}`" for e in arch["entry_points"]) or "—"))
    A("")

    # ۱۶) هشدارها
    A("## ۱۶) هشدارها و سلامت پروژه")
    A("")
    if not gi_ok:
        A("- ❌ `.gitignore` وجود ندارد.")
    elif gi_missing:
        A("- ⚠️ موارد جاافتاده در `.gitignore`: "
          + ", ".join(f"`{x}`" for x in gi_missing))
    else:
        A("- ✅ `.gitignore` کامل است.")
    for d, n in tracked_bad.items():
        A(f"- 🚨 `{d}` در گیت track شده ({n} فایل) → `git rm -r --cached {d}`")
    if envs:
        A("- 📁 فایل‌های env (فقط نام کلیدها بررسی شد): "
          + ", ".join(f"`{e}`" for e in envs))
    if (root / "htmlcov").exists():
        A("- ⚠️ پوشه `htmlcov` (خروجی coverage) موجود است؛ پاک/ignore شود.")
    if scan["todo_total"]:
        A(f"- 📝 TODO/FIXME: **{scan['todo_total']}** مورد")
        for s in scan["todo_samples"]:
            A(f"  - {s}")
    if cl_total:
        top = ", ".join(f"`{f2}` ({n})" for f2, n in scan["console_files"].most_common(3))
        A(f"- 🖥️ console.log در فرانت: {cl_total} مورد — بیشترین: {top}")
    if pr_total:
        A(f"- 🐍 print() در پایتون: {pr_total} مورد (در پروداکشن از logging استفاده شود)")
    if lh_total:
        top_lh = ", ".join(f"`{f3}` ({n})" for f3, n in scan["localhost_files"].most_common(5))
        A(f"- 🔗 آدرس localhost هاردکد: {lh_total} مورد — بیشترین: {top_lh}")
    if has_fe and fe_tests == 0:
        A("- ❌ تستی برای فرانت‌اند وجود ندارد (پیشنهاد: Vitest + Testing Library).")
    if be_tests == 0:
        A("- ⚠️ تست بک‌اند در مسیرهای رایج یافت نشد.")
    for size_b, rel_path in [x for x in largest if x[0] > 1_000_000][:5]:
        A(f"- 📦 فایل حجیم: `{rel_path}` ({human_size(size_b)})")
    A("")

    # ۱۷) امتیازدهی تفصیلی
    A("## ۱۷) امتیازدهی تفصیلی")
    A("")
    A(f"**امتیاز نهایی: {score}/100 — گرید {grade} {grade_emoji}**")
    A("")
    A("| کسر | دلیل |")
    A("|---:|---|")
    for p, reason in sorted(deductions, reverse=True):
        A(f"| -{p} | {reason} |")
    if not deductions:
        A("| — | هیچ کسری ثبت نشد 🎉 |")
    A("")

    # ۱۸) اقدامات پیشنهادی
    A("## ۱۸) اقدامات پیشنهادی")
    A("")
    recs = []
    if findings:
        recs.append("رسیدگی به یافته‌های امنیتی بخش ۹؛ انتقال کلیدها به متغیر محیطی "
                    "و افزودن gitleaks به CI")
    if fe_tests == 0 and has_fe:
        recs.append("افزودن Vitest و Testing Library برای تست فرانت‌اند")
    if be_tests == 0:
        recs.append("راه‌اندازی pytest و نوشتن تست برای بک‌اند")
    if (root / "htmlcov").exists():
        recs.append("حذف و ignore کردن پوشه `htmlcov`")
    if cl_total > 50:
        recs.append("پاک‌سازی console.logها (قانون no-console در ESLint)")
    if scan["lazy_count"] < 3 and ext_count.get(".tsx", 0) > 30:
        recs.append("Lazy loading مسیرها برای کاهش حجم باندل اولیه")
    if deps["npm"] and not deps["lockfile"]:
        recs.append("کامیت کردن lockfile برای بیلد تکرارپذیر")
    if deps["unpinned"]:
        recs.append("پین‌کردن نسخه‌های requirements.txt و اجرای دوره‌ای `pip-audit` / `npm audit`")
    if typed_pct < 50 and py["functions"]:
        recs.append("افزودن type hint به توابع پایتون و افزودن mypy به CI")
    if doc_total and doc_pct < 40:
        recs.append("افزودن docstring برای توابع و کلاس‌های کلیدی")
    if py["bare_except"] > 0:
        recs.append("جایگزینی exceptهای خام با استثناهای مشخص + لاگ خطا")
    if scan["ts"]["any"] > 30:
        recs.append("کاهش استفاده از `any` در TypeScript (فعال‌کردن strict mode)")
    if dupe_groups > 20:
        recs.append("بازآرایی (refactor) بلوک‌های تکراری به توابع/ماژول مشترک")
    if not docs["license"]:
        recs.append("افزودن فایل LICENSE")
    recs += ["اجرای `npx depcheck` برای یافتن وابستگی‌های بلااستفاده",
             "اجرای `npx vite-bundle-visualizer` برای تحلیل حجم باندل"]
    for i, r_item in enumerate(recs, 1):
        A(f"{i}. {r_item}")
    A("")

    # ---------- ذخیره ----------
    md_name = f"{args.out}.md" if args.out else "PROJECT_REPORT.md"
    json_name = f"{args.out}.json" if args.out else "project_report.json"
    (root / md_name).write_text("\n".join(md), encoding="utf-8")
    (root / json_name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")

    dur = (datetime.now() - t0).total_seconds()
    print()
    print("=" * 62)
    logger.info(f"✅ تحلیل کامل شد ({dur:.1f} ثانیه)")
    print(f"   ⭐ امتیاز سلامت: {score}/100 ({grade}) | فناوری‌ها: {len(techs)} | "
          f"فایل‌ها: {total_files:,}")
    print(f"   اندپوینت‌ها: {len(scan['endpoints'])} | خطوط کد: {loc_code:,}")
    print(f"   امنیت: {len(sec_high)} بالا / {len(sec_med)} متوسط | "
          f"TODO: {scan['todo_total']} | console.log: {cl_total}")
    logger.info("-" * 62)
    logger.info(f"📄 گزارش کامل:   {md_name}")
    logger.info(f"🗂️ داده ساختاریافته: {json_name}")
    logger.info("=" * 62)


if __name__ == "__main__":
    main()