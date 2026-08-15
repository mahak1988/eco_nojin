#!/usr/bin/env python3
"""
Eco Nojin - Comprehensive Project Analyzer
============================================
Multi-dimensional project audit for strategic planning.

Analyzes:
  Phase 1: Inventory & Structure
  Phase 2: Technology Stack
  Phase 3: Architecture Patterns
  Phase 4: Code Quality Metrics
  Phase 5: Security Audit
  Phase 6: Completeness Analysis
  Phase 7: Risk Matrix (SWOT)

Output:
  - project_analysis.json (structured data)
  - project_report.md (human-readable)
  - Console summary

Author: Eco Nojin Strategy Team
Version: 1.0
"""
import os
import sys
import re
import json
import ast
import hashlib
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import subprocess


class ProjectAnalyzer:
    """Main analyzer class with 7-phase audit pipeline."""
    
    # File extensions by category
    EXTENSION_MAP = {
        'python': ['.py', '.pyi', '.pyx'],
        'javascript': ['.js', '.jsx', '.mjs', '.cjs'],
        'typescript': ['.ts', '.tsx'],
        'css': ['.css', '.scss', '.sass', '.less'],
        'html': ['.html', '.htm', '.jsx'],
        'json': ['.json'],
        'yaml': ['.yml', '.yaml'],
        'markdown': ['.md', '.markdown'],
        'config': ['.toml', '.ini', '.cfg', '.conf'],
        'shell': ['.sh', '.bash', '.ps1', '.bat'],
        'data': ['.csv', '.tsv', '.parquet', '.xlsx'],
        'image': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp'],
        'database': ['.db', '.sqlite', '.sqlite3'],
    }
    
    # Ignore patterns
    IGNORE_DIRS = {
        '.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules',
        '.next', '.pytest_cache', '.mypy_cache', '.ruff_cache',
        'build', 'dist', '.idea', '.vscode', 'coverage', 'htmlcov',
        'target', '.cache', 'logs', 'temp', 'tmp'
    }
    
    IGNORE_FILES = {
        '.DS_Store', 'Thumbs.db', '.gitignore', '.env', '.env.local',
        'package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'poetry.lock'
    }
    
    def __init__(self, project_root: str):
        self.root = Path(project_root).resolve()
        self.report = {
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'project_path': str(self.root),
                'analyzer_version': '1.0'
            },
            'phase1_inventory': {},
            'phase2_stack': {},
            'phase3_architecture': {},
            'phase4_quality': {},
            'phase5_security': {},
            'phase6_completeness': {},
            'phase7_risk_matrix': {},
            'recommendations': []
        }
        
        # Caches
        self.all_files: List[Path] = []
        self.all_py_files: List[Path] = []
        self.all_ts_files: List[Path] = []
        
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        parts = path.parts
        return any(p in self.IGNORE_DIRS for p in parts)
    
    def _collect_files(self):
        """Collect all files respecting ignore patterns."""
        print("📂 Collecting files...")
        for root, dirs, files in os.walk(self.root):
            # Filter dirs in-place
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            
            root_path = Path(root)
            for f in files:
                if f in self.IGNORE_FILES:
                    continue
                file_path = root_path / f
                self.all_files.append(file_path)
                
                if f.endswith('.py'):
                    self.all_py_files.append(file_path)
                elif f.endswith(('.ts', '.tsx')):
                    self.all_ts_files.append(file_path)
        
        print(f"   Found {len(self.all_files):,} files")
        print(f"   Python: {len(self.all_py_files):,}")
        print(f"   TypeScript: {len(self.all_ts_files):,}")
    
    # ========================================================================
    # PHASE 1: Inventory & Structure
    # ========================================================================
    def phase1_inventory(self) -> Dict[str, Any]:
        """Analyze project structure and file distribution."""
        print("\n" + "="*70)
        print("  PHASE 1: INVENTORY & STRUCTURE")
        print("="*70)
        
        # Count by extension
        ext_counter = Counter()
        size_by_ext = defaultdict(int)
        empty_files = []
        
        for f in self.all_files:
            ext = f.suffix.lower() or 'no_ext'
            ext_counter[ext] += 1
            
            try:
                size = f.stat().st_size
                size_by_ext[ext] += size
                if size == 0:
                    empty_files.append(str(f.relative_to(self.root)))
            except:
                pass
        
        # Top-level structure
        top_level = {}
        for item in self.root.iterdir():
            if item.name in self.IGNORE_DIRS:
                continue
            if item.is_dir():
                # Count files in this directory
                count = sum(1 for _ in item.rglob('*') if _.is_file())
                top_level[item.name] = {
                    'type': 'directory',
                    'files': count,
                    'size_kb': sum(f.stat().st_size for f in item.rglob('*') 
                                   if f.is_file()) / 1024
                }
            else:
                top_level[item.name] = {
                    'type': 'file',
                    'size_bytes': item.stat().st_size
                }
        
        # Total size
        total_size = sum(size_by_ext.values())
        
        result = {
            'total_files': len(self.all_files),
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'extension_distribution': dict(ext_counter.most_common()),
            'size_by_extension_kb': {k: round(v/1024, 2) for k, v in size_by_ext.items()},
            'empty_files_count': len(empty_files),
            'empty_files_sample': empty_files[:20],
            'top_level_structure': top_level
        }
        
        self.report['phase1_inventory'] = result
        print(f"   Total files: {result['total_files']:,}")
        print(f"   Total size: {result['total_size_mb']:.2f} MB")
        print(f"   Empty files: {result['empty_files_count']}")
        print(f"   Top-level items: {len(top_level)}")
        
        return result
    
    # ========================================================================
    # PHASE 2: Technology Stack
    # ========================================================================
    def phase2_stack(self) -> Dict[str, Any]:
        """Detect technology stack from config files."""
        print("\n" + "="*70)
        print("  PHASE 2: TECHNOLOGY STACK")
        print("="*70)
        
        stack = {
            'languages': {},
            'frameworks': {},
            'tools': [],
            'dependencies': {
                'python': {},
                'javascript': {}
            }
        }
        
        # Languages by LOC count
        loc_by_lang = Counter()
        for f in self.all_files:
            ext = f.suffix.lower()
            for lang, exts in self.EXTENSION_MAP.items():
                if ext in exts:
                    try:
                        lines = sum(1 for _ in f.open(encoding='utf-8', errors='ignore'))
                        loc_by_lang[lang] += lines
                    except:
                        pass
        
        stack['languages'] = dict(loc_by_lang.most_common())
        
        # Python dependencies (pyproject.toml / requirements.txt)
        pyproject = self.root / 'pyproject.toml'
        if pyproject.exists():
            stack['tools'].append('pyproject.toml')
            try:
                import tomllib
                data = tomllib.loads(pyproject.read_text(encoding='utf-8'))
                if 'project' in data:
                    deps = data['project'].get('dependencies', [])
                    for d in deps:
                        name = re.split(r'[=<>!~]', d)[0].strip()
                        stack['dependencies']['python'][name] = d
                    stack['frameworks']['python_project'] = data['project'].get('name', 'unknown')
            except Exception as e:
                stack['dependencies']['python']['_parse_error'] = str(e)
        
        req_txt = self.root / 'requirements.txt'
        if req_txt.exists():
            stack['tools'].append('requirements.txt')
            try:
                for line in req_txt.read_text(encoding='utf-8').splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        name = re.split(r'[=<>!~]', line)[0].strip()
                        stack['dependencies']['python'][name] = line
            except Exception as e:
                stack['dependencies']['python']['_parse_error'] = str(e)
        
        # Frontend dependencies (package.json)
        pkg_json = self.root / 'frontend' / 'package.json'
        if not pkg_json.exists():
            pkg_json = self.root / 'package.json'
        
        if pkg_json.exists():
            stack['tools'].append('package.json')
            try:
                data = json.loads(pkg_json.read_text(encoding='utf-8'))
                for section in ['dependencies', 'devDependencies', 'peerDependencies']:
                    if section in data:
                        for name, version in data[section].items():
                            stack['dependencies']['javascript'][name] = version
                stack['frameworks']['frontend_project'] = data.get('name', 'unknown')
            except Exception as e:
                stack['dependencies']['javascript']['_parse_error'] = str(e)
        
        # Detect key frameworks
        if 'fastapi' in stack['dependencies']['python']:
            stack['frameworks']['backend'] = 'FastAPI'
        if 'next' in stack['dependencies']['javascript']:
            stack['frameworks']['frontend'] = 'Next.js'
        if 'sqlalchemy' in stack['dependencies']['python']:
            stack['frameworks']['orm'] = 'SQLAlchemy'
        if 'alembic' in stack['dependencies']['python']:
            stack['frameworks']['migration'] = 'Alembic'
        
        # Detect CI/CD
        if (self.root / '.github' / 'workflows').exists():
            stack['tools'].append('GitHub Actions')
        if (self.root / 'Dockerfile').exists():
            stack['tools'].append('Docker')
        if (self.root / 'alembic').exists() or (self.root / 'alembic.ini').exists():
            stack['tools'].append('Alembic')
        
        self.report['phase2_stack'] = stack
        print(f"   Languages detected: {len(stack['languages'])}")
        print(f"   Python deps: {len(stack['dependencies']['python'])}")
        print(f"   JS deps: {len(stack['dependencies']['javascript'])}")
        print(f"   Frameworks: {list(stack['frameworks'].keys())}")
        print(f"   Tools: {stack['tools']}")
        
        return stack
    
    # ========================================================================
    # PHASE 3: Architecture Analysis
    # ========================================================================
    def phase3_architecture(self) -> Dict[str, Any]:
        """Analyze architectural patterns."""
        print("\n" + "="*70)
        print("  PHASE 3: ARCHITECTURE PATTERNS")
        print("="*70)
        
        arch = {
            'modules': {},
            'api_endpoints': [],
            'database_models': [],
            'routers': [],
            'patterns_detected': [],
            'layers': {}
        }
        
        # Detect modules (Python packages with __init__.py)
        for p in self.all_py_files:
            if p.name == '__init__.py':
                rel = p.parent.relative_to(self.root)
                if len(rel.parts) >= 1:
                    module_name = rel.parts[0]
                    if module_name not in arch['modules']:
                        arch['modules'][module_name] = {
                            'path': str(rel),
                            'files': 0,
                            'submodules': []
                        }
                    arch['modules'][module_name]['files'] += 1
                    if len(rel.parts) >= 2:
                        arch['modules'][module_name]['submodules'].append(rel.parts[1])
        
        # Detect FastAPI routers
        router_files = [f for f in self.all_py_files if 'router' in f.stem.lower()]
        for r in router_files:
            try:
                content = r.read_text(encoding='utf-8', errors='ignore')
                if 'APIRouter' in content:
                    # Extract prefix
                    prefix_match = re.search(r'APIRouter\([^)]*prefix=["\']([^"\']+)["\']', content)
                    prefix = prefix_match.group(1) if prefix_match else None
                    arch['routers'].append({
                        'file': str(r.relative_to(self.root)),
                        'prefix': prefix
                    })
                    
                    # Extract endpoints
                    endpoints = re.findall(r'@(?:router|app)\.(get|post|put|delete|patch|options)\s*\(\s*["\']([^"\']+)["\']', content)
                    for method, path in endpoints:
                        full_path = f"{prefix or ''}{path}" if prefix else path
                        arch['api_endpoints'].append({
                            'method': method.upper(),
                            'path': full_path,
                            'router': r.name.replace('.py', '')
                        })
            except Exception as e:
                pass
        
        # Detect SQLAlchemy models
        for f in self.all_py_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                # Find class definitions inheriting from Base
                if re.search(r'class\s+\w+\(.*Base.*\):', content):
                    classes = re.findall(r'class\s+(\w+)\s*\([^)]*Base[^)]*\)\s*:', content)
                    for cls in classes:
                        if cls not in ['Base', 'BaseSettings']:
                            arch['database_models'].append({
                                'class': cls,
                                'file': str(f.relative_to(self.root))
                            })
            except:
                pass
        
        # Detect architectural patterns
        has_engine = any('engine' in str(f) for f in self.all_files)
        has_api = any('api' in str(f).lower() for f in self.all_files)
        has_frontend = any('frontend' in str(f).lower() for f in self.all_files)
        has_tests = any('test' in str(f).lower() for f in self.all_files)
        has_db = any('database' in str(f).lower() or 'models' in str(f).lower() for f in self.all_files)
        
        if has_engine and has_api and has_frontend:
            arch['patterns_detected'].append('Layered Architecture (Engine + API + Frontend)')
        if has_tests:
            arch['patterns_detected'].append('Test-Driven Development structure')
        if len(arch['routers']) > 5:
            arch['patterns_detected'].append('Router-based API organization')
        
        arch['layers'] = {
            'engine': has_engine,
            'api': has_api,
            'frontend': has_frontend,
            'database': has_db,
            'tests': has_tests
        }
        
        self.report['phase3_architecture'] = arch
        print(f"   Modules: {len(arch['modules'])}")
        print(f"   Routers: {len(arch['routers'])}")
        print(f"   API endpoints: {len(arch['api_endpoints'])}")
        print(f"   Database models: {len(arch['database_models'])}")
        print(f"   Patterns: {arch['patterns_detected']}")
        
        return arch
    
    # ========================================================================
    # PHASE 4: Code Quality Metrics
    # ========================================================================
    def phase4_quality(self) -> Dict[str, Any]:
        """Analyze code quality indicators."""
        print("\n" + "="*70)
        print("  PHASE 4: CODE QUALITY METRICS")
        print("="*70)
        
        quality = {
            'loc_stats': {},
            'test_coverage': {},
            'documentation': {},
            'complexity_indicators': {},
            'code_smells': []
        }
        
        # LOC stats for Python
        total_lines = 0
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        largest_files = []
        
        for f in self.all_py_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                file_total = len(lines)
                file_blank = sum(1 for line in lines if not line.strip())
                file_comment = sum(1 for line in lines if line.strip().startswith('#'))
                file_code = file_total - file_blank - file_comment
                
                total_lines += file_total
                code_lines += file_code
                comment_lines += file_comment
                blank_lines += file_blank
                
                largest_files.append({
                    'file': str(f.relative_to(self.root)),
                    'lines': file_total,
                    'code_lines': file_code
                })
            except:
                pass
        
        largest_files.sort(key=lambda x: x['lines'], reverse=True)
        
        quality['loc_stats'] = {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
            'comment_ratio': round(comment_lines / total_lines * 100, 2) if total_lines > 0 else 0,
            'largest_files': largest_files[:20]
        }
        
        # Test coverage
        test_files = [f for f in self.all_py_files if 'test_' in f.name or '_test.py' in f.name]
        quality['test_coverage'] = {
            'test_files_count': len(test_files),
            'test_files': [str(f.relative_to(self.root)) for f in test_files[:20]],
            'has_pytest_ini': (self.root / 'pytest.ini').exists() or 
                             'pytest' in (self.root / 'pyproject.toml').read_text() if (self.root / 'pyproject.toml').exists() else False,
            'test_to_code_ratio': round(len(test_files) / len(self.all_py_files), 2) if self.all_py_files else 0
        }
        
        # Documentation
        docs_dir = self.root / 'docs'
        readme = self.root / 'README.md'
        
        quality['documentation'] = {
            'has_docs_dir': docs_dir.exists(),
            'docs_files': sum(1 for _ in docs_dir.rglob('*.md')) if docs_dir.exists() else 0,
            'has_readme': readme.exists(),
            'readme_lines': len(readme.read_text(encoding='utf-8').splitlines()) if readme.exists() else 0,
            'docstrings_in_code': 0
        }
        
        # Count docstrings
        docstring_count = 0
        for f in self.all_py_files[:500]:  # Sample
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                docstring_count += content.count('"""') // 2 + content.count("'''") // 2
            except:
                pass
        
        quality['documentation']['docstrings_in_code'] = docstring_count
        
        # Code smells
        for f in self.all_py_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                rel = str(f.relative_to(self.root))
                
                # Very long files
                if len(content.split('\n')) > 1000:
                    quality['code_smells'].append({
                        'type': 'long_file',
                        'file': rel,
                        'lines': len(content.split('\n'))
                    })
                
                # Long functions (rough estimate)
                if content.count('def ') > 30:
                    quality['code_smells'].append({
                        'type': 'too_many_functions',
                        'file': rel,
                        'functions': content.count('def ')
                    })
            except:
                pass
        
        quality['complexity_indicators'] = {
            'avg_file_size': round(total_lines / len(self.all_py_files), 1) if self.all_py_files else 0,
            'code_smells_count': len(quality['code_smells'])
        }
        
        self.report['phase4_quality'] = quality
        print(f"   Total LOC: {total_lines:,}")
        print(f"   Code lines: {code_lines:,}")
        print(f"   Comment ratio: {quality['loc_stats']['comment_ratio']}%")
        print(f"   Test files: {len(test_files)}")
        print(f"   Code smells: {len(quality['code_smells'])}")
        
        return quality
    
    # ========================================================================
    # PHASE 5: Security Audit
    # ========================================================================
    def phase5_security(self) -> Dict[str, Any]:
        """Security-focused analysis."""
        print("\n" + "="*70)
        print("  PHASE 5: SECURITY AUDIT")
        print("="*70)
        
        security = {
            'secrets_exposed': [],
            'env_files': [],
            'gitignore_coverage': {},
            'sensitive_patterns': [],
            'critical_findings': []
        }
        
        # Sensitive patterns to detect
        sensitive_patterns = [
            (r'(?i)(password|passwd|pwd)\s*=\s*["\']([^"\']+)["\']', 'Hardcoded password'),
            (r'(?i)(api_key|apikey|api_secret)\s*=\s*["\']([^"\']+)["\']', 'Hardcoded API key'),
            (r'(?i)(secret_key|jwt_secret)\s*=\s*["\']([^"\']+)["\']', 'Hardcoded secret'),
            (r'(?i)(token)\s*=\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'Hardcoded token'),
            (r'(?i)(private_key)\s*=\s*["\']([^"\']+)["\']', 'Private key'),
            (r'BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY', 'Private key file'),
            (r'sk_live_[a-zA-Z0-9]+', 'Stripe live key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub personal token'),
        ]
        
        # Scan Python files
        files_scanned = 0
        for f in self.all_py_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                files_scanned += 1
                rel = str(f.relative_to(self.root))
                
                for pattern, description in sensitive_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Skip if in comments
                        line_num = content[:match.start()].count('\n') + 1
                        line = content.split('\n')[line_num - 1]
                        if not line.strip().startswith('#'):
                            security['sensitive_patterns'].append({
                                'file': rel,
                                'line': line_num,
                                'pattern': description,
                                'severity': 'HIGH'
                            })
            except:
                pass
        
        # Check .env files
        for env_name in ['.env', '.env.local', '.env.development', '.env.production']:
            env_file = self.root / env_name
            if env_file.exists():
                security['env_files'].append({
                    'name': env_name,
                    'size': env_file.stat().st_size,
                    'in_gitignore': self._check_gitignore(env_name)
                })
        
        # Gitignore coverage
        gitignore = self.root / '.gitignore'
        if gitignore.exists():
            gi_content = gitignore.read_text(encoding='utf-8')
            critical_patterns = ['.env', '*.pem', '*.key', '__pycache__', '.venv', 'node_modules']
            security['gitignore_coverage'] = {
                'exists': True,
                'has_env': '.env' in gi_content,
                'has_keys': any(p in gi_content for p in ['*.pem', '*.key', 'secrets']),
                'has_venv': '.venv' in gi_content or 'venv' in gi_content,
                'has_pycache': '__pycache__' in gi_content,
                'critical_patterns_covered': sum(1 for p in critical_patterns if p in gi_content)
            }
        else:
            security['gitignore_coverage'] = {'exists': False}
        
        # Critical findings
        if security['sensitive_patterns']:
            security['critical_findings'].append({
                'severity': 'HIGH',
                'issue': f"Found {len(security['sensitive_patterns'])} hardcoded secrets in code",
                'recommendation': 'Move all secrets to .env file and add to .gitignore'
            })
        
        if security['gitignore_coverage'].get('exists') and not security['gitignore_coverage'].get('has_env'):
            security['critical_findings'].append({
                'severity': 'HIGH',
                'issue': '.env not in .gitignore',
                'recommendation': 'Add .env and .env.* to .gitignore immediately'
            })
        
        security['files_scanned'] = files_scanned
        
        self.report['phase5_security'] = security
        print(f"   Files scanned: {files_scanned}")
        print(f"   Sensitive patterns found: {len(security['sensitive_patterns'])}")
        print(f"   .env files: {len(security['env_files'])}")
        print(f"   Critical findings: {len(security['critical_findings'])}")
        
        return security
    
    def _check_gitignore(self, pattern: str) -> bool:
        """Check if pattern is in .gitignore."""
        gitignore = self.root / '.gitignore'
        if not gitignore.exists():
            return False
        return pattern in gitignore.read_text(encoding='utf-8')
    
    # ========================================================================
    # PHASE 6: Completeness Analysis
    # ========================================================================
    def phase6_completeness(self) -> Dict[str, Any]:
        """Detect incomplete/placeholder code."""
        print("\n" + "="*70)
        print("  PHASE 6: COMPLETENESS ANALYSIS")
        print("="*70)
        
        completeness = {
            'placeholder_files': [],
            'stub_functions': [],
            'todo_fixme_count': 0,
            'todo_items': [],
            'empty_modules': [],
            'not_implemented': []
        }
        
        placeholder_indicators = [
            'pass  # placeholder',
            'raise NotImplementedError',
            'TODO:',
            'FIXME:',
            'XXX:',
            '# placeholder',
            'NotImplementedError',
        ]
        
        for f in self.all_py_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                rel = str(f.relative_to(self.root))
                lines = content.split('\n')
                
                # Placeholder files (very small or mostly empty)
                code_lines = [l for l in lines if l.strip() and not l.strip().startswith(('#', '"""', "'''"))]
                if len(code_lines) < 5 and len(lines) < 20:
                    completeness['placeholder_files'].append({
                        'file': rel,
                        'lines': len(lines),
                        'code_lines': len(code_lines)
                    })
                
                # TODO/FIXME
                for i, line in enumerate(lines, 1):
                    if re.search(r'#\s*(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
                        completeness['todo_items'].append({
                            'file': rel,
                            'line': i,
                            'text': line.strip()[:100]
                        })
                        completeness['todo_fixme_count'] += 1
                    
                    if 'NotImplementedError' in line:
                        completeness['not_implemented'].append({
                            'file': rel,
                            'line': i
                        })
                
                # Stub functions (functions with only pass/NotImplementedError)
                if 'def ' in content:
                    # Simple heuristic
                    funcs = re.findall(r'def\s+(\w+)\([^)]*\)[^:]*:\s*(?:pass|raise NotImplementedError)', content)
                    for func in funcs:
                        completeness['stub_functions'].append({
                            'file': rel,
                            'function': func
                        })
            except:
                pass
        
        # Empty modules (dirs with only __init__.py)
        for p in self.root.rglob('__init__.py'):
            if self._should_ignore(p):
                continue
            parent = p.parent
            py_files = list(parent.glob('*.py'))
            if len(py_files) == 1:  # Only __init__.py
                completeness['empty_modules'].append(str(parent.relative_to(self.root)))
        
        self.report['phase6_completeness'] = completeness
        print(f"   Placeholder files: {len(completeness['placeholder_files'])}")
        print(f"   Stub functions: {len(completeness['stub_functions'])}")
        print(f"   TODO/FIXME: {completeness['todo_fixme_count']}")
        print(f"   NotImplementedError: {len(completeness['not_implemented'])}")
        print(f"   Empty modules: {len(completeness['empty_modules'])}")
        
        return completeness
    
    # ========================================================================
    # PHASE 7: Risk Matrix (SWOT)
    # ========================================================================
    def phase7_risk_matrix(self) -> Dict[str, Any]:
        """Generate SWOT analysis and risk matrix."""
        print("\n" + "="*70)
        print("  PHASE 7: RISK MATRIX (SWOT)")
        print("="*70)
        
        swot = {
            'strengths': [],
            'weaknesses': [],
            'opportunities': [],
            'threats': []
        }
        
        risks = []
        
        # Analyze based on previous phases
        p1 = self.report.get('phase1_inventory', {})
        p2 = self.report.get('phase2_stack', {})
        p3 = self.report.get('phase3_architecture', {})
        p4 = self.report.get('phase4_quality', {})
        p5 = self.report.get('phase5_security', {})
        p6 = self.report.get('phase6_completeness', {})
        
        # Strengths
        if p2.get('frameworks', {}).get('backend') == 'FastAPI':
            swot['strengths'].append('Modern async web framework (FastAPI)')
        if p2.get('frameworks', {}).get('frontend') == 'Next.js':
            swot['strengths'].append('Modern React framework (Next.js)')
        if p4.get('loc_stats', {}).get('comment_ratio', 0) > 10:
            swot['strengths'].append(f"Good comment ratio ({p4['loc_stats']['comment_ratio']}%)")
        if p4.get('test_coverage', {}).get('test_files_count', 0) > 0:
            swot['strengths'].append(f"Has test suite ({p4['test_coverage']['test_files_count']} files)")
        if p1.get('total_files', 0) > 50:
            swot['strengths'].append(f"Substantial codebase ({p1['total_files']} files)")
        if p3.get('layers', {}).get('engine') and p3.get('layers', {}).get('api'):
            swot['strengths'].append('Layered architecture (Engine + API separation)')
        
        # Weaknesses
        if p6.get('placeholder_files'):
            swot['weaknesses'].append(f"{len(p6['placeholder_files'])} placeholder files detected")
        if p6.get('stub_functions'):
            swot['weaknesses'].append(f"{len(p6['stub_functions'])} stub functions (not implemented)")
        if p6.get('todo_fixme_count', 0) > 10:
            swot['weaknesses'].append(f"{p6['todo_fixme_count']} TODO/FIXME markers")
        if p4.get('loc_stats', {}).get('comment_ratio', 0) < 5:
            swot['weaknesses'].append('Low comment ratio - poor documentation')
        if p5.get('critical_findings'):
            swot['weaknesses'].append(f"{len(p5['critical_findings'])} critical security findings")
        if p4.get('code_smells'):
            swot['weaknesses'].append(f"{len(p4['code_smells'])} code smells detected")
        if not p2.get('tools') or 'GitHub Actions' not in p2.get('tools', []):
            swot['weaknesses'].append('No CI/CD pipeline detected')
        
        # Opportunities
        if 'alembic' not in p2.get('tools', []):
            swot['opportunities'].append('Add database migrations with Alembic')
        if 'Docker' not in p2.get('tools', []):
            swot['opportunities'].append('Containerize with Docker for deployment')
        if p4.get('test_coverage', {}).get('test_to_code_ratio', 0) < 0.3:
            swot['opportunities'].append('Increase test coverage')
        swot['opportunities'].append('Add observability (Prometheus/Grafana)')
        swot['opportunities'].append('Add comprehensive API documentation')
        
        # Threats
        if p5.get('sensitive_patterns'):
            swot['threats'].append('Exposed secrets could lead to security breach')
        if p1.get('empty_files_count', 0) > 10:
            swot['threats'].append(f"{p1['empty_files_count']} empty files - potential cleanup needed")
        swot['threats'].append('Dependency vulnerabilities if not regularly updated')
        swot['threats'].append('Technical debt from incomplete implementations')
        
        # Risk scoring
        risk_score = 0
        risk_score += len(p5.get('critical_findings', [])) * 10
        risk_score += len(p6.get('stub_functions', [])) * 2
        risk_score += len(p6.get('placeholder_files', [])) * 3
        risk_score += len(p5.get('sensitive_patterns', [])) * 5
        
        max_risk = 100
        risk_level = 'LOW' if risk_score < 20 else 'MEDIUM' if risk_score < 50 else 'HIGH' if risk_score < 80 else 'CRITICAL'
        
        result = {
            'swot': swot,
            'risk_score': min(risk_score, max_risk),
            'risk_level': risk_level,
            'top_priorities': self._generate_priorities(swot, p5, p6)
        }
        
        self.report['phase7_risk_matrix'] = result
        print(f"   Strengths: {len(swot['strengths'])}")
        print(f"   Weaknesses: {len(swot['weaknesses'])}")
        print(f"   Opportunities: {len(swot['opportunities'])}")
        print(f"   Threats: {len(swot['threats'])}")
        print(f"   Risk score: {result['risk_score']}/{max_risk} ({risk_level})")
        
        return result
    
    def _generate_priorities(self, swot, p5, p6) -> List[Dict]:
        """Generate prioritized action items."""
        priorities = []
        
        # Security issues first
        for finding in p5.get('critical_findings', []):
            priorities.append({
                'priority': 'P0 - CRITICAL',
                'category': 'Security',
                'issue': finding['issue'],
                'action': finding['recommendation'],
                'estimated_effort': '1-2 hours'
            })
        
        # Then incomplete code
        if p6.get('stub_functions'):
            priorities.append({
                'priority': 'P1 - HIGH',
                'category': 'Completeness',
                'issue': f"{len(p6['stub_functions'])} stub functions",
                'action': 'Implement or remove stub functions',
                'estimated_effort': '2-5 days'
            })
        
        if p6.get('placeholder_files'):
            priorities.append({
                'priority': 'P1 - HIGH',
                'category': 'Completeness',
                'issue': f"{len(p6['placeholder_files'])} placeholder files",
                'action': 'Fill placeholders or mark as planned',
                'estimated_effort': '1-3 days'
            })
        
        # Testing
        priorities.append({
            'priority': 'P2 - MEDIUM',
            'category': 'Quality',
            'issue': 'Test coverage needs improvement',
            'action': 'Add comprehensive unit and integration tests',
            'estimated_effort': '1-2 weeks'
        })
        
        # CI/CD
        priorities.append({
            'priority': 'P2 - MEDIUM',
            'category': 'DevOps',
            'issue': 'CI/CD pipeline',
            'action': 'Setup automated testing and deployment',
            'estimated_effort': '2-3 days'
        })
        
        return priorities
    
    # ========================================================================
    # REPORT GENERATION
    # ========================================================================
    def generate_json_report(self) -> str:
        """Generate JSON report."""
        path = self.root / 'project_analysis.json'
        path.write_text(json.dumps(self.report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"\n✅ JSON report saved: {path}")
        return str(path)
    
    def generate_markdown_report(self) -> str:
        """Generate human-readable Markdown report."""
        r = self.report
        
        md = []
        md.append("# 📊 Eco Nojin - Project Analysis Report")
        md.append(f"\n**Generated:** {r['metadata']['analyzed_at']}")
        md.append(f"**Project Path:** `{r['metadata']['project_path']}`")
        md.append(f"**Analyzer Version:** {r['metadata']['analyzer_version']}")
        
        md.append("\n---\n")
        
        # Executive Summary
        md.append("## 📋 Executive Summary\n")
        p1 = r.get('phase1_inventory', {})
        p7 = r.get('phase7_risk_matrix', {})
        md.append(f"- **Total Files:** {p1.get('total_files', 0):,}")
        md.append(f"- **Total Size:** {p1.get('total_size_mb', 0):.2f} MB")
        md.append(f"- **Risk Level:** **{p7.get('risk_level', 'N/A')}** (Score: {p7.get('risk_score', 0)}/100)")
        md.append(f"- **Languages:** {', '.join(r.get('phase2_stack', {}).get('languages', {}).keys())}")
        
        md.append("\n---\n")
        
        # Phase 1
        md.append("## 📂 Phase 1: Inventory & Structure\n")
        md.append(f"- **Total Files:** {p1.get('total_files', 0):,}")
        md.append(f"- **Total Size:** {p1.get('total_size_mb', 0):.2f} MB")
        md.append(f"- **Empty Files:** {p1.get('empty_files_count', 0)}")
        md.append("\n### Top-Level Structure\n")
        md.append("| Item | Type | Metric |")
        md.append("|------|------|--------|")
        for name, info in list(p1.get('top_level_structure', {}).items())[:15]:
            if info.get('type') == 'directory':
                md.append(f"| `{name}/` | Directory | {info.get('files', 0)} files |")
            else:
                md.append(f"| `{name}` | File | {info.get('size_bytes', 0):,} bytes |")
        
        md.append("\n---\n")
        
        # Phase 2
        md.append("## 🛠️ Phase 2: Technology Stack\n")
        p2 = r.get('phase2_stack', {})
        md.append("### Languages (by LOC)\n")
        for lang, loc in list(p2.get('languages', {}).items())[:10]:
            md.append(f"- **{lang}:** {loc:,} lines")
        
        md.append("\n### Frameworks\n")
        for key, val in p2.get('frameworks', {}).items():
            md.append(f"- **{key}:** {val}")
        
        md.append(f"\n### Tools: {', '.join(p2.get('tools', []))}")
        
        md.append("\n---\n")
        
        # Phase 3
        md.append("## 🏗️ Phase 3: Architecture\n")
        p3 = r.get('phase3_architecture', {})
        md.append(f"- **Modules:** {len(p3.get('modules', {}))}")
        md.append(f"- **Routers:** {len(p3.get('routers', []))}")
        md.append(f"- **API Endpoints:** {len(p3.get('api_endpoints', []))}")
        md.append(f"- **Database Models:** {len(p3.get('database_models', []))}")
        
        if p3.get('patterns_detected'):
            md.append("\n### Patterns Detected\n")
            for p in p3['patterns_detected']:
                md.append(f"- ✅ {p}")
        
        md.append("\n---\n")
        
        # Phase 4
        md.append("## 📏 Phase 4: Code Quality\n")
        p4 = r.get('phase4_quality', {})
        loc = p4.get('loc_stats', {})
        md.append(f"- **Total Lines:** {loc.get('total_lines', 0):,}")
        md.append(f"- **Code Lines:** {loc.get('code_lines', 0):,}")
        md.append(f"- **Comment Lines:** {loc.get('comment_lines', 0):,}")
        md.append(f"- **Comment Ratio:** {loc.get('comment_ratio', 0)}%")
        md.append(f"- **Test Files:** {p4.get('test_coverage', {}).get('test_files_count', 0)}")
        md.append(f"- **Code Smells:** {len(p4.get('code_smells', []))}")
        
        md.append("\n---\n")
        
        # Phase 5
        md.append("## 🔒 Phase 5: Security\n")
        p5 = r.get('phase5_security', {})
        md.append(f"- **Files Scanned:** {p5.get('files_scanned', 0)}")
        md.append(f"- **Sensitive Patterns:** {len(p5.get('sensitive_patterns', []))}")
        md.append(f"- **Critical Findings:** {len(p5.get('critical_findings', []))}")
        
        if p5.get('critical_findings'):
            md.append("\n### ⚠️ Critical Findings\n")
            for f in p5['critical_findings']:
                md.append(f"- **[{f['severity']}]** {f['issue']}")
                md.append(f"  - Action: {f['recommendation']}")
        
        md.append("\n---\n")
        
        # Phase 6
        md.append("## 📝 Phase 6: Completeness\n")
        p6 = r.get('phase6_completeness', {})
        md.append(f"- **Placeholder Files:** {len(p6.get('placeholder_files', []))}")
        md.append(f"- **Stub Functions:** {len(p6.get('stub_functions', []))}")
        md.append(f"- **TODO/FIXME:** {p6.get('todo_fixme_count', 0)}")
        md.append(f"- **NotImplementedError:** {len(p6.get('not_implemented', []))}")
        md.append(f"- **Empty Modules:** {len(p6.get('empty_modules', []))}")
        
        if p6.get('empty_modules'):
            md.append("\n### Empty Modules\n")
            for m in p6['empty_modules'][:20]:
                md.append(f"- `{m}`")
        
        md.append("\n---\n")
        
        # Phase 7
        md.append("## ⚡ Phase 7: Risk Matrix (SWOT)\n")
        swot = p7.get('swot', {})
        md.append(f"**Risk Score:** {p7.get('risk_score', 0)}/100 (**{p7.get('risk_level', 'N/A')}**)\n")
        
        md.append("### 💪 Strengths\n")
        for s in swot.get('strengths', []):
            md.append(f"- ✅ {s}")
        
        md.append("\n### ⚠️ Weaknesses\n")
        for w in swot.get('weaknesses', []):
            md.append(f"- ⚠️ {w}")
        
        md.append("\n### 🚀 Opportunities\n")
        for o in swot.get('opportunities', []):
            md.append(f"- 💡 {o}")
        
        md.append("\n### 🛡️ Threats\n")
        for t in swot.get('threats', []):
            md.append(f"- 🚨 {t}")
        
        md.append("\n---\n")
        
        # Recommendations
        md.append("## 🎯 Priority Action Items\n")
        for p in p7.get('top_priorities', []):
            md.append(f"### {p['priority']}: {p['category']}")
            md.append(f"- **Issue:** {p['issue']}")
            md.append(f"- **Action:** {p['action']}")
            md.append(f"- **Effort:** {p['estimated_effort']}\n")
        
        md.append("\n---\n")
        md.append("*Report generated by Eco Nojin Project Analyzer v1.0*")
        
        path = self.root / 'project_report.md'
        path.write_text('\n'.join(md), encoding='utf-8')
        print(f"✅ Markdown report saved: {path}")
        return str(path)
    
    def run_all_phases(self):
        """Execute complete analysis pipeline."""
        print("\n" + "█"*70)
        print("  ECO NOJIN - COMPREHENSIVE PROJECT ANALYSIS")
        print("█"*70)
        
        self._collect_files()
        
        self.phase1_inventory()
        self.phase2_stack()
        self.phase3_architecture()
        self.phase4_quality()
        self.phase5_security()
        self.phase6_completeness()
        self.phase7_risk_matrix()
        
        self.generate_json_report()
        self.generate_markdown_report()
        
        print("\n" + "█"*70)
        print("  ANALYSIS COMPLETE")
        print("█"*70)
        print(f"\n📄 Reports generated:")
        print(f"   • {self.root / 'project_analysis.json'}")
        print(f"   • {self.root / 'project_report.md'}")
        print(f"\n💡 To view Markdown report:")
        print(f"   code {self.root / 'project_report.md'}")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    # Auto-detect project root
    project_root = Path.cwd()
    
    # If run from different location, accept argument
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    
    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        sys.exit(1)
    
    print(f"📁 Project root: {project_root}")
    
    analyzer = ProjectAnalyzer(project_root)
    analyzer.run_all_phases()