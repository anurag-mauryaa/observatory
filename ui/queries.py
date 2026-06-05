import pandas as pd
import duckdb
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List

from src.utils.config import load_config, get_db_path
from src.utils.constants import (
    DB_TABLE_DIM_API,
    DB_TABLE_DIM_DATE,
    DB_TABLE_FACT_CHECKS,
    DB_TABLE_FACT_METRICS
)
from src.utils.logger import setup_logger

logger = setup_logger()

class UIQueries:
    def __init__(self, config_path: Path = None):
        self.config = load_config(config_path)
        self.db_path = get_db_path(self.config)
        
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path), read_only=True)

    def get_dashboard_summary_kpis(self, selected_api: str, days: int) -> Dict[str, Any]:
        """Queries database to get the overall metrics for the dashboard cards."""
        con = self._get_connection()
        try:
            # 1. Date filter clause
            date_filter = ""
            params = []
            if days > 0:
                min_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                date_filter = "AND d.full_date >= ?"
                params.append(min_date)

            api_filter = ""
            if selected_api != "All":
                api_filter = "AND a.api_name = ?"
                params.append(selected_api)

            # Get overall aggregates
            query = f"""
                SELECT 
                    ROUND(AVG(m.reliability_score), 2) as avg_reliability,
                    ROUND(AVG(m.health_score), 2) as avg_health,
                    ROUND(AVG(m.average_response_time), 2) as avg_latency,
                    ROUND(AVG(m.uptime_percentage), 2) as avg_uptime,
                    ROUND(AVG(m.error_rate), 2) as avg_error
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                WHERE 1=1 {date_filter} {api_filter};
            """
            
            res = con.execute(query, params).fetchone()
            
            # Default values if no data
            avg_reliability = res[0] if res and res[0] is not None else 0.0
            avg_health = res[1] if res and res[1] is not None else 0.0
            avg_latency = res[2] if res and res[2] is not None else 0.0
            avg_uptime = res[3] if res and res[3] is not None else 0.0
            
            # Fetch latest daily scores to classify APIs as Healthy, Degraded, or Offline
            # Get the max date first
            max_date_res = con.execute(f"SELECT MAX(d.full_date) FROM {DB_TABLE_FACT_METRICS} m JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key").fetchone()
            latest_date = max_date_res[0] if max_date_res else None
            
            total_apis = 0
            healthy_apis = 0
            degraded_apis = 0
            offline_apis = 0
            
            if latest_date:
                # Query status of APIs on latest date
                status_query = f"""
                    SELECT a.api_name, m.health_score, m.uptime_percentage
                    FROM {DB_TABLE_FACT_METRICS} m
                    JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                    JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                    WHERE d.full_date = ?;
                """
                api_statuses = con.execute(status_query, [latest_date]).fetchall()
                
                total_apis = len(api_statuses)
                for name, health, uptime in api_statuses:
                    # Healthy: health >= 95
                    # Degraded: 80 <= health < 95
                    # Offline: health < 80 or uptime < 80
                    if health >= 95.0 and uptime >= 98.0:
                        healthy_apis += 1
                    elif health >= 80.0 and uptime >= 90.0:
                        degraded_apis += 1
                    else:
                        offline_apis += 1
            else:
                # Fallback: Count total configured apis
                total_apis_res = con.execute(f"SELECT COUNT(*) FROM {DB_TABLE_DIM_API}").fetchone()
                total_apis = total_apis_res[0] if total_apis_res else 0
                healthy_apis = total_apis
                
            return {
                "total_apis": total_apis,
                "healthy_apis": healthy_apis,
                "degraded_apis": degraded_apis,
                "offline_apis": offline_apis,
                "avg_response_time": f"{avg_latency:.1f}ms" if avg_latency > 0 else "N/A",
                "avg_reliability": f"{avg_reliability:.2f}%",
                "avg_health": f"{avg_health:.2f}%",
                "avg_uptime": f"{avg_uptime:.2f}%"
            }
        except Exception as e:
            logger.error(f"UIQueries: get_dashboard_summary_kpis failed: {e}")
            return {}
        finally:
            con.close()

    def get_trend_data(self, selected_api: str, days: int) -> pd.DataFrame:
        """Retrieves daily aggregated metric rows for charts."""
        con = self._get_connection()
        try:
            params = []
            date_filter = ""
            if days > 0:
                min_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
                date_filter = "AND d.full_date >= ?"
                params.append(min_date)
                
            api_filter = ""
            if selected_api != "All":
                api_filter = "AND a.api_name = ?"
                params.append(selected_api)
                
            query = f"""
                SELECT 
                    d.full_date as date,
                    a.api_name,
                    m.sla_score,
                    m.reliability_score,
                    m.health_score,
                    m.uptime_percentage,
                    m.error_rate,
                    m.average_response_time
                FROM {DB_TABLE_FACT_METRICS} m
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key
                JOIN {DB_TABLE_DIM_DATE} d ON m.date_key = d.date_key
                WHERE 1=1 {date_filter} {api_filter}
                ORDER BY date ASC, api_name ASC;
            """
            return con.execute(query, params).fetch_df()
        except Exception as e:
            logger.error(f"UIQueries: get_trend_data failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()

    def get_api_explorer_list(self, search: str = "", sort_by: str = "API Name") -> List[Dict[str, Any]]:
        """Queries recent status and metrics for the API Explorer grid."""
        con = self._get_connection()
        try:
            # Get latest checks dates for each API
            latest_check_query = f"""
                WITH latest_check AS (
                    SELECT 
                        api_key,
                        MAX(date_key) as max_date_key
                    FROM {DB_TABLE_FACT_METRICS}
                    GROUP BY api_key
                )
                SELECT 
                    a.api_name,
                    a.api_url,
                    a.api_category,
                    m.sla_score,
                    m.reliability_score,
                    m.health_score,
                    m.uptime_percentage,
                    m.average_response_time
                FROM latest_check lc
                JOIN {DB_TABLE_FACT_METRICS} m ON lc.api_key = m.api_key AND lc.max_date_key = m.date_key
                JOIN {DB_TABLE_DIM_API} a ON m.api_key = a.api_key;
            """
            
            df = con.execute(latest_check_query).fetch_df()
            if df.empty:
                return []
                
            # Filter
            if search:
                df = df[df["api_name"].str.contains(search, case=False) | df["api_category"].str.contains(search, case=False)]
                
            # Sort
            sort_mappings = {
                "API Name": ("api_name", True),
                "Health Score": ("health_score", False),
                "SLA Score": ("sla_score", False),
                "Latency": ("average_response_time", True),
                "Reliability": ("reliability_score", False)
            }
            
            sort_col, ascending = sort_mappings.get(sort_by, ("api_name", True))
            df = df.sort_values(by=sort_col, ascending=ascending)
            
            # Map columns to status text and format values
            results = []
            for _, r in df.iterrows():
                # Status classification based on latest health/uptime
                if r["health_score"] >= 95 and r["uptime_percentage"] >= 98:
                    status = "Healthy"
                elif r["health_score"] >= 80 and r["uptime_percentage"] >= 90:
                    status = "Degraded"
                else:
                    status = "Offline"
                    
                results.append({
                    "name": r["api_name"],
                    "url": r["api_url"],
                    "category": r["api_category"],
                    "status": status,
                    "latency": f"{r['average_response_time']:.1f}ms",
                    "health": f"{r['health_score']:.1f}%",
                    "sla": f"{r['sla_score']:.1f}%",
                    "reliability": f"{r['reliability_score']:.1f}%",
                    "raw_latency": r["average_response_time"],
                    "raw_health": r["health_score"],
                    "raw_sla": r["sla_score"],
                    "raw_reliability": r["reliability_score"]
                })
            return results
        except Exception as e:
            logger.error(f"UIQueries: get_api_explorer_list failed: {e}")
            return []
        finally:
            con.close()

    def get_api_recent_checks(self, api_name: str, limit: int = 50) -> pd.DataFrame:
        """Fetches raw list of recent checks for detailed view drawer."""
        con = self._get_connection()
        try:
            query = f"""
                SELECT 
                    d.full_date as date,
                    c.status_code,
                    c.response_time_ms,
                    c.response_size_bytes,
                    c.availability_flag
                FROM {DB_TABLE_FACT_CHECKS} c
                JOIN {DB_TABLE_DIM_API} a ON c.api_key = a.api_key
                JOIN {DB_TABLE_DIM_DATE} d ON c.date_key = d.date_key
                WHERE a.api_name = ?
                ORDER BY c.check_key DESC
                LIMIT ?;
            """
            return con.execute(query, [api_name, limit]).fetch_df()
        except Exception as e:
            logger.error(f"UIQueries: get_api_recent_checks failed: {e}")
            return pd.DataFrame()
        finally:
            con.close()
            
    def get_dim_apis(self) -> List[str]:
        """Gets all API names registered in the warehouse dim_api table."""
        con = self._get_connection()
        try:
            res = con.execute(f"SELECT api_name FROM {DB_TABLE_DIM_API} ORDER BY api_name").fetchall()
            return [r[0] for r in res]
        except Exception as e:
            logger.error(f"UIQueries: get_dim_apis failed: {e}")
            return []
        finally:
            con.close()
