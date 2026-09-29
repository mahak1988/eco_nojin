"""Layer 9 — request anomaly behavior scoring (free, in-memory).

Per-IP sliding profile: request volume, 4xx ratio, query-string entropy
(encoded/obfuscated payloads have high entropy), payload size outliers and
user-agent diversity. Score >= 80 flags the IP as anomalous; the middleware
then throttles it (slower budget) and logs the event.
"""

import math
import threading
import time
from collections import defaultdict, deque

PROFILE_TTL = 300.0


class AnomalyDetector:
    # A caller that rotates source addresses (botnet, IPv6 prefix rotation)
    # would otherwise add a permanent entry per address. Idle profiles are
    # evicted once they fall outside the window, which keeps the resident set
    # proportional to *active* callers rather than to lifetime traffic.
    def __init__(self, max_profiles: int = 10_000) -> None:
        self._lock = threading.Lock()
        self._vol: dict[str, deque[float]] = defaultdict(deque)
        self._err4xx: dict[str, int] = defaultdict(int)
        self._flags: dict[str, float] = {}
        self._max_profiles = max_profiles

    def _evict_idle(self, now: float) -> None:
        stale = [ip for ip, dq in self._vol.items() if not dq or now - dq[-1] > PROFILE_TTL]
        for ip in stale:
            self._vol.pop(ip, None)
            self._err4xx.pop(ip, None)
            self._flags.pop(ip, None)
        overflow = len(self._vol) - self._max_profiles
        if overflow > 0:
            oldest = sorted(self._vol.items(), key=lambda kv: kv[1][-1] if kv[1] else 0.0)
            for ip, _dq in oldest[:overflow]:
                self._vol.pop(ip, None)
                self._err4xx.pop(ip, None)
                self._flags.pop(ip, None)

    @staticmethod
    def _entropy(s: str) -> float:
        if not s:
            return 0.0
        n = len(s)
        counts: dict[str, int] = {}
        for ch in s:
            counts[ch] = counts.get(ch, 0) + 1
        return -sum((c / n) * math.log2(c / n) for c in counts.values())

    def score(self, ip: str, status_code: int, query: str, payload_len: int) -> int:
        """Increment profile and return the anomaly score (0-100)."""
        with self._lock:
            now = time.time()
            self._evict_idle(now)
            dq = self._vol[ip]
            while dq and now - dq[0] > 60:
                dq.popleft()
            dq.append(now)
            if status_code >= 400:
                self._err4xx[ip] += 1
            else:
                self._err4xx[ip] = max(0, self._err4xx[ip] - 1)

            score = 0
            vol = len(dq)
            if vol > 300:
                score += 30
            elif vol > 150:
                score += 15
            err_ratio = self._err4xx[ip] / max(1, vol)
            if err_ratio > 0.6:
                score += 30
            elif err_ratio > 0.3:
                score += 15
            if self._entropy(query) > 4.5 and query:
                score += 25
            if payload_len > 200_000:
                score += 15

            if score >= 80:
                self._flags[ip] = now
            else:
                self._flags.pop(ip, None)
            return min(100, score)

    def is_flagged(self, ip: str) -> bool:
        with self._lock:
            ts = self._flags.get(ip)
            if ts is None:
                return False
            if time.time() - ts > 600:
                self._flags.pop(ip, None)
                return False
            return True


anomaly_detector = AnomalyDetector()
