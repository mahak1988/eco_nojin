"""Tests for the PrivacyVault (encrypted off-chain storage)."""

import json

import pytest

from services.privacy.vault import PrivacyVault


@pytest.fixture
def vault(tmp_path):
    """A vault rooted in a throwaway directory."""
    return PrivacyVault(storage_path=str(tmp_path / "vault"))


class TestPrivacyVaultConstruction:
    """Tests for vault construction and key management."""

    def test_construction_succeeds(self, vault):
        """The vault must be constructible (it used to raise AttributeError)."""
        assert vault is not None
        assert vault.storage_path.exists()

    def test_master_key_is_persisted(self, tmp_path):
        """The master key is written to disk so the vault survives a restart."""
        path = tmp_path / "vault"
        PrivacyVault(storage_path=str(path))
        assert (path / ".master.key").exists()

    def test_reopening_uses_the_same_key(self, tmp_path):
        """A second instance on the same path can read the first one's entries."""
        path = tmp_path / "vault"
        first = PrivacyVault(storage_path=str(path))
        entry_id = first.store("user-1", {"secret": "value"})

        second = PrivacyVault(storage_path=str(path))
        payload = second.retrieve(entry_id, "user-1")
        assert payload is not None
        assert payload["secret"] == "value"

    def test_index_is_loaded_from_disk(self, tmp_path):
        """The index cache is rebuilt from the on-disk entries."""
        path = tmp_path / "vault"
        first = PrivacyVault(storage_path=str(path))
        entry_id = first.store("user-1", {"a": 1})

        second = PrivacyVault(storage_path=str(path))
        assert entry_id in second._index


class TestPrivacyVaultStore:
    """Tests for storing entries."""

    def test_store_returns_an_entry_id(self, vault):
        entry_id = vault.store("user-1", {"data": "value"})
        assert entry_id.startswith("VAULT-")

    def test_store_writes_a_file_named_after_the_entry(self, vault):
        """The file name must match the id handed back to the caller."""
        entry_id = vault.store("user-1", {"data": "value"})
        assert (vault.storage_path / f"{entry_id}.json").exists()

    def test_stored_entry_records_the_owner(self, vault):
        entry_id = vault.store("user-1", {"data": "value"})
        entry = json.loads((vault.storage_path / f"{entry_id}.json").read_text())
        assert entry["owner_id"] == "user-1"
        assert entry["entry_id"] == entry_id

    def test_stored_ciphertext_does_not_contain_the_plaintext(self, vault):
        """The payload must not be readable from the file."""
        entry_id = vault.store("user-1", {"secret": "clear-text-value"})
        raw = (vault.storage_path / f"{entry_id}.json").read_text()
        assert "clear-text-value" not in raw

    def test_commitment_is_stable(self, vault):
        """The same data always yields the same commitment hash."""
        vault.store("user-1", {"x": 1, "y": 2})
        vault.store("user-1", {"y": 2, "x": 1})
        hashes = {
            json.loads(f.read_text())["commitment_hash"]
            for f in vault.storage_path.glob("*.json")
        }
        assert len(hashes) == 1


class TestPrivacyVaultRetrieve:
    """Tests for retrieving entries."""

    def test_owner_can_retrieve(self, vault):
        entry_id = vault.store("user-1", {"data": "value"})
        payload = vault.retrieve(entry_id, "user-1")
        assert payload is not None
        assert payload["data"] == "value"

    def test_missing_entry_returns_none(self, vault):
        assert vault.retrieve("VAULT-doesnotexist", "user-1") is None

    def test_stranger_cannot_retrieve(self, vault):
        """A non-owner without a grant is refused."""
        entry_id = vault.store("user-1", {"data": "value"})
        assert vault.retrieve(entry_id, "user-2") is None

    def test_auditor_can_retrieve(self, vault):
        """The auditor role is granted by policy."""
        entry_id = vault.store("user-1", {"data": "value"})
        payload = vault.retrieve(entry_id, "auditor-1", requester_role="auditor")
        assert payload is not None
        assert payload["data"] == "value"

    def test_granted_third_party_can_retrieve(self, vault):
        """An explicit grant lets a third party read the entry."""
        entry_id = vault.store("user-1", {"data": "value"})
        vault.grant_access(entry_id, "user-2", granted_by="user-1")
        payload = vault.retrieve(entry_id, "user-2")
        assert payload is not None
        assert payload["data"] == "value"

    def test_access_is_logged(self, vault):
        entry_id = vault.store("user-1", {"data": "value"})
        vault.retrieve(entry_id, "user-1")
        entry = json.loads((vault.storage_path / f"{entry_id}.json").read_text())
        assert any(log["action"] == "read" for log in entry["access_log"])


class TestPrivacyVaultCommitments:
    """Tests for the commitment hash API."""

    def test_verify_commitment_accepts_the_original_data(self, vault):
        data = {"x": 1, "y": 2}
        entry_id = vault.store("user-1", data)
        assert vault.verify_commitment(entry_id, data) is True

    def test_verify_commitment_rejects_tampered_data(self, vault):
        entry_id = vault.store("user-1", {"x": 1})
        assert vault.verify_commitment(entry_id, {"x": 2}) is False

    def test_verify_commitment_on_missing_entry(self, vault):
        assert vault.verify_commitment("VAULT-nope", {"x": 1}) is False

    def test_get_commitment_returns_the_hash(self, vault):
        entry_id = vault.store("user-1", {"x": 1})
        commitment = vault.get_commitment(entry_id)
        assert commitment is not None
        assert len(commitment) == 64  # sha256 hexdigest

    def test_get_commitment_on_missing_entry(self, vault):
        assert vault.get_commitment("VAULT-nope") is None


class TestPrivacyVaultListing:
    """Tests for listing a user's entries."""

    def test_list_returns_only_the_owner_entries(self, vault):
        vault.store("user-1", {"a": 1})
        vault.store("user-1", {"a": 2})
        vault.store("user-2", {"a": 3})

        entries = vault.list_user_entries("user-1")
        assert len(entries) == 2

    def test_list_entries_exposes_metadata_only(self, vault):
        """Listing must not leak the payload."""
        vault.store("user-1", {"secret": "value"}, metadata={"kind": "test"})
        entries = vault.list_user_entries("user-1")
        assert entries[0]["metadata"] == {"kind": "test"}
        assert "secret" not in json.dumps(entries[0])
