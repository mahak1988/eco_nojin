#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
آنالیز سختگیرانه پروژه هیدروما
بررسی واقعیت پروژه از روی فایل‌های موجود
بدون هیچ حدس و تفسیر قبلی
============================================================================
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

ROOT = Path(__file__).resolve().parent


class ProjectAnalyzer:
    """آنالیزور سختگیرانه پروژه"""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.report = {
            "analysis_time": datetime.now().isoformat(),
            "project_path": str(root_path),
            "structure": {},
            "knowledge_base": {},
            "data_files": {},
            "integration": {},
            "cpp_files": {},
            "python_files": {},
            "issues": [],
            "missing": [],
        }
    
    def analyze_directory_structure(self):
        """تحلیل ساختار دایرکتوری‌ها"""
        print("\n📁 تحلیل ساختار دایرکتوری‌ها...")
        
        dir_count = 0
        file_count = 0
        file_types = Counter()
        
        for root, dirs, files in os.walk(self.root):
            # نادیده گرفتن دایرکتوری‌های غیرضروری
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', '.git', '.venv', 'venv']]
            
            for dir_name in dirs:
                dir_count += 1
            
            for file_name in files:
                file_count += 1
                ext = Path(file_name).suffix
                file_types[ext] += 1
        
        self.report["structure"] = {
            "total_directories": dir_count,
            "total_files": file_count,
            "file_types": dict(file_types),
        }
        
        print(f"   📁 تعداد دایرکتوری‌ها: {dir_count}")
        print(f"   📄 تعداد فایل‌ها: {file_count}")
        print(f"   📊 انواع فایل‌ها:")
        for ext, count in file_types.most_common(20):
            print(f"      {ext or 'بدون پسوند'}: {count}")
        
        return dir_count, file_count
    
    def analyze_knowledge_base(self):
        """تحلیل پایگاه دانش"""
        print("\n📚 تحلیل پایگاه دانش...")
        
        kb_files = list(self.root.rglob("knowledge_base*.json"))
        
        if not kb_files:
            self.report["knowledge_base"] = {"status": "NOT_FOUND"}
            self.report["missing"].append("پایگاه دانش یافت نشد")
            print("   ❌ پایگاه دانش یافت نشد")
            return
        
        print(f"   ✅ تعداد فایل‌های پایگاه دانش: {len(kb_files)}")
        
        for kb_file in kb_files:
            print(f"\n   📄 {kb_file.name}:")
            
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    kb_data = json.load(f)
                
                # شمارش گرایش‌ها
                if isinstance(kb_data, dict):
                    # حذف کلیدهای غیرگرایش
                    specialties = {k: v for k, v in kb_data.items() 
                                  if k.startswith(('AGR', 'CLI', 'WAS', 'GOV', 'FOR', 'ENV', 'TEC', 'ECO', 'TOU', 'GEO', 'LIV'))}
                    
                    specialty_count = len(specialties)
                    indicator_count = 0
                    formula_count = 0
                    
                    for spec_id, spec_data in specialties.items():
                        if isinstance(spec_data, dict):
                            indicators = spec_data.get("indicators", [])
                            indicator_count += len(indicators)
                            
                            formulas = spec_data.get("formulas", {})
                            formula_count += len(formulas)
                    
                    print(f"      📊 تعداد گرایش‌ها: {specialty_count}")
                    print(f"      📊 تعداد شاخص‌ها: {indicator_count}")
                    print(f"      📊 تعداد فرمول‌ها: {formula_count}")
                    
                    self.report["knowledge_base"][kb_file.name] = {
                        "path": str(kb_file),
                        "specialty_count": specialty_count,
                        "indicator_count": indicator_count,
                        "formula_count": formula_count,
                    }
                    
                    # بررسی مشکلات
                    if specialty_count < 330:
                        self.report["issues"].append(f"تعداد گرایش‌ها ({specialty_count}) کمتر از ۳۳۰ است")
                    
                else:
                    self.report["knowledge_base"][kb_file.name] = {
                        "path": str(kb_file),
                        "status": "INVALID_FORMAT",
                    }
                    self.report["issues"].append(f"فرمت نامعتبر در {kb_file.name}")
            
            except json.JSONDecodeError as e:
                self.report["knowledge_base"][kb_file.name] = {
                    "path": str(kb_file),
                    "status": "JSON_ERROR",
                    "error": str(e),
                }
                self.report["issues"].append(f"خطای JSON در {kb_file.name}")
            except Exception as e:
                self.report["knowledge_base"][kb_file.name] = {
                    "path": str(kb_file),
                    "status": "ERROR",
                    "error": str(e),
                }
                self.report["issues"].append(f"خطا در {kb_file.name}")
    
    def analyze_data_files(self):
        """تحلیل فایل‌های داده"""
        print("\n💾 تحلیل فایل‌های داده...")
        
        data_patterns = [
            "*.json",
            "*.csv",
            "*.xlsx",
            "*.db",
            "*.sqlite",
        ]
        
        data_files = []
        for pattern in data_patterns:
            data_files.extend(self.root.rglob(pattern))
        
        # فیلتر کردن فایل‌های واقعی داده (نه اسکریپت‌ها)
        data_files = [f for f in data_files if f.stat().st_size > 1000]  # بزرگتر از ۱ کیلوبایت
        
        print(f"   📊 تعداد فایل‌های داده: {len(data_files)}")
        
        for data_file in data_files[:20]:  # فقط ۲۰ فایل اول
            size = data_file.stat().st_size
            print(f"      📄 {data_file.name}: {size:,} bytes")
            
            self.report["data_files"][data_file.name] = {
                "path": str(data_file),
                "size_bytes": size,
            }
        
        if len(data_files) == 0:
            self.report["missing"].append("هیچ فایل داده‌ای یافت نشد")
            print("   ❌ هیچ فایل داده‌ای یافت نشد")
    
    def analyze_python_files(self):
        """تحلیل فایل‌های پایتون"""
        print("\n🐍 تحلیل فایل‌های پایتون...")
        
        py_files = list(self.root.rglob("*.py"))
        py_files = [f for f in py_files if 'venv' not in str(f) and '.venv' not in str(f)]
        
        print(f"   📊 تعداد فایل‌های پایتون: {len(py_files)}")
        
        # شمارش خطوط کد
        total_lines = 0
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                    total_lines += lines
            except:
                pass
        
        print(f"   📊 تعداد کل خطوط کد: {total_lines:,}")
        
        self.report["python_files"] = {
            "count": len(py_files),
            "total_lines": total_lines,
        }
        
        if len(py_files) == 0:
            self.report["missing"].append("هیچ فایل پایتونی یافت نشد")
            print("   ❌ هیچ فایل پایتونی یافت نشد")
    
    def analyze_cpp_files(self):
        """تحلیل فایل‌های C++"""
        print("\n⚙️ تحلیل فایل‌های C++...")
        
        cpp_patterns = ["*.cpp", "*.h", "*.hpp", "*.cc", "*.cxx"]
        cpp_files = []
        
        for pattern in cpp_patterns:
            cpp_files.extend(self.root.rglob(pattern))
        
        print(f"   📊 تعداد فایل‌های C++: {len(cpp_files)}")
        
        if len(cpp_files) == 0:
            self.report["missing"].append("هیچ فایل C++ یافت نشد")
            print("   ❌ هیچ فایل C++ یافت نشد")
            self.report["cpp_files"] = {"status": "NOT_FOUND"}
        else:
            for cpp_file in cpp_files:
                print(f"      📄 {cpp_file.name}")
            
            self.report["cpp_files"] = {
                "count": len(cpp_files),
                "files": [str(f) for f in cpp_files],
            }
    
    def analyze_integration_files(self):
        """تحلیل فایل‌های ادغام"""
        print("\n🔗 تحلیل فایل‌های ادغام...")
        
        integration_patterns = [
            "*integration*.json",
            "*integration*.py",
            "*benchmark*.json",
            "*benchmark*.py",
        ]
        
        integration_files = []
        for pattern in integration_patterns:
            integration_files.extend(self.root.rglob(pattern))
        
        print(f"   📊 تعداد فایل‌های ادغام: {len(integration_files)}")
        
        for int_file in integration_files[:10]:  # فقط ۱۰ فایل اول
            print(f"      📄 {int_file.name}")
            
            self.report["integration"][int_file.name] = {
                "path": str(int_file),
            }
        
        if len(integration_files) == 0:
            self.report["missing"].append("هیچ فایل ادغامی یافت نشد")
            print("   ❌ هیچ فایل ادغامی یافت نشد")
    
    def generate_report(self):
        """تولید گزارش نهایی"""
        print("\n" + "=" * 80)
        print("📊 گزارش نهایی آنالیز پروژه")
        print("=" * 80)
        
        # خلاصه ساختار
        structure = self.report.get("structure", {})
        print(f"\n📁 ساختار پروژه:")
        print(f"   دایرکتوری‌ها: {structure.get('total_directories', 0)}")
        print(f"   فایل‌ها: {structure.get('total_files', 0)}")
        
        # خلاصه پایگاه دانش
        kb = self.report.get("knowledge_base", {})
        if kb and "NOT_FOUND" not in str(kb):
            total_specialties = sum(v.get("specialty_count", 0) for v in kb.values() if isinstance(v, dict))
            total_indicators = sum(v.get("indicator_count", 0) for v in kb.values() if isinstance(v, dict))
            print(f"\n📚 پایگاه دانش:")
            print(f"   گرایش‌ها: {total_specialties}")
            print(f"   شاخص‌ها: {total_indicators}")
        
        # مشکلات
        issues = self.report.get("issues", [])
        missing = self.report.get("missing", [])
        
        if issues:
            print(f"\n⚠️ مشکلات شناسایی‌شده ({len(issues)}):")
            for issue in issues:
                print(f"   ❌ {issue}")
        
        if missing:
            print(f"\n❌ موارد گم‌شده ({len(missing)}):")
            for item in missing:
                print(f"   ❌ {item}")
        
        # ذخیره گزارش
        report_file = self.root / "docs" / "hydroma" / "project_analysis_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 گزارش ذخیره شد: {report_file}")
        
        return self.report


def main():
    """تابع اصلی"""
    print("=" * 80)
    print("🔬 آنالیز سختگیرانه پروژه هیدروما")
    print("=" * 80)
    
    # ایجاد آنالیزور
    analyzer = ProjectAnalyzer(ROOT)
    
    # اجرای آنالیزها
    analyzer.analyze_directory_structure()
    analyzer.analyze_knowledge_base()
    analyzer.analyze_data_files()
    analyzer.analyze_python_files()
    analyzer.analyze_cpp_files()
    analyzer.analyze_integration_files()
    
    # تولید گزارش نهایی
    report = analyzer.generate_report()
    
    print("\n" + "=" * 80)
    print("✅ آنالیز کامل شد")
    print("=" * 80)


if __name__ == "__main__":
    main()