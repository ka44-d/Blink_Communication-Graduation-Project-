"""Unified end-to-end tests verifying all 4 modules run together via main.py."""

import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from main import app


class TestUnifiedServiceAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_lists_all_4_modules(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["active_modules"], ["IR", "Spelling", "TTS", "LLM"])

    def test_combined_health_endpoint(self) -> None:
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            set(resp.json()["modules"].keys()),
            {"IR", "Spelling", "TTS", "LLM"},
        )

    def test_all_4_modules_work_on_same_server(self) -> None:
        # 1. IR
        r_ir = self.client.post(
            "/api/ir/suggest", json={"text": "انا عايز اش", "lang": "ar", "limit": 4}
        )
        self.assertEqual(r_ir.status_code, 200)
        self.assertEqual(r_ir.json()["suggestions"][0], "اشرب")

        # 2. Spelling
        r_sp = self.client.post(
            "/api/spelling/correct-sentence",
            json={"text": "انا عاز اشب ميهه", "lang": "ar"},
        )
        self.assertEqual(r_sp.status_code, 200)
        self.assertEqual(r_sp.json()["corrected_text"], "انا عايز اشرب ميه")

        # 3. TTS
        with patch(
            "modules.TTS.tts_router.tts_service._synthesize_bytes",
            new=AsyncMock(return_value=b"\xff\xf3d\xc4" + b"\x00" * 50),
        ), patch(
            "modules.TTS.tts_router.tts_service._read_disk_cache",
            return_value=None,
        ), patch(
            "modules.TTS.tts_router.tts_service._write_disk_cache",
        ):
            r_tts = self.client.post(
                "/api/tts/speak", json={"text": "انا عايز اشرب ميه", "lang": "ar"}
            )
            self.assertEqual(r_tts.status_code, 200)
            self.assertEqual(r_tts.headers["content-type"], "audio/mpeg")

        # 4. LLM
        r_llm = self.client.post(
            "/api/llm/suggest",
            json={"text": "انا تعبان", "lang": "ar", "mode": "complete", "limit": 4},
        )
        self.assertEqual(r_llm.status_code, 200)
        self.assertEqual(len(r_llm.json()["suggestions"]), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
