from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from agentic_chat.rag.embeddings import OpenRouterEmbeddingsClient


RAG_SYSTEM_PREFIX = (
    "Use the following retrieved knowledge base context to answer the user. "
    "If the answer is not in the context, say you do not know based on the current knowledge base. "
    "Do not invent facts outside this context."
)
 
ALLOWED_RAG_SUFFIXES = {".md", ".txt", ".json", ".csv", ".rst"}


@dataclass(frozen=True)
class RAGContext:
    text: str
    hits: int
    sources: tuple[str, ...]


@dataclass(frozen=True)
class RAGStats:
    files_indexed: int
    chunks_indexed: int


class RAGPipeline:
    def __init__(
        self,
        embeddings_client: OpenRouterEmbeddingsClient,
        data_dir: str,
        top_k: int = 4,
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> None:
        self.embeddings_client = embeddings_client
        self.data_dir = Path(data_dir)
        self.top_k = top_k
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = "rag_documents"
        self.client = QdrantClient(location=":memory:")
        self._indexed = False
        self._stats = RAGStats(files_indexed=0, chunks_indexed=0)

    @property
    def stats(self) -> RAGStats:
        return self._stats

    @property
    def indexed(self) -> bool:
        return self._indexed

    def _should_index_file(self, path: Path) -> bool:
        if path.suffix.lower() not in ALLOWED_RAG_SUFFIXES:
            return False

        # Skip helper docs in the knowledge folder.
        if path.name.lower() == "readme.md":
            return False

        # If a dedicated chunk folder exists for this file, index chunks only.
        chunks_dir = path.with_name(f"{path.stem}_chunks")
        if chunks_dir.is_dir():
            return False

        return True

    def index_data(self) -> RAGStats:
        if not self.data_dir.exists():
            self._indexed = False
            self._stats = RAGStats(files_indexed=0, chunks_indexed=0)
            return self._stats

        chunks: list[dict[str, str | int]] = []
        indexed_files = 0

        for path in sorted(self.data_dir.rglob("*")):
            if not path.is_file() or not self._should_index_file(path):
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            split_chunks = self._chunk_text(content)
            if not split_chunks:
                continue

            indexed_files += 1
            source = str(path)
            for chunk_index, text in enumerate(split_chunks):
                chunks.append(
                    {
                        "id": str(uuid5(NAMESPACE_URL, f"{source}:{chunk_index}")),
                        "source": source,
                        "chunk_index": chunk_index,
                        "text": text,
                    }
                )

        if not chunks:
            self._indexed = False
            self._stats = RAGStats(files_indexed=indexed_files, chunks_indexed=0)
            return self._stats

        vectors = self.embeddings_client.embed_many(
            [str(chunk["text"]) for chunk in chunks]
        )

        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )

        points = [
            PointStruct(
                id=str(chunk["id"]),
                vector=vector,
                payload={
                    "source": str(chunk["source"]),
                    "chunk_index": int(chunk["chunk_index"]),
                    "text": str(chunk["text"]),
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

        self._indexed = True
        self._stats = RAGStats(files_indexed=indexed_files, chunks_indexed=len(points))
        return self._stats

    def _search_points(self, query_vector: list[float]) -> list[Any]:
        if hasattr(self.client, "search"):
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=self.top_k,
                with_payload=True,
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=self.top_k,
            with_payload=True,
        )
        points = getattr(response, "points", None)
        if isinstance(points, list):
            return points
        return []

    def build_context(self, query: str) -> RAGContext | None:
        if not query.strip():
            return None

        if not self._indexed:
            try:
                self.index_data()
            except RuntimeError:
                return None

        if not self._indexed:
            return None

        query_vector = self.embeddings_client.embed_one(query)
        results = self._search_points(query_vector)
        if not results:
            return None

        snippets: list[str] = []
        sources: list[str] = []

        for rank, item in enumerate(results, start=1):
            payload = item.payload or {}
            source = str(payload.get("source") or "unknown")
            chunk_index = int(payload.get("chunk_index") or 0)
            text = str(payload.get("text") or "").strip()
            if not text:
                continue
            snippets.append(f"[{rank}] Source: {source} (chunk {chunk_index})\\n{text}")
            sources.append(source)

        if not snippets:
            return None

        return RAGContext(
            text="\\n\\n".join(snippets),
            hits=len(snippets),
            sources=tuple(sorted(set(sources))),
        )

    def _chunk_text(self, text: str) -> list[str]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []

        if len(cleaned) <= self.chunk_size:
            return [cleaned]

        chunks: list[str] = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        start = 0
        while start < len(cleaned):
            end = min(len(cleaned), start + self.chunk_size)
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(cleaned):
                break
            start += step
        return chunks


def build_rag_message(context: RAGContext) -> dict[str, str]:
    return {
        "role": "system",
        "content": f"{RAG_SYSTEM_PREFIX}\\n\\nRAG CONTEXT:\\n{context.text}",
    }
