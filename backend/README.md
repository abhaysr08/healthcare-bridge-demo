# Backend - FastAPI + Mistral AI

FastAPI server for Healthcare Bridge chatbot with Mistral AI integration.

## Run Server

```bash
./venv/bin/python main.py
```

Runs on http://127.0.0.1:8000

## API Endpoints

- `GET /` - Health check (returns status and patient count)
- `GET /patients` - List all patients (basic info)
- `GET /patients/{id}` - Get full patient details by ID
- `POST /chat` - Chat with AI about patients

## Configuration

The `.env` file contains all server configuration:

```bash
# Mistral AI Configuration
MISTRAL_API_KEY=your-mistral-api-key-here
MODEL_NAME=mistral-small-latest

# Server Configuration
HOST=127.0.0.1
PORT=8000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Setup**: Copy `.env.example` to `.env` and update the values as needed.

## Features

- **Smart Context Loading**: Automatically detects single vs multi-patient queries
- **Bilingual Support**: Responds in the language used by the user (English/Italian)
- **Natural Responses**: Conversational AI, not database dumps
- **Patient Search**: Finds patients by name, surname, or codice fiscale

## Data

- 50 synthetic patients in `data/patients.json`
- 48 fields per patient (clinical, social, organizational)
- All data is synthetic and for demo purposes only

See main README.md for full setup instructions.
