"""Internal automation agent — one daily cycle against the platform API.

Usage:
    python scripts/agent_daily.py                       # default: local gateway
    python scripts/agent_daily.py --base http://host:8000 --farms 1,2,3
Env:
    AGENT_TOKEN  (default: dev-agent-token)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='http://127.0.0.1:8000')
    ap.add_argument('--farms', default='')
    ap.add_argument('--token', default=os.environ.get('AGENT_TOKEN', 'dev-agent-token'))
    args = ap.parse_args()

    farms = [int(x) for x in args.farms.split(',') if x.strip().isdigit()]
    body = json.dumps({'watch_farms': farms, 'store_digest': True}).encode()
    req = urllib.request.Request(
        f'{args.base}/api/v1/automation/agent-run',
        data=body,
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Agent-Token': args.token},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:  # noqa: BLE001
        print(f'[agent] FAILED: {exc}', file=sys.stderr)
        return 1

    print(f"[agent] started {data.get('started_at')} finished {data.get('finished_at')}")
    for step in data.get('steps', []):
        print(f"  - {step['step']}: {step['status']} ({step['detail']})")
    v = data.get('validation') or {}
    if v:
        print(f"  validation: {v.get('passed')}/{v.get('total')} checks passed")
    print(f"  digest stored: {data.get('stored')}")
    return 0 if all(s['status'] != 'error' for s in data.get('steps', [])) else 2


if __name__ == '__main__':
    raise SystemExit(main())
