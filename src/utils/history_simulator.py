import os
import random
import uuid
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from src.utils.config import load_config, get_path
from src.utils.logger import setup_logger

logger = setup_logger()

class HistorySimulator:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.raw_dir = get_path(self.config["database"]["paths"]["raw"]) / "monitoring_logs"
        self.apis = self.config.get("apis", ["GitHub", "StackExchange", "OpenLibrary", "JSONPlaceholder", "SpaceX", "CoinGecko"])

    def simulate_history(self, days: int = 30):
        """Generates synthetic history files under data/raw/monitoring_logs/."""
        logger.info(f"Simulator: Generating {days} days of historical monitoring records.")
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        # Define API behavior patterns
        api_profiles = {
            "GitHub": {"base_lat": 180, "jitter": 30, "uptime": 0.998, "size": 1200, "err_code": 503},
            "StackExchange": {"base_lat": 280, "jitter": 40, "uptime": 0.992, "size": 3500, "err_code": 500},
            "OpenLibrary": {"base_lat": 650, "jitter": 150, "uptime": 0.975, "size": 8500, "err_code": 504},
            "JSONPlaceholder": {"base_lat": 80, "jitter": 15, "uptime": 0.999, "size": 2200, "err_code": 502},
            "SpaceX": {"base_lat": 420, "jitter": 80, "uptime": 0.985, "size": 14000, "err_code": 500},
            "CoinGecko": {"base_lat": 310, "jitter": 60, "uptime": 0.945, "size": 4000, "err_code": 429} # Simulate rate limits (429)
        }

        current_day = start_time
        total_records = 0
        
        while current_day <= end_time:
            daily_records = []
            
            # Simulate 1 check every 30 minutes (48 checks per day per API)
            # This provides rich chart detail while keeping dataset sizes efficient
            for hour in range(24):
                for minute in [0, 30]:
                    check_time = current_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if check_time > end_time:
                        break
                        
                    for api in self.apis:
                        profile = api_profiles.get(api, {"base_lat": 300, "jitter": 50, "uptime": 0.98, "size": 5000, "err_code": 500})
                        
                        # Introduce a weekend effect (slightly slower latencies)
                        is_weekend = check_time.weekday() >= 5
                        weekend_mult = 1.15 if is_weekend else 1.0
                        
                        # Determine status
                        is_up = random.random() < profile["uptime"]
                        
                        # SpaceX has an occasional simulated outage block on some days
                        if api == "SpaceX" and check_time.day % 11 == 0 and 14 <= check_time.hour <= 17:
                            is_up = False
                            
                        # OpenLibrary has occasional morning latency spikes
                        lat_spike = 1.0
                        if api == "OpenLibrary" and 8 <= check_time.hour <= 10:
                            lat_spike = 2.0
                            
                        if is_up:
                            status_code = 200
                            response_time = (profile["base_lat"] * weekend_mult * lat_spike) + random.uniform(-profile["jitter"], profile["jitter"])
                            response_size = int(profile["size"] + random.uniform(-profile["size"]*0.1, profile["size"]*0.1))
                            availability_flag = 1
                            error_message = None
                        else:
                            status_code = profile["err_code"]
                            response_time = None
                            response_size = None
                            availability_flag = 0
                            if status_code == 429:
                                error_message = "Rate Limit Exceeded: 429 Too Many Requests"
                            elif status_code == 504:
                                error_message = "Gateway Timeout: 504"
                            else:
                                error_message = f"Internal Server Error: {status_code}"
                                
                        record = {
                            "monitoring_id": str(uuid.uuid4()),
                            "api_name": api,
                            "timestamp": check_time.isoformat(),
                            "status_code": status_code,
                            "response_time_ms": round(response_time, 2) if response_time else None,
                            "response_size_bytes": response_size,
                            "availability_flag": availability_flag,
                            "error_message": error_message
                        }
                        daily_records.append(record)
                        
            # Write one JSON file per simulated day
            if daily_records:
                date_str = current_day.strftime("%Y%m%d")
                file_path = self.raw_dir / f"simulated_checks_{date_str}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(daily_records, f, indent=4)
                total_records += len(daily_records)
                
            current_day += timedelta(days=1)
            
        logger.info(f"Simulator: Successfully generated {total_records} historical checks across {days} days.")
