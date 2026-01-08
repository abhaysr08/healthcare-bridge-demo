import json
import logging
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mistralai import Mistral
from .config import HOST, PORT

from .config import (
    MISTRAL_API_KEY,
    MODEL_NAME,
    CORS_ORIGINS,
    CHROMA_PERSIST_DIRECTORY
)
from .models import ChatRequest, ChatResponse
from .vector_store import VectorStoreManager, create_context_from_results
from .utils import get_system_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Healthcare Home-Care Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

client = Mistral(api_key=MISTRAL_API_KEY)

DATA_PATH = Path(__file__).parent.parent / "data" / "patients.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    PATIENTS_DATA = json.load(f)

vector_store = None

@app.on_event("startup")
async def startup_event():
    global vector_store

    try:
        logger.info("Initializing vector store...")

        vector_store = VectorStoreManager(client, CHROMA_PERSIST_DIRECTORY, PATIENTS_DATA)
        vector_store.initialize_collection()

        if vector_store.collection.count() == 0:
            logger.info(f"Collection empty. Vectorizing {len(PATIENTS_DATA)} patients...")
            vector_store.add_patients(PATIENTS_DATA)
            logger.info("Vectorization complete!")
        else:
            logger.info(f"Loaded existing vectors for {vector_store.collection.count()} patients")

        logger.info("Vector store initialization complete")

    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        logger.warning("Application will continue but vector search may not work correctly")

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Healthcare Home-Care Chatbot API",
        "patients_loaded": len(PATIENTS_DATA)
    }

@app.get("/patients")
async def get_patients():
    return [
        {
            "id": i,
            "nome": p.get("Nome"),
            "cognome": p.get("Cognome"),
            "codice_fiscale": p.get("Codice_fiscale"),
            "data_nascita": p.get("Data_nascita")
        }
        for i, p in enumerate(PATIENTS_DATA)
    ]

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: int):
    if patient_id < 0 or patient_id >= len(PATIENTS_DATA):
        raise HTTPException(status_code=404, detail="Patient not found")
    return PATIENTS_DATA[patient_id]

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if vector_store is None:
            raise HTTPException(
                status_code=503,
                detail="Vector store not initialized. Please wait or restart the server."
            )

        search_results = vector_store.search_patients(query=request.message, top_k=10)
        context = create_context_from_results(search_results, request.message, all_patients_data=PATIENTS_DATA)
        system_prompt = get_system_prompt(len(PATIENTS_DATA))

        messages = [
            {"role": "system", "content": system_prompt + context}
        ]

        for msg in request.conversation_history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": request.message})

        response = client.chat.complete(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )

        assistant_message = response.choices[0].message.content

        patient_context = None
        if search_results and search_results[0]['similarity'] >= 0.8:
            patient_context = search_results[0]['patient']

        return ChatResponse(
            response=assistant_message,
            patient_context=patient_context
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)