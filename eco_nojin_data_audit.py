import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ==========================================
# تنظیمات ممیزی اکوسیستم eco_nojin
# ==========================================
PROJECT_ROOT = Path(__file__).parent.resolve()
REPORT_FILE = PROJECT_ROOT / "eco_nojin_data_audit_report.json"
MAX_CORE_SIZE_MB = 25.0 # محدودیت استراتژیک شما

# فرمت‌های داده‌ای که باید اسکن شوند
DATA_EXTENSIONS = {
    'databases': ['.db', '.sqlite', '.sqlite3'],
    'spatial_raster': ['.tif', '.tiff', '.geotiff', '.nc', '.h5', '.zarr'],
    'spatial_vector': ['.shp', '.geojson', '.gpkg', '.kml'],
    'analytical': ['.parquet', '.feather', '.csv', '.tsv'],
    'documents': ['.xlsx', '.xls', '.json', '.xml']
}

# دایرکتوری‌هایی که باید نادیده گرفته شوند (برای سرعت اسکن)
IGNORE_DIRS = {'.venv', 'node_modules', '.git', '__pycache__', 'build', 'build2', 'dist', '.next'}

class EcoNojinDataAuditor:
    def __init__(self):
        self.audit_results = {
            "audit_date": datetime.now().isoformat(),
            "project_root": str(PROJECT_ROOT),
            "summary": {},
            "data_silos": defaultdict(lambda: {"count": 0, "total_size_mb": 0.0, "files": []}),
            "heavy_files_alert": [],
            "architectural_recommendations": []
        }
        self.total_files = 0
        self.total_size_bytes = 0

    def scan_project(self):
        print(f"🔍 در حال اسکن عمیق اکوسیستم داده‌ای در: {PROJECT_ROOT}")
        print("این عملیات ممکن است چند دقیقه طول بکشد...\n")
        
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # حذف دایرکتوری‌های غیرضروری از پیمایش
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                # بررسی اینکه آیا فایل جزء فرمت‌های داده‌ای است
                category = self._get_category(ext)
                if category:
                    try:
                        size_bytes = file_path.stat().st_size
                        size_mb = size_bytes / (1024 * 1024)
                        
                        self.total_files += 1
                        self.total_size_bytes += size_bytes
                        
                        rel_path = file_path.relative_to(PROJECT_ROOT)
                        
                        self.audit_results["data_silos"][category]["count"] += 1
                        self.audit_results["data_silos"][category]["total_size_mb"] += size_mb
                        self.audit_results["data_silos"][category]["files"].append({
                            "path": str(rel_path),
                            "size_mb": round(size_mb, 3),
                            "extension": ext
                        })
                        
                        # هشدار فایل‌های حجیم (بالای ۲۵ مگابایت)
                        if size_mb > MAX_CORE_SIZE_MB:
                            self.audit_results["heavy_files_alert"].append({
                                "path": str(rel_path),
                                "size_mb": round(size_mb, 2),
                                "risk": "این فایل برای هسته مرجع (Core Reference) بسیار حجیم است و باید به لایه Spatial/Cloud منتقل شود."
                            })
                            
                    except OSError as e:
                        print(f"⚠️ خطا در خواندن متادیتای فایل {file_path}: {e}")

    def _get_category(self, ext):
        for category, extensions in DATA_EXTENSIONS.items():
            if ext in extensions:
                return category
        return None

    def generate_analysis(self):
        print("📊 در حال تولید تحلیل معماری...")
        
        # محاسبه خلاصه
        self.audit_results["summary"] = {
            "total_data_files_found": self.total_files,
            "total_data_volume_mb": round(self.total_size_bytes / (1024 * 1024), 2),
            "categories_breakdown": {
                cat: {
                    "count": data["count"],
                    "total_size_mb": round(data["total_size_mb"], 2)
                } for cat, data in self.audit_results["data_silos"].items()
            }
        }
        
        # تحلیل معماری بر اساس یافته‌ها
        if self.audit_results["data_silos"]["databases"]["count"] > 2:
            self.audit_results["architectural_recommendations"].append(
                "هشدار: تعدد فایل‌های SQLite/DB کشف شد. برای مقیاس‌پذیری، تمام دیتابیس‌های محلی باید در PostgreSQL (لایه تراکنشی) یا DuckDB (لایه تحلیلی) تجمیع شوند."
            )
            
        if self.audit_results["data_silos"]["documents"]["count"] > 10:
             self.audit_results["architectural_recommendations"].append(
                "هشدار: وابستگی به فایل‌های JSON/Excel برای تنظیمات موتورهای علمی (مانند SWAT یا AquaCrop) کشف شد. این فایل‌ها باید به فرمت Parquet تبدیل و از طریق DuckDB کوئری شوند."
            )

    def save_report(self):
        # تبدیل defaultdict به dict برای serialization
        self.audit_results["data_silos"] = dict(self.audit_results["data_silos"])
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.audit_results, f, ensure_ascii=False, indent=4)
            
        self._print_console_summary()

    def _print_console_summary(self):
        print("\n" + "="*70)
        print("📈 گزارش ممیزی اکوسیستم داده‌ای eco_nojin")
        print("="*70)
        print(f"🔹 کل فایل‌های داده‌ای کشف شده: {self.audit_results['summary']['total_data_files_found']}")
        print(f"🔹 حجم کل داده‌های محلی: {self.audit_results['summary']['total_data_volume_mb']} مگابایت")
        print("-" * 70)
        print("📂 توزیع داده‌ها بر اساس سیلوهای اطلاعاتی:")
        for cat, info in self.audit_results['summary']['categories_breakdown'].items():
            print(f"   - {cat:15} | تعداد: {info['count']:4} | حجم: {info['total_size_mb']:8.2f} MB")
        
        print("-" * 70)
        if self.audit_results["heavy_files_alert"]:
            print(f"🚨 هشدار بحرانی: {len(self.audit_results['heavy_files_alert'])} فایل بزرگتر از ۲۵ مگابایت کشف شد:")
            for f in self.audit_results["heavy_files_alert"][:5]: # نمایش ۵ تای اول
                print(f"   ❌ {f['path']} ({f['size_mb']} MB)")
        else:
            print("✅ هیچ فایل تکی بزرگتر از ۲۵ مگابایت در هسته کشف نشد.")
            
        print("="*70)
        print(f"📄 گزارش کامل و دقیق در فایل زیر ذخیره شد:")
        print(f"   {REPORT_FILE}")
        print("="*70 + "\n")

if __name__ == "__main__":
    auditor = EcoNojinDataAuditor()
    auditor.scan_project()
    auditor.generate_analysis()
    auditor.save_report()