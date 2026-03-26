import re
from typing import Any

from exa_py import Exa

from agentic_chat.tools import datetime_tool, exa_tool

DATE_TIME_PHRASES = (
    "what is today's date",
    "what is the date today",
    "today date",
    "todays date",
    "current date",
    "what is the time",
    "what time is it",
    "current time",
    "time now",
    "what day is it",
)

RELATIVE_DAY_WORDS = {"today", "tomorrow", "yesterday", "tonight"}
DATE_WORDS = {"date", "day", "weekday", "month", "year", "calendar"}
TIME_WORDS = {
    "time",
    "clock",
    "hour",
    "hours",
    "minute",
    "minutes",
    "second",
    "seconds",
    "timezone",
}

WEB_INTENT_PHRASES = (
    "search",
    "research",
    "look up",
    "lookup",
    "find",
    "check online",
    "browse",
    "web search",
)

WEB_FRESHNESS_WORDS = {
    "latest",
    "recent",
    "current",
    "breaking",
    "today",
    "today's",
    "todays",
    "new",
    "updates",
    "update",
}

WEB_TOPIC_WORDS = {
    "news",
    "headline",
    "headlines",
    "weather",
    "stock",
    "stocks",
    "price",
    "prices",
    "score",
    "scores",
    "results",
    "market",
    "crypto",
}


def build_tool_schemas(has_exa: bool) -> list[dict[str, Any]]:
    tools = [datetime_tool.build_schema()]
    if has_exa:
        tools.append(exa_tool.build_schema())
    return tools


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def _is_datetime_intent(normalized: str, tokens: set[str]) -> bool:
    if any(phrase in normalized for phrase in DATE_TIME_PHRASES):
        return True

    has_relative_day = any(word in tokens for word in RELATIVE_DAY_WORDS)
    has_date_words = any(word in tokens for word in DATE_WORDS)
    has_time_words = any(word in tokens for word in TIME_WORDS)

    if has_relative_day and (has_date_words or has_time_words):
        return True

    if "current" in tokens and ("date" in tokens or "time" in tokens):
        return True

    return False


def _is_web_intent(normalized: str, tokens: set[str]) -> bool:
    has_phrase = any(phrase in normalized for phrase in WEB_INTENT_PHRASES)
    has_topic = any(word in tokens for word in WEB_TOPIC_WORDS)
    has_freshness = any(word in tokens for word in WEB_FRESHNESS_WORDS)

    if has_phrase:
        return True

    if has_topic and has_freshness:
        return True

    # Keep explicit topic lookups web-backed even without freshness markers.
    if has_topic and any(
        word in tokens for word in {"search", "find", "lookup", "look"}
    ):
        return True

    return False


def default_tool_choice(last_user_message: str, has_exa: bool) -> dict[str, Any] | None:
    normalized = _normalize(last_user_message)
    if not normalized:
        return None

    tokens = _tokenize(normalized)

    if _is_datetime_intent(normalized, tokens):
        return {
            "type": "function",
            "function": {"name": datetime_tool.TOOL_NAME},
        }

    if has_exa and _is_web_intent(normalized, tokens):
        return {
            "type": "function",
            "function": {"name": exa_tool.TOOL_NAME},
        }

    return None


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    exa_client: Exa | None,
    exa_num_results: int,
) -> dict[str, Any]:
    if tool_name == datetime_tool.TOOL_NAME:
        return datetime_tool.run()

    if tool_name == exa_tool.TOOL_NAME:
        query = str(arguments.get("query") or "").strip()
        if not query:
            return {"error": "Tool argument 'query' is required."}

        num_results = arguments.get("num_results")
        if not isinstance(num_results, int) or num_results < 1:
            num_results = exa_num_results

        return exa_tool.run(exa_client=exa_client, query=query, num_results=num_results)

    return {"error": f"Unsupported tool requested: {tool_name}"}
