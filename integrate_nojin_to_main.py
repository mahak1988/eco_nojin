"""
Integrate Nojin Router into Main Application
==============================================
Adds Nojin router to services/api_gateway/main.py (the REAL main app)
so all endpoints are available on the single unified server (port 8000).

Run: python integrate_nojin_to_main.py
"""

from pathlib import Path
import shutil

PROJECT_ROOT = Path(r"D:\eco_nojin")
MAIN_FILE = PROJECT_ROOT / "services" / "api_gateway" / "main.py"

print("=" * 80)
print("🔧 INTEGRATING NOJIN INTO MAIN APPLICATION")
print("=" * 80)

# Step 1: Check main file exists
if not MAIN_FILE.exists():
    print(f"❌ Main file not found: {MAIN_FILE}")
    exit(1)

print(f"✅ Found main file: {MAIN_FILE.relative_to(PROJECT_ROOT)}")

# Step 2: Read and analyze
content = MAIN_FILE.read_text(encoding="utf-8")
print(f"📏 File size: {len(content)} characters")

# Step 3: Check if already integrated
if "from services.api_gateway.routers import nojin" in content or \
   "from .routers import nojin" in content:
    print("✅ Nojin router already imported")
    has_import = True
else:
    has_import = False

if "include_router(nojin.router)" in content or "include_router(nojin)" in content:
    print("✅ Nojin router already registered")
    has_registration = True
else:
    has_registration = False

if has_import and has_registration:
    print("\n🎉 Nojin router already fully integrated!")
    print("   All endpoints should be available on port 8000")
    exit(0)

# Step 4: Backup
backup = MAIN_FILE.with_suffix(".py.before_nojin_integration")
if not backup.exists():
    shutil.copy2(MAIN_FILE, backup)
    print(f"📝 Backup created: {backup.name}")

# Step 5: Add import
if not has_import:
    lines = content.split("\n")
    
    # Find the imports section (look for 'from' or 'import' statements)
    last_import_line = 0
    for i, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            last_import_line = i
    
    # Insert after last import
    import_line = "from services.api_gateway.routers import nojin"
    lines.insert(last_import_line + 1, import_line)
    content = "\n".join(lines)
    print(f"✅ Added import at line {last_import_line + 2}")

# Step 6: Add router registration
if not has_registration:
    lines = content.split("\n")
    
    # Find app = FastAPI(...) or the last include_router call
    app_line = -1
    last_router_line = -1
    
    for i, line in enumerate(lines):
        if "= FastAPI(" in line:
            app_line = i
        if "include_router" in line:
            last_router_line = i
    
    # Decide where to insert
    if last_router_line >= 0:
        # Insert after the last router registration
        insert_pos = last_router_line + 1
        print(f"📍 Inserting after line {insert_pos} (last router registration)")
    elif app_line >= 0:
        # Insert after app creation (skip the FastAPI constructor lines)
        insert_pos = app_line + 1
        # Skip multi-line FastAPI constructor
        while insert_pos < len(lines):
            if ")" in lines[insert_pos - 1] and not lines[insert_pos - 1].strip().endswith(","):
                break
            insert_pos += 1
        print(f"📍 Inserting after line {insert_pos} (after app creation)")
    else:
        # Append at end
        insert_pos = len(lines)
        print(f"📍 Inserting at end of file")
    
    # Build registration block
    registration = [
        "",
        "# ═══════════════════════════════════════════════════════════════",
        "# Nojin Biofertilizer Router - Scientific soil restoration",
        "# ═══════════════════════════════════════════════════════════════",
        "app.include_router(nojin.router)",
    ]
    
    # Insert
    for j, line in enumerate(reversed(registration)):
        lines.insert(insert_pos, line)
    
    content = "\n".join(lines)
    print(f"✅ Added router registration")

# Step 7: Write back
MAIN_FILE.write_text(content, encoding="utf-8")
print(f"✅ Updated: {MAIN_FILE.relative_to(PROJECT_ROOT)}")

# Step 8: Verify syntax
print("\n🔍 Verifying syntax...")
try:
    compile(content, str(MAIN_FILE), "exec")
    print("✅ Syntax valid")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    print("💡 Restoring backup...")
    shutil.copy2(backup, MAIN_FILE)
    exit(1)

# Step 9: Test import
print("\n🔍 Testing import...")
import subprocess
import sys
result = subprocess.run(
    [sys.executable, "-c",
     f"import sys; sys.path.insert(0, r'{PROJECT_ROOT}'); "
     "from services.api_gateway.routers import nojin; "
     "print(f'✅ Router import OK - {len(nojin.router.routes)} routes')"],
    cwd=PROJECT_ROOT,
    capture_output=True,
    text=True,
    timeout=30,
)

print(result.stdout.strip())
if result.returncode != 0:
    print("❌ Import failed:")
    print(result.stderr[:1000])
    print("💡 Restoring backup...")
    shutil.copy2(backup, MAIN_FILE)
    exit(1)

print("\n" + "=" * 80)
print("✅ NOJIN ROUTER INTEGRATED INTO MAIN APPLICATION")
print("=" * 80)
print("""
🎯 What was done:
  1. Fixed classify endpoint bug
  2. Added Nojin router import to services/api_gateway/main.py
  3. Registered router with app.include_router()
  4. Verified syntax and imports

🚀 Next Steps:

1. Stop the current server (Ctrl+C)

2. Restart the unified server:
   uvicorn services.api_gateway.main:app --reload --host 127.0.0.1 --port 8000

3. Test all endpoints on port 8000:
   python test_nojin_api_8001.py
   
   (Change BASE_URL to http://localhost:8000 in the test file)

4. Or visit Swagger UI:
   http://localhost:8000/docs

🌟 All endpoints (Nojin + existing) now on ONE server!
""")