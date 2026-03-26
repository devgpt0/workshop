from typing import Any

from exa_py import Exa

TOOL_NAME = "exa_search"


def build_schema() -> dict:
    return {
        "type": "function",
        "function": {
            "name": TOOL_NAME,
            "description": "Search the web for recent or niche facts and return snippets with source URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The web search query to run.",
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Optional number of results to return.",
                        "minimum": 1,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }


def _result_field(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def run(exa_client: Exa | None, query: str, num_results: int) -> dict[str, Any]:
    if not exa_client:
        return {"error": "EXA_API_KEY is not configured."}

    try:
        result = exa_client.search(
            query,
            type="auto",
            num_results=num_results,
            contents={"highlights": {"max_characters": 4000}},
        )
    except Exception as exc:
        return {"error": f"Exa request failed: {exc}"}

    raw_results = getattr(result, "results", None)
    if raw_results is None and isinstance(result, dict):
        raw_results = result.get("results")
    if not isinstance(raw_results, list):
        raw_results = []

    results: list[dict[str, str]] = []
    for item in raw_results:
        title = str(_result_field(item, "title") or "")
        url = str(_result_field(item, "url") or "")
        text = _result_field(item, "text")

        if not text:
            highlights = _result_field(item, "highlights")
            if isinstance(highlights, list):
                text = "\n".join(str(part) for part in highlights if part)

        results.append(
            {
                "title": title,
                "url": url,
                "text": str(text or "")[:1200],
            }
        )

    return {"query": query, "results": results}
