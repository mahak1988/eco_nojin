"""
Phase 2.5: Safe Localhost to Env Variable Injector
تبدیل localhost به os.environ.get تا پروژه قابلیت دیپلوی پیدا کند
"""
import os
import csv

CSV_FILE = "localhost_report.csv"

def fix_python_file(filepath, line_num, bad_line):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # خط‌ها از 1 شروع می‌شوند، لیست از 0
    target_idx = line_num - 1
    original_line = lines[target_idx]
    
    # استراتژی جایگزینی ایمن
    new_line = original_line
    
    # اگر در یک رشته استرینگ (URL) است
    if 'localhost' in new_line:
        # جایگزینی localhost با متغیر محیطی با یک فال‌بک امن
        new_line = new_line.replace('localhost', "os.environ.get('HOST', 'localhost')")
        
    if '127.0.0.1' in new_line:
        new_line = new_line.replace('127.0.0.1', "os.environ.get('HOST', '127.0.0.1')")

    if new_line != original_line:
        lines[target_idx] = new_line
        
        # بررسی اینکه آیا import os در فایل وجود دارد یا خیر
        has_os_import = any('import os' in line for line in lines)
        if not has_os_import:
            # پیدا کردن اولین ایمپورت و اضافه کردن os
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i, 'import os\n\n')
                    break
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, CSV_FILE)
    
    if not os.path.exists(csv_path):
        print(f"[ERROR] {CSV_FILE} not found. Run phase1_find_localhost.py first.")
        return

    print("[INFO] Reading localhost report...")
    fixes = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filepath = os.path.join(base_dir, row['File'].replace('/', os.sep))
            line_num = int(row['Line'])
            
            # فقط فایل‌های پایتون را FIX میکنیم (فرانت را بعداً در محیط خودش فیکس میکنیم)
            if filepath.endswith('.py') and os.path.exists(filepath):
                if fix_python_file(filepath, line_num, row['Content']):
                    print(f"  [FIXED] {row['File']}:{line_num}")
                    fixes += 1

    print(f"\n[SUCCESS] Injected environment variables into {fixes} Python files.")
    print("[INFO] Now you can set HOST=your-server-ip in your .env file for deployment.")

if __name__ == "__main__":
    main()