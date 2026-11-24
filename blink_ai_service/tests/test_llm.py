"""Unit and API tests for the LLM module (llm_service.py + llm_router.py + main.py)."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from main import app
from modules.LLM.llm_service import LLMService


class TestLLMService(unittest.TestCase):
    def setUp(self) -> None:
        self.llm = LLMService(api_key="")

    def test_local_complete_arabic(self) -> None:
        res = asyncio.run(self.llm.suggest("انا تعبان", lang="ar", mode="complete", limit=4))
        print(f"\n[LLM Complete AR 'انا تعبان'] => {res['suggestions']}")
        self.assertTrue(res["fallback_used"])
        self.assertEqual(res["source"], "local_fallback")
        self.assertEqual(len(res["suggestions"]), 4)

    def test_local_reply_arabic(self) -> None:
        res = asyncio.run(
            self.llm.suggest("تحب تشرب حاجة؟", lang="ar", mode="reply", limit=4)
        )
        print(f"[LLM Reply AR 'تحب تشرب حاجة؟'] => {res['suggestions']}")
        self.assertEqual(len(res["suggestions"]), 4)
        self.assertTrue(any("ميه" in s or "لا" in s for s in res["suggestions"]))

    def test_local_expand_arabic(self) -> None:
        res = asyncio.run(self.llm.suggest("ميه", lang="ar", mode="expand", limit=4))
        print(f"[LLM Expand AR 'ميه'] => {res['suggestions']}")
        self.assertEqual(len(res["suggestions"]), 4)

    def test_local_english_complete(self) -> None:
        res = asyncio.run(self.llm.suggest("I need", lang="en", mode="complete", limit=4))
        print(f"[LLM Complete EN 'I need'] => {res['suggestions']}")
        self.assertEqual(len(res["suggestions"]), 4)

    def test_remote_api_mode_and_graceful_fallback_on_error(self) -> None:
        api_llm = LLMService(api_key="test-key-123")
        self.assertTrue(api_llm.is_api_configured)

        with patch.object(
            api_llm,
            "_call_remote_llm",
            new=AsyncMock(return_value=["عايز اشرب ميه", "محتاج انام", "نادي الدكتور", "انا كويس"]),
        ):
            res = asyncio.run(api_llm.suggest("عايز", lang="ar", mode="complete", limit=4))
            self.assertFalse(res["fallback_used"])
            self.assertEqual(res["source"], "llm_api")
            self.assertEqual(len(res["suggestions"]), 4)

        with patch.object(
            api_llm,
            "_call_remote_llm",
            new=AsyncMock(side_effect=RuntimeError("network down")),
        ):
            res = asyncio.run(api_llm.suggest("عايز", lang="ar", mode="complete", limit=4))
            self.assertTrue(res["fallback_used"])
            self.assertEqual(res["source"], "local_fallback")
            self.assertEqual(len(res["suggestions"]), 4)


class TestLLMAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("LLM", data["active_modules"])

    def test_llm_health_endpoint(self) -> None:
        resp = self.client.get("/api/llm/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["module"], "LLM")
        self.assertEqual(data["status"], "ready")

    def test_llm_suggest_endpoint(self) -> None:
        resp = self.client.post(
            "/api/llm/suggest",
            json={"text": "محتاج", "lang": "ar", "mode": "complete", "limit": 4},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["suggestions"]), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
