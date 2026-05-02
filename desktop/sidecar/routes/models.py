"""Models route – list available models from the proxy."""
from fastapi import APIRouter

from common.llm_client import AsyncOpenRouterClient
from settings import load_settings

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def list_models():
    settings = load_settings()
    proxy = settings.get("proxy_url", "https://aiden.acreetionos.org/api/chat")
    client = AsyncOpenRouterClient(proxy)
    try:
        models = await client.models()
        return {"models": models}
    finally:
        await client.close()
