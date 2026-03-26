import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_MODEL = "openrouter/free"
DEFAULT_EXA_RESULTS = 5


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
    )
