"""Download gate for ZED rule §2.2ج (data rules).

ZED §2.2ج rules referenced here:

1. No live downloads in the scientific core — the compute core of the
   engine must be able to run fully offline.
2. Downloads are permitted only when explicitly gated (opt-in by flag),
   never as an unconditional side effect.
3. Downloads must be confined to non-core paths — the engine core must
   stay HTTP-framework free (AR-03); ingestion belongs outside the core.
4. The gate itself is an end-user control: an operator decides, per run,
   whether the pipeline may reach the network.

Enforcement roadmap (deliberately behaviour-preserving):

* **This change (W2-6)** only makes every network fetch *observable* and
  *nameable*. With ``HYDROMA_ALLOW_DOWNLOAD`` unset — the default — the
  current permissive behaviour is unchanged: the download is performed and
  a single warning per target is emitted, so the ZED §2.2ج obligation is
  now visible in logs without altering any result.
* **Wave-3 decision** — whether strict becomes the default (i.e. the
  strict values below become the out-of-the-box behaviour).
* **Ultimately** engine ingestion should move out of the engine core
  (§2.2ج.3 / AR-03) into a separate, operator-invoked ingestion layer, at
  which point this gate becomes a hard, flag-only boundary.

Strict mode (**opt-in**, operator-controlled):

* ``HYDROMA_ALLOW_DOWNLOAD`` is read *at call time* (never at import time),
  normalised lower-case and stripped:
  - ``1`` / ``true`` / ``yes`` / ``on`` — permit (explicit allow = the
    historical default);
  - ``0`` / ``false`` / ``no`` / ``off`` — strict: the download is refused
    with :class:`PermissionError`;
  - anything else (incl. unset/empty) — treated as the historical default
    (permit) and a one-time warning is emitted about the unrecognised value.

Standard library only — no third-party imports.

Precedence (documented, and implemented exactly this way):

1. **CLI wins** — :func:`set_strict` (called by ``pipeline.py --strict`` /
   ``--deny-download`` / ``--allow-download``) pins the mode for the process
   and the environment is no longer consulted.
2. **Then the environment** — ``HYDROMA_ALLOW_DOWNLOAD``, re-read at every
   call while no CLI pin is active.
3. **Default permit** — unset/unrecognised env value and no CLI flag.
"""

from __future__ import annotations

import logging
import os

#: Environment variable read by :func:`is_strict` at every call.
ENV_VAR = "HYDROMA_ALLOW_DOWNLOAD"

#: Values that turn the gate into a hard refusal.
_VALUES_STRICT = frozenset({"0", "false", "no", "off"})

#: Values that explicitly permit the download (the historical default).
_VALUES_ALLOW = frozenset({"1", "true", "yes", "on"})

#: State of the gate: ``None`` = unparsed, ``True`` = strict, ``False`` = permit.
#: Deliberately not a constant: the env must decide, not this module.
_MODE: bool | None = None

#: Process-level pin installed by :func:`set_strict` (the CLI). ``None`` means
#: "no CLI pin": the environment is still read at call time. This is what makes
#: the CLI take precedence over ``HYDROMA_ALLOW_DOWNLOAD``.
_OVERRIDE: bool | None = None

#: Every target ever handed to :func:`note_download`, in first-seen order. This
#: is the source inventory used by ``pipeline.py --list-sources``; it is filled
#: at call time, so it is empty until the first gated fetch actually runs.
REGISTERED_SOURCES: dict[str, int] = {}

#: Set when the flag held an unrecognised value (its warning replaces the
#: per-target gate warning for that run, so a mistyped flag is named once).
_FLAG_WAS_UNRECOGNISED = False

#: Warnings already emitted (one-time-per-target de-duplication).
_SEEN: set[str] = set()

_logger = logging.getLogger("engine.hydroma.data_pipeline.download_gate")


def _current_mode() -> bool:
    """Return the current gate mode, re-reading ``HYDROMA_ALLOW_DOWNLOAD`` now."""
    global _MODE, _FLAG_WAS_UNRECOGNISED

    if _OVERRIDE is not None:
        # A CLI pin is active: the operator already decided, so the env is not
        # consulted and no "unrecognised env value" warning can be raised.
        _FLAG_WAS_UNRECOGNISED = False
        _MODE = _OVERRIDE
        return _MODE

    raw = os.environ.get(ENV_VAR)
    value = "" if raw is None else raw.strip().lower()
    _FLAG_WAS_UNRECOGNISED = False

    if value in _VALUES_STRICT:
        _MODE = True
    elif value in _VALUES_ALLOW:
        _MODE = False
    else:
        if value:
            _warn_once(
                "env-value",
                f"HYDROMA_ALLOW_DOWNLOAD={raw!r} is not a recognised gate value "
                f"({', '.join(sorted(_VALUES_STRICT | _VALUES_ALLOW))}); "
                "defaulting to permit (download enabled)",
            )
            _FLAG_WAS_UNRECOGNISED = True
        _MODE = False
    return _MODE


def is_strict() -> bool:
    """Return ``True`` when the gate currently refuses downloads (strict mode)."""
    return _current_mode()


def set_strict(value: bool | None) -> None:
    """Pin (or unpin) the gate for the current process — the CLI entry point.

    ``True`` — strict: downloads are refused regardless of the environment.
    ``False`` — permit: downloads are allowed regardless of the environment.
    ``None`` — drop the pin and fall back to reading
    ``HYDROMA_ALLOW_DOWNLOAD`` at call time again.

    This is deliberately how the CLI gets its precedence: once a flag has been
    parsed, the operator's decision wins over the environment for the rest of
    the process. Passing ``None`` restores the env-driven behaviour.
    """
    global _OVERRIDE

    if value is None:
        _OVERRIDE = None
        return
    _OVERRIDE = bool(value)


def _permit_reason() -> str:
    """Describe why the download is being permitted (used in the warning)."""
    if _OVERRIDE is None:
        return (
            f"{ENV_VAR} is unset or not a strict value, i.e. the default policy "
            f"(permit) applies"
        )
    return "the command line explicitly allowed downloads (--allow-download)"


def _refusal_reason() -> str:
    """Describe why the download is being refused (used in the error)."""
    if _OVERRIDE is None:
        return (
            f"{ENV_VAR} is set to a strict value "
            f"({', '.join(sorted(_VALUES_STRICT))})"
        )
    return "the command line requested strict mode (--strict / --deny-download)"


def _warn_once(key: str, message: str) -> None:
    """Emit ``message`` as a warning exactly once per ``key`` (no per-call flood)."""
    if key in _SEEN:
        return
    _SEEN.add(key)
    _logger.warning(message)


def note_download(target: str) -> None:
    """Gate one network fetch, ``target`` naming the source/endpoint.

    Must be called immediately before the ``requests`` call it guards.

    * permit (default env policy, or ``--allow-download``): the fetch proceeds —
      behaviour is exactly what it was before this gate existed — and a one-time
      warning states that ZED §2.2ج requires ingestion to be flag-gated and that
      this download was nonetheless permitted.
    * strict (a strict ``HYDROMA_ALLOW_DOWNLOAD`` value, or ``--strict`` /
      ``--deny-download``): :class:`PermissionError` naming ``target`` and
      pointing at the way to permit downloads explicitly.

    Every call records ``target`` in :data:`REGISTERED_SOURCES` (the inventory
    behind ``pipeline.py --list-sources``), so the set of network paths this
    module can reach is discoverable at runtime rather than by grep.
    """
    REGISTERED_SOURCES[target] = REGISTERED_SOURCES.get(target, 0) + 1

    if not _current_mode():
        if not _FLAG_WAS_UNRECOGNISED:
            _warn_once(
                target,
                f"ZED §2.2ج requires ingestion to be flag-gated (opt-in), but the "
                f"download {target!r} was permitted because "
                f"{_permit_reason()}. "
                f"Set {ENV_VAR}=0 to refuse downloads (strict mode) or =1 to "
                f"allow them explicitly.",
            )
        return

    raise PermissionError(
        f"Download blocked by the ZED §2.2ج gate: {target!r} may not reach the "
        f"network because {_refusal_reason()}. "
        f"Re-run with --allow-download (or {ENV_VAR}=1) to permit downloads "
        f"explicitly."
    )


def reset_seen() -> None:
    """Clear the one-time-warning registry. Provided for tests."""
    _SEEN.clear()


__all__ = [
    "ENV_VAR",
    "REGISTERED_SOURCES",
    "is_strict",
    "note_download",
    "reset_seen",
    "set_strict",
]
