from agentic_chat.core.config import Settings
from agentic_chat.rag.embeddings import OpenRouterEmbeddingsClient
from agentic_chat.rag.pipeline import RAGPipeline


def build_rag_pipeline(settings: Settings) -> RAGPipeline | None:
    if not settings.rag_enabled:
        return None

    embeddings_client = OpenRouterEmbeddingsClient(
        api_key=settings.api_key,
        model=settings.embedding_model,
        timeout=settings.timeout,
        site_url=settings.site_url,
        site_name=settings.site_name,
    )
    return RAGPipeline(
        embeddings_client=embeddings_client,
        data_dir=settings.rag_data_dir,
        top_k=settings.rag_top_k,
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )
