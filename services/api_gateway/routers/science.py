"""Science / open-academic layer router (Phase 9 kickoff)."""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/science", tags=["science"])


@router.get("/citations")
def model_citation(slug: str):
    """Citation suggestion for a registered model (offline, honest)."""
    from fastapi import HTTPException

    from services.science.citations import citation_for_model

    try:
        return citation_for_model(slug)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/citations/index")
def citation_index_endpoint():
    """All models with citation suggestions (offline, honest)."""
    from services.science.citations import citation_index

    return citation_index()


@router.get("/datasets")
def dataset_catalog():
    """Honest catalog of platform datasets (no fake availability)."""
    from services.science.datasets import dataset_catalog

    return dataset_catalog()


@router.get("/model-cards")
def model_cards_endpoint(slug: str | None = None):
    """Model cards: limitations, validity domain, fidelity (Phase 9 star 11)."""
    from services.models.registry import MODEL_CARDS, get_model

    if slug:
        card = MODEL_CARDS.get(slug)
        if card is None:
            raise HTTPException(status_code=404, detail=f"no model card for {slug}")
        model = get_model(slug)
        return {"slug": slug, "card": card, "model": model.__dict__ if model else None}
    out = []
    for slug in MODEL_CARDS:
        model = get_model(slug)
        out.append({
            "slug": slug,
            "card": MODEL_CARDS[slug],
            "fidelity": model.fidelity if model else None,
            "domain": model.domain if model else None,
        })
    return {"count": len(out), "cards": out}


@router.get("/agrovoc")
def agrovoc_search_endpoint(q: str = "", limit: int = 8):
    """Offline AGROVOC knowledge-graph search (Phase 9 star 12)."""
    from services.science.agrovoc import agrovoc_search, agrovoc_stats

    q = (q or "").strip()
    if not q:
        return {"count": 0, "results": [], "stats": agrovoc_stats()}
    return {"count": None, "results": agrovoc_search(q, limit), "stats": agrovoc_stats()}


@router.get("/zenodo/status")
def zenodo_status_endpoint():
    """Zenodo DOI capability status (honest: not_configured without token)."""
    from services.science.zenodo import default_zenodo_client

    return default_zenodo_client().status()


@router.post("/datasets/{slug}/doi")
def request_dataset_doi(slug: str):
    """Request a Zenodo DOI for a dataset (write path; requires ZENODO_TOKEN).

    Returns honest 501 (not_configured) when the token is missing.
    """
    from fastapi import HTTPException as _HTTP

    from services.science.datasets import dataset_catalog
    from services.science.zenodo import ZenodoError, default_zenodo_client

    ds = next((d for d in dataset_catalog()["datasets"] if d.get("slug") == slug), None)
    if ds is None:
        raise _HTTP(status_code=404, detail=f"unknown dataset {slug}")
    client = default_zenodo_client()
    if not client.configured:
        raise _HTTP(
            status_code=501,
            detail={
                "status": "not_configured",
                "message": "ZENODO_TOKEN تنظیم نشده است؛ DOI واقعی صادر نمی‌شود.",
            },
        )
    try:
        meta = {
            "metadata": {
                "title": ds.get("name_en") or ds.get("slug"),
                "description": (ds.get("description") or "")[:1000],
                "upload_type": "dataset",
                "creators": [{"name": "Eco Nojin Platform"}],
                "license": "cc-by-4.0",
                "access_right": "open",
                "prereserve_doi": True,
            }
        }
        dep = client.create_deposition(meta)
        return {"status": "deposition_created", "deposition_id": dep.get("id"), "links": dep.get("links")}
    except ZenodoError as exc:
        raise _HTTP(status_code=502, detail=str(exc)) from exc
