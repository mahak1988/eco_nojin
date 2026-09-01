"""Self-healing watchdog (Phase 10, star 13).

Monitors an HTTP health endpoint, tracks latency/error trend (EMA), and on
failure invokes a configurable restart command (Human-in-the-loop: it only
logs the restart action unless --auto-restart is passed).

Usage:
  python scripts/watchdog.py --url http://os.environ.get('HOST', '127.0.0.1'):8000/api/v1/health \
      --interval 30 --auto-restart --restart-cmd "taskkill /F /IM uvicorn.exe"

Pure logic lives in analyze_samples() so it is unit-testable.
"""

import os

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from typing import Dict, List, Optional

log = logging.getLogger("watchdog")


def analyze_samples(
    latencies_ms: List[float],
    errors: List[bool],
    fail_threshold_ms: float = 2000.0,
    error_ratio_threshold: float = 0.5,
    ema_alpha: float = 0.3,
) -> Dict[str, object]:
    """Predictive health analysis from recent probe samples.

    Returns status: ok | degraded | failing, plus EMA latency and error ratio.
    """
    if not latencies_ms or not errors or len(latencies_ms) != len(errors):
        raise ValueError("latencies_ms and errors must be non-empty and same length")

    ema: float = float(latencies_ms[0])
    for lat in latencies_ms[1:]:
        ema = ema_alpha * lat + (1.0 - ema_alpha) * ema

    error_ratio = sum(1 for e in errors if e) / len(errors)

    if error_ratio >= error_ratio_threshold or ema >= fail_threshold_ms:
        status = "failing"
    elif error_ratio > 0.0 or ema >= fail_threshold_ms * 0.6:
        status = "degraded"
    else:
        status = "ok"
    return {
        "status": status,
        "ema_latency_ms": round(ema, 1),
        "error_ratio": round(error_ratio, 3),
        "samples": len(latencies_ms),
    }


def probe(url: str, timeout: float = 5.0) -> tuple[float, bool]:
    """Measure one probe: returns (latency_ms, is_error)."""
    import time as _t

    import httpx

    start = _t.monotonic()
    try:
        resp = httpx.get(url, timeout=timeout)
        ok = resp.status_code < 500
        latency = (_t.monotonic() - start) * 1000.0
        if resp.status_code >= 400 and resp.status_code < 500:
            latency = latency * 0.5  # client errors are not service failures
        return latency, not ok
    except Exception:
        return timeout * 1000.0, True


def run_watchdog(args: argparse.Namespace) -> int:
    """Main loop; returns process exit code."""
    latencies: List[float] = []
    errors: List[bool] = []
    consecutive_failures = 0
    restarts = 0

    while True:
        lat, err = probe(args.url, args.timeout)
        latencies.append(lat)
        errors.append(err)
        if len(latencies) > args.window:
            latencies = latencies[-args.window :]
            errors = errors[-args.window :]

        analysis = analyze_samples(latencies, errors, args.fail_threshold_ms, args.error_ratio)
        log.info("probe=%sms err=%s -> %s", round(lat, 1), err, analysis["status"])

        if err:
            consecutive_failures += 1
        else:
            consecutive_failures = 0

        if consecutive_failures >= args.fail_count:
            log.warning("FAILING: %d consecutive failures", consecutive_failures)
            if args.auto_restart and args.restart_cmd:
                log.warning("RESTARTING service: %s", args.restart_cmd)
                try:
                    subprocess.run(args.restart_cmd, shell=True, timeout=60)
                    restarts += 1
                    log.warning("restart #%d issued", restarts)
                except Exception as exc:  # pragma: no cover
                    log.error("restart failed: %s", exc)
            elif not args.auto_restart:
                log.warning("ACTION REQUIRED (human-in-the-loop): restart the service")
            consecutive_failures = 0

        time.sleep(args.interval)


def main() -> int:  # pragma: no cover
    parser = argparse.ArgumentParser(description="Eco Nojin self-healing watchdog")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/health")
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--fail-threshold-ms", type=float, default=2000.0)
    parser.add_argument("--error-ratio", type=float, default=0.5)
    parser.add_argument("--fail-count", type=int, default=3)
    parser.add_argument("--auto-restart", action="store_true")
    parser.add_argument("--restart-cmd", default="")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return run_watchdog(parser.parse_args())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
