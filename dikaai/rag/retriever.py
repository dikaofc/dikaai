"""DikaAI Retriever - Searches knowledge base and provides context to LLM."""

import os
from pathlib import Path
from rag.vector_db import VectorDB
from rag.embeddings import embed_text
from core.config import RAG, DATA_DIR


class Retriever:
    """Retrieves relevant knowledge for coding tasks."""

    def __init__(self):
        self.db = VectorDB()
        self.indexed = False

    def index_directory(self, path: str, extensions: list = None):
        """Index all code files in a directory."""
        extensions = extensions or ['.py', '.js', '.ts', '.go', '.rs', '.java',
                                    '.kt', '.sh', '.c', '.cpp', '.md', '.txt']

        p = Path(path)
        if not p.exists():
            return

        count = 0
        for ext in extensions:
            for file in p.rglob(f'*{ext}'):
                # Skip hidden dirs, node_modules, etc
                parts = file.parts
                if any(d.startswith('.') or d in ('__pycache__', 'node_modules', 'venv', 'build')
                       for d in parts):
                    continue

                try:
                    content = file.read_text(encoding='utf-8', errors='replace')
                    if len(content) > 50:  # Skip tiny files
                        self.db.add_chunks(
                            content,
                            metadata={
                                'path': str(file),
                                'type': 'code',
                                'extension': ext,
                                'name': file.name,
                            }
                        )
                        count += 1
                except Exception:
                    pass

        self.indexed = True
        return count

    def index_error(self, error: str, solution: str, language: str = ""):
        """Index an error-solution pair."""
        text = f"Error: {error}\nSolution: {solution}"
        self.db.add(text, metadata={
            'type': 'error_solution',
            'language': language,
            'error': error[:200],
            'solution': solution[:200],
        })

    def index_documentation(self, text: str, source: str = ""):
        """Index documentation text."""
        self.db.add_chunks(text, metadata={
            'type': 'documentation',
            'source': source,
        })

    def retrieve(self, query: str, context_type: str = None) -> str:
        """Retrieve relevant context for a query."""
        results = self.db.search(query, top_k=RAG['top_k'])

        if context_type:
            results = [r for r in results if r['metadata'].get('type') == context_type]

        if not results:
            return ""

        lines = ["Relevant knowledge:"]
        for r in results[:3]:
            meta = r['metadata']
            score = r['score']

            if meta.get('type') == 'code':
                lines.append(f"  [{meta.get('name', 'code')}] (score: {score:.2f})")
                lines.append(f"  {r['text'][:200]}...")
            elif meta.get('type') == 'error_solution':
                lines.append(f"  [Error fix] (score: {score:.2f})")
                lines.append(f"  Error: {meta.get('error', '')[:100]}")
                lines.append(f"  Fix: {meta.get('solution', '')[:100]}")
            elif meta.get('type') == 'documentation':
                lines.append(f"  [Docs: {meta.get('source', '')}] (score: {score:.2f})")
                lines.append(f"  {r['text'][:200]}...")
            lines.append("")

        return '\n'.join(lines)

    def get_stats(self) -> dict:
        return {
            'documents': self.db.count(),
            'indexed': self.indexed,
        }
