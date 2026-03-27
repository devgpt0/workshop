import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_MODEL = "openrouter/free"
DEFAULT_EXA_RESULTS = 5
DEFAULT_EMBEDDING_MODEL = "openai/text-embedding-3-small"
DEFAULT_RAG_TOP_K = 4
DEFAULT_RAG_CHUNK_SIZE = 800
DEFAULT_RAG_CHUNK_OVERLAP = 120


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    site_url: str | None
    site_name: str | None
    timeout: float
    no_effect: bool
    available_models: tuple[str, ...]
    exa_api_key: str | None
    exa_num_results: int
    rag_enabled: bool = True
    rag_data_dir: str = "rag/data"
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    rag_top_k: int = DEFAULT_RAG_TOP_K
    rag_chunk_size: int = DEFAULT_RAG_CHUNK_SIZE
    rag_chunk_overlap: int = DEFAULT_RAG_CHUNK_OVERLAP


def parse_models(raw_value: str | None, fallback: str) -> tuple[str, ...]:
    if not raw_value:
        return (fallback,)

    models = tuple(part.strip() for part in raw_value.split(",") if part.strip())
    return models or (fallback,)


def _parse_exa_num_results(raw_value: str | None) -> int:
    if not raw_value:
        return DEFAULT_EXA_RESULTS

    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise ValueError("EXA_NUM_RESULTS must be an integer.") from exc

    if parsed < 1:
        raise ValueError("EXA_NUM_RESULTS must be at least 1.")

    return parsed


def _parse_positive_int(raw_value: str | None, name: str, fallback: int) -> int:
    if not raw_value:
        return fallback

    try:
        parsed = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc

    if parsed < 1:
        raise ValueError(f"{name} must be at least 1.")

    return parsed


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Add it to your environment or .env file."
        )

    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    return Settings(
        api_key=api_key,
        model=model,
        site_url=os.getenv("OPENROUTER_SITE_URL"),
        site_name=os.getenv("OPENROUTER_SITE_NAME"),
        timeout=float(os.getenv("OPENROUTER_TIMEOUT", "30")),
        no_effect=os.getenv("WORKSHOP_NO_EFFECT") == "1",
        available_models=parse_models(os.getenv("OPENROUTER_MODELS"), model),
        exa_api_key=os.getenv("EXA_API_KEY"),
        exa_num_results=_parse_exa_num_results(os.getenv("EXA_NUM_RESULTS")),
        rag_enabled=os.getenv("RAG_ENABLED", "1") != "0",
        rag_data_dir=os.getenv("RAG_DATA_DIR", "rag/data"),
        embedding_model=os.getenv(
            "OPENROUTER_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
        ),
        rag_top_k=_parse_positive_int(
            os.getenv("RAG_TOP_K"), "RAG_TOP_K", DEFAULT_RAG_TOP_K
        ),
        rag_chunk_size=_parse_positive_int(
            os.getenv("RAG_CHUNK_SIZE"), "RAG_CHUNK_SIZE", DEFAULT_RAG_CHUNK_SIZE
        ),
        rag_chunk_overlap=_parse_positive_int(
            os.getenv("RAG_CHUNK_OVERLAP"),
            "RAG_CHUNK_OVERLAP",
            DEFAULT_RAG_CHUNK_OVERLAP,
        ),
    )
