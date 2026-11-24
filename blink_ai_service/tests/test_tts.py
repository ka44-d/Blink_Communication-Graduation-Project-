"""Unit and API tests for the TTS module (tts_service.py + tts_router.py + main.py)."""

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from main import app
from modules.TTS.tts_service import TTSService


class TestTTSService(unittest.TestCase):
    def setUp(self) -> None:
        self.tts_offline = TTSService(
            max_cache_items=10, mode="offline", enable_disk_cache=False
        )
        self.tts_online = TTSService(
            max_cache_items=10, mode="online", enable_disk_cache=False
        )
        self.tts_auto = TTSService(
            max_cache_items=10, mode="auto", enable_disk_cache=False
        )

    def test_language_auto_detection(self) -> None:
        self.assertEqual(self.tts_auto.detect_language("انا عايز اشرب ميه", "auto"), "ar")
        self.assertEqual(self.tts_auto.detect_language("I want water", "auto"), "en")
        self.assertEqual(self.tts_auto.detect_language("hello", "ar"), "ar")

    def test_voice_selection_offline_and_online(self) -> None:
        self.assertEqual(
            self.tts_offline.select_voice("السلام عليكم", "auto"),
            ("ar", "mms-tts-ara"),
        )
        self.assertEqual(
            self.tts_offline.select_voice("Hello doctor", "auto"),
            ("en", "en_US-ryan-medium"),
        )
        # Default voice must be male Egyptian (Shakir) / English male (Guy)
        self.assertEqual(
            self.tts_online.select_voice("السلام عليكم", "auto"),
            ("ar", "ar-EG-ShakirNeural"),
        )
        self.assertEqual(
            self.tts_online.select_voice("Hello doctor", "auto"),
            ("en", "en-US-GuyNeural"),
        )
        self.assertEqual(
            self.tts_online.select_voice("السلام عليكم", "auto", "female"),
            ("ar", "ar-EG-SalmaNeural"),
        )
        self.assertEqual(
            self.tts_online.select_voice("Hello doctor", "auto", "female"),
            ("en", "en-US-JennyNeural"),
        )

    def test_rate_validation_and_piper_scale(self) -> None:
        self.assertEqual(self.tts_offline.normalize_rate("-15%"), "-15%")
        self.assertEqual(self.tts_offline.normalize_rate("+10%"), "+10%")
        self.assertEqual(self.tts_offline._rate_to_length_scale("+0%"), 1.0)
        self.assertGreater(self.tts_offline._rate_to_length_scale("-20%"), 1.0)
        self.assertLess(self.tts_offline._rate_to_length_scale("+25%"), 1.0)
        with self.assertRaises(ValueError):
            self.tts_offline.normalize_rate("fast")

    def test_lru_cache_hit_avoids_second_synthesis_call(self) -> None:
        fake_wav = b"RIFF" + b"\x00" * 100
        with patch.object(
            self.tts_offline, "_synthesize_bytes", new=AsyncMock(return_value=fake_wav)
        ) as mock_synth:
            first = asyncio.run(self.tts_offline.synthesize("انا عايز ميه", lang="ar"))
            second = asyncio.run(self.tts_offline.synthesize("انا عايز ميه", lang="ar"))
            self.assertFalse(first["cached"])
            self.assertTrue(second["cached"])
            self.assertEqual(first["mime_type"], "audio/wav")
            self.assertEqual(first["audio_bytes"], fake_wav)
            self.assertEqual(mock_synth.await_count, 1)

    def test_persistent_disk_cache_replays_egyptian_offline(self) -> None:
        fake_mp3 = b"\xff\xf3d\xc4" + b"\x00" * 150
        with tempfile.TemporaryDirectory() as tmp:
            s1 = TTSService(mode="auto", models_dir=tmp, enable_disk_cache=True)
            with patch.object(
                s1, "_synthesize_bytes", new=AsyncMock(return_value=fake_mp3)
            ):
                r1 = asyncio.run(s1.synthesize("الترفيه", lang="ar"))
                self.assertFalse(r1["cached"])

            # Fresh offline instance with no internet reads Egyptian Male MP3 from disk cache
            s2 = TTSService(mode="offline", models_dir=tmp, enable_disk_cache=True)
            r2 = asyncio.run(s2.synthesize("الترفيه", lang="ar"))
            self.assertTrue(r2["cached"])
            self.assertEqual(r2["mime_type"], "audio/mpeg")
            self.assertEqual(r2["voice"], "ar-EG-ShakirNeural")
            self.assertEqual(r2["audio_bytes"], fake_mp3)

    def test_elevenlabs_egyptian_caches_and_replays_offline_plus_fallback(self) -> None:
        fake_el_mp3 = b"ID3" + b"\x22" * 150
        fake_edge_mp3 = b"\xff\xf3d\xc4" + b"\x33" * 150
        with tempfile.TemporaryDirectory() as tmp:
            # 1. Online with ElevenLabs key -> saves Haytham MP3 permanently to disk cache
            s1 = TTSService(
                mode="auto",
                models_dir=tmp,
                enable_disk_cache=True,
                elevenlabs_api_key="el-test-key",
            )
            with patch.object(
                s1,
                "_synthesize_elevenlabs_bytes",
                new=AsyncMock(return_value=fake_el_mp3),
            ) as mock_el:
                r1 = asyncio.run(s1.synthesize("انا عايز اشرب ميه", lang="ar"))
                self.assertFalse(r1["cached"])
                self.assertEqual(r1["voice"], "ElevenLabs-Adam (ar)")
                self.assertEqual(r1["audio_bytes"], fake_el_mp3)
                self.assertEqual(mock_el.await_count, 1)

            # 2. Offline with NO API key & NO internet -> replays cached MP3 in 0.5 ms
            s_off = TTSService(
                mode="offline",
                models_dir=tmp,
                enable_disk_cache=True,
                elevenlabs_api_key="",
            )
            r2 = asyncio.run(s_off.synthesize("انا عايز اشرب ميه", lang="ar"))
            self.assertTrue(r2["cached"])
            self.assertEqual(r2["voice"], "ElevenLabs-Adam (ar)")
            self.assertEqual(r2["audio_bytes"], fake_el_mp3)

            # 3. If ElevenLabs fails (e.g. quota finished), gracefully falls back to Edge
            with patch.object(
                s1,
                "_synthesize_elevenlabs_bytes",
                new=AsyncMock(side_effect=RuntimeError("Quota exceeded")),
            ), patch.object(
                s1,
                "_synthesize_bytes",
                new=AsyncMock(return_value=fake_edge_mp3),
            ):
                r3 = asyncio.run(s1.synthesize("جملة جديدة تماما", lang="ar"))
                self.assertEqual(r3["voice"], "ar-EG-ShakirNeural")
                self.assertEqual(r3["audio_bytes"], fake_edge_mp3)

    def test_auto_mode_falls_back_to_offline_when_network_fails(self) -> None:
        fake_wav = b"RIFF" + b"\x11" * 100
        with patch.object(
            self.tts_auto,
            "_synthesize_edge_bytes",
            new=AsyncMock(side_effect=RuntimeError("No internet")),
        ), patch.object(
            self.tts_auto,
            "_synthesize_offline_fallback",
            new=AsyncMock(return_value=fake_wav),
        ) as mock_off:
            res = asyncio.run(self.tts_auto.synthesize("انا عايز ميه", lang="ar"))
            self.assertEqual(res["mime_type"], "audio/wav")
            self.assertEqual(res["audio_bytes"], fake_wav)
            mock_off.assert_awaited_once()

    def test_offline_piper_synthesis_if_models_present(self) -> None:
        """Run real 100% offline Piper synthesis if models are already downloaded."""
        svc = TTSService(mode="offline", enable_disk_cache=False)
        status = svc.offline_models_status()
        if not (status["piper_ar"] and status["piper_en"]):
            self.skipTest(
                "Offline Piper models not yet in modules/TTS/voices/; run `python -B -m modules.TTS.tts_service` once."
            )
        res_ar = asyncio.run(svc.synthesize("انا عايز اشرب ميه", lang="ar"))
        res_en = asyncio.run(svc.synthesize("I need water please", lang="en"))
        self.assertEqual(res_ar["mime_type"], "audio/wav")
        self.assertEqual(res_en["mime_type"], "audio/wav")
        self.assertGreater(res_ar["bytes_count"], 5000)
        self.assertGreater(res_en["bytes_count"], 5000)


class TestTTSAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("TTS", data["active_modules"])

    def test_tts_health_and_voices(self) -> None:
        h = self.client.get("/api/tts/health")
        self.assertEqual(h.status_code, 200)
        body = h.json()
        self.assertEqual(body["module"], "TTS")
        self.assertIn(body["mode"], ("auto", "offline", "online"))
        self.assertIn("offline_models_ready", body)

        v = self.client.get("/api/tts/voices")
        self.assertEqual(v.status_code, 200)
        self.assertEqual(len(v.json()["voices"]), 9)

    def test_tts_speak_and_base64_endpoints(self) -> None:
        fake_mp3 = b"\xff\xf3d\xc4" + b"\x11" * 80
        with patch(
            "modules.TTS.tts_router.tts_service._synthesize_bytes",
            new=AsyncMock(return_value=fake_mp3),
        ), patch(
            "modules.TTS.tts_router.tts_service._read_disk_cache",
            return_value=None,
        ), patch(
            "modules.TTS.tts_router.tts_service._write_disk_cache",
        ):
            r_audio = self.client.post(
                "/api/tts/speak",
                json={"text": "محتاج دكتور", "lang": "ar", "gender": "male"},
            )
            self.assertEqual(r_audio.status_code, 200)
            self.assertEqual(r_audio.headers["content-type"], "audio/mpeg")
            self.assertEqual(r_audio.headers["x-tts-voice"], "ar-EG-ShakirNeural")
            self.assertEqual(r_audio.content, fake_mp3)

            r_audio_get = self.client.get(
                "/api/tts/speak",
                params={"text": "محتاج دكتور", "lang": "ar", "gender": "male"},
            )
            self.assertEqual(r_audio_get.status_code, 200)
            self.assertEqual(r_audio_get.headers["content-type"], "audio/mpeg")
            self.assertEqual(r_audio_get.headers["accept-ranges"], "bytes")
            self.assertEqual(r_audio_get.content, fake_mp3)

            r_range = self.client.get(
                "/api/tts/speak",
                params={"text": "محتاج دكتور", "lang": "ar", "gender": "male"},
                headers={"Range": "bytes=0-9"},
            )
            self.assertEqual(r_range.status_code, 206)
            self.assertEqual(r_range.content, fake_mp3[:10])

            r_player = self.client.get("/api/tts/player")
            self.assertEqual(r_player.status_code, 200)
            self.assertIn("text/html", r_player.headers["content-type"])

            r_b64 = self.client.post(
                "/api/tts/speak-base64",
                json={"text": "I need help", "lang": "en"},
            )
            self.assertEqual(r_b64.status_code, 200)
            data = r_b64.json()
            self.assertEqual(data["voice"], "en-US-GuyNeural")
            self.assertEqual(data["mime_type"], "audio/mpeg")
            self.assertEqual(data["bytes_count"], len(fake_mp3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
