#!/usr/bin/env python3
"""
Eco Nojin - Placeholder Triage Tool
====================================
Identifies, categorizes, and prioritizes placeholder/incomplete files.

Categories:
  - EMPTY: File with no meaningful content
  - STUB: File with only pass/NotImplementedError
  - MINIMAL: File with < 10 lines of actual code
  - PARTIAL: File with some implementation but incomplete
  
Output:
  - triage_report.json (structured data)
  - triage_report.md (human-readable)
  - Decision matrix for Keep/Implement/Remove
"""
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter


PROJECT_ROOT = Path(__file__).parent
REPORT_JSON = PROJECT_ROOT / "triage_report.json"
REPORT_MD = PROJECT_ROOT / "triage_report.md"

# Module importance scoring (business value)
MODULE_IMPORTANCE = {
    # Core scientific modules (highest priority)
    'soil': 10, 'carbon': 10, 'satellite': 9, 'hydrology': 9,
    'climate': 8, 'crop': 8, 'scenarios': 8,
    
    # Business modules
    'marketplace': 7, 'ecowallet': 7, 'blockchain': 6,
    'mrv': 7, 'finance': 6,
    
    # Supporting modules
    'geospatial': 7, 'groundwater': 6, 'erosion': 6,
    'watershed': 6, 'materials': 5, 'plants': 5,
    
    # Infrastructure
    'api': 8, 'config': 8, 'core': 9, 'ml': 5,
    'data_ingestion': 6, 'performance': 4,
    
    # Optional/future
    'ecotourism': 3, 'web_search': 3, 'risk': 5,
    'standards': 6, 'scenario': 5,
    
    # Services
    'auth': 9, 'notification': 5, 'reporting': 5,
    'workflow': 5, 'ledger': 6,
}

# Ignore patterns
IGNORE_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', 'node_modules',
    '.next', '.pytest_cache', '.mypy_cache', 'build', 'dist',
    '.idea', '.vscode', 'coverage', 'htmlcov'
}


@dataclass
class PlaceholderFile:
    """Represents a placeholder/incomplete file."""
    path: str
    category: str  # EMPTY, STUB, MINIMAL, PARTIAL
    total_lines: int
    code_lines: int
    has_docstring: bool
    has_imports: bool
    has_functions: bool
    has_classes: bool
    function_count: int
    class_count: int
    module_name: str
    importance_score: int
    recommendation: str  # KEEP, IMPLEMENT, REMOVE, REVIEW
    effort_estimate: str  # hours
    notes: str


class PlaceholderTriage:
    """Main triage engine."""
    
    def __init__(self):
        self.files: List[PlaceholderFile] = []
        self.stats = {
            'total_scanned': 0,
            'placeholders_found': 0,
            'by_category': Counter(),
            'by_module': Counter(),
            'by_recommendation': Counter()
        }
    
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        parts = path.parts
        return any(p in IGNORE_DIRS for p in parts)
    
    def get_module_name(self, file_path: Path) -> str:
        """Extract module name from file path."""
        try:
            rel = file_path.relative_to(PROJECT_ROOT)
            parts = rel.parts
            
            # Get the main module name
            if len(parts) >= 2:
                return parts[0] if parts[0] not in ['engine', 'services'] else parts[1] if len(parts) > 1 else parts[0]
            return parts[0] if parts else 'root'
        except:
            return 'unknown'
    
    def analyze_file(self, file_path: Path) -> Optional[PlaceholderFile]:
        """Analyze a single file for placeholder characteristics."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            # Count different line types
            total_lines = len(lines)
            blank_lines = sum(1 for line in lines if not line.strip())
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            docstring_lines = content.count('"""') + content.count("'''")
            
            # Count actual code lines (non-blank, non-comment)
            code_lines = 0
            in_docstring = False
            for line in lines:
                stripped = line.strip()
                
                # Track docstrings
                if '"""' in stripped or "'''" in stripped:
                    in_docstring = not in_docstring
                    continue
                
                if in_docstring:
                    continue
                
                if stripped and not stripped.startswith('#'):
                    code_lines += 1
            
            # Detect features
            has_docstring = '"""' in content or "'''" in content
            has_imports = bool(re.search(r'^(import|from)\s+', content, re.MULTILINE))
            function_count = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))
            class_count = len(re.findall(r'^class\s+\w+', content, re.MULTILINE))
            
            # Check for stub indicators
            has_notimplemented = 'NotImplementedError' in content
            has_pass_only = bool(re.search(r'^\s*pass\s*$', content, re.MULTILINE))
            
            # Categorize
            category = self._categorize(
                total_lines, code_lines, has_docstring, has_imports,
                function_count, class_count, has_notimplemented, has_pass_only
            )
            
            # Only include if it's a placeholder
            if category == 'COMPLETE':
                return None
            
            # Get module and importance
            module_name = self.get_module_name(file_path)
            importance = MODULE_IMPORTANCE.get(module_name.lower(), 5)
            
            # Generate recommendation
            recommendation, effort, notes = self._generate_recommendation(
                category, module_name, importance, code_lines, 
                function_count, class_count
            )
            
            return PlaceholderFile(
                path=str(file_path.relative_to(PROJECT_ROOT)),
                category=category,
                total_lines=total_lines,
                code_lines=code_lines,
                has_docstring=has_docstring,
                has_imports=has_imports,
                has_functions=function_count > 0,
                has_classes=class_count > 0,
                function_count=function_count,
                class_count=class_count,
                module_name=module_name,
                importance_score=importance,
                recommendation=recommendation,
                effort_estimate=effort,
                notes=notes
            )
            
        except Exception as e:
            return None
    
    def _categorize(self, total_lines: int, code_lines: int, has_docstring: bool,
                    has_imports: bool, function_count: int, class_count: int,
                    has_notimplemented: bool, has_pass_only: bool) -> str:
        """Categorize file based on characteristics."""
        
        # EMPTY: No meaningful content
        if code_lines <= 2 and total_lines < 10:
            return 'EMPTY'
        
        # STUB: Only pass/NotImplementedError
        if has_notimplemented or (has_pass_only and code_lines < 5):
            return 'STUB'
        
        # MINIMAL: Very little actual code
        if code_lines < 10:
            return 'MINIMAL'
        
        # PARTIAL: Some implementation but likely incomplete
        if code_lines < 50 and (function_count == 0 or has_notimplemented):
            return 'PARTIAL'
        
        # COMPLETE: Seems to have real implementation
        return 'COMPLETE'
    
    def _generate_recommendation(self, category: str, module_name: str, 
                                  importance: int, code_lines: int,
                                  function_count: int, class_count: int) -> Tuple[str, str, str]:
        """Generate recommendation based on analysis."""
        
        # High importance modules should be implemented
        if importance >= 8:
            if category == 'EMPTY':
                return ('IMPLEMENT', '8-16 hours', 
                       f'Critical module {module_name} needs full implementation')
            elif category == 'STUB':
                return ('IMPLEMENT', '4-8 hours',
                       f'Stub functions in {module_name} need implementation')
            elif category == 'MINIMAL':
                return ('IMPLEMENT', '2-4 hours',
                       f'Minimal implementation in {module_name} needs expansion')
            else:
                return ('REVIEW', '1-2 hours',
                       f'Partial implementation in {module_name} needs review')
        
        # Medium importance - decide based on category
        elif importance >= 5:
            if category == 'EMPTY':
                return ('REVIEW', '1 hour',
                       f'Empty module {module_name} - decide if needed')
            elif category == 'STUB':
                return ('IMPLEMENT', '2-4 hours',
                       f'Stub in {module_name} - implement if in roadmap')
            else:
                return ('KEEP', '0 hours',
                       f'Acceptable minimal implementation in {module_name}')
        
        # Low importance - consider removal
        else:
            if category == 'EMPTY':
                return ('REMOVE', '0 hours',
                       f'Empty low-priority module {module_name} - consider removal')
            elif category == 'STUB':
                return ('REVIEW', '30 min',
                       f'Stub in low-priority {module_name} - review necessity')
            else:
                return ('KEEP', '0 hours',
                       f'Keep as-is for future use')
    
    def scan_project(self) -> None:
        """Scan all Python files for placeholders."""
        print("\n" + "="*70)
        print("  SCANNING FOR PLACEHOLDERS")
        print("="*70)
        
        py_files = list(PROJECT_ROOT.rglob('*.py'))
        py_files = [f for f in py_files if not self.should_ignore(f)]
        
        print(f"  Python files to analyze: {len(py_files)}")
        
        for file_path in py_files:
            self.stats['total_scanned'] += 1
            
            result = self.analyze_file(file_path)
            if result:
                self.files.append(result)
                self.stats['placeholders_found'] += 1
                self.stats['by_category'][result.category] += 1
                self.stats['by_module'][result.module_name] += 1
                self.stats['by_recommendation'][result.recommendation] += 1
        
        print(f"\n  ✅ Scan complete")
        print(f"     Total scanned: {self.stats['total_scanned']}")
        print(f"     Placeholders found: {self.stats['placeholders_found']}")
        print(f"\n  By category:")
        for cat, count in self.stats['by_category'].most_common():
            print(f"     {cat}: {count}")
        
        print(f"\n  By recommendation:")
        for rec, count in self.stats['by_recommendation'].most_common():
            print(f"     {rec}: {count}")
    
    def generate_reports(self) -> None:
        """Generate JSON and Markdown reports."""
        print("\n" + "="*70)
        print("  GENERATING REPORTS")
        print("="*70)
        
        # JSON report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'project_path': str(PROJECT_ROOT),
            'statistics': {
                'total_scanned': self.stats['total_scanned'],
                'placeholders_found': self.stats['placeholders_found'],
                'by_category': dict(self.stats['by_category']),
                'by_module': dict(self.stats['by_module']),
                'by_recommendation': dict(self.stats['by_recommendation'])
            },
            'files': [asdict(f) for f in self.files]
        }
        
        REPORT_JSON.write_text(
            json.dumps(report_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"  ✓ JSON report: {REPORT_JSON}")
        
        # Markdown report
        md = self._generate_markdown_report()
        REPORT_MD.write_text(md, encoding='utf-8')
        print(f"  ✓ Markdown report: {REPORT_MD}")
    
    def _generate_markdown_report(self) -> str:
        """Generate human-readable Markdown report."""
        md = []
        md.append("# 📋 Placeholder Triage Report")
        md.append(f"\n**Generated:** {datetime.now().isoformat()}")
        md.append(f"**Project:** `{PROJECT_ROOT}`")
        md.append(f"**Files Scanned:** {self.stats['total_scanned']}")
        md.append(f"**Placeholders Found:** {self.stats['placeholders_found']}")
        
        # Summary by category
        md.append("\n## 📊 Summary by Category\n")
        md.append("| Category | Count | Description |")
        md.append("|----------|-------|-------------|")
        
        category_desc = {
            'EMPTY': 'No meaningful content',
            'STUB': 'Only pass/NotImplementedError',
            'MINIMAL': '< 10 lines of actual code',
            'PARTIAL': 'Some implementation but incomplete'
        }
        
        for cat, count in self.stats['by_category'].most_common():
            md.append(f"| {cat} | {count} | {category_desc.get(cat, 'Unknown')} |")
        
        # Summary by recommendation
        md.append("\n## 🎯 Summary by Recommendation\n")
        md.append("| Recommendation | Count | Action |")
        md.append("|----------------|-------|--------|")
        
        rec_desc = {
            'IMPLEMENT': '🔨 Needs implementation',
            'REVIEW': '👀 Needs review/decision',
            'KEEP': '✅ Keep as-is',
            'REMOVE': '🗑️ Consider removal'
        }
        
        for rec, count in self.stats['by_recommendation'].most_common():
            md.append(f"| {rec} | {count} | {rec_desc.get(rec, 'Unknown')} |")
        
        # Detailed by module
        md.append("\n## 📁 Detailed Analysis by Module\n")
        
        by_module = defaultdict(list)
        for f in self.files:
            by_module[f.module_name].append(f)
        
        for module, files in sorted(by_module.items(), 
                                     key=lambda x: -max(f.importance_score for f in x[1])):
            max_importance = max(f.importance_score for f in files)
            md.append(f"### `{module}` (Importance: {max_importance}/10)\n")
            
            for f in sorted(files, key=lambda x: -x.importance_score):
                emoji = {'IMPLEMENT': '🔨', 'REVIEW': '👀', 
                        'KEEP': '✅', 'REMOVE': '🗑️'}.get(f.recommendation, '❓')
                
                md.append(f"- {emoji} **`{f.path}`**")
                md.append(f"  - Category: {f.category} | Lines: {f.code_lines}/{f.total_lines}")
                md.append(f"  - Recommendation: **{f.recommendation}** ({f.effort_estimate})")
                md.append(f"  - Notes: {f.notes}")
        
        # Action plan
        md.append("\n## 🎯 Action Plan\n")
        
        implement_files = [f for f in self.files if f.recommendation == 'IMPLEMENT']
        review_files = [f for f in self.files if f.recommendation == 'REVIEW']
        remove_files = [f for f in self.files if f.recommendation == 'REMOVE']
        
        if implement_files:
            md.append(f"### 🔨 To Implement ({len(implement_files)} files)\n")
            total_effort = sum(int(f.effort_estimate.split('-')[0]) for f in implement_files if '-' in f.effort_estimate)
            md.append(f"**Estimated effort:** ~{total_effort}+ hours\n")
            
            for f in sorted(implement_files, key=lambda x: -x.importance_score)[:20]:
                md.append(f"1. `{f.path}` - {f.notes}")
        
        if review_files:
            md.append(f"\n### 👀 To Review ({len(review_files)} files)\n")
            for f in sorted(review_files, key=lambda x: -x.importance_score)[:20]:
                md.append(f"- `{f.path}` - {f.notes}")
        
        if remove_files:
            md.append(f"\n### 🗑️ To Consider Removing ({len(remove_files)} files)\n")
            for f in remove_files[:20]:
                md.append(f"- `{f.path}` - {f.notes}")
        
        # Recommendations
        md.append("\n## 💡 Strategic Recommendations\n")
        md.append("1. **Priority 1:** Implement high-importance EMPTY/STUB modules")
        md.append("2. **Priority 2:** Review PARTIAL implementations for completeness")
        md.append("3. **Priority 3:** Remove or archive low-priority empty modules")
        md.append("4. **Documentation:** Add docstrings to all MINIMAL files")
        md.append("5. **Testing:** Create test stubs for IMPLEMENT files")
        
        return "\n".join(md)
    
    def run(self) -> None:
        """Execute complete triage pipeline."""
        print("\n" + "█"*70)
        print("  ECO NOJIN - PLACEHOLDER TRIAGE")
        print("█"*70)
        
        self.scan_project()
        self.generate_reports()
        
        print("\n" + "█"*70)
        print("  TRIAGE COMPLETE")
        print("█"*70)
        print(f"\n📄 Reports:")
        print(f"   • {REPORT_JSON}")
        print(f"   • {REPORT_MD}")


if __name__ == '__main__':
    triage = PlaceholderTriage()
    triage.run()