# Healthcare Bridge - Home Care Chatbot Demo

A minimal demo chatbot for healthcare home-care patient management using FastAPI backend and React.js frontend with Mistral AI.

## Features

- Chat with AI about 50 synthetic patients
- Complete patient overview with all clinical, social, and organizational fields
- Answer any follow-up questions about patient data in English or Italian
- Beautiful, modern UI for positive customer impression
- Conversational AI responses (not database dumps)
- Smart context loading for fast performance

## Project Structure

```
healthcare-bridge-demo/
├── backend/
│   ├── data/
│   │   └── patients.json          # 50 synthetic patients
│   ├── main.py                     # FastAPI server with Mistral AI
│   ├── requirements.txt
│   ├── .env                        # API keys (not in git)
│   ├── .gitignore
│   └── README.md
└── healthcare-ui/
    ├── src/
    │   ├── Chatbot.jsx             # Main chatbot component
    │   ├── Chatbot.css             # Chatbot styles
    │   ├── App.jsx
    │   ├── App.css
    │   ├── index.css
    │   └── main.jsx
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── README.md
```

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Create `.env` file in the root directory:**
   ```bash
   # Copy the example and update with your values
   cp .env.example .env
   # Edit .env and add your MISTRAL_API_KEY
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

4. **Stop services:**
   ```bash
   docker-compose down
   ```

### Option 2: Manual Setup

#### Step 1: Configure Environment Variables

**Backend:**
```bash
cd backend
# The .env file already exists with configuration
# For a new setup, copy .env.example to .env and update values
```

**Frontend:**
```bash
cd healthcare-ui
# The .env file already exists with configuration
# For a new setup, copy .env.example to .env and update values
```

#### Step 2: Start Backend (Terminal 1)

```bash
cd backend
./venv/bin/python main.py
```

You should see: `INFO: Uvicorn running on http://127.0.0.1:8000`

#### Step 3: Start Frontend (Terminal 2 - New Tab)

```bash
cd healthcare-ui
npm run dev
```

You should see: `Local: http://localhost:3000/`

#### Step 4: Open Browser

Go to **http://localhost:3000** and start chatting!

## Demo Questions to Try

### English:
1. "Tell me about Luigi Rossi"
2. "Which patients have allergies?"
3. "Who has active home care services?"
4. "Tell me about a few patients"
5. "How many patients are in the database?"

### Italian:
1. "Mostrami le informazioni su Luigi Rossi"
2. "Quali pazienti hanno allergie?"
3. "Chi ha cure domiciliari attive?"
4. "Dimmi tutto su Paolo Ferrari"
5. "Quali pazienti hanno la Misura B1 attiva?"

## Stopping the Demo

Press **Ctrl+C** in both terminals

## Patient Data Fields

The system understands and can answer questions about all 48 patient fields:

- **Personal Info**: Name, surname, fiscal code, address, birth date, contact
- **Caregivers**: Caregiver presence/name, aide presence/name
- **Medical**: Doctor info, exemptions, disability status
- **Prosthetics**: Equipment type, requests, delivery status
- **Hospital**: Recent admissions, diagnoses, therapies, allergies
- **Psychiatric**: Mental health services, addiction services
- **Social Services**: Active services and notes
- **Visits**: Ambulatory visits, reports, therapies
- **Palliative**: Hospice, palliative care, protected discharge
- **Home Care**: Active services, provider, care path
- **Support**: Economic support (Misura B1)

## API Endpoints

- `GET /` - Health check
- `GET /patients` - List all patients
- `GET /patients/{id}` - Get patient details
- `POST /chat` - Chat with AI

## Technologies

- **Backend**: FastAPI, Python 3.12, Mistral AI
- **Frontend**: React.js 18, Vite, Axios, ReactMarkdown
- **AI**: Mistral Small (fast and conversational)

## Key Features

- **Bilingual Support**: Auto-detects user language (English/Italian)
- **Natural Responses**: Conversational AI, not database dumps
- **Smart Context**: Single patient queries get full data, multi-patient queries get summaries
- **Modern UI**: Flexible message bubbles, auto-expanding input, gradient design
- **Fast Performance**: Optimized data loading for quick responses
- **Professional Configuration**: All settings managed via environment variables

## Environment Configuration

### Single .env File (Root Directory)

For Docker Compose, create a single `.env` file in the root directory:

```bash
# Backend Configuration
MISTRAL_API_KEY=your-mistral-api-key-here
MODEL_NAME=mistral-small-latest
HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend Configuration
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Healthcare Bridge
VITE_APP_SUBTITLE=Assistente Cure Domiciliari
FRONTEND_PORT=3000
```

**Note**: The `.env` file is in `.gitignore` and won't be committed. Copy `.env.example` to `.env` and update with your values.

### Manual Setup (Separate .env files)

If running manually without Docker, you can use separate `.env` files:

**Backend (`backend/.env`):**
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

**Frontend (`healthcare-ui/.env`):**
```bash
VITE_API_URL=http://127.0.0.1:8000
VITE_APP_NAME=Healthcare Bridge
VITE_APP_SUBTITLE=Assistente Cure Domiciliari
```

## Troubleshooting

### Backend Issues
- **Port in use**: Check if port 8000 is free: `lsof -i :8000`
- **API Key Error**: Check `.env` file has valid Mistral API key

### Frontend Issues
- **Connection Error**: Make sure backend is running first
- **Port in use**: Check if port 3000 is free: `lsof -i :3000`
- **Dependencies Error**: Try `rm -rf node_modules package-lock.json && npm install`

### CORS Errors
- Ensure backend is running on 127.0.0.1:8000
- Check browser console for specific error messages
