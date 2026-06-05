import os
import hashlib
import pandas as pd
import duckdb
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.utils.config import load_config, get_db_path, get_path
from src.utils.constants import (
    DEFAULT_API_REGISTRY,
    DB_TABLE_DIM_API,
    DB_TABLE_DIM_DATE,
    DB_TABLE_FACT_CHECKS,
    DB_TABLE_FACT_METRICS
)
from src.utils.logger import setup_logger

logger = setup_logger()

class WarehouseLoader:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.db_path = get_db_path(self.config)
        self.processed_dir = get_path(self.config["database"]["paths"]["processed"])
        
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Helper to create a DuckDB connection and ensure directories exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(self.db_path))

    def create_schema(self, con: duckdb.DuckDBPyConnection):
        """Creates the star schema dimension and fact tables if they do not exist."""
        logger.info("WarehouseLoader: Creating schemas if not exist.")
        
        # 1. Dimension Table: dim_api
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {DB_TABLE_DIM_API} (
                api_key VARCHAR PRIMARY KEY,
                api_name VARCHAR,
                api_url VARCHAR,
                api_category VARCHAR
            );
        """)
        
        # 2. Dimension Table: dim_date
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {DB_TABLE_DIM_DATE} (
                date_key INTEGER PRIMARY KEY,
                full_date DATE,
                month INTEGER,
                quarter INTEGER,
                year INTEGER
            );
        """)
        
        # 3. Fact Table: fact_api_checks
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {DB_TABLE_FACT_CHECKS} (
                check_key VARCHAR PRIMARY KEY,
                api_key VARCHAR REFERENCES {DB_TABLE_DIM_API}(api_key),
                date_key INTEGER REFERENCES {DB_TABLE_DIM_DATE}(date_key),
                status_code INTEGER,
                response_time_ms DOUBLE,
                response_size_bytes INTEGER,
                availability_flag INTEGER
            );
        """)
        
        # 4. Fact Table: fact_api_metrics
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {DB_TABLE_FACT_METRICS} (
                metric_key VARCHAR PRIMARY KEY,
                api_key VARCHAR REFERENCES {DB_TABLE_DIM_API}(api_key),
                date_key INTEGER REFERENCES {DB_TABLE_DIM_DATE}(date_key),
                sla_score DOUBLE,
                reliability_score DOUBLE,
                health_score DOUBLE,
                uptime_percentage DOUBLE,
                error_rate DOUBLE,
                average_response_time DOUBLE
            );
        """)
        logger.info("WarehouseLoader: Database schemas verified.")

    def load_dimension_tables(self, con: duckdb.DuckDBPyConnection):
        """Populates dimension tables dim_api and dim_date."""
        logger.info("WarehouseLoader: Loading dimension tables.")
        
        # Populate dim_api
        apis_to_load = []
        apis_in_config = self.config.get("apis", [])
        
        for item in apis_in_config:
            name = item if isinstance(item, str) else item.get("name")
            # Resolve url and category
            if name in DEFAULT_API_REGISTRY:
                url = DEFAULT_API_REGISTRY[name]["url"]
                category = DEFAULT_API_REGISTRY[name]["category"]
            elif isinstance(item, dict):
                url = item.get("url", f"https://api.{name.lower()}.com")
                category = item.get("category", "Other")
            else:
                url = f"https://api.{name.lower()}.com"
                category = "Other"
                
            api_key = hashlib.md5(name.encode("utf-8")).hexdigest()
            apis_to_load.append((api_key, name, url, category))
            
        # Insert dim_api rows
        for api_key, name, url, category in apis_to_load:
            con.execute(f"""
                INSERT OR REPLACE INTO {DB_TABLE_DIM_API} (api_key, api_name, api_url, api_category)
                VALUES (?, ?, ?, ?);
            """, (api_key, name, url, category))
            
        logger.info(f"WarehouseLoader: Populated {len(apis_to_load)} APIs into {DB_TABLE_DIM_API}.")
        
        # Populate dim_date: pre-populate date window (last 120 days to next 30 days) to prevent joins from failing
        start_date = datetime.now() - timedelta(days=120)
        dates_to_insert = []
        for d in range(150):
            current = start_date + timedelta(days=d)
            date_key = int(current.strftime("%Y%m%d"))
            full_date = current.date()
            month = current.month
            quarter = (current.month - 1) // 3 + 1
            year = current.year
            dates_to_insert.append((date_key, full_date, month, quarter, year))
            
        for date_key, full_date, month, quarter, year in dates_to_insert:
            con.execute(f"""
                INSERT OR REPLACE INTO {DB_TABLE_DIM_DATE} (date_key, full_date, month, quarter, year)
                VALUES (?, ?, ?, ?, ?);
            """, (date_key, full_date, month, quarter, year))
            
        logger.info(f"WarehouseLoader: Populated {len(dates_to_insert)} days into {DB_TABLE_DIM_DATE}.")

    def load_api_check_facts(self, con: duckdb.DuckDBPyConnection):
        """Loads check history fact table fact_api_checks."""
        logger.info("WarehouseLoader: Loading API check facts.")
        cleaned_file = self.processed_dir / "cleaned_monitoring_logs.csv"
        
        if not cleaned_file.exists():
            logger.warning("WarehouseLoader: No processed checks file found to load.")
            return
            
        df = pd.read_csv(cleaned_file)
        if df.empty:
            logger.warning("WarehouseLoader: Processed checks file is empty.")
            return
            
        # Parse fields
        df["api_key"] = df["api_name"].apply(lambda name: hashlib.md5(name.encode("utf-8")).hexdigest())
        
        df["dt"] = pd.to_datetime(df["timestamp"])
        df["date_key"] = df["dt"].dt.strftime("%Y%m%d").astype(int)
        
        # Ensure correct datatypes
        df["status_code"] = df["status_code"].fillna(-1).astype(int)
        df["response_time_ms"] = df["response_time_ms"].fillna(0.0).astype(float)
        df["response_size_bytes"] = df["response_size_bytes"].fillna(0).astype(int)
        df["availability_flag"] = df["availability_flag"].fillna(0).astype(int)
        
        # DuckDB allows direct loading from pandas dataframe
        # We will write a query that inserts or replaces checks
        con.execute(f"""
            INSERT OR REPLACE INTO {DB_TABLE_FACT_CHECKS} 
            (check_key, api_key, date_key, status_code, response_time_ms, response_size_bytes, availability_flag)
            SELECT monitoring_id, api_key, date_key, status_code, response_time_ms, response_size_bytes, availability_flag
            FROM df;
        """)
        
        cnt = con.execute(f"SELECT COUNT(*) FROM {DB_TABLE_FACT_CHECKS}").fetchone()[0]
        logger.info(f"WarehouseLoader: Total records in {DB_TABLE_FACT_CHECKS}: {cnt}")

    def load_metric_facts(self, con: duckdb.DuckDBPyConnection):
        """Loads metric records into fact_api_metrics."""
        logger.info("WarehouseLoader: Loading metrics facts.")
        metrics_file = self.processed_dir / "calculated_metrics.csv"
        
        if not metrics_file.exists():
            logger.warning("WarehouseLoader: No processed metrics file found to load.")
            return
            
        df = pd.read_csv(metrics_file)
        if df.empty:
            logger.warning("WarehouseLoader: Processed metrics file is empty.")
            return
            
        df["api_key"] = df["api_name"].apply(lambda name: hashlib.md5(name.encode("utf-8")).hexdigest())
        df["dt"] = pd.to_datetime(df["date"])
        df["date_key"] = df["dt"].dt.strftime("%Y%m%d").astype(int)
        
        # Generate metric_key = api_key + "_" + date_key string
        df["metric_key"] = df["api_key"] + "_" + df["date_key"].astype(str)
        
        con.execute(f"""
            INSERT OR REPLACE INTO {DB_TABLE_FACT_METRICS}
            (metric_key, api_key, date_key, sla_score, reliability_score, health_score, uptime_percentage, error_rate, average_response_time)
            SELECT metric_key, api_key, date_key, sla_score, reliability_score, health_score, uptime_percentage, error_rate, average_response_time
            FROM df;
        """)
        
        cnt = con.execute(f"SELECT COUNT(*) FROM {DB_TABLE_FACT_METRICS}").fetchone()[0]
        logger.info(f"WarehouseLoader: Total records in {DB_TABLE_FACT_METRICS}: {cnt}")

    def run(self):
        """Runs the warehouse loader pipeline."""
        logger.info("WarehouseLoader: Starting ETL load to DuckDB.")
        con = self._get_connection()
        try:
            self.create_schema(con)
            self.load_dimension_tables(con)
            self.load_api_check_facts(con)
            self.load_metric_facts(con)
            logger.info("WarehouseLoader: ETL load complete.")
        except Exception as e:
            logger.error(f"WarehouseLoader: ETL failed: {str(e)}", exc_info=True)
            raise e
        finally:
            con.close()
