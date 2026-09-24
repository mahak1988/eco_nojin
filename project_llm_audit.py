# project_llm_audit.py
"""
اسکریپت تحلیل نیاز پروژه به مدل‌های ابری و رایگان
قابل اجرا در هر محیطی که Python نصب باشد
"""

import json
import os
import platform
from datetime import datetime


class ProjectLLMAudit:
    """تحلیل‌گر نیاز پروژه به مدل‌های زبانی"""
    
    # سطوح مدل بر اساس پیچیدگی
    TIERS = {
        "micro": {
            "title": "محلی / رایگان",
            "models": ["Ollama + Qwen2.5:7B", "Ollama + Gemma 3:2B", "Llama 3.3 70B (Groq)"],
            "suitable_for": ["پاسخ‌های ساده", "دسته‌بندی", "خلاصه‌سازی کوتاه", "تشخیص زبان"],
            "cost": "$0",
            "latency": "کم تا متوسط"
        },
        "small": {
            "title": "ابر رایگان",
            "models": ["OpenRouter Free Models", "Groq (Llama 3.3)", "Google AI Studio (Gemini Flash)"],
            "suitable_for": ["چت‌بات پشتیبانی", "پاسخ به سوالات متداول", "تحلیل متن ساده"],
            "cost": "$0 (با محدودیت نرخ)",
            "latency": "کم"
        },
        "medium": {
            "title": "ابر رایگان پیشرفته یا ارزان",
            "models": ["DeepSeek V3", "Mistral Large (Free)", "GLM-4-Flash", "Gemini 2.5 Flash"],
            "suitable_for": ["تحلیل داده", "RAG", "ایجنت‌های داخلی", "تولید محتوا"],
            "cost": "$0 - $5/ماه",
            "latency": "متوسط"
        },
        "large": {
            "title": "ابر پیشرفته (نیاز به بسته پولی)",
            "models": ["GPT-4o", "Claude Sonnet 4", "GigaChat Pro/Max", "Gemini 2.5 Pro"],
            "suitable_for": ["تحلیل عمیق", "استدلال پیچیده", "کدتولید", "پروژه‌های تجاری پرترافیک"],
            "cost": "$10 - $200+/ماه",
            "latency": "متوسط تا بالا"
        }
    }
    
    # محدودیت‌های رایج سرویس‌های رایگان
    FREE_LIMITS = {
        "OpenRouter": {"rpm": 20, "rpd": 50, "note": "با $10 شارژ، ۱۰۰۰ درخواست در روز"},
        "Groq": {"rpm": 30, "rpd": 1000, "note": "به ازای هر مدل، روزانه ۱۰۰۰ درخواست"},
        "Google AI Studio": {"rpm": 15, "rpd": 1500, "note": "مدل‌های Flash رایگان هستند"},
        "Mistral": {"rpm": 1, "tpm": 500000, "note": "حدود ۱ میلیارد توکن در ماه"},
        "Cloudflare Workers AI": {"rpd": 10000, "note": "۱۰۰۰۰ نورون در روز"},
        "DeepSeek": {"rpm": 10, "note": "۵۰۰ میلیون توکن هدیه اولیه"}
    }
    
    def __init__(self):
        self.report = {
            "project_name": "LLM Project Audit",
            "timestamp": datetime.now().isoformat(),
            "platform": self._detect_platform(),
            "analysis": {},
            "recommendations": []
        }
    
    def _detect_platform(self):
        """تشخیص پلتفرم سرور"""
        system = platform.system()
        info = {"os": system, "python": platform.python_version()}
        
        if os.path.exists('/.dockerenv'):
            info["containerized"] = True
        else:
            info["containerized"] = False
            
        # تشخیص منابع سیستم
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            info["disk_free_gb"] = round(free / (2**30), 2)
        except Exception:
            info["disk_free_gb"] = "unknown"
            
        return info
    
    def analyze_project(self, 
                         daily_requests: int,
                         avg_input_tokens: int,
                         avg_output_tokens: int,
                         privacy_required: bool = False,
                         needs_rag: bool = False,
                         needs_agent: bool = False,
                         is_commercial: bool = True):
        """
        تحلیل نیاز پروژه به مدل‌های ابری
        
        Args:
            daily_requests: تعداد درخواست روزانه
            avg_input_tokens: میانگین توکن ورودی هر درخواست
            avg_output_tokens: میانگین توکن خروجی هر درخواست
            privacy_required: آیا داده‌ها باید خصوصی بمانند؟
            needs_rag: آیا نیاز به RAG (بازیابی دانش) دارد؟
            needs_agent: آیا نیاز به ایجنت خودکار دارد؟
            is_commercial: آیا استفاده تجاری است؟
        """
        analysis = {}
        
        # محاسبه حجم توکن روزانه
        daily_tokens = daily_requests * (avg_input_tokens + avg_output_tokens)
        monthly_tokens = daily_tokens * 30
        
        analysis["daily_requests"] = daily_requests
        analysis["daily_tokens"] = daily_tokens
        analysis["monthly_tokens"] = monthly_tokens
        analysis["monthly_tokens_m"] = round(monthly_tokens / 1_000_000, 2)
        
        # تعیین سطح پیچیدگی
        tier = self._determine_tier(
            daily_requests, monthly_tokens, 
            privacy_required, needs_rag, needs_agent, is_commercial
        )
        
        analysis["required_tier"] = tier
        analysis["tier_info"] = self.TIERS[tier]
        
        # بررسی امکان استفاده از رایگان
        free_viability = self._check_free_viability(daily_requests, tier)
        analysis["free_tier_viable"] = free_viability
        
        # توصیه‌های عملی
        recommendations = self._generate_recommendations(
            tier, free_viability, needs_rag, needs_agent, privacy_required, is_commercial
        )
        
        self.report["analysis"] = analysis
        self.report["recommendations"] = recommendations
        
        return self.report
    
    def _determine_tier(self, daily_requests, monthly_tokens, 
                         privacy, rag, agent, commercial):
        """تعیین سطح مدل مورد نیاز"""
        score = 0
        
        # امتیاز بر اساس حجم
        if daily_requests > 5000:
            score += 3
        elif daily_requests > 1000:
            score += 2
        elif daily_requests > 100:
            score += 1
        
        # امتیاز بر اساس توکن
        if monthly_tokens > 50_000_000:
            score += 3
        elif monthly_tokens > 10_000_000:
            score += 2
        elif monthly_tokens > 1_000_000:
            score += 1
        
        # امتیاز بر اساس قابلیت‌ها
        if rag:
            score += 1
        if agent:
            score += 1
        if privacy:
            score += 1
        
        # تعیین سطح
        if score >= 7:
            return "large"
        elif score >= 4:
            return "medium"
        elif score >= 2:
            return "small"
        else:
            return "micro"
    
    def _check_free_viability(self, daily_requests, tier):
        """بررسی امکان استفاده از سرویس‌های رایگان"""
        # ظرفیت کل تقریبی سرویس‌های رایگان (با ترکیب چند سرویس)
        total_free_capacity = 50 + 1000 + 1500 + 10000  # OpenRouter + Groq + Gemini + Cloudflare
        total_free_capacity += 100  # سرویس‌های اضافی
        
        viable = daily_requests <= total_free_capacity
        
        result = {
            "viable": viable,
            "max_free_daily": total_free_capacity,
            "your_daily": daily_requests,
            "utilization": round(daily_requests / total_free_capacity * 100, 1)
        }
        
        # اگر تجاری نیست یا حجم کم است، رایگان کافی است
        if tier in ["micro", "small"] and viable:
            result["verdict"] = "✅ استفاده از سرویس‌های رایگان کاملاً کافی است"
        elif viable:
            result["verdict"] = "⚠️ رایگان کافی است اما نیاز به ترکیب چند سرویس و مدیریت نرخ دارید"
        else:
            result["verdict"] = "❌ حجم شما از ظرفیت رایگان فراتر می‌رود؛ نیاز به بسته پولی دارید"
        
        return result
    
    def _generate_recommendations(self, tier, free_viability, 
                                   rag, agent, privacy, commercial):
        """تولید توصیه‌های عملی"""
        recs = []
        
        # توصیه بر اساس سطح
        if tier == "micro":
            recs.append({
                "priority": "بالا",
                "title": "استفاده از Ollama برای مدل محلی",
                "action": "ollama pull qwen2.5:7b",
                "reason": "مدل محلی رایگان، حریم خصوصی کامل، برای حجم کم عالی است"
            })
        elif tier == "small":
            recs.append({
                "priority": "بالا",
                "title": "استفاده از OpenRouter یا Groq",
                "action": "ثبت‌نام در openrouter.ai و دریافت API Key رایگان",
                "reason": "۲۰+ مدل رایگان با یک کلید، بدون نیاز به کارت اعتباری"
            })
        elif tier == "medium":
            recs.append({
                "priority": "بالا",
                "title": "ترکیب DeepSeek + OpenRouter + Gemini",
                "action": "از DeepSeek برای تحلیل، از OpenRouter برای چت، از Gemini Flash برای حجم بالا",
                "reason": "هر سه رایگان یا بسیار ارزان هستند"
            })
        else:
            recs.append({
                "priority": "بالا",
                "title": "نیاز به بسته پولی",
                "action": "با GigaChat یا OpenAI یا Anthropic قرارداد تجاری ببندید",
                "reason": "حجم و پیچیدگی فراتر از ظرفیت رایگان است"
            })
        
        # توصیه RAG
        if rag:
            recs.append({
                "priority": "بالا",
                "title": "پیاده‌سازی RAG با Embedding محلی",
                "action": "pip install langchain-community chromadb",
                "reason": "استفاده از nomic-embed-text یا Qwen3-Embedding-0.6B به صورت محلی و رایگان"
            })
        
        # توصیه ایجنت
        if agent:
            recs.append({
                "priority": "متوسط",
                "title": "استفاده از Qwen3 برای ایجنت",
                "action": "qwen3:14b یا qwen3-coder:32b",
                "reason": "بهترین مدل开源 برای工具调用 و ایجنت به زبان فارسی/چینی"
            })
        
        # توصیه حریم خصوصی
        if privacy:
            recs.append({
                "priority": "بالا",
                "title": "استفاده از Ollama به جای ابر",
                "action": "نصب Ollama روی سرور خودتان",
                "reason": "داده‌ها از سرور شما خارج نمی‌شوند"
            })
        
        # توصیه تجاری
        if commercial and tier in ["medium", "large"]:
            recs.append({
                "priority": "بالا",
                "title": "بررسی شرایط استفاده تجاری",
                "action": "سرویس‌های رایگان را بررسی کنید",
                "reason": "برخی سرویس‌ها (Google AI Studio، Cohere) استفاده تجاری را ممنوع کرده‌اند"
            })
        
        # توصیه‌های عمومی
        recs.append({
            "priority": "متوسط",
            "title": "پیاده‌سازی Failover بین سرویس‌ها",
            "action": "از freeflow-llm یا کتابخانه مشابه برای چرخش کلیدها استفاده کنید",
            "reason": "وقتی یک سرویس به محدودیت خورد، به سرویس دیگر سوئیچ کند"
        })
        
        recs.append({
            "priority": "پایین",
            "title": "مانیتورینگ مصرف توکن",
            "action": "از pytokencalc برای شمارش توکن قبل از ارسال استفاده کنید",
            "reason": "جلوگیری از هدررفت سهمیه رایگان"
        })
        
        return recs
    
    def save_report(self, filename=None):
        """ذخیره گزارش به صورت JSON"""
        if filename is None:
            filename = f"llm_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def print_summary(self):
        """چاپ خلاصه گزارش"""
        a = self.report["analysis"]
        
        print("\n" + "="*60)
        print("📊 گزارش تحلیل نیاز پروژه به مدل‌های زبانی")
        print("="*60)
        
        print(f"\n📅 زمان: {self.report['timestamp'][:19]}")
        print(f"🖥️ پلتفرم: {self.report['platform']['os']}")
        
        print(f"\n📈 آمار درخواست‌ها:")
        print(f"   درخواست روزانه: {a['daily_requests']:,}")
        print(f"   توکن روزانه: {a['daily_tokens']:,}")
        print(f"   توکن ماهانه: {a['monthly_tokens_m']:,} میلیون")
        
        print(f"\n🎯 سطح مورد نیاز: {self.TIERS[a['required_tier']]['title']}")
        print(f"   مدل‌های پیشنهادی: {', '.join(self.TIERS[a['required_tier']]['models'])}")
        print(f"   هزینه تقریبی: {self.TIERS[a['required_tier']]['cost']}")
        
        fv = a["free_tier_viable"]
        print(f"\n💰 امکان استفاده رایگان:")
        print(f"   وضعیت: {fv['verdict']}")
        print(f"   ظرفیت رایگان روزانه: {fv['max_free_daily']:,} درخواست")
        print(f"   استفاده شما: {fv['utilization']}% از ظرفیت رایگان")
        
        print(f"\n🛣️ توصیه‌های عملی:")
        for i, rec in enumerate(self.report["recommendations"], 1):
            print(f"\n   {i}. [{rec['priority']}] {rec['title']}")
            print(f"      ▶ {rec['action']}")
            print(f"      💡 {rec['reason']}")
        
        print("\n" + "="*60)


# ============================================================
# اجرای اسکریپت با پارامترهای پروژه شما
# ============================================================

if __name__ == "__main__":
    audit = ProjectLLMAudit()
    
    # ⬇️ این مقادیر را بر اساس پروژه خود تنظیم کنید ⬇️
    report = audit.analyze_project(
        daily_requests=500,           # تعداد درخواست روزانه
        avg_input_tokens=800,         # میانگین توکن ورودی
        avg_output_tokens=400,        # میانگین توکن خروجی
        privacy_required=False,       # آیا داده‌ها باید خصوصی بمانند؟
        needs_rag=True,               # آیا نیاز به RAG دارید؟
        needs_agent=True,             # آیا نیاز به ایجنت دارید؟
        is_commercial=True            # آیا استفاده تجاری است؟
    )
    
    # چاپ خلاصه
    audit.print_summary()
    
    # ذخیره گزارش
    filename = audit.save_report()
    print(f"\n📄 گزارش تفصیلی ذخیره شد: {filename}")