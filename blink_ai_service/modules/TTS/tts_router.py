"""FastAPI router for the Text-to-Speech (TTS) module."""

from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from modules.TTS.tts_service import TTSService

tts_service = TTSService()

router = APIRouter(prefix="/api/tts", tags=["TTS - Text to Speech"])

RANGE_HEADER_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


class AudioStreamResponse(Response):
    """Binary audio response so Swagger UI / OpenAPI treats WAV/MP3 as audio."""

    media_type = "audio/mpeg"


AUDIO_RESPONSES = {
    200: {
        "description": "Audio stream (MP3 in Egyptian online/cached mode, WAV in offline mode)",
        "content": {
            "audio/mpeg": {"schema": {"type": "string", "format": "binary"}},
            "audio/wav": {"schema": {"type": "string", "format": "binary"}},
        },
    }
}


class TTSRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=3000,
        description="Text to speak aloud.",
        examples=["انا عايز اشرب ميه"],
    )
    lang: Literal["auto", "ar", "en"] = Field(
        default="auto",
        description="Speech language ('auto', 'ar', or 'en').",
    )
    gender: Literal["male", "female"] = Field(
        default="male",
        description="Voice gender ('male' default Egyptian Shakir / Guy, or 'female').",
    )
    rate: str = Field(
        default="+0%",
        description="Speaking speed adjustment like '-15%', '+0%', '+15%'.",
        examples=["+0%"],
    )


class TTSBase64Response(BaseModel):
    text: str
    language: Literal["ar", "en"]
    voice: str
    rate: str
    mime_type: str
    bytes_count: int
    cached: bool
    audio_base64: str


def _build_audio_response(res: dict, range_header: str | None = None) -> Response:
    """Return full 200 audio or 206 Partial Content so Chrome/Edge <audio> always plays."""
    data: bytes = res["audio_bytes"]
    total = len(data)
    ext = "wav" if res["mime_type"] == "audio/wav" else "mp3"
    base_headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="blink_speech.{ext}"',
        "Cache-Control": "no-store",
        "X-TTS-Voice": res["voice"],
        "X-TTS-Language": res["language"],
        "X-TTS-Cached": str(res["cached"]).lower(),
    }

    if range_header:
        match = RANGE_HEADER_RE.match(range_header.strip())
        if match and total > 0:
            start_s, end_s = match.groups()
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else total - 1
            if start_s == "" and end_s:
                # Suffix range like bytes=-500
                start = max(0, total - int(end_s))
                end = total - 1
            end = min(end, total - 1)
            if 0 <= start <= end < total:
                chunk = data[start : end + 1]
                headers = {
                    **base_headers,
                    "Content-Range": f"bytes {start}-{end}/{total}",
                    "Content-Length": str(len(chunk)),
                }
                return Response(
                    content=chunk,
                    status_code=206,
                    media_type=res["mime_type"],
                    headers=headers,
                )

    headers = {**base_headers, "Content-Length": str(total)}
    return Response(
        content=data,
        status_code=200,
        media_type=res["mime_type"],
        headers=headers,
    )


@router.get("/health")
def tts_health() -> dict:
    """Return TTS module readiness, active mode, offline model status, and cache stats."""
    return {
        "module": "TTS",
        "status": "ready",
        "mode": tts_service.mode,
        "elevenlabs_configured": tts_service.is_elevenlabs_configured,
        "elevenlabs_voice_ar": tts_service._resolve_elevenlabs_voice("ar", "male")[1],
        "offline_models_ready": tts_service.offline_models_status(),
        "model": (
            "ElevenLabs Haytham (ar-EG) + Edge Shakir + Offline Cache/Piper"
            if tts_service.is_elevenlabs_configured
            else "Dual-Mode Egyptian ShakirNeural (Online/Cached) + Piper Male (Offline)"
        ),
        "cached_phrases": len(tts_service._cache),
        "voices_count": len(tts_service.list_voices()),
    }


@router.get("/voices")
def list_tts_voices() -> dict:
    """List supported offline Piper and online Edge neural voices."""
    return {"mode": tts_service.mode, "voices": tts_service.list_voices()}


@router.get("/player", response_class=HTMLResponse, include_in_schema=False)
def audio_test_player() -> str:
    """Lightweight built-in browser tester to verify TTS playback reliably."""
    return """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>Blink TTS Audio Test</title>
  <style>
    body { font-family: Tahoma, Arial, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; padding: 40px 16px; }
    .box { width: 100%; max-width: 560px; background: #1e293b; border-radius: 14px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
    h2 { margin-top: 0; color: #38bdf8; }
    input { width: 100%; box-sizing: border-box; padding: 12px; border-radius: 8px; border: 1px solid #475569; background: #0f172a; color: #fff; font-size: 16px; margin-bottom: 12px; }
    button { background: #2563eb; color: #fff; border: none; padding: 10px 16px; border-radius: 8px; font-size: 15px; cursor: pointer; margin: 4px 0 4px 6px; }
    button:hover { background: #1d4ed8; }
    .quick button { background: #334155; font-size: 13px; }
    .info { margin-top: 14px; font-size: 14px; color: #cbd5e1; }
    audio { width: 100%; margin-top: 14px; }
  </style>
</head>
<body>
  <div class="box">
    <h2>Blink TTS — تجربة الصوت المباشرة</h2>
    <input id="txt" type="text" value="انا عايز اشرب ميه" placeholder="اكتب أي جملة عربي أو إنجليزي..." />
    <div>
      <button onclick="playText()">نطق الصوت</button>
    </div>
    <div class="quick">
      <button onclick="quick('الترفيه')">الترفيه</button>
      <button onclick="quick('الاحتياجات')">الاحتياجات</button>
      <button onclick="quick('محتاج دكتور')">محتاج دكتور</button>
      <button onclick="quick('I need water please')">I need water please</button>
    </div>
    <audio id="player" controls></audio>
    <div class="info" id="status">اضغط "نطق الصوت" أو أي زرار فوق.</div>
  </div>
  <script>
    function quick(t) { document.getElementById('txt').value = t; playText(); }
    async function playText() {
      const text = document.getElementById('txt').value.trim();
      const status = document.getElementById('status');
      const player = document.getElementById('player');
      if (!text) return;
      status.textContent = 'جاري توليد الصوت...';
      try {
        const res = await fetch('/api/tts/speak-base64', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ text, lang: 'auto', gender: 'male' })
        });
        const data = await res.json();
        if (!res.ok) { status.textContent = 'خطأ: ' + (data.detail || res.status); return; }
        const bin = atob(data.audio_base64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const blobUrl = URL.createObjectURL(new Blob([bytes], { type: data.mime_type }));
        player.src = blobUrl;
        await player.play();
        status.textContent = 'الصوت: ' + data.voice + ' | النوع: ' + data.mime_type + ' | الكاش: ' + data.cached;
      } catch (e) {
        status.textContent = 'حصل خطأ: ' + e;
      }
    }
  </script>
</body>
</html>"""


@router.get("/speak", response_class=AudioStreamResponse, responses=AUDIO_RESPONSES)
async def speak_audio_get(
    request: Request,
    text: str = Query(
        ...,
        min_length=1,
        max_length=3000,
        description="Text to speak aloud.",
        examples=["انا عايز اشرب ميه"],
    ),
    lang: Literal["auto", "ar", "en"] = Query(default="auto"),
    gender: Literal["male", "female"] = Query(default="male"),
    rate: str = Query(default="+0%"),
) -> Response:
    """Synthesize speech via GET (supports HTTP Range requests for browser players)."""
    try:
        res = await tts_service.synthesize(
            text=text,
            lang=lang,
            gender=gender,
            rate=rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TTS synthesis unavailable: {exc}") from exc

    return _build_audio_response(res, request.headers.get("range"))


@router.post("/speak", response_class=AudioStreamResponse, responses=AUDIO_RESPONSES)
async def speak_audio(request: Request, payload: TTSRequest) -> Response:
    """Synthesize speech and return raw audio bytes (audio/mpeg or audio/wav)."""
    try:
        res = await tts_service.synthesize(
            text=payload.text,
            lang=payload.lang,
            gender=payload.gender,
            rate=payload.rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TTS synthesis unavailable: {exc}") from exc

    return _build_audio_response(res, request.headers.get("range"))


@router.post("/speak-base64", response_model=TTSBase64Response)
async def speak_base64(payload: TTSRequest) -> dict:
    """Synthesize speech and return audio encoded as JSON base64."""
    try:
        return await tts_service.synthesize_base64(
            text=payload.text,
            lang=payload.lang,
            gender=payload.gender,
            rate=payload.rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"TTS synthesis unavailable: {exc}") from exc
