"""
Science citations (Phase 9 kickoff) — honest, offline.

For every registered model we return its canonical reference (from the
model registry) plus a copy-ready citation string. DOI resolution via
Crossref/OpenAlex comes in the full Phase 9 (external API, gated).

Never fabricates: unknown slugs return a clear error.
"""
from __future__ import annotations

from typing import Any, Dict

from services.models.registry import get_model, list_models


def citation_for_model(slug: str) -> Dict[str, Any]:
    """Citation suggestion for a registered model slug."""
    model = get_model(slug)
    if model is None:
        raise ValueError(f"unknown model slug: {slug}")
    fa_name = model.name_fa
    en_name = model.name_en
    ref = model.reference
    citation = (
        f"{fa_name} ({en_name}) — {ref}. "
        "Eco Nojin HyDroMa Engine, مدل کدباز (https://github.com/eco-nojin/hydroma)."
    )
    return {
        "slug": slug,
        "name_fa": fa_name,
        "name_en": en_name,
        "reference": ref,
        "citation": citation,
        "doi": None,
        "note": "DOI از طریق Crossref/OpenAlex در تکمیل فاز ۹ (نیازمند API خارجی)",
    }


def citation_index() -> Dict[str, Any]:
    """All models with citations (for the science dashboard)."""
    items = []
    for m in list_models():
        try:
            items.append(citation_for_model(m["slug"]))
        except ValueError:
            continue
    return {"count": len(items), "items": items}
