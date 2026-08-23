"""DikaAI Vector DB - Simple in-memory vector store for RAG."""

import json
from pathlib import Path
from dikaai.rag.embeddings import embed_text, cosine_similarity
from dikaai.config import RAG, DATA_DIR


class VectorDB:
    """Simple in-memory vector database."""

    def __init__(self, path: str = None):
        self.path = Path(path) if path else DATA_DIR / "rag" / "vectors.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.dim = RAG['embedding_dim']
        self.documents = self._load()

    def _load(self) -> list:
        if self.path.exists():
            try:
                with open(self.path) as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save(self):
        # Keep under 10K documents
        if len(self.documents) > 10000:
            self.documents = self.documents[-10000:]
        with open(self.path, 'w') as f:
            json.dump(self.documents, f, ensure_ascii=False)

    def add(self, text: str, metadata: dict = None):
        """Add a document to the vector DB."""
        embedding = embed_text(text, self.dim)
        doc = {
            'text': text[:2000],
            'embedding': embedding,
            'metadata': metadata or {},
        }
        self.documents.append(doc)

    def add_chunks(self, text: str, metadata: dict = None, chunk_size: int = None):
        """Split text into chunks and add all."""
        from rag.embeddings import embed_chunks
        chunk_size = chunk_size or RAG['chunk_size']
        overlap = RAG['chunk_overlap']
        chunks = embed_chunks(text, chunk_size, overlap, self.dim)

        for chunk in chunks:
            doc = {
                'text': chunk['text'][:2000],
                'embedding': chunk['embedding'],
                'metadata': {**(metadata or {}), 'start': chunk['start'], 'end': chunk['end']},
            }
            self.documents.append(doc)

    def search(self, query: str, top_k: int = None) -> list:
        """Search for similar documents."""
        top_k = top_k or RAG['top_k']
        query_emb = embed_text(query, self.dim)

        results = []
        for doc in self.documents:
            sim = cosine_similarity(query_emb, doc['embedding'])
            if sim >= RAG['similarity_threshold']:
                results.append({
                    'text': doc['text'],
                    'score': sim,
                    'metadata': doc.get('metadata', {}),
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def count(self) -> int:
        return len(self.documents)

    def clear(self):
        self.documents = []
        self._save()
