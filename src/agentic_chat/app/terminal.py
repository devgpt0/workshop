import argparse

from agentic_chat.externals.openrouter import OpenRouterClient
from agentic_chat.core.config import load_settings
from agentic_chat.core.modes import SessionState
from agentic_chat.rag.bootstrap import build_rag_pipeline
from agentic_chat.ui.terminal.chat import run_interactive_chat, run_single_prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-chat",
        description="Run Agentic Chat terminal UI.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Optional terminal prompt. Leave empty to start interactive terminal mode.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
    rag_pipeline = build_rag_pipeline(settings)

    state = SessionState(
        current_mode="chat",
        current_model=settings.model,
        available_models=list(settings.available_models),
    )

    if args.prompt:
        return run_single_prompt(" ".join(args.prompt), client, state, rag_pipeline)

    return run_interactive_chat(
        client=client,
        state=state,
        no_effect=settings.no_effect,
        rag_pipeline=rag_pipeline,
    )
