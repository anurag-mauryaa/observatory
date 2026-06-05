import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from src.utils.config import load_config, get_path
from src.utils.constants import DEFAULT_API_REGISTRY
from src.utils.logger import setup_logger
from src.monitoring.api_checker import APIChecker, APICheckResult

logger = setup_logger()

class APIMonitor:
    def __init__(self, config_path: Path = None):
        self.config = load_config(config_path)
        self.timeout_seconds = self.config.get("timeout_seconds", 10)
        self.checker = APIChecker(timeout_seconds=self.timeout_seconds)
        self.api_registry = self.load_api_registry()
        
    def load_api_registry(self) -> List[Dict[str, str]]:
        """Loads APIs from config and resolves their URLs and categories."""
        apis_in_config = self.config.get("apis", [])
        resolved_apis = []
        
        for item in apis_in_config:
            if isinstance(item, str):
                name = item
                # Resolve url and category from constants registry
                if name in DEFAULT_API_REGISTRY:
                    resolved_apis.append({
                        "name": name,
                        "url": DEFAULT_API_REGISTRY[name]["url"],
                        "category": DEFAULT_API_REGISTRY[name]["category"]
                    })
                else:
                    # Generic fallback URL if not in DEFAULT_API_REGISTRY
                    logger.warning(f"API '{name}' not found in default registry. Using placeholder URL.")
                    resolved_apis.append({
                        "name": name,
                        "url": f"https://api.{name.lower()}.com",
                        "category": "Other"
                    })
            elif isinstance(item, dict):
                # If custom dict is passed in config
                name = item.get("name")
                url = item.get("url")
                category = item.get("category", "Other")
                if name and url:
                    resolved_apis.append({
                        "name": name,
                        "url": url,
                        "category": category
                    })
        return resolved_apis

    def run_single_check(self, api_name: str, api_url: str) -> APICheckResult:
        """Executes a monitoring check for a single API."""
        return self.checker.check_api(api_name, api_url)

    def run_all_checks(self) -> List[Dict[str, Any]]:
        """Executes monitoring checks for all registered APIs."""
        logger.info(f"Starting monitoring cycle for {len(self.api_registry)} APIs.")
        raw_results = []
        
        for api in self.api_registry:
            result = self.run_single_check(api["name"], api["url"])
            
            # Construct raw monitoring schema dictionary
            raw_record = {
                "monitoring_id": str(uuid.uuid4()),
                "api_name": result.api_name,
                "timestamp": result.timestamp,
                "status_code": result.status_code,
                "response_time_ms": result.response_time_ms,
                "response_size_bytes": result.response_size_bytes,
                "availability_flag": 1 if result.is_available else 0,
                "error_message": result.error_message
            }
            raw_results.append(raw_record)
            
        self.save_monitoring_results(raw_results)
        return raw_results

    def save_monitoring_results(self, results: List[Dict[str, Any]]):
        """Saves check records to the Raw Data Lake under raw/monitoring_logs/."""
        if not results:
            return
            
        raw_dir = get_path(self.config["database"]["paths"]["raw"]) / "monitoring_logs"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each run using a unique timestamp/uuid file name
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_name = f"raw_checks_{timestamp_str}_{uuid.uuid4().hex[:8]}.json"
        file_path = raw_dir / file_name
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
            
        logger.info(f"Saved {len(results)} monitoring results to {file_path.name}")
