"""
Database connection handler for PostgreSQL consolidated database
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.dbname = os.getenv('DB_NAME', 'healthbridge_care')
        self.user = os.getenv('DB_USER', 'healthbridge_user')
        self.password = os.getenv('DB_PASSWORD')

        if not self.password:
            raise ValueError("DB_PASSWORD environment variable is required")

    def get_connection_string(self):
        return f"host={self.host} port={self.port} dbname={self.dbname} user={self.user} password={self.password}"

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(self.get_connection_string())
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Context manager for database cursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
            try:
                yield cursor
            finally:
                cursor.close()

    def test_connection(self):
        """Test database connectivity"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT version();")
                result = cursor.fetchone()
                logger.info(f"Database connection successful: {result['version']}")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def update_etl_status(self, source_system, status, message=None, records_processed=0, records_failed=0):
        """Update ETL metadata table"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE etl_metadata
                    SET last_successful_run = CASE WHEN %s = 'SUCCESS' THEN CURRENT_TIMESTAMP ELSE last_successful_run END,
                        last_run_status = %s,
                        last_run_message = %s,
                        records_processed = records_processed + %s,
                        records_failed = records_failed + %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE source_system = %s
                """, (status, status, message, records_processed, records_failed, source_system))
                logger.info(f"ETL status updated for {source_system}: {status}")
        except Exception as e:
            logger.error(f"Failed to update ETL status: {e}")
