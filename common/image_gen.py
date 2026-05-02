"""Image generation via proxy.

The proxy is expected to support an /images/generations endpoint
compatible with the OpenAI Images API specification.
"""
import json
from typing import Optional

import httpx


class ImageGenerator:
    def __init__(self, proxy_url: str = "https://aiden.acreetionos.org/api/chat"):
        self.proxy_url = proxy_url.rstrip("/")

    async def generate(self, prompt: str, size: str = "1024x1024",
                       style: str = "vivid",
                       n: int = 1) -> list[str]:
        images_url = f"{self.proxy_url}/images/generations"
        payload = {
            "prompt": prompt,
            "n": n,
            "size": size,
            "response_format": "b64_json",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(images_url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            urls = []
            for item in data.get("data", []):
                if "url" in item:
                    urls.append(item["url"])
                elif "b64_json" in item:
                    urls.append(f"data:image/png;base64,{item['b64_json']}")
            return urls
