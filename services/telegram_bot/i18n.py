"""
Multilingual support for Telegram Bot.
Languages: Persian (fa), English (en), Arabic (ar), Spanish (es)
"""
from typing import Dict

TRANSLATIONS = {
    "fa": {
        "welcome": "🌱 به اکو نوژین خوش آمدید!\n\nمن دستیار هوشمند کشاورزی شما هستم.\n\nدستورهای موجود:\n/analyze - تحلیل کامل زمین\n/crops - توصیه محصولات\n/calendar - تقویم کاشت\n/carbon - پتانسیل کربن\n/irrigate - برنامه آبیاری\n/erosion - ریسک فرسایش\n/help - راهنما",
        "analyze_usage": "📍 نحوه استفاده:\n\n/analyze <عرض جغرافیایی> <طول جغرافیایی> <مساحت هکتار>\n\nمثال:\n/analyze 35.0 51.0 50",
        "analyzing": "🔬 در حال تحلیل زمین شما...\n\n⏳ لطفاً صبر کنید (۱۰-۳۰ ثانیه)",
        "analysis_complete": "✅ تحلیل کامل شد!",
        "location": "📍 موقعیت",
        "koppen": "🌡️ اقلیم کوپن",
        "best_crops": "🌾 بهترین محصولات",
        "planting_time": "📅 زمان کاشت",
        "irrigation": "💧 آبیاری",
        "erosion_risk": "⚠️ ریسک فرسایش",
        "carbon_potential": "🌱 پتانسیل کربن",
        "carbon_value": "💰 ارزش کربن",
        "error": "❌ خطا رخ داد. لطفاً دوباره تلاش کنید.",
        "invalid_coords": "❌ مختصات نامعتبر. لطفاً از فرمت زیر استفاده کنید:\n/analyze 35.0 51.0 50",
        "soil_health": "🏞️ سلامت خاک",
        "recommendations": "💡 توصیه‌ها",
        "language_set": "✅ زبان به فارسی تغییر یافت",
    },
    "en": {
        "welcome": "🌱 Welcome to Eco Nojin!\n\nI'm your intelligent agricultural assistant.\n\nAvailable commands:\n/analyze - Full land analysis\n/crops - Crop recommendations\n/calendar - Planting calendar\n/carbon - Carbon potential\n/irrigate - Irrigation schedule\n/erosion - Erosion risk\n/help - Guide",
        "analyze_usage": "📍 Usage:\n\n/analyze <latitude> <longitude> <area_ha>\n\nExample:\n/analyze 35.0 51.0 50",
        "analyzing": "🔬 Analyzing your land...\n\n⏳ Please wait (10-30 seconds)",
        "analysis_complete": "✅ Analysis complete!",
        "location": "📍 Location",
        "koppen": "🌡️ Köppen Climate",
        "best_crops": "🌾 Best Crops",
        "planting_time": "📅 Planting Time",
        "irrigation": "💧 Irrigation",
        "erosion_risk": "⚠️ Erosion Risk",
        "carbon_potential": "🌱 Carbon Potential",
        "carbon_value": "💰 Carbon Value",
        "error": "❌ Error occurred. Please try again.",
        "invalid_coords": "❌ Invalid coordinates. Please use:\n/analyze 35.0 51.0 50",
        "soil_health": "🏞️ Soil Health",
        "recommendations": "💡 Recommendations",
        "language_set": "✅ Language set to English",
    },
    "ar": {
        "welcome": "🌱 مرحباً بكم في إيكو نوجين!\n\nأنا مساعدك الزراعي الذكي.\n\nالأوامر المتاحة:\n/analyze - تحليل كامل للأرض\n/crops - توصيات المحاصيل\n/calendar - تقويم الزراعة\n/carbon - إمكانات الكربون\n/irrigate - جدول الري\n/erosion - خطر التعرية\n/help - دليل",
        "analyze_usage": "📍 الاستخدام:\n\n/analyze <خط العرض> <خط الطول> <المساحة هكتار>\n\nمثال:\n/analyze 35.0 51.0 50",
        "analyzing": "🔬 جارٍ تحليل أرضك...\n\n⏳ يرجى الانتظار (10-30 ثانية)",
        "analysis_complete": "✅ اكتمل التحليل!",
        "location": "📍 الموقع",
        "koppen": "🌡️ مناخ كوبن",
        "best_crops": "🌾 أفضل المحاصيل",
        "planting_time": "📅 وقت الزراعة",
        "irrigation": "💧 الري",
        "erosion_risk": "⚠️ خطر التعرية",
        "carbon_potential": "🌱 إمكانات الكربون",
        "carbon_value": "💰 قيمة الكربون",
        "error": "❌ حدث خطأ. يرجى المحاولة مرة أخرى.",
        "invalid_coords": "❌ إحداثيات غير صالحة. يرجى استخدام:\n/analyze 35.0 51.0 50",
        "soil_health": "🏞️ صحة التربة",
        "recommendations": "💡 توصيات",
        "language_set": "✅ تم تعيين اللغة إلى العربية",
    },
    "es": {
        "welcome": "🌱 ¡Bienvenido a Eco Nojin!\n\nSoy tu asistente agrícola inteligente.\n\nComandos disponibles:\n/analyze - Análisis completo del terreno\n/crops - Recomendaciones de cultivos\n/calendar - Calendario de siembra\n/carbon - Potencial de carbono\n/irrigate - Programa de riego\n/erosion - Riesgo de erosión\n/help - Guía",
        "analyze_usage": "📍 Uso:\n\n/analyze <latitud> <longitud> <área_ha>\n\nEjemplo:\n/analyze 35.0 51.0 50",
        "analyzing": "🔬 Analizando tu terreno...\n\n⏳ Por favor espera (10-30 segundos)",
        "analysis_complete": "✅ ¡Análisis completo!",
        "location": "📍 Ubicación",
        "koppen": "🌡️ Clima Köppen",
        "best_crops": "🌾 Mejores Cultivos",
        "planting_time": "📅 Época de Siembra",
        "irrigation": "💧 Riego",
        "erosion_risk": "⚠️ Riesgo de Erosión",
        "carbon_potential": "🌱 Potencial de Carbono",
        "carbon_value": "💰 Valor del Carbono",
        "error": "❌ Ocurrió un error. Por favor inténtalo de nuevo.",
        "invalid_coords": "❌ Coordenadas inválidas. Por favor usa:\n/analyze 35.0 51.0 50",
        "soil_health": "🏞️ Salud del Suelo",
        "recommendations": "💡 Recomendaciones",
        "language_set": "✅ Idioma configurado a Español",
    },
}


def t(lang: str, key: str) -> str:
    """Get translation for a key."""
    lang_data = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return lang_data.get(key, TRANSLATIONS["en"].get(key, key))


def detect_language(text: str) -> str:
    """Simple language detection based on character ranges."""
    # Persian/Arabic characters
    if any('\u0600' <= c <= '\u06FF' for c in text):
        # Distinguish Persian from Arabic
        persian_chars = set('پچژکگی')
        if any(c in persian_chars for c in text):
            return "fa"
        return "ar"
    
    # Spanish characters
    if any(c in text for c in 'áéíóúñ¿¡'):
        return "es"
    
    return "en"
