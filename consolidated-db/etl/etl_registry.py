"""
ETL script for Central Patient Registry
Extracts patient demographic and anagraphic data
"""
import os
import requests
import logging
from datetime import datetime
from db_connection import DatabaseConnection

logger = logging.getLogger(__name__)


class RegistryETL:
    def __init__(self):
        self.api_url = os.getenv('REGISTRY_API_URL', 'https://clumiddle.aodv.local/AC/pac/rest/paziente')
        self.timeout = int(os.getenv('REGISTRY_API_TIMEOUT', 30))
        self.db = DatabaseConnection()

    def fetch_patient(self, fiscal_code):
        """Fetch single patient from Registry API"""
        try:
            url = f"{self.api_url}/{fiscal_code}"
            response = requests.get(url, verify=False, timeout=self.timeout)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Patient not found: {fiscal_code}")
                return None
            else:
                logger.error(f"Registry API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Failed to fetch patient {fiscal_code}: {e}")
            return None

    def transform_patient_data(self, raw_data):
        """Transform Registry API response to database schema"""
        if not raw_data:
            return None

        # Map API fields to database schema
        # Note: Field mapping will need adjustment based on actual API response structure
        transformed = {
            'fiscal_code': raw_data.get('codiceFiscale'),
            'first_name': raw_data.get('nome'),
            'last_name': raw_data.get('cognome'),
            'birth_date': raw_data.get('dataNascita'),
            'sex': raw_data.get('sesso'),
            'residence_address': raw_data.get('indirizzoResidenza'),
            'domicile_address': raw_data.get('indirizzoDomicilio'),
            'phone_numbers': raw_data.get('telefoni', []),  # JSONB array
            'email': raw_data.get('email'),
            'primary_doctor_name': raw_data.get('medicoCurante', {}).get('nome'),
            'primary_doctor_email': raw_data.get('medicoCurante', {}).get('email'),
            'exemptions': raw_data.get('esenzioni', []),  # JSONB array
            'disability_status': raw_data.get('invalidita', False),
            'disability_details': raw_data.get('invaliditaDettagli'),
            'cps_active': raw_data.get('servizioPS', False),
            'noa_sert_active': raw_data.get('servizioNOA', False),
            'caregiver_name': raw_data.get('caregiver', {}).get('nome'),
            'caregiver_relationship': raw_data.get('caregiver', {}).get('relazione'),
            'caregiver_phone': raw_data.get('caregiver', {}).get('telefono'),
            'source_system': 'CENTRAL_REGISTRY',
            'last_validated': datetime.now()
        }

        return transformed

    def upsert_patient(self, patient_data):
        """Insert or update patient in database"""
        if not patient_data or not patient_data.get('fiscal_code'):
            return False

        try:
            with self.db.get_cursor() as cursor:
                # Use PostgreSQL UPSERT (INSERT ... ON CONFLICT UPDATE)
                cursor.execute("""
                    INSERT INTO patients (
                        fiscal_code, first_name, last_name, birth_date, sex,
                        residence_address, domicile_address, phone_numbers, email,
                        primary_doctor_name, primary_doctor_email, exemptions,
                        disability_status, disability_details,
                        cps_active, noa_sert_active,
                        caregiver_name, caregiver_relationship, caregiver_phone,
                        source_system, last_validated, updated_at
                    ) VALUES (
                        %(fiscal_code)s, %(first_name)s, %(last_name)s, %(birth_date)s, %(sex)s,
                        %(residence_address)s, %(domicile_address)s, %(phone_numbers)s, %(email)s,
                        %(primary_doctor_name)s, %(primary_doctor_email)s, %(exemptions)s,
                        %(disability_status)s, %(disability_details)s,
                        %(cps_active)s, %(noa_sert_active)s,
                        %(caregiver_name)s, %(caregiver_relationship)s, %(caregiver_phone)s,
                        %(source_system)s, %(last_validated)s, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (fiscal_code) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        birth_date = EXCLUDED.birth_date,
                        sex = EXCLUDED.sex,
                        residence_address = EXCLUDED.residence_address,
                        domicile_address = EXCLUDED.domicile_address,
                        phone_numbers = EXCLUDED.phone_numbers,
                        email = EXCLUDED.email,
                        primary_doctor_name = EXCLUDED.primary_doctor_name,
                        primary_doctor_email = EXCLUDED.primary_doctor_email,
                        exemptions = EXCLUDED.exemptions,
                        disability_status = EXCLUDED.disability_status,
                        disability_details = EXCLUDED.disability_details,
                        cps_active = EXCLUDED.cps_active,
                        noa_sert_active = EXCLUDED.noa_sert_active,
                        caregiver_name = EXCLUDED.caregiver_name,
                        caregiver_relationship = EXCLUDED.caregiver_relationship,
                        caregiver_phone = EXCLUDED.caregiver_phone,
                        last_validated = EXCLUDED.last_validated,
                        updated_at = CURRENT_TIMESTAMP
                """, patient_data)

                logger.info(f"Patient upserted: {patient_data['fiscal_code']}")
                return True

        except Exception as e:
            logger.error(f"Failed to upsert patient: {e}")
            return False

    def sync_patient(self, fiscal_code):
        """Full sync workflow for single patient"""
        logger.info(f"Syncing patient from Registry: {fiscal_code}")

        # Step 1: Fetch from API
        raw_data = self.fetch_patient(fiscal_code)
        if not raw_data:
            return False

        # Step 2: Transform
        patient_data = self.transform_patient_data(raw_data)
        if not patient_data:
            return False

        # Step 3: Load to database
        success = self.upsert_patient(patient_data)

        return success

    def sync_patient_list(self, fiscal_codes):
        """Sync multiple patients"""
        logger.info(f"Starting Registry ETL for {len(fiscal_codes)} patients")

        success_count = 0
        failed_count = 0

        self.db.update_etl_status('CENTRAL_REGISTRY', 'RUNNING', 'ETL job started')

        for fiscal_code in fiscal_codes:
            if self.sync_patient(fiscal_code):
                success_count += 1
            else:
                failed_count += 1

        # Update ETL metadata
        status = 'SUCCESS' if failed_count == 0 else 'PARTIAL_SUCCESS'
        message = f"Processed {success_count} patients, {failed_count} failed"
        self.db.update_etl_status('CENTRAL_REGISTRY', status, message, success_count, failed_count)

        logger.info(f"Registry ETL completed: {message}")
        return success_count, failed_count


if __name__ == "__main__":
    # Test with sample fiscal code
    logging.basicConfig(level=logging.INFO)

    etl = RegistryETL()

    # Test single patient sync
    test_fiscal_code = "RSSMRA85M01F205X"
    etl.sync_patient(test_fiscal_code)
