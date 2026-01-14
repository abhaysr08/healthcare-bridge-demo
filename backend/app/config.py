import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the parent directory (project root)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral-small-latest")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS = cors_origins_str.split(",") if cors_origins_str != "*" else ["*"]

chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "/app/chroma_db")
if chroma_dir == "/app/chroma_db" and not os.path.exists("/app"):
    chroma_dir = str(Path(__file__).parent.parent / "chroma_db")
CHROMA_PERSIST_DIRECTORY = chroma_dir
