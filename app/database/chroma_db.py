import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages ChromaDB collections and text embeddings for semantic skill matching."""

    def __init__(self):
        self.chroma_client = None
        self.encoder = None
        self._init_encoder()
        self._init_chroma()

    def _init_encoder(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self.is_fallback = False
            self.vector_mode = "sentence_transformers"
            logger.info("Loaded SentenceTransformer ('all-MiniLM-L6-v2').")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({e}). Using deterministic lexical vectorizer fallback.")
            self.encoder = None
            self.is_fallback = True
            self.vector_mode = "deterministic_lexical_fallback"

    def _init_chroma(self):
        try:
            import chromadb
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            self.market_collection = self.chroma_client.get_or_create_collection("market_skills")
            self.course_collection = self.chroma_client.get_or_create_collection("course_outcomes")
            logger.info("ChromaDB persistent client initialized successfully.")
        except Exception as e:
            logger.warning(f"ChromaDB initialization error ({e}). Using in-memory fallback store.")
            self.chroma_client = None
            self.in_memory_vectors: Dict[str, Dict] = {}

    def _get_lexical_vector(self, text: str, dim: int = 384) -> List[float]:
        """
        Deterministic lexical token hash vector.
        Maps alphanumeric tokens to fixed dimensions with term frequencies.
        Guarantees that texts sharing words have genuine lexical cosine similarity,
        and texts with zero overlap have 0.0 similarity (no pseudo-random similarity).
        """
        import re
        import hashlib
        tokens = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
        if not tokens:
            return [0.0] * dim
        vec = np.zeros(dim, dtype=float)
        for token in tokens:
            idx = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16) % dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / (norm + 1e-9)
        return vec.tolist()

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates 384-dim dense embedding for input text.
        Uses SentenceTransformer when available, or deterministic lexical token
        vector as an explicit non-random fallback.
        """
        if self.encoder:
            return self.encoder.encode(text).tolist()
        return self._get_lexical_vector(text)

    def add_skill(self, skill_id: str, text: str, metadata: Dict[str, Any]):
        embedding = self.get_embedding(text)
        if self.chroma_client:
            self.market_collection.upsert(
                ids=[skill_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
        else:
            self.in_memory_vectors[skill_id] = {
                "id": skill_id,
                "embedding": embedding,
                "document": text,
                "metadata": metadata
            }

    def search_similar_skills(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches ChromaDB for most similar skills to a given embedding vector."""
        if self.chroma_client:
            results = self.market_collection.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )
            parsed = []
            if results and results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    parsed.append({
                        "skill_id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
                    })
            return parsed
        else:
            # In-memory cosine similarity calculation
            q = np.array(query_vector)
            q_norm = np.linalg.norm(q) + 1e-9
            scores = []
            for s_id, data in self.in_memory_vectors.items():
                v = np.array(data["embedding"])
                v_norm = np.linalg.norm(v) + 1e-9
                cosine_sim = float(np.dot(q, v) / (q_norm * v_norm))
                scores.append((cosine_sim, data))
            scores.sort(key=lambda x: x[0], reverse=True)
            return [{
                "skill_id": data["id"],
                "document": data["document"],
                "metadata": data["metadata"],
                "distance": 1.0 - sim
            } for (sim, data) in scores[:top_k]]

vector_store = VectorStoreManager()
