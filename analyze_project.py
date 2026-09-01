# -*- coding: utf-8 -*-
"""
analyze_project.py — تحلیل جامع پروژه و تولید گزارش کامل
اجرا:   python analyze_project.py  [مسیر اختیاری پروژه]
خروجی:  PROJECT_REPORT.md  +  project_report.json
نیازمندی: فقط پایتون استاندارد (بدون pip install)
"""

import structlog

logger = structlog.get_logger()
import os
import re
import sys
import json
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

# ---------------- تنظیمات ----------------
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".next", ".nuxt", ".output",
    "coverage", "htmlcov", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "staticfiles", "media", "artifacts", ".cache", "target", "out",
}

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".scss",
            ".less", ".html", ".htm", ".vue", ".svelte"}

PY_FRAMEWORKS = {"django": "Django", "flask": "Flask", "fastapi": "FastAPI",
                 "tornado": "Tornado", "pyramid": "Pyramid", "starlette": "Starlette"}

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
}

CDN_PATTERNS = [
    (re.compile(r"<script[^>]+tailwind", re.I), "Tailwind CSS (CDN)"),
    (re.compile(r"<(?:script|link)[^>]+bootstrap", re.I), "Bootstrap (CDN)"),
    (re.compile(r"<script[^>]+jquery", re.I), "jQuery (CDN)"),
    (re.compile(r"<script[^>]+vue[^>]*\.js", re.I), "Vue (CDN)"),
    (re.compile(r"<script[^>]+htmx", re.I), "HTMX (CDN)"),
    (re.compile(r"<link[^>]+fonts\.googleapis", re.I), "Google Fonts"),
]

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
    if run_git(root, ["rev-parse", "--is-inside-work-tree"]) != "true\n":
        if run_git(root, ["rev-parse", "--is-inside-work-tree"]) != "true":
            return {}
    info = {}
    info["branch"] = (run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"]) or "").strip()
    info["last_commit"] = (run_git(root, ["log", "-1", "--format=%h | %ad | %an: %s",
                                          "--date=short"]) or "").strip()
    info["total_commits"] = (run_git(root, ["rev-list", "--count", "HEAD"]) or "").strip()
    info["remote"] = (run_git(root, ["remote", "get-url", "origin"]) or "").strip()
    st = run_git(root, ["status", "--porcelain"]) or ""
    info["uncommitted"] = len([l for l in st.splitlines() if l.strip()])
    return info


def git_tracked_bad(root: Path) -> dict:
    """پوشه‌هایی که نباید در گیت باشند ولی track شده‌اند"""
    out = {}
    for d in ("htmlcov", "node_modules", ".venv", "dist", "frontend/dist",
              "frontend/node_modules"):
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
    lines = []
    truncated = []
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


# ---------------- ۳) آمار حجم فایل‌ها ----------------
def scan_sizes(root: Path):
    ext_count, ext_size = Counter(), Counter()
    total_files = total_size = 0
    largest = []
    for f in walk_files(root):
        try:
            size = f.stat().st_size
        except OSError:
            continue
        ext = f.suffix.lower() or "(بدون پسوند)"
        ext_count[ext] += 1
        ext_size[ext] += size
        total_files += 1
        total_size += size
        largest.append((size, f.relative_to(root).as_posix()))
    largest.sort(reverse=True)
    return ext_count, ext_size, total_files, total_size, largest


# ---------------- ۴) اسکن عمیق کد ----------------
def deep_scan(root: Path) -> dict:
    lang = defaultdict(lambda: {"files": 0, "lines": 0, "code": 0,
                                "comment": 0, "blank": 0})
    todo_total, todo_samples = 0, []
    console_files, print_files, os.environ.get('HOST', 'localhost')_files = Counter(), Counter(), Counter()
    endpoints, ws_endpoints = [], []
    lazy_count = suspense_count = route_count = 0
    cdn_techs = Counter()

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
        if ext == ".tsx":
            suspense_count += len(re.findall(r"<Suspense\b", text))

        # --- بک‌اند ---
        if is_py:
            n = len(re.findall(r"(?<![\w.])print\(", text))
            if n:
                print_files[rel] += n
            for m in re.finditer(r"@\w+\.(get|post|put|delete|patch|head|options)"
                                 r"\(\s*[\"']([^\"']*)[\"']", text):
                endpoints.append((m.group(1).upper(), m.group(2) or "/", rel))
            for m in re.finditer(r"@\w+\.websocket\(\s*[\"']([^\"']*)[\"']", text):
                ws_endpoints.append((m.group(1), rel))

        # --- os.environ.get('HOST', 'localhost') هاردکد ---
        for m in re.finditer(r"https?://(?:os.environ.get('HOST', 'localhost')|127\.0\.0\.1)[^\s\"'<>]*", text):
            os.environ.get('HOST', 'localhost')_files[rel] += 1

        # --- CDN در HTML ---
        if ext in {".html", ".htm"}:
            for pat, label in CDN_PATTERNS:
                if pat.search(text):
                    cdn_techs[label] += 1

    return {"lang": dict(lang), "todo_total": todo_total,
            "todo_samples": todo_samples, "console_files": console_files,
            "print_files": print_files, "os.environ.get('HOST', 'localhost')_files": os.environ.get('HOST', 'localhost')_files,
            "endpoints": endpoints, "ws_endpoints": ws_endpoints,
            "lazy_count": lazy_count, "suspense_count": suspense_count,
            "route_count": route_count, "cdn_techs": cdn_techs}


# ---------------- ۵) فناوری‌ها و وابستگی‌ها ----------------
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
    out = {"npm": None, "scripts": {}, "requirements": [],
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
            break
    out["pyproject"] = (root / "pyproject.toml").exists()
    return out


def analyze_devops(root: Path) -> list:
    found = []
    checks = [
        ("Dockerfile", "Dockerfile"), ("backend/Dockerfile", "Dockerfile (backend)"),
        ("docker-compose.yml", "Docker Compose"), ("docker-compose.yaml", "Docker Compose"),
        ("alembic.ini", "Alembic (مهاجرت DB)"), ("backend/alembic.ini", "Alembic (مهاجرت DB)"),
        ("Makefile", "Makefile"), ("nginx.conf", "Nginx"),
        ("README.md", "README.md"), (".env.example", "نمونه .env"),
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
def main():
    t0 = datetime.now()
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not root.is_dir():
        logger.info(f"❌ مسیر پیدا نشد: {root}")
        sys.exit(1)

    logger.info(f"🔍 در حال تحلیل: {root} ...")
    data = {"meta": {"path": str(root),
                     "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                     "python": platform.python_version(),
                     "os": f"{platform.system()} {platform.release()}"}}

    git = git_info(root)
    ext_count, ext_size, total_files, total_size, largest = scan_sizes(root)
    scan = deep_scan(root)
    deps = analyze_deps(root)
    devops = analyze_devops(root)
    envs = find_env_files(root)
    gi_ok, gi_missing = check_gitignore(root)
    tracked_bad = git_tracked_bad(root)
    be_tests, fe_tests = detect_tests(root)
    techs = detect_techs(root) | set(scan["cdn_techs"].keys())

    cl_total = sum(scan["console_files"].values())
    pr_total = sum(scan["print_files"].values())
    loc_code = sum(r["code"] for r in scan["lang"].values())
    methods = Counter(m for m, _, _ in scan["endpoints"])

    data.update({"techs": sorted(techs), "git": git,
                 "stats": {"total_files": total_files, "total_size": total_size,
                           "loc_code": loc_code,
                           "endpoints": len(scan["endpoints"]),
                           "tests_backend": be_tests, "tests_frontend": fe_tests},
                 "endpoints": scan["endpoints"],
                 "ws_endpoints": scan["ws_endpoints"],
                 "dependencies": deps, "devops": devops, "env_files": envs,
                 "langs": scan["lang"],
                 "health": {"gitignore_missing": gi_missing if gi_ok else None,
                            "tracked_build_dirs": tracked_bad,
                            "todo_total": scan["todo_total"],
                            "console_log_total": cl_total, "print_total": pr_total}})

    # ---------- ساخت مارک‌داون ----------
    md = []
    A = md.append
    A(f"# 📊 گزارش جامع پروژه — {root.name}")
    A("")
    A(f"- **تاریخ تولید:** {data['meta']['generated']}")
    A(f"- **مسیر:** `{root}`")
    A(f"- **محیط:** Python {data['meta']['python']} | {data['meta']['os']}")
    A(f"- **مدت اسکن:** {(datetime.now() - t0).total_seconds():.1f} ثانیه")
    A("")

    A("## ۱) خلاصه اجرایی")
    A("")
    A("| مورد | مقدار |")
    A("|---|---|")
    A(f"| کل فایل‌ها | {total_files:,} |")
    A(f"| حجم کل | {human_size(total_size)} |")
    A(f"| خطوط کد واقعی | {loc_code:,} |")
    A(f"| اندپوینت‌های API | {len(scan['endpoints'])} |")
    A(f"| کامپوننت‌های React (tsx) | {ext_count.get('.tsx', 0)} |")
    A(f"| تست بک‌اند / فرانت‌اند | {be_tests} / {fe_tests} فایل |")
    A("")
    A("**استک:** " + " · ".join(sorted(techs)))
    if devops:
        A("")
        A("**ابزارها:** " + " · ".join(devops))
    A("")

    A("## ۲) وضعیت Git")
    A("")
    if git:
        A(f"- شاخه: `{git.get('branch')}`")
        A(f"- آخرین کامیت: {git.get('last_commit')}")
        A(f"- تعداد کامیت‌ها: {git.get('total_commits')}")
        A(f"- ریموت: `{git.get('remote')}`")
        A(f"- تغییرات کامیت‌نشده: {git.get('uncommitted')} فایل")
    else:
        A("- ریپازیتوری Git یافت نشد.")
    A("")

    A("## ۳) ساختار پوشه‌ها (تا عمق ۳)")
    A("")
    A("```text")
    tree_lines, truncated = build_tree(root, max_depth=3)
    md.extend(tree_lines)
    if truncated:
        A(f"… و {len(truncated)} زیرپوشه در عمق بیشتر")
    A("```")
    A("")

    A("## ۴) آمار فایل‌ها بر اساس نوع")
    A("")
    A("| پسوند | تعداد | حجم |")
    A("|---|---:|---:|")
    for ext, cnt in ext_count.most_common(25):
        A(f"| `{ext}` | {cnt:,} | {human_size(ext_size[ext])} |")
    A("")

    A("## ۵) بزرگ‌ترین فایل‌ها")
    A("")
    A("| حجم | فایل |")
    A("|---:|---|")
    for size, rel in largest[:15]:
        A(f"| {human_size(size)} | `{rel}`{' ⚠️' if size > 1_000_000 else ''} |")
    A("")

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
    else:
        A("- یافت نشد")
    A(f"- pyproject.toml: {'✅ موجود' if deps['pyproject'] else '—'}")
    A(f"- lockfile فرانت‌اند: {('✅ ' + deps['lockfile']) if deps['lockfile'] else '❌ یافت نشد'}")
    A("")

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

    A("## ۸) فرانت‌اند (React)")
    A("")
    A(f"- کامپوننت‌های TSX: {ext_count.get('.tsx', 0)}")
    pages = root / "frontend" / "src" / "pages"
    if pages.is_dir():
        n_pages = sum(1 for f in walk_files(pages) if f.suffix in {".tsx", ".ts"})
        A(f"- صفحات (src/pages): {n_pages}")
    A(f"- lazy(): {scan['lazy_count']} | Suspense: {scan['suspense_count']} | Route: {scan['route_count']}")
    A(f"- فایل‌های تست فرانت‌اند: {fe_tests}")
    A("")

    A("## ۹) سلامت پروژه و هشدارها")
    A("")
    if not gi_ok:
        A("- ❌ `.gitignore` وجود ندارد.")
    elif gi_missing:
        A(f"- ⚠️ موارد جاافتاده در `.gitignore`: "
          + ", ".join(f"`{x}`" for x in gi_missing))
    else:
        A("- ✅ `.gitignore` کامل است.")
    for d, n in tracked_bad.items():
        A(f"- 🚨 `{d}` در گیت track شده ({n} فایل) → `git rm -r --cached {d}`")
    if envs:
        A("- 📁 فایل‌های env (محتوا خوانده نشد): "
          + ", ".join(f"`{e}`" for e in envs))
    if (root / "htmlcov").exists():
        A("- ⚠️ پوشه `htmlcov` (خروجی coverage) موجود است؛ پاک/ignore شود.")
    if scan["todo_total"]:
        A(f"- 📝 TODO/FIXME: **{scan['todo_total']}** مورد")
        for s in scan["todo_samples"]:
            A(f"  - {s}")
    if cl_total:
        top = ", ".join(f"`{f}` ({n})" for f, n in scan["console_files"].most_common(3))
        A(f"- 🖥️ console.log در فرانت: {cl_total} مورد — بیشترین: {top}")
    if pr_total:
        A(f"- 🐍 print() در پایتون: {pr_total} مورد (در پروداکشن از logging استفاده شود)")
    if scan["os.environ.get('HOST', 'localhost')_files"]:
        lh = ", ".join(f"`{f}` ({n})" for f, n in scan["os.environ.get('HOST', 'localhost')_files"].most_common(5))
        A(f"- 🔗 os.environ.get('HOST', 'localhost') هاردکد در {len(scan['os.environ.get('HOST', 'localhost')_files'])} فایل: {lh}")
    if fe_tests == 0:
        A("- ❌ تستی برای فرانت‌اند وجود ندارد (پیشنهاد: Vitest + Testing Library).")
    if be_tests == 0:
        A("- ⚠️ تست بک‌اند در مسیرهای رایج یافت نشد.")
    for size, rel in [x for x in largest if x[0] > 1_000_000][:5]:
        A(f"- 📦 فایل حجیم: `{rel}` ({human_size(size)})")
    A("")

    A("## ۱۰) اقدامات پیشنهادی")
    A("")
    recs = []
    if fe_tests == 0:
        recs.append("افزودن Vitest و Testing Library برای تست فرانت‌اند")
    if (root / "htmlcov").exists():
        recs.append("حذف و ignore کردن پوشه `htmlcov`")
    if cl_total > 50:
        recs.append("پاک‌سازی console.logها (قانون no-console در ESLint)")
    if scan["lazy_count"] < 3 and ext_count.get(".tsx", 0) > 30:
        recs.append("Lazy loading مسیرها برای کاهش حجم باندل اولیه")
    if deps["npm"] and not deps["lockfile"]:
        recs.append("کامیت کردن lockfile برای بیلد تکرارپذیر")
    recs += ["اجرای `npx depcheck` برای یافتن وابستگی‌های بلااستفاده",
             "اجرای `npx vite-bundle-visualizer` برای تحلیل حجم باندل"]
    for i, r in enumerate(recs, 1):
        A(f"{i}. {r}")
    A("")

    # ---------- ذخیره ----------
    (root / "PROJECT_REPORT.md").write_text("\n".join(md), encoding="utf-8")
    (root / "project_report.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")

    dur = (datetime.now() - t0).total_seconds()
    logger.info()
    logger.info("=" * 62)
    logger.info(f"✅ تحلیل کامل شد ({dur:.1f} ثانیه)")
    print(f"   فناوری‌ها: {len(techs)} | فایل‌ها: {total_files:,} | "
          f"اندپوینت‌ها: {len(scan['endpoints'])}")
    print(f"   خطوط کد: {loc_code:,} | TODO: {scan['todo_total']} | "
          f"console.log: {cl_total}")
    logger.info("-" * 62)
    logger.info("📄 گزارش کامل:   PROJECT_REPORT.md")
    logger.info("🗂️ داده ساختاریافته: project_report.json")
    logger.info("=" * 62)


if __name__ == "__main__":
    main()