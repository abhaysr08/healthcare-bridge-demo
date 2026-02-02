import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import chromadb
from openai import OpenAI

from .services.date_utils import calculate_age, normalize_oracle_date

logger = logging.getLogger(__name__)


def create_patient_document(patient: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
    """
    Create a rich text document for embedding that captures all patient information.
    This document will be used for semantic search.
    """
    parts = []

    # Basic patient info
    nome = patient.get("nome", "")
    cognome = patient.get("cognome", "")
    cf = patient.get("codice_fiscale", "")
    sesso = patient.get("sesso", "")
    data_nascita = patient.get("data_nascita", "")

    parts.append(f"Patient: {nome} {cognome}")
    parts.append(f"Fiscal Code (Codice Fiscale): {cf}")

    if sesso:
        gender = "Male" if sesso.upper() == "M" else "Female"
        parts.append(f"Gender: {gender} ({sesso})")

    if data_nascita:
        age = calculate_age(data_nascita)
        if age:
            parts.append(f"Date of Birth: {data_nascita}, Age: {age} years")
        else:
            parts.append(f"Date of Birth: {data_nascita}")

    # Clinical events summary
    if events:
        parts.append(f"Total Clinical Events: {len(events)}")

        # Get unique facilities and diagnoses
        facilities = set()
        diagnoses = set()
        access_types = set()

        for event in events:
            if event.get("struttura"):
                facilities.add(event["struttura"])
            if event.get("presidio"):
                facilities.add(event["presidio"])
            if event.get("diagnosi_acc"):
                diagnoses.add(event["diagnosi_acc"])
            if event.get("tipo_accesso"):
                access_types.add(event["tipo_accesso"])

        if facilities:
            parts.append(f"Healthcare Facilities: {', '.join(facilities)}")
        if access_types:
            parts.append(f"Access Types: {', '.join(access_types)}")
        if diagnoses:
            parts.append(f"Diagnoses: {', '.join(diagnoses)}")

        # Add event details
        parts.append("Clinical History:")
        for i, event in enumerate(events[:10], 1):  # Limit to first 10 events for embedding
            event_parts = []
            if event.get("data_accettazione"):
                event_parts.append(f"Date: {event['data_accettazione']}")
            if event.get("tipo_accesso"):
                event_parts.append(f"Type: {event['tipo_accesso']}")
            if event.get("struttura"):
                event_parts.append(f"Facility: {event['struttura']}")
            if event.get("diagnosi_acc"):
                event_parts.append(f"Diagnosis: {event['diagnosi_acc']}")
            if event_parts:
                parts.append(f"  Event {i}: {', '.join(event_parts)}")

    return "\n".join(parts)


def parse_aurora_json(json_path: str) -> tuple[Dict[str, Dict], Dict[str, List[Dict]]]:
    """
    Parse Aurora JSON file and return patients and their events.
    Returns: (patients_dict, events_dict)
    """
    patients: Dict[str, Dict[str, Any]] = {}
    events: Dict[str, List[Dict[str, Any]]] = {}

    try:
        path = Path(json_path)
        if not path.exists():
            logger.error(f"Aurora data file not found: {json_path}")
            return patients, events

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "results" not in data or len(data["results"]) == 0:
            logger.error("Invalid Aurora JSON structure")
            return patients, events

        items = data["results"][0].get("items", [])

        for item in items:
            fiscal_code = item.get("cf", "").upper().strip()
            if not fiscal_code:
                continue

            # Create or update patient record
            if fiscal_code not in patients:
                patients[fiscal_code] = {
                    "codice_fiscale": fiscal_code,
                    "cognome": item.get("cognome", ""),
                    "nome": item.get("nome", ""),
                    "sesso": item.get("sesso", ""),
                    "data_nascita": normalize_oracle_date(item.get("data_nascita", "")),
                    "id_anag": item.get("id_anag", "")
                }
                events[fiscal_code] = []

            # Add clinical event
            event = {
                "id_anag": item.get("id_anag"),
                "numero_episodio": item.get("numero_episodio"),
                "tipo_accesso": item.get("tipo_accesso"),
                "data_accettazione": normalize_oracle_date(item.get("data_accettazione", "")),
                "data_dimissione": normalize_oracle_date(item.get("data_dimissione", "")) if item.get("data_dimissione") else None,
                "struttura": item.get("struttura"),
                "presidio": item.get("presidio"),
                "diagnosi_acc": item.get("diagnosi_acc") if item.get("diagnosi_acc") else None
            }
            events[fiscal_code].append(event)

        logger.info(f"Parsed {len(patients)} patients with {sum(len(e) for e in events.values())} total events")

    except Exception as e:
        logger.error(f"Failed to parse Aurora JSON: {e}")

    return patients, events


class VectorStoreManager:
    """
    RAG-based vector store manager that handles all patient data through embeddings.
    This is the PRIMARY data source - no direct JSON loading needed elsewhere.
    """

    def __init__(self, openai_client: OpenAI, persist_directory: str, aurora_data_path: Optional[str] = None):
        self.openai_client = openai_client
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = None
        self.aurora_data_path = aurora_data_path

        # In-memory storage for complete patient data (stored as metadata in ChromaDB)
        self._patients: Dict[str, Dict[str, Any]] = {}
        self._events: Dict[str, List[Dict[str, Any]]] = {}

        # Load and parse data if path provided
        if aurora_data_path:
            self._patients, self._events = parse_aurora_json(aurora_data_path)

    def initialize_collection(self):
        """Initialize or get the ChromaDB collection."""
        self.collection = self.chroma_client.get_or_create_collection(
            name="patients",
            metadata={"description": "Healthcare patient records with full RAG support"}
        )
        logger.info(f"Collection initialized with {self.collection.count()} records")

    def clear_collection(self):
        """Clear and recreate the collection."""
        try:
            self.chroma_client.delete_collection("patients")
        except Exception:
            pass
        self.collection = self.chroma_client.create_collection(
            name="patients",
            metadata={"description": "Healthcare patient records with full RAG support"}
        )
        logger.info("Collection cleared and recreated")

    def build_vector_store(self) -> int:
        """
        Build the vector store from loaded patient data.
        Creates embeddings for all patients and stores complete data as metadata.
        Returns the number of patients indexed.
        """
        if not self.collection:
            raise ValueError("Collection not initialized")

        if not self._patients:
            logger.warning("No patient data to index")
            return 0

        documents = []
        metadatas = []
        ids = []

        for cf, patient in self._patients.items():
            patient_events = self._events.get(cf, [])

            # Create rich document for embedding
            doc = create_patient_document(patient, patient_events)
            documents.append(doc)

            # Store complete patient data and events as JSON in metadata
            metadata = {
                "codice_fiscale": cf,
                "nome": patient.get("nome", ""),
                "cognome": patient.get("cognome", ""),
                "sesso": patient.get("sesso", ""),
                "data_nascita": patient.get("data_nascita", ""),
                "id_anag": patient.get("id_anag", ""),
                "event_count": len(patient_events),
                # Store complete data as JSON strings for retrieval
                "patient_json": json.dumps(patient, ensure_ascii=False),
                "events_json": json.dumps(patient_events, ensure_ascii=False)
            }
            metadatas.append(metadata)
            ids.append(f"patient_{cf}")

        # Generate embeddings in batches
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            logger.info(f"Generating embeddings for batch {i//batch_size + 1}...")

            embeddings_response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=batch_docs
            )
            embeddings = [item.embedding for item in embeddings_response.data]

            self.collection.add(
                embeddings=embeddings,
                documents=batch_docs,
                metadatas=batch_metas,
                ids=batch_ids
            )

        logger.info(f"Indexed {len(documents)} patients in vector store")
        return len(documents)

    def search_patients(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search for patients based on query.
        Returns full patient data with events from vector store.
        """
        if not self.collection:
            raise ValueError("Collection not initialized")

        # Generate query embedding
        query_embedding = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        ).data[0].embedding

        # Search vector store
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        search_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                document = results['documents'][0][i]

                # Calculate similarity score
                similarity = max(0, 1 - (distance ** 2 / 2))

                # Parse stored JSON data
                patient_data = json.loads(metadata.get('patient_json', '{}'))
                events_data = json.loads(metadata.get('events_json', '[]'))

                search_results.append({
                    'codice_fiscale': metadata.get('codice_fiscale', ''),
                    'patient': patient_data,
                    'events': events_data,
                    'similarity': similarity,
                    'document': document,
                    'metadata': {
                        'nome': metadata.get('nome', ''),
                        'cognome': metadata.get('cognome', ''),
                        'sesso': metadata.get('sesso', ''),
                        'data_nascita': metadata.get('data_nascita', ''),
                        'event_count': metadata.get('event_count', 0)
                    }
                })

        return search_results

    def get_patient_by_fiscal_code(self, fiscal_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve patient by exact fiscal code match.
        First tries vector store, then falls back to in-memory data.
        """
        if not self.collection:
            raise ValueError("Collection not initialized")

        fiscal_code = fiscal_code.upper().strip()

        # Try vector store first
        try:
            results = self.collection.get(
                ids=[f"patient_{fiscal_code}"],
                include=["metadatas", "documents"]
            )

            if results['ids'] and len(results['ids']) > 0:
                metadata = results['metadatas'][0]
                patient_data = json.loads(metadata.get('patient_json', '{}'))
                events_data = json.loads(metadata.get('events_json', '[]'))

                return {
                    'codice_fiscale': fiscal_code,
                    'patient': patient_data,
                    'events': events_data,
                    'metadata': {
                        'nome': metadata.get('nome', ''),
                        'cognome': metadata.get('cognome', ''),
                        'sesso': metadata.get('sesso', ''),
                        'data_nascita': metadata.get('data_nascita', ''),
                        'event_count': metadata.get('event_count', 0)
                    }
                }
        except Exception as e:
            logger.debug(f"Vector store lookup failed for {fiscal_code}: {e}")

        # Fall back to in-memory data (from parsed JSON)
        if fiscal_code in self._patients:
            patient = self._patients[fiscal_code]
            events = self._events.get(fiscal_code, [])
            logger.info(f"Found patient {fiscal_code} in in-memory data")
            return {
                'codice_fiscale': fiscal_code,
                'patient': patient,
                'events': events,
                'metadata': {
                    'nome': patient.get('nome', ''),
                    'cognome': patient.get('cognome', ''),
                    'sesso': patient.get('sesso', ''),
                    'data_nascita': patient.get('data_nascita', ''),
                    'event_count': len(events)
                }
            }

        return None

    def get_all_patients(self) -> List[Dict[str, Any]]:
        """Get all patients from vector store."""
        if not self.collection:
            raise ValueError("Collection not initialized")

        results = self.collection.get(include=["metadatas"])

        patients = []
        if results['ids']:
            for metadata in results['metadatas']:
                patients.append({
                    'codice_fiscale': metadata.get('codice_fiscale', ''),
                    'nome': metadata.get('nome', ''),
                    'cognome': metadata.get('cognome', ''),
                    'sesso': metadata.get('sesso', ''),
                    'data_nascita': metadata.get('data_nascita', ''),
                    'event_count': metadata.get('event_count', 0)
                })

        return patients

    def get_patient_count(self) -> int:
        """Get total number of patients in vector store."""
        if not self.collection:
            return 0
        return self.collection.count()

    def patient_exists(self, fiscal_code: str) -> bool:
        """Check if patient exists in vector store."""
        return self.get_patient_by_fiscal_code(fiscal_code) is not None


def create_rag_context(search_results: List[Dict[str, Any]], query: str) -> str:
    """
    Create context string from RAG search results for LLM consumption.
    """
    if not search_results:
        return "\n\n**No matching patients found in the database.**"

    # Check if this is an analytics query
    analytics_keywords = [
        'how many', 'quanti', 'count', 'list', 'lista', 'all patients',
        'tutti i pazienti', 'which', 'quali', 'who', 'chi', 'total', 'totale'
    ]
    query_lower = query.lower()
    is_analytics = any(kw in query_lower for kw in analytics_keywords)

    if is_analytics:
        # For analytics queries, provide summary
        context = f"\n\n**Found {len(search_results)} matching patients:**\n"
        for result in search_results:
            patient = result['patient']
            context += f"- {patient.get('nome', '')} {patient.get('cognome', '')} (CF: {result['codice_fiscale']})\n"
        return context

    # For specific patient queries, return detailed info
    top_result = search_results[0]
    similarity = top_result['similarity']

    if similarity >= 0.4:  # Good match threshold
        patient = top_result['patient']
        events = top_result['events']

        patient_context = {
            **patient,
            'clinical_events': events,
            'event_count': len(events)
        }

        context = f"\n\n**Patient Data (similarity: {similarity:.0%}):**\n"
        context += f"```json\n{json.dumps(patient_context, ensure_ascii=False, indent=2)}\n```"
        return context

    # Low confidence - show top matches
    context = f"\n\n**Low confidence matches (top result: {similarity:.0%}):**\n"
    for result in search_results[:3]:
        patient = result['patient']
        context += f"- {patient.get('nome', '')} {patient.get('cognome', '')} (CF: {result['codice_fiscale']}, match: {result['similarity']:.0%})\n"
    context += "\n**Please provide a fiscal code for accurate patient lookup.**"

    return context
