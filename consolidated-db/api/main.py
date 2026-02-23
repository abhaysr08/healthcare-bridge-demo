"""
Unified FastAPI Endpoint for Healthbridge Care+ Consolidated Database
Provides single API endpoint for patient data retrieval
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Healthbridge Care+ API",
    description="Unified API for consolidated patient data",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'healthbridge_care'),
    'user': os.getenv('DB_USER', 'healthbridge_user'),
    'password': os.getenv('DB_PASSWORD')
}

API_TOKEN = os.getenv('API_TOKEN', 'dev-token-12345')


# Pydantic models
class Patient(BaseModel):
    fiscal_code: str
    first_name: Optional[str]
    last_name: Optional[str]
    birth_date: Optional[Any]
    sex: Optional[str]
    residence_address: Optional[str]
    domicile_address: Optional[str]
    phone_numbers: Optional[Any]
    email: Optional[str]
    primary_doctor_name: Optional[str]
    primary_doctor_email: Optional[str]
    exemptions: Optional[Any]
    disability_status: Optional[bool]
    disability_details: Optional[str]
    cps_active: Optional[bool]
    noa_sert_active: Optional[bool]
    caregiver_name: Optional[str]
    caregiver_relationship: Optional[str]
    caregiver_phone: Optional[str]
    last_validated: Optional[Any]


class ClinicalEvent(BaseModel):
    id: int
    episode_number: Optional[str]
    event_type: Optional[str]
    admission_date: Optional[Any]
    discharge_date: Optional[Any]
    structure: Optional[str]
    hospital_unit: Optional[str]
    diagnosis: Optional[str]


class ProtectedDischarge(BaseModel):
    id: int
    discharge_date: Optional[Any]
    discharge_type: Optional[str]
    discharge_status: Optional[str]
    home_care_active: Optional[bool]
    home_care_provider: Optional[str]
    home_care_pathway: Optional[str]
    palliative_care: Optional[bool]
    hospice: Optional[bool]
    social_services_active: Optional[bool]
    sgdt_last_visit_date: Optional[Any]
    sgdt_last_visit_operator: Optional[str]
    sgdt_notes: Optional[str]
    patient_description: Optional[str]
    care_level: Optional[str]
    admission_date: Optional[Any]
    operators_involved: Optional[str]


class ProstheticsItem(BaseModel):
    id: int
    prescription_id: Optional[str]
    delivery_note: Optional[str]
    delivery_date: Optional[Any]
    supplier_name: Optional[str]
    product_code: Optional[str]
    product_description: Optional[str]
    brand: Optional[str]
    model: Optional[str]
    quantity: Optional[str]
    total_price: Optional[Any]
    status: Optional[str]


class DataFreshness(BaseModel):
    registry_last_update: Optional[str]
    aurora_last_update: Optional[str]
    bof_last_update: Optional[str]
    prosthetics_last_update: Optional[str]


class PatientResponse(BaseModel):
    patient: Optional[Patient]
    clinical_events: List[ClinicalEvent]
    protected_discharges: List[ProtectedDischarge]
    prosthetics_items: List[ProstheticsItem]
    data_freshness: DataFreshness
    patient_found: bool


# Database connection
def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


def verify_token(authorization: str = Header(None)):
    """Verify API token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid token")

    return True


# API Endpoints
@app.get("/")
def root():
    """API root endpoint"""
    return {
        "service": "Healthbridge Care+ API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/status")
def status():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/api/v1/patient/{fiscal_code}", response_model=PatientResponse)
def get_patient(fiscal_code: str, authorized: bool = Depends(verify_token)):
    """
    Get complete patient profile from consolidated database

    Args:
        fiscal_code: Italian fiscal code (16 characters)

    Returns:
        Complete patient profile including demographics, clinical events, and discharges
    """
    logger.info(f"Fetching patient data for fiscal_code: {fiscal_code}")

    # Validate fiscal code format
    if len(fiscal_code) != 16:
        raise HTTPException(status_code=400, detail="Invalid fiscal code format")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Step 1: Get patient demographics
        cursor.execute("""
            SELECT
                fiscal_code, first_name, last_name, birth_date, sex,
                residence_address, domicile_address, phone_numbers, email,
                primary_doctor_name, primary_doctor_email, exemptions,
                disability_status, disability_details,
                cps_active, noa_sert_active,
                caregiver_name, caregiver_relationship, caregiver_phone,
                last_validated
            FROM patients
            WHERE fiscal_code = %s
        """, (fiscal_code,))

        patient_data = cursor.fetchone()

        if not patient_data:
            logger.warning(f"Patient not found: {fiscal_code}")
            cursor.close()
            conn.close()
            return PatientResponse(
                patient=None,
                clinical_events=[],
                protected_discharges=[],
                prosthetics_items=[],
                data_freshness=DataFreshness(
                    registry_last_update=None,
                    aurora_last_update=None,
                    bof_last_update=None,
                    prosthetics_last_update=None
                ),
                patient_found=False
            )

        # Step 2: Get clinical events (last 12 months)
        cursor.execute("""
            SELECT
                id, episode_number, event_type,
                admission_date, discharge_date,
                structure, hospital_unit, diagnosis
            FROM clinical_events
            WHERE fiscal_code = %s
            AND admission_date > CURRENT_DATE - INTERVAL '12 months'
            ORDER BY admission_date DESC
        """, (fiscal_code,))

        clinical_events = cursor.fetchall()

        # Step 3: Get protected discharges
        cursor.execute("""
            SELECT
                id, discharge_date, discharge_type, discharge_status,
                home_care_active, home_care_provider, home_care_pathway,
                palliative_care, hospice, social_services_active,
                sgdt_last_visit_date, sgdt_last_visit_operator, sgdt_notes,
                patient_description, care_level, admission_date, operators_involved
            FROM protected_discharges
            WHERE fiscal_code = %s
            ORDER BY discharge_date DESC
        """, (fiscal_code,))

        discharges = cursor.fetchall()

        # Step 4: Get prosthetics items
        cursor.execute("""
            SELECT
                id, prescription_id, delivery_note, delivery_date,
                supplier_name, product_code, product_description,
                brand, model, quantity, total_price, status
            FROM prosthetics_items
            WHERE fiscal_code = %s
            ORDER BY delivery_date DESC
        """, (fiscal_code,))

        prosthetics = cursor.fetchall()

        # Step 5: Get data freshness
        cursor.execute("""
            SELECT source_system, last_successful_run
            FROM etl_metadata
        """)

        etl_status = cursor.fetchall()
        freshness = {
            'registry_last_update': None,
            'aurora_last_update': None,
            'bof_last_update': None,
            'prosthetics_last_update': None
        }

        for status in etl_status:
            system = status['source_system']
            timestamp = status['last_successful_run']
            if system == 'CENTRAL_REGISTRY':
                freshness['registry_last_update'] = timestamp.isoformat() if timestamp else None
            elif system == 'AURORA':
                freshness['aurora_last_update'] = timestamp.isoformat() if timestamp else None
            elif system == 'BOF':
                freshness['bof_last_update'] = timestamp.isoformat() if timestamp else None
            elif system == 'PROSTHETICS_NFS':
                freshness['prosthetics_last_update'] = timestamp.isoformat() if timestamp else None

        cursor.close()
        conn.close()

        # Format response
        response = PatientResponse(
            patient=Patient(**dict(patient_data)),
            clinical_events=[ClinicalEvent(**dict(event)) for event in clinical_events],
            protected_discharges=[ProtectedDischarge(**dict(discharge)) for discharge in discharges],
            prosthetics_items=[ProstheticsItem(**dict(item)) for item in prosthetics],
            data_freshness=DataFreshness(**freshness),
            patient_found=True
        )

        logger.info(f"Patient data retrieved successfully: {fiscal_code}")
        return response

    except Exception as e:
        logger.error(f"Error fetching patient data: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v1/etl/status")
def get_etl_status(authorized: bool = Depends(verify_token)):
    """Get ETL job status and data freshness"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                source_system, last_successful_run, last_run_status,
                last_run_message, records_processed, records_failed,
                updated_at
            FROM etl_metadata
            ORDER BY source_system
        """)

        etl_status = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "etl_jobs": [dict(job) for job in etl_status],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching ETL status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8080))

    logger.info(f"Starting Healthbridge Care+ API on {host}:{port}")

    uvicorn.run(app, host=host, port=port)
