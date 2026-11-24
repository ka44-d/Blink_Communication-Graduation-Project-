"""Standalone Spelling Correction Engine for Blink Communication.

Implements a fast Hybrid Noisy-Channel NLP model combining:
1. Damerau-Levenshtein edit distance (via C++ rapidfuzz backend) for omissions,
   insertions, substitutions, and adjacent transpositions.
2. Corpus Unigram Frequency Prior from the 22,000-word AR/EN dictionary.
3. Context N-Gram Re-ranking (Bigram/Trigram) using preceding words.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from rapidfuzz import process
from rapidfuzz.distance import DamerauLevenshtein

Language = Literal["ar", "en"]

AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
AR_ALEF_RE = re.compile(r"[أإآ]")
TOKEN_SPLIT_RE = re.compile(r"(\s+)")

DEFAULT_DICT_PATH = Path(__file__).resolve().parents[2] / "data" / "dictionary.json"


def normalize_for_spelling(text: str, lang: Language = "ar") -> str:
    """Normalize text for typo matching without altering canonical display words."""
    if not text:
        return ""

    if lang == "en":
        return text.lower().strip()

    cleaned = AR_DIACRITICS_RE.sub("", text)
    cleaned = AR_ALEF_RE.sub("ا", cleaned)
    cleaned = cleaned.replace("ى", "ي").replace("ة", "ه")
    return cleaned.strip()


class SpellingCorrector:
    """Fast Arabic & English Spelling Corrector (zero dependency on IR module)."""

    def __init__(self, dictionary_path: str | Path = DEFAULT_DICT_PATH) -> None:
        self.dictionary_path = Path(dictionary_path)
        self._data = self._load_dictionary(self.dictionary_path)

        self.words: dict[Language, list[str]] = {
            "ar": self._data.get("words", {}).get("ar", []),
            "en": self._data.get("words", {}).get("en", []),
        }

        self._norm_words: dict[Language, list[str]] = {
            "ar": [normalize_for_spelling(w, "ar") for w in self.words["ar"]],
            "en": [normalize_for_spelling(w, "en") for w in self.words["en"]],
        }

        self._word_sets: dict[Language, set[str]] = {
            "ar": set(self._norm_words["ar"]),
            "en": set(self._norm_words["en"]),
        }

        # Map normalized word -> first (most frequent) index in vocabulary
        self._first_index: dict[Language, dict[str, int]] = {"ar": {}, "en": {}}
        self._unique_norms: dict[Language, list[str]] = {"ar": [], "en": []}
        for lang in ("ar", "en"):
            idx_map = self._first_index[lang]
            unique_list = self._unique_norms[lang]
            for idx, norm in enumerate(self._norm_words[lang]):
                if norm and norm not in idx_map:
                    idx_map[norm] = idx
                    unique_list.append(norm)

        # Context index from nextWords for context-aware candidate re-ranking
        self._context_index: dict[Language, dict[str, set[str]]] = {
            "ar": self._build_context_index(
                self._data.get("nextWords", {}).get("ar", {}), "ar"
            ),
            "en": self._build_context_index(
                self._data.get("nextWords", {}).get("en", {}), "en"
            ),
        }

    @staticmethod
    def _load_dictionary(path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"Dictionary file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _build_context_index(
        raw_next_words: dict[str, list[str]], lang: Language
    ) -> dict[str, set[str]]:
        indexed: dict[str, set[str]] = {}
        for key, candidates in raw_next_words.items():
            norm_key = " ".join(
                normalize_for_spelling(tok, lang)
                for tok in key.split()
                if tok.strip()
            )
            if not norm_key:
                continue
            norm_cands = {
                normalize_for_spelling(c, lang) for c in candidates if c.strip()
            }
            if norm_cands:
                indexed[norm_key] = norm_cands
        return indexed

    def is_valid_word(self, word: str, lang: Language = "ar") -> bool:
        """Check whether the word exists in the normalized dictionary."""
        active_lang: Language = "en" if lang == "en" else "ar"
        norm = normalize_for_spelling(word, active_lang)
        return bool(norm) and norm in self._word_sets[active_lang]

    def _get_context_candidates(
        self, context_words: list[str] | None, lang: Language
    ) -> set[str]:
        if not context_words:
            return set()

        ctx_map = self._context_index[lang]
        expected: set[str] = set()

        if len(context_words) >= 2:
            two_key = " ".join(
                normalize_for_spelling(w, lang) for w in context_words[-2:]
            )
            expected.update(ctx_map.get(two_key, set()))

        last_key = normalize_for_spelling(context_words[-1], lang)
        if last_key:
            expected.update(ctx_map.get(last_key, set()))

        return expected

    def correct_word(
        self,
        word: str,
        lang: Language = "ar",
        limit: int = 4,
        context_words: list[str] | None = None,
    ) -> dict:
        """Return ranked spelling corrections for a single word."""
        active_lang: Language = "en" if lang == "en" else "ar"
        raw_word = (word or "").strip()
        norm_input = normalize_for_spelling(raw_word, active_lang)

        if not norm_input:
            return {
                "input": raw_word,
                "normalized": "",
                "is_valid": False,
                "best_correction": "",
                "suggestions": [],
                "results": [],
            }

        is_valid = norm_input in self._word_sets[active_lang]
        vocab = self.words[active_lang]
        first_index = self._first_index[active_lang]
        unique_norms = self._unique_norms[active_lang]
        context_expected = self._get_context_candidates(context_words, active_lang)

        input_len = len(norm_input)
        max_len_diff = max(2, input_len // 2 + 1)
        min_sim = 0.45 if input_len <= 4 else 0.52

        matches = process.extract(
            norm_input,
            unique_norms,
            scorer=DamerauLevenshtein.normalized_similarity,
            score_cutoff=min_sim,
            limit=None,
        )

        scored_results: list[dict] = []

        for cand_norm, sim, _ in matches:
            if abs(len(cand_norm) - input_len) > max_len_diff:
                continue

            idx = first_index[cand_norm]
            edit_dist = DamerauLevenshtein.distance(norm_input, cand_norm)
            freq_bonus = 0.25 / (1.0 + idx / 150.0)
            first_bonus = 0.05 if cand_norm[0] == norm_input[0] else 0.0
            len_bonus = 0.02 if abs(len(cand_norm) - input_len) <= 1 else 0.0
            in_context = cand_norm in context_expected
            context_bonus = 0.16 if in_context else 0.0

            # Exact dictionary match keeps priority when valid
            exact_bonus = 0.35 if edit_dist == 0 else 0.0

            total_score = (
                sim + freq_bonus + first_bonus + len_bonus + context_bonus + exact_bonus
            )

            scored_results.append(
                {
                    "word": vocab[idx],
                    "score": round(total_score, 4),
                    "similarity": round(sim, 3),
                    "edit_distance": int(edit_dist),
                    "freq_bonus": round(freq_bonus, 3),
                    "context_match": in_context,
                }
            )

        ranked = sorted(
            scored_results,
            key=lambda item: (-item["score"], item["edit_distance"]),
        )[:limit]

        suggestions = [item["word"] for item in ranked]
        best = suggestions[0] if suggestions else raw_word

        return {
            "input": raw_word,
            "normalized": norm_input,
            "is_valid": is_valid,
            "best_correction": best,
            "suggestions": suggestions,
            "results": ranked,
        }

    def correct_sentence(self, text: str, lang: Language = "ar") -> dict:
        """Correct misspelled words across a full sentence using running context."""
        active_lang: Language = "en" if lang == "en" else "ar"
        raw_text = text or ""

        if not raw_text.strip():
            return {
                "original_text": raw_text,
                "corrected_text": raw_text,
                "has_changes": False,
                "corrections": [],
            }

        parts = TOKEN_SPLIT_RE.split(raw_text)
        fixed_parts: list[str] = []
        corrections: list[dict] = []
        running_context: list[str] = []

        for part in parts:
            if not part or part.isspace():
                fixed_parts.append(part)
                continue

            if self.is_valid_word(part, active_lang):
                fixed_parts.append(part)
                running_context.append(part)
                continue

            res = self.correct_word(
                part,
                lang=active_lang,
                limit=4,
                context_words=running_context,
            )

            best = res["best_correction"] or part
            # Only apply correction when similarity is reasonably confident
            top_sim = res["results"][0]["similarity"] if res["results"] else 0.0
            if best != part and top_sim >= 0.50:
                fixed_parts.append(best)
                running_context.append(best)
                corrections.append(
                    {
                        "original": part,
                        "corrected": best,
                        "alternatives": res["suggestions"],
                    }
                )
            else:
                fixed_parts.append(part)
                running_context.append(part)

        corrected_text = "".join(fixed_parts)
        return {
            "original_text": raw_text,
            "corrected_text": corrected_text,
            "has_changes": corrected_text != raw_text,
            "corrections": corrections,
        }
