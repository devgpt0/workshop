from typing import Any

import requests
import ujson


EMBEDDINGS_API_URL = "https://openrouter.ai/api/v1/embeddings"


class OpenRouterEmbeddingsClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float,
        site_url: str | None = None,
        site_name: str | None = None,
    ) -> None:
        self.model = model
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if site_url:
            self.headers["HTTP-Referer"] = site_url
        if site_name:
            self.headers["X-OpenRouter-Title"] = site_name

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        payload: dict[str, Any] = {"model": self.model, "input": texts}
        response = requests.post(
            EMBEDDINGS_API_URL,
            headers=self.headers,
            data=ujson.dumps(payload),
            timeout=self.timeout,
        )
        if not response.ok:
            raise RuntimeError(
                f"Failed to create embeddings: HTTP {response.status_code} {response.text.strip()}"
            )

        body = response.json()
        data = body.get("data")
        if not isinstance(data, list) or not data:
            raise RuntimeError("Embedding response did not contain vectors.")

        vectors: list[list[float]] = []     
        for item in data:
            if not isinstance(item, dict):
                continue
            vector = item.get("embedding")
            if isinstance(vector, list) and vector:
                vectors.append([float(value) for value in vector])

        if len(vectors) != len(texts):
            raise RuntimeError(
                "Embedding response length did not match input length."
            )

        return vectors

    def embed_one(self, text: str) -> list[float]:
        return self.embed_many([text])[0]
