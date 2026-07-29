import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from the parent directory (project root)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

cors_origins_str = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = cors_origins_str.split(",") if cors_origins_str != "*" else ["*"]

chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "/app/chroma_db")
if chroma_dir == "/app/chroma_db" and not os.path.exists("/app"):
    chroma_dir = str(Path(__file__).parent.parent / "chroma_db")
CHROMA_PERSIST_DIRECTORY = chroma_dir

aurora_data_path = os.getenv("AURORA_DATA_PATH", "/app/data/real-patient.json")
if not os.path.exists(aurora_data_path):
    aurora_data_path = str(Path(__file__).parent.parent / "data" / "real-patient.json")
AURORA_DATA_PATH = aurora_data_path

# Patient data schema selector for the RAG store: "chronic_care" (demo dataset,
# default) or "aurora" (real hospital registry export, see AURORA_DATA_PATH above)
PATIENT_DATA_SCHEMA = os.getenv("PATIENT_DATA_SCHEMA", "chronic_care")

chronic_care_data_path = os.getenv("CHRONIC_CARE_DATA_PATH", "/app/data/chronic-care-patients.json")
if not os.path.exists(chronic_care_data_path):
    chronic_care_data_path = str(Path(__file__).parent.parent / "data" / "chronic-care-patients.json")
CHRONIC_CARE_DATA_PATH = chronic_care_data_path

# Registry API configuration - fully dynamic, no mock data
REGISTRY_API_URL = os.getenv("REGISTRY_API_URL", "https://clumiddle.aodv.local/AC/pac/rest/paziente")
REGISTRY_API_TIMEOUT = int(os.getenv("REGISTRY_API_TIMEOUT", "30"))
REGISTRY_API_ENABLED = os.getenv("REGISTRY_API_ENABLED", "true").lower() == "true"

# BOF API configuration with proper defaults
BOF_API_URL = os.getenv("BOF_API_URL", "https://bof.asst-brianza.it/api/v1/index.php")
BOF_API_TOKEN = os.getenv("BOF_API_TOKEN", None)
BOF_API_TIMEOUT = int(os.getenv("BOF_API_TIMEOUT", "10"))
BOF_API_ENABLED = os.getenv("BOF_API_ENABLED", "true").lower() == "true"

# Consolidated API (AI1 server at 10.30.229.21 via VPN)
# When enabled, replaces direct Registry and BOF API calls from AWS EC2
CONSOLIDATED_API_URL = os.getenv("CONSOLIDATED_API_URL", "http://10.30.229.21:8080")
CONSOLIDATED_API_TOKEN = os.getenv("CONSOLIDATED_API_TOKEN", "dev-token-12345")
CONSOLIDATED_API_TIMEOUT = int(os.getenv("CONSOLIDATED_API_TIMEOUT", "15"))
CONSOLIDATED_API_ENABLED = os.getenv("CONSOLIDATED_API_ENABLED", "false").lower() == "true"

# PostgreSQL (auth DB — users, refresh tokens, audit logs)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://healthbridge:healthbridge@localhost:5432/healthbridge"
)

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Initial admin account (seeded on first startup if no users exist)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_FULL_NAME = os.getenv("ADMIN_FULL_NAME", "Amministratore Sistema")


def get_config_summary() -> dict:
    return {
        "model": MODEL_NAME,
        "patient_data_schema": PATIENT_DATA_SCHEMA,
        "aurora_data_path": AURORA_DATA_PATH,
        "chronic_care_data_path": CHRONIC_CARE_DATA_PATH,
        "registry_api": {
            "url": REGISTRY_API_URL,
            "enabled": REGISTRY_API_ENABLED,
            "timeout": REGISTRY_API_TIMEOUT
        },
        "bof_api": {
            "url": BOF_API_URL,
            "enabled": BOF_API_ENABLED,
            "has_token": BOF_API_TOKEN is not None,
            "timeout": BOF_API_TIMEOUT
        },
        "consolidated_api": {
            "url": CONSOLIDATED_API_URL,
            "enabled": CONSOLIDATED_API_ENABLED,
            "timeout": CONSOLIDATED_API_TIMEOUT
        }
    }
