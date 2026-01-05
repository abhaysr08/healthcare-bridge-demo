import json
import logging
from typing import List
from datetime import datetime
import chromadb
from mistralai import Mistral
from .utils import create_patient_summary

logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self, mistral_client: Mistral, persist_directory: str, patients_data: List[dict]):
        self.mistral_client = mistral_client
        self.chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.collection = None
        self.patients_data = patients_data
        logger.info(f"Initialized VectorStoreManager with persist directory: {persist_directory}")

    def initialize_collection(self):
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name="patients",
                metadata={"description": "Healthcare patient records for semantic search"}
            )
            logger.info(f"Collection 'patients' initialized with {self.collection.count()} existing records")
        except Exception as e:
            logger.error(f"Error initializing collection: {e}")
            raise

    def add_patients(self, patients: List[dict]):
        if not self.collection:
            raise ValueError("Collection not initialized. Call initialize_collection() first.")

        try:
            logger.info(f"Creating summaries for {len(patients)} patients...")
            documents = []
            metadatas = []
            ids = []

            for i, patient in enumerate(patients):
                summary = create_patient_summary(patient)
                documents.append(summary)

                metadatas.append({
                    "patient_id": str(i),
                    "nome": patient.get("Nome", ""),
                    "cognome": patient.get("Cognome", ""),
                    "codice_fiscale": patient.get("Codice_fiscale", ""),
                    "residenza": patient.get("Residenza", "")
                })
                ids.append(f"patient_{i}")

            logger.info("Generating embeddings via Mistral API...")
            embeddings_response = self.mistral_client.embeddings.create(
                model="mistral-embed",
                inputs=documents
            )

            embeddings = [item.embedding for item in embeddings_response.data]
            logger.info(f"Generated {len(embeddings)} embeddings")

            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully added {len(patients)} patients to vector store")

        except Exception as e:
            logger.error(f"Error adding patients to vector store: {e}")
            raise

    def search_patients(self, query: str, top_k: int = 3) -> List[dict]:
        if not self.collection:
            raise ValueError("Collection not initialized. Call initialize_collection() first.")

        try:
            query_embedding_response = self.mistral_client.embeddings.create(
                model="mistral-embed",
                inputs=[query]
            )
            query_embedding = query_embedding_response.data[0].embedding

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            search_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    patient_id = int(results['metadatas'][0][i]['patient_id'])
                    distance = results['distances'][0][i]

                    similarity = max(0, 1 - (distance ** 2 / 2))

                    search_results.append({
                        'patient': self.patients_data[patient_id],
                        'patient_id': patient_id,
                        'similarity': similarity,
                        'metadata': results['metadatas'][0][i]
                    })

                logger.info(f"Search for '{query}': Found {len(search_results)} results, "
                           f"top similarity: {search_results[0]['similarity']:.3f}")

            return search_results

        except Exception as e:
            logger.error(f"Error searching patients: {e}")
            raise

    def get_patient_by_id(self, patient_id: int) -> dict:
        if patient_id < 0 or patient_id >= len(self.patients_data):
            raise ValueError(f"Invalid patient ID: {patient_id}")
        return self.patients_data[patient_id]


def create_context_from_results(results: List[dict], query: str, all_patients_data: List[dict] = None) -> str:
    """
    Create context from search results.
    For analytics/statistics queries, provides complete database with essential fields.
    For specific patient queries, provides top matches.
    """

    analytics_keywords = [
        'how many', 'quanti', 'count', 'conta', 'list', 'lista', 'elenca',
        'all patients', 'tutti i pazienti', 'patients', 'pazienti',
        'receiving', 'ricevono', 'taking', 'prendono', 'with', 'con',
        'their names', 'i nomi', 'i loro nomi', 'give me', 'dammi',
        'tell me', 'dimmi', 'show', 'mostra', 'provide', 'fornisci',
        'which', 'quali', 'who', 'chi', 'over', 'oltre', 'under', 'sotto',
        'years old', 'anni', 'age', 'età', 'elderly', 'anziani', 'older', 'younger',
        'live in', 'lives in', 'residing', 'reside', 'vivono', 'abita', 'abitano',
        'enrolled', 'iscritti', 'iscritt'
    ]

    query_lower = query.lower()
    is_analytics_query = any(keyword in query_lower for keyword in analytics_keywords)

    if is_analytics_query and all_patients_data:
        def calculate_age(birth_date_str):
            try:
                birth_date = datetime.strptime(birth_date_str, "%d/%m/%Y")
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                return age
            except:
                return None

        filtered_patients = all_patients_data
        filter_applied = "No filter"

        if 'female' in query_lower or 'women' in query_lower or 'femmine' in query_lower or 'donne' in query_lower:
            filtered_patients = [p for p in all_patients_data if p.get('Sesso') == 'F']
            filter_applied = "Gender = Female (Sesso = 'F')"
        elif 'male' in query_lower or 'men' in query_lower or 'maschi' in query_lower or 'uomini' in query_lower:
            filtered_patients = [p for p in all_patients_data if p.get('Sesso') == 'M']
            filter_applied = "Gender = Male (Sesso = 'M')"

        elif 'home care' in query_lower or 'cure domiciliari' in query_lower or 'domiciliar' in query_lower:
            filtered_patients = [p for p in all_patients_data if p.get('Cure_domiciliari_attive') == 'Si']
            filter_applied = "Home Care Active (Cure_domiciliari_attive = 'Si')"

        elif 'palliative' in query_lower or 'palliativ' in query_lower:
            filtered_patients = [p for p in all_patients_data if p.get('Cure_palliative') == 'Si']
            filter_applied = "Palliative Care (Cure_palliative = 'Si')"

        elif 'misura b1' in query_lower or 'b1' in query_lower:
            filtered_patients = [p for p in all_patients_data if p.get('Misura_B1_attiva') == 'Si']
            filter_applied = "Misura B1 Active (Misura_B1_attiva = 'Si')"

        elif 'caregiver' in query_lower or 'badante' in query_lower:
            filtered_patients = [p for p in all_patients_data if p.get('Caregiver_nome')]
            filter_applied = "Has Caregiver (Caregiver_nome is not empty)"

        elif 'over 90' in query_lower or 'oltre 90' in query_lower or 'più di 90' in query_lower:
            filtered_patients = [p for p in all_patients_data if calculate_age(p.get('Data_nascita', '')) and calculate_age(p.get('Data_nascita', '')) > 90]
            filter_applied = "Age > 90 years"
        elif 'over 80' in query_lower or 'oltre 80' in query_lower or 'più di 80' in query_lower:
            filtered_patients = [p for p in all_patients_data if calculate_age(p.get('Data_nascita', '')) and calculate_age(p.get('Data_nascita', '')) > 80]
            filter_applied = "Age > 80 years"
        elif 'over 70' in query_lower or 'oltre 70' in query_lower or 'più di 70' in query_lower:
            filtered_patients = [p for p in all_patients_data if calculate_age(p.get('Data_nascita', '')) and calculate_age(p.get('Data_nascita', '')) > 70]
            filter_applied = "Age > 70 years"
        elif 'elderly' in query_lower or 'anziani' in query_lower or 'anziane' in query_lower:
            filtered_patients = [p for p in all_patients_data if calculate_age(p.get('Data_nascita', '')) and calculate_age(p.get('Data_nascita', '')) >= 65]
            filter_applied = "Age >= 65 years (elderly)"

        else:
            cities = ['napoli', 'roma', 'milano', 'torino', 'firenze', 'bologna', 'genova', 'bari']
            for city in cities:
                if city in query_lower:
                    filtered_patients = [p for p in all_patients_data if p.get('Residenza', '').lower() == city.capitalize()]
                    filter_applied = f"Residence = {city.capitalize()}"
                    break

        names_list = [f"{p.get('Nome')} {p.get('Cognome')}" for p in filtered_patients]

        context = f"\n\n**BACKEND FILTERED RESULTS:**\n"
        context += f"Filter applied: {filter_applied}\n"
        context += f"**EXACT COUNT: {len(filtered_patients)} patients**\n\n"
        context += f"**Complete list of {len(filtered_patients)} patient names:**\n"
        for name in names_list:
            context += f"- {name}\n"
        context += f"\n**CRITICAL: Report these EXACT {len(filtered_patients)} names. Do NOT add, remove, or modify any names.**"
        return context

    if not results:
        return "\n\n**No relevant patients found in the database.**"

    top_similarity = results[0]['similarity']

    if top_similarity >= 0.5:
        patient = results[0]['patient']
        context = f"\n\n**Most Relevant Patient (confidence: {top_similarity:.2%}):**\n```json\n{json.dumps(patient, ensure_ascii=False, indent=2)}\n```"

        if len(results) > 1:
            additional_patients = [r for r in results[1:] if r['similarity'] >= (top_similarity - 0.1)]
            if additional_patients:
                context += f"\n\n**Other Potentially Relevant Patients:**\n"
                for result in additional_patients[:2]:
                    patient_info = result['patient']
                    context += f"\n- {patient_info.get('Nome')} {patient_info.get('Cognome')} "
                    context += f"(similarity: {result['similarity']:.2%}, "
                    context += f"from {patient_info.get('Residenza', 'Unknown')})"

        return context

    else:
        summaries = []
        for result in results[:3]:
            patient = result['patient']
            summaries.append({
                "Nome": patient.get("Nome"),
                "Cognome": patient.get("Cognome"),
                "Residenza": patient.get("Residenza"),
                "Data_nascita": patient.get("Data_nascita"),
                "Ricoveri_diagnosi": patient.get("Ricoveri_diagnosi")
            })

        context = f"\n\n**Note:** Low relevance match (top similarity: {top_similarity:.2%}). "
        context += f"The query may not match well. Here are the closest patients:\n```json\n{json.dumps(summaries, ensure_ascii=False, indent=2)}\n```"
        return context
