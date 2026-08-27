"""Self-healing supervisor for the API (Phase 8-C layer 7).

Usage (Render/Railway start command):
    python scripts/run_with_watchdog.py [--port 8011] [--interval 30]

The watchdog polls /health and restarts the worker on failure, so a crash
or hang heals itself without a human.
"""
import argparse
import sys

from services.security.watchdog import HealthWatchdog


def main() -> None:
    parser = argparse.ArgumentParser(description="Eco Nojin self-healing API supervisor")
    parser.add_argument("--port", type=int, default=8011)
    parser.add_argument("--interval", type=float, default=30.0)
    args = parser.parse_args()

    watchdog = HealthWatchdog(
        cmd=[sys.executable, "-m", "uvicorn", "services.api_gateway.main:app",
             "--port", str(args.port), "--host", "0.0.0.0"],
        health_url=f"http://127.0.0.1:{args.port}/health",
    )
    try:
        watchdog.run_forever(check_interval=args.interval)
    except KeyboardInterrupt:
        watchdog.stop()


if __name__ == "__main__":
    main()
