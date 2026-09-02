"""Persian response formatters for Telegram messages."""
from __future__ import annotations
import os


from typing import Any

# Risk level translations
RISK_TRANSLATIONS = {
    "CRITICAL": "🔴 بحرانی",
    "HIGH": "🟠 بالا",
    "MEDIUM": "🟡 متوسط",
    "LOW": "🟢 پایین",
    "Very Low": "🟢 بسیار پایین",
    "EXCELLENT": "🏆 عالی",
    "GOOD": "✅ خوب",
    "MODERATE": "⚖️ متوسط",
    "POOR": "⚠️ ضعیف",
}

RECOMMENDATION_ICONS = {
    "Irrigation": "💧",
    "Soil": "🌱",
    "Erosion Control": "🏔️",
    "Carbon": "🌍",
    "Wind Protection": "💨",
    "Soil Conservation": "🌿",
    "Drainage": "🌊",
    "Crop Selection": "🌾",
}


def format_analysis_response(data: dict[str, Any]) -> str:
    """
    Format comprehensive analysis as Persian Telegram message.
    
    Uses Markdown for rich formatting.
    """
    name = data.get("name", "زمین")
    area = data.get("area_ha", 0)
    location = data.get("location", {})
    climate = data.get("climate", {})
    vegetation = data.get("vegetation", {})
    erosion = data.get("erosion", {})
    irrigation = data.get("irrigation", {})
    carbon = data.get("carbon", {})
    risk = data.get("risk_assessment", {})
    recommendations = data.get("recommendations", [])
    performance = data.get("performance", {})

    # Build message
    lines = [
        f"🌾 *تحلیل زمین: {name}*",
        f"📏 مساحت: *{area:.1f}* هکتار",
        f"📍 مختصات: `{location.get('latitude', 0):.4f}, {location.get('longitude', 0):.4f}`",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # Climate section
    if climate:
        koppen = climate.get("koppen_description", climate.get("koppen_class", ""))
        temp = climate.get("temperature", {})
        precip = climate.get("precipitation", {})

        lines.extend([
            "🌡️ *اقلیم (ERA5):*",
            f"  ┣ نوع: {koppen}",
            f"  ┣ میانگین دما: {temp.get('avg_mean_c', 0):.1f}°C",
            f"  ┣ بیشینه: {temp.get('avg_max_c', 0):.1f}°C / کمینه: {temp.get('avg_min_c', 0):.1f}°C",
            f"  ┗ بارش سالانه: {precip.get('annual_mm', 0):.0f} میلی‌متر",
            "",
        ])

    # Vegetation - robust extraction
    if vegetation:
        def get_field(obj, field, default=""):
            if obj is None: return default
            if isinstance(obj, dict): return obj.get(field, default)
            return getattr(obj, field, default)

        health = get_field(vegetation, "vegetation_health", "")
        ndvi = get_field(vegetation, "avg_ndvi", 0.0)
        health_fa = RISK_TRANSLATIONS.get(health.upper(), health) if health else ""
        lines.extend([
            "🌿 *پوشش گیاهی:*",
            f"  ┣ NDVI: *{ndvi:.3f}*",
            f"  ┗ سلامت: {health_fa}",
            "",
        ])

    # Erosion - robust
    if erosion:
        def get_field(obj, field, default=""):
            if obj is None: return default
            if isinstance(obj, dict): return obj.get(field, default)
            return getattr(obj, field, default)

        risk_level = get_field(erosion, "risk_level", "")
        rate = get_field(erosion, "rusle_rate_t_ha_yr", 0.0)
        risk_fa = RISK_TRANSLATIONS.get(risk_level, risk_level) if risk_level else ""
        lines.extend([
            "🏔️ *فرسایش خاک:*",
            f"  ┣ نرخ: {rate:.2f} تن/هکتار/سال",
            f"  ┗ ریسک: {risk_fa}",
            "",
        ])

    # Irrigation
    if irrigation:
        # Handle both old (et0_mm_day) and new (IrrigationAnalysis) formats
        if isinstance(irrigation, dict):
            et0 = irrigation.get("et0_mm_day") or irrigation.get("et0_mm_day", 0)
            annual = irrigation.get("annual_water_need_mm") or irrigation.get("annual_water_need_mm", 0)
            rec = irrigation.get("irrigation_system") or irrigation.get("recommendation", "")

            lines.extend([
                "💧 *آبیاری:*",
                f"  ┣ ET₀ روزانه: {et0:.2f} میلی‌متر",
                f"  ┣ نیاز سالانه: {annual:.0f} میلی‌متر",
                f"  ┗ سیستم پیشنهادی: *{rec}*",
                "",
            ])

    # Carbon - robust
    if carbon:
        def get_field(obj, field, default=""):
            if obj is None: return default
            if isinstance(obj, dict): return obj.get(field, default)
            return getattr(obj, field, default)

        suitability = get_field(carbon, "suitability", "")
        rate = get_field(carbon, "rate_tCO2e_ha_yr", 0.0)
        total = get_field(carbon, "total_potential_tCO2e", 0.0)
        value = get_field(carbon, "annual_value_usd", 0.0)
        suit_fa = RISK_TRANSLATIONS.get(suitability, suitability) if suitability else ""
        lines.extend([
            "🌍 *پتانسیل کربن:*",
            f"  ┣ نرخ: {rate:.2f} tCO₂e/هکتار/سال",
            f"  ┣ کل: *{total:.1f}* tCO₂e",
            f"  ┣ ارزش سالانه: 💰 *${value:.0f}*",
            f"  ┗ وضعیت: {suit_fa}",
            "",
        ])

    # Risk Assessment - robust
    if risk:
        def get_field(obj, field, default=""):
            if obj is None: return default
            if isinstance(obj, dict): return obj.get(field, default)
            return getattr(obj, field, default)

        overall = get_field(risk, "overall_risk", "")
        drought = get_field(risk, "drought", "")
        drought_fa = RISK_TRANSLATIONS.get(drought, drought) if drought else ""
        lines.extend([
            "⚠️ *ارزیابی ریسک:*",
            f"  ┣ ریسک کلی: {overall}",
            f"  ┗ خشکسالی: {drought_fa}",
            "",
        ])

    # Recommendations (top 3)
    if recommendations:
        lines.append("💡 *توصیه‌های اولویت‌دار:*")
        for i, rec in enumerate(recommendations[:3], 1):
            if isinstance(rec, dict):
                category = rec.get("category", "")
                title = rec.get("title", "")
                icon = RECOMMENDATION_ICONS.get(category, "💡")
                priority = rec.get("priority", "")
                priority_icon = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
                lines.append(f"  {i}. {priority_icon} {icon} {title}")
            else:
                lines.append(f"  {i}. {rec}")
        lines.append("")

    # Performance footer
    total_ms = performance.get("total_ms", 0)
    lines.extend([
        "━━━━━━━━━━━━━━━━━━━━",
        f"⚡ زمان پردازش: {total_ms:.0f}ms",
        f"🔗 [گزارش کامل در Swagger]({config_url()})",
    ])

    return "\n".join(lines)


def config_url() -> str:
    """Get Swagger URL."""
    from .config import config
    return f"{config.API_BASE_URL}/docs"


def format_error(message: str) -> str:
    """Format error message."""
    return f"❌ *خطا:*\n{message}"


def format_help() -> str:
    """Format help message."""
    return """🌾 *ربات Eco Nojin*

دستورات موجود:

/start - شروع و راهنما
/analyze `lat lon area` - تحلیل زمین
  مثال: `/analyze 35.6892 51.389 50`
/landscapes - لیست زمین‌های ثبت‌شده
/stats - آمار پلتفرم
/health - بررسی وضعیت API
/help - این راهنما

💡 *نکته:* مختصات جغرافیایی را از Google Maps کپی کنید.

🔗 [مستندات API](http://os.environ.get('HOST', '127.0.0.1'):8000/docs)"""


def format_welcome() -> str:
    """Format welcome message."""
    return """🎉 *به Eco Nojin خوش آمدید!*

من یک دستیار هوشمند برای تحلیل زمین‌های کشاورزی هستم.

برای شروع، مختصات زمین خود را به من بدهید:

📝 *فرمت:*
`/analyze عرض‌جغرافیایی طول‌جغرافیایی مساحت`

🌟 *مثال:*
`/analyze 35.6892 51.389 50`
(تهران، 50 هکتار)

📚 برای راهنمای کامل: /help"""


def format_landscapes_list(landscapes: list) -> str:
    """Format landscapes list."""
    if not landscapes:
        return "📭 هیچ زمینی ثبت نشده است."

    lines = [f"🌾 *زمین‌های ثبت‌شده ({len(landscapes)}):*", ""]

    for i, land in enumerate(landscapes[:10], 1):
        name = land.get("name", "بدون نام")
        area = land.get("area_ha", "?")
        created = land.get("created_at", "")[:10]
        lines.append(f"{i}. *{name}* ({area} ha) - {created}")

    if len(landscapes) > 10:
        lines.append(f"\n... و {len(landscapes) - 10} زمین دیگر")

    return "\n".join(lines)


def format_stats(stats: dict[str, Any]) -> str:
    """Format platform statistics."""
    return f"""📊 *آمار پلتفرم Eco Nojin*

━━━━━━━━━━━━━━━━━━━━
🌾 زمین‌های ثبت‌شده: *{stats.get('total_landscapes', 0)}*
🌍 پروژه‌های کربن: *{stats.get('total_projects', 0)}*
✅ پروژه‌های فعال: *{stats.get('active_projects', 0)}*
━━━━━━━━━━━━━━━━━━━━
🚀 C++ فعال: {'✅' if stats.get('cpp_available') else '❌'}
💾 Supabase: {'✅' if stats.get('supabase_available') else '❌'}"""
