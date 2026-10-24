"""The typed error a failed Engine Gateway call raises at the services boundary.

Remediation item **D4** of ``reports/eco-nojin/ERROR-MAP.md`` §4 ("The
gateway's code is destroyed at the services boundary"): the facade used to
convert every ``engine.gateway.GatewayError`` into a bare
``RuntimeError(f"Gateway error: {result.message}")``
(``services/_gateway_facade.py:218-219``), discarding the gateway's
``error_code``, ``validation_errors`` and ``evidence_id`` at the one boundary
48 services modules go through.

:class:`GatewayCallError` keeps that exact message text and still subclasses
``RuntimeError``, so the change is behaviour-preserving for every existing
consumer: an ``except RuntimeError`` arm still catches it and ``str(exc)``
still returns the same string. What is new is that the machine-readable fields
the gateway produced survive the boundary, and that they are mapped onto the
specification's own 13-code vocabulary (``ERROR-MAP.md`` §3) via
:attr:`GatewayCallError.spec_error_code`.

Nothing here raises on import and nothing here imports the facade, so the
dependency stays one-directional: ``services._gateway_facade`` imports this
module, never the reverse.
"""

from __future__ import annotations

from typing import Any

from engine.errors import ERROR_CODES

__all__ = [
    "GATEWAY_CODE_TO_SPEC_CODE",
    "GATEWAY_ERROR_MESSAGE",
    "SPEC_ERROR_CODES",
    "GatewayCallError",
]

#: The message template the facade has always produced. Defined once so the
#: format has a single definition and the D4 guarantee ("``str(exc)`` is
#: unchanged") is checkable rather than asserted.
GATEWAY_ERROR_MESSAGE = "Gateway error: {message}"

#: The gateway's own codes mapped onto the specification's 13
#: (``ERROR-MAP.md`` §3). ``EXECUTION_ERROR`` is the blanket catch the gateway
#: uses, which is why it lands on ``EXECUTION_FAILED`` rather than on the more
#: specific codes its raw exceptions are re-labelled from (ERROR-MAP §4 D9).
#: A gateway code absent from this table has no spec equivalent, and
#: ``spec_error_code`` stays ``None`` for it — no code is invented.
GATEWAY_CODE_TO_SPEC_CODE: dict[str, str] = {
    "INVALID_REQUEST": "INPUT_INVALID",
    "MODEL_NOT_FOUND": "MODEL_UNKNOWN",
    "EXECUTION_ERROR": "EXECUTION_FAILED",
}

#: The specification's 13-code vocabulary, re-exported from the engine's single
#: definition (``engine/errors.py:57``) rather than copied, so this service-side
#: map cannot drift from the contract it claims to honour.
SPEC_ERROR_CODES: dict[str, str] = dict(ERROR_CODES)


class GatewayCallError(RuntimeError):
    """A failed gateway call that still carries the gateway's error.

    Subclasses :class:`RuntimeError` deliberately: the facade raised exactly
    that, so ``except RuntimeError`` in any of the 48 consuming modules keeps
    working without edit, and ``str(exc)`` keeps returning
    ``"Gateway error: <gateway message>"``.

    Attributes:
        message: The exact text the facade produced before D4.
        error_code: The gateway's own code (``INVALID_REQUEST``,
            ``MODEL_NOT_FOUND`` / ``EXECUTION_ERROR``), preserved instead of
            discarded. ``None`` when the caller constructs the error without
            one.
        validation_errors: The gateway's per-field validation messages, in
            the order it reported them.
        evidence_id: The gateway's evidence record id for this execution, when
            it produced one.
        trace_id: The execution trace id from the gateway's
            ``ExecutionMetadata``, when it carries one.
        model_id: The model the call targeted, when known.
        spec_error_code: ``error_code`` mapped onto the specification's
            13-code vocabulary, or ``None`` when the gateway code has no spec
            equivalent or was not supplied.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        validation_errors: list[str] | None = None,
        evidence_id: str | None = None,
        trace_id: str | None = None,
        model_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.validation_errors: list[str] = list(validation_errors or [])
        self.evidence_id = evidence_id
        self.trace_id = trace_id
        self.model_id = model_id
        self.spec_error_code: str | None = (
            GATEWAY_CODE_TO_SPEC_CODE.get(error_code) if error_code else None
        )

    def __str__(self) -> str:
        """The unchanged facade message — see the D4 behaviour guarantee."""
        return self.message

    def __repr__(self) -> str:
        return (
            f"GatewayCallError(error_code={self.error_code!r}, "
            f"spec_error_code={self.spec_error_code!r}, message={self.message!r})"
        )

    def as_dict(self) -> dict[str, Any]:
        """The machine-readable payload this error carries, code first."""
        return {
            "error_code": self.error_code,
            "spec_error_code": self.spec_error_code,
            "message": self.message,
            "validation_errors": list(self.validation_errors),
            "evidence_id": self.evidence_id,
            "trace_id": self.trace_id,
            "model_id": self.model_id,
        }

    @property
    def spec_error_description(self) -> str | None:
        """The Persian description of :attr:`spec_error_code`, when mapped."""
        if self.spec_error_code is None:
            return None
        return SPEC_ERROR_CODES.get(self.spec_error_code)

    @classmethod
    def from_gateway_error(cls, error: Any) -> GatewayCallError:
        """Build the exception from a returned ``engine.gateway.GatewayError``.

        ``EngineGateway.execute`` *returns* its error value object rather than
        raising it (``engine/gateway/__init__.py``), which is why callers test
        ``isinstance(result, GatewayError)``. This constructor is the single
        place that value object crosses into the services tier.

        ``trace_id`` is read from the error's ``execution`` metadata, the only
        place the gateway publishes it; ``model_id`` is read from the error
        itself. Both use ``getattr`` so the constructor keeps working against
        any duck-typed stand-in a test supplies.
        """
        execution = getattr(error, "execution", None)
        return cls(
            GATEWAY_ERROR_MESSAGE.format(message=error.message),
            error_code=getattr(error, "error_code", None),
            validation_errors=list(getattr(error, "validation_errors", None) or []),
            evidence_id=getattr(error, "evidence_id", None),
            trace_id=getattr(execution, "trace_id", None),
            model_id=getattr(error, "model_id", None),
        )
