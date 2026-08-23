"""
Register Nojin Router in Existing Main Application
====================================================
Intelligently adds the Nojin router to the existing FastAPI application.

Strategy:
1. Locate the main.py file (services/api_gateway/main.py)
2. Find the app = FastAPI(...) instance
3. Add import for Nojin router
4. Register the router with app.include_router()
5. Ensure router file exists in correct location
6. Verify and test

Run: python register_nojin_router.py
"""

import sys
import shutil
import re
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")

print("=" * 80)
print("🔧 REGISTERING NOJIN ROUTER IN MAIN APP")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Find main.py
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 1: Locating main.py...")

main_candidates = [
    PROJECT_ROOT / "services" / "api_gateway" / "main.py",
    PROJECT_ROOT / "main.py",
    PROJECT_ROOT / "app.py",
    PROJECT_ROOT / "econoJin" / "api.py",
]

# Also search for any file with FastAPI( in it
search_patterns = ["FastAPI(", "app = FastAPI", "app=FastAPI"]
for pattern in search_patterns:
    try:
        result = __import__("subprocess").run(
            ["findstr", "/S", "/M", f"/C:{pattern}", "*.py"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        for file in result.stdout.split("\n"):
            file = file.strip()
            if file and ".venv" not in file and "node_modules" not in file:
                p = PROJECT_ROOT / file
                if p.exists() and p not in main_candidates:
                    main_candidates.append(p)
    except Exception:
        pass

main_file = None
for candidate in main_candidates:
    if candidate.exists():
        main_file = candidate
        print(f"✅ Found main.py at: {main_file.relative_to(PROJECT_ROOT)}")
        break

if not main_file:
    print("❌ Could not find main.py")
    print("\n🔍 Searched:")
    for c in main_candidates[:5]:
        print(f"   • {c}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
# STEP 2: Create router file in correct location
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 2: Ensuring router file exists...")

routers_dir = PROJECT_ROOT / "services" / "api_gateway" / "routers"
routers_dir.mkdir(parents=True, exist_ok=True)

router_file = routers_dir / "nojin.py"

# Check if router file exists
if not router_file.exists():
    print(f"❌ Router file not found at: {router_file.relative_to(PROJECT_ROOT)}")
    print("\n💡 Please create nojin.py with the router code first.")
    print("   See the previous script for the full router code.")
    sys.exit(1)
else:
    size = router_file.stat().st_size
    print(f"✅ Router file exists: {router_file.relative_to(PROJECT_ROOT)} ({size} bytes)")

# Ensure __init__.py exists in routers
init_file = routers_dir / "__init__.py"
if not init_file.exists():
    init_file.write_text('"""API Gateway Routers."""\nfrom . import nojin\n\n__all__ = ["nojin"]\n', encoding="utf-8")
    print(f"✅ Created: {init_file.relative_to(PROJECT_ROOT)}")
else:
    # Ensure nojin is exported
    content = init_file.read_text(encoding="utf-8")
    if "nojin" not in content:
        with open(init_file, "a", encoding="utf-8") as f:
            f.write("\nfrom . import nojin\n")
        print(f"✅ Updated {init_file.name} to export nojin")

# ═══════════════════════════════════════════════════════════════════
# STEP 3: Read main.py and check for existing registration
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 3: Analyzing main.py...")

content = main_file.read_text(encoding="utf-8")

# Check if already registered
has_nojin_import = "nojin" in content.lower() and ("import" in content[:5000] or "routers" in content[:5000])
has_nojin_include = "include_router" in content and "nojin" in content

if has_nojin_import and has_nojin_include:
    print("✅ Nojin router already registered in main.py")
    print("   Nothing to do - server should already work.")
    print("\n🎯 Try accessing: http://localhost:8000/api/nojin/health")
    sys.exit(0)

# Find app variable name
app_match = re.search(r"(\w+)\s*=\s*FastAPI\(", content)
if app_match:
    app_var = app_match.group(1)
    print(f"✅ Found FastAPI app variable: '{app_var}'")
else:
    app_var = "app"
    print(f"⚠️  Could not find app variable, using default: 'app'")

# Find imports section
import_section_end = 0
lines = content.split("\n")
for i, line in enumerate(lines):
    if line.startswith("from ") or line.startswith("import "):
        import_section_end = i + 1
    elif line.strip() and not line.startswith("#") and import_section_end > 0:
        # First non-import, non-comment line after imports
        if not any(line.startswith(p) for p in ["from ", "import ", " "]):
            break

print(f"📍 Import section ends around line {import_section_end}")

# Find where routers are included (or end of file)
router_include_pattern = re.compile(r"app\.include_router\(|app\.mount\(")
last_include_pos = -1
for i, line in enumerate(lines):
    if router_include_pattern.search(line):
        last_include_pos = i

# Find good insertion point
if last_include_pos >= 0:
    # Insert after the last include_router
    insert_pos = last_include_pos + 1
    print(f"📍 Will insert after line {insert_pos} (last router include)")
else:
    # Insert at end of file
    insert_pos = len(lines) - 1
    print(f"📍 Will insert at end of file")

# ═══════════════════════════════════════════════════════════════════
# STEP 4: Backup and modify
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 4: Modifying main.py...")

# Backup
backup = main_file.with_suffix(".py.before_nojin")
if not backup.exists():
    shutil.copy2(main_file, backup)
    print(f"✅ Backup created: {backup.name}")

# Build the new import and registration
import_line = "from services.api_gateway.routers import nojin"
registration_lines = [
    "",
    "# ═══════════════════════════════════════════════════════════════",
    "# Nojin Biofertilizer Router - Scientific soil restoration",
    "# ═══════════════════════════════════════════════════════════════",
    f"{app_var}.include_router(nojin.router)",
    "",
]

# Check if import already exists
if import_line in content:
    print("ℹ️  Import already exists")
    new_content = content
else:
    # Insert import
    lines.insert(import_section_end, import_line)
    new_content = "\n".join(lines)
    print(f"✅ Added import: {import_line}")

# Add registration
if f"{app_var}.include_router(nojin.router)" not in new_content:
    # Find good spot - after existing include_router calls
    lines = new_content.split("\n")
    
    # Find last router registration
    last_router_line = -1
    for i, line in enumerate(lines):
        if "include_router" in line:
            last_router_line = i
    
    if last_router_line >= 0:
        # Insert after last router
        for j, reg_line in enumerate(reversed(registration_lines)):
            lines.insert(last_router_line + 1, reg_line)
    else:
        # Find app creation and insert after it
        app_line = -1
        for i, line in enumerate(lines):
            if f"{app_var} = FastAPI(" in line or "app = FastAPI(" in line:
                app_line = i
                # Find end of FastAPI() constructor
                for j in range(i, min(i + 30, len(lines))):
                    if ")" in lines[j] and ("prefix=" in lines[j] or "title=" in lines[j] or j == i):
                        app_line = j
                        break
        
        if app_line >= 0:
            for reg_line in registration_lines:
                lines.insert(app_line + 1, reg_line)
                app_line += 1
        else:
            # Just append at end
            lines.extend(registration_lines)
    
    new_content = "\n".join(lines)
    print(f"✅ Added router registration")
else:
    print("ℹ️  Registration already exists")

# Write back
main_file.write_text(new_content, encoding="utf-8")
print(f"✅ Updated: {main_file.relative_to(PROJECT_ROOT)}")

# ═══════════════════════════════════════════════════════════════════
# STEP 5: Verify syntax
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 5: Verifying syntax...")

try:
    compile(new_content, str(main_file), "exec")
    print("✅ Syntax valid")
except SyntaxError as e:
    print(f"❌ Syntax error: {e}")
    print("\n💡 Restoring from backup...")
    shutil.copy2(backup, main_file)
    print("✅ Backup restored")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
# STEP 6: Test import
# ═══════════════════════════════════════════════════════════════════

print("\n📋 Step 6: Testing import...")

import subprocess
result = subprocess.run(
    [sys.executable, "-c", 
     f"""
import sys
sys.path.insert(0, r"{PROJECT_ROOT}")

# Test imports
try:
    from services.api_gateway.routers import nojin
    print("✅ Router import successful")
    print(f"   Router prefix: {{nojin.router.prefix}}")
    print(f"   Tags: {{nojin.router.tags}}")
    print(f"   Routes: {{len(nojin.router.routes)}}")
except Exception as e:
    print(f"❌ Import failed: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
     """],
    cwd=PROJECT_ROOT,
    capture_output=True,
    text=True,
    timeout=30,
)

print(result.stdout)
if result.returncode != 0:
    print("❌ Import test failed:")
    print(result.stderr[:1500])
    print("\n💡 Restoring from backup...")
    shutil.copy2(backup, main_file)
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
# FINAL OUTPUT
# ═══════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("✅ NOJIN ROUTER SUCCESSFULLY REGISTERED")
print("=" * 80)
print(f"""
📍 Files Modified:
   • {main_file.relative_to(PROJECT_ROOT)}
   • {backup.name} (backup)

🎯 Next Steps:

1. RESTART the server (Ctrl+C then run again):
   uvicorn services.api_gateway.main:app --reload --host 127.0.0.1 --port 8000

2. TEST the API (in a new terminal):
   python test_nojin_api.py

3. Or visit Swagger UI:
   http://localhost:8000/docs

4. Quick manual test:
   curl http://localhost:8000/api/nojin/health
   curl http://localhost:8000/api/nojin/materials

5. Try the full analysis (POST request via Swagger or curl)

🌟 Endpoints Available (after restart):
   GET  /api/nojin/health
   GET  /api/nojin/statistics
   GET  /api/nojin/materials
   GET  /api/nojin/materials/arid-priority
   GET  /api/nojin/materials/{{code}}
   GET  /api/nojin/soils
   GET  /api/nojin/soils/{{code}}
   POST /api/nojin/classify
   GET  /api/nojin/recipes
   GET  /api/nojin/recipes/{{code}}
   POST /api/nojin/recommend
   POST /api/nojin/optimize
   POST /api/nojin/cost-benefit
   POST /api/nojin/water-savings
   POST /api/nojin/scale
   POST /api/nojin/full-analysis ⭐

🎉 Ready to serve 2.5 billion people in arid regions!
""")