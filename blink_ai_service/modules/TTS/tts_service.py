"""Standalone Text-to-Speech (TTS) Service for Blink Communication.

Multi-Tier Bilingual (Arabic & English) TTS:
1. Natural Online Voice (ElevenLabs): When ELEVENLABS_API_KEY is set in .env,
   speaks using ElevenLabs (Adam ar / George en-US) and saves every generated MP3
   permanently to disk cache so it replays 100% offline with zero repeated credits.
2. Free Online Neural (edge-tts): Egyptian colloquial (ar-EG-ShakirNeural / SalmaNeural)
   and natural English (en-US-GuyNeural / JennyNeural), also disk-cached for offline use.
3. 100% Offline Fallback (auto fallback or TTS_MODE=offline):
   a. Persistent Disk Cache (ElevenLabs MP3s first, then Edge Egyptian Shakir MP3s).
   b. Windows Offline Voice (WinRT ar-EG / en-US).
   c. Local Neural ONNX models (mms-tts-ara Male Arabic + en_US-ryan-medium Piper Male).

One-time setup (pre-caches core phrases + downloads offline ONNX backup models):
    python -B -m modules.TTS.tts_service
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import os
import re
import sys
import threading
import wave
from collections import OrderedDict
from pathlib import Path
from typing import Literal

Language = Literal["ar", "en", "auto"]
Gender = Literal["female", "male"]
TTSMode = Literal["auto", "offline", "online"]

ARABIC_CHAR_RE = re.compile(r"[\u0600-\u06FF]")
RATE_RE = re.compile(r"^[+-]\d{1,3}%$")

DEFAULT_MODELS_DIR = Path(__file__).resolve().parent / "voices"

ONLINE_VOICE_MAP: dict[tuple[str, str], str] = {
    ("ar", "female"): "ar-EG-SalmaNeural",
    ("ar", "male"): "ar-EG-ShakirNeural",
    ("en", "female"): "en-US-JennyNeural",
    ("en", "male"): "en-US-GuyNeural",
}

ELEVENLABS_VOICE_MAP: dict[tuple[str, str], tuple[str, str]] = {
    ("ar", "male"): ("pNInz6obpgDQGcFmaJgB", "ElevenLabs-Adam (ar)"),
    ("ar", "female"): ("EXAVITQu4vr4xnSDxMaL", "ElevenLabs-Sarah (ar)"),
    ("en", "male"): ("JBFqnCBsd6RMkjVDRZzb", "ElevenLabs-George (en-US)"),
    ("en", "female"): ("EXAVITQu4vr4xnSDxMaL", "ElevenLabs-Sarah (en-US)"),
}

OFFLINE_VOICE_MAP: dict[str, str] = {
    "ar": "mms-tts-ara",
    "en": "en_US-ryan-medium",
}

MMS_AR_MODEL_URL = (
    "https://huggingface.co/Phoonnx/vits-ar-mms-graphemes/resolve/main/model.onnx"
)
MMS_AR_CONFIG_URL = (
    "https://huggingface.co/Phoonnx/vits-ar-mms-graphemes/resolve/main/config.json"
)
AR_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")

# Keep backward-compatible alias
VOICE_MAP = ONLINE_VOICE_MAP

DEFAULT_WARMUP_PHRASES: list[str] = [
    # أزرار وصفحات المشروع الأساسية
    "الاحتياجات",
    "الاحتياجات الأساسية",
    "الترفيه",
    "الكيبورد",
    "لوحة المفاتيح",
    "الإعدادات",
    "الطوارئ",
    "التواصل",
    "مساعدة",
    "رجوع",
    "الرئيسية",
    "التالي",
    "السابق",
    "نطق",
    "مسح",
    "مسافة",
    "تأكيد",
    "إلغاء",
    # ترفيه وقصص وميديا
    "قرآن",
    "عايز اسمع قرآن",
    "أغاني",
    "عايز اسمع اغاني",
    "أفلام",
    "فيديوهات",
    "ألعاب",
    "أخبار",
    "عايز اتفرج علي حاجة",
    # احتياجات المريض اليومية بالعامية المصرية
    "ميه",
    "أكل",
    "دواء",
    "دكتور",
    "الحمام",
    "نوم",
    "راحة",
    "غطا",
    "انا عايز اشرب ميه",
    "عايز اشرب ميه من فضلك",
    "ممكن كوباية ميه لو سمحت",
    "انا عايز اكل",
    "جعان وعايز اكل",
    "عطشان ومحتاج ميه",
    "محتاج دكتور",
    "نادي الدكتور لو سمحت",
    "محتاج الدواء بتاعي دلوقتي",
    "عايز اروح الحمام",
    "انا محتاج اروح الحمام",
    "انا تعبان",
    "انا حاسس بتعب شويه",
    "حاسس بوجع في جسمي",
    "حاسس بدوخة ومحتاج ارتاح",
    "مش قادر اتنفس كويس",
    "حاسس ببرد عايز غطا",
    "الجو حر شويه",
    "الحقوني",
    "محتاج مساعدة لو سمحت",
    "ممكن تساعدني",
    "محتاج اغير وضعيتي",
    "عايز انام وارتاح شويه",
    "عايز اقعد",
    "عايز حد يقعد جنبي",
    "انا كويس الحمد لله",
    "ايوه",
    "لا",
    "شكرا",
    "لو سمحت",
    "من فضلك",
    "الحمد لله",
    "صباح الخير",
    "مساء الخير",
    "السلام عليكم",
    "ازيك",
    "عامل ايه",
    # English UI & AAC phrases
    "Needs",
    "Entertainment",
    "Keyboard",
    "Settings",
    "Emergency",
    "Help",
    "Back",
    "Speak",
    "Clear",
    "Yes",
    "No",
    "Thank you",
    "Please",
    "I need water please",
    "I need the doctor",
    "I want to eat",
    "I need help right now",
    "I feel tired and need rest",
    "I am feeling better now",
]

# Light Egyptian vowel hints so offline Piper phonemizer pronounces colloquial words naturally
EGYPTIAN_PIPER_HINTS: dict[str, str] = {
    "انا": "أَنَا",
    "انت": "إِنْتَ",
    "انتي": "إِنْتِي",
    "احنا": "إِحْنَا",
    "ده": "دَه",
    "دي": "دِي",
    "دول": "دُول",
    "عايز": "عَايِز",
    "عايزة": "عَايْزَة",
    "ميه": "مَيَّة",
    "كوباية": "كُبَّايَة",
    "شاي": "شَاي",
    "قهوة": "قَهْوَة",
    "عصير": "عَصِير",
    "ساقع": "سَاقِع",
    "ساقعة": "سَاقْعَة",
    "دافي": "دَافِي",
    "سخن": "سُخْن",
    "عيش": "عِيش",
    "رز": "رُز",
    "فطار": "فِطَار",
    "غدا": "غَدَا",
    "عشا": "عَشَا",
    "دلوقتي": "دِلْوَقْتِي",
    "شويه": "شْوَيَّة",
    "شوية": "شْوَيَّة",
    "كتير": "كِتِير",
    "اوي": "أَوِي",
    "خالص": "خَالِص",
    "لسه": "لِسَّه",
    "تاني": "تَانِي",
    "بعدين": "بَعْدِين",
    "بسرعة": "بِسُرْعَة",
    "عشان": "عَشَان",
    "علشان": "عَلَشَان",
    "كده": "كِدَه",
    "ايوه": "أَيْوَة",
    "اه": "آه",
    "معلش": "مَعْلِش",
    "طيب": "طَيِّب",
    "ماشي": "مَاشِي",
    "حاضر": "حَاضِر",
    "يلا": "يَلَّا",
    "تمام": "تَمَام",
    "تعبان": "تَعْبَان",
    "تعبانة": "تَعْبَانَة",
    "جعان": "جَعَان",
    "جعانة": "جَعَانَة",
    "عطشان": "عَطْشَان",
    "عطشانة": "عَطْشَانَة",
    "بردان": "بَرْدَان",
    "حران": "حَرَّان",
    "دايخ": "دَايِخ",
    "مخنوق": "مَخْنُوق",
    "محتاج": "مِحْتَاج",
    "محتاجة": "مِحْتَاجَة",
    "حاسس": "حَاسِس",
    "حاسة": "حَاسَّة",
    "اشرب": "أَشْرَب",
    "اكل": "آكُل",
    "انام": "أَنَام",
    "اقعد": "أَقْعُد",
    "اروح": "أَرُوح",
    "اسمع": "أَسْمَع",
    "اشوف": "أَشُوف",
    "اتفرج": "أَتْفَرَّج",
    "افتح": "اِفْتَح",
    "اقفل": "اِقْفِل",
    "شغل": "شَغَّل",
    "اطفي": "اِطْفِي",
    "هات": "هَات",
    "اديني": "اِدِّينِي",
    "نادي": "نَادِي",
    "كلم": "كَلِّم",
    "اتصل": "اِتِّصِل",
    "الحقوني": "اِلْحَقُونِي",
    "ازيك": "إِزَّيَّك",
    "ازاي": "إِزَّاي",
    "اخبارك": "أَخْبَارَك",
    "أخبارك": "أَخْبَارَك",
    "عامل": "عَامِل",
    "عاملة": "عَامْلَة",
    "ايه": "إِيه",
    "إيه": "إِيه",
    "اي": "إِيه",
    "مين": "مِين",
    "امتى": "إِمْتَى",
    "فين": "فِين",
    "ليه": "لِيه",
    "النهارده": "النَّهَارْدَه",
    "بكرة": "بُكْرَة",
    "امبارح": "إِمْبَارِح",
    "مش": "مِش",
    "بتاعي": "بِتَاعِي",
    "شغاله": "شَغَّالَة",
    "حاجة": "حَاجَة",
    "كويس": "كْوَيِّس",
    "كويسة": "كْوَيِّسَة",
    "دوا": "دَوَا",
    "دواء": "دَوَا",
    "دكتور": "دُكْتُور",
    "مستشفى": "مُسْتَشْفَى",
    "تلفزيون": "تِلِفِزْيُون",
    "تليفون": "تِلِفُون",
    "جنبي": "جَنْبِي",
    "لو": "لَوْ",
    "سمحت": "سَمَحْت"
}


class TTSService:
    """Async Dual-Mode (Online + Offline Egyptian/English) TTS with RAM & Disk cache."""

    def __init__(
        self,
        max_cache_items: int = 512,
        mode: TTSMode | None = None,
        models_dir: str | Path | None = None,
        enable_disk_cache: bool = True,
        elevenlabs_api_key: str | None = None,
        elevenlabs_model_id: str | None = None,
    ) -> None:
        self.max_cache_items = max_cache_items
        raw_mode = (mode or os.getenv("TTS_MODE", "auto")).strip().lower()
        self.mode: TTSMode = (
            raw_mode if raw_mode in ("auto", "offline", "online") else "auto"
        )  # type: ignore[assignment]
        self.models_dir = Path(models_dir) if models_dir else DEFAULT_MODELS_DIR
        self.enable_disk_cache = enable_disk_cache
        self._disk_cache_dir = self.models_dir / "cache"
        self._cache: OrderedDict[tuple[str, str, str], bytes] = OrderedDict()
        self._cache_voices: dict[tuple[str, str, str], str] = {}
        self._piper_voices: dict[str, object] = {}
        self._piper_lock = threading.Lock()
        self.elevenlabs_api_key = (
            elevenlabs_api_key
            if elevenlabs_api_key is not None
            else os.getenv("ELEVENLABS_API_KEY", "")
        ).strip()
        self.elevenlabs_model_id = (
            elevenlabs_model_id
            if elevenlabs_model_id is not None
            else os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
        ).strip() or "eleven_flash_v2_5"
        self.elevenlabs_voice_ar = os.getenv("ELEVENLABS_VOICE_ID_AR", "").strip()
        self.elevenlabs_voice_en = os.getenv("ELEVENLABS_VOICE_ID_EN", "").strip()

    @property
    def is_elevenlabs_configured(self) -> bool:
        return bool(self.elevenlabs_api_key)

    def _resolve_elevenlabs_voice(
        self, lang: Literal["ar", "en"], gender: Gender = "male"
    ) -> tuple[str, str]:
        if lang == "ar" and self.elevenlabs_voice_ar:
            return self.elevenlabs_voice_ar, f"ElevenLabs-{self.elevenlabs_voice_ar[:8]} (ar-EG)"
        if lang == "en" and self.elevenlabs_voice_en:
            return self.elevenlabs_voice_en, f"ElevenLabs-{self.elevenlabs_voice_en[:8]} (en-US)"
        return ELEVENLABS_VOICE_MAP[(lang, gender)]

    @staticmethod
    def detect_language(text: str, lang: Language = "auto") -> Literal["ar", "en"]:
        """Resolve 'auto' to 'ar' if Arabic script is present, otherwise 'en'."""
        if lang == "ar":
            return "ar"
        if lang == "en":
            return "en"
        return "ar" if ARABIC_CHAR_RE.search(text or "") else "en"

    @staticmethod
    def normalize_rate(rate: str | None) -> str:
        """Validate speaking rate string (e.g. '-15%', '+0%', '+20%')."""
        cleaned = (rate or "+0%").strip()
        if not RATE_RE.match(cleaned):
            raise ValueError(
                f"Invalid speech rate '{rate}'. Expected format like '+0%', '-15%', or '+20%'."
            )
        return cleaned

    @staticmethod
    def _rate_to_speed_factor(norm_rate: str) -> float:
        pct = int(norm_rate.replace("%", ""))
        return max(0.5, min(2.0, 1.0 + pct / 100.0))

    @classmethod
    def _rate_to_length_scale(cls, norm_rate: str) -> float:
        """Convert '+20%' / '-15%' into Piper length_scale (>1 slower, <1 faster)."""
        return round(1.0 / cls._rate_to_speed_factor(norm_rate), 3)

    def select_voice(
        self,
        text: str,
        lang: Language = "auto",
        gender: Gender = "male",
    ) -> tuple[Literal["ar", "en"], str]:
        """Pick the matching voice ID for language and gender (default: male)."""
        resolved_lang = self.detect_language(text, lang)
        resolved_gender: Gender = "female" if gender == "female" else "male"
        if self.mode == "offline":
            return resolved_lang, OFFLINE_VOICE_MAP[resolved_lang]
        voice_id = ONLINE_VOICE_MAP[(resolved_lang, resolved_gender)]
        return resolved_lang, voice_id

    @staticmethod
    def list_voices() -> list[dict]:
        """Return available Egyptian/English voices across ElevenLabs, Edge, WinRT, and Piper."""
        return [
            {
                "engine": "elevenlabs",
                "lang": "ar",
                "locale": "ar-EG",
                "gender": "male",
                "voice": "ElevenLabs-Adam (ar)",
                "offline": False,
            },
            {
                "engine": "elevenlabs",
                "lang": "en",
                "locale": "en-US",
                "gender": "male",
                "voice": "ElevenLabs-George (en-US)",
                "offline": False,
            },
            {
                "engine": "edge-tts",
                "lang": "ar",
                "locale": "ar-EG",
                "gender": "female",
                "voice": ONLINE_VOICE_MAP[("ar", "female")],
                "offline": False,
            },
            {
                "engine": "edge-tts",
                "lang": "ar",
                "locale": "ar-EG",
                "gender": "male",
                "voice": ONLINE_VOICE_MAP[("ar", "male")],
                "offline": False,
            },
            {
                "engine": "edge-tts",
                "lang": "en",
                "locale": "en-US",
                "gender": "female",
                "voice": ONLINE_VOICE_MAP[("en", "female")],
                "offline": False,
            },
            {
                "engine": "edge-tts",
                "lang": "en",
                "locale": "en-US",
                "gender": "male",
                "voice": ONLINE_VOICE_MAP[("en", "male")],
                "offline": False,
            },
            {
                "engine": "windows-winrt",
                "lang": "ar",
                "locale": "ar-EG",
                "gender": "female",
                "voice": "Microsoft Hoda (ar-EG)",
                "offline": True,
            },
            {
                "engine": "mms-onnx-offline",
                "lang": "ar",
                "locale": "ar",
                "gender": "male",
                "voice": OFFLINE_VOICE_MAP["ar"],
                "offline": True,
            },
            {
                "engine": "piper-offline",
                "lang": "en",
                "locale": "en-US",
                "gender": "male",
                "voice": OFFLINE_VOICE_MAP["en"],
                "offline": True,
            },
        ]

    def offline_models_status(self) -> dict:
        """Report local readiness of Piper ONNX models, Windows Egyptian voice, and disk cache."""
        cached_files = (
            len(list(self._disk_cache_dir.glob("*.mp3")))
            if self._disk_cache_dir.exists()
            else 0
        )
        el_cached_files = (
            len(list(self._disk_cache_dir.glob("el_*.mp3")))
            if self._disk_cache_dir.exists()
            else 0
        )
        return {
            "piper_ar": (self.models_dir / f"{OFFLINE_VOICE_MAP['ar']}.onnx").exists()
            and (self.models_dir / f"{OFFLINE_VOICE_MAP['ar']}.onnx.json").exists(),
            "piper_en": (self.models_dir / f"{OFFLINE_VOICE_MAP['en']}.onnx").exists()
            and (self.models_dir / f"{OFFLINE_VOICE_MAP['en']}.onnx.json").exists(),
            "windows_egyptian_ar_eg": self.has_windows_egyptian_voice(),
            "disk_cached_elevenlabs_phrases": el_cached_files,
            "disk_cached_egyptian_phrases": cached_files,
        }

    @staticmethod
    def has_windows_egyptian_voice() -> bool:
        """Check if Windows WinRT has Arabic (Egypt) 'Microsoft Hoda' installed."""
        if sys.platform != "win32":
            return False
        try:
            from winrt.windows.media.speechsynthesis import SpeechSynthesizer

            return any(
                v.language.lower().startswith("ar-eg")
                for v in SpeechSynthesizer.all_voices
            )
        except Exception:
            return False

    def ensure_offline_model(self, lang: Literal["ar", "en"]) -> Path:
        """Ensure the local offline ONNX voice file exists, downloading once if missing."""
        voice_name = OFFLINE_VOICE_MAP[lang]
        self.models_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.models_dir / f"{voice_name}.onnx"
        config_path = self.models_dir / f"{voice_name}.onnx.json"

        if not (model_path.exists() and model_path.stat().st_size > 1000 and config_path.exists()):
            try:
                if lang == "ar":
                    import httpx

                    cfg_resp = httpx.get(
                        MMS_AR_CONFIG_URL, follow_redirects=True, timeout=30.0
                    )
                    cfg_resp.raise_for_status()
                    config_path.write_bytes(cfg_resp.content)

                    tmp_path = model_path.with_suffix(".onnx.tmp")
                    with httpx.stream(
                        "GET", MMS_AR_MODEL_URL, follow_redirects=True, timeout=180.0
                    ) as resp:
                        resp.raise_for_status()
                        with open(tmp_path, "wb") as fh:
                            for chunk in resp.iter_bytes():
                                fh.write(chunk)
                    tmp_path.replace(model_path)
                else:
                    from piper.download_voices import download_voice

                    download_voice(voice_name, self.models_dir)
            except Exception as exc:
                raise RuntimeError(
                    f"Offline voice model '{voice_name}' is not downloaded yet in "
                    f"'{self.models_dir}' and could not be downloaded ({exc}). "
                    "Connect to internet once and run: python -B -m modules.TTS.tts_service"
                ) from exc

        return model_path

    def _get_piper_voice(self, lang: Literal["ar", "en"]):
        """Load and cache the local ONNX inference session (MMS for AR, Piper for EN)."""
        voice_name = OFFLINE_VOICE_MAP[lang]
        with self._piper_lock:
            if voice_name not in self._piper_voices:
                model_path = self.ensure_offline_model(lang)
                if lang == "ar":
                    import json
                    import onnxruntime as ort

                    cfg_path = self.models_dir / f"{voice_name}.onnx.json"
                    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                    sess = ort.InferenceSession(
                        str(model_path), providers=["CPUExecutionProvider"]
                    )
                    self._piper_voices[voice_name] = (sess, cfg)
                else:
                    from piper.voice import PiperVoice

                    self._piper_voices[voice_name] = PiperVoice.load(model_path)
            return self._piper_voices[voice_name]

    @staticmethod
    def _apply_egyptian_hints(text: str) -> str:
        return re.sub(r"[\u0621-\u064A]+", lambda m: EGYPTIAN_PIPER_HINTS.get(m.group(0), m.group(0)), text)

    def _synthesize_piper_sync(
        self, text: str, lang: Literal["ar", "en"], rate: str
    ) -> bytes:
        """Run local ONNX synthesis synchronously (MMS-Arabic for AR, Piper for EN)."""
        if lang == "ar":
            import numpy as np

            sess, cfg = self._get_piper_voice("ar")
            pmap: dict[str, int] = cfg.get("phoneme_id_map", {})
            cleaned = AR_DIACRITICS_RE.sub("", text).strip()
            ids = [0]
            for ch in cleaned:
                if ch in pmap:
                    ids.extend([pmap[ch], 0])
            if len(ids) <= 1:
                ids = [0, pmap.get(" ", 25), 0]

            x = np.array([ids], dtype=np.int64)
            x_len = np.array([len(ids)], dtype=np.int64)
            inf_cfg = cfg.get("inference", {})
            y = sess.run(
                None,
                {
                    "x": x,
                    "x_length": x_len,
                    "noise_scale": np.array(
                        [float(inf_cfg.get("noise_scale", 0.667))], dtype=np.float32
                    ),
                    "length_scale": np.array(
                        [self._rate_to_length_scale(rate)], dtype=np.float32
                    ),
                    "noise_scale_w": np.array(
                        [float(inf_cfg.get("noise_w", 0.8))], dtype=np.float32
                    ),
                },
            )[0]
            audio = np.clip(y.squeeze(), -1.0, 1.0)
            pcm = (audio * 32767.0).astype(np.int16)
            sample_rate = int(cfg.get("audio", {}).get("sample_rate", 16000))
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm.tobytes())
            wav_bytes = buf.getvalue()
            if len(wav_bytes) <= 44:
                raise RuntimeError("Offline Arabic ONNX TTS produced empty audio.")
            return wav_bytes

        from piper.config import SynthesisConfig

        voice = self._get_piper_voice(lang)
        syn_cfg = SynthesisConfig(length_scale=self._rate_to_length_scale(rate))
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            voice.synthesize_wav(text, wf, syn_config=syn_cfg)
        wav_bytes = buf.getvalue()
        if len(wav_bytes) <= 44:
            raise RuntimeError("Offline Piper TTS produced empty audio.")
        return wav_bytes

    async def _synthesize_winrt_bytes(
        self,
        text: str,
        lang: Literal["ar", "en"],
        gender: Gender,
        rate: str,
    ) -> bytes | None:
        """Use Windows built-in WinRT SpeechSynthesizer (Egyptian ar-EG Hoda / English Zira)."""
        if sys.platform != "win32":
            return None
        try:
            from winrt.windows.media.speechsynthesis import (
                SpeechSynthesizer,
                VoiceGender,
            )
            from winrt.windows.storage.streams import DataReader
        except ImportError:
            return None

        voices = list(SpeechSynthesizer.all_voices)
        if lang == "ar":
            # Strictly look for Egyptian Arabic (ar-EG) so offline Arabic speaks Egyptian
            candidates = [v for v in voices if v.language.lower().startswith("ar-eg")]
        else:
            candidates = [v for v in voices if v.language.lower().startswith("en")]

        if not candidates:
            return None

        target_gender = VoiceGender.MALE if gender == "male" else VoiceGender.FEMALE
        chosen = next((v for v in candidates if v.gender == target_gender), None)
        if chosen is None:
            return None

        with SpeechSynthesizer() as synth:
            synth.voice = chosen
            synth.options.speaking_rate = self._rate_to_speed_factor(rate)
            stream = await synth.synthesize_text_to_stream_async(text)
            size = int(stream.size)
            if size <= 44:
                return None
            reader = DataReader(stream.get_input_stream_at(0))
            await reader.load_async(size)
            buf = bytearray(size)
            reader.read_bytes(buf)
            return bytes(buf)

    async def _synthesize_edge_bytes(self, text: str, voice: str, rate: str) -> bytes:
        import edge_tts

        spoken_text = self._apply_egyptian_hints(text) if voice.startswith("ar-EG-") else text
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                communicate = edge_tts.Communicate(text=spoken_text, voice=voice, rate=rate)
                chunks: list[bytes] = []
                async for chunk in communicate.stream():
                    if chunk.get("type") == "audio":
                        chunks.append(chunk["data"])
                audio_bytes = b"".join(chunks)
                if audio_bytes:
                    return audio_bytes
                last_err = RuntimeError("Edge TTS engine returned empty audio stream.")
            except Exception as exc:
                last_err = exc
                if attempt < 2:
                    await asyncio.sleep(0.35)
        raise last_err or RuntimeError("Edge TTS engine returned empty audio stream.")

    async def _synthesize_elevenlabs_bytes(
        self,
        text: str,
        voice_id: str,
        rate: str,
        lang: Literal["ar", "en"] = "ar",
    ) -> bytes:
        """Synthesize natural Arabic/English MP3 bytes via ElevenLabs REST API."""
        if not self.elevenlabs_api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not configured.")
        import httpx

        speed = max(0.7, min(1.2, self._rate_to_speed_factor(rate)))
        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            "?output_format=mp3_44100_128"
        )
        headers = {
            "xi-api-key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": self.elevenlabs_model_id,
            "language_code": lang,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "speed": round(speed, 2),
            },
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            audio_bytes = resp.content
        if not audio_bytes or len(audio_bytes) < 100:
            raise RuntimeError("ElevenLabs returned empty audio stream.")
        return audio_bytes

    def _elevenlabs_cache_path(
        self,
        text: str,
        lang: Literal["ar", "en"],
        gender: Gender,
        rate: str,
        voice_id: str,
    ) -> Path:
        digest = hashlib.sha256(
            f"{lang}|{gender}|{rate}|{text}".encode("utf-8")
        ).hexdigest()[:20]
        safe_vid = re.sub(r"[^A-Za-z0-9_-]", "", voice_id)[:24] or "el"
        return self._disk_cache_dir / f"el_{safe_vid}_{digest}.mp3"

    def _read_elevenlabs_disk_cache(
        self, text: str, lang: Literal["ar", "en"], gender: Gender, rate: str
    ) -> tuple[bytes, str] | None:
        if not self.enable_disk_cache:
            return None
        voice_id, voice_label = self._resolve_elevenlabs_voice(lang, gender)
        for candidate in (text, text.rstrip(".!؟?,،؛ ")):
            if not candidate:
                continue
            exact = self._elevenlabs_cache_path(candidate, lang, gender, rate, voice_id)
            if exact.exists() and exact.stat().st_size > 100:
                return exact.read_bytes(), voice_label
        return None

    def _write_elevenlabs_disk_cache(
        self,
        text: str,
        lang: Literal["ar", "en"],
        gender: Gender,
        rate: str,
        voice_id: str,
        audio_bytes: bytes,
    ) -> None:
        if not self.enable_disk_cache or not audio_bytes or audio_bytes.startswith(b"RIFF"):
            return
        self._disk_cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._elevenlabs_cache_path(text, lang, gender, rate, voice_id)
        path.write_bytes(audio_bytes)

    def _disk_cache_path(
        self, text: str, lang: Literal["ar", "en"], gender: Gender, rate: str
    ) -> Path:
        digest = hashlib.sha256(
            f"{lang}|{gender}|{rate}|{text}".encode("utf-8")
        ).hexdigest()[:24]
        return self._disk_cache_dir / f"{digest}.mp3"

    def _read_disk_cache(
        self, text: str, lang: Literal["ar", "en"], gender: Gender, rate: str
    ) -> bytes | None:
        if not self.enable_disk_cache:
            return None
        for candidate in (text, text.rstrip(".!؟?,،؛ ")):
            if not candidate:
                continue
            path = self._disk_cache_path(candidate, lang, gender, rate)
            if path.exists() and path.stat().st_size > 100:
                return path.read_bytes()
        return None

    def _write_disk_cache(
        self,
        text: str,
        lang: Literal["ar", "en"],
        gender: Gender,
        rate: str,
        audio_bytes: bytes,
    ) -> None:
        if not self.enable_disk_cache or audio_bytes.startswith(b"RIFF"):
            return
        self._disk_cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._disk_cache_path(text, lang, gender, rate)
        path.write_bytes(audio_bytes)

    async def _synthesize_offline_fallback(
        self, text: str, lang: Literal["ar", "en"], gender: Gender, rate: str
    ) -> bytes:
        """Try Windows Egyptian/English WinRT voice first, then Piper Neural ONNX."""
        winrt_bytes = await self._synthesize_winrt_bytes(text, lang, gender, rate)
        if winrt_bytes:
            return winrt_bytes
        return await asyncio.to_thread(self._synthesize_piper_sync, text, lang, rate)

    async def _synthesize_bytes(
        self,
        text: str,
        voice: str,
        rate: str,
        lang: Literal["ar", "en"] = "ar",
        gender: Gender = "male",
    ) -> bytes:
        """Synthesize audio bytes according to mode ('auto', 'offline', or 'online')."""
        if self.mode == "offline":
            return await self._synthesize_offline_fallback(text, lang, gender, rate)

        if self.mode == "online":
            return await self._synthesize_edge_bytes(text, voice, rate)

        # mode == 'auto': try Egyptian/English Edge TTS online first, fallback offline
        try:
            return await asyncio.wait_for(
                self._synthesize_edge_bytes(text, voice, rate),
                timeout=15.0,
            )
        except Exception:
            return await self._synthesize_offline_fallback(text, lang, gender, rate)

    @staticmethod
    def _detect_mime_type(audio_bytes: bytes) -> str:
        return "audio/wav" if audio_bytes.startswith(b"RIFF") else "audio/mpeg"

    async def synthesize(
        self,
        text: str,
        lang: Language = "auto",
        gender: Gender = "male",
        rate: str = "+0%",
    ) -> dict:
        """Synthesize spoken audio bytes (ElevenLabs Haytham -> Edge Shakir -> WinRT -> Piper)."""
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise ValueError("Text for speech synthesis must not be empty.")

        norm_rate = self.normalize_rate(rate)
        resolved_gender: Gender = "female" if gender == "female" else "male"
        resolved_lang, voice = self.select_voice(cleaned_text, lang, resolved_gender)
        cache_key = (cleaned_text, f"{resolved_lang}:{resolved_gender}", norm_rate)
        el_voice_id, el_voice_label = self._resolve_elevenlabs_voice(
            resolved_lang, resolved_gender
        )

        audio_bytes: bytes | None = None
        actual_voice: str = ""
        cached = False

        if cache_key in self._cache:
            cached_voice = self._cache_voices.get(cache_key, "")
            # If ElevenLabs was newly enabled and this RAM entry is from an older tier, upgrade it
            if not (
                self.is_elevenlabs_configured
                and self.mode != "offline"
                and not cached_voice.startswith("ElevenLabs")
            ) or (
                self.mode != "offline"
                and self._detect_mime_type(self._cache[cache_key]) == "audio/wav"
            ):
                self._cache.move_to_end(cache_key)
                audio_bytes = self._cache[cache_key]
                actual_voice = cached_voice or (
                    ONLINE_VOICE_MAP[(resolved_lang, resolved_gender)]
                    if self._detect_mime_type(audio_bytes) == "audio/mpeg"
                    else OFFLINE_VOICE_MAP[resolved_lang]
                )
                cached = True

        if audio_bytes is None:
            # 1. Always prefer pre-cached ElevenLabs Haytham MP3 on disk (works 100% offline too)
            el_disk = self._read_elevenlabs_disk_cache(
                cleaned_text, resolved_lang, resolved_gender, norm_rate
            )
            if el_disk is not None:
                audio_bytes, actual_voice = el_disk
                cached = True

        if audio_bytes is None and self.is_elevenlabs_configured and self.mode != "offline":
            # 2. Live ElevenLabs API call -> auto-saved permanently to disk cache
            try:
                audio_bytes = await self._synthesize_elevenlabs_bytes(
                    cleaned_text, el_voice_id, norm_rate, resolved_lang
                )
                self._write_elevenlabs_disk_cache(
                    cleaned_text,
                    resolved_lang,
                    resolved_gender,
                    norm_rate,
                    el_voice_id,
                    audio_bytes,
                )
                actual_voice = el_voice_label
                cached = False
            except Exception:
                audio_bytes = None

        if audio_bytes is None:
            # 3. Edge disk cache -> Live Edge / Offline WinRT / Piper fallback
            disk_bytes = self._read_disk_cache(
                cleaned_text, resolved_lang, resolved_gender, norm_rate
            )
            if disk_bytes is not None:
                audio_bytes = disk_bytes
                cached = True
            else:
                audio_bytes = await self._synthesize_bytes(
                    cleaned_text, voice, norm_rate, resolved_lang, resolved_gender
                )
                self._write_disk_cache(
                    cleaned_text, resolved_lang, resolved_gender, norm_rate, audio_bytes
                )
                cached = False

            mime_tmp = self._detect_mime_type(audio_bytes)
            actual_voice = (
                ONLINE_VOICE_MAP[(resolved_lang, resolved_gender)]
                if mime_tmp == "audio/mpeg"
                else OFFLINE_VOICE_MAP[resolved_lang]
            )

        self._cache[cache_key] = audio_bytes
        self._cache_voices[cache_key] = actual_voice
        if len(self._cache) > self.max_cache_items:
            evicted_key, _ = self._cache.popitem(last=False)
            self._cache_voices.pop(evicted_key, None)

        mime_type = self._detect_mime_type(audio_bytes)
        return {
            "text": cleaned_text,
            "language": resolved_lang,
            "voice": actual_voice,
            "rate": norm_rate,
            "mime_type": mime_type,
            "bytes_count": len(audio_bytes),
            "cached": cached,
            "audio_bytes": audio_bytes,
        }

    async def synthesize_base64(
        self,
        text: str,
        lang: Language = "auto",
        gender: Gender = "male",
        rate: str = "+0%",
    ) -> dict:
        """Synthesize audio and return JSON-safe base64 payload."""
        result = await self.synthesize(text=text, lang=lang, gender=gender, rate=rate)
        b64 = base64.b64encode(result["audio_bytes"]).decode("ascii")
        return {
            "text": result["text"],
            "language": result["language"],
            "voice": result["voice"],
            "rate": result["rate"],
            "mime_type": result["mime_type"],
            "bytes_count": result["bytes_count"],
            "cached": result["cached"],
            "audio_base64": b64,
        }

    def warmup_offline(self, phrases: list[str] | None = None) -> dict:
        """Pre-load downloaded Piper models and disk-cached Egyptian phrases into RAM."""
        status = self.offline_models_status()
        warmed_langs: list[str] = []
        warmed_phrases = 0

        for lang in ("ar", "en"):
            if status.get(f"piper_{lang}"):
                try:
                    self._get_piper_voice(lang)
                    warmed_langs.append(lang)
                except Exception:
                    pass

        for phrase in phrases if phrases is not None else DEFAULT_WARMUP_PHRASES:
            cleaned = (phrase or "").strip()
            if not cleaned:
                continue
            lang = self.detect_language(cleaned, "auto")
            cache_key = (cleaned, f"{lang}:male", "+0%")
            if cache_key in self._cache:
                continue

            # 1. Prefer pre-cached ElevenLabs MP3 on disk first
            el_disk = self._read_elevenlabs_disk_cache(cleaned, lang, "male", "+0%")
            if el_disk is not None:
                self._cache[cache_key] = el_disk[0]
                self._cache_voices[cache_key] = el_disk[1]
                warmed_phrases += 1
            else:
                # 2. Then Edge ShakirNeural MP3 on disk
                disk_bytes = self._read_disk_cache(cleaned, lang, "male", "+0%")
                if disk_bytes is not None:
                    self._cache[cache_key] = disk_bytes
                    self._cache_voices[cache_key] = ONLINE_VOICE_MAP[(lang, "male")]
                    warmed_phrases += 1
                elif lang in warmed_langs:
                    try:
                        self._cache[cache_key] = self._synthesize_piper_sync(
                            cleaned, lang, "+0%"
                        )
                        self._cache_voices[cache_key] = OFFLINE_VOICE_MAP[lang]
                        warmed_phrases += 1
                    except Exception:
                        pass

            if len(self._cache) > self.max_cache_items:
                evicted_key, _ = self._cache.popitem(last=False)
                self._cache_voices.pop(evicted_key, None)

        return {"warmed_langs": warmed_langs, "warmed_phrases": warmed_phrases}


def _load_env_file() -> None:
    root = Path(__file__).resolve().parents[2]
    env_path = root / ".env"
    if not env_path.exists() and (root / ".env.txt").exists():
        env_path = root / ".env.txt"
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


async def _setup_async() -> None:
    """Remove old Kareem model, keep English Piper backup, and pre-cache natural voices."""
    _load_env_file()

    service = TTSService(mode="auto")
    print(f"[TTS Setup] Models folder: {service.models_dir}")

    # Remove ar_JO-kareem* files so the old robotic Jordanian voice is never kept
    removed = 0
    if service.models_dir.exists():
        for old_file in service.models_dir.glob("ar_JO-kareem*"):
            try:
                old_file.unlink()
                removed += 1
            except Exception:
                pass
    if removed:
        print(f" -> Removed {removed} old 'ar_JO-kareem' file(s).")

    # Prepare offline ONNX backup models (MMS Male Arabic + Ryan Male English — never Kareem)
    for lang in ("ar", "en"):
        voice_name = OFFLINE_VOICE_MAP[lang]
        print(f" -> Preparing offline ONNX backup ({lang.upper()}: {voice_name})...")
        try:
            model_path = service.ensure_offline_model(lang)
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"    Ready: {model_path.name} ({size_mb:.1f} MB)")
        except Exception as exc:
            print(f"    Skipped {lang.upper()} ONNX backup ({exc})")

    if service.is_elevenlabs_configured:
        print(
            f" -> ELEVENLABS_API_KEY detected! Pre-caching {len(DEFAULT_WARMUP_PHRASES)} core "
            "Egyptian/English phrases with ElevenLabs (Adam ar / George en-US)..."
        )
        sem = asyncio.Semaphore(2)
        last_err: list[str] = []

        async def _cache_el_one(phrase: str) -> bool:
            lang = service.detect_language(phrase, "auto")
            if service._read_elevenlabs_disk_cache(phrase, lang, "male", "+0%") is not None:
                return True
            el_vid, _ = service._resolve_elevenlabs_voice(lang, "male")
            async with sem:
                for attempt in range(2):
                    try:
                        mp3 = await service._synthesize_elevenlabs_bytes(
                            phrase, el_vid, "+0%", lang
                        )
                        service._write_elevenlabs_disk_cache(
                            phrase, lang, "male", "+0%", el_vid, mp3
                        )
                        return True
                    except Exception as exc:
                        if attempt == 0:
                            await asyncio.sleep(0.5)
                        elif not last_err:
                            last_err.append(str(exc))
            return False

        el_results = await asyncio.gather(*(_cache_el_one(p) for p in DEFAULT_WARMUP_PHRASES))
        el_ok = sum(1 for r in el_results if r)
        print(
            f"    ElevenLabs Cache ready: {el_ok}/{len(DEFAULT_WARMUP_PHRASES)} phrases "
            "(100% offline replay, 0 repeated credits!)."
        )
        if el_ok == 0 and last_err:
            print(f"    [Warning] ElevenLabs request error: {last_err[0]}")

    # Also ensure Edge ShakirNeural (ar-EG) disk cache is populated as free Egyptian backup
    print(
        f" -> Ensuring free Egyptian backup cache ({len(DEFAULT_WARMUP_PHRASES)} phrases "
        "with ar-EG-ShakirNeural / en-US-GuyNeural)..."
    )
    sem_edge = asyncio.Semaphore(3)

    async def _cache_one(phrase: str) -> bool:
        lang = service.detect_language(phrase, "auto")
        if service._read_disk_cache(phrase, lang, "male", "+0%") is not None:
            return True
        voice = ONLINE_VOICE_MAP[(lang, "male")]
        async with sem_edge:
            for attempt in range(2):
                try:
                    mp3 = await service._synthesize_edge_bytes(phrase, voice, "+0%")
                    service._write_disk_cache(phrase, lang, "male", "+0%", mp3)
                    return True
                except Exception:
                    if attempt == 0:
                        await asyncio.sleep(0.3)
        return False

    results = await asyncio.gather(*(_cache_one(p) for p in DEFAULT_WARMUP_PHRASES))
    ok_count = sum(1 for r in results if r)
    print(f"    Egyptian Shakir Backup Cache ready: {ok_count}/{len(DEFAULT_WARMUP_PHRASES)} phrases.")

    print("[TTS Setup] Done! Kareem removed and natural voices are cached and ready.")


def setup_offline_models() -> None:
    asyncio.run(_setup_async())


if __name__ == "__main__":
    setup_offline_models()
