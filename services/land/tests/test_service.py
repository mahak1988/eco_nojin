"""Tests for Land Intelligence Service"""

import numpy as np
import pytest

from services.land.service import LandService


class TestLandService:
    """تست‌های سرویس تحلیل زمین"""

    @pytest.fixture
    def service(self):
        """ایجاد سرویس"""
        return LandService()

    @pytest.fixture
    def sample_dem(self):
        """DEM نمونه"""
        dem = np.zeros((10, 10))
        for i in range(10):
            dem[i, :] = 1000 + i * 10
        return dem

    def test_create_profile(self, service):
        """تست ایجاد پروفایل"""
        profile = service.create_profile(
            name="مزرعه نمونه",
            location_lat=32.65,
            location_lon=51.67,
            description="تست",
            area_hectares=10.0
        )

        assert profile.id is not None
        assert profile.name == "مزرعه نمونه"
        assert profile.location_lat == 32.65
        assert profile.location_lon == 51.67

    def test_get_profile(self, service):
        """تست دریافت پروفایل"""
        profile = service.create_profile(
            name="تست",
            location_lat=0,
            location_lon=0
        )

        retrieved = service.get_profile(profile.id)
        assert retrieved is not None
        assert retrieved.id == profile.id

        # Non-existent
        assert service.get_profile("non-existent") is None

    def test_list_profiles(self, service):
        """تست لیست پروفایل‌ها"""
        service.create_profile(name="1", location_lat=0, location_lon=0)
        service.create_profile(name="2", location_lat=0, location_lon=0)
        service.create_profile(name="3", location_lat=0, location_lon=0)

        profiles = service.list_profiles()
        assert len(profiles) == 3

    def test_analyze_terrain(self, service, sample_dem):
        """تست تحلیل توپوگرافی"""
        profile = service.create_profile(
            name="تست",
            location_lat=0,
            location_lon=0
        )

        analysis = service.analyze_terrain(
            profile_id=profile.id,
            dem_array=sample_dem,
            resolution=30.0
        )

        assert analysis.profile_id == profile.id
        assert analysis.terrain_type is not None

        # Check profile was updated
        updated_profile = service.get_profile(profile.id)
        assert updated_profile.terrain_analysis is not None

    def test_analyze_drainage(self, service, sample_dem):
        """تست تحلیل زهکشی"""
        profile = service.create_profile(
            name="تست",
            location_lat=0,
            location_lon=0
        )

        analysis = service.analyze_drainage(
            profile_id=profile.id,
            dem_array=sample_dem,
            resolution=30.0,
            area_km2=1.0
        )

        assert analysis.profile_id == profile.id
        assert analysis.drainage_pattern is not None

        # Check profile was updated
        updated_profile = service.get_profile(profile.id)
        assert updated_profile.drainage_analysis is not None

    def test_assess_capability(self, service):
        """تست ارزیابی قابلیت"""
        profile = service.create_profile(
            name="تست",
            location_lat=0,
            location_lon=0
        )

        assessment = service.assess_capability(
            profile_id=profile.id,
            slope_degrees=10.0,
            soil_depth_m=1.5,
            erosion_risk="low",
            drainage_class="well_drained",
            climate_zone="temperate"
        )

        assert assessment.profile_id == profile.id
        assert assessment.capability_class is not None
        assert assessment.confidence_score > 0

        # Check profile was updated
        updated_profile = service.get_profile(profile.id)
        assert updated_profile.capability_assessment is not None

    def test_delete_profile(self, service):
        """تست حذف پروفایل"""
        profile = service.create_profile(
            name="تست",
            location_lat=0,
            location_lon=0
        )

        assert service.delete_profile(profile.id) is True
        assert service.get_profile(profile.id) is None
        assert service.delete_profile("non-existent") is False

    def test_profile_not_found(self, service, sample_dem):
        """تست خطای پروفایل یافت نشد"""
        with pytest.raises(ValueError, match="Profile not found"):
            service.analyze_terrain(
                profile_id="non-existent",
                dem_array=sample_dem,
                resolution=30.0
            )

        with pytest.raises(ValueError, match="Profile not found"):
            service.analyze_drainage(
                profile_id="non-existent",
                dem_array=sample_dem,
                resolution=30.0
            )

        with pytest.raises(ValueError, match="Profile not found"):
            service.assess_capability(
                profile_id="non-existent",
                slope_degrees=10.0
            )
