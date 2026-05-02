"""Async streaming client for OpenRouter proxy.

Extends the sync OpenRouterClient with async SSE streaming.
"""
import json
import asyncio
from typing import AsyncIterator, Optional

import httpx


class AsyncOpenRouterClient:
    def __init__(self, proxy_url: str = "https://aiden.acreetionos.org/api/chat",
                 timeout: int = 60):
        self.proxy_url = proxy_url
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def close(self):
        await self._client.aclose()

    async def send_chat(self, messages: list, model: Optional[str] = None) -> dict:
        payload = {"messages": messages}
        if model:
            payload["model"] = model
        resp = await self._client.post(self.proxy_url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def stream_chat(self, messages: list,
                          model: Optional[str] = None) -> AsyncIterator[str]:
        payload = {"messages": messages, "stream": True}
        if model:
            payload["model"] = model
        async with self._client.stream("POST", self.proxy_url, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def healthy(self) -> bool:
        try:
            resp = await self._client.get(self.proxy_url, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    async def models(self) -> list[str]:
        candidates = [
            self.proxy_url.rstrip("/") + "/models",
            self.proxy_url.rstrip("/") + "/available-models",
            self.proxy_url,
        ]
        for url in candidates:
            try:
                resp = await self._client.get(url, timeout=5)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                if isinstance(data, dict):
                    if "models" in data and isinstance(data["models"], list):
                        return [
                            m if isinstance(m, str) else m.get("id")
                            for m in data["models"]
                        ]
                    if "id" in data:
                        return [data["id"]]
                if isinstance(data, list):
                    return [
                        m if isinstance(m, str) else m.get("id")
                        for m in data
                    ]
            except Exception:
                continue
        return []
