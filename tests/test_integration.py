import os
import shutil
import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.config import get_path, get_db_path
from src.utils.history_simulator import HistorySimulator
from src.processing.data_cleaner import DataCleaner
from src.processing.metric_calculator import MetricCalculator
from src.warehouse.warehouse_loader import WarehouseLoader
from src.analytics.reliability_analytics import ReliabilityAnalytics
from src.analytics.performance_analytics import PerformanceAnalytics
from src.analytics.ranking_analytics import RankingAnalytics
from src.analytics.reporting import Reporting
from src.monitoring.api_monitor import APIMonitor

@pytest.fixture
def integration_test_env(tmp_path):
    """Sets up a test config file and cleans up test folders before/after run."""
    # Define test directories under the project root
    test_raw_str = "data/test_raw"
    test_processed_str = "data/test_processed"
    test_warehouse_str = "data/test_warehouse"
    
    raw_dir = get_path(test_raw_str)
    processed_dir = get_path(test_processed_str)
    warehouse_dir = get_path(test_warehouse_str)
    
    # Cleanup previous runs if any
    for d in [raw_dir, processed_dir, warehouse_dir]:
        if d.exists():
            shutil.rmtree(d)
            
    # Write a test configuration file
    test_config = {
        "monitor_interval_minutes": 15,
        "timeout_seconds": 2,
        "apis": ["GitHub", "SpaceX", "CoinGecko"],
        "database": {
            "file_name": "test_api_observatory.duckdb",
            "paths": {
                "raw": test_raw_str,
                "processed": test_processed_str,
                "warehouse": test_warehouse_str
            }
        }
    }
    
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(test_config, f)
        
    # Set env var
    os.environ["API_OBSERVATORY_CONFIG_PATH"] = str(config_file)
    
    yield {
        "raw_dir": raw_dir,
        "processed_dir": processed_dir,
        "warehouse_dir": warehouse_dir,
        "db_path": warehouse_dir / "test_api_observatory.duckdb"
    }
    
    # Cleanup env var
    if "API_OBSERVATORY_CONFIG_PATH" in os.environ:
        del os.environ["API_OBSERVATORY_CONFIG_PATH"]
        
    # Cleanup generated files
    for d in [raw_dir, processed_dir, warehouse_dir]:
        if d.exists():
            shutil.rmtree(d)

@patch("src.monitoring.api_checker.requests.get")
def test_full_pipeline_integration(mock_requests_get, integration_test_env):
    """Executes the complete ETL and analytics pipeline end-to-end using test folders."""
    # 1. Mock requests.get for active monitoring checks
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Length": "150"}
    mock_resp.content = b"x" * 150
    mock_requests_get.return_value = mock_resp
    
    # 2. Step 1: Simulate 3 days of checks
    sim = HistorySimulator()
    sim.simulate_history(days=3)
    
    # Verify raw simulated checks exist
    raw_files = list((integration_test_env["raw_dir"] / "monitoring_logs").glob("*.json"))
    assert len(raw_files) == 4 # 3 days + today
    
    # 3. Step 2: Run active live check
    monitor = APIMonitor()
    live_results = monitor.run_all_checks()
    assert len(live_results) == 3
    
    # 4. Step 3: Run data cleaner
    cleaner = DataCleaner()
    cleaner.run()
    
    cleaned_file = integration_test_env["processed_dir"] / "cleaned_monitoring_logs.csv"
    assert cleaned_file.exists()
    
    # 5. Step 4: Run KPI calculator
    calculator = MetricCalculator()
    calculator.run()
    
    metrics_file = integration_test_env["processed_dir"] / "calculated_metrics.csv"
    assert metrics_file.exists()
    
    # 6. Step 5: Load DuckDB database
    loader = WarehouseLoader()
    loader.run()
    
    assert integration_test_env["db_path"].exists()
    
    # 7. Step 6: Query analytics layers
    reliability = ReliabilityAnalytics()
    top_rel = reliability.top_reliable_apis(limit=3)
    least_rel = reliability.least_reliable_apis(limit=3)
    trends_rel = reliability.reliability_trends()
    
    assert len(top_rel) > 0
    assert len(least_rel) > 0
    assert len(trends_rel) > 0
    
    performance = PerformanceAnalytics()
    fast = performance.fastest_apis(limit=3)
    slow = performance.slowest_apis(limit=3)
    trends_perf = performance.response_time_trends()
    
    assert len(fast) > 0
    assert len(slow) > 0
    assert len(trends_perf) > 0
    
    rankings = RankingAnalytics()
    leaderboard = rankings.api_leaderboard()
    health_rank = rankings.health_score_ranking()
    sla_rank = rankings.sla_ranking()
    rel_rank = rankings.reliability_ranking()
    
    assert len(leaderboard) > 0
    assert len(health_rank) > 0
    assert len(sla_rank) > 0
    assert len(rel_rank) > 0
    
    # 8. Step 7: Export reporting CSVs
    reporting = Reporting()
    reporting.export_report_csv()
    
    out_dir = integration_test_env["warehouse_dir"] / "analytics"
    assert (out_dir / "sla_scores.csv").exists()
    assert (out_dir / "health_scores.csv").exists()
    assert (out_dir / "reliability_scores.csv").exists()
    assert (out_dir / "leaderboard.csv").exists()
    assert (out_dir / "monthly_report.csv").exists()
