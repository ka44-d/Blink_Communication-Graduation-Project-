"""FastAPI router for the Information Retrieval (IR) module.

Exposes HTTP endpoints so the Front-end or another backend service
can send typed text and receive ranked word suggestions in <1 ms.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from modules.IR.ir_engine import IREngine

# Initialize the IR engine once at startup so the 22k-word Trie stays in memory.
ir_engine = IREngine()

router = APIRouter(prefix="/api/ir", tags=["IR - Information Retrieval"])


class IRSuggestionRequest(BaseModel):
    text: str = Field(
        default="",
        description="Current text typed by the user (e.g. 'انا عايز اش').",
        examples=["انا عايز اش"],
    )
    lang: Literal["ar", "en"] = Field(
        default="ar",
        description="Active keyboard language: 'ar' or 'en'.",
    )
    limit: int = Field(
        default=4,
        ge=1,
        le=12,
        description="Maximum number of suggestions to return.",
    )


class IRSuggestionItem(BaseModel):
    word: str
    score: float
    source: str
    action: Literal["next", "complete"]


class IRSuggestionResponse(BaseModel):
    mode: str
    current_fragment: str
    context_tokens: list[str]
    suggestions: list[str]
    results: list[IRSuggestionItem]


@router.get("/health")
def ir_health() -> dict:
    """Return IR engine readiness and loaded vocabulary counts."""
    return {
        "module": "IR",
        "status": "ready",
        "ar_words": len(ir_engine.words["ar"]),
        "en_words": len(ir_engine.words["en"]),
    }


@router.post("/suggest", response_model=IRSuggestionResponse)
def suggest_words(payload: IRSuggestionRequest) -> dict:
    """Return top-ranked Arabic or English word suggestions for the input text."""
    return ir_engine.retrieve(
        raw_text=payload.text,
        lang=payload.lang,
        limit=payload.limit,
    )
