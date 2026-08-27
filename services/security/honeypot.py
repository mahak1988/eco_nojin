"""Layer 8 — honeypot traps.

Fake endpoints that real users never call (admin.php, .env, wp-login.php,
legacy token paths). Any hit is almost certainly a scanner/attacker: the IP
is auto-blocked for 15 minutes and the event is recorded.
"""
import threading
import time
from typing import Dict

TRAP_PATHS = [
    "/admin.php",
    "/wp-login.php",
    "/.env",
    "/.git/config",
    "/api/v1/honeypot/token",
    "/api/v1/honeypot/admin",
    "/config.php.bak",
]


class Honeypot:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._blocked: Dict[str, float] = {}
        self.hits: list = []

    def is_trap(self, path: str) -> bool:
        return path in TRAP_PATHS

    def hit(self, ip: str, path: str, user_agent: str) -> None:
        with self._lock:
            self._blocked[ip] = time.time() + 900  # 15 min block
            self.hits.append({
                "ts": time.time(), "ip": ip, "path": path,
                "user_agent": user_agent[:120],
            })

    def is_blocked(self, ip: str) -> bool:
        with self._lock:
            until = self._blocked.get(ip)
            if until is None:
                return False
            if time.time() > until:
                self._blocked.pop(ip, None)
                return False
            return True


honeypot = Honeypot()
