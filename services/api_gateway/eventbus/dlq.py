"""
Dead Letter Queue Handler for NATS
===================================
Handles failed message processing with retry logic and DLQ storage.
"""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from database.hub import hub
from services.security.query_safe import _safe_ident

logger = logging.getLogger("econojin.eventbus.dlq")


@dataclass
class DeadLetter:
    """Dead letter entry for failed message processing."""

    id: int | None
    subject: str
    payload: dict[str, Any]
    headers: dict[str, str]
    error: str
    retry_count: int
    created_at: datetime
    last_attempt_at: datetime


class DLQHandler:
    """Manages dead letter queue for failed NATS message processing."""

    def __init__(self, max_retries: int = 3, dlq_table: str = "nats_dead_letter"):
        self.max_retries = max_retries
        self.dlq_table = _safe_ident(dlq_table)  # Validate table name at init
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Ensure DLQ table exists in SQLite."""
        try:
            conn = hub.get_sqlite("manual")
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.dlq_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    headers TEXT NOT NULL,
                    error TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_attempt_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        except Exception as e:
            logger.warning(f"Could not ensure DLQ table: {e}")

    async def add_to_dlq(
        self,
        subject: str,
        payload: dict[str, Any],
        headers: dict[str, str],
        error: str,
        retry_count: int = 0,
    ) -> int:
        """Add a failed message to the dead letter queue."""
        now = datetime.now(UTC).isoformat()
        try:
            conn = hub.get_sqlite("manual")
            cursor = conn.execute(
                f"""
                INSERT INTO {self.dlq_table}
                (subject, payload, headers, error, retry_count, created_at, last_attempt_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subject,
                    json.dumps(payload, ensure_ascii=False),
                    json.dumps(headers, ensure_ascii=False),
                    error,
                    retry_count,
                    now,
                    now,
                ),
            )
            conn.commit()
            dlq_id = cursor.lastrowid
            logger.warning(f"Added to DLQ [{dlq_id}]: {subject} - {error}")
            return dlq_id
        except Exception as e:
            logger.error(f"Failed to add to DLQ: {e}")
            return -1

    async def retry_from_dlq(self, dlq_id: int) -> bool:
        """Retry a message from the DLQ."""
        try:
            conn = hub.get_sqlite("manual")
            row = conn.execute(
                f"SELECT subject, payload, headers, retry_count FROM {self.dlq_table} WHERE id = ?",
                (dlq_id,),
            ).fetchone()

            if not row:
                logger.warning(f"DLQ entry {dlq_id} not found")
                return False

            subject, payload_json, headers_json, retry_count = row
            payload = json.loads(payload_json)
            headers = json.loads(headers_json)

            # Re-publish to NATS
            from services.api_gateway.eventbus import get_nats_manager

            nats_manager = get_nats_manager()

            success = await nats_manager.publish_with_retry(
                subject,
                payload,
                headers=headers,
                max_retries=self.max_retries - retry_count,
            )

            if success:
                # Remove from DLQ on success
                conn.execute(f"DELETE FROM {self.dlq_table} WHERE id = ?", (dlq_id,))
                conn.commit()
                logger.info(f"DLQ entry {dlq_id} retried successfully")
                return True
            else:
                # Increment retry count
                new_retry_count = retry_count + 1
                conn.execute(
                    f"UPDATE {self.dlq_table} SET retry_count = ?, last_attempt_at = ? WHERE id = ?",
                    (new_retry_count, datetime.now(UTC).isoformat(), dlq_id),
                )
                conn.commit()
                logger.warning(f"DLQ entry {dlq_id} retry failed (attempt {new_retry_count})")
                return False

        except Exception as e:
            logger.error(f"Failed to retry DLQ entry {dlq_id}: {e}")
            return False

    async def get_dlq_entries(self, limit: int = 100) -> list[DeadLetter]:
        """Get all entries from the DLQ."""
        try:
            conn = hub.get_sqlite("manual")
            rows = conn.execute(
                f"""
                SELECT id, subject, payload, headers, error, retry_count, created_at, last_attempt_at
                FROM {self.dlq_table}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            entries = []
            for row in rows:
                entries.append(
                    DeadLetter(
                        id=row[0],
                        subject=row[1],
                        payload=json.loads(row[2]),
                        headers=json.loads(row[3]),
                        error=row[4],
                        retry_count=row[5],
                        created_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(UTC),
                        last_attempt_at=datetime.fromisoformat(row[7])
                        if row[7]
                        else datetime.now(UTC),
                    )
                )
            return entries
        except Exception as e:
            logger.error(f"Failed to get DLQ entries: {e}")
            return []

    async def cleanup_old_entries(self, older_than_days: int = 30) -> int:
        """Remove old entries from DLQ."""
        try:
            cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
            conn = hub.get_sqlite("manual")
            cursor = conn.execute(
                f"DELETE FROM {self.dlq_table} WHERE created_at < ?",
                (cutoff.isoformat(),),
            )
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to cleanup DLQ: {e}")
            return 0


# Global DLQ handler
_dlq_handler: DLQHandler | None = None


def get_dlq_handler() -> DLQHandler:
    """Get or create the global DLQ handler."""
    global _dlq_handler
    if _dlq_handler is None:
        _dlq_handler = DLQHandler()
    return _dlq_handler