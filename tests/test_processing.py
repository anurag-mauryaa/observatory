import pytest
import pandas as pd
import numpy as np

from src.processing.data_cleaner import DataCleaner
from src.processing.metric_calculator import MetricCalculator

def test_data_cleaner_remove_duplicates():
    cleaner = DataCleaner()
    df = pd.DataFrame([
        {"monitoring_id": "1", "api_name": "GitHub"},
        {"monitoring_id": "1", "api_name": "GitHub"},
        {"monitoring_id": "2", "api_name": "StackExchange"}
    ])
    cleaned_df = cleaner.remove_duplicates(df)
    assert len(cleaned_df) == 2
    assert "1" in cleaned_df["monitoring_id"].values
    assert "2" in cleaned_df["monitoring_id"].values

def test_data_cleaner_standardize_timestamps():
    cleaner = DataCleaner()
    df = pd.DataFrame([
        {"timestamp": "2026-06-05 16:07:01+05:30"},
        {"timestamp": "2026-06-05T10:37:00Z"},
        {"timestamp": np.nan}
    ])
    standard_df = cleaner.standardize_timestamps(df)
    assert len(standard_df) == 3
    # Check that it compiles to string ISO format with UTC Z
    assert standard_df["timestamp"].iloc[1] == "2026-06-05T10:37:00Z"
    assert "Z" in standard_df["timestamp"].iloc[0]

def test_data_cleaner_handle_missing_values():
    cleaner = DataCleaner()
    df = pd.DataFrame([
        {"monitoring_id": "1", "availability_flag": 0, "error_message": None},
        {"monitoring_id": "2", "availability_flag": 1, "error_message": None}
    ])
    cleaned_df = cleaner.handle_missing_values(df)
    assert cleaned_df["error_message"].iloc[0] == "Connection failed or timeout occurred"
    assert cleaned_df["error_message"].iloc[1] is None

def test_metric_calculator_kpis():
    calc = MetricCalculator()
    
    # SLA Score
    assert calc.calculate_sla_score(10, 9) == 90.0
    assert calc.calculate_sla_score(0, 0) == 100.0
    
    # Uptime %
    assert calc.calculate_uptime_percentage(100, 99) == 99.0
    assert calc.calculate_uptime_percentage(0, 0) == 100.0
    
    # Error rate
    assert calc.calculate_error_rate(100, 5) == 5.0
    assert calc.calculate_error_rate(0, 0) == 0.0
    
    # Reliability Score: uptime * 0.70 + success * 0.30
    assert calc.calculate_reliability_score(100.0, 90.0) == 97.0
    assert calc.calculate_reliability_score(98.5, 95.0) == 97.45
    
    # Average Response Time
    assert calc.calculate_average_response_time([100, 200, 300, None]) == 200.0
    assert calc.calculate_average_response_time([]) == 0.0
    
    # Health Score: 100 - error * 1.5 - min(50, latency/100)
    # error = 10% -> penalty = 15
    # latency = 500ms -> penalty = 5
    # health = 100 - 15 - 5 = 80.0
    assert calc.calculate_health_score(10.0, 500.0) == 80.0
    assert calc.calculate_health_score(0.0, 100.0) == 99.0
