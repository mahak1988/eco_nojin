"""
Create Gitignore
================
ایجاد فایل .gitignore جامع برای پروژه.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import console

PROJECT_ROOT = Path(__file__).parent.parent.parent

GITIGNORE_CONTENT = r"""# ==============================================================================
# eco_nojin .gitignore
# ==============================================================================

# ------------------------------------------------------------------------------
# Environment & Secrets (هرگز commit نشود)
# ------------------------------------------------------------------------------
.env
.env.local
.env.*.local
!.env.example
!.env.template
secrets/
*.key
*.pem
*.p12
*.pfx

# ------------------------------------------------------------------------------
# Python
# ------------------------------------------------------------------------------
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/
ENV/
env/
.venv

# ------------------------------------------------------------------------------
# Node.js / pnpm
# ------------------------------------------------------------------------------
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
.pnpm-store/

# ------------------------------------------------------------------------------
# Build Outputs
# ------------------------------------------------------------------------------
frontend/dist/
frontend/build/
frontend/.vite/

# ------------------------------------------------------------------------------
# IDE & Editors
# ------------------------------------------------------------------------------
.vscode/
!.vscode/settings.json
!.vscode/extensions.json
.idea/
*.swp
*.swo
*~
.project
.classpath
.settings/
*.sublime-project
*.sublime-workspace

# ------------------------------------------------------------------------------
# OS Files
# ------------------------------------------------------------------------------
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
Desktop.ini

# ------------------------------------------------------------------------------
# Quarantine & Cache (بسیار حجیم)
# ------------------------------------------------------------------------------
_quarantine/
*.bundle
*.pkl

# Satellite cache
data/copernicus_cache/
data/maps/cache/
.satellite_cache/

# ------------------------------------------------------------------------------
# Data Files (برای commit خیلی حجیم‌اند)
# ------------------------------------------------------------------------------
data/raw/
data/processed/
*.tif
*.tiff
*.nc
*.h5
*.hdf

# ------------------------------------------------------------------------------
# C++ Build Outputs
# ------------------------------------------------------------------------------
engine/cpp_core/build2/
*.obj
*.o
*.a
*.lib
*.exe
*.dll
*.so
*.dylib
*.iobj
*.ipdb
*.pdb

# ------------------------------------------------------------------------------
# Logs
# ------------------------------------------------------------------------------
*.log
logs/
reports/
*.log.*

# ------------------------------------------------------------------------------
# Testing & Coverage
# ------------------------------------------------------------------------------
coverage/
.coverage
htmlcov/
.pytest_cache/
.tox/
.nox/

# ------------------------------------------------------------------------------
# Blockchain (secrets)
# ------------------------------------------------------------------------------
contracts/artifacts/
contracts/cache/
contracts/typechain-types/
contracts/.env

# ------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------
*.db
*.sqlite
*.sqlite3

# ------------------------------------------------------------------------------
# Documentation Build
# ------------------------------------------------------------------------------
docs/_build/
docs/.doctrees/

# ------------------------------------------------------------------------------
# Misc
# ------------------------------------------------------------------------------
*.bak
*.tmp
*.temp
.cache/
.parcel-cache/
.turbo/
"""

def create_gitignore() -> bool:
    """ایجاد فایل .gitignore"""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    
    try:
        if gitignore_path.exists():
            console.warning(f".gitignore وجود دارد، بازنویسی می‌شود: {gitignore_path}")
            # پشتیبان
            backup = gitignore_path.with_suffix(".gitignore.backup")
            backup.write_text(gitignore_path.read_text(encoding='utf-8'), encoding='utf-8')
            console.info(f"  پشتیبان: {backup}")
        
        gitignore_path.write_text(GITIGNORE_CONTENT, encoding='utf-8')
        console.success(f"✓ .gitignore ایجاد شد: {gitignore_path}")
        
        # نمایش آمار
        lines = GITIGNORE_CONTENT.count('\n')
        console.info(f"  تعداد خطوط: {lines}")
        
        return True
    except Exception as e:
        console.error(f"خطا در ایجاد .gitignore: {e}")
        return False

def main() -> int:
    console.header("📝 ایجاد .gitignore")
    
    if create_gitignore():
        console.success("\n✨ .gitignore با موفقیت ایجاد شد")
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())