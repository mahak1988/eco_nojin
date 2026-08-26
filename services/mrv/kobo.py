"""KoboToolbox client (free tier) — fetch field measurement submissions.

Env: KOBO_TOKEN (API token) + KOBO_FORM_ID (survey form id).
Without credentials the client returns an honest `requires_credentials`
status — never fabricated field data.
"""

import os
from typing import Any, Dict, List

import aiohttp


async def fetch_kobo_submissions(
    form_id: str | None = None,
    token: str | None = None,
    base_url: str = "https://kc.kobotoolbox.org",
) -> Dict[str, Any]:
    """Fetch latest survey submissions from KoboToolbox (free tier)."""
    token = token or os.getenv("KOBO_TOKEN", "")
    form_id = form_id or os.getenv("KOBO_FORM_ID", "")

    if not token or not form_id:
        return {
            "status": "requires_credentials",
            "data_source": "kobotoolbox",
            "hint": "KOBO_TOKEN and KOBO_FORM_ID are empty — add free KoboToolbox credentials to .env",
            "submissions": [],
        }

    url = f"{base_url}/api/v1/data/{form_id}?format=json&fields=[\"_id\",\"_submission_time\",\"soc_sample_t_ha\"]"
    headers = {"Authorization": f"Token {token}"}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return {
                        "status": "error",
                        "data_source": "kobotoolbox",
                        "error": f"HTTP {resp.status}",
                        "submissions": [],
                    }
                data: List[Any] = await resp.json()
                parsed = []
                for row in data or []:
                    soc = row.get("soc_sample_t_ha")
                    if soc is not None:
                        parsed.append(
                            {
                                "submission_id": row.get("_id"),
                                "time": row.get("_submission_time"),
                                "soc_t_ha": float(soc),
                            }
                        )
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


def average_measured_soc(payload: Dict[str, Any]) -> float | None:
    """Mean of measured SOC samples; None when nothing usable."""
    subs = payload.get("submissions") or []
    if not subs:
        return None
    vals = [s["soc_t_ha"] for s in subs if s.get("soc_t_ha") is not None]
    return round(sum(vals) / len(vals), 3) if vals else None
