import os
import glob
import json
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.utils.config import load_config, get_path
from src.utils.logger import setup_logger

logger = setup_logger()

class DataCleaner:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.raw_dir = get_path(self.config["database"]["paths"]["raw"]) / "monitoring_logs"
        self.processed_dir = get_path(self.config["database"]["paths"]["processed"])
        
    def run(self):
        """Runs the complete data cleaning pipeline."""
        logger.info("Starting DataCleaner run.")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all raw check JSON files
        raw_files = glob.glob(str(self.raw_dir / "*.json"))
        if not raw_files:
            logger.warning("DataCleaner: No raw monitoring logs found to clean.")
            # If no data exists, write an empty CSV to avoid crashes downstream
            empty_df = pd.DataFrame(columns=[
                "monitoring_id", "api_name", "timestamp", "status_code", 
                "response_time_ms", "response_size_bytes", "availability_flag", "error_message"
            ])
            self.save_processed_data(empty_df)
            return
            
        all_records = []
        for file_path in raw_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_records.extend(data)
                    elif isinstance(data, dict):
                        all_records.append(data)
            except Exception as e:
                logger.error(f"DataCleaner: Failed to parse raw log file {file_path}. Error: {str(e)}")
                
        if not all_records:
            logger.warning("DataCleaner: Parsed files but found 0 records.")
            return

        df = pd.DataFrame(all_records)
        
        # 1. Standardize Timestamps
        df = self.standardize_timestamps(df)
        
        # 2. Remove Duplicates
        df = self.remove_duplicates(df)
        
        # 3. Handle Missing Values
        df = self.handle_missing_values(df)
        
        # 4. Save processed output
        self.save_processed_data(df)
        logger.info(f"DataCleaner completed. Processed {len(df)} records.")

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Removes duplicated rows based on monitoring_id."""
        if "monitoring_id" in df.columns and not df.empty:
            before_cnt = len(df)
            df = df.drop_duplicates(subset=["monitoring_id"], keep="first")
            after_cnt = len(df)
            diff = before_cnt - after_cnt
            if diff > 0:
                logger.info(f"DataCleaner: Removed {diff} duplicate monitoring records.")
        return df

    def standardize_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converts timestamps to standard UTC ISO 8601 strings."""
        if "timestamp" in df.columns and not df.empty:
            # Parse and serialize back consistently as ISO formats
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True, format="mixed")
            # Fill missing timestamps with current time
            now_utc = datetime.now(timezone.utc)
            df["timestamp"] = df["timestamp"].fillna(now_utc)
            # Format to ISO format string with Z indicator
            df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return df

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fills missing data or standardizes null representation."""
        if df.empty:
            return df
            
        # Standardize expected columns
        cols = ["status_code", "response_time_ms", "response_size_bytes", "error_message"]
        for col in cols:
            if col not in df.columns:
                df[col] = None
                
        # Fill error messages if availability_flag indicates failure but message is null
        if "availability_flag" in df.columns:
            mask = (df["availability_flag"] == 0) & (df["error_message"].isna() | (df["error_message"] == ""))
            df.loc[mask, "error_message"] = "Connection failed or timeout occurred"
            
        # Re-ensure availability_flag exists and is 1 or 0
        if "availability_flag" not in df.columns:
            df["availability_flag"] = 0
        else:
            df["availability_flag"] = df["availability_flag"].fillna(0).astype(int)
            
        return df

    def save_processed_data(self, df: pd.DataFrame):
        """Saves the cleaned DataFrame as a CSV file in the processed data layer."""
        output_path = self.processed_dir / "cleaned_monitoring_logs.csv"
        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info(f"DataCleaner: Saved processed data to {output_path}")
