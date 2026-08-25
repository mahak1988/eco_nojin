#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eco Nojin - فاز ۳: تحلیل ماژول‌های Skeleton
═══════════════════════════════════════════════════════════════════════
این اسکریپت ماژول‌های با Maturity پایین (0-1) را تحلیل می‌کند و
آن‌ها را بر اساس ارزش کسب‌وکاری و قابلیت تکمیل رتبه‌بندی می‌کند.

اصل: Chesterton's Fence - قبل از اقدام، باید بدانیم چرا هر ماژول ناقص است.

اجرا: python phase3_analyze_skeleton_modules.py
"""

import ast
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

PROJECT_ROOT = Path("D:/eco_nojin")
SERVICES_ROOT = PROJECT_ROOT / "services"

IGNORE_DIRS = {
    '__pycache__', 'node_modules', '.git', '.venv', 'venv',
    '_trash', '_backups_fix', '_backup_', '.pytest_cache',
    'htmlcov', 'security_backup', 'tests'
}

# ماژول‌های Skeleton (Maturity 0-1) از گزارش فاز ۱
SKELETON_MODULES = [
    'admin', 'analytics', 'api_gateway', 'auth', 'bots',
    'business_modules', 'carbon', 'content', 'data_sources',
    'design_engine', 'field_monitoring', 'ledger', 'map_engine',
    'mobile_monitoring', 'models', 'reporting', 'satellite',
    'science', 'scientific_motors', 'supabase', 'telegram_bot', 'workflow'
]

# اولویت‌های کسب‌وکاری (Business Value)
BUSINESS_PRIORITY = {
    # Tier 1: هسته کسب‌وکار - باید کامل شوند
    'analytics': 10,      # گزارش‌گیری و تحلیل
    'auth': 9,            # احراز هویت (امنیتی)
    'admin': 8,           # پنل مدیریت
    'reporting': 8,       # گزارش‌های رسمی
    
    # Tier 2: ویژگی‌های کلیدی
    'bots': 7,            # ربات‌های تعاملی
    'satellite': 7,       # داده‌های ماهواره‌ای
    'telegram_bot': 6,    # ارتباط با کاربران
    'notification': 6,    # اطلاع‌رسانی
    'map_engine': 6,      # نقشه و GIS
    
    # Tier 3: ویژگی‌های پیشرفته
    'carbon': 5,          # اعتبار کربن
    'design_engine': 5,   # طراحی مهندسی
    'scientific_motors': 5,  # موتورهای علمی
    'science': 4,         # ماژول علمی
    
    # Tier 4: پشتیبانی
    'ledger': 4,          # دفتر کل
    'workflow': 4,        # گردش کار
    'field_monitoring': 3,   # پایش میدانی
    'mobile_monitoring': 3,  # پایش موبایل
    
    # Tier 5: ادغام خارجی
    'supabase': 3,        # Backend as a Service
    'data_sources': 2,    # منابع داده
    'content': 2,         # مدیریت محتوا
    
    # Tier 6: نیاز به بررسی (شاید حذف شوند)
    'models': 1,          # ممکن است redundant باشد
    'business_modules': 1,  # پس از فاز ۲ باید بررسی شود
    'api_gateway': 1,     # Hub، تکمیل تدریجی
}


def log(msg, icon="i"):
    print(f"  [{icon}] {msg}")


def separator(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def should_ignore(path):
    return any(p in str(path) for p in IGNORE_DIRS)


def read_file(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
# تحلیل عمیق هر ماژول
# ═══════════════════════════════════════════════════════════════

class ModuleAnalyzer:
    def __init__(self, name: str):
        self.name = name
        self.path = SERVICES_ROOT / name
        self.result = {
            'name': name,
            'exists': False,
            'file_count': 0,
            'py_files': [],
            'total_lines': 0,
            'classes': [],
            'functions': [],
            'services': [],
            'external_deps': [],
            'internal_deps': [],
            'has_docstrings': False,
            'has_type_hints': False,
            'readme_exists': False,
            'git_commits': 0,
            'last_commit_date': None,
            'maturity_score': 0,
            'business_priority': BUSINESS_PRIORITY.get(name, 0),
            'completion_effort': 'Unknown',  # Low/Medium/High
            'recommended_action': 'Unknown',
        }
    
    def analyze(self):
        """تحلیل کامل ماژول"""
        if not self.path.exists():
            return self.result
        
        self.result['exists'] = True
        
        # جمع‌آوری فایل‌ها
        for item in self.path.rglob('*'):
            if should_ignore(item) or not item.is_file():
                continue
            
            rel = str(item.relative_to(self.path))
            
            if item.name == 'README.md':
                self.result['readme_exists'] = True
            
            if item.suffix == '.py':
                self.result['py_files'].append(rel)
                
                if item.name.startswith('test_'):
                    continue
                
                content = read_file(item)
                if not content:
                    continue
                
                lines = content.split('\n')
                self.result['total_lines'] += len(lines)
                
                # AST parsing
                try:
                    tree = ast.parse(content)
                except SyntaxError:
                    continue
                
                # استخراج classes و functions
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.ClassDef):
                        self.result['classes'].append({
                            'name': node.name,
                            'file': rel,
                            'methods': len([n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]),
                        })
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.result['functions'].append({
                            'name': node.name,
                            'file': rel,
                        })
                
                # استخراج imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        if node.module.startswith(('services.', 'engine.', 'database.')):
                            self.result['internal_deps'].append(node.module)
                        elif not node.module.startswith(('sqlalchemy', 'pydantic', 'fastapi', 'typing', 'datetime')):
                            self.result['external_deps'].append(node.module.split('.')[0])
        
        self.result['file_count'] = len(self.result['py_files'])
        
        # شمارش service classes
        self.result['services'] = [
            c for c in self.result['classes']
            if 'Service' in c['name'] or 'service' in c['file']
        ]
        
        # محاسبه Maturity
        self._calculate_maturity()
        
        # تخمین effort
        self._estimate_effort()
        
        # تعیین اقدام پیشنهادی
        self._recommend_action()
        
        # Git history
        self._analyze_git()
        
        return self.result
    
    def _calculate_maturity(self):
        """محاسبه Maturity Score"""
        score = 0
        
        has_models = any('model' in c['file'] or 'Model' in c['name'] for c in self.result['classes'])
        has_service = len(self.result['services']) > 0
        has_api = any('api' in f or 'router' in f for f in self.result['py_files'])
        has_tests = any('test_' in f for f in self.result['py_files'])
        has_schemas = any('schema' in f for f in self.result['py_files'])
        has_repositories = any('repositor' in f for f in self.result['py_files'])
        
        if has_models: score += 1
        if has_service: score += 1
        if has_api: score += 1
        if has_tests: score += 1
        if has_schemas: score += 1
        if has_repositories: score += 1
        
        # Bonus برای README
        if self.result['readme_exists']:
            score += 1
        
        # Bonus برای مستندات کد
        if self.result['total_lines'] > 100:
            score += 1
        if self.result['total_lines'] > 500:
            score += 1
        
        self.result['maturity_score'] = score
    
    def _estimate_effort(self):
        """تخمین تلاش مورد نیاز برای تکمیل"""
        lines = self.result['total_lines']
        files = self.result['file_count']
        classes = len(self.result['classes'])
        
        if lines < 50 and files <= 2:
            self.result['completion_effort'] = 'Low'
        elif lines < 300 and files <= 5:
            self.result['completion_effort'] = 'Medium'
        else:
            self.result['completion_effort'] = 'High'
    
    def _recommend_action(self):
        """تعیین اقدام پیشنهادی"""
        maturity = self.result['maturity_score']
        priority = self.result['business_priority']
        effort = self.result['completion_effort']
        
        # ماتریس تصمیم
        if priority >= 8 and maturity <= 2:
            self.result['recommended_action'] = 'URGENT_COMPLETE'
        elif priority >= 6 and maturity <= 2 and effort != 'High':
            self.result['recommended_action'] = 'COMPLETE'
        elif priority >= 5 and maturity == 1:
            self.result['recommended_action'] = 'ENHANCE'
        elif priority <= 2 and maturity == 0:
            self.result['recommended_action'] = 'CANDIDATE_FOR_REMOVAL'
        elif maturity == 0 and self.result['file_count'] <= 1:
            self.result['recommended_action'] = 'PLACEHOLDER_CHECK'
        else:
            self.result['recommended_action'] = 'REVIEW'
    
    def _analyze_git(self):
        """تحلیل Git history"""
        try:
            proc = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD', '--', str(self.path)],
                cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0:
                try:
                    self.result['git_commits'] = int(proc.stdout.strip())
                except ValueError:
                    pass
            
            proc = subprocess.run(
                ['git', 'log', '-1', '--format=%ci', '--', str(self.path)],
                cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=10,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                self.result['last_commit_date'] = proc.stdout.strip()[:10]
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
# تولید گزارش
# ═══════════════════════════════════════════════════════════════

def generate_report(analyses: List[Dict]) -> Path:
    separator("تولید گزارش نهایی")
    
    report = []
    report.append("# 📊 گزارش تحلیل ماژول‌های Skeleton - فاز ۳\n\n")
    report.append(f"**تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    report.append("**اصل:** Chesterton's Fence - قبل از اقدام، باید بدانیم چرا هر ماژول ناقص است.\n\n")
    report.append("---\n\n")
    
    # مرتب‌سازی بر اساس اولویت کسب‌وکاری
    sorted_analyses = sorted(analyses, key=lambda x: -x['business_priority'])
    
    # خلاصه اجرایی
    report.append("## 🎯 خلاصه اجرایی\n\n")
    
    action_groups = defaultdict(list)
    for a in sorted_analyses:
        action_groups[a['recommended_action']].append(a)
    
    report.append("| اقدام پیشنهادی | تعداد | اولویت‌های بالا |\n")
    report.append("|---|---|---|\n")
    
    action_labels = {
        'URGENT_COMPLETE': '🚨 تکمیل فوری',
        'COMPLETE': '✅ تکمیل',
        'ENHANCE': '🔧 بهبود',
        'REVIEW': '👁️ بررسی',
        'PLACEHOLDER_CHECK': '🔍 بررسی Placeholder',
        'CANDIDATE_FOR_REMOVAL': '🗑️ کاندید حذف',
    }
    
    for action, label in action_labels.items():
        count = len(action_groups.get(action, []))
        high_priority = len([a for a in action_groups.get(action, []) if a['business_priority'] >= 7])
        report.append(f"| {label} | {count} | {high_priority} |\n")
    
    report.append("\n---\n\n")
    
    # ماتریس اولویت
    report.append("## 📊 ماتریس اولویت (Business Priority × Maturity)\n\n")
    report.append("| ماژول | Priority | Maturity | Effort | Files | Lines | اقدام پیشنهادی |\n")
    report.append("|---|---|---|---|---|---|---|\n")
    
    for a in sorted_analyses:
        action = action_labels.get(a['recommended_action'], a['recommended_action'])
        report.append(
            f"| **{a['name']}** | {a['business_priority']}/10 | "
            f"{a['maturity_score']}/10 | {a['completion_effort']} | "
            f"{a['file_count']} | {a['total_lines']} | {action} |\n"
        )
    
    report.append("\n---\n\n")
    
    # تحلیل هر گروه
    for action, label in action_labels.items():
        group = action_groups.get(action, [])
        if not group:
            continue
        
        report.append(f"## {label} ({len(group)} ماژول)\n\n")
        
        for a in group:
            report.append(f"### 📦 `{a['name']}`\n\n")
            report.append(f"- **مسیر:** `services/{a['name']}/`\n")
            report.append(f"- **Priority کسب‌وکاری:** {a['business_priority']}/10\n")
            report.append(f"- **Maturity:** {a['maturity_score']}/10\n")
            report.append(f"- **تعداد فایل:** {a['file_count']}\n")
            report.append(f"- **تعداد خطوط:** {a['total_lines']}\n")
            report.append(f"- **تعداد Classes:** {len(a['classes'])}\n")
            report.append(f"- **Service Classes:** {len(a['services'])}\n")
            report.append(f"- **README:** {'✅' if a['readme_exists'] else '❌'}\n")
            report.append(f"- **Commits:** {a['git_commits']}\n")
            report.append(f"- **آخرین تغییر:** {a['last_commit_date'] or 'N/A'}\n\n")
            
            # Classes
            if a['classes']:
                report.append("**Classes:**\n")
                for c in a['classes'][:10]:
                    report.append(f"- `{c['name']}` in `{c['file']}` ({c['methods']} methods)\n")
                if len(a['classes']) > 10:
                    report.append(f"- ... و {len(a['classes']) - 10} مورد دیگر\n")
                report.append("\n")
            
            # Dependencies
            if a['internal_deps']:
                unique_deps = sorted(set(a['internal_deps']))[:10]
                report.append(f"**وابستگی‌های داخلی:** {', '.join('`' + d + '`' for d in unique_deps)}\n\n")
            
            if a['external_deps']:
                unique_ext = sorted(set(a['external_deps']))[:10]
                report.append(f"**وابستگی‌های خارجی:** {', '.join('`' + d + '`' for d in unique_ext)}\n\n")
            
            report.append("---\n\n")
    
    # نقشه راه پیشنهادی
    report.append("## 🗺️ نقشه راه پیشنهادی فاز ۳\n\n")
    
    report.append("### موج ۱: تکمیل فوری (۱-۲ هفته)\n\n")
    urgent = action_groups.get('URGENT_COMPLETE', [])
    for a in urgent[:4]:
        report.append(f"- **{a['name']}** (Priority {a['business_priority']})\n")
    report.append("\n")
    
    report.append("### موج ۲: تکمیل (۲-۳ هفته)\n\n")
    complete = action_groups.get('COMPLETE', [])
    for a in complete[:5]:
        report.append(f"- **{a['name']}** (Priority {a['business_priority']})\n")
    report.append("\n")
    
    report.append("### موج ۳: بهبود (تدریجی)\n\n")
    enhance = action_groups.get('ENHANCE', [])
    for a in enhance[:5]:
        report.append(f"- **{a['name']}** (Priority {a['business_priority']})\n")
    report.append("\n")
    
    report.append("### کاندید حذف (پس از بررسی)\n\n")
    remove = action_groups.get('CANDIDATE_FOR_REMOVAL', [])
    for a in remove:
        report.append(f"- **{a['name']}** (Priority {a['business_priority']})\n")
    report.append("\n")
    
    report.append("---\n\n")
    report.append("*این گزارش فقط تحلیلی است و هیچ تغییری اعمال نکرده است.*\n")
    report.append("*گام بعدی: اسکریپت `phase3_complete_priority_modules.py` برای تکمیل ماژول‌های موج ۱*\n")
    
    # ذخیره
    report_text = ''.join(report)
    report_file = PROJECT_ROOT / "PHASE3_SKELETON_ANALYSIS.md"
    report_file.write_text(report_text, encoding='utf-8')
    
    log(f"گزارش ذخیره شد: {report_file}", "+")
    return report_file


# ═══════════════════════════════════════════════════════════════
# اجرای اصلی
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("  Eco Nojin - فاز ۳: تحلیل ماژول‌های Skeleton")
    print("=" * 70)
    print("\n  اصل: Chesterton's Fence")
    print("  این اسکریپت فقط تحلیل می‌کند و هیچ تغییری اعمال نمی‌کند.")
    
    separator("تحلیل ماژول‌ها")
    
    analyses = []
    
    for module_name in SKELETON_MODULES:
        log(f"تحلیل {module_name}...", "i")
        analyzer = ModuleAnalyzer(module_name)
        result = analyzer.analyze()
        analyses.append(result)
        
        if result['exists']:
            log(f"  Maturity: {result['maturity_score']}/10 | "
                f"Priority: {result['business_priority']}/10 | "
                f"Action: {result['recommended_action']}", "+")
        else:
            log(f"  یافت نشد", "X")
    
    # گزارش
    report_file = generate_report(analyses)
    
    # خلاصه
    separator("خلاصه نهایی")
    
    print("\n  ماژول‌های تحلیل‌شده:\n")
    
    action_groups = defaultdict(int)
    for a in analyses:
        action_groups[a['recommended_action']] += 1
    
    action_labels = {
        'URGENT_COMPLETE': '🚨 تکمیل فوری',
        'COMPLETE': '✅ تکمیل',
        'ENHANCE': '🔧 بهبود',
        'REVIEW': '👁️ بررسی',
        'PLACEHOLDER_CHECK': '🔍 بررسی Placeholder',
        'CANDIDATE_FOR_REMOVAL': '🗑️ کاندید حذف',
    }
    
    for action, label in action_labels.items():
        count = action_groups.get(action, 0)
        if count > 0:
            print(f"  {label}: {count} ماژول")
    
    print(f"\n  [i] گزارش کامل: {report_file}")
    print("\n  >>> این گزارش فقط تحلیلی است - هیچ تغییری اعمال نشده <<<")
    print("\n  گام بعدی (پس از تأیید گزارش):")
    print("     python phase3_complete_priority_modules.py")
    print("\n" + "=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())