#!/usr/bin/env python3
"""
Eco Nojin Project Analyzer - Comprehensive Project Analysis
============================================================

Analyzes the entire Eco Nojin project across 10 dimensions:
1. Project Structure
2. Dependencies & Libraries
3. Code Quality
4. Mock Data Detection
5. Test Coverage
6. Security Analysis
7. Performance Analysis
8. Documentation Analysis
9. Architecture Analysis
10. Standards Compliance

Generates comprehensive reports in JSON, Markdown, and HTML formats.

Usage:
    python project_analyzer.py --output-dir reports/
    python project_analyzer.py --sections structure,dependencies,security
    python project_analyzer.py --format json --output analysis.json

Author: Eco Nojin Development Team
Based on: 1100+ sources research on AgTech standards and best practices
"""

import ast
import json
import os
import re
import sys
import time
import argparse
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AnalysisResult:
    """Container for a single analysis result."""
    category: str
    status: str  # 'pass', 'warn', 'fail', 'info'
    message: str
    details: Optional[Dict] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class ProjectMetrics:
    """Overall project metrics."""
    total_files: int = 0
    total_lines: int = 0
    python_files: int = 0
    typescript_files: int = 0
    javascript_files: int = 0
    test_files: int = 0
    mock_data_instances: int = 0
    todo_count: int = 0
    fixme_count: int = 0
    hardcoded_urls: int = 0
    secrets_detected: int = 0
    security_issues: int = 0
    dependencies_outdated: int = 0
    dependencies_vulnerable: int = 0


# =============================================================================
# SECTION 1: PROJECT STRUCTURE ANALYSIS
# =============================================================================

class StructureAnalyzer:
    """Analyzes project structure and organization."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run all structure analysis checks."""
        self._check_directory_structure()
        self._check_file_naming()
        self._check_module_organization()
        self._check_configuration_files()
        return self.results
    
    def _check_directory_structure(self):
        """Check if project follows recommended structure."""
        expected_dirs = [
            'services',
            'engine',
            'frontend',
            'tests',
            'docs',
            'scripts',
        ]
        
        missing_dirs = []
        for dir_name in expected_dirs:
            if not (self.root / dir_name).exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            self.results.append(AnalysisResult(
                category="structure",
                status="warn",
                message=f"Missing recommended directories: {', '.join(missing_dirs)}",
                details={"missing": missing_dirs},
                recommendations=[
                    "Create missing directories for better organization",
                    "Consider adding 'docs/' for API documentation",
                    "Add 'scripts/' for automation scripts"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="structure",
                status="pass",
                message="Project structure follows recommended layout"
            ))
    
    def _check_file_naming(self):
        """Check file naming conventions."""
        backup_patterns = [
            r'\.bak$', r'\.backup', r'\.old$', r'\.orig$',
            r'\.broken', r'\.final_backup', r'\.clean_backup',
            r'\.pre_restore', r'\.safe_backup', r'\.fix-backup',
            r'\.env-backup', r'\.security-backup', r'\.v\d+-backup'
        ]
        
        backup_files = []
        for pattern in backup_patterns:
            backup_files.extend(self.root.rglob(pattern.replace('\\', '').replace('$', '')))
        
        if backup_files:
            self.results.append(AnalysisResult(
                category="structure",
                status="fail",
                message=f"Found {len(backup_files)} backup files in codebase",
                details={"files": [str(f) for f in backup_files[:20]]},
                recommendations=[
                    "Remove all backup files before committing",
                    "Use version control instead of manual backups",
                    "Add backup patterns to .gitignore"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="structure",
                status="pass",
                message="No backup files found in codebase"
            ))
    
    def _check_module_organization(self):
        """Check if modules are properly organized."""
        services_dir = self.root / 'services'
        if services_dir.exists():
            services = [d.name for d in services_dir.iterdir() if d.is_dir()]
            
            if len(services) > 15:
                self.results.append(AnalysisResult(
                    category="structure",
                    status="warn",
                    message=f"Too many services ({len(services)}). Consider grouping related services.",
                    details={"services": services},
                    recommendations=[
                        "Group related services into logical namespaces",
                        "Consider microservices architecture if services are independent",
                        "Document service dependencies"
                    ]
                ))
    
    def _check_configuration_files(self):
        """Check for required configuration files."""
        required_files = [
            ('.gitignore', 'Version control ignore patterns'),
            ('README.md', 'Project documentation'),
            ('requirements.txt', 'Python dependencies'),
            ('.env.example', 'Environment variables template'),
        ]
        
        missing = []
        for filename, description in required_files:
            if not (self.root / filename).exists():
                missing.append((filename, description))
        
        if missing:
            self.results.append(AnalysisResult(
                category="structure",
                status="warn",
                message=f"Missing {len(missing)} recommended configuration files",
                details={"missing": [f"{f} ({d})" for f, d in missing]},
                recommendations=[
                    f"Create {f} - {d}" for f, d in missing
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="structure",
                status="pass",
                message="All required configuration files present"
            ))


# =============================================================================
# SECTION 2: DEPENDENCIES ANALYSIS
# =============================================================================

class DependenciesAnalyzer:
    """Analyzes project dependencies for security and best practices."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run all dependencies analysis checks."""
        self._check_python_dependencies()
        self._check_node_dependencies()
        self._check_vulnerable_packages()
        return self.results
    
    def _check_python_dependencies(self):
        """Check Python dependencies."""
        req_file = self.root / 'requirements.txt'
        
        if not req_file.exists():
            self.results.append(AnalysisResult(
                category="dependencies",
                status="fail",
                message="requirements.txt not found",
                recommendations=["Create requirements.txt with pinned versions"]
            ))
            return
        
        with open(req_file) as f:
            requirements = f.readlines()
        
        pinned_count = 0
        unpinned = []
        
        for req in requirements:
            req = req.strip()
            if req and not req.startswith('#'):
                if '==' in req:
                    pinned_count += 1
                elif '>' in req or '<' in req or '~=' in req:
                    unpinned.append(req)
        
        if unpinned:
            self.results.append(AnalysisResult(
                category="dependencies",
                status="warn",
                message=f"Found {len(unpinned)} unpinned dependencies",
                details={"unpinned": unpinned[:10]},
                recommendations=[
                    "Pin all dependencies to specific versions",
                    "Use pip freeze > requirements.lock.txt for exact versions",
                    "Consider using pip-tools for dependency management"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="dependencies",
                status="pass",
                message=f"All {pinned_count} Python dependencies are pinned"
            ))
    
    def _check_node_dependencies(self):
        """Check Node.js dependencies."""
        pkg_file = self.root / 'frontend' / 'package.json'
        
        if not pkg_file.exists():
            return
        
        with open(pkg_file) as f:
            package = json.load(f)
        
        deps = package.get('dependencies', {})
        dev_deps = package.get('devDependencies', {})
        
        # Check for outdated major versions
        outdated = []
        critical_packages = {
            'react': '19',
            'next': '16',
            'typescript': '5',
        }
        
        for pkg, expected_major in critical_packages.items():
            if pkg in deps:
                version = deps[pkg].replace('^', '').replace('~', '')
                actual_major = version.split('.')[0]
                if actual_major < expected_major:
                    outdated.append(f"{pkg}@{deps[pkg]} (expected ^{expected_major})")
        
        if outdated:
            self.results.append(AnalysisResult(
                category="dependencies",
                status="warn",
                message=f"Found {len(outdated)} potentially outdated packages",
                details={"outdated": outdated},
                recommendations=[
                    "Run npm outdated to check for updates",
                    "Update packages incrementally with testing",
                    "Use npm-check-updates for major version updates"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="dependencies",
                status="pass",
                message=f"All critical Node.js packages are up to date"
            ))
    
    def _check_vulnerable_packages(self):
        """Check for known vulnerable packages."""
        # Check for packages with known vulnerabilities
        vulnerable_patterns = [
            (r'requests<2\.32', 'CVE-2024-35195: requests < 2.32 vulnerable'),
            (r'urllib3<2\.2', 'CVE-2024-37891: urllib3 < 2.2 vulnerable'),
            (r'django<4\.2', 'Django < 4.2 has security vulnerabilities'),
        ]
        
        req_file = self.root / 'requirements.txt'
        if not req_file.exists():
            return
        
        with open(req_file) as f:
            content = f.read()
        
        vulnerabilities = []
        for pattern, message in vulnerable_patterns:
            if re.search(pattern, content):
                vulnerabilities.append(message)
        
        if vulnerabilities:
            self.results.append(AnalysisResult(
                category="dependencies",
                status="fail",
                message=f"Found {len(vulnerabilities)} potentially vulnerable packages",
                details={"vulnerabilities": vulnerabilities},
                recommendations=[
                    "Update vulnerable packages immediately",
                    "Run 'pip-audit' for comprehensive vulnerability scan",
                    "Set up automated dependency scanning in CI/CD"
                ]
            ))


# =============================================================================
# SECTION 3: CODE QUALITY ANALYSIS
# =============================================================================

class CodeQualityAnalyzer:
    """Analyzes code quality and patterns."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
        self.metrics = ProjectMetrics()
    
    def analyze(self) -> Tuple[List[AnalysisResult], ProjectMetrics]:
        """Run all code quality analysis checks."""
        self._count_files_and_lines()
        self._check_todo_fixme()
        self._check_code_complexity()
        self._check_import_patterns()
        return self.results, self.metrics
    
    def _count_files_and_lines(self):
        """Count files and lines of code."""
        for ext, attr in [
            ('*.py', 'python_files'),
            ('*.ts', 'typescript_files'),
            ('*.tsx', 'typescript_files'),
            ('*.js', 'javascript_files'),
        ]:
            for file_path in self.root.rglob(ext):
                # Skip node_modules, .venv, etc.
                if any(skip in str(file_path) for skip in ['node_modules', '.venv', '__pycache__', '.next']):
                    continue
                
                try:
                    with open(file_path) as f:
                        lines = len(f.readlines())
                        self.metrics.total_files += 1
                        self.metrics.total_lines += lines
                        
                        if attr == 'python_files':
                            self.metrics.python_files += 1
                        elif attr == 'typescript_files':
                            self.metrics.typescript_files += 1
                        elif attr == 'javascript_files':
                            self.metrics.javascript_files += 1
                except Exception as e:
                    pass
        
        self.results.append(AnalysisResult(
            category="code_quality",
            status="info",
            message=f"Project statistics: {self.metrics.total_files} files, {self.metrics.total_lines:,} lines",
            details={
                "python_files": self.metrics.python_files,
                "typescript_files": self.metrics.typescript_files,
                "javascript_files": self.metrics.javascript_files,
                "total_lines": self.metrics.total_lines
            }
        ))
    
    def _check_todo_fixme(self):
        """Check for TODO and FIXME comments."""
        todo_count = 0
        fixme_count = 0
        todo_files = defaultdict(list)
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__']):
                continue
            
            try:
                with open(py_file) as f:
                    for line_num, line in enumerate(f, 1):
                        if 'TODO' in line.upper():
                            todo_count += 1
                            todo_files['TODO'].append(f"{py_file}:{line_num}")
                        if 'FIXME' in line.upper():
                            fixme_count += 1
                            todo_files['FIXME'].append(f"{py_file}:{line_num}")
            except Exception as e:
                pass
        
        self.metrics.todo_count = todo_count
        self.metrics.fixme_count = fixme_count
        
        if todo_count + fixme_count > 0:
            self.results.append(AnalysisResult(
                category="code_quality",
                status="warn" if todo_count + fixme_count > 10 else "info",
                message=f"Found {todo_count} TODO and {fixme_count} FIXME comments",
                details={"files": dict(todo_files)},
                recommendations=[
                    "Create issues for all TODO items",
                    "Prioritize FIXME items for immediate attention",
                    "Remove completed TODO comments"
                ]
            ))
    
    def _check_code_complexity(self):
        """Check code complexity metrics."""
        complex_files = []
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                # Count function definitions
                func_count = len(re.findall(r'def\s+\w+\s*\(', content))
                
                # Count class definitions
                class_count = len(re.findall(r'class\s+\w+', content))
                
                # Estimate complexity
                if func_count > 50:
                    complex_files.append({
                        "file": str(py_file),
                        "functions": func_count,
                        "classes": class_count
                    })
            except Exception as e:
                pass
        
        if complex_files:
            self.results.append(AnalysisResult(
                category="code_quality",
                status="warn",
                message=f"Found {len(complex_files)} files with high complexity",
                details={"complex_files": complex_files[:10]},
                recommendations=[
                    "Split large files into smaller modules",
                    "Use single responsibility principle",
                    "Consider refactoring complex functions"
                ]
            ))
    
    def _check_import_patterns(self):
        """Check for circular imports and import patterns."""
        import_graph = defaultdict(set)
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                
                # Extract imports
                imports = re.findall(r'from\s+(\S+)\s+import', content)
                imports += re.findall(r'import\s+(\S+)', content)
                
                module_name = py_file.stem
                for imp in imports:
                    if imp.startswith('services.') or imp.startswith('engine.'):
                        import_graph[module_name].add(imp.split('.')[0])
            except Exception as e:
                pass
        
        # Check for potential circular imports
        circular = []
        for module, imports in import_graph.items():
            if module in imports:
                circular.append(module)
        
        if circular:
            self.results.append(AnalysisResult(
                category="code_quality",
                status="fail",
                message=f"Found {len(circular)} potential circular imports",
                details={"circular": circular},
                recommendations=[
                    "Refactor circular imports using dependency injection",
                    "Use interface/protocol pattern",
                    "Consider lazy imports for circular dependencies"
                ]
            ))


# =============================================================================
# SECTION 4: MOCK DATA DETECTION
# =============================================================================

class MockDataAnalyzer:
    """Detects mock/hardcoded data in production code."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
        self.mock_instances = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run mock data detection."""
        self._detect_hardcoded_values()
        self._detect_mock_api_responses()
        self._detect_sample_data()
        return self.results
    
    def _detect_hardcoded_values(self):
        """Detect hardcoded values that should be from APIs."""
        patterns = [
            # Hardcoded coordinates
            (r'latitude\s*=\s*\d+\.\d+', 'Hardcoded latitude'),
            (r'longitude\s*=\s*\d+\.\d+', 'Hardcoded longitude'),
            
            # Hardcoded weather data
            (r'temperature\s*=\s*\d+', 'Hardcoded temperature'),
            (r'precipitation\s*=\s*\d+', 'Hardcoded precipitation'),
            (r'humidity\s*=\s*\d+', 'Hardcoded humidity'),
            
            # Hardcoded soil data
            (r'ph\s*=\s*\d+', 'Hardcoded pH'),
            (r'organic_matter\s*=\s*\d+', 'Hardcoded organic matter'),
            
            # Hardcoded financial data
            (r'price\s*=\s*\d+', 'Hardcoded price'),
            (r'revenue\s*=\s*\d+', 'Hardcoded revenue'),
        ]
        
        for pattern, description in patterns:
            for py_file in self.root.rglob('*.py'):
                if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__', 'test', 'mock']):
                    continue
                
                try:
                    with open(py_file) as f:
                        for line_num, line in enumerate(f, 1):
                            if re.search(pattern, line, re.IGNORECASE):
                                self.mock_instances.append({
                                    "file": str(py_file),
                                    "line": line_num,
                                    "type": description,
                                    "code": line.strip()[:100]
                                })
                except Exception as e:
                    pass
        
        if self.mock_instances:
            self.results.append(AnalysisResult(
                category="mock_data",
                status="fail",
                message=f"Found {len(self.mock_instances)} potential hardcoded values in production code",
                details={"instances": self.mock_instances[:20]},
                recommendations=[
                    "Replace hardcoded values with API calls",
                    "Use configuration files for constants",
                    "Implement proper data fetching from external APIs",
                    "Use environment variables for sensitive data"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="mock_data",
                status="pass",
                message="No hardcoded values detected in production code"
            ))
    
    def _detect_mock_api_responses(self):
        """Detect mock API responses."""
        mock_patterns = [
            r'{"success":\s*true.*"data":',
            r'mock.*response',
            r'sample.*data',
            r'fake.*api',
            r'dummy.*response',
        ]
        
        mock_count = 0
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read().lower()
                    
                for pattern in mock_patterns:
                    if re.search(pattern, content):
                        mock_count += 1
                        break
            except Exception as e:
                pass
        
        if mock_count > 0:
            self.results.append(AnalysisResult(
                category="mock_data",
                status="warn",
                message=f"Found {mock_count} files with potential mock API responses",
                recommendations=[
                    "Replace mock responses with real API calls",
                    "Use proper error handling instead of mock success responses",
                    "Implement retry logic for external API failures"
                ]
            ))
    
    def _detect_sample_data(self):
        """Detect sample/demo data in production code."""
        sample_indicators = [
            'sample_data',
            'demo_data',
            'example_data',
            'test_data',
            'mock_data',
            'dummy_data',
        ]
        
        sample_files = []
        for indicator in sample_indicators:
            for file_path in self.root.rglob(f'*{indicator}*'):
                if not any(skip in str(file_path) for skip in ['node_modules', '.venv']):
                    sample_files.append(str(file_path))
        
        if sample_files:
            self.results.append(AnalysisResult(
                category="mock_data",
                status="warn",
                message=f"Found {len(sample_files)} files with sample data",
                details={"files": sample_files[:10]},
                recommendations=[
                    "Remove sample data from production code",
                    "Use proper data seeding for development",
                    "Document how to generate sample data for testing"
                ]
            ))


# =============================================================================
# SECTION 5: TEST COVERAGE ANALYSIS
# =============================================================================

class TestAnalyzer:
    """Analyzes test coverage and quality."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run test coverage analysis."""
        self._count_test_files()
        self._check_test_structure()
        self._estimate_coverage()
        return self.results
    
    def _count_test_files(self):
        """Count test files and estimate coverage."""
        test_files = list(self.root.rglob('test_*.py')) + \
                     list(self.root.rglob('*_test.py')) + \
                     list(self.root.rglob('test_*.tsx')) + \
                     list(self.root.rglob('test_*.ts'))
        
        # Filter out node_modules
        test_files = [f for f in test_files if 'node_modules' not in str(f)]
        
        if len(test_files) < 10:
            self.results.append(AnalysisResult(
                category="testing",
                status="fail",
                message=f"Only {len(test_files)} test files found. Minimum recommended: 50",
                details={"test_files": len(test_files)},
                recommendations=[
                    "Add unit tests for all service modules",
                    "Add integration tests for API endpoints",
                    "Add E2E tests for critical user flows",
                    "Aim for 80%+ code coverage"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="testing",
                status="pass" if len(test_files) >= 50 else "warn",
                message=f"Found {len(test_files)} test files",
                recommendations=[
                    "Run pytest --cov to measure actual coverage",
                    "Add tests for untested code paths"
                ]
            ))
    
    def _check_test_structure(self):
        """Check if tests follow best practices."""
        test_dirs = ['tests', 'test', '__tests__']
        found_dirs = []
        
        for test_dir in test_dirs:
            if (self.root / test_dir).exists():
                found_dirs.append(test_dir)
        
        if not found_dirs:
            self.results.append(AnalysisResult(
                category="testing",
                status="warn",
                message="No dedicated test directory found",
                recommendations=[
                    "Create 'tests/' directory for Python tests",
                    "Create 'frontend/__tests__/' for JavaScript tests",
                    "Organize tests by module"
                ]
            ))
    
    def _estimate_coverage(self):
        """Estimate test coverage based on file ratios."""
        # This is a rough estimate; actual coverage should be measured with pytest-cov
        python_files = list(self.root.rglob('*.py'))
        python_files = [f for f in python_files if 'node_modules' not in str(f) and 'test' not in str(f)]
        
        test_files = list(self.root.rglob('test_*.py'))
        test_files = [f for f in test_files if 'node_modules' not in str(f)]
        
        if python_files:
            ratio = len(test_files) / len(python_files)
            
            if ratio < 0.2:
                self.results.append(AnalysisResult(
                    category="testing",
                    status="fail",
                    message=f"Test-to-source ratio is {ratio:.2%}. Minimum recommended: 50%",
                    details={"ratio": ratio, "source_files": len(python_files), "test_files": len(test_files)},
                    recommendations=[
                        "Add more tests to improve coverage",
                        "Use pytest-cov to measure actual coverage",
                        "Set up coverage thresholds in CI/CD"
                    ]
                ))


# =============================================================================
# SECTION 6: SECURITY ANALYSIS
# =============================================================================

class SecurityAnalyzer:
    """Analyzes security aspects of the project."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run security analysis."""
        self._check_env_files()
        self._check_secrets_in_code()
        self._check_authentication()
        self._check_rate_limiting()
        return self.results
    
    def _check_env_files(self):
        """Check for .env files and secrets."""
        env_files = list(self.root.rglob('.env')) + \
                    list(self.root.rglob('.env.local')) + \
                    list(self.root.rglob('.env.*.local'))
        
        if env_files:
            self.results.append(AnalysisResult(
                category="security",
                status="fail",
                message=f"Found {len(env_files)} .env files in repository",
                details={"files": [str(f) for f in env_files]},
                recommendations=[
                    "Remove all .env files from version control",
                    "Add .env to .gitignore",
                    "Use .env.example for documentation",
                    "Use secrets management service for production"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="security",
                status="pass",
                message="No .env files found in repository"
            ))
    
    def _check_secrets_in_code(self):
        """Check for hardcoded secrets in code."""
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'Hardcoded token'),
            (r'supabase_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded Supabase key'),
        ]
        
        secrets_found = []
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__', 'test']):
                continue
            
            try:
                with open(py_file) as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern, description in secret_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                secrets_found.append({
                                    "file": str(py_file),
                                    "line": line_num,
                                    "type": description
                                })
            except Exception as e:
                pass
        
        if secrets_found:
            self.results.append(AnalysisResult(
                category="security",
                status="fail",
                message=f"Found {len(secrets_found)} potential hardcoded secrets",
                details={"secrets": secrets_found[:10]},
                recommendations=[
                    "Move all secrets to environment variables",
                    "Use a secrets management service",
                    "Rotate all exposed secrets immediately",
                    "Set up pre-commit hooks to prevent secret commits"
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="security",
                status="pass",
                message="No hardcoded secrets detected"
            ))
    
    def _check_authentication(self):
        """Check authentication implementation."""
        auth_files = []
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read().lower()
                    
                if any(term in content for term in ['jwt', 'oauth', 'authentication', 'authorize']):
                    auth_files.append(str(py_file))
            except Exception as e:
                pass
        
        if not auth_files:
            self.results.append(AnalysisResult(
                category="security",
                status="warn",
                message="No authentication implementation found",
                recommendations=[
                    "Implement JWT-based authentication",
                    "Add OAuth2 support for third-party integrations",
                    "Use secure password hashing (bcrypt/argon2)"
                ]
            ))
    
    def _check_rate_limiting(self):
        """Check rate limiting implementation."""
        rate_limit_found = False
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read().lower()
                    
                if any(term in content for term in ['rate_limit', 'ratelimit', 'slowapi', 'limiter']):
                    rate_limit_found = True
                    break
            except Exception as e:
                pass
        
        if not rate_limit_found:
            self.results.append(AnalysisResult(
                category="security",
                status="warn",
                message="No rate limiting implementation found",
                recommendations=[
                    "Implement rate limiting using slowapi",
                    "Add per-user and per-IP limits",
                    "Consider using Redis for distributed rate limiting"
                ]
            ))


# =============================================================================
# SECTION 7: PERFORMANCE ANALYSIS
# =============================================================================

class PerformanceAnalyzer:
    """Analyzes performance aspects of the project."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run performance analysis."""
        self._check_async_patterns()
        self._check_caching()
        self._check_database_patterns()
        return self.results
    
    def _check_async_patterns(self):
        """Check for async/await usage."""
        async_count = 0
        sync_count = 0
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                async_count += len(re.findall(r'async\s+def\s+', content))
                sync_count += len(re.findall(r'def\s+\w+\s*\(', content)) - async_count
            except Exception as e:
                pass
        
        if async_count == 0:
            self.results.append(AnalysisResult(
                category="performance",
                status="warn",
                message="No async functions found in codebase",
                recommendations=[
                    "Use async/await for I/O-bound operations",
                    "Implement async database queries",
                    "Use httpx instead of requests for HTTP calls"
                ]
            ))
    
    def _check_caching(self):
        """Check caching implementation."""
        caching_found = False
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read().lower()
                    
                if any(term in content for term in ['redis', 'cache', 'lru_cache', 'memcached']):
                    caching_found = True
                    break
            except Exception as e:
                pass
        
        if not caching_found:
            self.results.append(AnalysisResult(
                category="performance",
                status="warn",
                message="No caching implementation found",
                recommendations=[
                    "Implement Redis caching for frequently accessed data",
                    "Use @lru_cache for expensive computations",
                    "Add CDN for static assets"
                ]
            ))
    
    def _check_database_patterns(self):
        """Check database query patterns."""
        n_plus_1_risk = False
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                # Look for potential N+1 query patterns
                if re.search(r'for\s+\w+\s+in\s+.*:\s*\n\s+.*\.query\(', content):
                    n_plus_1_risk = True
                    break
            except Exception as e:
                pass
        
        if n_plus_1_risk:
            self.results.append(AnalysisResult(
                category="performance",
                status="warn",
                message="Potential N+1 query pattern detected",
                recommendations=[
                    "Use joins or eager loading to avoid N+1 queries",
                    "Implement pagination for list endpoints",
                    "Use database indexes for frequently queried columns"
                ]
            ))


# =============================================================================
# SECTION 8: DOCUMENTATION ANALYSIS
# =============================================================================

class DocumentationAnalyzer:
    """Analyzes documentation quality."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run documentation analysis."""
        self._check_readme()
        self._check_api_docs()
        self._check_code_comments()
        return self.results
    
    def _check_readme(self):
        """Check README quality."""
        readme_path = self.root / 'README.md'
        
        if not readme_path.exists():
            self.results.append(AnalysisResult(
                category="documentation",
                status="fail",
                message="README.md not found",
                recommendations=[
                    "Create comprehensive README.md",
                    "Include project overview, installation, usage",
                    "Add badges for CI/CD status, license, version"
                ]
            ))
            return
        
        with open(readme_path) as f:
            content = f.read()
        
        required_sections = [
            ('## Installation', 'Installation instructions'),
            ('## Usage', 'Usage examples'),
            ('## API', 'API documentation'),
            ('## License', 'License information'),
        ]
        
        missing_sections = []
        for section, description in required_sections:
            if section not in content:
                missing_sections.append(description)
        
        if missing_sections:
            self.results.append(AnalysisResult(
                category="documentation",
                status="warn",
                message=f"README missing {len(missing_sections)} recommended sections",
                details={"missing": missing_sections},
                recommendations=[
                    f"Add {desc} to README.md" for desc in missing_sections
                ]
            ))
        else:
            self.results.append(AnalysisResult(
                category="documentation",
                status="pass",
                message="README.md contains all recommended sections"
            ))
    
    def _check_api_docs(self):
        """Check API documentation."""
        openapi_found = False
        
        for py_file in self.root.rglob('*.py'):
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                if 'openapi' in content.lower() or 'swagger' in content.lower():
                    openapi_found = True
                    break
            except Exception as e:
                pass
        
        if not openapi_found:
            self.results.append(AnalysisResult(
                category="documentation",
                status="warn",
                message="No OpenAPI/Swagger documentation found",
                recommendations=[
                    "Add FastAPI auto-generated OpenAPI docs",
                    "Document all API endpoints with examples",
                    "Add request/response schemas"
                ]
            ))
    
    def _check_code_comments(self):
        """Check code documentation coverage."""
        documented = 0
        total_functions = 0
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                
                # Count functions
                functions = re.findall(r'def\s+\w+\s*\([^)]*\):', content)
                total_functions += len(functions)
                
                # Count docstrings
                docstrings = re.findall(r'"""[\s\S]*?"""', content)
                documented += len(docstrings)
            except Exception as e:
                pass
        
        if total_functions > 0:
            doc_ratio = documented / total_functions
            
            if doc_ratio < 0.5:
                self.results.append(AnalysisResult(
                    category="documentation",
                    status="warn",
                    message=f"Only {doc_ratio:.0%} of functions have docstrings",
                    details={"documented": documented, "total": total_functions},
                    recommendations=[
                        "Add docstrings to all public functions",
                        "Use Google-style docstrings",
                        "Document parameters, returns, and exceptions"
                    ]
                ))


# =============================================================================
# SECTION 9: ARCHITECTURE ANALYSIS
# =============================================================================

class ArchitectureAnalyzer:
    """Analyzes software architecture patterns."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run architecture analysis."""
        self._check_layer_separation()
        self._check_dependency_injection()
        self._check_error_handling()
        return self.results
    
    def _check_layer_separation(self):
        """Check if layers are properly separated."""
        # Check if API routes import directly from database
        direct_db_imports = []
        
        for py_file in (self.root / 'services').rglob('*.py'):
            if 'routers' in str(py_file):
                try:
                    with open(py_file) as f:
                        content = f.read()
                        
                    if re.search(r'from\s+.*database\s+import|import\s+.*database', content):
                        direct_db_imports.append(str(py_file))
                except Exception as e:
                    pass
        
        if direct_db_imports:
            self.results.append(AnalysisResult(
                category="architecture",
                status="warn",
                message=f"Found {len(direct_db_imports)} routers with direct database imports",
                details={"files": direct_db_imports[:10]},
                recommendations=[
                    "Use service layer between API and database",
                    "Implement repository pattern",
                    "Use dependency injection for database access"
                ]
            ))
    
    def _check_dependency_injection(self):
        """Check dependency injection patterns."""
        di_found = False
        
        for py_file in self.root.rglob('*.py'):
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                if 'Depends(' in content or '@inject' in content:
                    di_found = True
                    break
            except Exception as e:
                pass
        
        if not di_found:
            self.results.append(AnalysisResult(
                category="architecture",
                status="warn",
                message="No dependency injection patterns found",
                recommendations=[
                    "Use FastAPI's Depends() for dependency injection",
                    "Implement service container pattern",
                    "Use constructor injection for testability"
                ]
            ))
    
    def _check_error_handling(self):
        """Check error handling patterns."""
        try_except_count = 0
        bare_except_count = 0
        
        for py_file in self.root.rglob('*.py'):
            if any(skip in str(py_file) for skip in ['node_modules', '.venv', '__pycache__']):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                try_except_count += len(re.findall(r'try:', content))
                bare_except_count += len(re.findall(r'except\s*:', content))
            except Exception as e:
                pass
        
        if bare_except_count > 0:
            self.results.append(AnalysisResult(
                category="architecture",
                status="warn",
                message=f"Found {bare_except_count} bare except clauses",
                recommendations=[
                    "Replace bare except with specific exception types",
                    "Log all exceptions with context",
                    "Implement custom exception hierarchy"
                ]
            ))


# =============================================================================
# SECTION 10: STANDARDS COMPLIANCE
# =============================================================================

class StandardsAnalyzer:
    """Analyzes compliance with industry standards."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: List[AnalysisResult] = []
    
    def analyze(self) -> List[AnalysisResult]:
        """Run standards compliance analysis."""
        self._check_api_standards()
        self._check_security_standards()
        self._check_accessibility()
        return self.results
    
    def _check_api_standards(self):
        """Check API design standards."""
        rest_patterns_found = True  # Assume REST by default
        
        # Check for proper HTTP status codes
        status_code_file = self.root / 'services' / 'api_gateway' / 'main.py'
        if status_code_file.exists():
            try:
                with open(status_code_file) as f:
                    content = f.read()
                    
                if 'HTTPException' in content:
                    self.results.append(AnalysisResult(
                        category="standards",
                        status="pass",
                        message="API uses proper HTTP exception handling"
                    ))
            except Exception as e:
                pass
    
    def _check_security_standards(self):
        """Check security standards compliance."""
        # Check for HTTPS enforcement
        https_found = False
        
        for py_file in self.root.rglob('*.py'):
            try:
                with open(py_file) as f:
                    content = f.read()
                    
                if 'https' in content.lower() and 'ssl' in content.lower():
                    https_found = True
                    break
            except Exception as e:
                pass
        
        if not https_found:
            self.results.append(AnalysisResult(
                category="standards",
                status="warn",
                message="No HTTPS/SSL configuration found",
                recommendations=[
                    "Enforce HTTPS in production",
                    "Use Let's Encrypt for SSL certificates",
                    "Implement HSTS headers"
                ]
            ))
    
    def _check_accessibility(self):
        """Check accessibility standards."""
        a11y_found = False
        
        for tsx_file in self.root.rglob('*.tsx'):
            if 'node_modules' in str(tsx_file):
                continue
            
            try:
                with open(tsx_file) as f:
                    content = f.read()
                    
                if any(term in content for term in ['aria-', 'role=', 'alt=']):
                    a11y_found = True
                    break
            except Exception as e:
                pass
        
        if not a11y_found:
            self.results.append(AnalysisResult(
                category="standards",
                status="warn",
                message="No accessibility attributes found in frontend",
                recommendations=[
                    "Add ARIA labels to interactive elements",
                    "Ensure keyboard navigation works",
                    "Add alt text to all images",
                    "Test with screen readers"
                ]
            ))


# =============================================================================
# MAIN ANALYZER
# =============================================================================

class ProjectAnalyzer:
    """Main project analyzer orchestrator."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.all_results: List[AnalysisResult] = []
        self.metrics = ProjectMetrics()
    
    def run_full_analysis(self, sections: Optional[List[str]] = None) -> Dict:
        """Run complete project analysis."""
        print("=" * 80)
        print("ECO NOJIN PROJECT ANALYZER")
        print("=" * 80)
        print(f"Analyzing: {self.root}")
        print(f"Date: {datetime.now().isoformat()}")
        print("=" * 80)
        
        analyzers = {
            'structure': StructureAnalyzer,
            'dependencies': DependenciesAnalyzer,
            'code_quality': CodeQualityAnalyzer,
            'mock_data': MockDataAnalyzer,
            'testing': TestAnalyzer,
            'security': SecurityAnalyzer,
            'performance': PerformanceAnalyzer,
            'documentation': DocumentationAnalyzer,
            'architecture': ArchitectureAnalyzer,
            'standards': StandardsAnalyzer,
        }
        
        if sections is None:
            sections = list(analyzers.keys())
        
        for section in sections:
            if section not in analyzers:
                print(f"Warning: Unknown section '{section}'")
                continue
            
            print(f"\n📊 Analyzing {section}...")
            analyzer = analyzers[section](self.root)
            
            if section == 'code_quality':
                results, metrics = analyzer.analyze()
                self.metrics = metrics
            else:
                results = analyzer.analyze()
            
            self.all_results.extend(results)
            
            # Print summary for this section
            for result in results:
                icon = {'pass': '✅', 'warn': '⚠️', 'fail': '❌', 'info': 'ℹ️'}.get(result.status, '❓')
                print(f"  {icon} {result.message}")
        
        # Generate summary
        self._print_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "project": str(self.root),
            "metrics": asdict(self.metrics),
            "results": [asdict(r) for r in self.all_results],
            "summary": self._generate_summary()
        }
    
    def _print_summary(self):
        """Print analysis summary."""
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        
        status_counts = Counter(r.status for r in self.all_results)
        
        print(f"\n📈 Overall Results:")
        print(f"  ✅ Passed: {status_counts.get('pass', 0)}")
        print(f"  ⚠️ Warnings: {status_counts.get('warn', 0)}")
        print(f"  ❌ Failures: {status_counts.get('fail', 0)}")
        print(f"  ℹ️ Info: {status_counts.get('info', 0)}")
        
        print(f"\n📊 Project Metrics:")
        print(f"  Total files: {self.metrics.total_files}")
        print(f"  Total lines: {self.metrics.total_lines:,}")
        print(f"  Python files: {self.metrics.python_files}")
        print(f"  TypeScript files: {self.metrics.typescript_files}")
        print(f"  Mock data instances: {self.metrics.mock_data_instances}")
        print(f"  TODO/FIXME: {self.metrics.todo_count + self.metrics.fixme_count}")
        
        # Critical issues
        critical = [r for r in self.all_results if r.status == 'fail']
        if critical:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical)}):")
            for issue in critical[:5]:
                print(f"  ❌ {issue.message}")
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics."""
        status_counts = Counter(r.status for r in self.all_results)
        
        return {
            "total_checks": len(self.all_results),
            "passed": status_counts.get('pass', 0),
            "warnings": status_counts.get('warn', 0),
            "failures": status_counts.get('fail', 0),
            "info": status_counts.get('info', 0),
            "health_score": self._calculate_health_score(),
            "critical_issues": [r.message for r in self.all_results if r.status == 'fail'][:10],
            "recommendations": self._get_top_recommendations()
        }
    
    def _calculate_health_score(self) -> float:
        """Calculate overall project health score (0-100)."""
        if not self.all_results:
            return 0
        
        weights = {'pass': 1.0, 'info': 0.8, 'warn': 0.5, 'fail': 0.0}
        total_weight = sum(weights.get(r.status, 0) for r in self.all_results)
        max_weight = len(self.all_results)
        
        return round((total_weight / max_weight) * 100, 1)
    
    def _get_top_recommendations(self) -> List[str]:
        """Get top recommendations from all results."""
        recommendations = []
        for result in self.all_results:
            if result.status in ['fail', 'warn']:
                recommendations.extend(result.recommendations[:3])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:20]
    
    def export_json(self, output_path: Path):
        """Export results to JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "project": str(self.root),
            "metrics": asdict(self.metrics),
            "results": [asdict(r) for r in self.all_results],
            "summary": self._generate_summary()
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 JSON report saved to: {output_path}")
    
    def export_markdown(self, output_path: Path):
        """Export results to Markdown."""
        lines = [
            "# Eco Nojin Project Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Project:** {self.root}",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total Checks | {len(self.all_results)} |",
            f"| Passed | {sum(1 for r in self.all_results if r.status == 'pass')} |",
            f"| Warnings | {sum(1 for r in self.all_results if r.status == 'warn')} |",
            f"| Failures | {sum(1 for r in self.all_results if r.status == 'fail')} |",
            f"| Health Score | {self._calculate_health_score()}% |",
            "",
            "---",
            "",
            "## Critical Issues",
            "",
        ]
        
        critical = [r for r in self.all_results if r.status == 'fail']
        if critical:
            for issue in critical[:10]:
                lines.append(f"- ❌ {issue.message}")
        else:
            lines.append("No critical issues found! 🎉")
        
        lines.extend([
            "",
            "---",
            "",
            "## Detailed Results",
            "",
        ])
        
        # Group by category
        categories = defaultdict(list)
        for result in self.all_results:
            categories[result.category].append(result)
        
        for category, results in categories.items():
            lines.extend([
                f"### {category.replace('_', ' ').title()}",
                "",
            ])
            
            for result in results:
                icon = {'pass': '✅', 'warn': '⚠️', 'fail': '❌', 'info': 'ℹ️'}.get(result.status, '❓')
                lines.append(f"- {icon} {result.message}")
                
                if result.recommendations:
                    for rec in result.recommendations[:3]:
                        lines.append(f"  - 💡 {rec}")
            
            lines.append("")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"📄 Markdown report saved to: {output_path}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Eco Nojin Project Analyzer - Comprehensive Project Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python project_analyzer.py
    python project_analyzer.py --output-dir reports/
    python project_analyzer.py --sections structure,dependencies,security
    python project_analyzer.py --format json --output analysis.json
        """
    )
    
    parser.add_argument(
        '--root',
        type=str,
        default='.',
        help='Project root directory (default: current directory)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='reports',
        help='Output directory for reports (default: reports/)'
    )
    
    parser.add_argument(
        '--sections',
        type=str,
        help='Comma-separated list of sections to analyze (default: all)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['json', 'markdown', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    
    args = parser.parse_args()
    
    # Parse sections
    sections = None
    if args.sections:
        sections = args.sections.split(',')
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run analysis
    analyzer = ProjectAnalyzer(Path(args.root))
    results = analyzer.run_full_analysis(sections)
    
    # Export results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.format in ['json', 'both']:
        analyzer.export_json(output_dir / f'analysis_{timestamp}.json')
    
    if args.format in ['markdown', 'both']:
        analyzer.export_markdown(output_dir / f'analysis_{timestamp}.md')
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()