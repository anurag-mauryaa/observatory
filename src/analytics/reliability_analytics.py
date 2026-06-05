import pandas as pd
import duckdb
from pathlib import Path
from typing import Optional

from src.utils.config import load_config, get_db_path
from src.utils.constants import DB_TABLE_DIM_API, DB_TABLE_DIM_DATE, DB_TABLE_FACT_METRICS
from src.utils.logger import setup_logger

logger = setup_logger()

class ReliabilityAnalytics:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.db_path = get_db_path(self.config)

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path), read_only=True)

    def top_reliable_apis(self, limit: int = 5) -> pd.DataFrame:
        """Returns the top reliable APIs based on average reliability score."""
        logger.info(f"ReliabilityAnalytics: Fetching top {limit} reliable APIs.")
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.reliability_score), 2) as avg_reliability_score,
                    ROUND(AVG(m.uptime_percentage), 2) as avg_uptime_percentage,
                    ROUND(AVG(m.sla_score), 2) as avg_sla_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY avg_reliability_score DESC
                LIMIT ?;
            """
            df = con.execute(query, [limit]).fetch_df()
            return df
        except Exception as e:
            logger.error(f"ReliabilityAnalytics: top_reliable_apis failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def least_reliable_apis(self, limit: int = 5) -> pd.DataFrame:
        """Returns the least reliable APIs based on average reliability score."""
        logger.info(f"ReliabilityAnalytics: Fetching least {limit} reliable APIs.")
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.reliability_score), 2) as avg_reliability_score,
                    ROUND(AVG(m.uptime_percentage), 2) as avg_uptime_percentage,
                    ROUND(AVG(m.sla_score), 2) as avg_sla_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY avg_reliability_score ASC
                LIMIT ?;
            """
            df = con.execute(query, [limit]).fetch_df()
            return df
        except Exception as e:
            logger.error(f"ReliabilityAnalytics: least_reliable_apis failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def reliability_trends(self, api_name: Optional[str] = None) -> pd.DataFrame:
        """Returns daily reliability trends, optionally filtered by API name."""
        con = self._get_connection()
        try:
            if api_name:
                query = f"""
                    SELECT 
                        d.full_date as date,
                        a.api_name,
                        m.reliability_score,
                        m.uptime_percentage,
                        m.sla_score
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
                        m.reliability_score,
                        m.uptime_percentage,
                        m.sla_score
                    FROM {DB_TABLE_FACT_METRICS} m
                    JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                    JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                    ORDER BY d.full_date ASC, a.api_name ASC;
                """
                df = con.execute(query).fetch_df()
            return df
        except Exception as e:
            logger.error(f"ReliabilityAnalytics: reliability_trends failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()
