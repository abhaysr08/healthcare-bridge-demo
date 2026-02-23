"""
ETL script for Prosthetics Warehouse Oracle DB (NFS)
Extracts warehouse movements and materials assigned to patients
Source: azeuro.CLIENTE_ASSISTANT view
"""
import os
import logging
from datetime import datetime
from db_connection import DatabaseConnection

import oracledb

logger = logging.getLogger(__name__)

ORACLE_CLIENT_LIB = '/opt/oracle/instantclient_23_26'
PROSTHETICS_HOST = os.getenv('PROSTHETICS_HOST', '10.30.208.232')
PROSTHETICS_PORT = os.getenv('PROSTHETICS_PORT', '1521')
PROSTHETICS_SERVICE = os.getenv('PROSTHETICS_SERVICE', 'NFS')
PROSTHETICS_USER = os.getenv('PROSTHETICS_USER', 'PROG_PILI')
PROSTHETICS_PASSWORD = os.getenv('PROSTHETICS_PASSWORD', 'ProgPili.2025!')


class ProstheticsETL:
    def __init__(self):
        self.dsn = f"{PROSTHETICS_HOST}:{PROSTHETICS_PORT}/{PROSTHETICS_SERVICE}"
        self.db = DatabaseConnection()
        self._oracle_initialized = False

    def _init_oracle(self):
        if not self._oracle_initialized:
            oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_LIB)
            self._oracle_initialized = True

    def get_connection(self):
        self._init_oracle()
        return oracledb.connect(
            user=PROSTHETICS_USER,
            password=PROSTHETICS_PASSWORD,
            dsn=self.dsn
        )

    def fetch_patient_items(self, fiscal_code):
        """Fetch all prosthetic items assigned to a patient."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    TIPOOP, IDPRESCR, DISTRETTO, DTEROG,
                    CODFORN, DSFORN,
                    MARCA, MODELLO,
                    COD_NFS, DESC_NFS,
                    QTA, PREZZO, TOTPRESCR,
                    BOLLA, STATO, DATAINVIO
                FROM azeuro.CLIENTE_ASSISTANT
                WHERE CFASS = :fiscal_code
                ORDER BY DTEROG DESC
            """, fiscal_code=fiscal_code)

            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            logger.info(f"Fetched {len(rows)} prosthetic items for {fiscal_code}")
            return rows

        except Exception as e:
            logger.error(f"Failed to fetch prosthetics for {fiscal_code}: {e}")
            return []

    def transform_item(self, raw, fiscal_code):
        """Transform a single prosthetics row to DB schema."""
        def to_float(val):
            try:
                return float(str(val).strip()) if val else None
            except Exception:
                return None

        return {
            'fiscal_code': fiscal_code,
            'prescription_id': str(raw.get('IDPRESCR', '')).strip() or None,
            'delivery_note': str(raw.get('BOLLA', '')).strip() or None,
            'delivery_date': raw.get('DTEROG'),
            'send_date': raw.get('DATAINVIO'),
            'supplier_code': str(raw.get('CODFORN', '')).strip() or None,
            'supplier_name': str(raw.get('DSFORN', '')).strip() or None,
            'product_code': str(raw.get('COD_NFS', '')).strip() or None,
            'product_description': str(raw.get('DESC_NFS', '')).strip() or None,
            'brand': str(raw.get('MARCA', '')).strip() or None,
            'model': str(raw.get('MODELLO', '')).strip() or None,
            'quantity': str(raw.get('QTA', '')).strip() or None,
            'unit_price': to_float(raw.get('PREZZO')),
            'total_price': to_float(raw.get('TOTPRESCR')),
            'district': str(raw.get('DISTRETTO', '')).strip() or None,
            'status': str(raw.get('STATO', '')).strip() or None,
            'operation_type': str(raw.get('TIPOOP', '')).strip() or None,
            'source_system': 'PROSTHETICS_NFS',
        }

    def upsert_item(self, item_data):
        """Insert or update a prosthetics item."""
        if not item_data or not item_data.get('fiscal_code'):
            return False

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM patients WHERE fiscal_code = %s",
                    (item_data['fiscal_code'],)
                )
                if not cursor.fetchone():
                    logger.warning(f"Patient {item_data['fiscal_code']} not in DB, skipping")
                    return False

                cursor.execute("""
                    INSERT INTO prosthetics_items (
                        fiscal_code, prescription_id, delivery_note,
                        delivery_date, send_date,
                        supplier_code, supplier_name,
                        product_code, product_description, brand, model,
                        quantity, unit_price, total_price,
                        district, status, operation_type,
                        source_system, updated_at
                    ) VALUES (
                        %(fiscal_code)s, %(prescription_id)s, %(delivery_note)s,
                        %(delivery_date)s, %(send_date)s,
                        %(supplier_code)s, %(supplier_name)s,
                        %(product_code)s, %(product_description)s, %(brand)s, %(model)s,
                        %(quantity)s, %(unit_price)s, %(total_price)s,
                        %(district)s, %(status)s, %(operation_type)s,
                        %(source_system)s, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (fiscal_code, prescription_id) DO UPDATE SET
                        delivery_note = EXCLUDED.delivery_note,
                        delivery_date = EXCLUDED.delivery_date,
                        send_date = EXCLUDED.send_date,
                        supplier_code = EXCLUDED.supplier_code,
                        supplier_name = EXCLUDED.supplier_name,
                        product_code = EXCLUDED.product_code,
                        product_description = EXCLUDED.product_description,
                        brand = EXCLUDED.brand,
                        model = EXCLUDED.model,
                        quantity = EXCLUDED.quantity,
                        unit_price = EXCLUDED.unit_price,
                        total_price = EXCLUDED.total_price,
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                """, item_data)

                return True

        except Exception as e:
            logger.error(f"Failed to upsert prosthetics item: {e}")
            return False

    def sync_patient_items(self, fiscal_code):
        """Sync all prosthetic items for a patient."""
        logger.info(f"Syncing prosthetics for {fiscal_code}")

        rows = self.fetch_patient_items(fiscal_code)
        if not rows:
            return 0, 0

        success, failed = 0, 0
        for row in rows:
            item = self.transform_item(row, fiscal_code)
            if self.upsert_item(item):
                success += 1
            else:
                failed += 1

        logger.info(f"Prosthetics sync for {fiscal_code}: {success} ok, {failed} failed")
        return success, failed

    def sync_all_patients(self):
        """Sync prosthetics for all patients in the DB."""
        logger.info("Starting Prosthetics ETL for all patients")
        self.db.update_etl_status('PROSTHETICS_NFS', 'RUNNING', 'ETL job started')

        total_success, total_failed = 0, 0

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT fiscal_code FROM patients")
                patients = cursor.fetchall()

            logger.info(f"Found {len(patients)} patients to sync")

            for patient in patients:
                s, f = self.sync_patient_items(patient['fiscal_code'])
                total_success += s
                total_failed += f

            status = 'SUCCESS' if total_failed == 0 else 'PARTIAL_SUCCESS'
            message = f"Processed {total_success} items, {total_failed} failed"
            self.db.update_etl_status('PROSTHETICS_NFS', status, message, total_success, total_failed)

            logger.info(f"Prosthetics ETL completed: {message}")
            return total_success, total_failed

        except Exception as e:
            logger.error(f"Prosthetics ETL failed: {e}")
            self.db.update_etl_status('PROSTHETICS_NFS', 'FAILED', str(e))
            return total_success, total_failed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    etl = ProstheticsETL()
    etl.sync_patient_items("CNFDDR53S12D038O")
