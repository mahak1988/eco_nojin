"""Natural-language advice — RAG→NLG.

Default provider is a free, deterministic Persian NLG that turns retrieved
knowledge + live chain metrics into natural recommendations. When the user
provides their own LLM key (AI_LLM_KEY / AI_LLM_URL), an OpenAI-compatible
adapter is used instead. Honesty: the default is NOT an LLM; it is labeled
`provider: local-nlg` so nobody mistakes it for model output.
"""
import os
from typing import Any, Dict, List

from services.ai.rag import index as rag_index

_TOPICS = {
    "بندسار": "ایجاد بندسار (سنگ‌چین/خاکریز در مسیر آبراهه) رواناب سطحی را مهار و نفوذ را چند برابر می‌کند؛ در کنار زهکش فرانسوی برای مناطق نیمه‌خشک بهترین نتیجه را دارد.",
    "رواناب": "کاهش رواناب با بندسار + تراس‌بندی + افزایش ماده آلی خاک (کمپوست/بیوچار)؛ پایش با شاخص‌های ماهواره‌ای و کالیبراسیون SCS-CN روی داده محلی.",
    "خشکسالی": "پایش SPI/SPEI با داده ERA5 انجام می‌شود؛ در خشکسالی ملایم یا شدیدتر، آبیاری قطر‌ه‌ای و مالچ ارگانیک را توصیه می‌کنیم.",
    "کربن": "اعتبار کربن (CCT) پس از ممیزی مستقل صادر می‌شود؛ محاسبه‌ها با روش‌های Verra/Gold Standard و گواهی PDF فارسی.",
    "فرسایش": "فرسایش با RUSLE سنجیده می‌شود؛ پوشش گیاهی (C پایین) و عملیات حفاظتی (P پایین) بیشترین اثر را روی کاهش A دارند.",
    "آبیاری": "برنامه آبیاری با FAO-56 محاسبه می‌شود؛ در اقلیم گرم، آبیاری شبانه تلفات تبخیر را تا ۳۰٪ کاهش می‌دهد.",
}

_DEFAULT = "بر اساس دانش محلی و مستندات پروژه، اجرای زنجیره علمی (خاک، آب، اقلیم، کربن) برای زمین شما توصیه می‌شود تا پاسخ دقیق و عددی بگیرید."


def _llm_advice(question: str, evidence: List[Dict]) -> Dict[str, Any]:
    """OpenAI-compatible adapter (BYO key). Provider name stays honest."""
    import httpx

    key = os.getenv("AI_LLM_KEY", "")
    url = os.getenv("AI_LLM_URL", "https://api.openai.com/v1/chat/completions")
    ctx = "\n".join(f"- [{e['file']}] {e['text']}" for e in evidence)
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": os.getenv("AI_LLM_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": "تو دستیار علمی پلتفرم اکو نوژین (احیای زمین/کشاورزی) هستی. پاسخ کوتاه و کاربردی به فارسی بده و به شواهد استناد کن."},
                {"role": "user", "content": f"زمینه:\n{ctx}\n\nسوال: {question}"},
            ],
            "temperature": 0.3,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return {"provider": "llm:" + os.getenv("AI_LLM_MODEL", "gpt-4o-mini"), "answer": resp.json()["choices"][0]["message"]["content"]}


def advise(question: str, metrics: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Answer with evidence. Uses BYO LLM when configured, local NLG otherwise."""
    evidence = rag_index.search(question, k=3)
    metrics = metrics or {}

    if os.getenv("AI_LLM_KEY"):
        try:
            out = _llm_advice(question, evidence)
            out["evidence"] = evidence
            out["metrics"] = metrics
            return out
        except Exception as exc:
            # honest fallback: never pretend the LLM answered
            return {"provider": "local-nlg", "answer": _DEFAULT, "evidence": evidence, "metrics": metrics,
                    "llm_error": str(exc), "note": "کلید LLM پیکربندی شده بود ولی پاسخ نداد؛ از موتور محلی استفاده شد."}

    # --- deterministic Persian NLG -------------------------------------------
    answer_parts: List[str] = []
    for keyword, sentence in _TOPICS.items():
        if keyword in question:
            answer_parts.append(sentence)
    if not answer_parts:
        answer_parts.append(_DEFAULT)

    if metrics.get("spi") is not None:
        spi = metrics["spi"]
        if spi < -1.5:
            answer_parts.append(f"وضعیت خشکسالی فعلی: SPI={spi} (شدید) — مدیریت اضطراری آب لازم است.")
        elif spi < -1:
            answer_parts.append(f"وضعیت خشکسالی فعلی: SPI={spi} (ملایم تا متوسط) — برنامه صرفه‌جویی توصیه می‌شود.")
        else:
            answer_parts.append(f"وضعیت خشکسالی فعلی: SPI={spi} (نزدیک نرمال).")
    if metrics.get("soil_loss_t_ha_yr") is not None:
        answer_parts.append(f"فرسایش برآوردی: {metrics['soil_loss_t_ha_yr']} تن در هکتار در سال.")

    if evidence:
        refs = " | ".join(f"{e['file']}: {e['title']}" for e in evidence)
        answer_parts.append(f"شواهد: {refs}")

    return {
        "provider": "local-nlg",
        "answer": "\n".join(answer_parts),
        "evidence": evidence,
        "metrics": metrics,
        "note": "پاسخ توسط موتور توصیه محلی (بدون LLM) ساخته شد؛ برای تحلیل عددی دقیق، زنجیره علمی را اجرا کنید. با افزودن AI_LLM_KEY، پاسخ به LLM واقعی ارتقا می‌یابد.",
    }
