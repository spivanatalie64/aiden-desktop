"""Chat routes – send messages and stream responses."""
import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from common.llm_client import AsyncOpenRouterClient
from common.audit import emit
from settings import load_settings

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    messages: list
    model: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    reply: str
    model: str


@router.post("")
async def chat(req: ChatRequest):
    settings = load_settings()
    proxy = settings.get("proxy_url", "https://aiden.acreetionos.org/api/chat")
    client = AsyncOpenRouterClient(proxy)
    try:
        resp = await client.send_chat(req.messages, req.model)
        reply = (
            resp.get("reply")
            or resp.get("choices", [{}])[0]
            .get("message", {})
            .get("content")
            or str(resp)
        )
        model = resp.get("model", req.model or "unknown")
        return ChatResponse(reply=reply, model=model)
    finally:
        await client.close()


@router.post("/stream")
async def chat_stream(req: ChatRequest):
    if not req.stream:
        return await chat(req)

    settings = load_settings()
    proxy = settings.get("proxy_url", "https://aiden.acreetionos.org/api/chat")
    client = AsyncOpenRouterClient(proxy)

    async def event_generator():
        try:
            async for token in client.stream_chat(req.messages, req.model):
                yield {"event": "token", "data": json.dumps({"token": token})}
            yield {"event": "done", "data": "[DONE]"}
        finally:
            await client.close()

    return EventSourceResponse(event_generator())
