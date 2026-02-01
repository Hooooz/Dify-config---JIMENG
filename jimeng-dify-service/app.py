import os
import sys
import logging
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field


logger = logging.getLogger("jimeng-dify-service")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


service_root = Path(__file__).parent.resolve()
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))

try:
    from jimeng.images import generate_images as jimeng_generate_images
except Exception as e:
    jimeng_generate_images = None
    jimeng_import_error = f"{type(e).__name__}: {e}"
else:
    jimeng_import_error = None


def _get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _get_cors_origins() -> List[str]:
    raw = os.getenv("ALLOW_ORIGINS", "*").strip()
    if not raw or raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]

def _cors_allow_credentials(origins: List[str]) -> bool:
    return origins != ["*"]


def _public_base_url() -> Optional[str]:
    value = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    return value or None


def _to_public_url(path: str) -> str:
    base = _public_base_url()
    if not base:
        return path
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


def _is_truthy_env(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


def _proxy_allow_hosts() -> List[str]:
    raw = os.getenv("PROXY_ALLOW_HOSTS", "").strip()
    if not raw:
        return []
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


class GenerateRequest(BaseModel):

    prompt: str = Field(..., min_length=1)
    width: int = Field(1024, ge=256, le=2048)
    height: int = Field(1024, ge=256, le=2048)
    sample_strength: float = Field(0.5, ge=0.0, le=1.0)
    negative_prompt: str = ""
    model: str = "jimeng-2.1"
    return_type: str = "base64"


class GenerateResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    message: str = ""


app = FastAPI(title="Jimeng Dify Service", version="1.0.0")
cors_origins = _get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=_cors_allow_credentials(cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "jimeng_loaded": jimeng_generate_images is not None,
        "jimeng_import_error": jimeng_import_error,
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    if jimeng_generate_images is None:
        raise HTTPException(status_code=500, detail=f"jimeng module not loaded: {jimeng_import_error}")

    try:
        token = _get_required_env("JIMENG_API_TOKEN")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        urls = jimeng_generate_images(
            model=req.model,
            prompt=req.prompt,
            width=req.width,
            height=req.height,
            sample_strength=req.sample_strength,
            negative_prompt=req.negative_prompt,
            refresh_token=token,
        )
    except Exception as e:
        logger.error(f"Error generating images: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")

    if not urls:
        return GenerateResponse(success=False, message="jimeng returned empty image list")

    first_url = urls[0]
    if req.return_type == "url":
        return GenerateResponse(success=True, image_url=first_url, message="ok")

    if req.return_type == "proxy":
        proxied_path = f"/image?url={requests.utils.quote(first_url, safe='')}"
        return GenerateResponse(success=True, image_url=_to_public_url(proxied_path), message="ok")

    try:
        resp = requests.get(first_url, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"download failed: {type(e).__name__}: {e}")

    import base64

    b64 = base64.b64encode(resp.content).decode("utf-8")
    return GenerateResponse(success=True, image_base64=b64, message="ok")


@app.get("/image")
def image(url: str):
    if not _is_truthy_env("ENABLE_IMAGE_PROXY"):
        raise HTTPException(status_code=404, detail="image proxy disabled")
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="invalid url")

    allow_hosts = _proxy_allow_hosts()
    if allow_hosts:
        host = parsed.netloc.split("@")[-1].split(":")[0].lower()
        if not any(host == h or host.endswith(f".{h}") for h in allow_hosts):
            raise HTTPException(status_code=403, detail="host not allowed")

    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")

    content_type = resp.headers.get("Content-Type") or "application/octet-stream"
    return Response(content=resp.content, media_type=content_type)


def _main():
    import uvicorn

    port_str = os.getenv("PORT", "8080")
    try:
        port = int(port_str)
    except ValueError:
        port = 8080
    
    print(f"Starting server on 0.0.0.0:{port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    _main()
