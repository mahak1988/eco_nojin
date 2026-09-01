"""
Phase 2.4: API Gateway Fat Router Detector
بررسی میکند که آیا روترهای API مستقیما با دیتابیس ارتباط دارند؟
"""
import os

GATEWAY_DIR = "services/api_gateway/routers"
# کلمات کلیدی که نشان دهنده دسترسی مستقیم به دیتابیس در لایه روتر هستند
DB_KEYWORDS = [
    "SessionLocal", 
    "get_db", 
    "db.execute", 
    "db.query", 
    "db.add", 
    "session.execute",
    "session.query"
]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gateway_path = os.path.join(base_dir, GATEWAY_DIR)
    
    if not os.path.exists(gateway_path):
        print(f"[ERROR] Gateway directory not found: {GATEWAY_DIR}")
        return

    violations = []
    total_routers = 0

    print(f"[INFO] Auditing API Gateway routers in /{GATEWAY_DIR}...\n")

    for root, _, files in os.walk(gateway_path):
        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                total_routers += 1
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, base_dir)
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                        
                    for keyword in DB_KEYWORDS:
                        if keyword in stripped:
                            violations.append({
                                'file': rel_path,
                                'line': i,
                                'code': stripped[:80],
                                'keyword': keyword
                            })
                            break # فقط یک بار برای هر خط ثبت کن

    print(f"Checked {total_routers} router files.")
    
    if not violations:
        print("\n✅ [EXCELLENT] All routers are SKINNY! No direct database access found.")
        print("Your API Gateway perfectly follows Clean Architecture.")
        return

    print(f"\n⚠️ [WARNING] Found {len(violations)} instances of direct DB access in routers (Fat Routers):\n")
    
    # گروه بندی بر اساس فایل
    from collections import defaultdict
    grouped = defaultdict(list)
    for v in violations:
        grouped[v['file']].append(v)

    for file, items in grouped.items():
        print(f"🚨 {file} ({len(items)} issues):")
        for item in items:
            print(f"   Line {item['line']}: [{item['keyword']}] {item['code']}")
        print()

if __name__ == "__main__":
    main()