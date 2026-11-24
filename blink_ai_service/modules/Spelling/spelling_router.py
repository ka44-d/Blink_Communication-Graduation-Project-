"""FastAPI router for the Spelling Correction module.

Exposes HTTP endpoints so the Front-end or another backend service
can send a misspelled word or full sentence and get ranked corrections.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from modules.Spelling.spelling_corrector import SpellingCorrector

# Initialize once at startup so the 22k-word vocabulary stays in memory.
spelling_corrector = SpellingCorrector()

router = APIRouter(prefix="/api/spelling", tags=["Spelling - Spell Correction"])


class WordCorrectionRequest(BaseModel):
    word: str = Field(
        ...,
        description="Single word to check/correct (e.g. 'عاز' or 'wter').",
        examples=["عاز"],
    )
    lang: Literal["ar", "en"] = Field(
        default="ar",
        description="Active keyboard language: 'ar' or 'en'.",
    )
    limit: int = Field(
        default=4,
        ge=1,
        le=12,
        description="Maximum number of correction candidates to return.",
    )
    context_words: list[str] = Field(
        default_factory=list,
        description="Optional preceding words in the sentence for context re-ranking.",
        examples=[["انا"]],
    )


class SpellingCandidateItem(BaseModel):
    word: str
    score: float
    similarity: float
    edit_distance: int
    freq_bonus: float
    context_match: bool


class WordCorrectionResponse(BaseModel):
    input: str
    normalized: str
    is_valid: bool
    best_correction: str
    suggestions: list[str]
    results: list[SpellingCandidateItem]


class SentenceCorrectionRequest(BaseModel):
    text: str = Field(
        ...,
        description="Full sentence to check and fix word by word.",
        examples=["انا عاز اشب ميهه"],
    )
    lang: Literal["ar", "en"] = Field(
        default="ar",
        description="Active keyboard language: 'ar' or 'en'.",
    )


class SentenceWordFix(BaseModel):
    original: str
    corrected: str
    alternatives: list[str]


class SentenceCorrectionResponse(BaseModel):
    original_text: str
    corrected_text: str
    has_changes: bool
    corrections: list[SentenceWordFix]


@router.get("/health")
def spelling_health() -> dict:
    """Return Spelling module readiness and model metadata."""
    return {
        "module": "Spelling",
        "status": "ready",
        "model": "Hybrid Noisy-Channel (Damerau-Levenshtein + Frequency + Context N-Gram)",
        "ar_words": len(spelling_corrector.words["ar"]),
        "en_words": len(spelling_corrector.words["en"]),
    }


@router.post("/correct-word", response_model=WordCorrectionResponse)
def correct_single_word(payload: WordCorrectionRequest) -> dict:
    """Return top-ranked spelling corrections for a single word."""
    return spelling_corrector.correct_word(
        word=payload.word,
        lang=payload.lang,
        limit=payload.limit,
        context_words=payload.context_words or None,
    )


@router.post("/correct-sentence", response_model=SentenceCorrectionResponse)
def correct_full_sentence(payload: SentenceCorrectionRequest) -> dict:
    """Check a full sentence and auto-correct misspelled words using context."""
    return spelling_corrector.correct_sentence(
        text=payload.text,
        lang=payload.lang,
    )
