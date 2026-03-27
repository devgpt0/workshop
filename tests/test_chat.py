import requests

from agentic_chat.core.modes import SessionState
from agentic_chat.rag.pipeline import RAGContext, RAGStats
from agentic_chat.ui.terminal.chat import (
    _build_messages_with_rag,
    handle_command,
    normalize_mode,
    run_single_prompt,
)


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


class FakeRAGPipeline:
    def __init__(self, context: RAGContext | None = None) -> None:
        self._context = context
        self.stats = RAGStats(files_indexed=1, chunks_indexed=2)
        self.indexed = True

    def build_context(self, query: str) -> RAGContext | None:
        return self._context

    def index_data(self) -> RAGStats:
        return self.stats


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


def test_build_messages_with_rag_injects_context() -> None:
    messages = _build_messages_with_rag(
        system_prompt="base system",
        conversation=[{"role": "user", "content": "What is policy?"}],
        rag_pipeline=FakeRAGPipeline(
            context=RAGContext(
                text="[1] Source: rag/data/policy.md (chunk 0)\\nPolicy text",
                hits=1,
                sources=("rag/data/policy.md",),
            )
        ),
    )

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "system"
    assert "RAG CONTEXT" in messages[1]["content"]


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


def test_handle_command_rag_toggle_updates_runtime_state() -> None:
    state = _state()
    messages: list[dict[str, str]] = []
    rag_runtime = {"enabled": True}
    rag_pipeline = FakeRAGPipeline()

    assert handle_command("/rag off", messages, state, rag_pipeline, rag_runtime) is True
    assert rag_runtime["enabled"] is False

    assert handle_command("/rag on", messages, state, rag_pipeline, rag_runtime) is True
    assert rag_runtime["enabled"] is True
