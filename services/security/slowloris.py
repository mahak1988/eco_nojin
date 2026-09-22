"""Slowloris attack protection middleware.

Protects against Slowloris-style attacks where malicious clients
send requests very slowly to keep connections open and exhaust thread pools.

Implementation:
- Enforce minimum request body transfer rate
- Maximum time to complete request headers
- Connection timeout enforcement
"""

import logging
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Minimum bytes per second to accept a connection
MIN_UPLOAD_SPEED = 512  # bytes/sec
MIN_DOWNLOAD_SPEED = 256  # bytes/sec

# Maximum time to receive request headers (seconds)
MAX_HEADER_TIME = 10.0

# Maximum total request time (seconds)
MAX_REQUEST_TIME = 30.0

# Minimum data rate threshold for abort (bytes/second)
SPEED_THRESHOLD = 100


class SlowlorisMiddleware:
    """Middleware to protect against Slowloris attacks.

    Monitors connection speed and aborts connections that
    transmit data too slowly.
    """

    def __init__(
        self,
        app: Callable,
        max_header_time: float = MAX_HEADER_TIME,
        max_request_time: float = MAX_REQUEST_TIME,
        min_speed_threshold: float = SPEED_THRESHOLD,
    ):
        self.app = app
        self.max_header_time = max_header_time
        self.max_request_time = max_request_time
        self.min_speed_threshold = min_speed_threshold

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get client IP for logging
        headers = dict(scope.get("headers") or [])
        fwd = headers.get(b"x-forwarded-for")
        if fwd:
            client_ip = fwd.decode().split(",")[0].strip()
        else:
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"

        path = scope.get("path", "/")

        # Track request start time
        request_start = time.time()
        last_receive = request_start
        bytes_received = 0

        async def monitored_receive():
            nonlocal last_receive, bytes_received

            msg = await receive()

            if msg["type"] == "http.request":
                body = msg.get("body", b"")
                bytes_received += len(body)

                current_time = time.time()
                elapsed = current_time - last_receive

                # Check if connecting too slowly
                if elapsed > 0 and len(body) < self.min_speed_threshold * elapsed:
                    duration = current_time - request_start
                    logger.warning(
                        f"Slowloris protection: aborting slow connection "
                        f"from {client_ip} to {path} "
                        f"({bytes_received} bytes in {duration:.1f}s)"
                    )
                    # Raise to abort connection
                    raise SlowlorisConnectionError(
                        f"Connection too slow: {bytes_received} bytes in {elapsed:.2f}s"
                    )

                last_receive = current_time

                # Check total request time
                total_time = current_time - request_start
                if total_time > self.max_request_time:
                    logger.warning(
                        f"Slowloris protection: request timeout for {client_ip} to {path} "
                        f"(took {total_time:.1f}s, max {self.max_request_time}s)"
                    )
                    raise SlowlorisTimeoutError(f"Request timeout: took {total_time:.1f}s")

            # Check header time
            if current_time - request_start > self.max_header_time:
                if msg["type"] == "http.disconnect" or not msg.get("more_body", True):
                    if bytes_received == 0:
                        logger.warning(
                            f"Slowloris protection: slow header from {client_ip} "
                            f"took {current_time - request_start:.1f}s"
                        )
                        raise SlowlorisTimeoutError("Headers received too slowly")

            return msg

        try:
            await self.app(scope, monitored_receive, send)
        except SlowlorisConnectionError:
            # Let the framework handle the error response
            raise
        except SlowlorisTimeoutError:
            # Let the framework handle the error response
            raise


class SlowlorisConnectionError(RuntimeError):
    """Raised when a connection is detected as slow and abusive."""

    pass


class SlowlorisTimeoutError(RuntimeError):
    """Raised when a request takes too long."""

    pass


def create_slowloris_middleware(
    max_header_time: float = MAX_HEADER_TIME,
    max_request_time: float = MAX_REQUEST_TIME,
    min_speed_threshold: float = SPEED_THRESHOLD,
) -> Callable:
    """Factory function to create Slowloris middleware with custom settings."""

    def middleware(app: Callable) -> SlowlorisMiddleware:
        return SlowlorisMiddleware(
            app,
            max_header_time=max_header_time,
            max_request_time=max_request_time,
            min_speed_threshold=min_speed_threshold,
        )

    return middleware
