import pytest

from agentic_chat.app import entrypoint


def test_main_web_mode_calls_web(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entrypoint.sys, "argv", ["agentic-chat", "--web"])

    called = {"web": False}

    def fake_web_main() -> int:
        called["web"] = True
        return 0

    def fail_terminal(_args: list[str]) -> int:
        raise AssertionError("terminal app should not run in web mode")

    monkeypatch.setattr(entrypoint.web, "main", fake_web_main)
    monkeypatch.setattr(entrypoint.terminal, "main", fail_terminal)

    assert entrypoint.main() == 0
    assert called["web"] is True


def test_main_terminal_mode_forwards_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entrypoint.sys, "argv", ["agentic-chat", "hello", "world"])

    calls: dict[str, list[str]] = {}

    def fake_terminal_main(args: list[str] | None = None) -> int:
        calls["args"] = args or []
        return 0

    monkeypatch.setattr(entrypoint.terminal, "main", fake_terminal_main)

    assert entrypoint.main() == 0
    assert calls["args"] == ["hello", "world"]


def test_main_rejects_prompt_with_web_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(entrypoint.sys, "argv", ["agentic-chat", "--web", "news"])

    with pytest.raises(SystemExit) as exc:
        entrypoint.main()

    assert exc.value.code == 2
