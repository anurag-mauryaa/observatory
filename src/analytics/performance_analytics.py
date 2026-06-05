import pandas as pd
import duckdb
from pathlib import Path
from typing import Optional

from src.utils.config import load_config, get_db_path
from src.utils.constants import DB_TABLE_DIM_API, DB_TABLE_DIM_DATE, DB_TABLE_FACT_METRICS
from src.utils.logger import setup_logger

logger = setup_logger()

class PerformanceAnalytics:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.db_path = get_db_path(self.config)

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path), read_only=True)

    def fastest_apis(self, limit: int = 5) -> pd.DataFrame:
        """Returns the fastest APIs sorted by average response time ascending."""
        logger.info(f"PerformanceAnalytics: Fetching top {limit} fastest APIs.")
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.average_response_time), 2) as avg_response_time_ms,
                    ROUND(MIN(m.average_response_time), 2) as min_response_time_ms,
                    ROUND(MAX(m.average_response_time), 2) as max_response_time_ms
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY avg_response_time_ms ASC
                LIMIT ?;
            """
            df = con.execute(query, [limit]).fetch_df()
            return df
        except Exception as e:
            logger.error(f"PerformanceAnalytics: fastest_apis failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def slowest_apis(self, limit: int = 5) -> pd.DataFrame:
        """Returns the slowest APIs sorted by average response time descending."""
        logger.info(f"PerformanceAnalytics: Fetching top {limit} slowest APIs.")
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.average_response_time), 2) as avg_response_time_ms,
                    ROUND(MAX(m.average_response_time), 2) as max_response_time_ms
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY avg_response_time_ms DESC
                LIMIT ?;
            """
            df = con.execute(query, [limit]).fetch_df()
            return df
        except Exception as e:
            logger.error(f"PerformanceAnalytics: slowest_apis failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def response_time_trends(self, api_name: Optional[str] = None) -> pd.DataFrame:
        """Returns daily response time trends, optionally filtered by API name."""
        con = self._get_connection()
        try:
            if api_name:
                query = f"""
                    SELECT 
                        d.full_date as date,
                        a.api_name,
                        m.average_response_time
                    FROM {DB_TABLE_FACT_METRICS} m
                    JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                    JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                    WHERE a.api_name = ?
                    ORDER BY d.full_date ASC;
                """
                df = con.execute(query, [api_name]).fetch_df()
            else:
                query = f"""
                    SELECT 
                        d.full_date as date,
                        a.api_name,
                        m.average_response_time
                    FROM {DB_TABLE_FACT_METRICS} m
                    JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                    JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                    ORDER BY d.full_date ASC, a.api_name ASC;
                """
                df = con.execute(query).fetch_df()
            return df
        except Exception as e:
            logger.error(f"PerformanceAnalytics: response_time_trends failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()
