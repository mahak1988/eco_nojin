"""
Phase 1.2: Localhost Hunter & Reporter
خروجی: فایل os.environ.get('HOST', 'localhost')_report.csv
"""
import os
import re
import csv

IGNORE_DIRS = {'.git', 'node_modules', '.venv', 'venv', 'env', '__pycache__', 
               'engine/cpp_core/build2', 'frontend/test-results', '_quarantine', '_backups', 'scripts'}

LOCALHOST_PATTERN = re.compile(
    r'(https?://)?(os.environ.get('HOST', 'localhost')|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?'
)

def should_scan(path):
    for ignore_dir in IGNORE_DIRS:
        if f"\\{ignore_dir}\\" in path or f"/{ignore_dir}/" in path:
            return False
    return True

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # پوشه scripts را هم اضافه کردم چون پر از کدهای موقتی است
    extensions = ('.py', '.ts', '.tsx', '.js', '.jsx', '.yaml', '.yml')
    report = []

    print("[INFO] Scanning for hardcoded os.environ.get('HOST', 'localhost') instances...")

    for root, _, files in os.walk(base_dir):
        if not should_scan(root):
            continue
        
        for file in files:
            if file.endswith(extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if LOCALHOST_PATTERN.search(line):
                                clean_line = line.strip()[:100] 
                                report.append({
                                    'File': filepath.replace(base_dir + "\\", ""),
                                    'Line': line_num,
                                    'Content': clean_line
                                })
                except Exception:
                    pass

    output_file = os.path.join(base_dir, 'os.environ.get('HOST', 'localhost')_report.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['File', 'Line', 'Content'])
        writer.writeheader()
        writer.writerows(report)

    print(f"[SUCCESS] Found {len(report)} instances.")
    print(f"[ACTION] Please open '{output_file}' to review them.")

if __name__ == "__main__":
    main()