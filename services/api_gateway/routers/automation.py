"""Internal automation agent API — the hook n8n / cron calls.

POST /api/v1/automation/agent-run
    Runs one agent cycle: formula verification, database health and a
    read-only satellite-data status per requested farm. The digest is
    stored in the central hub under the agent user key (audit trail).

Auth: shared token header ``X-Agent-Token`` compared to ``AGENT_TOKEN``
(env; defaults to ``dev-agent-token`` in development).
"""
from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from database.hub import hub
from database.models import ModelRun

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])

AGENT_USER_KEY = 'automation-agent'
AGENT_TOKEN = os.environ.get('AGENT_TOKEN', 'dev-agent-token')


class AgentRunRequest(BaseModel):
    """What one agent cycle should do."""

    watch_farms: list[int] = Field(default_factory=list, description='Farm ids to report satellite status for')
    store_digest: bool = Field(default=True, description='Store the digest in the central hub')


def _require_token(token: str | None) -> None:
    if not token or token != AGENT_TOKEN:
        raise HTTPException(status_code=401, detail='invalid or missing X-Agent-Token')


@router.get('/health')
def automation_health() -> dict[str, Any]:
    return {'status': 'ok', 'agent': AGENT_USER_KEY, 'token_configured': AGENT_TOKEN != 'dev-agent-token'}


@router.post('/agent-run')
def agent_run(
    payload: AgentRunRequest,
    x_agent_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Execute one internal-agent cycle and return its digest."""
    _require_token(x_agent_token)

    digest: dict[str, Any] = {
        'agent': AGENT_USER_KEY,
        'started_at': datetime.now(UTC).isoformat(),
        'steps': [],
    }

    # 1) formula verification
    try:
        from services.validation.formula_checks import run_all
        report = run_all()
        digest['validation'] = {k: report[k] for k in ('total', 'passed', 'failed', 'pass_rate')}
        digest['steps'].append({
            'step': 'validation',
            'status': 'ok' if report['failed'] == 0 else 'attention',
            'detail': f"{report['passed']}/{report['total']} checks passed",
        })
    except Exception as exc:  # noqa: BLE001 - recorded, never silent
        digest['validation'] = {'error': str(exc)}
        digest['steps'].append({'step': 'validation', 'status': 'error', 'detail': str(exc)})

    # 2) database health
    try:
        engine = hub.get_sqlalchemy_engine()
        with engine.connect() as conn:
            journal = (
                conn.exec_driver_sql('PRAGMA journal_mode').scalar()
                if engine.dialect.name == 'sqlite'
                else None
            )
            runs = int(conn.exec_driver_sql('SELECT COUNT(*) FROM hydroma_model_runs').scalar() or 0)
        digest['database'] = {'journal_mode': journal, 'model_runs': runs}
        digest['steps'].append({'step': 'database', 'status': 'ok', 'detail': f'{runs} model runs stored'})
    except Exception as exc:  # noqa: BLE001
        digest['database'] = {'error': str(exc)}
        digest['steps'].append({'step': 'database', 'status': 'error', 'detail': str(exc)})

    # 3) satellite data status per watched farm (read-only)
    if payload.watch_farms:
        status: list[dict[str, Any]] = []
        try:
            with hub.get_session() as session:
                for farm_id in payload.watch_farms:
                    row = session.execute(
                        text(
                            'SELECT COUNT(*), MAX(analyzed_at) FROM satellite_analyses WHERE CAST(farm_id AS TEXT) = :fid'
                        ),
                        {'fid': str(farm_id)},
                    ).all()
                    count, last = (row[0] if row else (0, None))
                    status.append({
                        'farm_id': farm_id,
                        'analyses': int(count or 0),
                        'last_analysis': str(last) if last else None,
                    })
            digest['satellite_status'] = status
            digest['steps'].append({
                'step': 'satellite_status',
                'status': 'ok',
                'detail': f'{len(status)} farms queried',
            })
        except Exception as exc:  # noqa: BLE001
            digest['satellite_status'] = {'error': str(exc)}
            digest['steps'].append({'step': 'satellite_status', 'status': 'error', 'detail': str(exc)})

    digest['finished_at'] = datetime.now(UTC).isoformat()

    # 4) persist the digest in the central hub (auditable history)
    if payload.store_digest:
        try:
            with hub.get_session() as session:
                session.add(ModelRun(
                    user_key=AGENT_USER_KEY,
                    model_id='agent-digest',
                    title='automation agent digest',
                    inputs={'watch_farms': payload.watch_farms},
                    outputs=digest,
                    shared=False,
                ))
                session.commit()
            digest['stored'] = True
        except Exception as exc:  # noqa: BLE001
            digest['stored'] = False
            digest['store_error'] = str(exc)

    return digest
