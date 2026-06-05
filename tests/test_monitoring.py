import pytest
from unittest.mock import patch, MagicMock
import requests

from src.monitoring.api_checker import APIChecker, APICheckResult
from src.monitoring.api_monitor import APIMonitor

def test_api_checker_measurements():
    checker = APIChecker()
    assert checker.measure_response_time(123.456) == 123.46
    assert checker.calculate_availability(200) is True
    assert checker.calculate_availability(302) is True
    assert checker.calculate_availability(400) is False
    assert checker.calculate_availability(500) is False
    assert checker.calculate_availability(None) is False

def test_api_checker_capture_response_size():
    checker = APIChecker()
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Length": "1024"}
    mock_resp.content = b"x" * 1024
    assert checker.capture_response_size(mock_resp) == 1024
    
    # Fallback to len(content) if header missing
    mock_resp.headers = {}
    mock_resp.content = b"test content"
    assert checker.capture_response_size(mock_resp) == 12

@patch("src.monitoring.api_checker.requests.get")
def test_api_checker_check_api_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Length": "100"}
    mock_resp.content = b"a" * 100
    mock_get.return_value = mock_resp
    
    checker = APIChecker()
    result = checker.check_api("GitHub", "https://api.github.com")
    
    assert isinstance(result, APICheckResult)
    assert result.api_name == "GitHub"
    assert result.is_available is True
    assert result.status_code == 200
    assert result.response_size_bytes == 100
    assert result.error_message is None

@patch("src.monitoring.api_checker.requests.get")
def test_api_checker_check_api_failure_retry(mock_get):
    # Simulate a request exception followed by success
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.content = b"ok"
    
    # Fail first request, succeed on retry
    mock_get.side_effect = [requests.exceptions.Timeout("Timeout!"), mock_resp]
    
    checker = APIChecker(backoff_factor=0.01) # fast retry
    result = checker.check_api("GitHub", "https://api.github.com")
    
    assert result.is_available is True
    assert result.status_code == 200
    assert mock_get.call_count == 2

def test_api_monitor_load_registry():
    # Pass a custom config mapping to test load_api_registry
    with patch("src.monitoring.api_monitor.load_config") as mock_load:
        mock_load.return_value = {
            "timeout_seconds": 5,
            "apis": ["GitHub", {"name": "CustomAPI", "url": "https://api.custom.com", "category": "Custom"}],
            "database": {"paths": {"raw": "data/raw"}}
        }
        
        monitor = APIMonitor()
        registry = monitor.load_api_registry()
        
        assert len(registry) == 2
        assert registry[0]["name"] == "GitHub"
        assert registry[0]["category"] == "VCS"
        assert registry[1]["name"] == "CustomAPI"
        assert registry[1]["url"] == "https://api.custom.com"
        assert registry[1]["category"] == "Custom"
