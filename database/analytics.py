"""DuckDB analytics engine."""

import duckdb

from database.config import DUCKDB_PATH


class AnalyticsEngine:
    def __init__(self):
        self.conn = duckdb.connect(str(DUCKDB_PATH))
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scenario_analytics (
                id INTEGER PRIMARY KEY, farm_id INTEGER, scenario VARCHAR,
                target_year INTEGER, temp_change DOUBLE,
                precip_change_percent DOUBLE, drought_risk_index DOUBLE,
                run_at TIMESTAMP
            )
        """)

    def insert_scenario(self, data):
        self.conn.execute(
            """
            INSERT INTO scenario_analytics
            (farm_id, scenario, target_year, temp_change,
             precip_change_percent, drought_risk_index, run_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                data.get(k)
                for k in [
                    "farm_id",
                    "scenario",
                    "target_year",
                    "temp_change",
                    "precip_change_percent",
                    "drought_risk_index",
                    "run_at",
                ]
            ],
        )

    def aggregate_scenarios(self):
        rows = self.conn.execute("""
            SELECT scenario, COUNT(*), AVG(temp_change), AVG(drought_risk_index)
            FROM scenario_analytics GROUP BY scenario
        """).fetchall()
        return [{"scenario": r[0], "count": r[1], "avg_temp": r[2], "avg_risk": r[3]} for r in rows]

    def close(self):
        self.conn.close()


_engine = None


def get_analytics():
    global _engine
    if _engine is None:
        _engine = AnalyticsEngine()
    return _engine
