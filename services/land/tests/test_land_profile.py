from services.land.land_profile import LandProfileCreateRequest, calculate_land_profile


def test_calculate_land_profile():
    """Test the basic land profile calculation."""
    request = LandProfileCreateRequest(
        project_id="test-project-123",
        latitude=35.6892,
        longitude=51.3890,
        area_hectares=50.0
    )

    profile = calculate_land_profile(request)

    assert profile.id is not None
    assert profile.project_id == "test-project-123"
    assert profile.location["lat"] == 35.6892
    assert profile.location["lng"] == 51.3890
    assert profile.area_hectares == 50.0
    assert profile.elevation_min is not None
    assert profile.elevation_mean is not None
    assert profile.slope_mean_degrees is not None
    assert profile.created_at is not None

    print("Land profile calculation test passed!")
    print(f"Generated Profile ID: {profile.id}")
    print(f"Elevation Range: {profile.elevation_min} - {profile.elevation_max} m")
    print(f"Mean Slope: {profile.slope_mean_degrees} degrees")
