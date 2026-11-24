"""Information Retrieval (IR) Engine for Blink Communication.

Provides fast O(L) prefix indexing using a Trie, Arabic text normalization,
context-based N-Gram next-word prediction, and ranked candidate retrieval.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

Language = Literal["ar", "en"]

AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
AR_ALEF_RE = re.compile(r"[أإآ]")
WHITESPACE_RE = re.compile(r"\s+")

DEFAULT_DICT_PATH = Path(__file__).resolve().parents[2] / "data" / "dictionary.json"


def normalize_text(text: str, lang: Language = "ar") -> str:
    """Normalize text for indexing and lookup without altering display words."""
    if not text:
        return ""

    if lang == "en":
        return text.lower().strip()

    cleaned = AR_DIACRITICS_RE.sub("", text)
    cleaned = AR_ALEF_RE.sub("ا", cleaned)
    cleaned = cleaned.replace("ى", "ي").replace("ة", "ه")
    return cleaned.strip()


class TrieNode:
    """Memory-efficient Trie node storing indices of top-ranked words."""

    __slots__ = ("children", "top_indices")

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.top_indices: list[int] = []


class IREngine:
    """Fast Information Retrieval & Ranking Engine for Arabic and English."""

    def __init__(self, dictionary_path: str | Path = DEFAULT_DICT_PATH) -> None:
        self.dictionary_path = Path(dictionary_path)
        self._data = self._load_dictionary(self.dictionary_path)

        self.words: dict[Language, list[str]] = {
            "ar": self._data.get("words", {}).get("ar", []),
            "en": self._data.get("words", {}).get("en", []),
        }
        self.starters: dict[Language, list[str]] = {
            "ar": self._data.get("starters", {}).get("ar", []),
            "en": self._data.get("starters", {}).get("en", []),
        }

        self._tries: dict[Language, TrieNode] = {
            "ar": self._build_trie(self.words["ar"], "ar"),
            "en": self._build_trie(self.words["en"], "en"),
        }
        self._context_index: dict[Language, dict[str, list[str]]] = {
            "ar": self._build_context_index(
                self._data.get("nextWords", {}).get("ar", {}), "ar"
            ),
            "en": self._build_context_index(
                self._data.get("nextWords", {}).get("en", {}), "en"
            ),
        }
        self._word_sets: dict[Language, set[str]] = {
            "ar": {normalize_text(w, "ar") for w in self.words["ar"]},
            "en": {normalize_text(w, "en") for w in self.words["en"]},
        }

    @staticmethod
    def _load_dictionary(path: Path) -> dict:
        if not path.exists():
            raise FileNotFoundError(f"Dictionary file not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _build_trie(words: list[str], lang: Language, max_per_node: int = 30) -> TrieNode:
        root = TrieNode()
        for idx, word in enumerate(words):
            norm = normalize_text(word, lang)
            if not norm:
                continue

            node = root
            for ch in norm:
                if ch not in node.children:
                    node.children[ch] = TrieNode()
                node = node.children[ch]
                if len(node.top_indices) < max_per_node:
                    node.top_indices.append(idx)
        return root

    @staticmethod
    def _build_context_index(
        raw_next_words: dict[str, list[str]], lang: Language
    ) -> dict[str, list[str]]:
        indexed: dict[str, list[str]] = {}
        for key, candidates in raw_next_words.items():
            norm_key = " ".join(
                normalize_text(tok, lang) for tok in key.split() if tok.strip()
            )
            if norm_key:
                indexed[norm_key] = candidates
        return indexed

    def has_word(self, word: str, lang: Language = "ar") -> bool:
        """Check whether the normalized word exists in the indexed vocabulary."""
        active_lang: Language = "en" if lang == "en" else "ar"
        return normalize_text(word, active_lang) in self._word_sets[active_lang]

    def search_prefix(
        self, prefix: str, lang: Language = "ar", limit: int = 10
    ) -> list[str]:
        """Return top-ranked words matching the given prefix in O(L) time."""
        active_lang: Language = "en" if lang == "en" else "ar"
        prefix_norm = normalize_text(prefix, active_lang)
        if not prefix_norm:
            return []

        node = self._tries[active_lang]
        for ch in prefix_norm:
            if ch not in node.children:
                return []
            node = node.children[ch]

        vocab = self.words[active_lang]
        return [vocab[idx] for idx in node.top_indices[:limit]]

    def predict_next_words(
        self, tokens: list[str], lang: Language = "ar", limit: int = 4
    ) -> list[str]:
        """Predict next words using 2-word (trigram) then 1-word (bigram) context."""
        active_lang: Language = "en" if lang == "en" else "ar"
        if not tokens:
            return []

        context_map = self._context_index[active_lang]
        last_word = tokens[-1]
        last_norm = normalize_text(last_word, active_lang)

        results: list[str] = []
        seen: set[str] = {last_norm} if last_norm else set()

        def add_candidates(candidates: list[str]) -> None:
            for cand in candidates:
                if len(results) >= limit:
                    break
                cand_norm = normalize_text(cand, active_lang)
                if not cand_norm or cand_norm in seen:
                    continue
                seen.add(cand_norm)
                results.append(cand)

        if len(tokens) >= 2:
            two_key = " ".join(normalize_text(t, active_lang) for t in tokens[-2:])
            if two_key in context_map:
                add_candidates(context_map[two_key])

        if last_norm and last_norm in context_map:
            add_candidates(context_map[last_norm])

        return results

    @staticmethod
    def parse_input(raw_text: str) -> dict:
        """Split raw user text into state mode, completed words, and active fragment."""
        text = raw_text or ""
        if not text.strip():
            return {
                "mode": "empty",
                "completed_words": [],
                "current_fragment": "",
            }

        ends_with_space = text[-1].isspace()
        tokens = [tok for tok in WHITESPACE_RE.split(text.strip()) if tok]

        if ends_with_space:
            return {
                "mode": "next_word",
                "completed_words": tokens,
                "current_fragment": "",
            }

        return {
            "mode": "complete_word",
            "completed_words": tokens[:-1],
            "current_fragment": tokens[-1],
        }

    def retrieve(
        self, raw_text: str, lang: Language = "ar", limit: int = 4
    ) -> dict:
        """Retrieve and rank top candidate suggestions for the given input text."""
        active_lang: Language = "en" if lang == "en" else "ar"
        parsed = self.parse_input(raw_text)
        mode = parsed["mode"]
        completed = parsed["completed_words"]
        fragment = parsed["current_fragment"]

        ranked_items: list[dict] = []
        seen: set[str] = set()

        def push_item(word: str, score: float, source: str, action: str) -> None:
            if len(ranked_items) >= limit:
                return
            norm = normalize_text(word, active_lang)
            if not norm or norm in seen:
                return
            seen.add(norm)
            ranked_items.append(
                {
                    "word": word,
                    "score": round(score, 3),
                    "source": source,
                    "action": action,
                }
            )

        # Case 1: Empty input -> return starter words
        if mode == "empty":
            for idx, word in enumerate(self.starters[active_lang]):
                push_item(word, 1.0 - idx * 0.05, "starter", "next")
            return self._format_response(mode, parsed, ranked_items)

        # Case 2: Trailing space -> predict next word from context + starters fallback
        if mode == "next_word":
            if completed:
                seen.add(normalize_text(completed[-1], active_lang))
            ctx_words = self.predict_next_words(completed, active_lang, limit=limit)
            for idx, word in enumerate(ctx_words):
                push_item(word, 0.98 - idx * 0.04, "context_ngram", "next")

            for idx, word in enumerate(self.starters[active_lang]):
                push_item(word, 0.60 - idx * 0.04, "starter_fallback", "next")

            for idx, word in enumerate(self.words[active_lang][:20]):
                push_item(word, 0.40 - idx * 0.01, "freq_fallback", "next")

            return self._format_response(mode, parsed, ranked_items)

        # Case 3: No trailing space -> check if completed known trigger word first (e.g. "عايز")
        frag_norm = normalize_text(fragment, active_lang)
        all_tokens_now = completed + [fragment]
        direct_next = self.predict_next_words(all_tokens_now, active_lang, limit=limit)

        if direct_next:
            effective_mode = "direct_next"
            max_next = limit - 1 if len(frag_norm) <= 2 else limit
            for idx, word in enumerate(direct_next[:max_next]):
                push_item(word, 0.96 - idx * 0.04, "direct_context", "next")

            if len(ranked_items) < limit:
                trie_longer = [
                    w
                    for w in self.search_prefix(fragment, active_lang, limit=limit * 2)
                    if normalize_text(w, active_lang) != frag_norm
                ]
                for idx, word in enumerate(trie_longer):
                    push_item(word, 0.72 - idx * 0.04, "trie_longer", "complete")

            return self._format_response(effective_mode, parsed, ranked_items)

        # Case 4: Partial word completion -> context-filtered first, then Trie frequency
        ctx_candidates = [
            w
            for w in self.predict_next_words(completed, active_lang, limit=limit * 2)
            if normalize_text(w, active_lang).startswith(frag_norm)
        ]
        for idx, word in enumerate(ctx_candidates):
            push_item(word, 0.95 - idx * 0.03, "context_prefix", "complete")

        trie_matches = self.search_prefix(fragment, active_lang, limit=limit * 2)
        for idx, word in enumerate(trie_matches):
            push_item(word, 0.85 - idx * 0.03, "trie_prefix", "complete")

        return self._format_response(mode, parsed, ranked_items)

    @staticmethod
    def _format_response(mode: str, parsed: dict, ranked_items: list[dict]) -> dict:
        return {
            "mode": mode,
            "current_fragment": parsed["current_fragment"],
            "context_tokens": parsed["completed_words"],
            "suggestions": [item["word"] for item in ranked_items],
            "results": ranked_items,
        }
