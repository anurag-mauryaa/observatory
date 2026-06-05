import time
import threading
import schedule
from pathlib import Path
from typing import Optional

from src.utils.config import load_config
from src.utils.logger import setup_logger
from src.monitoring.api_monitor import APIMonitor

logger = setup_logger()

class MonitoringScheduler:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = load_config(config_path)
        self.interval_minutes = self.config.get("monitor_interval_minutes", 15)
        self.api_monitor = APIMonitor(config_path)
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None

    def run_monitoring_cycle(self):
        """Runs the monitoring checks followed by the processing and warehouse update."""
        logger.info("Scheduler: Starting execution of monitoring cycle.")
        try:
            # 1. Run monitoring checks
            self.api_monitor.run_all_checks()
            
            # 2. Run Processing & ETL steps dynamically to keep the warehouse updated
            try:
                from src.processing.data_cleaner import DataCleaner
                from src.processing.metric_calculator import MetricCalculator
                from src.warehouse.warehouse_loader import WarehouseLoader
                
                logger.info("Scheduler: Running data cleaner...")
                cleaner = DataCleaner()
                cleaner.run()
                
                logger.info("Scheduler: Running metric calculator...")
                calculator = MetricCalculator()
                calculator.run()
                
                logger.info("Scheduler: Running warehouse loader...")
                loader = WarehouseLoader()
                loader.run()
                
                logger.info("Scheduler: Monitoring cycle and ETL pipeline completed successfully.")
            except ImportError as ie:
                logger.warning(f"Scheduler: ETL modules could not be imported yet. Check results saved. Error: {ie}")
                
        except Exception as e:
            logger.error(f"Scheduler: Error during monitoring cycle: {str(e)}", exc_info=True)

    def start_scheduler(self):
        """Starts the scheduler in a background daemon thread."""
        if self.thread is not None and self.thread.is_alive():
            logger.warning("Scheduler: Thread is already active.")
            return

        self.stop_event.clear()
        
        # Schedule the job
        schedule.every(self.interval_minutes).minutes.do(self.run_monitoring_cycle)
        
        # Trigger an initial check immediately for instant feedback
        # We run it in a separate thread so it doesn't block startup
        initial_check_thread = threading.Thread(target=self.run_monitoring_cycle, daemon=True)
        initial_check_thread.start()

        def _run_loop():
            while not self.stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)

        self.thread = threading.Thread(target=_run_loop, daemon=True)
        self.thread.start()
        logger.info(f"Scheduler: Monitoring Scheduler started. Interval: {self.interval_minutes} min(s).")

    def stop_scheduler(self):
        """Stops the scheduler and cancels pending runs."""
        if self.thread is None:
            logger.warning("Scheduler: No active thread to stop.")
            return
            
        logger.info("Scheduler: Initiating shutdown...")
        self.stop_event.set()
        schedule.clear()
        self.thread.join(timeout=5)
        self.thread = None
        logger.info("Scheduler: Shutdown complete.")
