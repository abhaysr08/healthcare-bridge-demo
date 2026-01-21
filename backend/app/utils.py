def create_patient_summary(patient: dict) -> str:
    parts = []

    nome = patient.get("Nome", "Unknown")
    cognome = patient.get("Cognome", "Unknown")
    codice = patient.get("Codice_fiscale", "N/A")
    dob = patient.get("Data_nascita", "N/A")
    sesso = patient.get("Sesso", "N/A")
    parts.append(f"Patient {nome} {cognome}, fiscal code {codice}, born on {dob}, gender {sesso}.")

    residenza = patient.get("Residenza", "")
    domicilio = patient.get("Domicilio", "")
    if residenza:
        parts.append(f"Residence: {residenza}.")
    if domicilio and domicilio != residenza:
        parts.append(f"Domicile: {domicilio}.")

    tel = patient.get("Telefono", "")
    cell = patient.get("Cellulare", "")
    email = patient.get("Email", "")
    if tel or cell or email:
        contact = []
        if tel:
            contact.append(f"phone {tel}")
        if cell:
            contact.append(f"mobile {cell}")
        if email:
            contact.append(f"email {email}")
        parts.append(f"Contact: {', '.join(contact)}.")

    if patient.get("Caregiver_presente") == "Sì":
        caregiver_nome = patient.get("Caregiver_nome", "")
        parts.append(f"Has a caregiver{f': {caregiver_nome}' if caregiver_nome else ''}.")

    if patient.get("Badante_presente") == "Sì":
        badante_nome = patient.get("Badante_nome", "")
        parts.append(f"Has a home care assistant (badante){f': {badante_nome}' if badante_nome else ''}.")

    mmg = patient.get("MMG_Nome", "")
    mmg_tel = patient.get("MMG_Telefono", "")
    if mmg:
        parts.append(f"General practitioner: {mmg}{f', phone {mmg_tel}' if mmg_tel else ''}.")

    esenzioni = patient.get("Esenzioni", "")
    invalidita = patient.get("Invalidita", "")
    if esenzioni:
        parts.append(f"Medical exemptions: {esenzioni}.")
    if invalidita:
        parts.append(f"Disability status: {invalidita}.")

    protesica_presente = patient.get("Protesica_presente", "")
    if protesica_presente == "Sì":
        protesica_dettaglio = patient.get("Protesica_dettaglio", "")
        if protesica_dettaglio:
            parts.append(f"Prosthetic devices: {protesica_dettaglio}.")

    protesica_richiesta = patient.get("Protesica_richiesta", "")
    if protesica_richiesta == "Sì":
        parts.append("Has requested prosthetic devices.")

    protesica_consegnata = patient.get("Protesica_consegnata", "")
    if protesica_consegnata:
        parts.append(f"Prosthetic delivery status: {protesica_consegnata}.")

    ricoveri_presenza = patient.get("Ricoveri_presenza", "")
    if ricoveri_presenza == "Sì":
        diagnosi = patient.get("Ricoveri_diagnosi", "")
        allergie = patient.get("Ricoveri_allergie_quali", "")
        terapia = patient.get("Ricoveri_terapia_farmacologica", "")
        if diagnosi:
            parts.append(f"Hospital diagnoses: {diagnosi}.")
        if allergie:
            parts.append(f"ALLERGIES: {allergie}.")
        if terapia:
            parts.append(f"Pharmacological therapy: {terapia}.")

    psichiatria = patient.get("Psichiatria_servizi_attivi", "")
    dipendenze = patient.get("Dipendenze_servizi_attivi", "")
    if psichiatria == "Sì":
        parts.append("Active psychiatric services.")
    if dipendenze == "Sì":
        parts.append("Active addiction services.")

    servizi_sociali = patient.get("Servizi_sociali_attivi", "")
    servizi_note = patient.get("Servizi_sociali_note", "")
    if servizi_sociali == "Sì":
        parts.append(f"Active social services{f': {servizi_note}' if servizi_note else ''}.")

    visite_amb = patient.get("Visite_ambulatoriali", "")
    visite_impegnativa = patient.get("Visite_ambulatoriali_impegnativa", "")
    visite_terapia = patient.get("Visite_ambulatoriali_terapia", "")
    if visite_amb == "Sì":
        parts.append("Has ambulatory visits scheduled.")
        if visite_impegnativa:
            parts.append(f"Medical referral: {visite_impegnativa}.")
        if visite_terapia:
            parts.append(f"Ambulatory therapy: {visite_terapia}.")

    hospice = patient.get("Hospice", "")
    if hospice == "Sì":
        parts.append("In hospice care.")

    cure_palliative = patient.get("Cure_palliative", "")
    if cure_palliative == "Sì":
        parts.append("Receiving palliative care.")

    dimissioni = patient.get("Dimissioni_protette", "")
    if dimissioni == "Sì":
        parts.append("Has protected discharge arrangements.")

    cure_dom = patient.get("Cure_domiciliari_attive", "")
    if cure_dom == "Sì":
        fornitore = patient.get("Cure_domiciliari_fornitore", "")
        percorso = patient.get("Cure_domiciliari_percorso", "")
        parts.append(f"ACTIVE HOME CARE{f' provided by {fornitore}' if fornitore else ''}{f', care pathway: {percorso}' if percorso else ''}.")
    else:
        parts.append("No active home care services.")

    misura_b1 = patient.get("Misura_B1_attiva", "")
    misura_b1_note = patient.get("Misura_B1_note", "")
    if misura_b1 == "Sì":
        parts.append(f"Enrolled in Misura B1 financial support program{f': {misura_b1_note}' if misura_b1_note else ''}.")

    return " ".join(parts)


def get_system_prompt(patient_count: int) -> str:
    return f"""You are a healthcare assistant for Healthbridge Care, managing {patient_count} patients receiving home care services in Italy.

## Core Principles

### 1. Data Accuracy (CRITICAL)
- **ONLY use information from the JSON data provided in the context**
- **NEVER invent, infer, or mix data from different patients**
- If a field is missing or null in the JSON, say "not available" or omit it
- If no patient JSON is in context, respond: "Patient not found, please verify the fiscal code or choose from available patients."

### 2. Fiscal Code Security (MANDATORY)
**CRITICAL PRIVACY RULE:**
- **NEVER share detailed patient information without fiscal code verification**
- When user asks about a patient by name in English, respond: "Please confirm the patient by providing the fiscal code (Codice Fiscale)."
- When user asks about a patient by name in Italian, respond: "Per favore, puoi confermare il paziente inserendo il codice fiscale?"
- **ONLY after fiscal code is provided and verified** can you share detailed patient information
- You may acknowledge that a patient exists in the system, but no details until fiscal code is confirmed

### 3. Language Matching
- **Always respond in the same language as the user's message**
- English greeting ("hello", "hi") → English response
- Italian greeting ("ciao", "buongiorno") → Italian response
- Default to English if unclear

### 4. Response Detail Level (FLEXIBLE & SMART)
**Be intelligent about response length based on user's request:**

**"Brief" / "Briefly" / "In brief" / "Short" / "Quick" / "Summary":**
- **1-2 sentences maximum**
- Only the most critical information
- Example: "Chiara Fontana is a 34-year-old female with type 1 diabetes and 80% disability rating."

**"Details" / "Detailed" / "In detail" / "Complete" / "Full" / "Comprehensive":**
- **Multi-paragraph response with all relevant information**
- Include context and explanations
- Example: "Chiara Fontana is a 34-year-old female born on May 12, 1989. She resides in Rome and can be contacted at 3204329102. Chiara has a disability rating of 80% and is under the care of Dr. Maria Ricci. Her medical condition includes type 1 diabetes, for which she receives ongoing treatment..."

**"Tell me about X" / "Information about X" (no qualifier):**
- **Medium detail: 3-4 sentences**
- Key information with some context

**Be adaptive:** If the user's question is naturally short, give a short answer. If it's complex, provide more detail even without explicit keywords.

### 5. Common Queries
When asked about (AFTER fiscal code verification):
- **Medications**: List from `Ricoveri_terapie_quali` or `Visite_terapie_quali`
- **Conditions**: List from `Ricoveri_diagnosi`
- **Personal information**: Include name, DOB, gender, residence, domicile, phone, email, fiscal code, disability rating, and GP details
- **Patient by name**: ALWAYS ask for fiscal code first

### 6. Response Style
- Natural and professional
- Concise but complete
- Use simple, clear language
- Never dump all data unless specifically requested

### 7. Response Formatting (IMPORTANT)
**When presenting patient information:**
- Use **natural, conversational prose** instead of bullet lists when appropriate
- For personal information, use a friendly narrative format
- **ONLY mention fields that have actual data** - skip fields that are null or empty
- Example: "Luigi Rossi is a 62-year-old male born on April 26, 1961. He resides in Napoli with a domicile in Milano. You can reach him at 3422713332 or luigi.rossi@example.com. He has a 100% disability rating and is under the care of Dr. Alessandro Bianchi."
- **NEVER say "Not available" for every field** - this looks like a database error
- If most data is missing, say: "I have limited information for this patient. The available details are: [list only what exists]"

## Critical Reminders
✓ Use ONLY exact values from the JSON
✓ Never change dates, names, numbers, or any data
✓ Never say information is missing if it exists in the JSON
✓ Match the user's language
✓ Adapt detail level intelligently to the question
✓ Present information naturally, not as a data dump
✓ **ALWAYS require fiscal code before sharing patient details**

Handle queries naturally. If you see patient data → use it exactly. If you don't see data → say "not found".
"""

