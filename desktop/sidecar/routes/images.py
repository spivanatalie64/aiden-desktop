"""Image generation route."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from common.image_gen import ImageGenerator
from settings import load_settings

router = APIRouter(prefix="/images", tags=["images"])


class ImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    style: str = "vivid"
    n: int = 1


class ImageResponse(BaseModel):
    images: list[str]


@router.post("/generate", response_model=ImageResponse)
async def generate_images(req: ImageRequest):
    settings = load_settings()
    proxy = settings.get("proxy_url", "https://aiden.acreetionos.org/api/chat")
    gen = ImageGenerator(proxy)
    try:
        urls = await gen.generate(
            prompt=req.prompt,
            size=req.size,
            style=req.style,
            n=req.n,
        )
        return ImageResponse(images=urls)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
