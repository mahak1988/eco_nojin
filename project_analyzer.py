#!/usr/bin/env python3
"""
Eco Nojin Project Analyzer
===========================
Analyzes the project structure, dependencies, and architecture
to provide a comprehensive understanding before architectural planning.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime
import re


@dataclass
class FileInfo:
    """Information about a file in the project."""
    path: str
    name: str
    extension: str
    size_bytes: int
    last_modified: datetime
    line_count: Optional[int] = None
    
    @property
    def size_human(self) -> str:
        """Return human-readable file size."""
        size = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


@dataclass
class ModuleInfo:
    """Information about a Python or frontend module."""
    name: str
    path: str
    type: str  # 'python', 'react', 'typescript'
    files_count: int
    total_size: int
    has_init: bool = False
    has_tests: bool = False


@dataclass
class DependencyInfo:
    """Information about a dependency."""
    name: str
    version: str
    group: str  # 'core', 'geo', 'ml', 'dev', etc.
    type: str  # 'python', 'javascript'


@dataclass
class ProjectReport:
    """Complete project analysis report."""
    project_name: str
    project_path: str
    analysis_date: str
    
    # Structure
    total_files: int = 0
    total_directories: int = 0
    total_size_bytes: int = 0
    
    # File types
    python_files: List[FileInfo] = field(default_factory=list)
    typescript_files: List[FileInfo] = field(default_factory=list)
    config_files: List[FileInfo] = field(default_factory=list)
    
    # Modules
    python_modules: List[ModuleInfo] = field(default_factory=list)
    frontend_modules: List[ModuleInfo] = field(default_factory=list)
    
    # Dependencies
    python_dependencies: List[DependencyInfo] = field(default_factory=list)
    frontend_dependencies: List[DependencyInfo] = field(default_factory=list)
    
    # Special files
    has_pyproject: bool = False
    has_package_json: bool = False
    has_docker: bool = False
    has_tests: bool = False
    has_migrations: bool = False
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    @property
    def total_size_human(self) -> str:
        """Return human-readable total size."""
        size = self.total_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


class ProjectAnalyzer:
    """Analyzes a project structure and generates comprehensive reports."""
    
    IGNORE_DIRS = {
        '.git', '.venv', 'venv', 'env', '__pycache__', 
        'node_modules', 'dist', 'build', '.next',
        '.pytest_cache', '.mypy_cache', '.ruff_cache',
        'backups', '.idea', '.vscode'
    }
    
    PYTHON_EXTENSIONS = {'.py', '.pyx', '.pxd'}
    TYPESCRIPT_EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx'}
    CONFIG_EXTENSIONS = {
        '.json', '.yaml', '.yml', '.toml', '.ini', 
        '.cfg', '.env', '.gitignore', '.dockerignore'
    }
    
    def __init__(self, project_path: str):
        """Initialize the analyzer with project path."""
        self.project_path = Path(project_path).resolve()
        self.report = ProjectReport(
            project_name=self.project_path.name,
            project_path=str(self.project_path),
            analysis_date=datetime.now().isoformat()
        )
        
    def analyze(self) -> ProjectReport:
        """Run complete project analysis."""
        print(f"🔍 Analyzing project: {self.project_path}")
        
        # Check for key files
        self._check_key_files()
        
        # Scan directory structure
        self._scan_directory()
        
        # Analyze dependencies
        self._analyze_dependencies()
        
        # Detect modules
        self._detect_modules()
        
        # Generate recommendations
        self._generate_recommendations()
        
        return self.report
    
    def _check_key_files(self):
        """Check for key configuration files."""
        key_files = {
            'pyproject.toml': 'has_pyproject',
            'package.json': 'has_package_json',
            'Dockerfile': 'has_docker',
            'docker-compose.yml': 'has_docker',
        }
        
        for filename, attr in key_files.items():
            if (self.project_path / filename).exists():
                setattr(self.report, attr, True)
        
        # Check for tests directory
        if (self.project_path / 'tests').exists():
            self.report.has_tests = True
        
        # Check for migrations
        migrations_dirs = ['migrations', 'alembic', 'database/migrations']
        for mig_dir in migrations_dirs:
            if (self.project_path / mig_dir).exists():
                self.report.has_migrations = True
                break
    
    def _scan_directory(self, path: Optional[Path] = None, depth: int = 0):
        """Recursively scan directory structure."""
        if path is None:
            path = self.project_path
        
        try:
            items = list(path.iterdir())
        except PermissionError:
            self.report.warnings.append(f"Permission denied: {path}")
            return
        
        for item in items:
            # Skip ignored directories
            if item.is_dir() and item.name in self.IGNORE_DIRS:
                continue
            
            if item.is_dir():
                self.report.total_directories += 1
                self._scan_directory(item, depth + 1)
            elif item.is_file():
                self._process_file(item)
    
    def _process_file(self, file_path: Path):
        """Process a single file."""
        try:
            stat = file_path.stat()
            file_info = FileInfo(
                path=str(file_path.relative_to(self.project_path)),
                name=file_path.name,
                extension=file_path.suffix.lower(),
                size_bytes=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime)
            )
            
            self.report.total_files += 1
            self.report.total_size_bytes += stat.st_size
            
            # Classify file
            if file_info.extension in self.PYTHON_EXTENSIONS:
                # Count lines for Python files
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_info.line_count = sum(1 for _ in f)
                except:
                    pass
                self.report.python_files.append(file_info)
                
            elif file_info.extension in self.TYPESCRIPT_EXTENSIONS:
                self.report.typescript_files.append(file_info)
                
            elif file_info.extension in self.CONFIG_EXTENSIONS or file_info.name in {
                'Dockerfile', 'docker-compose.yml', '.gitignore', '.env'
            }:
                self.report.config_files.append(file_info)
                
        except Exception as e:
            self.report.warnings.append(f"Error processing {file_path}: {str(e)}")
    
    def _analyze_dependencies(self):
        """Analyze project dependencies."""
        # Analyze Python dependencies from pyproject.toml
        pyproject_path = self.project_path / 'pyproject.toml'
        if pyproject_path.exists():
            self._parse_pyproject_toml(pyproject_path)
        
        # Analyze frontend dependencies from package.json
        package_json_path = self.project_path / 'package.json'
        if not package_json_path.exists():
            # Check in frontend subdirectory
            package_json_path = self.project_path / 'frontend' / 'package.json'
        
        if package_json_path.exists():
            self._parse_package_json(package_json_path)
    
    def _parse_pyproject_toml(self, path: Path):
        """Parse pyproject.toml for dependencies."""
        try:
            # Try to use tomli/tomllib
            try:
                import tomllib
            except ImportError:
                try:
                    import tomli as tomllib
                except ImportError:
                    self.report.warnings.append(
                        "tomllib/tomli not available. Install with: pip install tomli"
                    )
                    return
            
            with open(path, 'rb') as f:
                data = tomllib.load(f)
            
            # Core dependencies
            core_deps = data.get('project', {}).get('dependencies', [])
            for dep in core_deps:
                name, version = self._parse_dependency_string(dep)
                self.report.python_dependencies.append(
                    DependencyInfo(name=name, version=version, group='core', type='python')
                )
            
            # Optional dependencies
            optional_deps = data.get('project', {}).get('optional-dependencies', {})
            for group, deps in optional_deps.items():
                for dep in deps:
                    name, version = self._parse_dependency_string(dep)
                    self.report.python_dependencies.append(
                        DependencyInfo(name=name, version=version, group=group, type='python')
                    )
                    
        except Exception as e:
            self.report.warnings.append(f"Error parsing pyproject.toml: {str(e)}")
    
    def _parse_package_json(self, path: Path):
        """Parse package.json for dependencies."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Dependencies
            deps = data.get('dependencies', {})
            for name, version in deps.items():
                self.report.frontend_dependencies.append(
                    DependencyInfo(name=name, version=version, group='dependencies', type='javascript')
                )
            
            # Dev dependencies
            dev_deps = data.get('devDependencies', {})
            for name, version in dev_deps.items():
                self.report.frontend_dependencies.append(
                    DependencyInfo(name=name, version=version, group='devDependencies', type='javascript')
                )
                
        except Exception as e:
            self.report.warnings.append(f"Error parsing package.json: {str(e)}")
    
    def _parse_dependency_string(self, dep_str: str) -> tuple[str, str]:
        """Parse dependency string like 'numpy>=2.3,<2.4' into (name, version)."""
        # Remove extras like [binary]
        dep_str = re.sub(r'\[.*?\]', '', dep_str)
        
        # Split on version operators
        match = re.match(r'^([a-zA-Z0-9_-]+)(.*)$', dep_str.strip())
        if match:
            return match.group(1), match.group(2) or '*'
        return dep_str, '*'
    
    def _detect_modules(self):
        """Detect Python and frontend modules."""
        # Detect Python modules
        for item in self.project_path.iterdir():
            if item.is_dir() and item.name not in self.IGNORE_DIRS:
                # Check if it's a Python package
                init_file = item / '__init__.py'
                if init_file.exists() or (item / 'pyproject.toml').exists():
                    module_files = list(item.rglob('*.py'))
                    module_size = sum(f.stat().st_size for f in module_files)
                    
                    # Check for tests
                    has_tests = any('test' in f.name.lower() for f in module_files)
                    
                    self.report.python_modules.append(ModuleInfo(
                        name=item.name,
                        path=str(item.relative_to(self.project_path)),
                        type='python',
                        files_count=len(module_files),
                        total_size=module_size,
                        has_init=init_file.exists(),
                        has_tests=has_tests
                    ))
        
        # Detect frontend modules
        frontend_path = self.project_path / 'frontend'
        if frontend_path.exists():
            src_path = frontend_path / 'src'
            if src_path.exists():
                for item in src_path.iterdir():
                    if item.is_dir() and item.name not in self.IGNORE_DIRS:
                        module_files = list(item.rglob('*'))
                        module_files = [f for f in module_files if f.is_file()]
                        module_size = sum(f.stat().st_size for f in module_files)
                        
                        self.report.frontend_modules.append(ModuleInfo(
                            name=item.name,
                            path=str(item.relative_to(self.project_path)),
                            type='react',
                            files_count=len(module_files),
                            total_size=module_size
                        ))
    
    def _generate_recommendations(self):
        """Generate architectural recommendations based on analysis."""
        # Check for large files
        large_files = [f for f in self.report.python_files if f.size_bytes > 1_000_000]
        if large_files:
            self.report.warnings.append(
                f"Found {len(large_files)} large Python files (>1MB). Consider refactoring."
            )
        
        # Check for missing tests
        modules_without_tests = [m for m in self.report.python_modules if not m.has_tests]
        if modules_without_tests:
            self.report.recommendations.append(
                f"Consider adding tests for modules: {', '.join(m.name for m in modules_without_tests)}"
            )
        
        # Check for Docker
        if not self.report.has_docker:
            self.report.recommendations.append(
                "Consider adding Docker configuration for reproducible deployments."
            )
        
        # Check for migrations
        if not self.report.has_migrations and self.report.has_pyproject:
            self.report.recommendations.append(
                "Consider setting up database migrations (e.g., Alembic) for schema management."
            )
    
    def export_json(self, output_path: str):
        """Export report as JSON."""
        # Convert dataclasses to dict
        report_dict = asdict(self.report)
        
        # Convert datetime objects to strings
        for file_list in ['python_files', 'typescript_files', 'config_files']:
            for file_info in report_dict[file_list]:
                file_info['last_modified'] = file_info['last_modified'].isoformat()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON report exported to: {output_path}")
    
    def export_markdown(self, output_path: str):
        """Export report as Markdown."""
        lines = []
        
        # Header
        lines.append(f"# 📊 Project Analysis Report: {self.report.project_name}")
        lines.append(f"**Analysis Date:** {self.report.analysis_date}")
        lines.append(f"**Project Path:** `{self.report.project_path}`")
        lines.append("")
        
        # Summary
        lines.append("## 📈 Summary")
        lines.append(f"- **Total Files:** {self.report.total_files:,}")
        lines.append(f"- **Total Directories:** {self.report.total_directories:,}")
        lines.append(f"- **Total Size:** {self.report.total_size_human}")
        lines.append(f"- **Python Files:** {len(self.report.python_files):,}")
        lines.append(f"- **TypeScript Files:** {len(self.report.typescript_files):,}")
        lines.append("")
        
        # Key Features
        lines.append("## ✅ Key Features Detected")
        features = [
            ("pyproject.toml", self.report.has_pyproject),
            ("package.json", self.report.has_package_json),
            ("Docker", self.report.has_docker),
            ("Tests", self.report.has_tests),
            ("Database Migrations", self.report.has_migrations),
        ]
        for name, present in features:
            status = "✅" if present else "❌"
            lines.append(f"- {status} {name}")
        lines.append("")
        
        # Python Modules
        if self.report.python_modules:
            lines.append("## 🐍 Python Modules")
            lines.append("| Module | Files | Size | Has Tests |")
            lines.append("|--------|-------|------|-----------|")
            for module in sorted(self.report.python_modules, key=lambda m: m.total_size, reverse=True):
                size_mb = module.total_size / (1024 * 1024)
                tests = "✅" if module.has_tests else "❌"
                lines.append(f"| {module.name} | {module.files_count} | {size_mb:.2f} MB | {tests} |")
            lines.append("")
        
        # Frontend Modules
        if self.report.frontend_modules:
            lines.append("## ⚛️ Frontend Modules")
            lines.append("| Module | Files | Size |")
            lines.append("|--------|-------|------|")
            for module in sorted(self.report.frontend_modules, key=lambda m: m.total_size, reverse=True):
                size_mb = module.total_size / (1024 * 1024)
                lines.append(f"| {module.name} | {module.files_count} | {size_mb:.2f} MB |")
            lines.append("")
        
        # Dependencies
        if self.report.python_dependencies:
            lines.append("## 📦 Python Dependencies")
            groups = defaultdict(list)
            for dep in self.report.python_dependencies:
                groups[dep.group].append(dep)
            
            for group, deps in sorted(groups.items()):
                lines.append(f"### {group.title()}")
                for dep in sorted(deps, key=lambda d: d.name):
                    lines.append(f"- `{dep.name}` {dep.version}")
                lines.append("")
        
        if self.report.frontend_dependencies:
            lines.append("## 📦 Frontend Dependencies")
            groups = defaultdict(list)
            for dep in self.report.frontend_dependencies:
                groups[dep.group].append(dep)
            
            for group, deps in sorted(groups.items()):
                lines.append(f"### {group.title()}")
                for dep in sorted(deps, key=lambda d: d.name):
                    lines.append(f"- `{dep.name}` {dep.version}")
                lines.append("")
        
        # Warnings
        if self.report.warnings:
            lines.append("## ⚠️ Warnings")
            for warning in self.report.warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        # Recommendations
        if self.report.recommendations:
            lines.append("## 💡 Recommendations")
            for rec in self.report.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Markdown report exported to: {output_path}")


def main():
    """Main entry point."""
    # Determine project path
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = os.getcwd()
    
    print("=" * 80)
    print("🔬 Eco Nojin Project Analyzer")
    print("=" * 80)
    
    # Run analysis
    analyzer = ProjectAnalyzer(project_path)
    report = analyzer.analyze()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Total Files: {report.total_files:,}")
    print(f"Total Size: {report.total_size_human}")
    print(f"Python Files: {len(report.python_files):,}")
    print(f"TypeScript Files: {len(report.typescript_files):,}")
    print(f"Python Modules: {len(report.python_modules)}")
    print(f"Frontend Modules: {len(report.frontend_modules)}")
    
    # Export reports
    output_dir = Path(project_path)
    json_path = output_dir / 'project_analysis.json'
    md_path = output_dir / 'project_analysis.md'
    
    analyzer.export_json(str(json_path))
    analyzer.export_markdown(str(md_path))
    
    print("\n✅ Analysis complete! Check the generated reports:")
    print(f"  - JSON: {json_path}")
    print(f"  - Markdown: {md_path}")


if __name__ == '__main__':
    main()