import pytest

from agentic_chat.app import terminal
from agentic_chat.core.config import Settings


def _settings() -> Settings:
    return Settings(
        api_key="openrouter-key",
        model="openrouter/free",
        site_url=None,
        site_name=None,
        timeout=30.0,
        no_effect=False,
        available_models=("openrouter/free",),
        exa_api_key=None,
        exa_num_results=5,
    )


def test_main_terminal_prompt_uses_single_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(terminal, "load_settings", _settings)

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    calls: dict[str, str] = {}

    def fake_run_single_prompt(prompt: str, client, state, rag_pipeline=None) -> int:
        calls["prompt"] = prompt
        calls["model"] = state.current_model
        return 0

    monkeypatch.setattr(terminal, "OpenRouterClient", DummyClient)
    monkeypatch.setattr(terminal, "run_single_prompt", fake_run_single_prompt)

    assert terminal.main(["hello", "there"]) == 0
    assert calls["prompt"] == "hello there"
    assert calls["model"] == "openrouter/free"


def test_main_interactive_mode_when_no_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(terminal, "load_settings", _settings)

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    called = {"interactive": False}

    def fake_run_interactive_chat(*, client, state, no_effect: bool, rag_pipeline=None) -> int:
        called["interactive"] = True
        return 0

    monkeypatch.setattr(terminal, "OpenRouterClient", DummyClient)
    monkeypatch.setattr(terminal, "run_interactive_chat", fake_run_interactive_chat)

    assert terminal.main([]) == 0
    assert called["interactive"] is True
