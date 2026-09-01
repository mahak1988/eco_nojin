"""Layer 7 — self-healing watchdog + intrusion circuit breaker.

- `HealthWatchdog` supervises the uvicorn process: polls /health, restarts
  the worker on repeated failures, and exposes status.
- `circuit_breaker`: after N WAF blocks from an IP inside a window, the IP
  is auto-blocked for a cooldown (self-healing against scanners/brute force).
"""
import logging
import os
import subprocess
import sys
import threading
import time

logger = logging.getLogger("econojin.watchdog")


class CircuitBreaker:
    """Auto-block IPs that trigger >= 5 WAF blocks within 60s (10 min cooldown)."""

    def __init__(self, threshold: int = 5, cooldown: float = 600.0) -> None:
        self.threshold = threshold
        self.cooldown = cooldown
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = {}
        self._blocked: dict[str, float] = {}

    def report_block(self, ip: str) -> bool:
        """Returns True if the IP just crossed the circuit-breaker threshold."""
        with self._lock:
            now = time.time()
            hits = [t for t in self._hits.get(ip, []) if now - t <= 60]
            hits.append(now)
            self._hits[ip] = hits
            if len(hits) >= self.threshold:
                self._blocked[ip] = now + self.cooldown
                self._hits.pop(ip, None)
                logger.warning("circuit breaker tripped for %s", ip)
                return True
            return False

    def is_blocked(self, ip: str) -> bool:
        with self._lock:
            until = self._blocked.get(ip)
            if until is None:
                return False
            if time.time() > until:
                self._blocked.pop(ip, None)
                return False
            return True


circuit_breaker = CircuitBreaker()


class HealthWatchdog:
    """Supervises the API process (production mode)."""

    def __init__(self, cmd: list[str], health_url: str = "http://os.environ.get('HOST', '127.0.0.1'):8011/health") -> None:
        self.cmd = cmd
        self.health_url = health_url
        self.proc: subprocess.Popen | None = None
        self.restarts = 0
        self._stop = False

    def start(self) -> None:
        self.proc = subprocess.Popen(self.cmd, cwd=os.getcwd())

    def stop(self) -> None:
        self._stop = True
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def status(self) -> dict:
        import urllib.request

        alive = self.proc is not None and self.proc.poll() is None
        healthy = False
        if alive:
            try:
                with urllib.request.urlopen(self.health_url, timeout=3) as resp:
                    healthy = resp.status == 200
            except Exception:
                healthy = False
        return {"alive": alive, "healthy": healthy, "restarts": self.restarts}

    def run_forever(self, check_interval: float = 30.0) -> None:
        """Self-healing loop: restart the worker when it dies or fails health."""
        import urllib.request

        logger.info("watchdog started: %s", self.cmd)
        self.start()
        while not self._stop:
            time.sleep(check_interval)
            alive = self.proc is not None and self.proc.poll() is None
            healthy = False
            if alive:
                try:
                    with urllib.request.urlopen(self.health_url, timeout=3) as resp:
                        healthy = resp.status == 200
                except Exception:
                    healthy = False
            if not alive or not healthy:
                logger.warning("worker unhealthy (alive=%s healthy=%s); restarting", alive, healthy)
                self.restarts += 1
                if self.proc:
                    try:
                        self.proc.kill()
                    except Exception:
                        pass
                self.start()


watchdog = HealthWatchdog(
    cmd=[sys.executable, "-m", "uvicorn", "services.api_gateway.main:app", "--port", "8011", "--host", "os.environ.get('HOST', '127.0.0.1')"]
)
