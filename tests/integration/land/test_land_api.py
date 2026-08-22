"""Integration tests for Land Intelligence API"""

import pytest
from fastapi.testclient import TestClient
from services.api_gateway.main import app
import numpy as np


@pytest.fixture
def client():
    """ایجاد کلاینت تست"""
    return TestClient(app)


class TestLandAPI:
    """تست‌های یکپارچه API زمین"""
    
    def test_health_check(self, client):
        """تست بررسی سلامت"""
        response = client.get("/api/v1/land/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "land"
    
    def test_create_profile(self, client):
        """تست ایجاد پروفایل"""
        response = client.post(
            "/api/v1/land/profiles",
            json={
                "name": "مزرعه تست",
                "location_lat": 32.65,
                "location_lon": 51.67,
                "description": "پروفایل تست",
                "area_hectares": 10.0
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "مزرعه تست"
        assert data["location_lat"] == 32.65
        assert data["location_lon"] == 51.67
        assert "id" in data
    
    def test_list_profiles(self, client):
        """تست لیست پروفایل‌ها"""
        # Create profiles
        client.post("/api/v1/land/profiles", json={
            "name": "پروفایل 1",
            "location_lat": 0,
            "location_lon": 0
        })
        client.post("/api/v1/land/profiles", json={
            "name": "پروفایل 2",
            "location_lat": 0,
            "location_lon": 0
        })
        
        response = client.get("/api/v1/land/profiles")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    def test_get_profile(self, client):
        """تست دریافت پروفایل"""
        # Create profile
        create_response = client.post("/api/v1/land/profiles", json={
            "name": "تست",
            "location_lat": 10.0,
            "location_lon": 20.0
        })
        profile_id = create_response.json()["id"]
        
        # Get profile
        response = client.get(f"/api/v1/land/profiles/{profile_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
        assert data["name"] == "تست"
    
    def test_get_profile_not_found(self, client):
        """تست خطای پروفایل یافت نشد"""
        response = client.get("/api/v1/land/profiles/non-existent")
        
        assert response.status_code == 404
    
    def test_delete_profile(self, client):
        """تست حذف پروفایل"""
        # Create profile
        create_response = client.post("/api/v1/land/profiles", json={
            "name": "حذف",
            "location_lat": 0,
            "location_lon": 0
        })
        profile_id = create_response.json()["id"]
        
        # Delete profile
        response = client.delete(f"/api/v1/land/profiles/{profile_id}")
        
        assert response.status_code == 204
        
        # Verify deleted
        response = client.get(f"/api/v1/land/profiles/{profile_id}")
        assert response.status_code == 404
    
    def test_analyze_terrain(self, client):
        """تست تحلیل توپوگرافی"""
        # Create profile
        create_response = client.post("/api/v1/land/profiles", json={
            "name": "تحلیل",
            "location_lat": 0,
            "location_lon": 0
        })
        profile_id = create_response.json()["id"]
        
        # Create DEM
        dem = [[1000 + i * 10 for j in range(10)] for i in range(10)]
        
        # Analyze terrain
        response = client.post(
            f"/api/v1/land/profiles/{profile_id}/terrain-analysis",
            json={
                "dem_array": dem,
                "resolution": 30.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["profile_id"] == profile_id
        assert "terrain_type" in data
        assert "slope_mean" in data
        assert "elevation_mean" in data
    
    def test_analyze_drainage(self, client):
        """تست تحلیل زهکشی"""
        # Create profile
        create_response = client.post("/api/v1/land/profiles", json={
            "name": "زهکشی",
            "location_lat": 0,
            "location_lon": 0
        })
        profile_id = create_response.json()["id"]
        
        # Create DEM
        dem = [[1000 + i * 10 for j in range(10)] for i in range(10)]
        
        # Analyze drainage
        response = client.post(
            f"/api/v1/land/profiles/{profile_id}/drainage-analysis",
            json={
                "dem_array": dem,
                "resolution": 30.0,
                "area_km2": 1.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["profile_id"] == profile_id
        assert "drainage_pattern" in data
        assert "drainage_density" in data
    
    def test_assess_capability(self, client):
        """تست ارزیابی قابلیت"""
        # Create profile
        create_response = client.post("/api/v1/land/profiles", json={
            "name": "قابلیت",
            "location_lat": 0,
            "location_lon": 0
        })
        profile_id = create_response.json()["id"]
        
        # Assess capability
        response = client.post(
            f"/api/v1/land/profiles/{profile_id}/capability-assessment",
            json={
                "slope_degrees": 10.0,
                "soil_depth_m": 1.5,
                "erosion_risk": "low",
                "drainage_class": "well_drained",
                "climate_zone": "temperate",
                "soil_texture": "loam"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["profile_id"] == profile_id
        assert "capability_class" in data
        assert "suitable_uses" in data
        assert "recommendations" in data
        assert "confidence_score" in data
    
    def test_full_workflow(self, client):
        """تست گردش کار کامل"""
        # 1. Create profile
        response = client.post("/api/v1/land/profiles", json={
            "name": "گردش کار کامل",
            "location_lat": 32.65,
            "location_lon": 51.67,
            "area_hectares": 10.0
        })
        assert response.status_code == 201
        profile_id = response.json()["id"]
        
        # 2. Analyze terrain
        dem = [[1000 + i * 5 for j in range(10)] for i in range(10)]
        response = client.post(
            f"/api/v1/land/profiles/{profile_id}/terrain-analysis",
            json={"dem_array": dem, "resolution": 30.0}
        )
        assert response.status_code == 200
        
        # 3. Analyze drainage
        response = client.post(
            f"/api/v1/land/profiles/{profile_id}/drainage-analysis",
            json={"dem_array": dem, "resolution": 30.0, "area_km2": 1.0}
        )
        assert response.status_code == 200
        
        # 4. Assess capability
        response = client.post(
            f"/api/v1/land/profiles/{profile_id}/capability-assessment",
            json={
                "slope_degrees": 8.0,
                "soil_depth_m": 1.2,
                "erosion_risk": "moderate"
            }
        )
        assert response.status_code == 200
        
        # 5. Get complete profile
        response = client.get(f"/api/v1/land/profiles/{profile_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["terrain_analysis"] is not None
        assert data["drainage_analysis"] is not None
        assert data["capability_assessment"] is not None