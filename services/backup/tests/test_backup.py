"""Tests for backup service and router."""

import pytest

from services.backup.models import BackupConfig, BackupJob
from services.backup.schemas import BackupConfigCreate, BackupConfigResponse, BackupConfigUpdate


class TestBackupModels:
    """Tests for backup models."""

    def test_backup_config_model_creation(self):
        """Test creating a BackupConfig model instance."""
        config = BackupConfig(
            name="Daily Backup",
            description="Daily database backup",
            schedule_cron="0 2 * * *",
            retention_days=30,
            storage_backend="s3",
            storage_config={"bucket": "backups", "prefix": "daily/"},
            enabled=True,
        )
        assert config.name == "Daily Backup"
        assert config.schedule_cron == "0 2 * * *"
        assert config.retention_days == 30

    def test_backup_job_model_creation(self):
        """Test creating a BackupJob model instance."""
        job = BackupJob(
            config_id="test-config-id",
            backup_type="full",
            status="pending",
            databases=["db1", "db2"],
            size_bytes=0,
        )
        assert job.config_id == "test-config-id"
        assert job.status == "pending"
        assert job.backup_type == "full"
        assert job.databases == ["db1", "db2"]


class TestBackupSchemas:
    """Tests for backup schemas."""

    def test_backup_config_create_schema(self):
        """Test BackupConfigCreate schema validation."""
        data = BackupConfigCreate(
            name="Weekly Backup",
            description="Weekly full backup",
            schedule_cron="0 3 * * 0",
            retention_days=90,
            storage_backend="s3",
            storage_config={"bucket": "backups", "prefix": "weekly/"},
            enabled=True,
        )
        assert data.name == "Weekly Backup"
        assert data.schedule_cron == "0 3 * * 0"

    def test_backup_config_update_schema(self):
        """Test BackupConfigUpdate schema."""
        data = BackupConfigUpdate(
            name="Updated Backup",
            retention_days=60,
        )
        assert data.name == "Updated Backup"
        assert data.retention_days == 60

    def test_backup_config_response_schema(self):
        """Test BackupConfigResponse schema."""
        from datetime import datetime
        data = BackupConfigResponse(
            id="test-id",
            name="Test",
            description="Desc",
            backup_type="full",
            databases=[],
            schedule_cron="0 2 * * *",
            timezone="UTC",
            retention_days=30,
            max_backups=100,
            storage_backend="local",
            storage_path="./backups",
            compression="gzip",
            encryption_enabled=False,
            verify_after_backup=True,
            verify_checksum=True,
            notify_on_success=False,
            notify_on_failure=True,
            enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert data.id == "test-id"
        assert data.name == "Test"


class TestBackupService:
    """Tests for BackupService (requires database)."""

    @pytest.fixture
    def service(self, db_session):
        from services.backup.service import BackupService
        return BackupService(db_session)

    async def test_service_instantiation(self, service):
        """Test that service can be instantiated."""
        assert service is not None
        assert hasattr(service, 'create_config')
        assert hasattr(service, 'get_config')
        assert hasattr(service, 'list_configs')

    async def test_create_config(self, service):
        """Test creating a backup config."""
        config_data = {
            "name": "Test Config",
            "description": "Test backup config",
            "schedule_cron": "0 4 * * *",
            "retention_days": 14,
            "storage_backend": "local",
            "storage_config": {"path": "/tmp/backups"},
            "enabled": True,
        }
        config = await service.create_config(
            BackupConfigCreate(**config_data),
            user_id="test-user",
        )
        assert config is not None
        assert config.name == "Test Config"
        assert config.schedule_cron == "0 4 * * *"
    async def test_get_config(self, service):
        """Test retrieving a backup config."""
        config_data = {
            "name": "Test Config 2",
            "schedule_cron": "0 5 * * *",
            "retention_days": 7,
            "storage_backend": "s3",
            "storage_config": {"bucket": "test-bucket"},
            "enabled": True,
        }
        created = await service.create_config(
            BackupConfigCreate(**config_data), user_id="test-user"
        )
        retrieved = await service.get_config(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    async def test_list_configs(self, service):
        """Test listing backup configs."""
        configs = await service.list_configs(page=1, page_size=10)
        assert isinstance(configs, list)


class TestBackupRouter:
    """Tests for backup router endpoints."""

    def test_router_exists(self):
        """Test that router is defined."""
        from services.backup.router import router as backup_router
        assert backup_router is not None