import json
import logging
from typing import List
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


def create_context_from_results(results: List[dict], query: str) -> str:
    if not results:
        return "\n\n**No relevant patients found in the database.**"

    top_similarity = results[0]['similarity']

    if top_similarity >= 0.8:
        patient = results[0]['patient']
        context = f"\n\n**Most Relevant Patient (confidence: {top_similarity:.2%}):**\n```json\n{json.dumps(patient, ensure_ascii=False, indent=2)}\n```"
        return context

    elif top_similarity >= 0.6:
        summaries = []
        for i, result in enumerate(results[:3], 1):
            patient = result['patient']
            summary = {
                "Nome": patient.get("Nome"),
                "Cognome": patient.get("Cognome"),
                "Residenza": patient.get("Residenza"),
                "Ricoveri_allergie_quali": patient.get("Ricoveri_allergie_quali"),
                "Ricoveri_diagnosi": patient.get("Ricoveri_diagnosi"),
                "Cure_domiciliari_attive": patient.get("Cure_domiciliari_attive"),
                "Misura_B1_attiva": patient.get("Misura_B1_attiva"),
                "similarity": f"{result['similarity']:.2%}"
            }
            summaries.append(summary)

        context = f"\n\n**Top {len(summaries)} Relevant Patients:**\n```json\n{json.dumps(summaries, ensure_ascii=False, indent=2)}\n```"
        return context

    else:
        summaries = []
        for result in results[:3]:
            patient = result['patient']
            summaries.append({
                "Nome": patient.get("Nome"),
                "Cognome": patient.get("Cognome"),
                "Residenza": patient.get("Residenza")
            })

        context = f"\n\n**Note:** Low relevance match (top similarity: {top_similarity:.2%}). "
        context += f"Here are the closest patients, but they may not be highly relevant:\n```json\n{json.dumps(summaries, ensure_ascii=False, indent=2)}\n```"
        return context
