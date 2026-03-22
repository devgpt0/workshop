from typing import Any

import requests
import ujson


API_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_headers(api_key: str, site_url: str | None, site_name: str | None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if site_url:
        headers["HTTP-Referer"] = site_url
    if site_name:
        headers["X-OpenRouter-Title"] = site_name
    return headers


def extract_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ujson.dumps(payload, indent=2)

    message = choices[0].get("message") or {}
    content = message.get("content")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        if parts:
            return "\n".join(parts)

    return ujson.dumps(payload, indent=2)


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        timeout: float,
        site_url: str | None = None,
        site_name: str | None = None,
    ) -> None:
        self.timeout = timeout
        self.headers = build_headers(api_key, site_url, site_name)

    def send_chat(self, model: str, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": model,
            "messages": messages,
        }
        response = requests.post(
            API_URL,
            headers=self.headers,
            data=ujson.dumps(payload),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return extract_text(response.json())
