-- ============================================================================
-- Healthbridge Care+ Consolidated Database Schema
-- PostgreSQL 14+
-- Based on Technical Document Section 5 - Patient Data Model
-- ============================================================================

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS clinical_events CASCADE;
DROP TABLE IF EXISTS protected_discharges CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS etl_metadata CASCADE;

-- ============================================================================
-- Core Patient Table (from Central Registry - Source of Truth)
-- ============================================================================
CREATE TABLE patients (
    -- Primary Key
    fiscal_code VARCHAR(16) PRIMARY KEY,

    -- Demographic / Anagraphic Fields (from Central Registry)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    birth_date DATE,
    sex VARCHAR(10),
    residence_address TEXT,
    domicile_address TEXT,
    phone_numbers JSONB, -- Array of phone numbers
    email VARCHAR(255),

    -- Healthcare Provider
    primary_doctor_name VARCHAR(200),
    primary_doctor_email VARCHAR(255),

    -- Exemptions
    exemptions JSONB, -- Array of exemption codes

    -- Clinical / Service Flags (from Registry / ATS)
    disability_status BOOLEAN DEFAULT FALSE,
    disability_details TEXT,

    -- Psychiatric Services
    cps_active BOOLEAN DEFAULT FALSE, -- Psychiatric center
    noa_sert_active BOOLEAN DEFAULT FALSE, -- Addiction services

    -- Caregiver Information
    caregiver_name VARCHAR(200),
    caregiver_relationship VARCHAR(100),
    caregiver_phone VARCHAR(50),
    home_assistant_present BOOLEAN DEFAULT FALSE,

    -- Metadata
    source_system VARCHAR(50) DEFAULT 'CENTRAL_REGISTRY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_validated TIMESTAMP,

    -- Indexes
    CONSTRAINT check_fiscal_code CHECK (LENGTH(fiscal_code) = 16)
);

CREATE INDEX idx_patients_last_name ON patients(last_name);
CREATE INDEX idx_patients_birth_date ON patients(birth_date);
CREATE INDEX idx_patients_updated_at ON patients(updated_at);

-- ============================================================================
-- Clinical Events Table (from Aurora DB - PAZIENTI_ACCESSO2)
-- ============================================================================
CREATE TABLE clinical_events (
    id SERIAL PRIMARY KEY,
    fiscal_code VARCHAR(16) NOT NULL REFERENCES patients(fiscal_code) ON DELETE CASCADE,

    -- Event Information
    event_type VARCHAR(50) NOT NULL, -- 'ED_ACCESS', 'HOSPITALIZATION', 'OUTPATIENT', 'DAY_HOSPITAL'
    event_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP,

    -- Clinical Details
    diagnosis TEXT,
    diagnosis_code VARCHAR(20),
    department VARCHAR(100),
    ward VARCHAR(100),

    -- Treatment Information
    therapies JSONB, -- Array of therapy details
    allergies JSONB, -- Array of known allergies

    -- Metadata
    source_system VARCHAR(50) DEFAULT 'AURORA',
    source_record_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clinical_events_fiscal_code ON clinical_events(fiscal_code);
CREATE INDEX idx_clinical_events_event_date ON clinical_events(event_date DESC);
CREATE INDEX idx_clinical_events_event_type ON clinical_events(event_type);

-- ============================================================================
-- Protected Discharges Table (from BOF API)
-- ============================================================================
CREATE TABLE protected_discharges (
    id SERIAL PRIMARY KEY,
    fiscal_code VARCHAR(16) NOT NULL REFERENCES patients(fiscal_code) ON DELETE CASCADE,

    -- Discharge Information
    discharge_date DATE,
    discharge_type VARCHAR(100),
    discharge_status VARCHAR(50), -- 'ACTIVE', 'COMPLETED', 'CANCELLED'

    -- Care Plan
    home_care_active BOOLEAN DEFAULT FALSE,
    home_care_provider VARCHAR(200),
    home_care_pathway VARCHAR(200),

    -- Palliative / Hospice
    palliative_care BOOLEAN DEFAULT FALSE,
    hospice BOOLEAN DEFAULT FALSE,

    -- Social Services
    social_services_active BOOLEAN DEFAULT FALSE,
    social_services_notes TEXT,

    -- SGDT (Territorial Management)
    sgdt_last_visit_date DATE,
    sgdt_last_visit_operator VARCHAR(200),
    sgdt_notes TEXT,

    -- Special Programs
    measure_b1_active BOOLEAN DEFAULT FALSE, -- Regional program
    nad_nutrition_active BOOLEAN DEFAULT FALSE, -- Nutrition support

    -- Metadata
    source_system VARCHAR(50) DEFAULT 'BOF',
    source_record_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_protected_discharges_fiscal_code ON protected_discharges(fiscal_code);
CREATE INDEX idx_protected_discharges_status ON protected_discharges(discharge_status);
CREATE INDEX idx_protected_discharges_date ON protected_discharges(discharge_date DESC);

-- ============================================================================
-- ETL Metadata Table (tracking data freshness)
-- ============================================================================
CREATE TABLE etl_metadata (
    id SERIAL PRIMARY KEY,
    source_system VARCHAR(50) NOT NULL UNIQUE,
    last_successful_run TIMESTAMP,
    last_run_status VARCHAR(20), -- 'SUCCESS', 'FAILED', 'RUNNING'
    last_run_message TEXT,
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    next_scheduled_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial ETL tracking records
INSERT INTO etl_metadata (source_system, last_run_status) VALUES
    ('CENTRAL_REGISTRY', 'PENDING'),
    ('AURORA', 'PENDING'),
    ('BOF', 'PENDING');

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- Complete Patient Profile View
CREATE OR REPLACE VIEW v_patient_complete AS
SELECT
    p.*,

    -- Recent clinical events count
    (SELECT COUNT(*) FROM clinical_events ce
     WHERE ce.fiscal_code = p.fiscal_code
     AND ce.event_date > CURRENT_DATE - INTERVAL '6 months') as recent_events_6m,

    (SELECT COUNT(*) FROM clinical_events ce
     WHERE ce.fiscal_code = p.fiscal_code
     AND ce.event_date > CURRENT_DATE - INTERVAL '1 year') as recent_events_1y,

    -- Active protected discharge
    (SELECT discharge_status FROM protected_discharges pd
     WHERE pd.fiscal_code = p.fiscal_code
     AND pd.discharge_status = 'ACTIVE'
     ORDER BY pd.discharge_date DESC LIMIT 1) as active_discharge_status,

    -- Last clinical event
    (SELECT event_date FROM clinical_events ce
     WHERE ce.fiscal_code = p.fiscal_code
     ORDER BY ce.event_date DESC LIMIT 1) as last_clinical_event_date

FROM patients p;

-- Recent Clinical Activity View (last 12 months)
CREATE OR REPLACE VIEW v_recent_clinical_activity AS
SELECT
    ce.fiscal_code,
    p.last_name,
    p.first_name,
    ce.event_type,
    ce.event_date,
    ce.diagnosis,
    ce.department
FROM clinical_events ce
JOIN patients p ON ce.fiscal_code = p.fiscal_code
WHERE ce.event_date > CURRENT_DATE - INTERVAL '1 year'
ORDER BY ce.event_date DESC;

-- Active Protected Discharges View
CREATE OR REPLACE VIEW v_active_discharges AS
SELECT
    pd.fiscal_code,
    p.last_name,
    p.first_name,
    pd.discharge_date,
    pd.home_care_active,
    pd.home_care_provider,
    pd.palliative_care,
    pd.hospice,
    pd.sgdt_last_visit_date
FROM protected_discharges pd
JOIN patients p ON pd.fiscal_code = p.fiscal_code
WHERE pd.discharge_status = 'ACTIVE'
ORDER BY pd.discharge_date DESC;

-- ============================================================================
-- Functions for Data Validation
-- ============================================================================

-- Function to validate fiscal code format (Italian fiscal code)
CREATE OR REPLACE FUNCTION validate_fiscal_code(fc VARCHAR(16))
RETURNS BOOLEAN AS $$
BEGIN
    -- Basic validation: 16 chars, alphanumeric
    RETURN fc ~ '^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$';
END;
$$ LANGUAGE plpgsql;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to auto-update updated_at
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clinical_events_updated_at BEFORE UPDATE ON clinical_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_protected_discharges_updated_at BEFORE UPDATE ON protected_discharges
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample Data Queries (for testing)
-- ============================================================================

-- Query patient with all related data
-- SELECT * FROM v_patient_complete WHERE fiscal_code = 'RSSMRA85M01F205X';

-- Query recent clinical activity for a patient
-- SELECT * FROM clinical_events WHERE fiscal_code = 'RSSMRA85M01F205X' ORDER BY event_date DESC;

-- Query active protected discharges
-- SELECT * FROM v_active_discharges;

-- Check ETL status
-- SELECT * FROM etl_metadata;

-- ============================================================================
-- End of Schema
-- ============================================================================
