"""FastAPI router for the LLM Smart Sentence Suggestions module."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from modules.LLM.llm_service import LLMService

llm_service = LLMService()

router = APIRouter(prefix="/api/llm", tags=["LLM - Smart Sentence Suggestions"])


class LLMSuggestRequest(BaseModel):
    text: str = Field(
        default="",
        max_length=300,
        description="Partial phrase, keywords, or caregiver question.",
        examples=["انا تعبان"],
    )
    lang: Literal["ar", "en"] = Field(
        default="ar",
        description="Output language: 'ar' or 'en'.",
    )
    mode: Literal["complete", "reply", "expand"] = Field(
        default="complete",
        description="'complete' to finish sentence, 'reply' to answer a question, 'expand' to turn keywords into full sentences.",
    )
    limit: int = Field(
        default=4,
        ge=1,
        le=6,
        description="Number of suggested sentences to return.",
    )


class LLMSuggestResponse(BaseModel):
    input: str
    mode: Literal["complete", "reply", "expand"]
    lang: Literal["ar", "en"]
    source: Literal["llm_api", "local_fallback"]
    model: str
    fallback_used: bool
    suggestions: list[str]


@router.get("/health")
def llm_health() -> dict:
    """Return LLM module status without exposing secret API keys."""
    return {
        "module": "LLM",
        "status": "ready",
        "api_configured": llm_service.is_api_configured,
        "active_backend": "llm_api" if llm_service.is_api_configured else "local_fallback",
        "configured_model": (
            llm_service.model
            if llm_service.is_api_configured
            else "aac_local_context_engine"
        ),
    }


@router.post("/suggest", response_model=LLMSuggestResponse)
async def suggest_sentences(payload: LLMSuggestRequest) -> dict:
    """Return 4 smart, ready-to-speak sentences for the patient."""
    return await llm_service.suggest(
        text=payload.text,
        lang=payload.lang,
        mode=payload.mode,
        limit=payload.limit,
    )
