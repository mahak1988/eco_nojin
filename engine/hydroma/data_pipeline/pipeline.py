"""
Data Pipeline for Eco Nojin
============================

Provides infrastructure for:
- Data versioning with DVC
- STAC catalog management
- External data source connectors
- Pipeline orchestration
- Provenance tracking
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """External data source configuration."""

    source_id: str
    name: str
    description: str
    base_url: str
    auth_type: str = "none"  # none, api_key, oauth2, basic
    auth_config: dict[str, Any] = field(default_factory=dict)
    rate_limit: int | None = None  # requests per minute
    format: str = "json"  # json, netcdf, geotiff, csv, stac
    bbox: list[float] | None = None  # [minx, miny, maxx, maxy]
    temporal_extent: list[str] | None = None  # [start, end]
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataAsset:
    """Represents a data asset in the pipeline."""

    asset_id: str
    source_id: str
    name: str
    description: str
    file_path: Path
    format: str
    size_bytes: int
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "source_id": self.source_id,
            "name": self.name,
            "description": self.description,
            "file_path": str(self.file_path),
            "format": self.format,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "metadata": self.metadata,
            "provenance": self.provenance,
            "created_at": self.created_at,
            "tags": self.tags,
        }


class DataConnector(ABC):
    """Abstract base class for data connectors."""

    @abstractmethod
    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch data matching query."""
        pass

    @abstractmethod
    def validate(self, asset: DataAsset) -> bool:
        """Validate data asset."""
        pass


class OpenMeteoConnector(DataConnector):
    """Connector for Open-Meteo ERA5 data."""

    def __init__(self, cache_dir: Path = Path("data/cache/open_meteo")):
        self.source = DataSource(
            source_id="open_meteo",
            name="Open-Meteo ERA5",
            description="ERA5 reanalysis data via Open-Meteo API",
            base_url="https://api.open-meteo.com/v1/era5",
            auth_type="none",
            format="json",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch ERA5 data for given bbox and time range."""
        import requests

        bbox = query.get("bbox", [0, 0, 10, 10])
        start_date = query.get("start_date", "2020-01-01")
        end_date = query.get("end_date", "2020-12-31")
        variables = query.get("variables", ["temperature_2m", "precipitation"])

        params = {
            "latitude": (bbox[1] + bbox[3]) / 2,
            "longitude": (bbox[0] + bbox[2]) / 2,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(variables),
            "timezone": "UTC",
        }

        response = requests.get(self.source.base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Save to cache
        asset_id = f"era5_{hashlib.md5(str(params).encode()).hexdigest()[:8]}"
        file_path = self.cache_dir / f"{asset_id}.json"
        file_path.write_text(json.dumps(data))

        asset = DataAsset(
            asset_id=asset_id,
            source_id=self.source.source_id,
            name=f"ERA5 {start_date} to {end_date}",
            description=f"ERA5 reanalysis for bbox {bbox}",
            file_path=file_path,
            format="json",
            size_bytes=file_path.stat().st_size,
            checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
            metadata={
                "bbox": bbox,
                "start_date": start_date,
                "end_date": end_date,
                "variables": variables,
            },
            provenance={
                "source_url": self.source.base_url,
                "query_params": params,
                "fetched_at": datetime.now(UTC).isoformat(),
            },
        )

        return [asset]

    def validate(self, asset: DataAsset) -> bool:
        """Validate ERA5 data asset."""
        if not asset.file_path.exists():
            return False
        try:
            data = json.loads(asset.file_path.read_text())
            return "hourly" in data
        except Exception:
            return False


class NASA_POWER_Connector(DataConnector):
    """Connector for NASA POWER data."""

    def __init__(self, cache_dir: Path = Path("data/cache/nasa_power")):
        self.source = DataSource(
            source_id="nasa_power",
            name="NASA POWER",
            description="NASA Prediction of Worldwide Energy Resources",
            base_url="https://power.larc.nasa.gov/api/temporal/daily/point",
            auth_type="none",
            format="json",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch NASA POWER data."""
        import requests

        lat = query.get("lat", 0)
        lon = query.get("lon", 0)
        start = query.get("start_date", "2020-01-01")
        end = query.get("end_date", "2020-12-31")
        params = query.get("parameters", ["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"])

        url = f"{self.source.base_url}?parameters={','.join(params)}&community=AG&longitude={lon}&latitude={lat}&start={start}&end={end}&format=JSON"

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        asset_id = f"nasa_power_{lat}_{lon}_{start}_{end}"
        file_path = self.cache_dir / f"{asset_id}.json"
        file_path.write_text(json.dumps(data))

        return [
            DataAsset(
                asset_id=asset_id,
                source_id=self.source.source_id,
                name=f"NASA POWER {lat},{lon} {start}-{end}",
                description="NASA POWER daily data",
                file_path=file_path,
                format="json",
                size_bytes=file_path.stat().st_size,
                checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                provenance={"source_url": url, "fetched_at": datetime.now(UTC).isoformat()},
            )
        ]

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            data = json.loads(asset.file_path.read_text())
            return "properties" in data
        except Exception:
            return False


class SoilGridsConnector(DataConnector):
    """Connector for ISRIC SoilGrids v2.0."""

    def __init__(self, cache_dir: Path = Path("data/cache/soilgrids")):
        self.source = DataSource(
            source_id="soilgrids",
            name="ISRIC SoilGrids v2.0",
            description="Global soil property maps at 250m resolution",
            base_url="https://rest.isric.org/soilgrids/v2.0/properties/query",
            auth_type="none",
            format="geotiff",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch SoilGrids data for bbox."""
        import requests

        bbox = query.get("bbox", [0, 0, 1, 1])
        properties = query.get(
            "properties", ["bdod", "cec", "clay", "sand", "silt", "phh2o", "soc", "nitrogen"]
        )
        depths = query.get(
            "depths", ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]
        )

        assets = []
        for prop in properties:
            for depth in depths:
                params = {
                    "lon": (bbox[0] + bbox[2]) / 2,
                    "lat": (bbox[1] + bbox[3]) / 2,
                    "property": prop,
                    "depth": depth,
                    "value": "mean",
                }

                response = requests.get(self.source.base_url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()

                    asset_id = f"soilgrids_{prop}_{depth}_{bbox[0]}_{bbox[1]}"
                    file_path = self.cache_dir / f"{asset_id}.json"
                    file_path.write_text(json.dumps(data))

                    assets.append(
                        DataAsset(
                            asset_id=asset_id,
                            source_id=self.source.source_id,
                            name=f"SoilGrids {prop} {depth}",
                            description=f"SoilGrids {prop} at {depth}",
                            file_path=file_path,
                            format="json",
                            size_bytes=file_path.stat().st_size,
                            checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                            provenance={"source_url": self.source.base_url, "params": params},
                        )
                    )

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            data = json.loads(asset.file_path.read_text())
            return "properties" in data
        except Exception:
            return False


class STACConnector(DataConnector):
    """Connector for STAC (SpatioTemporal Asset Catalog) APIs."""

    def __init__(
        self,
        catalog_url: str,
        source_id: str,
        name: str,
        cache_dir: Path = Path("data/cache/stac"),
        auth_type: str = "none",
        auth_config: dict[str, Any] | None = None,
        collections: list[str] | None = None,
    ):
        self.catalog_url = catalog_url.rstrip("/")
        self.source = DataSource(
            source_id=source_id,
            name=name,
            description=f"STAC catalog: {catalog_url}",
            base_url=catalog_url,
            auth_type=auth_type,
            format="stac",
            auth_config=auth_config or {},
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.collections = collections or []

    def search(
        self,
        bbox: list[float],
        datetime_range: str,
        collections: list[str],
        limit: int = 100,
        query: dict[str, Any] | None = None,
        sortby: list[dict[str, str]] | None = None,
    ) -> list[dict]:
        """Search STAC catalog with optional query filters and sorting."""
        import requests

        url = f"{self.catalog_url}/search"
        payload: dict[str, Any] = {
            "bbox": bbox,
            "datetime": datetime_range,
            "collections": collections,
            "limit": limit,
        }
        if query:
            payload["query"] = query
        if sortby:
            payload["sortby"] = sortby

        headers: dict[str, str] = {}
        if self.source.auth_type == "oauth2":
            token = self._get_oauth2_token()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif self.source.auth_type == "api_key" and self.source.auth_config.get("api_key"):
            headers["Authorization"] = f"Bearer {self.source.auth_config['api_key']}"

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json().get("features", [])

    def _get_oauth2_token(self) -> str | None:
        """Fetch OAuth2 token from CDSE identity endpoint."""
        import requests

        identity_url = self.source.auth_config.get("identity_url", "")
        client_id = self.source.auth_config.get("client_id", "")
        client_secret = self.source.auth_config.get("client_secret", "")
        if not all([identity_url, client_id, client_secret]):
            return None
        try:
            resp = requests.post(
                f"{identity_url}/auth/realms/cdse/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")
        except Exception:
            return None
        return None

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch STAC items."""
        items = self.search(
            bbox=query.get("bbox", [0, 0, 10, 10]),
            datetime_range=query.get("datetime", "2020-01-01/2020-12-31"),
            collections=query.get("collections", ["sentinel-2-l2a"]),
            limit=query.get("limit", 10),
            query=query.get("query"),
            sortby=query.get("sortby"),
        )

        assets = []
        for item in items:
            asset_id = item["id"]
            file_path = self.cache_dir / f"{asset_id}.json"
            file_path.write_text(json.dumps(item))

            assets.append(
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=item["id"],
                    description=item.get("description", ""),
                    file_path=file_path,
                    format="stac",
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    provenance={"stac_item": item, "fetched_at": datetime.now(UTC).isoformat()},
                )
            )

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            data = json.loads(asset.file_path.read_text())
            return "stac_version" in data or "type" in data
        except Exception:
            return False


class CHIRPSConnector(DataConnector):
    """CHIRPS daily precipitation (0.05°, 1981-present, free)."""

    def __init__(self, cache_dir: Path = Path("data/cache/chirps")):
        self.source = DataSource(
            source_id="chirps",
            name="CHIRPS v2.0",
            description="Climate Hazards Group InfraRed Precipitation with Stations",
            base_url="https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf",
            auth_type="none",
            format="netcdf",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _monthly_url(self, year: int, month: int) -> str:
        """Build URL for CHIRPS monthly NetCDF file."""
        return f"{self.source.base_url}/chirps-v2.0.{year}.{month:02d}.days_p05.nc"

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch CHIRPS precipitation data for bbox and date range.

        query: {
            "bbox": [lon_min, lat_min, lon_max, lat_max],
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
        }
        """
        from datetime import datetime

        import requests
        import xarray as xr

        bbox = query.get("bbox", [-180, -50, 180, 50])
        start_date = query.get("start_date", "2020-01-01")
        end_date = query.get("end_date", "2020-12-31")

        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)

        assets = []
        current = start_dt.replace(day=1)
        while current <= end_dt:
            year, month = current.year, current.month
            url = self._monthly_url(year, month)

            try:
                response = requests.get(url, timeout=60, stream=True)
                response.raise_for_status()

                # Download to temp file
                with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    tmp_path = tmp.name

                # Subset to bbox and save subset
                ds = xr.open_dataset(tmp_path)
                precip = ds["precip"]

                # Subset spatial
                lon_min, lat_min, lon_max, lat_max = bbox
                subset = precip.sel(
                    longitude=slice(lon_min, lon_max),
                    latitude=slice(lat_max, lat_min),  # latitude descending
                )

                # Save subset
                asset_id = (
                    f"chirps_{year}_{month:02d}_{hashlib.md5(str(bbox).encode()).hexdigest()[:8]}"
                )
                file_path = self.cache_dir / f"{asset_id}.nc"
                subset.to_netcdf(file_path)

                assets.append(
                    DataAsset(
                        asset_id=asset_id,
                        source_id=self.source.source_id,
                        name=f"CHIRPS {year}-{month:02d}",
                        description=f"CHIRPS daily precipitation for bbox {bbox}",
                        file_path=file_path,
                        format="netcdf",
                        size_bytes=file_path.stat().st_size,
                        checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                        metadata={
                            "bbox": bbox,
                            "year": year,
                            "month": month,
                            "variable": "precipitation",
                            "units": "mm/day",
                        },
                        provenance={
                            "source_url": url,
                            "fetched_at": datetime.now(UTC).isoformat(),
                            "citation": "Funk et al. 2015, CHIRPS v2.0",
                        },
                    )
                )

                ds.close()
                os.unlink(tmp_path)

            except Exception as e:
                logger.warning(f"CHIRPS fetch failed for {year}-{month:02d}: {e}")
                continue

            # Next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            import xarray as xr

            ds = xr.open_dataset(asset.file_path)
            return "precip" in ds.data_vars
        except Exception:
            return False


class WorldClimConnector(DataConnector):
    """WorldClim v2.1 / CHELSA v2.1 climatology baselines (static GeoTIFF)."""

    def __init__(self, cache_dir: Path = Path("data/cache/worldclim"), dataset: str = "worldclim"):
        self.dataset = dataset
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if dataset == "worldclim":
            self.source = DataSource(
                source_id="worldclim",
                name="WorldClim v2.1",
                description="WorldClim 2.1 climate normals (1970-2000) at 30-sec resolution",
                base_url="https://worldclim.org/data/worldclim21_30s.zip",
                auth_type="none",
                format="geotiff",
            )
            self.variables = {
                "tmin": "wc2.1_30s_tmin",
                "tmax": "wc2.1_30s_tmax",
                "prec": "wc2.1_30s_prec",
                "srad": "wc2.1_30s_srad",
                "bio": "wc2.1_30s_bio",
            }
        else:  # chelsa
            self.source = DataSource(
                source_id="chelsa",
                name="CHELSA v2.1",
                description="CHELSA 2.1 climate normals (1981-2010) at 30-sec resolution",
                base_url="https://os.zhdk.cloud.switch.ch/envicloud/chelsa/chelsa_V2/GLOBAL",
                auth_type="none",
                format="geotiff",
            )
            self.variables = {
                "tmin": "CHELSA_tmin",
                "tmax": "CHELSA_tmax",
                "prec": "CHELSA_prec",
                "bio": "CHELSA_bio",
            }

    def _variable_urls(self, variable: str) -> list[str]:
        """Return list of monthly/annual URLs for a variable."""
        if self.dataset == "worldclim":
            # WorldClim provides single zip with all months
            return [self.source.base_url]
        else:
            # CHELSA: one file per month for most variables
            urls = []
            base = self.source.base_url
            if variable in ["tmin", "tmax", "prec"]:
                for m in range(1, 13):
                    urls.append(f"{base}/CHELSA_{variable}_{m:02d}_1981-2010_V2.1.tif")
            elif variable == "bio":
                for b in range(1, 20):
                    urls.append(f"{base}/CHELSA_bio{b:02d}_1981-2010_V2.1.tif")
            return urls

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch WorldClim/CHELSA climatology for bbox.

        query: {
            "bbox": [lon_min, lat_min, lon_max, lat_max],
            "variables": ["tmin", "tmax", "prec", "bio"],  # optional
        }
        """
        import rasterio
        import requests
        from rasterio.windows import from_bounds

        bbox = query.get("bbox", [-180, -90, 180, 90])
        variables = query.get("variables", list(self.variables.keys()))

        assets = []
        for var in variables:
            if var not in self.variables:
                continue

            urls = self._variable_urls(var)
            for url in urls:
                try:
                    # Download file
                    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                        resp = requests.get(url, timeout=120, stream=True)
                        resp.raise_for_status()
                        for chunk in resp.iter_content(chunk_size=8192):
                            tmp.write(chunk)
                        tmp_path = tmp.name

                    # Subset to bbox
                    with rasterio.open(tmp_path) as src:
                        window = from_bounds(*bbox, src.transform)
                        data = src.read(1, window=window)
                        profile = src.profile
                        profile.update(
                            {
                                "width": window.width,
                                "height": window.height,
                                "transform": rasterio.windows.transform(window, src.transform),
                            }
                        )

                    # Save subset
                    filename = os.path.basename(url).replace(
                        ".tif", f"_{hashlib.md5(str(bbox).encode()).hexdigest()[:8]}.tif"
                    )
                    file_path = self.cache_dir / filename
                    with rasterio.open(file_path, "w", **profile) as dst:
                        dst.write(data, 1)

                    assets.append(
                        DataAsset(
                            asset_id=f"{self.source.source_id}_{var}_{os.path.basename(url)}",
                            source_id=self.source.source_id,
                            name=f"{self.source.name} {var}",
                            description=f"{self.source.name} {var} for bbox {bbox}",
                            file_path=file_path,
                            format="geotiff",
                            size_bytes=file_path.stat().st_size,
                            checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                            metadata={
                                "bbox": bbox,
                                "variable": var,
                                "dataset": self.dataset,
                                "source_file": url,
                            },
                            provenance={
                                "source_url": url,
                                "fetched_at": datetime.now(UTC).isoformat(),
                            },
                        )
                    )

                    os.unlink(tmp_path)

                except Exception as e:
                    logger.warning(f"WorldClim/CHELSA fetch failed for {url}: {e}")
                    continue

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            import rasterio

            with rasterio.open(asset.file_path) as src:
                return src.width > 0 and src.height > 0
        except Exception:
            return False


class NCEPReanalysisConnector(DataConnector):
    """NOAA NCEP/NCAR Reanalysis-1 (1948-present, free OpenDAP)."""

    def __init__(self, cache_dir: Path = Path("data/cache/ncep_reanalysis")):
        self.source = DataSource(
            source_id="ncep_reanalysis",
            name="NCEP/NCAR Reanalysis-1",
            description="Global atmospheric reanalysis at 2.5° resolution (1948-present)",
            base_url="https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.derived",
            auth_type="none",
            format="netcdf",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.variable_map = {
            "air": "surface_gauss/air.mon.ltm.nc",  # surface air temp
            "slp": "surface_gauss/slp.mon.ltm.nc",  # sea level pressure
            "pr_wtr": "surface_gauss/pr_wtr.eatm.nc",  # precipitable water
            "uwnd": "surface_gauss/uwnd.mon.ltm.nc",  # zonal wind
            "vwnd": "surface_gauss/vwnd.mon.ltm.nc",  # meridional wind
            "rhum": "surface_gauss/rhum.mon.ltm.nc",  # relative humidity
        }

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch NCEP Reanalysis data via OpenDAP.

        query: {
            "bbox": [lon_min, lat_min, lon_max, lat_max],
            "variables": ["air", "slp", "pr_wtr", "uwnd", "vwnd", "rhum"],
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
        }
        """
        import xarray as xr

        bbox = query.get("bbox", [-180, -90, 180, 90])
        variables = query.get("variables", list(self.variable_map.keys()))
        start_date = query.get("start_date", "2020-01-01")
        end_date = query.get("end_date", "2020-12-31")

        assets = []
        lon_min, lat_min, lon_max, lat_max = bbox

        for var in variables:
            if var not in self.variable_map:
                continue

            url = f"{self.source.base_url}/{self.variable_map[var]}"

            try:
                ds = xr.open_dataset(url)
                data_var = ds[var]

                # Subset spatial (NCEP uses 0-360 lon, convert if needed)
                if lon_max > 180:
                    lon_min_sel, lon_max_sel = lon_min, lon_max
                else:
                    lon_min_sel = lon_min if lon_min >= 0 else lon_min + 360
                    lon_max_sel = lon_max if lon_max >= 0 else lon_max + 360

                subset = data_var.sel(
                    lon=slice(lon_min_sel, lon_max_sel),
                    lat=slice(lat_max, lat_min),  # lat descending
                    time=slice(start_date, end_date),
                )

                asset_id = f"ncep_{var}_{start_date}_{end_date}_{hashlib.md5(str(bbox).encode()).hexdigest()[:8]}"
                file_path = self.cache_dir / f"{asset_id}.nc"
                subset.to_netcdf(file_path)

                assets.append(
                    DataAsset(
                        asset_id=asset_id,
                        source_id=self.source.source_id,
                        name=f"NCEP Reanalysis-1 {var}",
                        description=f"NCEP Reanalysis {var} for bbox {bbox} ({start_date} to {end_date})",
                        file_path=file_path,
                        format="netcdf",
                        size_bytes=file_path.stat().st_size,
                        checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                        metadata={
                            "bbox": bbox,
                            "variable": var,
                            "start_date": start_date,
                            "end_date": end_date,
                            "resolution": "2.5°",
                        },
                        provenance={
                            "source_url": url,
                            "fetched_at": datetime.now(UTC).isoformat(),
                            "citation": "Kalnay et al. 1996, NCEP/NCAR Reanalysis-1",
                        },
                    )
                )

            except Exception as e:
                logger.warning(f"NCEP fetch failed for {var}: {e}")
                continue

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            import xarray as xr

            ds = xr.open_dataset(asset.file_path)
            return len(ds.data_vars) > 0
        except Exception:
            return False


class OpenMeteoSeasonalConnector(DataConnector):
    """Open-Meteo Seasonal forecasts & CMIP6 projections (free, no key)."""

    def __init__(self, cache_dir: Path = Path("data/cache/open_meteo_seasonal")):
        self.source = DataSource(
            source_id="open_meteo_seasonal",
            name="Open-Meteo Seasonal / CMIP6",
            description="Seasonal forecasts and CMIP6 climate projections via Open-Meteo",
            base_url="https://climate-api.open-meteo.com/v1/climate",
            auth_type="none",
            format="json",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch seasonal/CMIP6 data.

        query: {
            "bbox": [lon_min, lat_min, lon_max, lat_max],
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "scenario": "ssp126|ssp245|ssp585|historical",  # for CMIP6
            "variables": ["temperature_2m", "precipitation", ...],
            "models": ["EC-Earth3", "MPI-ESM1-2-LR", ...],  # optional
        }
        """
        import requests

        bbox = query.get("bbox", [0, 0, 10, 10])
        start_date = query.get("start_date", "2020-01-01")
        end_date = query.get("end_date", "2030-12-31")
        scenario = query.get("scenario", "ssp245")
        variables = query.get("variables", ["temperature_2m", "precipitation"])
        models = query.get("models", [])

        lat = (bbox[1] + bbox[3]) / 2
        lon = (bbox[0] + bbox[2]) / 2

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join(variables),
            "climate_scenario": scenario,
            "timezone": "UTC",
        }
        if models:
            params["models"] = ",".join(models)

        try:
            response = requests.get(self.source.base_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            asset_id = f"open_meteo_seasonal_{scenario}_{start_date}_{end_date}_{hashlib.md5(str(bbox).encode()).hexdigest()[:8]}"
            file_path = self.cache_dir / f"{asset_id}.json"
            file_path.write_text(json.dumps(data))

            return [
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"Open-Meteo {scenario} {start_date} to {end_date}",
                    description=f"CMIP6/Seasonal {scenario} for ({lat:.2f}, {lon:.2f})",
                    file_path=file_path,
                    format="json",
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "bbox": bbox,
                        "scenario": scenario,
                        "start_date": start_date,
                        "end_date": end_date,
                        "variables": variables,
                        "models": models,
                    },
                    provenance={
                        "source_url": self.source.base_url,
                        "query_params": params,
                        "fetched_at": datetime.now(UTC).isoformat(),
                    },
                )
            ]

        except Exception as e:
            logger.warning(f"Open-Meteo Seasonal fetch failed: {e}")
            return []

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            data = json.loads(asset.file_path.read_text())
            return "daily" in data or "daily_units" in data
        except Exception:
            return False


class CGLSConnector(DataConnector):
    """Copernicus Global Land Service (CGLS) products connector.

    ⚠️ IMPORTANT LIMITATION: The standard CGLS biophysical variables
    (LAI, FAPAR, NDVI, VCI, DMP) require Sentinel Hub authentication
    and are NOT available via keyless access.

    This connector provides access to the CGLS Lake Water Quality (LWQ)
    products that ARE available keyless via Digital Earth Africa S3:
    - LWQ300: Lake water quality at 300m (2002-2024)
    - LWQ100: Lake water quality at 100m (2019-2024)
    - Near-real-time (NRT) products

    Variables include: water reflectance (Rw620, Rw767), last observation.
    Source: DE Africa S3 bucket 'deafrica-input-datasets' (free, no key).
    """

    LWQ_PRODUCTS = {
        "lwq300_2016_2024": {
            "name": "LWQ300 2016-2024",
            "resolution": "300m",
            "bucket": "cgls_lwq300_2016_2024",
        },
        "lwq300_2002_2012": {
            "name": "LWQ300 2002-2012",
            "resolution": "300m",
            "bucket": "cgls_lwq300_2002_2012",
        },
        "lwq300_2024_nrt": {
            "name": "LWQ300 NRT",
            "resolution": "300m",
            "bucket": "cgls_lwq300_2024_nrt",
        },
        "lwq100_2019_2024": {
            "name": "LWQ100 2019-2024",
            "resolution": "100m",
            "bucket": "cgls_lwq100_2019_2024",
        },
        "lwq100_2024_nrt": {
            "name": "LWQ100 NRT",
            "resolution": "100m",
            "bucket": "cgls_lwq100_2024_nrt",
        },
    }

    def __init__(self, cache_dir: Path = Path("data/cache/cgls")):
        self.source = DataSource(
            source_id="cgls",
            name="Copernicus Global Land Service (LWQ - keyless)",
            description="CGLS Lake Water Quality products via DE Africa S3 (keyless). Standard biophysical vars (LAI, FAPAR, NDVI, VCI, DMP) require Sentinel Hub auth.",
            base_url="https://deafrica-input-datasets.s3.af-south-1.amazonaws.com",
            auth_type="none",
            format="geotiff",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.s3_bucket = "deafrica-input-datasets"
        self.region = "af-south-1"

    def _list_tiles(self, bucket_prefix: str) -> list[str]:
        """List available x/y tiles for a product bucket."""
        import boto3
        from botocore import UNSIGNED
        from botocore.config import Config

        s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED), region_name=self.region)
        paginator = s3.get_paginator("list_objects_v2")

        tiles = set()
        for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=bucket_prefix, Delimiter="/"):
            for cp in page.get("CommonPrefixes", []):
                prefix = cp["Prefix"]
                # Extract x tile prefix (e.g., x015/)
                parts = prefix.rstrip("/").split("/")
                # prefix is like "cgls_lwq300_2016_2024/x015/"
                # We want the x tile part (second element after split)
                if len(parts) >= 2 and parts[1].startswith("x"):
                    tiles.add(parts[1])

        return sorted(tiles)

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch CGLS Lake Water Quality data.

        query: {
            "bbox": [lon_min, lat_min, lon_max, lat_max],  # optional
            "product": "lwq300_2016_2024|lwq300_2002_2012|lwq300_2024_nrt|lwq100_2019_2024|lwq100_2024_nrt",
            "variables": ["Rw620_rep", "Rw767_rep", "last_obs"],  # optional
            "start_date": "YYYY-MM-DD",  # optional
            "end_date": "YYYY-MM-DD",  # optional
        }

        Note: Standard CGLS biophysical variables (LAI, FAPAR, NDVI, VCI, DMP)
        require Sentinel Hub authentication and are NOT available via this connector.
        """
        import os

        import boto3
        from botocore import UNSIGNED
        from botocore.config import Config

        product = query.get("product", "lwq300_2016_2024")
        variables = query.get("variables", ["Rw620_rep", "Rw767_rep", "last_obs"])

        if product not in self.LWQ_PRODUCTS:
            logger.warning(f"Unknown CGLS LWQ product: {product}")
            return []

        prod_info = self.LWQ_PRODUCTS[product]
        bucket_prefix = prod_info["bucket"] + "/"

        s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED), region_name=self.region)

        assets = []

        # List all tiles
        tiles = self._list_tiles(bucket_prefix)
        logger.info(f"Found {len(tiles)} tiles for CGLS {product}")

        for tile in tiles[:5]:  # Limit to first 5 tiles for testing
            try:
                f"{prod_info['bucket']}/{tile}/"

                # List all files in this tile
                paginator = s3.get_paginator("list_objects_v2")
                for page in paginator.paginate(
                    Bucket=self.s3_bucket, Prefix=f"{prod_info['bucket']}/{tile}/"
                ):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]

                        # Check if it's a GeoTIFF for one of our variables
                        if not key.endswith(".tif"):
                            continue

                        # Filter by variables
                        var_match = any(var in key for var in variables)
                        if not var_match:
                            continue

                        # Download

                        resp = requests.get(
                            f"https://{self.s3_bucket}.s3.{self.region}.amazonaws.com/{key}",
                            timeout=120,
                            stream=True,
                        )
                        resp.raise_for_status()

                        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                            for chunk in resp.iter_content(chunk_size=8192):
                                tmp.write(chunk)
                            tmp_path = tmp.name

                        asset_id = f"cgls_{product}_{os.path.basename(key).replace('.tif', '')}_{hashlib.md5(key.encode()).hexdigest()[:8]}"
                        file_path = self.cache_dir / f"{asset_id}.tif"

                        import shutil

                        shutil.move(tmp_path, file_path)

                        assets.append(
                            DataAsset(
                                asset_id=asset_id,
                                source_id=self.source.source_id,
                                name=f"CGLS {product} {os.path.basename(key)}",
                                description=f"CGLS LWQ water quality - {os.path.basename(key)}",
                                file_path=file_path,
                                format="geotiff",
                                size_bytes=file_path.stat().st_size,
                                checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                                metadata={
                                    "product": product,
                                    "variable": next(v for v in variables if v in key)
                                    if any(v in key for v in variables)
                                    else "unknown",
                                    "tile": key.split("/")[2]
                                    if len(key.split("/")) > 2
                                    else "unknown",
                                    "resolution": "300m" if "300" in product else "100m",
                                },
                                provenance={
                                    "source_url": f"https://{self.s3_bucket}.s3.{self.region}.amazonaws.com/{key}",
                                    "fetched_at": datetime.now(UTC).isoformat(),
                                    "citation": "Copernicus Global Land Service Lake Water Quality via DE Africa S3",
                                    "note": "Standard CGLS biophysical variables (LAI, FAPAR, NDVI, VCI, DMP) require Sentinel Hub auth",
                                },
                            )
                        )

            except Exception as e:
                logger.warning(f"CGLS fetch failed for tile {tile}: {e}")
                continue

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            import rasterio

            with rasterio.open(asset.file_path) as src:
                return src.width > 0 and src.height > 0
        except Exception:
            return False


class ESAWorldCoverConnector(DataConnector):
    """ESA WorldCover 2021 Land Cover (10m resolution, free, no key via AWS S3).

    Accesses the ESA WorldCover 2021 v200 product from the AWS Open Data registry.
    11 land cover classes at 10m resolution.
    """

    def __init__(self, cache_dir: Path = Path("data/cache/esa_worldcover")):
        self.source = DataSource(
            source_id="esa_worldcover",
            name="ESA WorldCover 2021",
            description="ESA WorldCover 2021 v200 - 10m land cover from Sentinel-1/2 (AWS Open Data)",
            base_url="https://esa-worldcover.s3.amazonaws.com",
            auth_type="none",
            format="geotiff",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_tile_name(self, bbox: list[float]) -> list[str]:
        """Determine which tiles intersect the given bbox.

        WorldCover uses 3x3 degree tiles with naming like N51E003.
        """
        import numpy as np

        lon_min, lat_min, lon_max, lat_max = bbox
        tiles = []

        lat_start = int(np.floor(lat_min / 3) * 3)
        lat_end = int(np.ceil(lat_max / 3) * 3)
        lon_start = int(np.floor(lon_min / 3) * 3)
        lon_end = int(np.ceil(lon_max / 3) * 3)

        for lat in range(lat_start, lat_end, 3):
            for lon in range(lon_start, lon_end, 3):
                lat_hemi = "N" if lat >= 0 else "S"
                lon_hemi = "E" if lon >= 0 else "W"
                tile_name = f"{lat_hemi}{abs(lat):02d}{lon_hemi}{abs(lon):03d}"
                tiles.append(tile_name)

        return tiles

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch ESA WorldCover 2021 tiles for given bbox.

        query: {
            "bbox": [lon_min, lat_min, lon_max, lat_max],
        }
        """
        import requests

        bbox = query.get("bbox", [-180, -90, 180, 90])
        tiles = self._get_tile_name(bbox)

        assets = []
        for tile in tiles:
            try:
                filename = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
                url = f"{self.source.base_url}/v200/2021/map/{filename}"

                resp = requests.get(url, timeout=120, stream=True)
                if resp.status_code == 404:
                    logger.warning(f"WorldCover tile not found: {tile}")
                    continue
                resp.raise_for_status()

                with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                    for chunk in resp.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    tmp_path = tmp.name

                asset_id = (
                    f"esa_worldcover_{tile}_{hashlib.md5(str(bbox).encode()).hexdigest()[:8]}"
                )
                file_path = self.cache_dir / f"{asset_id}.tif"

                import shutil

                shutil.move(tmp_path, file_path)

                assets.append(
                    DataAsset(
                        asset_id=asset_id,
                        source_id=self.source.source_id,
                        name=f"ESA WorldCover 2021 {tile}",
                        description=f"ESA WorldCover 2021 v200 tile {tile} (10m land cover)",
                        file_path=file_path,
                        format="geotiff",
                        size_bytes=file_path.stat().st_size,
                        checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                        metadata={
                            "bbox": bbox,
                            "tile": tile,
                            "year": 2021,
                            "version": "v200",
                            "resolution": "10m",
                            "crs": "EPSG:4326",
                        },
                        provenance={
                            "source_url": url,
                            "fetched_at": datetime.now(UTC).isoformat(),
                            "citation": "Zanaga et al. 2021, ESA WorldCover 10m 2021 v200",
                        },
                    )
                )

            except Exception as e:
                logger.warning(f"ESA WorldCover fetch failed for tile {tile}: {e}")
                continue

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            import rasterio

            with rasterio.open(asset.file_path) as src:
                return src.width > 0 and src.height > 0
        except Exception:
            return False


class GBIFConnector(DataConnector):
    """GBIF (Global Biodiversity Information Facility) connector.

    Provides access to:
    - Species occurrence records (occurrence API)
    - Species checklists for countries/regions (species/checklist API)
    - Species information (species API)
    - Dataset metadata (dataset API)

    API: https://api.gbif.org/v1/
    Free, no API key required.
    """

    def __init__(self, cache_dir: Path = Path("data/cache/gbif")):
        self.source = DataSource(
            source_id="gbif",
            name="GBIF",
            description="Global Biodiversity Information Facility - species occurrences, checklists, and taxonomy",
            base_url="https://api.gbif.org/v1",
            auth_type="none",
            format="json",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _build_occurrence_query(self, query: dict[str, Any]) -> dict[str, Any]:
        """Build query parameters for occurrence search."""
        params = {}

        # Spatial filter
        if "bbox" in query:
            bbox = query["bbox"]
            params["geometry"] = (
                f"POLYGON(({bbox[0]} {bbox[1]}, {bbox[2]} {bbox[1]}, {bbox[2]} {bbox[3]}, {bbox[0]} {bbox[3]}, {bbox[0]} {bbox[1]}))"
            )

        # Taxonomic filter
        if "taxon_key" in query:
            params["taxonKey"] = query["taxon_key"]
        if "scientific_name" in query:
            params["scientificName"] = query["scientific_name"]
        if "rank" in query:
            params["rank"] = query["rank"]

        # Temporal filter
        if "start_date" in query and "end_date" in query:
            params["year"] = f"{query['start_date'][:4]},{query['end_date'][:4]}"
        elif "year" in query:
            params["year"] = query["year"]

        # Country filter
        if "country" in query:
            params["country"] = query["country"]

        # Basis of record filter
        if "basis_of_record" in query:
            params["basisOfRecord"] = query["basis_of_record"]

        # Data quality filters
        if "has_coordinate" in query:
            params["hasCoordinate"] = str(query["has_coordinate"]).lower()
        if "has_geospatial_issue" in query:
            params["hasGeospatialIssue"] = str(query["has_geospatial_issue"]).lower()

        # Pagination
        params["limit"] = query.get("limit", 300)
        params["offset"] = query.get("offset", 0)

        return params

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch GBIF data.

        query: {
            "type": "occurrence|checklist|species|dataset",
            "bbox": [lon_min, lat_min, lon_max, lat_max],  # for occurrence
            "taxon_key": 12345,  # for occurrence/species
            "scientific_name": "Panthera leo",  # for occurrence
            "rank": "SPECIES",  # for occurrence
            "country": "IR",  # for occurrence/checklist (ISO 2-letter code)
            "year": "2020,2024",  # for occurrence
            "start_date": "2020-01-01", "end_date": "2024-12-31",  # alternative to year
            "basis_of_record": "HUMAN_OBSERVATION",  # for occurrence
            "has_coordinate": true,  # for occurrence
            "has_geospatial_issue": false,  # for occurrence
            "limit": 300,  # max 300 per request
            "offset": 0,
            "species_key": 12345,  # for species detail
            "dataset_key": "abc-123",  # for dataset detail
            "checklist_key": "xyz-789",  # for checklist detail
        }
        """

        query_type = query.get("type", "occurrence")

        if query_type == "occurrence":
            return self._fetch_occurrences(query)
        elif query_type == "checklist":
            return self._fetch_checklist(query)
        elif query_type == "species":
            return self._fetch_species(query)
        elif query_type == "dataset":
            return self._fetch_dataset(query)
        else:
            logger.warning(f"Unknown GBIF query type: {query_type}")
            return []

    def _fetch_occurrences(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch species occurrence records."""
        import requests

        params = self._build_occurrence_query(query)
        url = f"{self.source.base_url}/occurrence/search"

        assets = []
        max_records = query.get("max_records", params["limit"])
        total_fetched = 0

        while total_fetched < max_records:
            current_limit = min(params["limit"], max_records - total_fetched)
            params["limit"] = current_limit

            try:
                response = requests.get(url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    break

                # Save batch
                asset_id = f"gbif_occurrence_{hashlib.md5(str(params).encode()).hexdigest()[:8]}_{params['offset']}"
                file_path = self.cache_dir / f"{asset_id}.json"
                file_path.write_text(json.dumps(data))

                assets.append(
                    DataAsset(
                        asset_id=asset_id,
                        source_id=self.source.source_id,
                        name=f"GBIF Occurrences offset {params['offset']}-{params['offset'] + len(results)}",
                        description=f"GBIF occurrence records for query: {params}",
                        file_path=file_path,
                        format="json",
                        size_bytes=file_path.stat().st_size,
                        checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                        metadata={
                            "query_params": params,
                            "total_results": data.get("count", 0),
                            "offset": params["offset"],
                            "limit": current_limit,
                            "returned": len(results),
                        },
                        provenance={
                            "source_url": url,
                            "query_params": params,
                            "fetched_at": datetime.now(UTC).isoformat(),
                            "citation": "GBIF.org (2024) GBIF Occurrence Download",
                        },
                        tags=["biodiversity", "occurrence", "species"],
                    )
                )

                total_fetched += len(results)
                params["offset"] += current_limit

                # Check if we've fetched all available records
                if len(results) < current_limit or params["offset"] >= data.get("count", 0):
                    break

            except Exception as e:
                logger.warning(f"GBIF occurrence fetch failed at offset {params['offset']}: {e}")
                break

        return assets

    def _fetch_checklist(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch species list (checklist-like) for a country or taxonomic group.

        Uses the GBIF species search API since checklist endpoints are not available via REST.
        For full checklist downloads, use the DWC_ARCHIVE endpoints from dataset metadata.

        query: {
            "country": "IR",  # ISO 2-letter country code
            "taxon_key": 12345,  # taxonomic key to filter
            "rank": "SPECIES",  # taxonomic rank
            "limit": 300,
            "offset": 0,
        }
        """
        import requests

        country = query.get("country")
        taxon_key = query.get("taxon_key")
        rank = query.get("rank", "SPECIES")
        limit = query.get("limit", 300)
        offset = query.get("offset", 0)

        params = {
            "limit": limit,
            "offset": offset,
            "rank": rank,
        }

        if country:
            params["country"] = country
        if taxon_key:
            params["taxonKey"] = taxon_key

        url = f"{self.source.base_url}/species/search"

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])

            asset_id = f"gbif_species_list_{country or taxon_key or 'all'}_{hashlib.md5(str(params).encode()).hexdigest()[:8]}"
            file_path = self.cache_dir / f"{asset_id}.json"
            file_path.write_text(json.dumps(data))

            return [
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"GBIF Species List for {country or taxon_key or 'all'}",
                    description="GBIF species search results (checklist-like)",
                    file_path=file_path,
                    format="json",
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "country": country,
                        "taxon_key": taxon_key,
                        "rank": rank,
                        "total_species": data.get("count", 0),
                        "returned": len(results),
                    },
                    provenance={
                        "source_url": url,
                        "query_params": params,
                        "fetched_at": datetime.now(UTC).isoformat(),
                        "citation": "GBIF.org (2024) GBIF Species Search",
                    },
                    tags=["biodiversity", "checklist", "species", "taxonomy"],
                )
            ]

        except Exception as e:
            logger.warning(f"GBIF species list fetch failed: {e}")
            return []

    def _fetch_species(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch species detail by key."""
        import requests

        species_key = query.get("species_key")
        scientific_name = query.get("scientific_name")

        if species_key:
            url = f"{self.source.base_url}/species/{species_key}"
        elif scientific_name:
            url = f"{self.source.base_url}/species/match?name={scientific_name}"
        else:
            logger.warning("GBIF species requires species_key or scientific_name")
            return []

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            asset_id = f"gbif_species_{species_key or scientific_name.replace(' ', '_')}"
            file_path = self.cache_dir / f"{asset_id}.json"
            file_path.write_text(json.dumps(data))

            return [
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"GBIF Species {species_key or scientific_name}",
                    description="GBIF species detail",
                    file_path=file_path,
                    format="json",
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "species_key": species_key,
                        "scientific_name": scientific_name,
                    },
                    provenance={
                        "source_url": url,
                        "fetched_at": datetime.now(UTC).isoformat(),
                        "citation": "GBIF.org (2024) GBIF Backbone Taxonomy",
                    },
                    tags=["biodiversity", "taxonomy", "species"],
                )
            ]

        except Exception as e:
            logger.warning(f"GBIF species fetch failed: {e}")
            return []

    def _fetch_dataset(self, query: dict[str, Any]) -> list[DataAsset]:
        """Fetch dataset metadata."""
        import requests

        dataset_key = query.get("dataset_key")
        if not dataset_key:
            logger.warning("GBIF dataset requires dataset_key")
            return []

        url = f"{self.source.base_url}/dataset/{dataset_key}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            asset_id = f"gbif_dataset_{dataset_key}"
            file_path = self.cache_dir / f"{asset_id}.json"
            file_path.write_text(json.dumps(data))

            return [
                DataAsset(
                    asset_id=asset_id,
                    source_id=self.source.source_id,
                    name=f"GBIF Dataset {dataset_key}",
                    description="GBIF dataset metadata",
                    file_path=file_path,
                    format="json",
                    size_bytes=file_path.stat().st_size,
                    checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                    metadata={
                        "dataset_key": dataset_key,
                    },
                    provenance={
                        "source_url": url,
                        "fetched_at": datetime.now(UTC).isoformat(),
                        "citation": "GBIF.org (2024) GBIF Dataset Registry",
                    },
                    tags=["biodiversity", "dataset", "metadata"],
                )
            ]

        except Exception as e:
            logger.warning(f"GBIF dataset fetch failed: {e}")
            return []

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            data = json.loads(asset.file_path.read_text())
            # Check for GBIF response structure
            return "results" in data or "key" in data or "usageKey" in data or "count" in data
        except Exception:
            return False


class HydroSHEDSConnector(DataConnector):
    """HydroSHEDS Hydrography Data (free, no key, direct HTTP downloads).

    Provides access to:
    - HydroBASINS: Global watershed boundaries (multiple levels)
    - HydroRIVERS: Global river network
    - HydroLAKES: Global lake polygons and points
    - GloRiC: Global River Classification
    """

    DATASETS = {
        "hydrobasins": {
            "name": "HydroBASINS",
            "description": "Global watershed boundaries at multiple Pfafstetter levels",
            "base_url": "https://data.hydrosheds.org/file/hydrobasins/standard/",
            "files": {
                "af": "hybas_af_lev01-12_v1c.zip",
                "ar": "hybas_ar_lev01-12_v1c.zip",
                "as": "hybas_as_lev01-12_v1c.zip",
                "au": "hybas_au_lev01-12_v1c.zip",
                "eu": "hybas_eu_lev01-12_v1c.zip",
                "gr": "hybas_gr_lev01-12_v1c.zip",
                "na": "hybas_na_lev01-12_v1c.zip",
                "sa": "hybas_sa_lev01-12_v1c.zip",
                "si": "hybas_si_lev01-12_v1c.zip",
            },
            "format": "zip",
        },
        "hydrorivers": {
            "name": "HydroRIVERS",
            "description": "Global river network with stream order and discharge",
            "base_url": "https://data.hydrosheds.org/file/HydroRIVERS/",
            "files": {
                "gdb": "HydroRIVERS_v10.gdb.zip",
                "shp": "HydroRIVERS_v10_shp.zip",
                "af_gdb": "HydroRIVERS_v10_af.gdb.zip",
                "ar_gdb": "HydroRIVERS_v10_ar.gdb.zip",
                "as_gdb": "HydroRIVERS_v10_as.gdb.zip",
                "au_gdb": "HydroRIVERS_v10_au.gdb.zip",
                "eu_gdb": "HydroRIVERS_v10_eu.gdb.zip",
                "gr_gdb": "HydroRIVERS_v10_gr.gdb.zip",
                "na_gdb": "HydroRIVERS_v10_na.gdb.zip",
                "sa_gdb": "HydroRIVERS_v10_sa.gdb.zip",
                "si_gdb": "HydroRIVERS_v10_si.gdb.zip",
                "af_shp": "HydroRIVERS_v10_af_shp.zip",
                "ar_shp": "HydroRIVERS_v10_ar_shp.zip",
                "as_shp": "HydroRIVERS_v10_as_shp.zip",
                "au_shp": "HydroRIVERS_v10_au_shp.zip",
                "eu_shp": "HydroRIVERS_v10_eu_shp.zip",
                "gr_shp": "HydroRIVERS_v10_gr_shp.zip",
                "na_shp": "HydroRIVERS_v10_na_shp.zip",
                "sa_shp": "HydroRIVERS_v10_sa_shp.zip",
                "si_shp": "HydroRIVERS_v10_si_shp.zip",
            },
            "format": "zip",
        },
        "hydrolakes": {
            "name": "HydroLAKES",
            "description": "Global lake polygons and points",
            "base_url": "https://data.hydrosheds.org/file/hydrolakes/",
            "files": {
                "polys_gdb": "HydroLAKES_polys_v10.gdb.zip",
                "points_gdb": "HydroLAKES_points_v10.gdb.zip",
                "polys_shp": "HydroLAKES_polys_v10_shp.zip",
                "points_shp": "HydroLAKES_points_v10_shp.zip",
            },
            "format": "zip",
        },
        "gloric": {
            "name": "GloRiC",
            "description": "Global River Classification (river types by physio-climatic attributes)",
            "base_url": "https://data.hydrosheds.org/file/hydrosheds-associated/gloric/",
            "files": {
                "gdb": "GloRiC_v10_geodatabase.zip",
                "shp": "GloRiC_v10_shapefile.zip",
                "canada_gdb": "GloRiC_Canada_v10_geodatabase.zip",
                "canada_shp": "GloRiC_Canada_v10_shapefile.zip",
            },
            "format": "zip",
        },
    }

    def __init__(self, cache_dir: Path = Path("data/cache/hydrosheds")):
        self.source = DataSource(
            source_id="hydrosheds",
            name="HydroSHEDS",
            description="Global hydrography data (basins, rivers, lakes, river classification) - free HTTP downloads",
            base_url="https://data.hydrosheds.org/",
            auth_type="none",
            format="zip",
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self, query: dict[str, Any]) -> list[DataAsset]:
        """
        Fetch HydroSHEDS data.

        query: {
            "dataset": "hydrobasins|hydrorivers|hydrolakes|gloric",
            "region": "af|ar|as|au|eu|gr|na|sa|si|global",
            "format": "gdb|shp",
        }
        """
        import requests

        dataset = query.get("dataset", "hydrobasins")
        region = query.get("region", "global")
        fmt = query.get("format", "shp")

        if dataset not in self.DATASETS:
            logger.warning(f"Unknown HydroSHEDS dataset: {dataset}")
            return []

        ds_info = self.DATASETS[dataset]
        assets = []

        files_to_fetch = []

        if dataset == "hydrobasins":
            if region == "global":
                for reg, filename in ds_info["files"].items():
                    files_to_fetch.append((reg, filename))
            else:
                if region in ds_info["files"]:
                    files_to_fetch.append((region, ds_info["files"][region]))
        elif dataset == "hydrorivers":
            if fmt == "gdb":
                if region == "global":
                    files_to_fetch.append(("global", ds_info["files"]["gdb"]))
                elif f"{region}_gdb" in ds_info["files"]:
                    files_to_fetch.append((region, ds_info["files"][f"{region}_gdb"]))
            else:
                if region == "global":
                    files_to_fetch.append(("global", ds_info["files"]["shp"]))
                elif f"{region}_shp" in ds_info["files"]:
                    files_to_fetch.append((region, ds_info["files"][f"{region}_shp"]))
        elif dataset == "hydrolakes":
            if fmt == "gdb":
                if "polys_gdb" in ds_info["files"]:
                    files_to_fetch.append(("polys", ds_info["files"]["polys_gdb"]))
                if "points_gdb" in ds_info["files"]:
                    files_to_fetch.append(("points", ds_info["files"]["points_gdb"]))
            else:
                if "polys_shp" in ds_info["files"]:
                    files_to_fetch.append(("polys", ds_info["files"]["polys_shp"]))
                if "points_shp" in ds_info["files"]:
                    files_to_fetch.append(("points", ds_info["files"]["points_shp"]))
        elif dataset == "gloric":
            if fmt == "gdb":
                files_to_fetch.append(("global", ds_info["files"]["gdb"]))
                if "canada_gdb" in ds_info["files"]:
                    files_to_fetch.append(("canada", ds_info["files"]["canada_gdb"]))
            else:
                files_to_fetch.append(("global", ds_info["files"]["shp"]))
                if "canada_shp" in ds_info["files"]:
                    files_to_fetch.append(("canada", ds_info["files"]["canada_shp"]))

        for reg, filename in files_to_fetch:
            try:
                url = f"{ds_info['base_url']}{filename}"

                resp = requests.get(url, timeout=300, stream=True)
                resp.raise_for_status()

                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                    for chunk in resp.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    tmp_path = tmp.name

                asset_id = (
                    f"hydrosheds_{dataset}_{reg}_{hashlib.md5(filename.encode()).hexdigest()[:8]}"
                )
                file_path = self.cache_dir / f"{asset_id}.zip"

                import shutil

                shutil.move(tmp_path, file_path)

                assets.append(
                    DataAsset(
                        asset_id=asset_id,
                        source_id=self.source.source_id,
                        name=f"HydroSHEDS {ds_info['name']} {reg} {filename}",
                        description=f"{ds_info['description']} - {reg} ({filename})",
                        file_path=file_path,
                        format=ds_info["format"],
                        size_bytes=file_path.stat().st_size,
                        checksum=hashlib.md5(file_path.read_bytes()).hexdigest(),
                        metadata={
                            "dataset": dataset,
                            "region": reg,
                            "filename": filename,
                            "format": fmt,
                        },
                        provenance={
                            "source_url": url,
                            "fetched_at": datetime.now(UTC).isoformat(),
                            "citation": "Lehner et al. HydroSHEDS v1.0/v1c",
                        },
                    )
                )

            except Exception as e:
                logger.warning(f"HydroSHEDS fetch failed for {dataset}/{reg}/{filename}: {e}")
                continue

        return assets

    def validate(self, asset: DataAsset) -> bool:
        if not asset.file_path.exists():
            return False
        try:
            import zipfile

            with zipfile.ZipFile(asset.file_path, "r") as zf:
                return len(zf.namelist()) > 0
        except Exception:
            return False


class DataPipeline:
    def __init__(
        self,
        data_root: Path = Path("data"),
        dvc_remote: str | None = None,
    ):
        self.data_root = data_root
        self.dvc_remote = dvc_remote
        self.connectors: dict[str, DataConnector] = {}
        self.assets: dict[str, DataAsset] = {}
        self._register_default_connectors()

    def _register_default_connectors(self) -> None:
        """Register default data connectors."""
        self.register_connector(OpenMeteoConnector())
        self.register_connector(NASA_POWER_Connector())
        self.register_connector(SoilGridsConnector())
        self.register_connector(CHIRPSConnector())
        self.register_connector(WorldClimConnector())
        self.register_connector(NCEPReanalysisConnector())
        self.register_connector(OpenMeteoSeasonalConnector())
        self.register_connector(CGLSConnector())
        self.register_connector(ESAWorldCoverConnector())
        self.register_connector(HydroSHEDSConnector())
        self.register_connector(GBIFConnector())
        # STAC connectors
        self.register_connector(
            STACConnector(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                "planetary_computer",
                "Microsoft Planetary Computer",
            )
        )
        self.register_connector(
            STACConnector(
                "https://earth-search.aws.element84.com/v1",
                "aws_earth_search",
                "AWS Earth Search",
            )
        )
        # CDSE STAC connector (credentials optional — fails gracefully)
        self.register_connector(
            STACConnector(
                os.environ.get("CDSE_STAC_URL", "https://stac.dataspace.copernicus.eu"),
                "cdse",
                "Copernicus Data Space Ecosystem",
                auth_type="oauth2",
                auth_config={
                    "identity_url": os.environ.get(
                        "CDSE_IDENTITY_URL", "https://identity.dataspace.copernicus.eu"
                    ),
                    "client_id": os.environ.get("CDSE_CLIENT_ID", ""),
                    "client_secret": os.environ.get("CDSE_CLIENT_SECRET", ""),
                },
            )
        )

    def register_connector(self, connector: DataConnector) -> None:
        """Register a data connector."""
        self.connectors[connector.source.source_id] = connector
        logger.info(f"Registered connector: {connector.source.name}")

    def fetch_data(
        self,
        source_id: str,
        query: dict[str, Any],
    ) -> list[DataAsset]:
        """Fetch data from a source."""
        if source_id not in self.connectors:
            raise ValueError(f"Unknown source: {source_id}")

        connector = self.connectors[source_id]
        assets = connector.fetch(query)

        # Validate and store
        for asset in assets:
            if connector.validate(asset):
                self.assets[asset.asset_id] = asset
                logger.info(f"Fetched and validated: {asset.name}")
            else:
                logger.warning(f"Validation failed for: {asset.name}")

        return assets

    def get_asset(self, asset_id: str) -> DataAsset | None:
        """Get asset by ID."""
        return self.assets.get(asset_id)

    def list_assets(
        self,
        source_id: str | None = None,
        tags: list[str] | None = None,
    ) -> list[DataAsset]:
        """List assets with filters."""
        assets = list(self.assets.values())
        if source_id:
            assets = [a for a in assets if a.source_id == source_id]
        if tags:
            assets = [a for a in assets if any(t in a.tags for t in tags)]
        return assets

    def init_dvc(self) -> bool:
        """Initialize DVC in data directory."""
        try:
            result = subprocess.run(
                ["dvc", "init", "--no-scm"],
                cwd=self.data_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                logger.info("DVC initialized")
                if self.dvc_remote:
                    self.add_dvc_remote()
                return True
            else:
                logger.error(f"DVC init failed: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.error("DVC not installed")
            return False

    def add_dvc_remote(self) -> bool:
        """Add DVC remote storage."""
        try:
            subprocess.run(
                ["dvc", "remote", "add", "-d", "storage", self.dvc_remote],
                cwd=self.data_root,
                check=True,
            )
            logger.info(f"Added DVC remote: {self.dvc_remote}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add DVC remote: {e}")
            return False

    def dvc_add(self, file_path: Path) -> bool:
        """Add file to DVC tracking."""
        try:
            subprocess.run(
                ["dvc", "add", str(file_path)],
                cwd=self.data_root,
                check=True,
            )
            logger.info(f"Added to DVC: {file_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"DVC add failed: {e}")
            return False

    def dvc_push(self) -> bool:
        """Push DVC tracked files to remote."""
        try:
            subprocess.run(
                ["dvc", "push"],
                cwd=self.data_root,
                check=True,
            )
            logger.info("DVC push completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"DVC push failed: {e}")
            return False

    def dvc_pull(self) -> bool:
        """Pull DVC tracked files from remote."""
        try:
            subprocess.run(
                ["dvc", "pull"],
                cwd=self.data_root,
                check=True,
            )
            logger.info("DVC pull completed")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"DVC pull failed: {e}")
            return False

    def create_stac_catalog(
        self,
        catalog_id: str,
        title: str,
        description: str,
        assets: list[DataAsset],
    ) -> dict[str, Any]:
        """Create STAC catalog from assets."""
        catalog = {
            "stac_version": "1.0.0",
            "stac_extensions": [
                "https://stac-extensions.github.io/item-assets/v1.0.0/schema.json",
            ],
            "id": catalog_id,
            "title": title,
            "description": description,
            "type": "Catalog",
            "links": [
                {"rel": "self", "href": f"./{catalog_id}.json", "type": "application/json"},
                {"rel": "root", "href": "./catalog.json", "type": "application/json"},
            ],
        }

        # Save catalog
        catalog_path = self.data_root / "stac" / catalog_id / "catalog.json"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(json.dumps(catalog, indent=2))

        # Create collection
        collection = {
            "stac_version": "1.0.0",
            "id": f"{catalog_id}_collection",
            "title": f"{title} Collection",
            "description": description,
            "type": "Collection",
            "extent": {
                "spatial": {"bbox": [[-180, -90, 180, 90]]},
                "temporal": {"interval": [["2000-01-01T00:00:00Z", "2030-12-31T23:59:59Z"]]},
            },
            "links": [
                {
                    "rel": "self",
                    "href": f"./{catalog_id}_collection.json",
                    "type": "application/json",
                },
                {"rel": "root", "href": "../catalog.json", "type": "application/json"},
                {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
            ],
        }

        collection_path = catalog_path.parent / f"{catalog_id}_collection.json"
        collection_path.write_text(json.dumps(collection, indent=2))

        # Add items
        for asset in assets:
            item = {
                "stac_version": "1.0.0",
                "id": asset.asset_id,
                "type": "Feature",
                "geometry": asset.metadata.get(
                    "bbox",
                    {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
                ),
                "properties": {
                    "datetime": asset.created_at,
                    "title": asset.name,
                    "description": asset.description,
                },
                "assets": {
                    "data": {
                        "href": str(asset.file_path.relative_to(catalog_path.parent)),
                        "type": "application/json",
                        "roles": ["data"],
                    },
                },
                "links": [
                    {"rel": "self", "href": f"./{asset.asset_id}.json", "type": "application/json"},
                    {"rel": "root", "href": "./catalog.json", "type": "application/json"},
                    {
                        "rel": "parent",
                        "href": f"./{catalog_id}_collection.json",
                        "type": "application/json",
                    },
                    {
                        "rel": "collection",
                        "href": f"./{catalog_id}_collection.json",
                        "type": "application/json",
                    },
                ],
            }
            item_path = catalog_path.parent / f"{asset.asset_id}.json"
            item_path.write_text(json.dumps(item, indent=2))

            # Add to collection
            collection["links"].append(
                {"rel": "item", "href": f"./{asset.asset_id}.json", "type": "application/json"}
            )

        collection_path.write_text(json.dumps(collection, indent=2))

        logger.info(f"Created STAC catalog: {catalog_id} with {len(assets)} items")
        return catalog


# Global pipeline instance
_pipeline: DataPipeline | None = None


def get_pipeline() -> DataPipeline:
    """Get global data pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = DataPipeline()
    return _pipeline
