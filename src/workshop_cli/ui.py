import os
import shutil
import sys
from importlib.metadata import PackageNotFoundError, version


APP_NAME = "Bootcoding"
BORDER_COLOR = "38;5;209"
ART_COLOR = "1;38;5;209"
MUTED_COLOR = "38;5;223"
BOOT_ART = [
    "  █▀▀█  ▄▀▀▄  ▄▀▀▄  ▄▀▀▀▄",
    "  █▀▀▄  █  █  █  █    █  ",
    "  █  █  █  █  █  █    █  ",
    "  ▀▀▀   ▀▀▀   ▀▀▀     ▀  ",
]
CODING_ART = [
    "  ▄▀▀▀  ▄▀▀▄  █▀▀▄  ▀█▀  █▄  █  ▄▀▀▀",
    "  █     █  █  █  █   █   █ ▀▄█  █ ▀█",
    "  █▄▄▄  █  █  █  █   █   █  ▀█  █▄▄█",
    "   ▀▀▀  ▀▀▀   ▀▀▀   ▀▀▀  ▀   ▀   ▀▀ ",
]
BOOTCODING_ART = BOOT_ART + [""] + CODING_ART


def supports_effects(no_effect: bool) -> bool:
    return sys.stdout.isatty() and not no_effect


def colorize(text: str, code: str, no_effect: bool) -> str:
    if not supports_effects(no_effect):
        return text
    return f"\033[{code}m{text}\033[0m"


def get_app_version() -> str:
    try:
        return version("workshop")
    except PackageNotFoundError:
        return "dev"


def truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def pad(text: str, width: int) -> str:
    return truncate(text, width).ljust(width)


def render_border(inner_width: int, no_effect: bool, title: str | None = None) -> str:
    if not title:
        return colorize("+" + "-" * inner_width + "+", BORDER_COLOR, no_effect)

    prefix = f"+- {title} "
    line = prefix + "-" * max(0, inner_width - len(prefix) + 1) + "+"
    return colorize(line, BORDER_COLOR, no_effect)


def render_row(left: str, right: str, left_width: int, right_width: int, no_effect: bool) -> str:
    left_text = pad(left, left_width)
    right_text = pad(right, right_width)
    if left.strip():
        left_text = colorize(left_text, ART_COLOR, no_effect)
    right_text = colorize(right_text, MUTED_COLOR, no_effect)
    return (
        f"{colorize('|', BORDER_COLOR, no_effect)} {left_text} "
        f"{colorize('|', BORDER_COLOR, no_effect)} {right_text} "
        f"{colorize('|', BORDER_COLOR, no_effect)}"
    )


def show_welcome_screen(model: str, mode: str, no_effect: bool) -> None:
    if not supports_effects(no_effect):
        print(APP_NAME)
        return

    term_width = shutil.get_terminal_size((120, 30)).columns
    inner_width = min(116, max(96, term_width - 4))
    left_width = min(52, max(len(line) for line in BOOTCODING_ART) + 2)
    right_width = inner_width - left_width - 3
    title = f"{APP_NAME} v{get_app_version()}"

    right_lines = [
        "GET STARTED",
        "System  guided setup",
        "Assistant  ready",
        "/help  show commands",
        "/mode  switch capability",
        "/models  change model",
        "/system  edit behavior",
        "",
        "SESSION",
        f"Mode   {mode}",
        f"Model  {model}",
    ]

    left_lines = ["Welcome back!", ""] + BOOTCODING_ART
    total_rows = max(len(left_lines), len(right_lines))
    left_lines.extend([""] * (total_rows - len(left_lines)))
    right_lines.extend([""] * (total_rows - len(right_lines)))

    print(render_border(inner_width, no_effect, title))
    for left, right in zip(left_lines, right_lines):
        print(render_row(left, right, left_width, right_width, no_effect))
    print(render_border(inner_width, no_effect))
    print()


def print_chat_help() -> None:
    print("Interactive mode")
    print("  Type your message and press Enter.")
    print("  /mode                         Select or switch mode")
    print("  /mode chat|plan|thinking      Switch mode directly")
    print("  /models                       Select or switch model")
    print("  /models use <model>           Switch model directly")
    print("  /models add <model>           Add a model to this session")
    print("  /system                       View and edit the system prompt")
    print("  /system <text>                Set the system prompt directly")
    print("  /system reset                 Reset the system prompt")
    print("  /clear                        Start a fresh conversation")
    print("  /exit                         Quit the chat")