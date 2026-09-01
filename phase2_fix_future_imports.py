"""
Phase 2.7: Future Import Fixer
رفع ارور SyntaxError ناشی از تزریق structlog قبل از __future__
"""
import os

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    structlog_idx = -1
    last_future_idx = -1

    # پیدا کردن ایندکس‌ها
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('from __future__'):
            last_future_idx = i
        elif 'import structlog' in stripped and structlog_idx == -1:
            structlog_idx = i

    # اگر structlog قبل از __future__ آمده باشد
    if structlog_idx != -1 and last_future_idx != -1 and structlog_idx < last_future_idx:
        print(f"  [FIXING] {filepath.replace(os.getcwd() + os.sep, '')}")
        
        # استخراج بلوک structlog (معمولا 2 یا 3 خط است که اسکریپت قبلی اضافه کرده)
        structlog_block = []
        i = structlog_idx
        # جمع آوری خطوط structlog و logger و خطوط خالی بینشان
        while i < len(lines) and ('structlog' in lines[i] or 'logger = ' in lines[i] or lines[i].strip() == ''):
            structlog_block.append(lines[i])
            i += 1
            
        # حذف بلوک از جای قدیمی
        for _ in structlog_block:
            lines.pop(structlog_idx)
            
        # چون چند خط پاک کردیم، ایندکس __future__ جابجا شده است
        new_future_idx = last_future_idx - len(structlog_block)
        
        # inserting بلافاصله بعد از آخرین __future__
        for j, block_line in enumerate(structlog_block):
            lines.insert(new_future_idx + 1 + j, block_line)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True

    return False

def main():
    base_dir = os.getcwd()
    fixes = 0
    print("[ACTION] Scanning for misplaced structlog imports...\n")
    
    for root, _, files in os.walk(base_dir):
        # نادیده گرفتن پوشه‌های اضافی
        if '.venv' in root or 'node_modules' in root or '.git' in root:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixes += 1

    print(f"\n[RESULT] Fixed {fixes} file(s).")
    if fixes > 0:
        print("[INFO] The 'from __future__' rule is now respected.")

if __name__ == "__main__":
    main()