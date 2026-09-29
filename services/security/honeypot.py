"""Layer 8 — honeypot traps.

Fake endpoints that real users never call (admin.php, .env, wp-login.php,
legacy token paths). Any hit is almost certainly a scanner/attacker: the IP
is auto-blocked for 15 minutes and the event is recorded.
"""

import posixpath
import threading
import time
from collections import deque

TRAP_PATHS = [
    "/admin.php",
    "/wp-login.php",
    "/.env",
    "/.git/config",
    "/api/v1/honeypot/token",
    "/api/v1/honeypot/admin",
    "/config.php.bak",
]

_TRAP_SET = set(TRAP_PATHS)
_TRAP_FOLDED = {p.casefold() for p in TRAP_PATHS}

BLOCK_SECONDS = 900  # 15 minutes
MAX_HITS = 1_000
MAX_BLOCKED = 10_000


class Honeypot:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._blocked: dict[str, float] = {}
        # maxlen keeps the trail bounded: a scanner sweeping trap paths at
        # speed, or rotating source addresses, would otherwise grow this list
        # without limit and turn the honeypot into a memory-exhaustion vector
        # against the very process meant to defend the service.
        self.hits: deque[dict[str, object]] = deque(maxlen=MAX_HITS)

    def is_trap(self, path: str) -> bool:
        """Match traps case-insensitively, ignoring a trailing slash and
        dot-segments, so `/ADMIN.PHP`, `/admin.php/` and `/x/../admin.php`
        all land on the trap they were clearly probing for."""
        normalized = posixpath.normpath("/" + path.replace("\\", "/").lstrip("/"))
        normalized = normalized.rstrip("/") or "/"
        if normalized == "/":
            return False
        return normalized in _TRAP_SET or normalized.casefold() in _TRAP_FOLDED

    def hit(self, ip: str, path: str, user_agent: str) -> None:
        with self._lock:
            self._blocked[ip] = time.time() + BLOCK_SECONDS
            self.hits.append(
                {
                    "ts": time.time(),
                    "ip": ip,
                    "path": path,
                    "user_agent": user_agent[:120],
                }
            )
            if len(self._blocked) > MAX_BLOCKED:
                cutoff = time.time() - BLOCK_SECONDS
                expired = [k for k, until in self._blocked.items() if until < cutoff]
                for k in expired:
                    del self._blocked[k]
                while len(self._blocked) > MAX_BLOCKED:
                    self._blocked.pop(next(iter(self._blocked)))

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
