import argparse
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from src.utils.logger import setup_logger
from src.utils.config import load_config
from src.monitoring.api_monitor import APIMonitor
from src.processing.data_cleaner import DataCleaner
from src.processing.metric_calculator import MetricCalculator
from src.warehouse.warehouse_loader import WarehouseLoader
from src.analytics.reporting import Reporting
from src.utils.history_simulator import HistorySimulator
from src.monitoring.scheduler import MonitoringScheduler

logger = setup_logger()

def execute_etl_pipeline():
    """Runs a single pass of the monitoring check -> clean -> calculate -> warehouse load -> reports export."""
    logger.info("Pipeline: Initiating ETL pipeline cycle.")
    
    try:
        # 1. Run monitoring checks
        logger.info("Pipeline Step 1: Running API monitoring checks...")
        monitor = APIMonitor()
        monitor.run_all_checks()
        
        # 2. Run data cleaning
        logger.info("Pipeline Step 2: Running data cleaning...")
        cleaner = DataCleaner()
        cleaner.run()
        
        # 3. Calculate metrics
        logger.info("Pipeline Step 3: Calculating health and SLA metrics...")
        calculator = MetricCalculator()
        calculator.run()
        
        # 4. Load data warehouse
        logger.info("Pipeline Step 4: Loading warehouse data...")
        loader = WarehouseLoader()
        loader.run()
        
        # 5. Generate analytics export CSVs
        logger.info("Pipeline Step 5: Exporting analytics reports...")
        rep = Reporting()
        rep.export_report_csv()
        
        logger.info("Pipeline: ETL pipeline cycle completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Pipeline: ETL cycle encountered error: {str(e)}", exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description="API Observatory ETL Pipeline and Dashboard Runner")
    parser.add_argument("--simulate", action="store_true", help="Generate 30-day synthetic monitoring history")
    parser.add_argument("--start-ui", action="store_true", default=True, help="Start the NiceGUI dashboard (default: True)")
    parser.add_argument("--no-ui", action="store_false", dest="start_ui", help="Do not start the NiceGUI dashboard")
    parser.add_argument("--port", type=int, default=8080, help="NiceGUI dashboard port (default: 8080)")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("API Observatory Platform Starting")
    logger.info("=" * 60)
    
    # Optional Simulation Stage
    if args.simulate:
        logger.info("Pipeline: Running synthetic history simulation...")
        sim = HistorySimulator()
        sim.simulate_history(days=30)
        
    # Execute Pipeline
    pipeline_success = execute_etl_pipeline()
    if not pipeline_success:
        logger.warning("Pipeline: Pipeline run had failures. Checking logs for details.")

    # Start NiceGUI UI and Background Scheduler
    if args.start_ui:
        logger.info("Pipeline: Initializing background monitoring scheduler...")
        scheduler = MonitoringScheduler()
        scheduler.start_scheduler()
        
        logger.info("Pipeline: Launching NiceGUI Dashboard...")
        from nicegui import ui
        # Import the main index layout
        import ui.app as app_module
        
        # Start NiceGUI server
        ui.run(
            title="API Observatory Dashboard",
            dark=True,
            port=args.port,
            show=False  # Do not auto open browser window in server mode
        )
        
        # When UI stops (thread joins on exit), stop scheduler
        scheduler.stop_scheduler()
    else:
        logger.info("Pipeline: Execution complete (--no-ui passed). Exiting.")

if __name__ in {"__main__", "__mp_main__"}:
    main()
