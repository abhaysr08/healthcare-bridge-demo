-- ============================================================================
-- Healthbridge Care+ Consolidated Database Schema
-- PostgreSQL 14+
-- Based on real Aurora PAZIENTI_ACCESSO2 columns:
-- ID_ANAG, COGNOME, NOME, CF, SESSO, DATA_NASCITA,
-- TIPO_ACCESSO, NUMERO_EPISODIO, DATA_ACCETTAZIONE,
-- DATA_DIMISSIONE, STRUTTURA, PRESIDIO, DIAGNOSI_ACC
-- ============================================================================

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS clinical_events CASCADE;
DROP TABLE IF EXISTS protected_discharges CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS etl_metadata CASCADE;

-- ============================================================================
-- Core Patient Table
-- Primary source: Central Registry API
-- Fallback: demographics from Aurora PAZIENTI_ACCESSO2
-- ============================================================================
CREATE TABLE patients (
    fiscal_code         VARCHAR(16) PRIMARY KEY,

    -- Demographics (from Registry API or Aurora)
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    birth_date          DATE,
    sex                 VARCHAR(10),

    -- Contact / Address (from Registry API only)
    residence_address   TEXT,
    domicile_address    TEXT,
    phone_numbers       JSONB,
    email               VARCHAR(255),

    -- Primary Doctor (from Registry API only)
    primary_doctor_name  VARCHAR(200),
    primary_doctor_email VARCHAR(255),

    -- Exemptions (from Registry API only)
    exemptions          JSONB,

    -- Clinical / Service Flags (from Registry API only)
    disability_status   BOOLEAN DEFAULT FALSE,
    disability_details  TEXT,
    cps_active          BOOLEAN DEFAULT FALSE,
    noa_sert_active     BOOLEAN DEFAULT FALSE,

    -- Caregiver (from Registry API only)
    caregiver_name          VARCHAR(200),
    caregiver_relationship  VARCHAR(100),
    caregiver_phone         VARCHAR(50),

    -- Metadata
    source_system   VARCHAR(50) DEFAULT 'CENTRAL_REGISTRY',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_validated  TIMESTAMP,

    CONSTRAINT check_fiscal_code CHECK (LENGTH(fiscal_code) = 16)
);

CREATE INDEX idx_patients_last_name  ON patients(last_name);
CREATE INDEX idx_patients_birth_date ON patients(birth_date);
CREATE INDEX idx_patients_updated_at ON patients(updated_at);

-- ============================================================================
-- Clinical Events Table
-- Source: Aurora Oracle DB - PAZIENTI_ACCESSO2
-- One row per access/episode
-- ============================================================================
CREATE TABLE clinical_events (
    id              SERIAL PRIMARY KEY,
    fiscal_code     VARCHAR(16) NOT NULL REFERENCES patients(fiscal_code) ON DELETE CASCADE,

    -- Episode identifier from Aurora (used for delta sync / deduplication)
    episode_number  VARCHAR(50),

    -- Access type (TIPO_ACCESSO): e.g. ESTERNI, RICOVERO, PRONTO SOCCORSO
    event_type      VARCHAR(100),

    -- Dates (DATA_ACCETTAZIONE, DATA_DIMISSIONE)
    admission_date  TIMESTAMP,
    discharge_date  TIMESTAMP,

    -- Location (STRUTTURA = facility, PRESIDIO = hospital unit)
    structure       VARCHAR(200),
    hospital_unit   VARCHAR(200),

    -- Clinical (DIAGNOSI_ACC)
    diagnosis       TEXT,

    -- Metadata
    source_system   VARCHAR(50) DEFAULT 'AURORA',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate episodes
    CONSTRAINT uq_episode UNIQUE (fiscal_code, episode_number)
);

CREATE INDEX idx_clinical_events_fiscal_code   ON clinical_events(fiscal_code);
CREATE INDEX idx_clinical_events_admission_date ON clinical_events(admission_date DESC);
CREATE INDEX idx_clinical_events_event_type    ON clinical_events(event_type);

-- ============================================================================
-- Protected Discharges Table
-- Source: BOF API
-- ============================================================================
CREATE TABLE protected_discharges (
    id              SERIAL PRIMARY KEY,
    fiscal_code     VARCHAR(16) NOT NULL REFERENCES patients(fiscal_code) ON DELETE CASCADE,

    discharge_date      DATE,
    discharge_type      VARCHAR(100),
    discharge_status    VARCHAR(50),

    -- Home Care
    home_care_active    BOOLEAN DEFAULT FALSE,
    home_care_provider  VARCHAR(200),
    home_care_pathway   VARCHAR(200),

    -- Palliative / Hospice
    palliative_care     BOOLEAN DEFAULT FALSE,
    hospice             BOOLEAN DEFAULT FALSE,

    -- Social Services
    social_services_active  BOOLEAN DEFAULT FALSE,
    social_services_notes   TEXT,

    -- SGDT
    sgdt_last_visit_date        DATE,
    sgdt_last_visit_operator    VARCHAR(200),
    sgdt_notes                  TEXT,

    -- Special Programs
    measure_b1_active       BOOLEAN DEFAULT FALSE,
    nad_nutrition_active    BOOLEAN DEFAULT FALSE,

    -- Rich BOF fields
    patient_description     TEXT,
    care_level              TEXT,
    admission_date          DATE,
    operators_involved      TEXT,

    -- Metadata
    source_system       VARCHAR(50) DEFAULT 'BOF',
    source_record_id    VARCHAR(100),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Prosthetics Items Table
-- Source: Oracle NFS DB - azeuro.CLIENTE_ASSISTANT
-- One row per prescription/delivery
-- ============================================================================
CREATE TABLE prosthetics_items (
    id                  SERIAL PRIMARY KEY,
    fiscal_code         VARCHAR(16) NOT NULL REFERENCES patients(fiscal_code) ON DELETE CASCADE,

    -- Prescription identifiers
    prescription_id     VARCHAR(50),
    delivery_note       VARCHAR(50),

    -- Dates
    delivery_date       TIMESTAMP,
    send_date           TIMESTAMP,

    -- Supplier
    supplier_code       VARCHAR(50),
    supplier_name       VARCHAR(200),

    -- Product
    product_code        VARCHAR(50),
    product_description TEXT,
    brand               VARCHAR(100),
    model               VARCHAR(100),

    -- Quantity / Price
    quantity            VARCHAR(20),
    unit_price          NUMERIC(10,2),
    total_price         NUMERIC(10,2),

    -- Administrative
    district            VARCHAR(50),
    status              VARCHAR(20),
    operation_type      VARCHAR(10),

    -- Metadata
    source_system       VARCHAR(50) DEFAULT 'PROSTHETICS_NFS',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_prescription UNIQUE (fiscal_code, prescription_id)
);

CREATE INDEX idx_prosthetics_fiscal_code   ON prosthetics_items(fiscal_code);
CREATE INDEX idx_prosthetics_delivery_date ON prosthetics_items(delivery_date DESC);

CREATE INDEX idx_protected_discharges_fiscal_code ON protected_discharges(fiscal_code);
CREATE INDEX idx_protected_discharges_status      ON protected_discharges(discharge_status);
CREATE INDEX idx_protected_discharges_date        ON protected_discharges(discharge_date DESC);

-- ============================================================================
-- ETL Metadata Table
-- ============================================================================
CREATE TABLE etl_metadata (
    id                  SERIAL PRIMARY KEY,
    source_system       VARCHAR(50) NOT NULL UNIQUE,
    last_successful_run TIMESTAMP,
    last_run_status     VARCHAR(20),
    last_run_message    TEXT,
    records_processed   INTEGER DEFAULT 0,
    records_failed      INTEGER DEFAULT 0,
    next_scheduled_run  TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO etl_metadata (source_system, last_run_status) VALUES
    ('CENTRAL_REGISTRY', 'PENDING'),
    ('AURORA', 'PENDING'),
    ('BOF', 'PENDING'),
    ('PROSTHETICS_NFS', 'PENDING');

-- ============================================================================
-- Views
-- ============================================================================

CREATE OR REPLACE VIEW v_patient_complete AS
SELECT
    p.*,
    (SELECT COUNT(*) FROM clinical_events ce
     WHERE ce.fiscal_code = p.fiscal_code
     AND ce.admission_date > CURRENT_DATE - INTERVAL '6 months') AS recent_events_6m,

    (SELECT COUNT(*) FROM clinical_events ce
     WHERE ce.fiscal_code = p.fiscal_code
     AND ce.admission_date > CURRENT_DATE - INTERVAL '1 year')  AS recent_events_1y,

    (SELECT discharge_status FROM protected_discharges pd
     WHERE pd.fiscal_code = p.fiscal_code
     AND pd.discharge_status = 'ACTIVE'
     ORDER BY pd.discharge_date DESC LIMIT 1) AS active_discharge_status,

    (SELECT admission_date FROM clinical_events ce
     WHERE ce.fiscal_code = p.fiscal_code
     ORDER BY ce.admission_date DESC LIMIT 1) AS last_clinical_event_date
FROM patients p;


CREATE OR REPLACE VIEW v_recent_clinical_activity AS
SELECT
    ce.fiscal_code,
    p.last_name,
    p.first_name,
    ce.event_type,
    ce.admission_date,
    ce.discharge_date,
    ce.diagnosis,
    ce.structure,
    ce.hospital_unit
FROM clinical_events ce
JOIN patients p ON ce.fiscal_code = p.fiscal_code
WHERE ce.admission_date > CURRENT_DATE - INTERVAL '1 year'
ORDER BY ce.admission_date DESC;


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
-- Functions & Triggers
-- ============================================================================

CREATE OR REPLACE FUNCTION validate_fiscal_code(fc VARCHAR(16))
RETURNS BOOLEAN AS $$
BEGIN
    RETURN fc ~ '^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clinical_events_updated_at
    BEFORE UPDATE ON clinical_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_protected_discharges_updated_at
    BEFORE UPDATE ON protected_discharges
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- End of Schema
-- ============================================================================
