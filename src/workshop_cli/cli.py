import argparse

from workshop_cli.chat import run_interactive_chat, run_single_prompt
from workshop_cli.client import OpenRouterClient
from workshop_cli.config import load_settings
from workshop_cli.modes import SessionState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workshop",
        description="Chat with OpenRouter from the terminal.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Optional first prompt. Leave empty to start interactive chat mode.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        settings = load_settings()
    except ValueError as exc:
        parser.error(str(exc))

    client = OpenRouterClient(
        api_key=settings.api_key,
        timeout=settings.timeout,
        site_url=settings.site_url,
        site_name=settings.site_name,
        exa_api_key=settings.exa_api_key,
        exa_num_results=settings.exa_num_results,
    )
    state = SessionState(
        current_mode="chat",
        current_model=settings.model,
        available_models=list(settings.available_models),
    )

    if args.prompt:
        return run_single_prompt(" ".join(args.prompt), client, state)

    return run_interactive_chat(
        client=client,
        state=state,
        no_effect=settings.no_effect,
    )
