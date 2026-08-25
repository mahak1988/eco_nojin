"""Abstract Database Adapter for Eco Nojin (DuckDB-compatible)."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import geopandas as gpd


class DatabaseAdapter(ABC):
    """Abstract interface for database operations."""
    
    @abstractmethod
    def connect(self) -> None:
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Any = None) -> List:
        pass
    
    @abstractmethod
    def query_to_gdf(self, query: str, geom_col: str = "geom") -> gpd.GeoDataFrame:
        pass


class DuckDBAdapter(DatabaseAdapter):
    """DuckDB implementation - Eco Nojin primary storage."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.conn = None
    
    def connect(self) -> None:
        import duckdb
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))
        self.conn.execute("INSTALL spatial;")
        self.conn.execute("LOAD spatial;")
    
    def disconnect(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def execute(self, query: str, params: Any = None) -> List:
        """Execute query with optional parameters."""
        if params is None:
            return self.conn.execute(query).fetchall()
        
        # DuckDB accepts list/tuple/dict for parameters
        if isinstance(params, dict):
            return self.conn.execute(query, params).fetchall()
        elif isinstance(params, (list, tuple)):
            return self.conn.execute(query, params).fetchall()
        else:
            return self.conn.execute(query, [params]).fetchall()
    
    def query_to_gdf(self, query: str, geom_col: str = "geom") -> gpd.GeoDataFrame:
        """Return query results as GeoDataFrame."""
        result = self.conn.execute(query)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()
        
        df = gpd.GeoDataFrame.from_records(rows, columns=columns)
        
        # Convert WKT to geometry if geom_col exists
        if geom_col in df.columns:
            from shapely import wkt
            df[geom_col] = df[geom_col].apply(
                lambda x: wkt.loads(x) if x and isinstance(x, str) else x
            )
            df = df.set_geometry(geom_col)
        
        return df
    
    def insert_land_unit(
        self,
        project_id: UUID,
        name: str,
        geom,
        **kwargs
    ) -> UUID:
        """Insert a land unit and return its ID."""
        land_unit_id = uuid4()
        
        self.conn.execute("""
            INSERT INTO land_units (
                id, project_id, name, geom, area_ha, land_use, slope_class
            ) VALUES (?, ?, ?, ST_GeomFromText(?), ?, ?, ?)
        """, [
            str(land_unit_id),
            str(project_id),
            name,
            geom.wkt,
            kwargs.get('area_ha'),
            kwargs.get('land_use'),
            kwargs.get('slope_class'),
        ])
        
        return land_unit_id
    
    def insert_soil_profile(self, land_unit_id: UUID, **kwargs) -> UUID:
        """Insert a soil profile."""
        profile_id = uuid4()
        
        # Build dynamic columns
        columns = ['id', 'land_unit_id']
        values = [str(profile_id), str(land_unit_id)]
        placeholders = ['?', '?']
        
        for key, value in kwargs.items():
            if value is not None:
                columns.append(key)
                # Handle Point/geometry
                if hasattr(value, 'wkt'):
                    values.append(value.wkt)
                else:
                    values.append(value)
                placeholders.append('?')
        
        query = f"""
            INSERT INTO soil_profiles ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        self.conn.execute(query, values)
        return profile_id
    
    def insert_simulation_run(self, **kwargs) -> UUID:
        """Insert a simulation run."""
        run_id = uuid4()
        
        # Convert parameters dict to JSON string
        params = kwargs.get('parameters')
        if isinstance(params, dict):
            params = json.dumps(params)
        
        self.conn.execute("""
            INSERT INTO simulation_runs (
                id, project_id, land_unit_id, model_name, scenario_name,
                parameters, start_date, end_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            str(run_id),
            str(kwargs.get('project_id')),
            str(kwargs.get('land_unit_id')),
            kwargs.get('model_name'),
            kwargs.get('scenario_name'),
            params,
            kwargs.get('start_date'),
            kwargs.get('end_date'),
            'pending',
        ])
        
        return run_id
    
    def run_migrations(self, migrations_dir: Path) -> None:
        """Run SQL migrations in order."""
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            print(f"Running: {migration_file.name}")
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # Split by semicolons and execute each
            for statement in sql.split(';'):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        self.conn.execute(statement)
                    except Exception as e:
                        # Skip errors for idempotent statements
                        if "already exists" not in str(e).lower():
                            print(f"  ⚠️  {e}")
