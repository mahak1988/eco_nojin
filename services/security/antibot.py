"""Layer 6 — anti-bot and abuse resistance.

Three signals, ordered by how hard each is to forge:

1. **Proof of work** — a server-issued nonce the client must solve. A bot must
   spend real CPU per request, so bulk abuse stops being cheap. This is the
   only signal here that an attacker cannot bypass by simply sending valid
   traffic.
2. **HTTP/2 + header fingerprint** — the ``h2`` half of a JA4-style
   fingerprint, computed from the ASGI scope. This is *transport-observed*:
   the client never declares it. Different HTTP stacks emit different header
   sets and orders, and hand-rolled clients rarely match a browser.
3. **Request cadence and shape** — server-side timing statistics: inter-arrival
   variance, burst size, and path entropy. Measured, not claimed.

Deliberately excluded: client-reported "behavioural" telemetry (mouse paths,
keystroke rhythm, dwell time). A headless browser driving a real Chrome
reproduces a real human's timing exactly, and any client-side value is
attacker-controlled. Treating it as a primary signal is how anti-bot systems
end up decorative. The same weakness applies to the TLS half of JA4: a
full-stack emulation such as Puppeteer or Playwright yields a fingerprint
identical to a legitimate user (arXiv:2602.09606, 2026). Only the header-order
half, which a hand-rolled HTTP client gets wrong, is usable from here — and a
full-stack emulator gets *that* right too, so it is a tiebreaker, never a gate.

Escalation is progressive, never all-or-nothing::

    allow  ->  delay  ->  challenge  ->  block

so a false positive costs a slow request rather than a blocked user.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import secrets
import statistics
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

CHALLENGE_TTL = 120.0  # a PoW challenge is valid for two minutes
DEFAULT_DIFFICULTY_BITS = 14  # ~16k sha256 attempts: ~ms for a client, minutes for a flood
PROFILE_TTL = 300.0
MAX_PROFILES = 20_000
MAX_CHALLENGES = 20_000
SAMPLE_WINDOW = 40  # inter-arrival samples kept per client
# Slower than this and a client is background polling, not scraping. Above it,
# perfectly regular spacing is still worth a challenge: a scraper that sleeps
# to stay under the rate limiter is exactly the client this layer exists for.
MACHINE_CADENCE_CEILING = 5.0
# Above this many requests per second a client is not browsing.
BURST_RATE_FLOOR = 15.0
BEHAVIORAL_SALT = b"econojin-antibot-v1"

# Headers whose value is attacker-chosen and therefore excluded from the
# fingerprint; their *presence* is still counted.
VOLATILE_HEADERS = frozenset({b"date", b"if-modified-since", b"traceparent"})


class Action(StrEnum):
    ALLOW = "allow"
    DELAY = "delay"
    CHALLENGE = "challenge"
    BLOCK = "block"


@dataclass(frozen=True)
class Decision:
    action: Action
    score: int
    reasons: tuple[str, ...] = ()
    delay_seconds: float = 0.0
    challenge: Challenge | None = None

    @property
    def challenged(self) -> bool:
        return self.action is Action.CHALLENGE


@dataclass(frozen=True)
class Challenge:
    nonce: str
    difficulty_bits: int
    issued_at: float
    expires_at: float
    solved: bool = False


@dataclass
class Profile:
    """Per-client observations. Bounded and evictable — an attacker rotating
    addresses must not be able to grow this without limit."""

    seen: int = 0
    first_at: float = 0.0
    last_at: float = 0.0
    gaps: deque[float] = field(default_factory=lambda: deque(maxlen=SAMPLE_WINDOW))
    paths: set[str] = field(default_factory=set)
    tails: dict[str, set[str]] = field(default_factory=dict)
    fingerprints: set[str] = field(default_factory=set)
    challenges_issued: int = 0
    challenges_failed: int = 0
    blocked_until: float = 0.0

    def observe(self, path: str, fingerprint: str, now: float) -> None:
        # The first observation has no predecessor, so it contributes no
        # interval. Including a near-zero gap here would otherwise make every
        # client's cadence look like a machine.
        if self.seen:
            self.gaps.append(now - self.last_at)
        else:
            self.first_at = now
        self.seen += 1
        self.last_at = now
        if len(self.paths) < 512:
            self.paths.add(path)
        template, tail = _split_numeric_tail(path)
        if tail is not None:
            bucket = self.tails.setdefault(template, set())
            if len(bucket) < 512:
                bucket.add(tail)
        if len(self.fingerprints) < 16:
            self.fingerprints.add(fingerprint)


# ---------------------------------------------------------------------------
# proof of work
# ---------------------------------------------------------------------------
def issue_challenge(difficulty_bits: int = DEFAULT_DIFFICULTY_BITS) -> Challenge:
    return Challenge(
        nonce=secrets.token_urlsafe(24),
        difficulty_bits=difficulty_bits,
        issued_at=time.time(),
        expires_at=time.time() + CHALLENGE_TTL,
    )


def solve_pow(nonce: str, difficulty_bits: int, max_iterations: int = 5_000_000) -> str | None:
    """Reference solver, used by tests and by honest clients."""
    for counter in range(max_iterations):
        solution = f"{counter}"
        if _leading_zero_bits(_digest(nonce, solution)) >= difficulty_bits:
            return solution
    return None


def verify_pow(nonce: str, solution: str, difficulty_bits: int) -> bool:
    if not nonce or not solution or len(solution) > 32:
        return False
    return _leading_zero_bits(_digest(nonce, solution)) >= difficulty_bits


def _digest(nonce: str, solution: str) -> bytes:
    return hashlib.sha256(f"{nonce}:{solution}".encode()).digest()


def _leading_zero_bits(digest: bytes) -> int:
    full = digest[:4]
    bits = int.from_bytes(full, "big")
    return 32 - bits.bit_length()


# ---------------------------------------------------------------------------
# HTTP/2 + header fingerprint
# ---------------------------------------------------------------------------
def http_fingerprint(scope: dict[str, Any]) -> str:
    """JA4-style ``h2``-style fingerprint built from the observed scope.

    Mirrors the shape of the JA4 ``h2`` component: method, protocol, ordered
    header names with volatile ones removed, cookie presence, and a count.
    Returns a stable short hash; the input string is kept for debugging.
    """
    method = scope.get("method", "GET")
    proto = str(scope.get("http_version", "1.1"))
    names: list[str] = []
    has_cookie = False
    for raw_name, _value in scope.get("headers") or ():
        name = raw_name.lower()
        if name == b"cookie":
            has_cookie = True
        if name in VOLATILE_HEADERS:
            continue
        names.append(name.decode("latin-1"))
    raw = f"{method}_{proto}_{','.join(names)}_c{1 if has_cookie else 0}_{len(names)}"
    return "h2_" + hashlib.sha256(raw.encode("latin-1", "replace")).hexdigest()[:16]


def raw_fingerprint_input(scope: dict[str, Any]) -> str:
    """The pre-hash string, exposed so a mismatch can be diagnosed."""
    method = scope.get("method", "GET")
    proto = str(scope.get("http_version", "1.1"))
    names = [
        n.lower().decode("latin-1")
        for n, _ in scope.get("headers") or ()
        if n.lower() not in VOLATILE_HEADERS
    ]
    has_cookie = any(n.lower() == b"cookie" for n, _ in scope.get("headers") or ())
    return f"{method}_{proto}_{','.join(names)}_c{1 if has_cookie else 0}_{len(names)}"


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------
def _split_numeric_tail(path: str) -> tuple[str, str | None]:
    """Split ``/api/v1/farms/42`` into ``("/api/v1/farms", "42")``.

    This is what separates enumeration from ordinary browsing. Paginating
    ``?page=1..30`` keeps one path and varies a query parameter, so it yields a
    single template and no signal. Walking ``/farms/1``, ``/farms/2``, ... holds
    one template while the tail count climbs, which is what a scraper does.
    """
    clean = path.split("?", 1)[0].split("#", 1)[0]
    head, _, tail = clean.rpartition("/")
    if tail.isdigit():
        return (head or "/"), tail
    return clean, None


def _cadence_score(profile: Profile) -> tuple[int, str | None]:
    """Reward a human-shaped arrival pattern, penalise machine constancy.

    Capped at the challenge tier on purpose. A dashboard polling every 900ms is
    perfectly regular, and so is a scraper sleeping to stay under the rate
    limiter — timing alone cannot tell them apart. Resolving that costs the
    caller one proof of work (milliseconds in a browser, cached afterwards),
    which is cheap enough to charge on suspicion; it is not cheap enough to
    block on.
    """
    if len(profile.gaps) < 8:
        return 0, None
    gaps = list(profile.gaps)
    try:
        mean = statistics.fmean(gaps)
        stdev = statistics.pstdev(gaps)
    except statistics.StatisticsError:
        return 0, None
    if mean <= 0:
        return 25, "cadence_zero_interval"
    if mean >= MACHINE_CADENCE_CEILING:
        return 0, None
    # coefficient of variation: humans ~0.5-1.5, a scheduled loop is ~0
    cv = stdev / mean
    if cv < 0.05:
        return 25, "cadence_machine_even"
    if cv < 0.15:
        return 12, "cadence_robotic"
    return 0, None


def _path_entropy_score(profile: Profile) -> tuple[int, str | None]:
    """Flag one path template walked with many distinct ids."""
    if profile.seen < 40:
        return 0, None
    worst = max((len(v) for v in profile.tails.values()), default=0)
    if worst >= 25:
        return 20, "id_enumeration"
    return 0, None


def _fingerprint_score(profile: Profile) -> tuple[int, str | None]:
    """One client presenting many distinct header layouts is rotating clients."""
    if profile.seen < 25:
        return 0, None
    if len(profile.fingerprints) >= 4:
        return 20, "fingerprint_rotation"
    if len(profile.fingerprints) == 1 and profile.seen > 200:
        return 5, "fingerprint_constant"
    return 0, None


def _burst_score(profile: Profile, now: float) -> tuple[int, str | None]:
    """Scale with observed rate, so a heavy flood outweighs a brief one."""
    if profile.seen < 20 or profile.first_at <= 0:
        return 0, None
    elapsed = now - profile.first_at
    if elapsed <= 0:
        return 0, None
    rate = profile.seen / elapsed
    if rate < BURST_RATE_FLOOR:
        return 0, None
    points = min(35, 15 + int(rate - BURST_RATE_FLOOR))
    return points, "burst_rate"


class AntiBot:
    """Stateful scorer. Thread-safe; all state is bounded and evictable."""

    def __init__(
        self,
        difficulty_bits: int = DEFAULT_DIFFICULTY_BITS,
        block_score: int = 70,
        challenge_score: int = 35,
        delay_score: int = 15,
        max_delay: float = 3.0,
        max_profiles: int = MAX_PROFILES,
        max_challenges: int = MAX_CHALLENGES,
        sweep_interval: int = 64,
    ) -> None:
        self.difficulty_bits = difficulty_bits
        self.block_score = block_score
        self.challenge_score = challenge_score
        self.delay_score = delay_score
        self.max_delay = max_delay
        self.max_profiles = max_profiles
        self.max_challenges = max_challenges
        self.sweep_interval = max(1, sweep_interval)
        self._profiles: dict[str, Profile] = {}
        self._challenges: dict[str, Challenge] = {}
        self._lock = threading.RLock()
        self._since_sweep = 0
        self.signature_key = hashlib.sha256(BEHAVIORAL_SALT + secrets.token_bytes(32)).digest()

    # -- housekeeping -----------------------------------------------------
    def _sweep_locked(self, now: float) -> None:
        """Drop idle profiles and expired challenges.

        Deliberately *not* run per request: a full scan is O(profiles), so
        calling it on every assess() made a flood cost O(n) per request and
        turned the limiter into the bottleneck. The caller amortises it, and
        the hard cap is still enforced on every single call (see _enforce_cap).
        """
        stale = [k for k, p in self._profiles.items() if now - p.last_at > PROFILE_TTL]
        for k in stale:
            self._profiles.pop(k, None)
        for nonce, ch in list(self._challenges.items()):
            if now > ch.expires_at + 1:
                del self._challenges[nonce]
        if len(self._challenges) > self.max_challenges:
            cutoff = sorted(self._challenges.items(), key=lambda kv: kv[1].issued_at)
            for nonce, _c in cutoff[: len(self._challenges) - self.max_challenges]:
                self._challenges.pop(nonce, None)

    def _enforce_cap_locked(self, now: float) -> None:
        """Keep the profile table bounded, amortised.

        Trimming back to 90% rather than to the exact cap means one O(n log n)
        sweep covers many subsequent inserts instead of running per insert.
        """
        if len(self._profiles) <= self.max_profiles:
            return
        target = int(self.max_profiles * 0.9)
        oldest = sorted(self._profiles.items(), key=lambda kv: kv[1].last_at)
        for k, _p in oldest[: len(self._profiles) - target]:
            self._profiles.pop(k, None)

    def _housekeeping(self, now: float) -> None:
        self._since_sweep += 1
        if self._since_sweep >= self.sweep_interval or len(self._profiles) > self.max_profiles:
            self._sweep_locked(now)
            self._since_sweep = 0
        self._enforce_cap_locked(now)

    def _profile(self, client_id: str, now: float) -> Profile:
        profile = self._profiles.get(client_id)
        if profile is None:
            profile = Profile()
            self._profiles[client_id] = profile
        return profile

    def is_blocked(self, client_id: str, now: float | None = None) -> bool:
        now = now or time.time()
        with self._lock:
            profile = self._profiles.get(client_id)
            return bool(profile and now < profile.blocked_until)

    # -- main entry point -------------------------------------------------
    def assess(
        self,
        client_id: str,
        scope: dict[str, Any],
        path: str,
        now: float | None = None,
    ) -> Decision:
        """Score one request and pick an action. Cheap enough for every call."""
        now = now or time.time()
        fingerprint = http_fingerprint(scope)
        with self._lock:
            self._housekeeping(now)
            profile = self._profile(client_id, now)
            if now < profile.blocked_until:
                return Decision(Action.BLOCK, self.block_score, ("blocked",))
            profile.observe(path, fingerprint, now)

            score = 0
            reasons: list[str] = []
            # Explicit calls rather than iterating a tuple of scorers: the
            # burst scorer needs `now`, and a uniform-tuple loop with an
            # identity check hides that from the type checker.
            for points, reason in (
                _burst_score(profile, now),
                _cadence_score(profile),
                _path_entropy_score(profile),
                _fingerprint_score(profile),
            ):
                if points:
                    score += points
                    if reason:
                        reasons.append(reason)
            if profile.challenges_failed >= 3:
                score += 40
                reasons.append("pow_failed_repeatedly")
            elif profile.challenges_failed:
                score += 10
                reasons.append("pow_failed")

            if score >= self.block_score:
                profile.blocked_until = now + 300
                return Decision(Action.BLOCK, score, tuple(reasons))
            if score >= self.challenge_score:
                challenge = issue_challenge(self.difficulty_bits)
                self._challenges[challenge.nonce] = challenge
                profile.challenges_issued += 1
                return Decision(Action.CHALLENGE, score, tuple(reasons), challenge=challenge)
            if score >= self.delay_score:
                # longer delay the more suspicious the traffic looks
                excess = score - self.delay_score
                span = max(1, self.block_score - self.delay_score)
                delay = min(self.max_delay, self.max_delay * excess / span)
                return Decision(Action.DELAY, score, tuple(reasons), delay_seconds=round(delay, 3))
            return Decision(Action.ALLOW, score, tuple(reasons))

    # -- challenge lifecycle ---------------------------------------------
    def check_solution(self, nonce: str, solution: str) -> bool:
        """Validate a PoW response. Single-use: a solved nonce is consumed."""
        with self._lock:
            challenge = self._challenges.get(nonce)
            if challenge is None:
                return False
            now = time.time()
            if challenge.solved or now > challenge.expires_at:
                self._challenges.pop(nonce, None)
                return False
            if verify_pow(nonce, solution, challenge.difficulty_bits):
                # popping is what enforces single use; `solved` is only a
                # readable record for callers holding a reference.
                object.__setattr__(challenge, "solved", True)
                self._challenges.pop(nonce, None)
                return True
            return False

    def record_failed_solution(self, client_id: str) -> None:
        with self._lock:
            now = time.time()
            profile = self._profiles.get(client_id)
            if profile is None:
                # last_at must be set here: a Profile left at the 0.0 default is
                # immediately eligible for eviction, which would wipe the very
                # failure count this call is recording.
                profile = Profile(last_at=now)
                self._profiles[client_id] = profile
            profile.challenges_failed += 1
            profile.last_at = now

    def issue(self, client_id: str | None = None) -> Challenge:
        """Issue a challenge on demand (an endpoint can call this directly)."""
        with self._lock:
            self._sweep_locked(time.time())
            challenge = issue_challenge(self.difficulty_bits)
            self._challenges[challenge.nonce] = challenge
            if client_id and (p := self._profiles.get(client_id)):
                p.challenges_issued += 1
            return challenge

    def stats(self) -> dict[str, Any]:
        with self._lock:
            challenged = sum(1 for p in self._profiles.values() if p.challenges_issued)
            return {
                "profiles": len(self._profiles),
                "challenges_outstanding": len(self._challenges),
                "clients_challenged": challenged,
                "difficulty_bits": self.difficulty_bits,
                "thresholds": {
                    "delay": self.delay_score,
                    "challenge": self.challenge_score,
                    "block": self.block_score,
                },
            }

    def reset(self) -> None:
        with self._lock:
            self._profiles.clear()
            self._challenges.clear()


def difficulty_for_score(score: int) -> int:
    """Map a suspicion score onto a PoW cost, 12-18 bits.

    Kept low on purpose: a challenge must not read as a punishment. 12 bits is
    ~4k hashes (well under a second on a phone), 18 bits is ~260k, which is
    already awkward for a bulk harvester.
    """
    if score >= 55:
        return 18
    if score >= 45:
        return 16
    return 12


def hmac_token(nonce: str, key: bytes) -> str:
    return hmac.new(key, nonce.encode(), hashlib.sha256).hexdigest()


def clamp_score(value: float) -> int:
    return max(0, min(100, math.floor(value)))
