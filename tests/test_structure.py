from pathlib import Path

from agentic_chat.app.entrypoint import main as app_main
from agentic_chat.externals.openrouter import OpenRouterClient
from agentic_chat.core.config import Settings
from agentic_chat.core.modes import SessionState


ROOT = Path(__file__).resolve().parents[1]
SRC_PACKAGE = ROOT / "src" / "agentic_chat"


def test_new_structure_imports_are_available() -> None:
    assert callable(app_main)
    assert OpenRouterClient is not None
    assert Settings is not None
    assert SessionState is not None


def test_legacy_top_level_modules_are_removed() -> None:
    legacy_files = ["chat.py", "cli.py", "client.py", "config.py", "modes.py", "ui.py"]
    for legacy_file in legacy_files:
        assert not (SRC_PACKAGE / legacy_file).exists()


def test_expected_subfolders_exist() -> None:
    expected_dirs = ["app", "externals", "core", "tools", "ui"]
    for dirname in expected_dirs:
        assert (SRC_PACKAGE / dirname).is_dir()


def test_app_layer_has_separate_entrypoints() -> None:
    expected_files = ["entrypoint.py", "terminal.py", "web.py"]
    for filename in expected_files:
        assert (SRC_PACKAGE / "app" / filename).is_file()
