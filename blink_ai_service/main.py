"""Unified FastAPI Entry Point for Blink AI Service.

Runs ONE secure server on port 8000 hosting all 4 independent modules:
- IR       (/api/ir/...)
- Spelling (/api/spelling/...)
- TTS      (/api/tts/...)
- LLM      (/api/llm/...)

Run locally in VS Code:
    python -B main.py
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load .env cleanly even if python-dotenv is missing (keeps secret API keys out of source code)
def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        txt_path = Path(__file__).resolve().parent / ".env.txt"
        if txt_path.exists():
            env_path = txt_path
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False, encoding="utf-8-sig")
        return
    except ImportError:
        pass
    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


_load_local_env()

from modules.IR.ir_router import router as ir_router
from modules.Spelling.spelling_router import router as spelling_router
from modules.TTS.tts_router import router as tts_router, tts_service
from modules.LLM.llm_router import router as llm_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm offline TTS cache & log active voice config on server boot."""
    if tts_service.mode != "online":
        warm = tts_service.warmup_offline()
        print(
            f"[Blink AI] TTS ready | mode={tts_service.mode} | "
            f"elevenlabs={tts_service.is_elevenlabs_configured} | "
            f"cached_phrases={warm['warmed_phrases']}"
        )
    yield


app = FastAPI(
    title="Blink AI Service",
    description=(
        "Unified Modular AI/NLP Backend for Blink Communication "
        "(IR, Spelling Correction, Offline/Online Neural TTS, and LLM Smart Suggestions)."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

# Security: allow configured origins (default '*' for local teammate testing;
# restrict to teammate's exact domain/origin in production via ALLOWED_ORIGINS in .env)
raw_origins = os.getenv("ALLOWED_ORIGINS", "*").strip()
allowed_origins = (
    ["*"]
    if raw_origins == "*"
    else [o.strip() for o in raw_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Isolate unexpected failures without leaking internal tracebacks."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "An unexpected error occurred while processing the request.",
            "path": request.url.path,
        },
    )


# Register the 4 completely independent feature routers
app.include_router(ir_router)
app.include_router(spelling_router)
app.include_router(tts_router)
app.include_router(llm_router)


@app.get("/")
def root() -> dict:
    """Service overview, active modules, and unified API endpoints."""
    return {
        "service": "Blink AI Service",
        "version": "2.0.0",
        "status": "running",
        "active_modules": ["IR", "Spelling", "TTS", "LLM"],
        "docs_url": "/docs",
        "endpoints": {
            "health_all": "GET /health",
            "ir_suggest": "POST /api/ir/suggest",
            "spelling_correct_word": "POST /api/spelling/correct-word",
            "spelling_correct_sentence": "POST /api/spelling/correct-sentence",
            "tts_speak": "POST /api/tts/speak",
            "tts_speak_base64": "POST /api/tts/speak-base64",
            "llm_suggest": "POST /api/llm/suggest",
        },
    }


@app.get("/health")
def health_all() -> dict:
    """Combined health-check endpoints for all 4 modules."""
    return {
        "status": "healthy",
        "modules": {
            "IR": "/api/ir/health",
            "Spelling": "/api/spelling/health",
            "TTS": "/api/tts/health",
            "LLM": "/api/llm/health",
        },
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
