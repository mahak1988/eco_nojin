"""
Phase 2.1: Advanced Circular Dependency Detector
استفاده از AST برای پیدا کردن دقیق ایمپورت‌های داخلی پروژه
"""
import os
import ast
from collections import defaultdict

# پوشه‌هایی که باید اسکن شوند (ماژول‌های اصلی پروژه)
SCAN_DIRS = ['engine', 'services', 'adapters', 'database']
IGNORE_DIRS = {'__pycache__', 'tests', '.venv', 'node_modules', 'build2'}

class ImportVisitor(ast.NodeVisitor):
    def __init__(self, current_module):
        self.current_module = current_module
        self.imports = set()

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.level == 0: # فقط ایمپورت‌های مطلق (نه relative like from . import x)
            self.imports.add(node.module)
        self.generic_visit(node)

def get_module_name(filepath, base_dir):
    # تبدیل مسیر فایل به نام ماژول (مثال: services/auth/main.py -> services.auth.main)
    rel_path = os.path.relpath(filepath, base_dir)
    return rel_path.replace(os.sep, '.').replace('.py', '').replace('.__init__', '')

def find_cycles(graph):
    """پیدا کردن تمام حلقه‌ها در گراف با استفاده از DFS"""
    visited = set()
    path = set()
    cycles = []

    def dfs(node):
        visited.add(node)
        path.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in path:
                # یک حلقه پیدا شد!
                cycle_start = list(path).index(neighbor)
                cycle = list(path)[cycle_start:] + [neighbor]
                cycles.append(cycle)
        
        path.remove(node)

    for node in list(graph.keys()):
        if node not in visited:
            dfs(node)
            
    return cycles

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    graph = defaultdict(set)

    print("[INFO] Scanning Python files for internal imports (This may take a few seconds)...")
    
    for scan_dir in SCAN_DIRS:
        dir_path = os.path.join(base_dir, scan_dir)
        if not os.path.exists(dir_path):
            continue
            
        for root, _, files in os.walk(dir_path):
            # نادیده گرفتن پوشه‌های تست و بیلد
            if any(ignore in root for ignore in IGNORE_DIRS):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    module_name = get_module_name(filepath, base_dir)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            tree = ast.parse(f.read(), filename=filepath)
                            
                        visitor = ImportVisitor(module_name)
                        visitor.visit(tree)
                        
                        # فقط ایمپورت‌هایی را اضافه کن که به پروژه خودمان اشاره دارند
                        for imp in visitor.imports:
                            if any(imp.startswith(d) for d in SCAN_DIRS):
                                graph[module_name].add(imp)
                    except SyntaxError:
                        pass # فایل‌هایی که سینتکس خراب دارند (مثلاً پرینت‌های تبدیل شده اشتباه) را نادیده می‌گیریم

    print(f"[INFO] Built graph with {len(graph)} nodes.")
    print("[ACTION] Analyzing for circular dependencies...\n")

    cycles = find_cycles(graph)
    
    if not cycles:
        print("✅ [SUCCESS] No circular dependencies found in core modules!")
        return

    print(f"⚠️ [WARNING] Found {len(cycles)} circular dependency chain(s):\n")
    
    # حذف حلقه‌های تکراری (اگر A->B->A و B->A->B پیدا شده باشد)
    unique_cycles = set()
    for cycle in cycles:
        # مرتب‌سازی برای پیدا کردن حلقه‌های یکسان با شروع‌های متفاوت
        normalized = tuple(sorted(cycle[:-1]))
        unique_cycles.add(normalized)

    for i, cycle in enumerate(unique_cycles, 1):
        print(f"Cycle {i}: {' -> '.join(cycle)} -> {cycle[0]}")
        
    print("\n[ADVICE] To fix these, use Dependency Injection or move shared code to a new 'shared' or 'core' module.")

if __name__ == "__main__":
    main()