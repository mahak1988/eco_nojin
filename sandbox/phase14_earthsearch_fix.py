"""
Phase 14 Earth Search Final Fix
================================
ریشه مشکل: requests.get با query dict → URL-encoded
راه‌حل: requests.post با json body

همچنین: تاریخ‌ها باید در ISO 8601 strict format باشند
"""
from pathlib import Path

FILE = Path(r"D:\eco_nojin\sandbox\phase14_real_data_integration.py")
content = FILE.read_text(encoding="utf-8")
original = content

# ==========================================================================
# PATCH 1: Replace Earth Search request with proper POST + JSON
# ==========================================================================

old_request = '''        try:
            resp = requests.post(cls.URL, json=query, timeout=30)
            resp.raise_for_status()
            data = resp.json()'''

new_request = '''        try:
            # Format datetime in strict ISO 8601 with timezone
            start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Rebuild query with properly formatted datetime
            query["datetime"] = f"{start_iso}/{end_iso}"
            
            # POST request with JSON body (NOT URL-encoded)
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            resp = requests.post(
                cls.URL,
                json=query,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()'''

if old_request in content:
    content = content.replace(old_request, new_request)
    print("✅ Patch 1: Earth Search uses POST + JSON body")
else:
    print("ℹ️  Patch 1: Already applied")

# ==========================================================================
# PATCH 2: Remove redundant datetime in query builder (already handled in try block)
# ==========================================================================

old_datetime_build = '''        # Minimal query (works with v1 endpoint)
        # Note: We fetch more results and sort client-side
        query = {
            "collections": ["sentinel-2-l2a"],
            "datetime": f"{start_date.isoformat()}Z/{end_date.isoformat()}Z",
            "bbox": bbox,
            "limit": 5,
        }'''

new_datetime_build = '''        # Minimal query (works with v1 endpoint)
        # datetime will be formatted properly in try block
        query = {
            "collections": ["sentinel-2-l2a"],
            "bbox": bbox,
            "limit": 10,  # fetch more, filter client-side
        }'''

if old_datetime_build in content:
    content = content.replace(old_datetime_build, new_datetime_build)
    print("✅ Patch 2: Cleaned datetime handling")
else:
    print("ℹ️  Patch 2: Already applied")

# ==========================================================================
# PATCH 3: Add robust error handling with detailed diagnostics
# ==========================================================================

old_error_handling = '''        except Exception as e:
            print(f"⚠️  Earth Search fetch failed: {e}")
            return None'''

new_error_handling = '''        except requests.exceptions.HTTPError as e:
            status = getattr(e.response, 'status_code', 'unknown') if hasattr(e, 'response') else 'unknown'
            detail = ""
            try:
                if hasattr(e, 'response') and e.response is not None:
                    detail = e.response.text[:200]
            except Exception:
                pass
            print(f"⚠️  Earth Search HTTP {status}: {detail}")
            return None
        except Exception as e:
            print(f"⚠️  Earth Search fetch failed: {e}")
            return None'''

if old_error_handling in content:
    content = content.replace(old_error_handling, new_error_handling)
    print("✅ Patch 3: Enhanced error diagnostics")
else:
    print("ℹ️  Patch 3: Already applied")

# ==========================================================================
# PATCH 4: Add fallback to USGS Planetary Computer if Earth Search fails
# ==========================================================================

# Find the end of EarthSearchProvider.fetch_sentinel2 method
# We'll add a fallback strategy in the get_sentinel2 method of RealDataProvider

old_get_sentinel = '''    def get_sentinel2(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"sentinel:{lat:.4f}:{lon:.4f}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.use_real:
            # For demo, we just get metadata (not full imagery)
            metadata = EarthSearchProvider.fetch_sentinel2(lat, lon)
            if metadata:
                # Use mock imagery for now (full COG download in Phase 14b)
                data = get_mock_sentinel2(lat, lon)
                data["source"] = f"sentinel2-metadata:{metadata.get('scene_id', 'unknown')}"
                data["cloud_cover"] = metadata.get("cloud_cover", 0)
                self.cache[cache_key] = data
                return data
        
        return get_mock_sentinel2(lat, lon)'''

new_get_sentinel = '''    def get_sentinel2(self, lat: float, lon: float) -> Dict[str, Any]:
        cache_key = f"sentinel:{lat:.4f}:{lon:.4f}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if self.use_real:
            # Try primary source (Earth Search / Element 84)
            metadata = EarthSearchProvider.fetch_sentinel2(lat, lon)
            
            # Fallback: Use Copernicus Data Space or other sources
            if metadata is None:
                metadata = self._fallback_sentinel_metadata(lat, lon)
            
            if metadata:
                # Use mock imagery for now (full COG download in Phase 14b)
                data = get_mock_sentinel2(lat, lon)
                scene_id = metadata.get('scene_id', 'unknown')
                data["source"] = f"sentinel2-metadata:{scene_id}"
                data["cloud_cover"] = metadata.get("cloud_cover", 0)
                data["metadata"] = metadata
                self.cache[cache_key] = data
                return data
        
        return get_mock_sentinel2(lat, lon)
    
    def _fallback_sentinel_metadata(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Fallback Sentinel-2 metadata from Microsoft Planetary Computer.
        
        Planetary Computer STAC API: https://planetarycomputer.microsoft.com/api/stac/v1
        More stable than Earth Search for programmatic access.
        """
        if not HAS_REQUESTS:
            return None
        
        try:
            from datetime import datetime, timedelta, timezone
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=30)
            
            # Planetary Computer STAC API
            url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
            bbox_size = 0.1
            bbox = [lon - bbox_size, lat - bbox_size,
                    lon + bbox_size, lat + bbox_size]
            
            query = {
                "collections": ["sentinel-2-l2a"],
                "bbox": bbox,
                "datetime": f"{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "limit": 10,
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            resp = requests.post(url, json=query, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            features = data.get("features", [])
            if not features:
                return None
            
            # Sort by datetime client-side
            try:
                features.sort(
                    key=lambda f: f.get("properties", {}).get("datetime", ""),
                    reverse=True
                )
            except Exception:
                pass
            
            # Filter by cloud cover
            scene = None
            for f in features:
                props = f.get("properties", {})
                cloud = props.get("eo:cloud_cover", 
                        props.get("s2:cloud_shadow_percentage",
                        props.get("cloud_cover", 100)))
                if cloud < 20.0:
                    scene = f
                    break
            
            if scene is None:
                scene = features[0]
            
            props = scene.get("properties", {})
            assets = scene.get("assets", {})
            
            return {
                "scene_id": scene.get("id"),
                "acquisition_date": props.get("datetime", ""),
                "cloud_cover": props.get("eo:cloud_cover", 0),
                "source": "planetary-computer-stac",
                "assets": {
                    "B02_blue": assets.get("B02", {}).get("href"),
                    "B03_green": assets.get("B03", {}).get("href"),
                    "B04_red": assets.get("B04", {}).get("href"),
                    "B08_nir": assets.get("B08", {}).get("href"),
                    "B11_swir": assets.get("B11", {}).get("href"),
                },
            }
        except Exception as e:
            print(f"⚠️  Planetary Computer fallback failed: {e}")
            return None'''

if old_get_sentinel in content:
    content = content.replace(old_get_sentinel, new_get_sentinel)
    print("✅ Patch 4: Added Planetary Computer as Sentinel-2 fallback")
else:
    print("ℹ️  Patch 4: Already applied")

# ==========================================================================
# Write
# ==========================================================================

if content != original:
    FILE.write_text(content, encoding="utf-8")
    print(f"\n💾 Updated: {FILE}")
    print("\n🚀 Run: python sandbox\\phase14_real_data_integration.py")
else:
    print("\n⚠️  No changes made")