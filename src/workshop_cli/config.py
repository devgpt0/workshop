import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_MODEL = "openrouter/free"


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    site_url: str | None
    site_name: str | None
    timeout: float
    no_effect: bool
    available_models: tuple[str, ...]


def parse_models(raw_value: str | None, fallback: str) -> tuple[str, ...]:
    if not raw_value:
        return (fallback,)

    models = tuple(part.strip() for part in raw_value.split(",") if part.strip())
    return models or (fallback,)


def load_settings() -> Settings:
    load_dotenv()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set. Add it to your environment or .env file.")

    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    return Settings(
        api_key=api_key,
        model=model,
        site_url=os.getenv("OPENROUTER_SITE_URL"),
        site_name=os.getenv("OPENROUTER_SITE_NAME"),
        timeout=float(os.getenv("OPENROUTER_TIMEOUT", "30")),
        no_effect=os.getenv("WORKSHOP_NO_EFFECT") == "1",
        available_models=parse_models(os.getenv("OPENROUTER_MODELS"), model),
    )
