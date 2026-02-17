"""
ETL Scheduler - Runs ETL jobs on a schedule
"""
import time
import schedule
import logging
from datetime import datetime
from dotenv import load_dotenv

from run_etl import ETLOrchestrator

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_etl_job():
    """Run full ETL pipeline"""
    logger.info("=" * 80)
    logger.info(f"Scheduled ETL job starting at {datetime.now()}")
    logger.info("=" * 80)

    try:
        orchestrator = ETLOrchestrator()
        # Run for all patients (fiscal_codes=None syncs all)
        orchestrator.run_full_etl(fiscal_codes=None)
        logger.info("Scheduled ETL job completed successfully")
    except Exception as e:
        logger.error(f"Scheduled ETL job failed: {e}")


def main():
    """Main scheduler loop"""
    logger.info("ETL Scheduler starting...")

    # Run nightly at 02:00
    schedule.every().day.at("02:00").do(run_etl_job)

    # Run immediately on startup to populate DB
    logger.info("Running initial ETL on startup...")
    run_etl_job()

    logger.info("ETL Scheduler running. Next run scheduled at 02:00 daily.")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
