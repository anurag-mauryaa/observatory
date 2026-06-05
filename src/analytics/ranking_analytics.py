import pandas as pd
import duckdb
from pathlib import Path
from typing import Optional

from src.utils.config import load_config, get_db_path
from src.utils.constants import DB_TABLE_DIM_API, DB_TABLE_FACT_METRICS
from src.utils.logger import setup_logger

logger = setup_logger()

class RankingAnalytics:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.db_path = get_db_path(self.config)

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path), read_only=True)

    def api_leaderboard(self) -> pd.DataFrame:
        """Ranks APIs based on: reliability_score * 0.40 + health_score * 0.30 + sla_score * 0.30."""
        logger.info("RankingAnalytics: Computing overall API Leaderboard.")
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.reliability_score), 2) as avg_reliability_score,
                    ROUND(AVG(m.health_score), 2) as avg_health_score,
                    ROUND(AVG(m.sla_score), 2) as avg_sla_score,
                    ROUND(AVG(m.average_response_time), 2) as avg_response_time_ms,
                    ROUND(
                        (AVG(m.reliability_score) * 0.40) + 
                        (AVG(m.health_score) * 0.30) + 
                        (AVG(m.sla_score) * 0.30), 2
                    ) as leaderboard_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY leaderboard_score DESC;
            """
            df = con.execute(query).fetch_df()
            # Add rank rank column
            if not df.empty:
                df.insert(0, "rank", range(1, len(df) + 1))
            return df
        except Exception as e:
            logger.error(f"RankingAnalytics: api_leaderboard failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def health_score_ranking(self) -> pd.DataFrame:
        """Ranks APIs by average health score descending."""
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.health_score), 2) as health_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY health_score DESC;
            """
            df = con.execute(query).fetch_df()
            if not df.empty:
                df.insert(0, "rank", range(1, len(df) + 1))
            return df
        except Exception as e:
            logger.error(f"RankingAnalytics: health_score_ranking failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def sla_ranking(self) -> pd.DataFrame:
        """Ranks APIs by average SLA score descending."""
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.sla_score), 2) as sla_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY sla_score DESC;
            """
            df = con.execute(query).fetch_df()
            if not df.empty:
                df.insert(0, "rank", range(1, len(df) + 1))
            return df
        except Exception as e:
            logger.error(f"RankingAnalytics: sla_ranking failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def reliability_ranking(self) -> pd.DataFrame:
        """Ranks APIs by average reliability score descending."""
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.reliability_score), 2) as reliability_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                GROUP BY a.api_name
                ORDER BY reliability_score DESC;
            """
            df = con.execute(query).fetch_df()
            if not df.empty:
                df.insert(0, "rank", range(1, len(df) + 1))
            return df
        except Exception as e:
            logger.error(f"RankingAnalytics: reliability_ranking failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()
