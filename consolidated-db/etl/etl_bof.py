"""
ETL script for BOF API
Extracts protected discharge and care continuity data
"""
import os
import requests
import logging
from datetime import datetime
from db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class BofETL:
    def __init__(self):
        self.api_url = os.getenv('BOF_API_URL', 'https://bof.asst-brianza.it/api/v1/index.php')
        self.token = os.getenv('BOF_API_TOKEN')
        self.db = DatabaseConnection()

        if not self.token:
            raise ValueError("BOF_API_TOKEN environment variable is required")

    def fetch_patient_discharges(self, fiscal_code):
        """Fetch protected discharges for a patient from BOF API"""
        try:
            payload = {
                "token": self.token,
                "action": "dimissioniprotette.getpatitient",
                "data": fiscal_code
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # BOF API may return {"data": null} if no records found
                if data.get('data') is None:
                    logger.info(f"No discharge data found for patient {fiscal_code}")
                    return []

                # Extract discharge records (adjust based on actual API response structure)
                discharges = data.get('data', [])
                if not isinstance(discharges, list):
                    discharges = [discharges]

                logger.info(f"Fetched {len(discharges)} discharges for patient {fiscal_code}")
                return discharges

            else:
                logger.error(f"BOF API error: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch discharges from BOF: {e}")
            return []

    def transform_discharge_data(self, raw_data, fiscal_code):
        """Transform BOF API response to database schema using real field names."""
        if not raw_data:
            return None

        def parse_date(val):
            if not val:
                return None
            try:
                from datetime import datetime
                return datetime.strptime(val, '%d/%m/%Y').date()
            except Exception:
                return None

        transformed = {
            'fiscal_code': fiscal_code,
            'discharge_date': parse_date(raw_data.get('data_dimissione')),
            'discharge_type': raw_data.get('setting_finale_label'),
            'discharge_status': 'ACTIVE',
            'home_care_active': False,
            'home_care_provider': raw_data.get('territorio_destinazione_label'),
            'home_care_pathway': raw_data.get('servizi_attivati_label'),
            'palliative_care': False,
            'hospice': False,
            'social_services_active': raw_data.get('servizi_sociali_comuni') is not None,
            'social_services_notes': raw_data.get('servizi_sociali_comuni_label'),
            'sgdt_last_visit_date': None,
            'sgdt_last_visit_operator': raw_data.get('case_manager'),
            'sgdt_notes': raw_data.get('note'),
            'measure_b1_active': False,
            'nad_nutrition_active': False,
            'source_system': 'BOF',
            'source_record_id': str(raw_data.get('id')) if raw_data.get('id') else None
        }

        return transformed

    def upsert_protected_discharge(self, discharge_data):
        """Insert or update protected discharge in database"""
        if not discharge_data or not discharge_data.get('fiscal_code'):
            return False

        try:
            with self.db.get_cursor() as cursor:
                # Check if patient exists first (foreign key constraint)
                cursor.execute(
                    "SELECT 1 FROM patients WHERE fiscal_code = %s",
                    (discharge_data['fiscal_code'],)
                )
                if not cursor.fetchone():
                    logger.warning(f"Patient {discharge_data['fiscal_code']} not found, skipping discharge")
                    return False

                # Upsert protected discharge
                cursor.execute("""
                    INSERT INTO protected_discharges (
                        fiscal_code, discharge_date, discharge_type, discharge_status,
                        home_care_active, home_care_provider, home_care_pathway,
                        palliative_care, hospice,
                        social_services_active, social_services_notes,
                        sgdt_last_visit_date, sgdt_last_visit_operator, sgdt_notes,
                        measure_b1_active, nad_nutrition_active,
                        source_system, source_record_id, updated_at
                    ) VALUES (
                        %(fiscal_code)s, %(discharge_date)s, %(discharge_type)s, %(discharge_status)s,
                        %(home_care_active)s, %(home_care_provider)s, %(home_care_pathway)s,
                        %(palliative_care)s, %(hospice)s,
                        %(social_services_active)s, %(social_services_notes)s,
                        %(sgdt_last_visit_date)s, %(sgdt_last_visit_operator)s, %(sgdt_notes)s,
                        %(measure_b1_active)s, %(nad_nutrition_active)s,
                        %(source_system)s, %(source_record_id)s, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        discharge_status = EXCLUDED.discharge_status,
                        home_care_active = EXCLUDED.home_care_active,
                        home_care_provider = EXCLUDED.home_care_provider,
                        home_care_pathway = EXCLUDED.home_care_pathway,
                        palliative_care = EXCLUDED.palliative_care,
                        hospice = EXCLUDED.hospice,
                        social_services_active = EXCLUDED.social_services_active,
                        social_services_notes = EXCLUDED.social_services_notes,
                        sgdt_last_visit_date = EXCLUDED.sgdt_last_visit_date,
                        sgdt_last_visit_operator = EXCLUDED.sgdt_last_visit_operator,
                        sgdt_notes = EXCLUDED.sgdt_notes,
                        measure_b1_active = EXCLUDED.measure_b1_active,
                        nad_nutrition_active = EXCLUDED.nad_nutrition_active,
                        updated_at = CURRENT_TIMESTAMP
                """, discharge_data)

                logger.info(f"Protected discharge upserted for patient {discharge_data['fiscal_code']}")
                return True

        except Exception as e:
            logger.error(f"Failed to upsert protected discharge: {e}")
            return False

    def sync_patient_discharges(self, fiscal_code):
        """Full sync workflow for patient discharges"""
        logger.info(f"Syncing protected discharges from BOF: {fiscal_code}")

        # Step 1: Fetch from BOF API
        raw_discharges = self.fetch_patient_discharges(fiscal_code)
        if not raw_discharges:
            return 0, 0

        # Step 2: Transform and load
        success_count = 0
        failed_count = 0

        for raw_discharge in raw_discharges:
            discharge_data = self.transform_discharge_data(raw_discharge, fiscal_code)
            if discharge_data and self.upsert_protected_discharge(discharge_data):
                success_count += 1
            else:
                failed_count += 1

        logger.info(f"BOF sync completed for {fiscal_code}: {success_count} discharges processed")
        return success_count, failed_count

    def sync_all_patients(self):
        """Sync discharges for all patients in the database"""
        logger.info("Starting BOF ETL for all patients")

        self.db.update_etl_status('BOF', 'RUNNING', 'ETL job started')

        total_success = 0
        total_failed = 0

        try:
            # Get all fiscal codes from patients table
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT fiscal_code FROM patients")
                patients = cursor.fetchall()

            logger.info(f"Found {len(patients)} patients to sync")

            for patient in patients:
                fiscal_code = patient['fiscal_code']
                success, failed = self.sync_patient_discharges(fiscal_code)
                total_success += success
                total_failed += failed

            # Update ETL metadata
            status = 'SUCCESS' if total_failed == 0 else 'PARTIAL_SUCCESS'
            message = f"Processed {total_success} discharges, {total_failed} failed"
            self.db.update_etl_status('BOF', status, message, total_success, total_failed)

            logger.info(f"BOF ETL completed: {message}")
            return total_success, total_failed

        except Exception as e:
            logger.error(f"BOF ETL failed: {e}")
            self.db.update_etl_status('BOF', 'FAILED', str(e))
            return total_success, total_failed


if __name__ == "__main__":
    # Test BOF ETL
    logging.basicConfig(level=logging.INFO)

    etl = BofETL()

    # Test single patient sync
    test_fiscal_code = "RSSMRA85M01F205X"
    etl.sync_patient_discharges(test_fiscal_code)
