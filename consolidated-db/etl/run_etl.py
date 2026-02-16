"""
Main ETL orchestrator
Runs all ETL jobs in sequence with proper error handling
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

from db_connection import DatabaseConnection
from etl_registry import RegistryETL
from etl_aurora import AuroraETL
from etl_bof import BofETL

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/healthbridge/etl.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ETLOrchestrator:
    def __init__(self):
        self.db = DatabaseConnection()
        self.registry_etl = None
        self.aurora_etl = None
        self.bof_etl = None

    def test_connections(self):
        """Test all connections before starting ETL"""
        logger.info("Testing database connections...")

        # Test PostgreSQL
        if not self.db.test_connection():
            logger.error("PostgreSQL connection failed")
            return False

        # Test Registry ETL
        try:
            self.registry_etl = RegistryETL()
            logger.info("Registry ETL initialized")
        except Exception as e:
            logger.error(f"Registry ETL initialization failed: {e}")
            return False

        # Test Aurora ETL
        try:
            self.aurora_etl = AuroraETL()
            logger.info("Aurora ETL initialized")
        except Exception as e:
            logger.error(f"Aurora ETL initialization failed: {e}")
            return False

        # Test BOF ETL
        try:
            self.bof_etl = BofETL()
            logger.info("BOF ETL initialized")
        except Exception as e:
            logger.error(f"BOF ETL initialization failed: {e}")
            return False

        logger.info("All connections tested successfully")
        return True

    def run_full_etl(self, fiscal_codes=None):
        """
        Run complete ETL pipeline

        Args:
            fiscal_codes: List of fiscal codes to sync. If None, sync all patients.
        """
        logger.info("=" * 80)
        logger.info(f"Starting full ETL run at {datetime.now()}")
        logger.info("=" * 80)

        if not self.test_connections():
            logger.error("Connection tests failed, aborting ETL")
            return False

        total_stats = {
            'registry': {'success': 0, 'failed': 0},
            'aurora': {'success': 0, 'failed': 0},
            'bof': {'success': 0, 'failed': 0}
        }

        # Step 1: Sync Registry (must run first - creates patient records)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Syncing Central Patient Registry")
        logger.info("=" * 80)

        if fiscal_codes:
            success, failed = self.registry_etl.sync_patient_list(fiscal_codes)
            total_stats['registry']['success'] = success
            total_stats['registry']['failed'] = failed
        else:
            logger.warning("No fiscal codes provided for Registry sync")

        # Step 2: Sync Aurora (requires patients to exist)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Syncing Aurora Clinical Events")
        logger.info("=" * 80)

        if fiscal_codes:
            for fiscal_code in fiscal_codes:
                success, failed = self.aurora_etl.sync_patient_events(fiscal_code)
                total_stats['aurora']['success'] += success
                total_stats['aurora']['failed'] += failed
        else:
            success, failed = self.aurora_etl.sync_all_patients()
            total_stats['aurora']['success'] = success
            total_stats['aurora']['failed'] = failed

        # Step 3: Sync BOF (requires patients to exist)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Syncing BOF Protected Discharges")
        logger.info("=" * 80)

        if fiscal_codes:
            for fiscal_code in fiscal_codes:
                success, failed = self.bof_etl.sync_patient_discharges(fiscal_code)
                total_stats['bof']['success'] += success
                total_stats['bof']['failed'] += failed
        else:
            success, failed = self.bof_etl.sync_all_patients()
            total_stats['bof']['success'] = success
            total_stats['bof']['failed'] = failed

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("ETL RUN SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Registry: {total_stats['registry']['success']} success, {total_stats['registry']['failed']} failed")
        logger.info(f"Aurora:   {total_stats['aurora']['success']} success, {total_stats['aurora']['failed']} failed")
        logger.info(f"BOF:      {total_stats['bof']['success']} success, {total_stats['bof']['failed']} failed")
        logger.info("=" * 80)

        total_failed = sum(s['failed'] for s in total_stats.values())
        if total_failed == 0:
            logger.info("ETL completed successfully with no errors")
            return True
        else:
            logger.warning(f"ETL completed with {total_failed} total errors")
            return False


def main():
    """Main entry point"""
    orchestrator = ETLOrchestrator()

    # Example: Sync specific patients
    test_patients = [
        "RSSMRA85M01F205X",
        # Add more fiscal codes here
    ]

    # Run ETL
    success = orchestrator.run_full_etl(fiscal_codes=test_patients)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
