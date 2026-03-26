import argparse
import sys

from agentic_chat.app import terminal, web


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-chat",
        description="Run Agentic Chat in terminal or web mode.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--terminal",
        action="store_true",
        help="Run the terminal UI (default mode).",
    )
    mode_group.add_argument(
        "--web",
        action="store_true",
        help="Run the Streamlit web UI.",
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="Optional terminal prompt. Leave empty to start interactive terminal mode.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:])

    if args.web:
        if args.prompt:
            parser.error("Prompt arguments are not supported with --web.")
        return web.main()

    forwarded_args = list(args.prompt)
    return terminal.main(forwarded_args)
