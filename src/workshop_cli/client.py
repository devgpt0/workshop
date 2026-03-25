from typing import Any

import requests
import ujson
from exa_py import Exa

from workshop_cli.tools import build_tool_schemas, default_tool_choice, execute_tool


API_URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_TOOL_ROUNDS = 3


def build_headers(
    api_key: str, site_url: str | None, site_name: str | None
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if site_url:
        headers["HTTP-Referer"] = site_url
    if site_name:
        headers["X-OpenRouter-Title"] = site_name
    return headers


def parse_tool_arguments(raw_arguments: str | None) -> dict[str, Any]:
    if not raw_arguments:
        return {}

    try:
        parsed = ujson.loads(raw_arguments)
    except ValueError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


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


def build_api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"HTTP {response.status_code}: {response.text.strip()}"

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = error.get("message") or "Unknown API error"
        code = error.get("code") or response.status_code
        return f"HTTP {response.status_code} ({code}): {message}"

    return f"HTTP {response.status_code}: {payload}"


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        timeout: float,
        site_url: str | None = None,
        site_name: str | None = None,
        exa_api_key: str | None = None,
        exa_num_results: int = 5,
    ) -> None:
        self.timeout = timeout
        self.headers = build_headers(api_key, site_url, site_name)
        self.exa_api_key = exa_api_key
        self.exa_num_results = exa_num_results
        self._exa_client = Exa(api_key=exa_api_key) if exa_api_key else None

    def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            API_URL,
            headers=self.headers,
            data=ujson.dumps(payload),
            timeout=self.timeout,
        )
        if not response.ok:
            raise RuntimeError(build_api_error(response))
        return response.json()

    def send_chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        require_exa_tool: bool = False,
    ) -> str:
        if require_exa_tool and not self.exa_api_key:
            raise RuntimeError(
                "Exa tool requires EXA_API_KEY. Please set EXA_API_KEY in your .env file."
            )

        tools = build_tool_schemas(has_exa=bool(self.exa_api_key))
        conversation = list(messages)

        last_user_message = ""
        for item in reversed(conversation):
            if item.get("role") == "user":
                last_user_message = str(item.get("content") or "")
                break

        forced_tool = default_tool_choice(
            last_user_message=last_user_message,
            has_exa=bool(self.exa_api_key),
        )

        if require_exa_tool and not forced_tool:
            forced_tool = {
                "type": "function",
                "function": {"name": "exa_search"},
            }

        for round_index in range(MAX_TOOL_ROUNDS):
            payload: dict[str, Any] = {
                "model": model,
                "messages": conversation,
                "tools": tools,
            }
            if round_index == 0 and forced_tool:
                payload["tool_choice"] = forced_tool

            response_payload = self._post_chat_completion(payload)

            choices = response_payload.get("choices") or []
            if not choices:
                return extract_text(response_payload)

            message = choices[0].get("message") or {}
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                return extract_text(response_payload)

            conversation.append(
                {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )

            for tool_call in tool_calls:
                function = tool_call.get("function") or {}
                name = str(function.get("name") or "")
                arguments = parse_tool_arguments(function.get("arguments"))
                tool_call_id = tool_call.get("id")

                tool_output = execute_tool(
                    tool_name=name,
                    arguments=arguments,
                    exa_client=self._exa_client,
                    exa_num_results=self.exa_num_results,
                )

                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": ujson.dumps(tool_output),
                    }
                )

        return "Unable to complete tool-assisted response within tool-call limit."
