import requests

from agentic_chat.ui.terminal.chat import (
    handle_command,
    normalize_mode,
    run_single_prompt,
)
from agentic_chat.core.modes import SessionState


class StubClient:
    def __init__(self, reply: str = "ok", error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[dict[str, object]] = []

    def send_chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        require_exa_tool: bool = False,
    ) -> str:
        self.calls.append(
            {
                "model": model,
                "messages": messages,
                "require_exa_tool": require_exa_tool,
            }
        )
        if self.error is not None:
            raise self.error
        return self.reply


def _state() -> SessionState:
    return SessionState(
        current_mode="chat",
        current_model="openrouter/free",
        available_models=["openrouter/free"],
    )


def test_normalize_mode_accepts_alias_and_index() -> None:
    assert normalize_mode("think") == "thinking"
    assert normalize_mode("2") == "plan"
    assert normalize_mode("9") is None
    assert normalize_mode("browser") is None


def test_run_single_prompt_success_prints_reply(capsys) -> None:
    client = StubClient(reply="Hi")
    code = run_single_prompt("Hello", client, _state())

    captured = capsys.readouterr()
    assert code == 0
    assert "Hi" in captured.out
    assert client.calls[0]["require_exa_tool"] is False


def test_run_single_prompt_handles_request_error(capsys) -> None:
    err = requests.RequestException("network down")

    code = run_single_prompt("Hello", StubClient(error=err), _state())

    captured = capsys.readouterr()
    assert code == 1
    assert "network down" in captured.out


def test_handle_command_mode_switch_clears_messages() -> None:
    state = _state()
    messages = [{"role": "user", "content": "hi"}]

    handled = handle_command("/mode plan", messages, state)

    assert handled is True
    assert state.current_mode == "plan"
    assert messages == []


def test_handle_command_models_add_and_use() -> None:
    state = _state()
    messages = [{"role": "user", "content": "hi"}]

    assert (
        handle_command("/models add openai/gpt-oss-20b:free", messages, state) is True
    )
    assert "openai/gpt-oss-20b:free" in state.available_models

    messages = [{"role": "user", "content": "again"}]
    assert (
        handle_command("/models use openai/gpt-oss-20b:free", messages, state) is True
    )
    assert state.current_model == "openai/gpt-oss-20b:free"
    assert messages == []


def test_handle_command_system_reset_clears_messages() -> None:
    state = _state()
    state.set_system_prompt("custom")
    messages = [{"role": "user", "content": "hi"}]

    handled = handle_command("/system reset", messages, state)

    assert handled is True
    assert messages == []
    assert "custom" not in state.system_prompt
