"""Advisory Agent — Combines RAG, Drought Analysis, and Scenario for farmer advice."""

from __future__ import annotations

from typing import Any

from services.ai.unified_rag import get_rag
from services.analysis.drought_agent import get_drought_agent
from services.analysis.scenario_agent import get_scenario_agent
from services.ai.llm_router import get_router


class AdvisoryAgent:
    """Main agent for farmer advisory: answers questions, runs analysis, gives advice."""

    def __init__(self):
        self.rag = get_rag()
        self.drought_agent = get_drought_agent()
        self.llm_router = get_router()

    async def process_question(
        self,
        question: str,
        lat: float | None = None,
        lon: float | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Process a farmer question with optional location context."""
        
        # Detect intent
        intent = self._detect_intent(question)

        if intent == "drought" and lat is not None and lon is not None:
            # Run drought analysis
            analysis = await self.drought_agent.analyze(lat, lon)
            # Get RAG context for drought advice
            rag_result = await self.rag.answer(
                f"داستان خشکسالی و راهکارهای مقابله با آن در کشاورزی {analysis.get('summary', '')}",
                language=language,
            )
            return {
                "type": "drought_analysis",
                "analysis": analysis,
                "advice": rag_result["answer"],
                "sources": rag_result["sources"],
                "language": language or rag_result["language"],
            }

        elif intent == "scenario" and lat is not None and lon is not None:
            # Run scenario
            scenario_agent = get_scenario_agent(lat, lon)
            # Parse scenario parameters from question
            params = self._parse_scenario_params(question)
            scenario = await scenario_agent.run_scenario(**params)
            # Get advice
            rag_result = await self.rag.answer(
                f"سناریوی تغییر اقلیم: بارش {params.get('precip_change_pct', 0)}% تغییر می‌کند. توصیه‌های کشت؟",
                language=language,
            )
            return {
                "type": "scenario_analysis",
                "scenario": scenario,
                "advice": rag_result["answer"],
                "sources": rag_result["sources"],
            }

        else:
            # General advisory - use RAG
            result = await self.rag.answer(question, language=language)
            return {
                "type": "general_advice",
                "answer": result["answer"],
                "sources": result["sources"],
                "confidence": result["confidence"],
                "language": result["language"],
            }

    def _detect_intent(self, question: str) -> str:
        """Simple intent detection."""
        q = question.lower()
        drought_keywords = ["خشکسالی", "دریاچه", "آب", "بارش", "کم‌آبی", "spi", "spei", "درو", "index", "شاخص"]
        scenario_keywords = ["اگر", "چه می‌شود", "سناریو", "تغییر", "آینده", "پیش‌بینی", "what if", "scenario"]
        
        # Check scenario first (more specific)
        if any(k in q for k in scenario_keywords):
            return "scenario"
        if any(k in q for k in drought_keywords):
            return "drought"
        return "general"

    def _parse_scenario_params(self, question: str) -> dict[str, float]:
        """Extract scenario parameters from question."""
        import re
        params = {"precip_change_pct": 0.0, "temp_change_c": 0.0}
        
        # Look for percentage changes
        precip_match = re.search(r"بارش\s*(\+?-?\d+)\s*%", question)
        if precip_match:
            params["precip_change_pct"] = float(precip_match.group(1))
        
        temp_match = re.search(r"دما\s*(\+?-?\d+)\s*[°C]", question)
        if temp_match:
            params["temp_change_c"] = float(temp_match.group(1))
            
        return params

    async def get_drought_report(
        self,
        lat: float,
        lon: float,
        months: int = 6,
        language: str = "fa",
    ) -> dict[str, Any]:
        """Generate comprehensive drought report."""
        analysis = await self.drought_agent.analyze(lat, lon, months)
        
        # Get contextual advice from RAG
        rag_result = await self.rag.answer(
            f"راهکارهای مقابله با خشکسالی در منطقه با SPI {analysis.get('spi', {}).get('3month', {}).get('value', 'N/A')}",
            language=language,
        )

        return {
            "location": {"lat": lat, "lon": lon},
            "analysis": analysis,
            "recommendations": rag_result["answer"],
            "sources": rag_result["sources"],
            "language": language,
        }

    async def close(self):
        await self.rag.close()
        await self.drought_agent.close()


# Singleton
_advisory_agent: AdvisoryAgent | None = None


def get_advisory_agent() -> AdvisoryAgent:
    global _advisory_agent
    if _advisory_agent is None:
        _advisory_agent = AdvisoryAgent()
    return _advisory_agent