import json
import logging
import uvicorn
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from .config import HOST, PORT

from .config import (
    OPENAI_API_KEY,
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

client = OpenAI(api_key=OPENAI_API_KEY)

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

def find_patient_by_name(name: str) -> dict:
    """
    Find patient by exact name match (case-insensitive).
    Returns patient dict if found, None otherwise.
    """
    name_lower = name.lower().strip()
    for patient in PATIENTS_DATA:
        full_name = f"{patient.get('Nome', '')} {patient.get('Cognome', '')}".lower().strip()
        if full_name == name_lower:
            logger.info(f"Found exact match for patient: {name}")
            return patient
    logger.warning(f"No patient found with name: {name}")
    return None

def validate_fiscal_code(patient: dict, fiscal_code: str) -> bool:
    """
    Validate that the fiscal code matches the patient.
    Returns True if match, False otherwise.
    """
    patient_fc = patient.get('Codice_fiscale', '').strip().upper()
    provided_fc = fiscal_code.strip().upper()
    
    if patient_fc == provided_fc:
        logger.info(f"Fiscal code validated for patient: {patient.get('Nome')} {patient.get('Cognome')}")
        return True
    else:
        logger.warning(f"Fiscal code mismatch for patient {patient.get('Nome')} {patient.get('Cognome')}: expected {patient_fc}, got {provided_fc}")
        return False

def detect_language(text: str) -> str:
    """
    Detect if the text is in Italian or English.
    Returns 'it' for Italian, 'en' for English.
    Uses strict detection - only Italian if Italian keywords found, otherwise English.
    """
    text_lower = text.lower()
    
    italian_keywords = [
        'dimmi', 'dammi', 'mostra', 'mostrami', 'puoi', 'potresti',
        'per favore', 'grazie', 'ciao', 'buongiorno', 'buonasera',
        'paziente', 'pazienti', 'informazioni', 'riepilogo', 'panoramica',
        'visitare', 'andare', 'sto', 'sono', 'vorrei', 'mi', 'di più'
    ]
    
    if any(keyword in text_lower for keyword in italian_keywords):
        return 'it'
    
    return 'en'



def is_fiscal_code(text: str) -> bool:
    """
    Check if text looks like an Italian fiscal code.
    Italian fiscal codes are 16 alphanumeric characters.
    """
    text = text.strip().upper()
    if len(text) != 16:
        return False
    
    import re
    # Allow alphanumeric characters (letters and digits)
    pattern = r'^[A-Z0-9]{16}$'
    return bool(re.match(pattern, text))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if vector_store is None:
            raise HTTPException(
                status_code=503,
                detail="Vector store not initialized. Please wait or restart the server."
            )

        logger.info(f"Received query: {request.message}")
        
        if is_fiscal_code(request.message):
            logger.info(f"Fiscal code detected: {request.message}")
            
            patient_by_fc = None
            for p in PATIENTS_DATA:
                if p.get('Codice_fiscale', '').strip().upper() == request.message.strip().upper():
                    patient_by_fc = p
                    break
            
            if patient_by_fc:
                logger.info(f"Fiscal code validated: {patient_by_fc.get('Nome')} {patient_by_fc.get('Cognome')}")
                
                context = f"\n\n**Patient Data:**\n```json\n{json.dumps(patient_by_fc, ensure_ascii=False, indent=2)}\n```"
                system_prompt = get_system_prompt(len(PATIENTS_DATA))
                
                messages = [
                    {"role": "system", "content": system_prompt + context}
                ]
                
                for msg in request.conversation_history:
                    messages.append({"role": msg.role, "content": msg.content})
                
                messages.append({"role": "user", "content": request.message})
                
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1500
                )
                
                return ChatResponse(
                    response=response.choices[0].message.content,
                    patient_context=patient_by_fc
                )
            else:
                logger.warning(f"Fiscal code not found: {request.message}")
                
                lang = 'en'
                if request.conversation_history:
                    last_user_msg = None
                    for msg in reversed(request.conversation_history):
                        if msg.role == "user":
                            last_user_msg = msg.content
                            break
                    if last_user_msg:
                        lang = detect_language(last_user_msg)
                
                if lang == 'it':
                    error_message = "Paziente non trovato, per favore verifica il codice fiscale / scegli tra i pazienti disponibili."
                else:
                    error_message = "Patient not found, please verify the fiscal code or choose from available patients."
                
                return ChatResponse(
                    response=error_message,
                    patient_context=None
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

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )

        assistant_message = response.choices[0].message.content

        patient_context = None
        if search_results and search_results[0]['similarity'] >= 0.7:
            patient_context = search_results[0]['patient']

        return ChatResponse(
            response=assistant_message,
            patient_context=patient_context
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

