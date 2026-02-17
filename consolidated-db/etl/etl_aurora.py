"""
ETL script for Aurora Oracle Database
Extracts clinical events from PAZIENTI_ACCESSO2 view
Uses python-oracledb in thick mode with Oracle Instant Client
"""
import os
import logging
from datetime import datetime, timedelta
from db_connection import DatabaseConnection

try:
    import oracledb
    oracledb.init_oracle_client(lib_dir='/opt/oracle/instantclient_23_26')
    oracledb.defaults.fetch_lobs = False
    ORACLE_AVAILABLE = True
except Exception as e:
    ORACLE_AVAILABLE = False
    import logging as _l
    _l.getLogger(__name__).warning(f"oracledb not available: {e}")

logger = logging.getLogger(__name__)


class AuroraETL:
    def __init__(self):
        if not ORACLE_AVAILABLE:
            logger.warning("Oracle client not available - Aurora ETL disabled")
            self.db = DatabaseConnection()
            return

        self.host = os.getenv('AURORA_HOST', '10.30.208.195')
        self.port = int(os.getenv('AURORA_PORT', 1521))
        self.service = os.getenv('AURORA_SERVICE', 'E4CURE')
        self.user = os.getenv('AURORA_USER', 'PROG_PILI')
        self.password = os.getenv('AURORA_PASSWORD')
        self.db = DatabaseConnection()

        if not self.password:
            logger.warning("AURORA_PASSWORD not set - Aurora ETL will skip operations")

    def get_oracle_connection(self):
        if not ORACLE_AVAILABLE:
            return None
        try:
            dsn = f"{self.host}:{self.port}/{self.service}"
            conn = oracledb.connect(user=self.user, password=self.password, dsn=dsn)
            logger.info("Aurora Oracle DB connection successful (thick mode)")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to Aurora: {e}")
            return None

    def get_all_fiscal_codes(self):
        if not ORACLE_AVAILABLE:
            logger.warning("oracledb not available - cannot fetch fiscal codes from Aurora")
            return []
        conn = self.get_oracle_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT cf FROM PAZIENTI_ACCESSO2 WHERE cf IS NOT NULL ORDER BY cf"
            )
            fiscal_codes = [row[0].strip().upper() for row in cursor if row[0]]
            cursor.close()
            conn.close()
            logger.info(f"Fetched {len(fiscal_codes)} distinct fiscal codes from Aurora")
            return fiscal_codes
        except Exception as e:
            logger.error(f"Failed to fetch fiscal codes from Aurora: {e}")
            return []

    def fetch_patient_events(self, fiscal_code, lookback_months=12):
        if not ORACLE_AVAILABLE:
            return []
        try:
            conn = self.get_oracle_connection()
            if not conn:
                return []
            cursor = conn.cursor()
            lookback_date = datetime.now() - timedelta(days=lookback_months * 30)
            query = """
                SELECT
                    CODICE_FISCALE,
                    TIPO_ACCESSO,
                    DATA_ACCESSO,
                    DATA_DIMISSIONE,
                    DIAGNOSI,
                    CODICE_DIAGNOSI,
                    REPARTO,
                    UNITA_OPERATIVA
                FROM PAZIENTI_ACCESSO2
                WHERE CODICE_FISCALE = :fiscal_code
                AND DATA_ACCESSO >= :lookback_date
                ORDER BY DATA_ACCESSO DESC
            """
            cursor.execute(query, fiscal_code=fiscal_code, lookback_date=lookback_date)
            events = []
            for row in cursor:
                event = {
                    'fiscal_code': row[0],
                    'event_type': self.map_event_type(row[1]),
                    'event_date': row[2],
                    'discharge_date': row[3],
                    'diagnosis': row[4],
                    'diagnosis_code': row[5],
                    'department': row[6],
                    'ward': row[7]
                }
                events.append(event)
            cursor.close()
            conn.close()
            logger.info(f"Fetched {len(events)} events for patient {fiscal_code}")
            return events
        except Exception as e:
            logger.error(f"Failed to fetch events from Aurora: {e}")
            return []

    def map_event_type(self, raw_type):
        type_mapping = {
            'PS': 'ED_ACCESS',
            'RIC': 'HOSPITALIZATION',
            'AMB': 'OUTPATIENT',
            'DH': 'DAY_HOSPITAL'
        }
        return type_mapping.get(raw_type, raw_type)

    def upsert_clinical_event(self, event_data):
        if not event_data or not event_data.get('fiscal_code'):
            return False
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM patients WHERE fiscal_code = %s",
                    (event_data['fiscal_code'],)
                )
                if not cursor.fetchone():
                    logger.warning(f"Patient {event_data['fiscal_code']} not found, skipping event")
                    return False
                cursor.execute("""
                    INSERT INTO clinical_events (
                        fiscal_code, event_type, event_date, discharge_date,
                        diagnosis, diagnosis_code, department, ward,
                        source_system, updated_at
                    ) VALUES (
                        %(fiscal_code)s, %(event_type)s, %(event_date)s, %(discharge_date)s,
                        %(diagnosis)s, %(diagnosis_code)s, %(department)s, %(ward)s,
                        'AURORA', CURRENT_TIMESTAMP
                    )
                    ON CONFLICT DO NOTHING
                """, event_data)
                return True
        except Exception as e:
            logger.error(f"Failed to upsert clinical event: {e}")
            return False

    def sync_patient_events(self, fiscal_code):
        logger.info(f"Syncing clinical events from Aurora: {fiscal_code}")
        events = self.fetch_patient_events(fiscal_code)
        if not events:
            return 0, 0
        success_count = 0
        failed_count = 0
        for event in events:
            if self.upsert_clinical_event(event):
                success_count += 1
            else:
                failed_count += 1
        logger.info(f"Aurora sync completed for {fiscal_code}: {success_count} events inserted")
        return success_count, failed_count

    def sync_all_patients(self):
        logger.info("Starting Aurora ETL for all patients")
        self.db.update_etl_status('AURORA', 'RUNNING', 'ETL job started')
        total_success = 0
        total_failed = 0
        try:
            fiscal_codes = self.get_all_fiscal_codes()
            if not fiscal_codes:
                logger.info("Oracle unavailable, falling back to local patients table")
                with self.db.get_cursor() as cursor:
                    cursor.execute("SELECT fiscal_code FROM patients")
                    rows = cursor.fetchall()
                fiscal_codes = [row['fiscal_code'] for row in rows]
            for fiscal_code in fiscal_codes:
                success, failed = self.sync_patient_events(fiscal_code)
                total_success += success
                total_failed += failed
            status = 'SUCCESS' if total_failed == 0 else 'PARTIAL_SUCCESS'
            message = f"Processed {total_success} events, {total_failed} failed"
            self.db.update_etl_status('AURORA', status, message, total_success, total_failed)
            logger.info(f"Aurora ETL completed: {message}")
            return total_success, total_failed
        except Exception as e:
            logger.error(f"Aurora ETL failed: {e}")
            self.db.update_etl_status('AURORA', 'FAILED', str(e))
            return total_success, total_failed
