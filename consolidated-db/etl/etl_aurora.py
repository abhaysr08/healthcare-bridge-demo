"""
ETL script for Aurora Oracle Database
Extracts clinical events from PAZIENTI_ACCESSO2 view

Real column names (confirmed from DB):
  ID_ANAG, COGNOME, NOME, CF, SESSO, DATA_NASCITA,
  TIPO_ACCESSO, NUMERO_EPISODIO, DATA_ACCETTAZIONE,
  DATA_DIMISSIONE, STRUTTURA, PRESIDIO, DIAGNOSI_ACC

Uses python-oracledb in thick mode with Oracle Instant Client
"""
import os
import logging
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
        self.host     = os.getenv('AURORA_HOST', '10.30.208.195')
        self.port     = int(os.getenv('AURORA_PORT', 1521))
        self.service  = os.getenv('AURORA_SERVICE', 'E4CURE')
        self.user     = os.getenv('AURORA_USER', 'PROG_PILI')
        self.password = os.getenv('AURORA_PASSWORD')
        self.db       = DatabaseConnection()

        if not ORACLE_AVAILABLE:
            logger.warning("Oracle client not available - Aurora ETL disabled")
        if not self.password:
            logger.warning("AURORA_PASSWORD not set - Aurora ETL will be skipped")

    def get_oracle_connection(self):
        if not ORACLE_AVAILABLE or not self.password:
            return None
        try:
            dsn  = f"{self.host}:{self.port}/{self.service}"
            conn = oracledb.connect(user=self.user, password=self.password, dsn=dsn)
            logger.info("Aurora Oracle connection successful (thick mode)")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to Aurora: {e}")
            return None

    # ------------------------------------------------------------------
    # Fetch all distinct fiscal codes (source of truth for patient list)
    # ------------------------------------------------------------------
    def get_all_fiscal_codes(self):
        if not ORACLE_AVAILABLE:
            logger.warning("oracledb not available - cannot fetch fiscal codes")
            return []
        conn = self.get_oracle_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT CF FROM PAZIENTI_ACCESSO2 WHERE CF IS NOT NULL ORDER BY CF"
            )
            fiscal_codes = [row[0].strip().upper() for row in cursor if row[0]]
            cursor.close()
            conn.close()
            logger.info(f"Fetched {len(fiscal_codes)} distinct fiscal codes from Aurora")
            return fiscal_codes
        except Exception as e:
            logger.error(f"Failed to fetch fiscal codes from Aurora: {e}")
            return []

    # ------------------------------------------------------------------
    # Fetch all clinical events for a single patient
    # ------------------------------------------------------------------
    def fetch_patient_events(self, fiscal_code):
        if not ORACLE_AVAILABLE or not self.password:
            return []
        conn = self.get_oracle_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    CF,
                    NUMERO_EPISODIO,
                    TIPO_ACCESSO,
                    DATA_ACCETTAZIONE,
                    DATA_DIMISSIONE,
                    STRUTTURA,
                    PRESIDIO,
                    DIAGNOSI_ACC
                FROM PAZIENTI_ACCESSO2
                WHERE CF = :fiscal_code
                ORDER BY DATA_ACCETTAZIONE DESC
            """, fiscal_code=fiscal_code)

            events = []
            for row in cursor:
                events.append({
                    'fiscal_code':    row[0].strip().upper() if row[0] else None,
                    'episode_number': str(row[1]) if row[1] else None,
                    'event_type':     row[2],
                    'admission_date': row[3],
                    'discharge_date': row[4],
                    'structure':      row[5],
                    'hospital_unit':  row[6],
                    'diagnosis':      row[7],
                })
            cursor.close()
            conn.close()
            logger.info(f"Fetched {len(events)} events for {fiscal_code}")
            return events
        except Exception as e:
            logger.error(f"Failed to fetch events for {fiscal_code}: {e}")
            return []

    # ------------------------------------------------------------------
    # Upsert a single clinical event (idempotent via episode_number)
    # ------------------------------------------------------------------
    def upsert_clinical_event(self, event):
        if not event or not event.get('fiscal_code'):
            return False
        try:
            with self.db.get_cursor() as cursor:
                # Ensure patient record exists (FK constraint)
                cursor.execute(
                    "SELECT 1 FROM patients WHERE fiscal_code = %s",
                    (event['fiscal_code'],)
                )
                if not cursor.fetchone():
                    logger.warning(f"Patient {event['fiscal_code']} not in DB, skipping event")
                    return False

                cursor.execute("""
                    INSERT INTO clinical_events (
                        fiscal_code, episode_number, event_type,
                        admission_date, discharge_date,
                        structure, hospital_unit, diagnosis,
                        source_system, updated_at
                    ) VALUES (
                        %(fiscal_code)s, %(episode_number)s, %(event_type)s,
                        %(admission_date)s, %(discharge_date)s,
                        %(structure)s, %(hospital_unit)s, %(diagnosis)s,
                        'AURORA', CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (fiscal_code, episode_number) DO UPDATE SET
                        event_type     = EXCLUDED.event_type,
                        admission_date = EXCLUDED.admission_date,
                        discharge_date = EXCLUDED.discharge_date,
                        structure      = EXCLUDED.structure,
                        hospital_unit  = EXCLUDED.hospital_unit,
                        diagnosis      = EXCLUDED.diagnosis,
                        updated_at     = CURRENT_TIMESTAMP
                """, event)
                return True
        except Exception as e:
            logger.error(f"Failed to upsert clinical event: {e}")
            return False

    # ------------------------------------------------------------------
    # Sync all events for one patient
    # ------------------------------------------------------------------
    def sync_patient_events(self, fiscal_code):
        events = self.fetch_patient_events(fiscal_code)
        if not events:
            return 0, 0
        success, failed = 0, 0
        for event in events:
            if self.upsert_clinical_event(event):
                success += 1
            else:
                failed += 1
        logger.info(f"Aurora sync for {fiscal_code}: {success} ok, {failed} failed")
        return success, failed

    # ------------------------------------------------------------------
    # Sync all patients (called by ETL orchestrator)
    # ------------------------------------------------------------------
    def sync_all_patients(self):
        logger.info("Starting Aurora ETL for all patients")
        self.db.update_etl_status('AURORA', 'RUNNING', 'ETL job started')
        total_success, total_failed = 0, 0
        try:
            # Use local patients table as the list (Registry ETL must run first)
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT fiscal_code FROM patients")
                rows = cursor.fetchall()
            fiscal_codes = [row['fiscal_code'] for row in rows]

            logger.info(f"Syncing Aurora events for {len(fiscal_codes)} patients")
            for fc in fiscal_codes:
                s, f = self.sync_patient_events(fc)
                total_success += s
                total_failed  += f

            status  = 'SUCCESS' if total_failed == 0 else 'PARTIAL_SUCCESS'
            message = f"Processed {total_success} events, {total_failed} failed"
            self.db.update_etl_status('AURORA', status, message, total_success, total_failed)
            logger.info(f"Aurora ETL completed: {message}")
            return total_success, total_failed
        except Exception as e:
            logger.error(f"Aurora ETL failed: {e}")
            self.db.update_etl_status('AURORA', 'FAILED', str(e))
            return total_success, total_failed
