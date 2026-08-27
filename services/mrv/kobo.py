"""KoboToolbox client (free tier) — fetch field measurement submissions.

Supports:
- API v2 (current free service: https://kf.kobotoolbox.org) — assets/{uid}/data
- API v1 (legacy: kc.kobotoolbox.org/api/v1/data/{form_id})

Env: KOBO_TOKEN (API token) + KOBO_FORM_ID (asset uid or numeric form id).
Without credentials the client returns an honest `requires_credentials`
status — never fabricated field data.
"""

import os
from typing import Any

import aiohttp

SOC_FIELD_NAMES = ["soc_t_ha", "soc_sample_t_ha", "soc_t_ha_0_30", "soc_g_kg"]


async def _parse_submissions(raw: list[Any]) -> list[dict[str, Any]]:
    parsed = []
    for row in raw or []:
        soc = None
        for key in SOC_FIELD_NAMES:
            if row.get(key) is not None:
                soc = float(row[key])
                if key == "soc_g_kg":
                    # g/kg bulk-density approximation -> t C/ha (0-30 cm, ~1.3 g/cm3)
                    soc = soc / 10 * 1.3 * 0.3 * 10
                break
        if soc is not None:
            parsed.append(
                {
                    "submission_id": row.get("_id") or row.get("_uuid"),
                    "time": row.get("_submission_time"),
                    "soc_t_ha": round(soc, 3),
                    "lat": float(row["lat"]) if row.get("lat") is not None else None,
                    "lon": float(row["lon"]) if row.get("lon") is not None else None,
                }
            )
    return parsed


async def _request_v2(session: aiohttp.ClientSession, token: str, form_id: str) -> dict[str, Any]:
    url = f"https://kf.kobotoolbox.org/api/v2/assets/{form_id}/data/?format=json&limit=1000"
    headers = {"Authorization": f"Token {token}"}
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return {"error": f"HTTP {resp.status}"}
        data = await resp.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        return {"results": results}


async def _request_v1(session: aiohttp.ClientSession, token: str, form_id: str) -> dict[str, Any]:
    url = f"https://kc.kobotoolbox.org/api/v1/data/{form_id}?format=json"
    headers = {"Authorization": f"Token {token}"}
    async with session.get(url, headers=headers) as resp:
        if resp.status != 200:
            return {"error": f"HTTP {resp.status}"}
        data = await resp.json()
        return {"results": data if isinstance(data, list) else []}


async def fetch_kobo_submissions(
    form_id: str | None = None,
    token: str | None = None,
) -> dict[str, Any]:
    """Fetch latest survey submissions from KoboToolbox (free tier)."""
    token = token or os.getenv("KOBO_TOKEN", "")
    form_id = form_id or os.getenv("KOBO_FORM_ID", "")

    if not token or not form_id:
        return {
            "status": "requires_credentials",
            "data_source": "kobotoolbox",
            "hint": "KOBO_TOKEN and KOBO_FORM_ID are empty — free signup: https://kf.kobotoolbox.org (Settings → API → token)",
            "submissions": [],
        }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            # API v2 first (current free service), v1 as fallback
            payload = await _request_v2(session, token, form_id)
            if "error" in payload:
                payload = await _request_v1(session, token, form_id)
            if "error" in payload:
                return {
                    "status": "error",
                    "data_source": "kobotoolbox",
                    "error": payload["error"],
                    "submissions": [],
                }
            parsed = await _parse_submissions(payload.get("results", []))
            return {
                "status": "ok" if parsed else "no_soc_samples",
                "data_source": "kobotoolbox",
                "count": len(parsed),
                "submissions": parsed,
            }
    except Exception as exc:  # defensive: never crash the caller
        return {
            "status": "error",
            "data_source": "kobotoolbox",
            "error": str(exc),
            "submissions": [],
        }


def average_measured_soc(payload: dict[str, Any]) -> float | None:
    """Mean of measured SOC samples; None when nothing usable."""
    subs = payload.get("submissions") or []
    if not subs:
        return None
    vals = [s["soc_t_ha"] for s in subs if s.get("soc_t_ha") is not None]
    return round(sum(vals) / len(vals), 3) if vals else None
