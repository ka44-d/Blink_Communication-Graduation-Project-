"""Standalone LLM Smart Sentence Suggestion Service for Blink Communication.

Supports:
1. Cloud/Local OpenAI-compatible LLM APIs (Groq Llama 3.1, OpenAI GPT-4o-mini,
   OpenRouter, or local Ollama) configured securely via environment variables
   (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL).
2. Automatic offline AAC fallback engine using curated Egyptian Arabic & English
   patient sentence patterns and dictionary.json context — ensuring 100% uptime
   even without internet or an API key.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Literal

import httpx

Language = Literal["ar", "en"]
LLMMode = Literal["complete", "reply", "expand"]

DEFAULT_DICT_PATH = Path(__file__).resolve().parents[2] / "data" / "dictionary.json"

AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
AR_ALEF_RE = re.compile(r"[أإآ]")

AR_CURATED_COMPLETIONS: dict[str, list[str]] = {
    "انا": [
        "انا عايز اشرب ميه",
        "انا حاسس بتعب شويه",
        "انا محتاج اروح الحمام",
        "انا كويس الحمد لله",
    ],
    "عايز": [
        "عايز اشرب ميه من فضلك",
        "عايز اكلم الدكتور",
        "عايز انام وارتاح شويه",
        "عايز حد يقعد جنبي",
    ],
    "محتاج": [
        "محتاج الدواء بتاعي دلوقتي",
        "محتاج دكتور يشوفني",
        "محتاج مساعدة لو سمحت",
        "محتاج اغير وضعيتي",
    ],
    "حاسس": [
        "حاسس بوجع في جسمي",
        "حاسس بدوخة ومحتاج ارتاح",
        "حاسس ببرد عايز غطا",
        "حاسس اني احسن دلوقتي",
    ],
    "تعبان": [
        "انا تعبان ومحتاج دكتور",
        "تعبان ومش قادر اتنفس كويس",
        "تعبان عايز اخد المسكن",
        "تعبان ومحتاج ارتاح شويه",
    ],
    "دكتور": [
        "نادي الدكتور لو سمحت",
        "عايز اسأل الدكتور عن العلاج",
        "محتاج الدكتور يكشف عليا",
        "الدكتور هييجي امتى",
    ],
    "ميه": [
        "ممكن كوباية ميه لو سمحت",
        "عايز اشرب ميه ساقعه",
        "عطشان ومحتاج ميه",
        "ميه دافيه من فضلك",
    ],
    "وجع": [
        "عندي وجع جامد ومحتاج مسكن",
        "حاسس بوجع في صدري",
        "الوجع زاد شويه دلوقتي",
        "محتاج حد يطمني على الوجع ده",
    ],
}

EN_CURATED_COMPLETIONS: dict[str, list[str]] = {
    "i": [
        "I want to drink some water",
        "I need to see the doctor",
        "I feel tired and need rest",
        "I am feeling better now",
    ],
    "want": [
        "I want some water please",
        "I want to take my medicine",
        "I want to rest for a bit",
        "I want to call my family",
    ],
    "need": [
        "I need help right now",
        "I need the doctor please",
        "I need my pain medicine",
        "I need to use the bathroom",
    ],
    "feel": [
        "I feel pain right now",
        "I feel cold please cover me",
        "I feel dizzy and tired",
        "I feel much better thank you",
    ],
    "doctor": [
        "Please call the doctor",
        "When will the doctor arrive",
        "I need to ask the doctor something",
        "Please tell the doctor I am in pain",
    ],
    "water": [
        "Can I have some water please",
        "I am thirsty and need water",
        "Cold water please",
        "Just a sip of water",
    ],
}

AR_QUICK_REPLIES: list[tuple[tuple[str, ...], list[str]]] = [
    (
        ("تشرب", "اكل", "تاكل", "جعان", "عطشان", "ميه", "شاي", "عصير"),
        ["ايوه عايز اشرب ميه", "لا شكرا مش دلوقتي", "ممكن حاجة دافيه", "عايز اكل حاجة خفيفة"],
    ),
    (
        ("وجع", "تعبان", "بيوجع", "الم", "حاسس", "كويس", "عامل"),
        ["الحمد لله احسن شويه", "في وجع بسيط لسه", "تعبان ومحتاج مسكن", "محتاج انام وارتاح"],
    ),
    (
        ("دكتور", "دوا", "علاج", "ممرضة"),
        ["ايوه ناديه لو سمحت", "خدت الدواء خلاص", "محتاج مسكن للوجع", "عايز اعرف معاد الدواء"],
    ),
]

EN_QUICK_REPLIES: list[tuple[tuple[str, ...], list[str]]] = [
    (
        ("water", "drink", "eat", "hungry", "thirsty", "food"),
        ["Yes please some water", "No thank you not now", "Something warm please", "Just a small snack"],
    ),
    (
        ("pain", "hurt", "feel", "okay", "how", "better"),
        ["I feel better thank you", "I still have some pain", "I feel tired and need rest", "Please call the nurse"],
    ),
    (
        ("doctor", "medicine", "nurse", "help"),
        ["Yes please call them", "I already took my medicine", "I need pain relief", "Thank you for helping"],
    ),
]


def _norm_ar(text: str) -> str:
    cleaned = AR_DIACRITICS_RE.sub("", text or "")
    cleaned = AR_ALEF_RE.sub("ا", cleaned)
    return cleaned.replace("ى", "ي").replace("ة", "ه").strip()


class LLMService:
    """AAC-focused Smart Sentence Generator with API + Local Fallback."""

    def __init__(
        self,
        dictionary_path: str | Path = DEFAULT_DICT_PATH,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.dictionary_path = Path(dictionary_path)
        self._next_words: dict[str, dict[str, list[str]]] = self._load_next_words(
            self.dictionary_path
        )
        self.api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY", "").strip()
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").strip().rstrip("/")
        )
        self.model = (
            model
            if model is not None
            else os.getenv("LLM_MODEL", "llama-3.1-8b-instant").strip()
        )

    @staticmethod
    def _load_next_words(path: Path) -> dict[str, dict[str, list[str]]]:
        if not path.exists():
            return {"ar": {}, "en": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("nextWords", {"ar": {}, "en": {}})
        except Exception:
            return {"ar": {}, "en": {}}

    @property
    def is_api_configured(self) -> bool:
        return bool(self.api_key)

    def _build_system_prompt(self, lang: Language, mode: LLMMode, limit: int) -> str:
        lang_label = (
            "Egyptian Colloquial Arabic (عامية مصرية بسيطة ومهذبة)"
            if lang == "ar"
            else "simple natural English"
        )
        if mode == "reply":
            task_desc = "Generate short, natural patient replies to the caregiver's question."
        elif mode == "expand":
            task_desc = "Expand the patient's brief keywords into complete, polite, ready-to-speak sentences."
        else:
            task_desc = "Complete the patient's partial input into full, short, ready-to-speak sentences."

        return (
            "You are an AAC communication assistant for a speech-impaired patient using an eye-tracking keyboard.\n"
            f"{task_desc}\n"
            f"Language: {lang_label}.\n"
            "Rules:\n"
            f"- Return strictly a JSON object with one key \"suggestions\" containing an array of exactly {limit} short sentences (3 to 7 words each).\n"
            "- No numbering, no markdown, no extra explanation."
        )

    @staticmethod
    def _parse_llm_json(raw_content: str, limit: int) -> list[str]:
        text = (raw_content or "").strip()
        if not text:
            return []

        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL).strip()

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and isinstance(parsed.get("suggestions"), list):
                items = [str(x).strip() for x in parsed["suggestions"] if str(x).strip()]
                return items[:limit]
            if isinstance(parsed, list):
                items = [str(x).strip() for x in parsed if str(x).strip()]
                return items[:limit]
        except Exception:
            pass

        lines = [
            re.sub(r"^[\d\-\.\)\*\s]+", "", ln).strip(" \"'")
            for ln in text.splitlines()
            if ln.strip()
        ]
        return [ln for ln in lines if ln][:limit]

    async def _call_remote_llm(
        self, text: str, lang: Language, mode: LLMMode, limit: int
    ) -> list[str]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": 0.4,
            "max_tokens": 220,
            "messages": [
                {"role": "system", "content": self._build_system_prompt(lang, mode, limit)},
                {"role": "user", "content": f"Input ({mode}): {text}"},
            ],
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        return self._parse_llm_json(content, limit)

    def _local_suggest(
        self, text: str, lang: Language, mode: LLMMode, limit: int
    ) -> list[str]:
        cleaned = (text or "").strip()
        results: list[str] = []
        seen: set[str] = set()

        def add_all(items: list[str]) -> None:
            for item in items:
                s = item.strip()
                if s and s not in seen:
                    seen.add(s)
                    results.append(s)
                    if len(results) >= limit:
                        return

        if mode == "reply":
            norm_q = _norm_ar(cleaned) if lang == "ar" else cleaned.lower()
            table = AR_QUICK_REPLIES if lang == "ar" else EN_QUICK_REPLIES
            for keywords, replies in table:
                if any((_norm_ar(k) if lang == "ar" else k) in norm_q for k in keywords):
                    add_all(replies)
            if len(results) < limit:
                add_all(
                    [
                        "ايوه من فضلك",
                        "لا شكرا",
                        "محتاج مساعدة لو سمحت",
                        "الحمد لله انا كويس",
                    ]
                    if lang == "ar"
                    else [
                        "Yes please",
                        "No thank you",
                        "I need help please",
                        "I am doing okay",
                    ]
                )
            return results[:limit]

        tokens = [t for t in cleaned.split() if t]
        curated = AR_CURATED_COMPLETIONS if lang == "ar" else EN_CURATED_COMPLETIONS

        if tokens:
            # 1. Curated full AAC sentences matching any token (most recent first)
            for tok in reversed(tokens):
                key = _norm_ar(tok) if lang == "ar" else tok.lower()
                if key in curated:
                    add_all(curated[key])

            # 2. Dictionary nextWords continuation fallback if still short
            if len(results) < limit:
                next_map = self._next_words.get(lang, {})
                if len(tokens) >= 2:
                    two_key = " ".join(tokens[-2:])
                    if two_key in next_map:
                        add_all([f"{cleaned} {w}" for w in next_map[two_key]])
                last_tok = tokens[-1]
                if last_tok in next_map:
                    add_all([f"{cleaned} {w}" for w in next_map[last_tok]])

            # 3. Polite sentence templates wrapping the raw input
            if len(results) < limit:
                if lang == "ar":
                    add_all(
                        [
                            f"{cleaned} من فضلك",
                            f"انا محتاج {cleaned}",
                            f"ممكن {cleaned} لو سمحت",
                            f"عايز {cleaned} دلوقتي",
                        ]
                    )
                else:
                    add_all(
                        [
                            f"{cleaned} please",
                            f"I need {cleaned}",
                            f"Can I have {cleaned}",
                            f"Please help with {cleaned}",
                        ]
                    )
        else:
            default_key = "انا" if lang == "ar" else "i"
            add_all(curated[default_key])

        return results[:limit]

    async def suggest(
        self,
        text: str,
        lang: Language = "ar",
        mode: LLMMode = "complete",
        limit: int = 4,
    ) -> dict:
        """Generate smart AAC sentence suggestions using LLM API or local fallback."""
        active_lang: Language = "en" if lang == "en" else "ar"
        active_mode: LLMMode = mode if mode in ("complete", "reply", "expand") else "complete"
        cleaned_text = (text or "").strip()

        if self.is_api_configured and cleaned_text:
            try:
                api_suggestions = await self._call_remote_llm(
                    cleaned_text, active_lang, active_mode, limit
                )
                if api_suggestions:
                    return {
                        "input": cleaned_text,
                        "mode": active_mode,
                        "lang": active_lang,
                        "source": "llm_api",
                        "model": self.model,
                        "fallback_used": False,
                        "suggestions": api_suggestions,
                    }
            except Exception:
                pass

        local_suggestions = self._local_suggest(
            cleaned_text, active_lang, active_mode, limit
        )
        return {
            "input": cleaned_text,
            "mode": active_mode,
            "lang": active_lang,
            "source": "local_fallback",
            "model": "aac_local_context_engine",
            "fallback_used": True,
            "suggestions": local_suggestions,
        }
