import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List

from src.utils.config import load_config, get_path
from src.utils.logger import setup_logger

logger = setup_logger()

class MetricCalculator:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.processed_dir = get_path(self.config["database"]["paths"]["processed"])
        
    def calculate_sla_score(self, total_requests: int, successful_requests: int) -> float:
        """SLA Score = successful_requests / total_requests * 100."""
        if total_requests == 0:
            return 100.0
        return round((successful_requests / total_requests) * 100, 2)

    def calculate_uptime_percentage(self, total_checks: int, available_checks: int) -> float:
        """Uptime % = available_checks / total_checks * 100."""
        if total_checks == 0:
            return 100.0
        return round((available_checks / total_checks) * 100, 2)

    def calculate_error_rate(self, total_checks: int, failed_checks: int) -> float:
        """Error Rate = failed_checks / total_checks * 100."""
        if total_checks == 0:
            return 0.0
        return round((failed_checks / total_checks) * 100, 2)

    def calculate_reliability_score(self, uptime_percentage: float, success_rate: float) -> float:
        """Reliability Score = uptime_percentage * 0.70 + success_rate * 0.30."""
        # success_rate refers to the SLA score (%) in our model
        score = (uptime_percentage * 0.70) + (success_rate * 0.30)
        return round(score, 2)

    def calculate_health_score(self, error_rate: float, average_response_time: float) -> float:
        """Health Score = 100 - normalized_error_penalty - latency_penalty."""
        # Penalty rules:
        # Error penalty: error_rate * 1.5 (so 10% error rate drops health by 15 points)
        # Latency penalty: average response time in ms divided by 100 (e.g. 500ms -> 5 points, capped at 50)
        error_penalty = error_rate * 1.5
        latency_penalty = min(50.0, average_response_time / 100.0)
        
        health = 100.0 - error_penalty - latency_penalty
        return round(max(0.0, min(100.0, health)), 2)

    def calculate_average_response_time(self, response_times: List[float]) -> float:
        """Calculate average response time excluding nulls."""
        valid_times = [t for t in response_times if t is not None and not np.isnan(t)]
        if not valid_times:
            return 0.0
        return round(float(np.mean(valid_times)), 2)

    def calculate_availability_rate(self, total_checks: int, available_checks: int) -> float:
        """Alias or specific variant for availability rate (same as uptime %)."""
        return self.calculate_uptime_percentage(total_checks, available_checks)

    def run(self):
        """Processes cleaned logs and aggregates metrics by API and Date."""
        logger.info("Starting MetricCalculator run.")
        cleaned_file = self.processed_dir / "cleaned_monitoring_logs.csv"
        
        if not cleaned_file.exists():
            logger.warning("MetricCalculator: No cleaned logs found. Cannot calculate metrics.")
            # Save empty metrics CSV
            empty_metrics = pd.DataFrame(columns=[
                "api_name", "date", "sla_score", "reliability_score", "health_score",
                "uptime_percentage", "error_rate", "average_response_time"
            ])
            empty_metrics.to_csv(self.processed_dir / "calculated_metrics.csv", index=False)
            return

        df = pd.read_csv(cleaned_file)
        if df.empty:
            logger.warning("MetricCalculator: Cleaned logs file is empty.")
            empty_metrics = pd.DataFrame(columns=[
                "api_name", "date", "sla_score", "reliability_score", "health_score",
                "uptime_percentage", "error_rate", "average_response_time"
            ])
            empty_metrics.to_csv(self.processed_dir / "calculated_metrics.csv", index=False)
            return

        # Extract Date key (YYYY-MM-DD) from Timestamp
        df["date"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d")
        
        aggregated_metrics = []
        
        # Group by api_name and date
        grouped = df.groupby(["api_name", "date"])
        for (api_name, date_str), group in grouped:
            total_checks = len(group)
            available_checks = int(group["availability_flag"].sum())
            failed_checks = total_checks - available_checks
            
            # Successful requests defined as status code in 2xx (200 to 299)
            # Standard successful check responds with 2xx status code
            if "status_code" in group.columns:
                successful_requests = int(((group["status_code"] >= 200) & (group["status_code"] < 300)).sum())
            else:
                successful_requests = available_checks

            # Calculate individual KPIs
            uptime_pct = self.calculate_uptime_percentage(total_checks, available_checks)
            err_rate = self.calculate_error_rate(total_checks, failed_checks)
            sla = self.calculate_sla_score(total_checks, successful_requests)
            
            # Latency checks
            lats = group["response_time_ms"].tolist() if "response_time_ms" in group.columns else []
            avg_lat = self.calculate_average_response_time(lats)
            
            reliability = self.calculate_reliability_score(uptime_pct, sla)
            health = self.calculate_health_score(err_rate, avg_lat)
            
            aggregated_metrics.append({
                "api_name": api_name,
                "date": date_str,
                "sla_score": sla,
                "reliability_score": reliability,
                "health_score": health,
                "uptime_percentage": uptime_pct,
                "error_rate": err_rate,
                "average_response_time": avg_lat
            })
            
        metrics_df = pd.DataFrame(aggregated_metrics)
        output_file = self.processed_dir / "calculated_metrics.csv"
        metrics_df.to_csv(output_file, index=False, encoding="utf-8")
        logger.info(f"MetricCalculator: Saved aggregated metrics to {output_file}")
