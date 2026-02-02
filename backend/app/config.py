import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the parent directory (project root)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

cors_origins_str = os.getenv("CORS_ORIGINS")
CORS_ORIGINS = cors_origins_str.split(",") if cors_origins_str != "*" else ["*"]

chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "/app/chroma_db")
if chroma_dir == "/app/chroma_db" and not os.path.exists("/app"):
    chroma_dir = str(Path(__file__).parent.parent / "chroma_db")
CHROMA_PERSIST_DIRECTORY = chroma_dir

aurora_data_path = os.getenv("AURORA_DATA_PATH", "/app/data/real-patient.json")
if not os.path.exists(aurora_data_path):
    aurora_data_path = str(Path(__file__).parent.parent / "data" / "real-patient.json")
AURORA_DATA_PATH = aurora_data_path

REGISTRY_API_URL = os.getenv("REGISTRY_API_URL")
REGISTRY_API_TIMEOUT = int(os.getenv("REGISTRY_API_TIMEOUT", "5"))
REGISTRY_API_ENABLED = os.getenv("REGISTRY_API_ENABLED", "true").lower() == "true"
REGISTRY_API_MOCK = os.getenv("REGISTRY_API_MOCK", "false").lower() == "true"

BOF_API_URL = os.getenv("BOF_API_URL")
BOF_API_TOKEN = os.getenv("BOF_API_TOKEN", None)
BOF_API_TIMEOUT = int(os.getenv("BOF_API_TIMEOUT", "10"))
BOF_API_ENABLED = os.getenv("BOF_API_ENABLED", "false").lower() == "true"


def get_config_summary() -> dict:
    return {
        "model": MODEL_NAME,
        "aurora_data_path": AURORA_DATA_PATH,
        "registry_api": {"url": REGISTRY_API_URL, "enabled": REGISTRY_API_ENABLED, "mock": REGISTRY_API_MOCK},
        "bof_api": {"url": BOF_API_URL, "enabled": BOF_API_ENABLED}
    }
