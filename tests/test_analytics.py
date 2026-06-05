import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from src.analytics.reliability_analytics import ReliabilityAnalytics
from src.analytics.performance_analytics import PerformanceAnalytics
from src.analytics.ranking_analytics import RankingAnalytics
from src.analytics.reporting import Reporting

@patch("src.analytics.reliability_analytics.ReliabilityAnalytics._get_connection")
def test_reliability_analytics(mock_conn):
    # Mocking connection response to return a pre-defined DataFrame
    mock_db = MagicMock()
    mock_conn.return_value = mock_db
    
    mock_df = pd.DataFrame([
        {"api_name": "GitHub", "avg_reliability_score": 99.5},
        {"api_name": "SpaceX", "avg_reliability_score": 97.2}
    ])
    mock_db.execute.return_value.fetch_df.return_value = mock_df
    
    analytics = ReliabilityAnalytics()
    res = analytics.top_reliable_apis(limit=2)
    
    assert len(res) == 2
    assert res["api_name"].iloc[0] == "GitHub"
    assert res["avg_reliability_score"].iloc[0] == 99.5

@patch("src.analytics.performance_analytics.PerformanceAnalytics._get_connection")
def test_performance_analytics(mock_conn):
    mock_db = MagicMock()
    mock_conn.return_value = mock_db
    
    mock_df = pd.DataFrame([
        {"api_name": "JSONPlaceholder", "avg_response_time_ms": 75.2},
        {"api_name": "GitHub", "avg_response_time_ms": 185.0}
    ])
    mock_db.execute.return_value.fetch_df.return_value = mock_df
    
    perf = PerformanceAnalytics()
    res = perf.fastest_apis(limit=2)
    
    assert len(res) == 2
    assert res["api_name"].iloc[0] == "JSONPlaceholder"
    assert res["avg_response_time_ms"].iloc[0] == 75.2

@patch("src.analytics.ranking_analytics.RankingAnalytics._get_connection")
def test_ranking_analytics_leaderboard(mock_conn):
    mock_db = MagicMock()
    mock_conn.return_value = mock_db
    
    mock_df = pd.DataFrame([
        {"api_name": "GitHub", "avg_reliability_score": 99.5, "avg_health_score": 98.2, "avg_sla_score": 99.0, "avg_response_time_ms": 180.0, "leaderboard_score": 98.96}
    ])
    mock_db.execute.return_value.fetch_df.return_value = mock_df
    
    rank = RankingAnalytics()
    res = rank.api_leaderboard()
    
    assert len(res) == 1
    assert "rank" in res.columns
    assert res["rank"].iloc[0] == 1
    assert res["api_name"].iloc[0] == "GitHub"
    assert res["leaderboard_score"].iloc[0] == 98.96

@patch("src.analytics.reporting.Reporting._get_connection")
def test_reporting_monthly_report(mock_conn):
    mock_db = MagicMock()
    mock_conn.return_value = mock_db
    
    mock_df = pd.DataFrame([
        {"api_name": "GitHub", "year": 2026, "month": 6, "avg_reliability_score": 99.5, "avg_sla_score": 99.0, "avg_health_score": 98.2, "avg_uptime_percentage": 99.7, "avg_error_rate": 0.3, "avg_response_time_ms": 180.0}
    ])
    mock_db.execute.return_value.fetch_df.return_value = mock_df
    
    rep = Reporting()
    res = rep.generate_monthly_report()
    
    assert len(res) == 1
    assert res["api_name"].iloc[0] == "GitHub"
    assert res["month"].iloc[0] == 6
