import time
import requests
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import logging

from src.utils.logger import setup_logger

logger = setup_logger()

@dataclass
class APICheckResult:
    api_name: str
    api_url: str
    timestamp: str  # ISO 8601 UTC format
    status_code: Optional[int]
    response_time_ms: Optional[float]
    response_size_bytes: Optional[int]
    is_available: bool
    error_message: Optional[str]

class APIChecker:
    def __init__(self, timeout_seconds: int = 10, max_retries: int = 3, backoff_factor: float = 1.5):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def check_api(self, api_name: str, api_url: str) -> APICheckResult:
        """Runs the API check with retry mechanism and returns APICheckResult."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        attempt = 0
        status_code = None
        response_time_ms = None
        response_size_bytes = None
        is_available = False
        error_message = None
        
        while attempt <= self.max_retries:
            try:
                start_time = time.perf_counter()
                
                # Perform the GET request
                # Note: We use headers like User-Agent to avoid issues with some APIs (like GitHub or SpaceX) that block default python-requests
                headers = {"User-Agent": "API-Observatory/1.0"}
                response = requests.get(api_url, timeout=self.timeout_seconds, headers=headers)
                
                duration = (time.perf_counter() - start_time) * 1000
                
                status_code = self.capture_status_code(response)
                response_time_ms = self.measure_response_time(duration)
                response_size_bytes = self.capture_response_size(response)
                is_available = self.calculate_availability(status_code)
                
                if is_available:
                    error_message = None
                    break
                else:
                    error_message = f"HTTP Error: Status Code {status_code}"
                    
            except requests.exceptions.Timeout as e:
                error_message = f"Timeout error: {str(e)}"
            except requests.exceptions.RequestException as e:
                error_message = f"Request error: {str(e)}"
            except Exception as e:
                error_message = f"Unexpected error: {str(e)}"
                
            attempt += 1
            if attempt <= self.max_retries:
                sleep_time = self.backoff_factor ** attempt
                logger.warning(
                    f"Check failed for {api_name} at {api_url} (Attempt {attempt}/{self.max_retries + 1}). "
                    f"Retrying in {sleep_time:.2f}s. Error: {error_message}"
                )
                time.sleep(sleep_time)
        
        # If still not available and error occurred, availability is False
        if not is_available:
            logger.error(f"API monitoring check failed for {api_name} ({api_url}). Error: {error_message}")
        else:
            logger.info(f"API monitoring check succeeded for {api_name} ({api_url}). Status: {status_code}, {response_time_ms:.1f}ms")
            
        return APICheckResult(
            api_name=api_name,
            api_url=api_url,
            timestamp=timestamp,
            status_code=status_code,
            response_time_ms=response_time_ms,
            response_size_bytes=response_size_bytes,
            is_available=is_available,
            error_message=error_message
        )

    def measure_response_time(self, duration_ms: float) -> float:
        """Returns the measured response time in milliseconds."""
        return round(duration_ms, 2)

    def capture_status_code(self, response: requests.Response) -> int:
        """Extracts status code from HTTP response."""
        return response.status_code

    def capture_response_size(self, response: requests.Response) -> int:
        """Calculates size of response in bytes."""
        if 'Content-Length' in response.headers:
            try:
                return int(response.headers['Content-Length'])
            except ValueError:
                pass
        # Fallback to len of content
        return len(response.content)

    def calculate_availability(self, status_code: Optional[int]) -> bool:
        """Determines availability based on HTTP status code."""
        if status_code is None:
            return False
        # Available if status is 2xx or 3xx
        return 200 <= status_code < 400
