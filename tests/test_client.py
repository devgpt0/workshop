from types import SimpleNamespace

from workshop_cli.client import build_api_error, build_headers, extract_text


def test_build_headers_includes_optional_fields() -> None:
    headers = build_headers("key", "https://site", "My App")

    assert headers["Authorization"] == "Bearer key"
    assert headers["HTTP-Referer"] == "https://site"
    assert headers["X-OpenRouter-Title"] == "My App"


def test_extract_text_returns_string_content() -> None:
    payload = {"choices": [{"message": {"content": "hello"}}]}

    assert extract_text(payload) == "hello"


def test_extract_text_joins_text_parts_from_array_content() -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": [
                        {"type": "text", "text": "first"},
                        {"type": "text", "text": "second"},
                        {"type": "image", "url": "ignored"},
                    ]
                }
            }
        ]
    }

    assert extract_text(payload) == "first\nsecond"


def test_build_api_error_handles_json_error_payload() -> None:
    response = SimpleNamespace(
        status_code=401,
        json=lambda: {"error": {"message": "bad token", "code": "invalid_api_key"}},
    )

    assert build_api_error(response) == "HTTP 401 (invalid_api_key): bad token"


def test_build_api_error_handles_non_json_response() -> None:
    def _raise_value_error() -> dict:
        raise ValueError("not json")

    response = SimpleNamespace(
        status_code=500, text=" server failed ", json=_raise_value_error
    )

    assert build_api_error(response) == "HTTP 500: server failed"
