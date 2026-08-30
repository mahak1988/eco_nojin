#!/usr/bin/env python3
"""
اسکریپت اصلاح خطای make_figures در generate_hydroma_docs.py
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
DOCS_SCRIPT = PROJECT_ROOT / "generate_hydroma_docs.py"

def fix_make_figures_call():
    """اصلاح فراخوانی make_figures با افزودن پارامتر sig"""
    print("🔧 اصلاح خطای make_figures...")
    
    if not DOCS_SCRIPT.exists():
        print(f"   ❌ فایل {DOCS_SCRIPT} یافت نشد")
        return False
    
    content = DOCS_SCRIPT.read_text(encoding="utf-8")
    
    # خط معیوب:
    old_line = 'make_figures(*live[:1], live[1], live[2]) if False else make_figures(live[0], live[1], live[2])'
    
    # خط صحیح:
    new_line = 'make_figures(live[0], live[1], live[2], live[3])'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        DOCS_SCRIPT.write_text(content, encoding="utf-8")
        print("   ✅ خط اصلاح شد: make_figures(live[0], live[1], live[2], live[3])")
        return True
    else:
        print("   ⚠️ خط مورد نظر یافت نشد")
        return False

def main():
    print("="*70)
    print("اصلاح خطای make_figures در generate_hydroma_docs.py")
    print("="*70)
    
    success = fix_make_figures_call()
    
    if success:
        print("\n📋 گام بعدی:")
        print("   python generate_hydroma_docs.py")
    print("="*70)

if __name__ == "__main__":
    main()