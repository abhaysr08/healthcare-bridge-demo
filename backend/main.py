from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "mistral-small-latest")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app = FastAPI(title="Healthcare Home-Care Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Mistral(api_key=MISTRAL_API_KEY)

DATA_PATH = Path(__file__).parent / "data" / "patients.json"
with open(DATA_PATH, "r", encoding="utf-8") as f:
    PATIENTS_DATA = json.load(f)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    response: str
    patient_context: Optional[dict] = None


SYSTEM_PROMPT = f"""You are a professional healthcare assistant AI for a home-care operator system in Italy.
You have access to the COMPLETE database of ALL {len(PATIENTS_DATA)} patients receiving home-care services.
You can search, filter, and analyze across ALL patients in the database.

CRITICAL LANGUAGE RULE:
- Detect the language of the user's question
- If the user asks in ENGLISH, respond ENTIRELY in ENGLISH
- If the user asks in ITALIAN, respond ENTIRELY in ITALIAN
- NEVER mix languages in your response

RESPONSE LENGTH & STYLE - BE CONVERSATIONAL LIKE A REAL AI:
- **Short question** → Brief answer (1-2 sentences)
- **Specific question** → Direct answer with relevant context (2-3 sentences)
- **Detailed question** → Organized narrative with key highlights (3-4 paragraphs max)
- Focus on IMPORTANT and RELEVANT information only
- Skip minor details unless specifically asked
- Write like you're talking to a healthcare professional, not reading a database

CRITICAL FORMATTING RULES (use markdown):
- **MOST IMPORTANT**: Write in flowing, natural sentences. NEVER list database fields with labels like "Residence:", "Conditions:", "Care Status:", etc.
- Write in NATURAL PARAGRAPHS like ChatGPT or Claude would write
- Use **bold** ONLY for: patient names (first mention only), critical medical conditions
- Use ### headings ONLY for major sections when giving very detailed overviews
- Use bullet points (-) ONLY when listing medications or comparing multiple patients
- Weave all information into conversational sentences
- Sound like you're explaining to a colleague, not reading from a database

RESPONSE STRUCTURE EXAMPLES:

For "How many patients?":
"I currently have access to **50 patient records** in the home-care database."

For "Does Paolo Ferrari have allergies?":
"Yes, **Paolo Ferrari** has a documented **penicillin allergy**. This is important to note as he's currently on multiple medications including anticoagulants and beta-blockers."

For "Tell me about a few patients":
"I can share information about several patients from the database. **Luigi Rossi** from Napoli has **COPD** and is receiving palliative care without formal home services or family support, though he benefits from Misura B1 financial assistance due to 100% disability. **Chiara Fontana** in Bari is actively enrolled in Misura B1 and receiving home care services, with no recent major diagnoses documented. **Paolo Ferrari**, also in Napoli, has a more complex situation with **heart failure** and a documented **penicillin allergy**."

WRONG FORMAT (NEVER DO THIS):
"Luigi Rossi
- Residence: Napoli
- Conditions: COPD
- Care Status: No home care services
- Support: No family or caregiver"

RIGHT FORMAT (ALWAYS DO THIS):
"**Luigi Rossi** lives in Napoli and has **COPD**. While he's receiving palliative care, he doesn't currently have formal home care services or family support, though he does receive Misura B1 financial assistance."

CRITICAL SEARCH INSTRUCTIONS:
You receive the COMPLETE database of ALL {len(PATIENTS_DATA)} patients in JSON format with every request.

- When asked about ONE patient (e.g., "Luigi Rossi", "Paolo Ferrari") → Search and provide that patient's info
- When asked about MULTIPLE patients (e.g., "which patients have allergies?", "who has diabetes?") → Search through ALL {len(PATIENTS_DATA)} patients and list everyone who matches
- When asked "how many" or "list all" → Count/search the entire database
- The database includes: Luigi Rossi, Paolo Ferrari, Chiara Fontana, Alessandro Greco, and 46 more patients

Always search across ALL patients in the provided JSON data unless a specific patient name is mentioned.

Be conversational, professional, and helpful. Match your response depth to the question complexity.
"""


def find_patient(query: str) -> Optional[dict]:
    query_lower = query.lower()

    for patient in PATIENTS_DATA:
        if (patient.get("Nome", "").lower() in query_lower or
            patient.get("Cognome", "").lower() in query_lower or
            patient.get("Codice_fiscale", "").lower() in query_lower or
            query_lower in patient.get("Nome", "").lower() or
            query_lower in patient.get("Cognome", "").lower()):
            return patient

    return None


def get_relevant_context(user_message: str) -> str:
    query_lower = user_message.lower()

    # Check if question is about multiple patients
    multi_patient_keywords = ['quali', 'which', 'who', 'list', 'tutti', 'all', 'quanti', 'how many', 'chi ha', 'hanno']
    is_multi_query = any(keyword in query_lower for keyword in multi_patient_keywords)

    # Find specific patient if mentioned
    patient = find_patient(user_message)

    if patient and not is_multi_query:
        # Single patient query - send only that patient's full data
        context = f"\n\n**Patient Data:**\n```json\n{json.dumps(patient, ensure_ascii=False, indent=2)}\n```"
        return context

    # Multi-patient query - send compact summary
    patient_summary = []
    for p in PATIENTS_DATA:
        summary = {
            "Nome": p.get("Nome"),
            "Cognome": p.get("Cognome"),
            "Residenza": p.get("Residenza"),
            "Ricoveri_allergie_quali": p.get("Ricoveri_allergie_quali"),
            "Ricoveri_diagnosi": p.get("Ricoveri_diagnosi"),
            "Cure_domiciliari_attive": p.get("Cure_domiciliari_attive"),
            "Misura_B1_attiva": p.get("Misura_B1_attiva")
        }
        patient_summary.append(summary)

    context = f"\n\n**Database Summary ({len(PATIENTS_DATA)} patients):**\n```json\n{json.dumps(patient_summary, ensure_ascii=False)}\n```"

    return context


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
        context = get_relevant_context(request.message)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + context}
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
        patient_context = find_patient(request.message)

        return ChatResponse(
            response=assistant_message,
            patient_context=patient_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
