"""
Phase 2.3: Sniper Circular Dependency Fixer
جستجوی دقیق در تمام فایل‌های پوشه برای پیدا کردن خط ایمپورت مشکل‌ساز و کامنت کردن آن
"""
import os

# تعریف دقیق هدف‌ها: کجا را بگردیم و چه چیزی را پاک کنیم
TARGETS = [
    {
        "search_dir": "services/data_manual",
        "bad_import_string": "services.api_gateway.routers.manual_data"
    },
    {
        "search_dir": "engine/hydroma/biofertilizer",
        "bad_import_string": "database.config"
    }
]

def sniper_fix(base_dir, target_dir, bad_string):
    full_dir = os.path.join(base_dir, target_dir)
    if not os.path.exists(full_dir):
        print(f"  [SKIP] Directory not found: {target_dir}")
        return False

    for root, _, files in os.walk(full_dir):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = []
            file_modified = False

            for i, line in enumerate(lines):
                # اگر خط حاوی ایمپورت ممنوعه باشد و از قبل کامنت نشده باشد
                if bad_string in line and not line.strip().startswith('#'):
                    print(f"  [TARGET ACQUIRED] {filepath.replace(base_dir + os.sep, '')}:{i+1}")
                    print(f"    Original: {line.strip()}")
                    
                    new_lines.append(f"# [PHASE 2 BLOCKED] Circular dependency fix: {line}")
                    file_modified = True
                else:
                    new_lines.append(line)

            if file_modified:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                return True # فرض می‌کنیم در هر پوشه فقط یک جا ایمپورت شده

    return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print("[ACTION] Sniping circular dependency imports...\n")
    
    fixes = 0
    for target in TARGETS:
        print(f"Searching in '{target['search_dir']}' for '{target['bad_import_string']}'...")
        if sniper_fix(base_dir, target["search_dir"], target["bad_import_string"]):
            fixes += 1
            print("  -> Neutralized!\n")
        else:
            print("  -> Not found or already fixed.\n")

    print(f"[RESULT] {fixes} import(s) successfully blocked.")
    if fixes > 0:
        print("[WARN] Please test your backend to ensure no function is missing.")

if __name__ == "__main__":
    main()