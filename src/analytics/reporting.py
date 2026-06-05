import os
import pandas as pd
import duckdb
from pathlib import Path
from typing import Optional

from src.utils.config import load_config, get_db_path, get_path
from src.utils.constants import DB_TABLE_DIM_API, DB_TABLE_DIM_DATE, DB_TABLE_FACT_METRICS
from src.utils.logger import setup_logger

logger = setup_logger()

class Reporting:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.config = load_config(config_path)
        self.db_path = get_db_path(self.config)
        self.analytics_dir = get_path(self.config["database"]["paths"]["warehouse"]) / "analytics"

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path), read_only=True)

    def generate_monthly_report(self) -> pd.DataFrame:
        """Generates a report summarizing average monthly metrics for all APIs."""
        logger.info("Reporting: Generating monthly metrics summary report.")
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    d.year,
                    d.month,
                    ROUND(AVG(m.sla_score), 2) as avg_sla_score,
                    ROUND(AVG(m.reliability_score), 2) as avg_reliability_score,
                    ROUND(AVG(m.health_score), 2) as avg_health_score,
                    ROUND(AVG(m.uptime_percentage), 2) as avg_uptime_percentage,
                    ROUND(AVG(m.error_rate), 2) as avg_error_rate,
                    ROUND(AVG(m.average_response_time), 2) as avg_response_time_ms
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                GROUP BY a.api_name, d.year, d.month
                ORDER BY d.year DESC, d.month DESC, avg_reliability_score DESC;
            """
            df = con.execute(query).fetch_df()
            return df
        except Exception as e:
            logger.error(f"Reporting: generate_monthly_report failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def generate_api_summary_report(self, api_name: str) -> pd.DataFrame:
        """Generates a summary of all metrics for a single API."""
        logger.info(f"Reporting: Generating summary report for API: {api_name}")
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    a.api_name,
                    ROUND(AVG(m.sla_score), 2) as avg_sla_score,
                    ROUND(AVG(m.reliability_score), 2) as avg_reliability_score,
                    ROUND(AVG(m.health_score), 2) as avg_health_score,
                    ROUND(AVG(m.uptime_percentage), 2) as avg_uptime_percentage,
                    ROUND(AVG(m.error_rate), 2) as avg_error_rate,
                    ROUND(AVG(m.average_response_time), 2) as avg_response_time_ms,
                    COUNT(m.metric_key) as total_days_tracked
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                WHERE a.api_name = ?
                GROUP BY a.api_name;
            """
            df = con.execute(query, [api_name]).fetch_df()
            return df
        except Exception as e:
            logger.error(f"Reporting: generate_api_summary_report failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def export_report_csv(self):
        """Generates and writes CSV files for all analytical layers under data/warehouse/analytics/."""
        logger.info("Reporting: Exporting all reports to CSV.")
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        
        con = self._get_connection()
        try:
            # 1. sla_scores.csv: Daily SLA scores by API
            query_sla = f"""
                SELECT a.api_name, d.full_date as date, m.sla_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                ORDER BY date DESC, api_name ASC;
            """
            df_sla = con.execute(query_sla).fetch_df()
            df_sla.to_csv(self.analytics_dir / "sla_scores.csv", index=False)
            
            # 2. health_scores.csv: Daily health scores by API
            query_health = f"""
                SELECT a.api_name, d.full_date as date, m.health_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                ORDER BY date DESC, api_name ASC;
            """
            df_health = con.execute(query_health).fetch_df()
            df_health.to_csv(self.analytics_dir / "health_scores.csv", index=False)

            # 3. reliability_scores.csv: Daily reliability scores by API
            query_reliability = f"""
                SELECT a.api_name, d.full_date as date, m.reliability_score
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                ORDER BY date DESC, api_name ASC;
            """
            df_reliability = con.execute(query_reliability).fetch_df()
            df_reliability.to_csv(self.analytics_dir / "reliability_scores.csv", index=False)

            # 4. leaderboard.csv: Current API leaderboard standings
            from src.analytics.ranking_analytics import RankingAnalytics
            ranking = RankingAnalytics(self.config_path)
            df_leaderboard = ranking.api_leaderboard()
            df_leaderboard.to_csv(self.analytics_dir / "leaderboard.csv", index=False)

            # 5. monthly_report.csv: Monthly aggregated API health and performance metrics
            df_monthly = self.generate_monthly_report()
            df_monthly.to_csv(self.analytics_dir / "monthly_report.csv", index=False)
            
            logger.info("Reporting: CSV export of analytics scores and leaderboard reports complete.")
            
        except Exception as e:
            logger.error(f"Reporting: export_report_csv failed: {e}")
        finally:
            con.close()
