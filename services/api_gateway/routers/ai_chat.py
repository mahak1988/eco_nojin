"""AI Chat router with streaming and voice support."""

import asyncio
import contextlib
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.config import get_db
from services.auth.models import AIConversation, Farm, SatelliteAnalysis, SoilAnalysis, User
from services.api_gateway.auth import get_current_user, require_user

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


# ============================================================================
# Knowledge Base (multi-language)
# ============================================================================
KB = {
    "soil": {
        "keywords": [
            "soil",
            "ph",
            "nitrogen",
            "phosphorus",
            "potassium",
            "npk",
            "fertility",
            "خاک",
            "فسفر",
            "نیتروژن",
        ],
        "en": """**Soil Health Guidelines:**

- **pH**: 6.0-7.5 optimal. Apply lime if <5.5, sulfur if >7.5
- **Nitrogen**: 30-80 ppm. Use legume cover crops if low
- **Phosphorus**: 20-60 ppm. Add bone meal or rock phosphate
- **Potassium**: 100-300 ppm. Use potassium sulfate
- **Organic matter**: 2-5% target. Add compost, practice no-till

Would you like me to analyze your specific soil data?""",
        "fa": """**راهنمای سلامت خاک:**

- **pH**: ۶.۰-۷.۵ بهینه. اگر کمتر از ۵.۵ آهک، اگر بیشتر از ۷.۵ گوگرد اضافه کنید
- **نیتروژن**: ۳۰-۸۰ ppm. در صورت کمبود از گیاهان پوششی حبوبات استفاده کنید
- **فسفر**: ۲۰-۶۰ ppm. پودر استخوان یا فسفات سنگ اضافه کنید
- **پتاسیم**: ۱۰۰-۳۰۰ ppm. از سولفات پتاسیم استفاده کنید
- **ماده آلی**: هدف ۲-۵٪. کمپوست اضافه کنید، بدون شخم

آیا می‌خواهید داده‌های خاص خاک خود را تحلیل کنم؟""",
    },
    "water": {
        "keywords": ["water", "irrigation", "drought", "et0", "آب", "آبیاری", "خشکسالی"],
        "en": """**Water Management:**

- **Irrigation**: Use ET0 as baseline with crop coefficient (Kc)
- **Drip irrigation**: 90% efficiency vs 60% for flood
- **Mulching**: Reduces evaporation by 30-50%
- **Rainwater harvesting**: Capture up to 80% of runoff
- **Deficit irrigation**: During non-critical growth stages""",
        "fa": """**مدیریت آب:**

- **آبیاری**: از ET0 با ضریب محصول (Kc) استفاده کنید
- **آبیاری قطره‌ای**: ۹۰٪ کارایی در برابر ۶۰٪ غرقابی
- **مالچ پاشی**: تبخیر را ۳۰-۵۰٪ کاهش می‌دهد
- **جمع‌آوری آب باران**: تا ۸۰٪ از رواناب را ذخیره کنید
- **آبیاری کمبود**: در مراحل غیرحساس رشد""",
    },
    "climate": {
        "keywords": ["climate", "ssp", "scenario", "temperature", "اقلیم", "سناریو", "دما"],
        "en": """**IPCC Scenarios (by 2100):**

- **SSP1-2.6** (Best): +1.8°C, -5% precipitation
- **SSP2-4.5** (Moderate): +2.7°C, -10% precipitation
- **SSP3-7.0** (Bad): +3.6°C, -15% precipitation
- **SSP5-8.5** (Worst): +4.4°C, -20% precipitation

**Adaptation**: Drought-tolerant varieties, water harvesting, adjusted planting dates""",
        "fa": """**سناریوهای IPCC (تا ۲۱۰۰):**

- **SSP1-2.6** (بهترین): +۱.۸°C، -۵٪ بارش
- **SSP2-4.5** (متوسط): +۲.۷°C، -۱۰٪ بارش
- **SSP3-7.0** (بد): +۳.۶°C، -۱۵٪ بارش
- **SSP5-8.5** (بدترین): +۴.۴°C، -۲۰٪ بارش

**سازگاری**: ارقام مقاوم به خشکسالی، جمع‌آوری آب، تنظیم تاریخ کاشت""",
    },
    "erosion": {
        "keywords": ["erosion", "rusle", "conservation", "فرسایش", "حفاظت"],
        "en": """**Erosion Management (RUSLE):**

- **Low** (<5 t/ha/yr): Acceptable, maintain practices
- **Moderate** (5-15): Monitor, plan conservation
- **High** (15-30): Implement contour farming, terracing
- **Very High** (>30): Urgent - cover crops, no-till

**Key practices**: Contour farming (50% reduction), terracing (slopes >10%), cover crops (C-factor 0.1-0.2)""",
        "fa": """**مدیریت فرسایش (RUSLE):**

- **پایین** (<۵ تن/هکتار/سال): قابل قبول
- **متوسط** (۵-۱۵): نظارت و برنامه‌ریزی
- **بالا** (۱۵-۳۰): کشت کنتور، تراس‌بندی
- **بسیار بالا** (>۳۰): فوری - گیاهان پوششی، بدون شخم

**شیوه‌های کلیدی**: کشت کنتور (۵۰٪ کاهش)، تراس‌بندی (شیب >۱۰٪)""",
    },
    "carbon": {
        "keywords": ["carbon", "credit", "sequestration", "کربن", "اعتبار", "ترسیب"],
        "en": """**Carbon Credits:**

**Sequestration rates:**
- Afforestation: 5-15 tCO2/ha/yr
- Soil carbon: 0.5-2 tCO2/ha/yr
- Biochar: 2-5 tCO2/ha (permanent)

**Workflow**: Register -> Monitor -> Verify -> Issue credits -> Trade
**Market prices**: $5-100/credit (voluntary to compliance)""",
        "fa": """**اعتبارات کربن:**

**نرخ‌های ترسیب:**
- جنگل‌کاری: ۵-۱۵ تن CO2/هکتار/سال
- کربن خاک: ۰.۵-۲ تن CO2/هکتار/سال
- بیوچار: ۲-۵ تن CO2/هکتار (دائمی)

**گردش کار**: ثبت -> نظارت -> تأیید -> صدور اعتبار -> تجارت
**قیمت‌های بازار**: ۵-۱۰۰ دلار/اعتبار""",
    },
}

DEFAULT_RESPONSES = {
    "en": "I can help you with **soil health**, **water management**, **climate scenarios**, **erosion control**, and **carbon credits**. What would you like to know?",
    "fa": "من می‌توانم در مورد **سلامت خاک**، **مدیریت آب**، **سناریوهای اقلیمی**، **کنترل فرسایش** و **اعتبارات کربن** به شما کمک کنم. چه می‌خواهید بدانید؟",
}


def match_topic(question: str, language: str) -> tuple:
    """Find best matching topic and return response."""
    q = question.lower()
    scores = {}
    for topic, data in KB.items():
        score = sum(1 for kw in data["keywords"] if kw.lower() in q)
        if score > 0:
            scores[topic] = score

    if scores:
        best = max(scores, key=scores.get)
        response = KB[best].get(language, KB[best]["en"])
        return response, [best], 0.85
    return DEFAULT_RESPONSES.get(language, DEFAULT_RESPONSES["en"]), [], 0.3


def build_farm_context(farm_id: int, db: Session) -> str:
    """Build context string from farm's recent analyses."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        return ""

    context_lines = []
    context_lines.append(
        f"\n**Your farm: {farm.name}** ({farm.area_hectares} ha, {farm.soil_type or 'unknown'} soil)"
    )

    # Recent soil analysis
    soil = (
        db.query(SoilAnalysis)
        .filter(SoilAnalysis.farm_id == farm_id)
        .order_by(SoilAnalysis.analyzed_at.desc())
        .first()
    )
    if soil:
        context_lines.append(
            f"- Last soil: pH {soil.ph}, health score {soil.health_score}, {soil.texture}"
        )

    # Recent satellite
    sat = (
        db.query(SatelliteAnalysis)
        .filter(SatelliteAnalysis.farm_id == farm_id)
        .order_by(SatelliteAnalysis.analyzed_at.desc())
        .first()
    )
    if sat:
        ndvi_status = "healthy" if sat.ndvi > 0.5 else "stressed"
        context_lines.append(f"- Latest NDVI: {sat.ndvi:.2f} ({ndvi_status})")

    if len(context_lines) > 1:
        return "\n".join(context_lines)
    return ""


# ============================================================================
# Models
# ============================================================================
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    language: str = "en"
    farm_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    confidence: float
    saved_id: int | None = None
    farm_context: str | None = None


# ============================================================================
# Endpoints
# ============================================================================
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Chat with AI (non-streaming)."""
    answer, sources, confidence = match_topic(req.question, req.language)

    farm_context = ""
    if req.farm_id:
        farm_context = build_farm_context(req.farm_id, db)
        if farm_context:
            answer = farm_context + "\n\n" + answer

    # Save
    conv = AIConversation(
        user_id=user.id,
        question=req.question,
        answer=answer,
        language=req.language,
        sources=sources,
        confidence=confidence,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return ChatResponse(
        answer=answer,
        sources=sources,
        confidence=confidence,
        saved_id=conv.id,
        farm_context=farm_context if farm_context else None,
    )


@router.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db), user: User = Depends(require_user)):
    """Get chat history."""
    convs = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == user.id)
        .order_by(AIConversation.asked_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "count": len(convs),
        "conversations": [
            {
                "id": c.id,
                "question": c.question,
                "answer": c.answer,
                "language": c.language,
                "confidence": c.confidence,
                "asked_at": c.asked_at.isoformat() if c.asked_at else None,
            }
            for c in convs
        ],
    }


@router.post("/stream")
async def stream_chat(
    req: ChatRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Stream AI response word by word."""
    answer, sources, confidence = match_topic(req.question, req.language)

    if req.farm_id:
        farm_context = build_farm_context(req.farm_id, db)
        if farm_context:
            answer = farm_context + "\n\n" + answer

    async def generate():
        words = answer.split()
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield f"data: {json.dumps({'type': 'token', 'content': token, 'progress': (i + 1) / len(words)})}\n\n"
            await asyncio.sleep(0.03)

        # Save
        if user:
            conv = AIConversation(
                user_id=user.id,
                question=req.question,
                answer=answer,
                language=req.language,
                sources=sources,
                confidence=confidence,
            )
            db.add(conv)
            db.commit()

        yield f"data: {json.dumps({'type': 'complete', 'sources': sources, 'confidence': confidence})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/voice/tts")
async def text_to_speech(req: ChatRequest):
    """Generate speech from text (returns audio URL)."""
    return {
        "text": req.question,
        "language": req.language,
        "use_browser_tts": True,
    }


# ============================================================================
# WebSocket Streaming
# ============================================================================
@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    """WebSocket streaming chat."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            question = data.get("question", "")
            language = data.get("language", "en")

            answer, sources, confidence = match_topic(question, language)
            words = answer.split()

            for i, word in enumerate(words):
                await websocket.send_json(
                    {
                        "type": "token",
                        "content": word + " ",
                        "progress": (i + 1) / len(words),
                    }
                )
                await asyncio.sleep(0.03)

            await websocket.send_json(
                {
                    "type": "complete",
                    "sources": sources,
                    "confidence": confidence,
                }
            )
    except WebSocketDisconnect:
        pass
    except Exception as e:
        with contextlib.suppress(BaseException):
            await websocket.send_json({"type": "error", "content": str(e)})
