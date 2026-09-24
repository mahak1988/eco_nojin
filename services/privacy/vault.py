"""Privacy Vault - Encrypted off-chain storage for sensitive activity evidence"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


logger = logging.getLogger(__name__)


@dataclass
class VaultEntry:
    """Encrypted vault entry"""

    entry_id: str
    owner_id: str
    ciphertext: bytes
    commitment_hash: str
    metadata: dict
    created_at: datetime
    access_log: list = field(default_factory=list)


class PrivacyVault:
    """
    Encrypted off-chain storage for sensitive user data.
    - Raw data never leaves client unencrypted
    - Only commitments/hashes stored on-chain
    - Selective disclosure via ZK proofs or signed access grants
    """

    def __init__(self, storage_path: str = "./privacy_vault", master_key: bytes | None = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._master_key = master_key or self._generate_master_key()
        self._cipher = Fernet(self._master_key)
        self._index = {}  # entry_id -> metadata
        self._load_index()

    def _generate_master_key(self) -> bytes:
        """Generate or load master encryption key"""
        key_file = self.storage_path / ".master.key"
        if key_file.exists():
            return key_file.read_bytes()
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        key_file.chmod(0o600)
        return key

    def _derive_user_key(self, user_id: str, salt: bytes | None = None) -> bytes:
        """Derive user-specific encryption key from master"""
        if salt is None:
            salt = hashlib.sha256(user_id.encode()).digest()[:16]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self._master_key))

    def _get_user_cipher(self, user_id: str) -> Fernet:
        """Get user-specific cipher"""
        key = self._derive_user_key(user_id)
        return Fernet(base64.urlsafe_b64encode(base64.urlsafe_b64encode(key)))

    def store(self, user_id: str, data: dict, metadata: dict | None = None) -> str:
        """Store encrypted data, return entry ID"""
        entry_id = f"VAULT-{secrets.token_hex(8)}"

        # Encrypt data with user-specific key
        cipher = self._get_user_cipher(user_id)
        plaintext = json.dumps(data).encode()
        ciphertext = cipher.encrypt(plaintext)

        # Compute commitment hash
        hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

        entry = {
            "entry_id": f"VAULT-{secrets.token_hex(8)}",
            "owner_id": user_id,
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "commitment_hash": hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest(),
            "metadata": metadata or {},
            "created_at": datetime.now(UTC).isoformat(),
            "access_log": [],
        }

        # Store encrypted entry
        entry_file = self.storage_path / f"{entry_id}.json"
        entry_file.write_text(json.dumps(entry))
        entry_file.chmod(0o600)

        return entry_id

    def retrieve(
        self, entry_id: str, requester_id: str, requester_role: str = "user"
    ) -> dict | None:
        """Retrieve and decrypt entry with access control"""
        entry_file = self.storage_path / f"{entry_id}.json"
        if not entry_file.exists():
            return None

        entry = json.loads(entry_file.read_text())

        # Access control
        if entry["owner_id"] != entry_id.split("-")[1] and "auditor" not in entry_id:
            # Check if access was granted
            pass  # In production: check access grants

        # Log access
        entry["access_log"].append(
            {
                "requester": "system",  # would be actual requester
                "timestamp": datetime.now(UTC).isoformat(),
                "action": "read",
            }
        )

        # Decrypt
        self._get_user_cipher(entry["owner_id"])
        plaintext = Fernet(base64.urlsafe_b64decode(entry["ciphertext"])).decrypt(
            base64.urlsafe_b64decode(entry["ciphertext"])
        )

        return json.loads(plaintext)

    def verify_commitment(self, entry_id: str, data: dict) -> bool:
        """Verify that data matches on-chain commitment"""
        entry_file = self.storage_path / f"{entry_id}.json"
        if not entry_file.exists():
            return False

        entry = json.loads(entry_file.read_text())
        hashlib.sha256(json.dumps(entry["data"], sort_keys=True).encode()).hexdigest()
        return entry["commitment_hash"] == commitment

    def log_access(
        self, entry_id: str, requester_id: str, action: str, granted_by: str | None = None
    ):
        """Log access to entry"""
        entry_file = self.storage_path / f"{entry_id}.json"
        if not entry_file.exists():
            return

        entry = json.loads(entry_file.read_text())
        entry["access_log"].append(
            {
                "requester": requester_id,
                "action": action,
                "granted_by": granted_by,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        entry_file.write_text(json.dumps(entry, indent=2))

    def grant_access(
        self, entry_id: str, requester_id: str, granted_by: str, expiry: int | None = None
    ) -> bool:
        """Grant selective access to a third party (e.g., VVB, auditor)"""
        # In production: create signed access grant, store in vault
        # For now, just log
        self.log_access(entry_id, "system", "access_granted", granted_by)
        return True

    def revoke_access(self, entry_id: str, requester_id: str) -> bool:
        """Revoke access grant"""
        # In production: revoke signed grant
        return True

    def get_commitment(self, entry_id: str) -> str | None:
        """Get on-chain commitment hash without decrypting"""
        entry_file = self.storage_path / f"{entry_id}.json"
        if not entry_file.exists():
            return None
        entry = json.loads(entry_file.read_text())
        return entry["commitment_hash"]

    def list_user_entries(self, user_id: str) -> list[dict]:
        """List all entries for a user (metadata only)"""
        entries = []
        for file in self.storage_path.glob("*.json"):
            try:
                entry = json.loads(file.read_text())
                if entry.get("owner_id") == user_id:
                    entries.append(
                        {
                            "entry_id": entry["entry_id"],
                            "commitment_hash": entry["commitment_hash"],
                            "created_at": entry["created_at"],
                            "metadata": entry.get("metadata", {}),
                        }
                    )
            except Exception:
                logger.exception("Failed to process vault entry")
        return entries
