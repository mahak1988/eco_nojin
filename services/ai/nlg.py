"""
services/ai/nlg.py
==================
ماژول Natural Language Generation برای پروژه eco_nojin
اصلاح‌شده: 2026-09-03 01:16:32
"""

from typing import Dict, Any, List, Optional
from . import rag


# ── پایگاه دانش محلی ────────────────────────────────────────────
_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "بندسار": {
        "category": "آبخیزداری",
        "description": (
            "بندسار یک سازهٔ آبخیزداری است که برای کاهش رواناب سطحی، "
            "افزایش نفوذپذیری خاک و حفظ رطوبت در مناطق خشک و نیمه‌خشک "
            "استفاده می‌شود. با کاهش سرعت جریان آب، فرصت نفوذ افزایش می‌یابد."
        ),
        "benefits": ["کاهش رواناب", "افزایش رطوبت خاک", "کنترل فرسایش"],
        "keywords": ["بندسار", "رواناب", "آبخیزداری", "نفوذ", "فرسایش"],
    },
    "بادشکن": {
        "category": "کنترل فرسایش",
        "description": (
            "بادشکن‌های بیولوژیک با کاشت درختان در جهت باد غالب، "
            "سرعت باد را کاهش داده و فرسایش بادی را کنترل می‌کنند."
        ),
        "benefits": ["کاهش فرسایش بادی", "حفاظت از محصولات", "ایجاد میکروکلیما"],
        "keywords": ["بادشکن", "فرسایش", "بادی", "درختکاری"],
    },
    "بیوچار": {
        "category": "اصلاح خاک",
        "description": (
            "بیوچار یک ماده کربنی پایدار است که از پیرولیز زیست‌توده "
            "تولید می‌شود و ظرفیت نگهداری آب خاک را تا ۳۰٪ افزایش می‌دهد."
        ),
        "benefits": ["افزایش ظرفیت نگهداری آب", "بهبود حاصلخیزی", "ترسیب کربن"],
        "keywords": ["بیوچار", "خاک", "کربن", "حاصلخیزی"],
    },
    "آبیاری قطره‌ای": {
        "category": "مدیریت آب",
        "description": (
            "آبیاری قطره‌ای می‌تواند مصرف آب را تا ۶۰٪ نسبت به آبیاری "
            "غرقابی کاهش دهد."
        ),
        "benefits": ["صرفه‌جویی ۶۰٪ آب", "کاهش علف هرز", "بهبود عملکرد"],
        "keywords": ["آبیاری", "قطره‌ای", "آب", "راندمان"],
    },
    "گابیون": {
        "category": "سازه‌های حفاظتی",
        "description": (
            "گابیون یک سازه حفاظتی از سیم و سنگ است که برای کنترل فرسایش "
            "و تثبیت شیب‌ها استفاده می‌شود."
        ),
        "keywords": ["گابیون", "فرسایش", "شیب"],
    },
    "ترانشه": {
        "category": "جذب آب",
        "description": (
            "ترانشه‌های جذب آب سازه‌های خطی هستند که باعث جذب رواناب "
            "و تغذیه سفره آب زیرزمینی می‌شوند."
        ),
        "keywords": ["ترانشه", "جذب", "آب", "نفوذ"],
    },
}


def _extract_keywords(query: str) -> List[str]:
    """استخراج کلمات کلیدی از query"""
    keywords = []
    for key in _KNOWLEDGE_BASE:
        if key in query:
            keywords.append(key)
    return keywords


def advise(query: str, metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    تولید توصیه مبتنی بر شواهد.

    Args:
        query: پرسش یا موضوع کاربر
        metrics: شاخص‌های مرتبط

    Returns:
        Dict شامل: provider, answer, metrics, evidence
    """
    metrics = metrics or {}

    # ۱) جستجو در RAG
    rag_results = []
    try:
        rag_results = rag.search(query, top_k=3)
    except Exception:
        # اگر rag.build() هنوز اجرا نشده، اجرا کن
        try:
            rag.index.build()
            rag_results = rag.search(query, top_k=3)
        except Exception:
            rag_results = []

    # ۲) تطبیق با پایگاه دانش محلی
    matched_topics = _extract_keywords(query)

    # ۳) تولید پاسخ و evidence
    answer_parts: List[str] = []
    evidence: List[Dict[str, Any]] = []

    # افزودن نتایج RAG به evidence
    for i, r in enumerate(rag_results):
        evidence.append({
            "source": r.get("path", "rag"),
            "type": "rag",
            "content": r.get("content", "")[:200],
            "rank": i + 1,
        })
        if i == 0:
            answer_parts.append(r.get("content", ""))

    # افزودن تطبیق‌های پایگاه دانش
    for topic in matched_topics:
        info = _KNOWLEDGE_BASE[topic]
        evidence.append({
            "source": "knowledge_base/" + topic,
            "type": "local_knowledge",
            "content": info["description"],
            "category": info["category"],
        })
        answer_parts.append("**" + topic + "**: " + info["description"])

    # اگر هیچ evidence پیدا نشد، یک evidence پیش‌فرض بساز
    if not evidence:
        evidence.append({
            "source": "default",
            "type": "system",
            "content": "پاسخ عمومی برای: " + query,
        })
        answer_parts.append("در حال تحلیل درخواست شما: " + query)

    # ۴) تطبیق با metrics
    metrics_context = ""
    if metrics:
        if "spi" in metrics and isinstance(metrics["spi"], (int, float)):
            if metrics["spi"] < -0.5:
                metrics_context = "با توجه به شرایط خشکسالی (SPI منفی)، "
                evidence.append({
                    "source": "metrics",
                    "type": "metric_alert",
                    "content": "SPI=" + str(metrics["spi"]) + " - شرایط خشک",
                })

    # ۵) ساخت پاسخ نهایی
    answer = metrics_context + " ".join(answer_parts)
    if not answer:
        answer = "بر اساس دانش موجود، " + query + " نیازمند تحلیل دقیق‌تر است."

    return {
        "provider": "local-nlg",
        "answer": answer,
        "metrics": metrics,
        "evidence": evidence,
        "matched_topics": matched_topics,
    }


def explain(topic: str) -> Dict[str, Any]:
    """توضیح یک موضوع با استفاده از پایگاه دانش"""
    if topic in _KNOWLEDGE_BASE:
        info = _KNOWLEDGE_BASE[topic]
        return {
            "topic": topic,
            "category": info["category"],
            "description": info["description"],
            "benefits": info.get("benefits", []),
            "provider": "local-nlg",
        }
    return {
        "topic": topic,
        "description": "اطلاعاتی درباره " + topic + " در دسترس نیست.",
        "provider": "local-nlg",
    }
