from types import SimpleNamespace

import pytest
import requests
import ujson

from agentic_chat.externals.openrouter import (
    API_URL,
    OpenRouterClient,
    build_api_error,
    build_headers,
    extract_reasoning,
    extract_text,
)


def test_build_headers_includes_optional_fields() -> None:
    headers = build_headers("key", "https://site", "My App")

    assert headers["Authorization"] == "Bearer key"
    assert headers["HTTP-Referer"] == "https://site"
    assert headers["X-OpenRouter-Title"] == "My App"


def test_extract_text_returns_string_content() -> None:
    payload = {"choices": [{"message": {"content": "hello"}}]}

    assert extract_text(payload) == "hello"


def test_extract_text_returns_empty_string_when_content_missing() -> None:
    payload = {"choices": [{"message": {"content": None}}]}

    assert extract_text(payload) == ""


def test_extract_reasoning_prefers_reasoning_field() -> None:
    message = {"reasoning": "thinking text", "reasoning_details": [{"text": "alt"}]}

    assert extract_reasoning(message) == "thinking text"


def test_build_api_error_handles_json_error_payload() -> None:
    response = SimpleNamespace(
        status_code=401,
        json=lambda: {"error": {"message": "bad token", "code": "invalid_api_key"}},
    )

    assert build_api_error(response) == "HTTP 401 (invalid_api_key): bad token"


def test_send_chat_runs_date_tool_for_date_question(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_index = {"value": 0}

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload
            self.ok = True
            self.status_code = 200
            self.text = ""

        def json(self) -> dict:
            return self._payload

    def fake_post(url: str, **kwargs):
        assert url == API_URL
        idx = call_index["value"]
        call_index["value"] += 1

        payload = ujson.loads(kwargs["data"])
        if idx == 0:
            assert (
                payload.get("tool_choice", {}).get("function", {}).get("name")
                == "get_current_datetime"
            )
            return FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "tool_1",
                                        "type": "function",
                                        "function": {
                                            "name": "get_current_datetime",
                                            "arguments": "{}",
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            )

        assert payload["messages"][-1]["role"] == "tool"
        return FakeResponse({"choices": [{"message": {"content": "today is ..."}}]})

    monkeypatch.setattr(requests, "post", fake_post)

    client = OpenRouterClient(api_key="k", timeout=10)
    reply = client.send_chat(
        model="openrouter/free",
        messages=[{"role": "user", "content": "what is today's date"}],
    )

    assert reply == "today is ..."


def test_send_chat_uses_exa_tool_for_news_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_index = {"value": 0}

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload
            self.ok = True
            self.status_code = 200
            self.text = ""

        def json(self) -> dict:
            return self._payload

    class FakeExa:
        def __init__(self, api_key: str | None = None) -> None:
            self.api_key = api_key

        def search(self, query: str, **kwargs):
            assert query == "today news"
            return {
                "results": [
                    {
                        "title": "Headline",
                        "url": "https://example.com",
                        "text": "content",
                    }
                ]
            }

    def fake_post(url: str, **kwargs):
        assert url == API_URL
        idx = call_index["value"]
        call_index["value"] += 1
        payload = ujson.loads(kwargs["data"])

        if idx == 0:
            assert (
                payload.get("tool_choice", {}).get("function", {}).get("name")
                == "exa_search"
            )
            return FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": "",
                                "tool_calls": [
                                    {
                                        "id": "tool_1",
                                        "type": "function",
                                        "function": {
                                            "name": "exa_search",
                                            "arguments": '{"query": "today news"}',
                                        },
                                    }
                                ],
                            }
                        }
                    ]
                }
            )

        return FakeResponse({"choices": [{"message": {"content": "news summary"}}]})

    monkeypatch.setattr("agentic_chat.externals.openrouter.Exa", FakeExa)
    monkeypatch.setattr(requests, "post", fake_post)

    client = OpenRouterClient(api_key="k", timeout=10, exa_api_key="exa")
    reply = client.send_chat(
        model="openrouter/free",
        messages=[{"role": "user", "content": "today news"}],
    )

    assert reply == "news summary"


def test_send_chat_retries_when_model_returns_only_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call_index = {"value": 0}

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload
            self.ok = True
            self.status_code = 200
            self.text = ""

        def json(self) -> dict:
            return self._payload

    def fake_post(url: str, **kwargs):
        assert url == API_URL
        idx = call_index["value"]
        call_index["value"] += 1
        payload = ujson.loads(kwargs["data"])

        if idx == 0:
            return FakeResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "reasoning": "Need to answer first.",
                            }
                        }
                    ]
                }
            )

        assert payload["messages"][-1]["role"] == "user"
        assert "Provide only the final answer" in payload["messages"][-1]["content"]
        return FakeResponse({"choices": [{"message": {"content": "It is Thursday."}}]})

    monkeypatch.setattr(requests, "post", fake_post)

    events: list[dict[str, object]] = []
    client = OpenRouterClient(api_key="k", timeout=10)
    reply = client.send_chat(
        model="openrouter/free",
        messages=[{"role": "user", "content": "What day is today?"}],
        on_event=events.append,
    )

    assert reply == "It is Thursday."
    assert any(event.get("type") == "thinking" for event in events)
