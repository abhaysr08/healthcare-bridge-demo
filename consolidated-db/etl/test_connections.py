"""
Test all data source connections before running full ETL
"""
import os
import sys
import requests
import cx_Oracle
import psycopg2
from dotenv import load_dotenv
import logging

# Load environment
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_postgres():
    """Test PostgreSQL connection"""
    logger.info("Testing PostgreSQL connection...")
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname=os.getenv('DB_NAME', 'healthbridge_care'),
            user=os.getenv('DB_USER', 'healthbridge_user'),
            password=os.getenv('DB_PASSWORD')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        logger.info(f"✅ PostgreSQL: Connected - {version[:50]}...")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL: Failed - {e}")
        return False


def test_registry_api():
    """Test Central Registry API"""
    logger.info("Testing Central Registry API...")
    try:
        url = os.getenv('REGISTRY_API_URL', 'https://clumiddle.aodv.local/AC/pac/rest/paziente')
        test_fiscal_code = "RSSMRA85M01F205X"
        response = requests.get(
            f"{url}/{test_fiscal_code}",
            verify=False,
            timeout=30
        )
        if response.status_code == 200:
            logger.info(f"✅ Registry API: Connected - Status {response.status_code}")
            return True
        elif response.status_code == 404:
            logger.info(f"✅ Registry API: Connected (patient not found is OK) - Status {response.status_code}")
            return True
        else:
            logger.warning(f"⚠️  Registry API: Unexpected status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Registry API: Failed - {e}")
        return False


def test_aurora_db():
    """Test Aurora Oracle DB"""
    logger.info("Testing Aurora Oracle DB...")
    try:
        host = os.getenv('AURORA_HOST', '10.30.208.195')
        port = int(os.getenv('AURORA_PORT', 1521))
        service = os.getenv('AURORA_SERVICE', 'E4CURE')
        user = os.getenv('AURORA_USER', 'PROG_PILI')
        password = os.getenv('AURORA_PASSWORD')

        dsn = cx_Oracle.makedsn(host, port, service_name=service)
        conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)

        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        logger.info(f"✅ Aurora Oracle DB: Connected - Service {service}")
        return True
    except Exception as e:
        logger.error(f"❌ Aurora Oracle DB: Failed - {e}")
        return False


def test_bof_api():
    """Test BOF API"""
    logger.info("Testing BOF API...")
    try:
        url = os.getenv('BOF_API_URL', 'https://bof.asst-brianza.it/api/v1/index.php')
        token = os.getenv('BOF_API_TOKEN')

        payload = {
            "token": token,
            "action": "dimissioniprotette.getpatitient",
            "data": "RSSMRA85M01F205X"
        }

        response = requests.post(
            url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            logger.info(f"✅ BOF API: Connected - Status {response.status_code}")
            return True
        else:
            logger.warning(f"⚠️  BOF API: Unexpected status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ BOF API: Failed - {e}")
        return False


def main():
    """Run all connection tests"""
    logger.info("=" * 80)
    logger.info("CONNECTION TESTS - Healthbridge Care+ ETL")
    logger.info("=" * 80)

    results = {
        'PostgreSQL': test_postgres(),
        'Registry API': test_registry_api(),
        'Aurora Oracle DB': test_aurora_db(),
        'BOF API': test_bof_api()
    }

    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    for service, status in results.items():
        status_str = "✅ PASS" if status else "❌ FAIL"
        logger.info(f"{service:20} {status_str}")

    logger.info("=" * 80)

    all_passed = all(results.values())
    if all_passed:
        logger.info("🎉 All connection tests passed! Ready to run ETL.")
        return 0
    else:
        logger.error("❌ Some connection tests failed. Fix issues before running ETL.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
