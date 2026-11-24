"""Unit and API tests for the IR module (ir_engine.py + ir_router.py + main.py)."""

import sys
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from main import app
from modules.IR.ir_engine import IREngine, normalize_text


class TestIREngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        t0 = time.perf_counter()
        cls.engine = IREngine()
        cls.build_ms = (time.perf_counter() - t0) * 1000
        print(f"\n[IR Setup] Indexed 22,000 words in {cls.build_ms:.2f} ms")

    def test_arabic_normalization(self) -> None:
        self.assertEqual(normalize_text("أَشْرَب", "ar"), "اشرب")
        self.assertEqual(normalize_text("إلى", "ar"), "الي")
        self.assertEqual(normalize_text("آسف", "ar"), "اسف")
        self.assertEqual(normalize_text("مروحة", "ar"), "مروحه")

    def test_empty_returns_starters(self) -> None:
        res = self.engine.retrieve("", lang="ar", limit=4)
        self.assertEqual(res["mode"], "empty")
        self.assertEqual(res["suggestions"], ["انا", "عايز", "محتاج", "حاسس"])

    def test_prefix_retrieval_and_speed(self) -> None:
        t0 = time.perf_counter()
        res = self.engine.retrieve("مست", lang="ar", limit=4)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        print(f"[IR Query 'مست'] => {res['suggestions']} ({elapsed_ms:.3f} ms)")
        self.assertIn("مستشفى", res["suggestions"])
        self.assertLess(elapsed_ms, 5.0)

    def test_next_word_with_space(self) -> None:
        res = self.engine.retrieve("انا عايز ", lang="ar", limit=4)
        print(f"[IR Query 'انا عايز '] => {res['suggestions']}")
        self.assertEqual(res["mode"], "next_word")
        self.assertEqual(res["suggestions"], ["اشرب", "اكل", "انام", "الحمام"])

    def test_direct_next_word_without_space(self) -> None:
        res = self.engine.retrieve("عايز", lang="ar", limit=4)
        print(f"[IR Query 'عايز' (no space)] => {res['suggestions']}")
        self.assertEqual(res["mode"], "direct_next")
        self.assertIn("اشرب", res["suggestions"])
        self.assertEqual(res["results"][0]["action"], "next")

    def test_context_filtered_partial_word(self) -> None:
        res = self.engine.retrieve("انا عايز اش", lang="ar", limit=4)
        print(f"[IR Query 'انا عايز اش'] => {res['suggestions']}")
        self.assertEqual(res["suggestions"][0], "اشرب")
        self.assertEqual(res["results"][0]["source"], "context_prefix")

    def test_english_retrieval(self) -> None:
        res = self.engine.retrieve("I want wa", lang="en", limit=4)
        print(f"[IR Query 'I want wa'] => {res['suggestions']}")
        self.assertEqual(res["suggestions"][0], "water")

    def test_unknown_misspelled_word_returns_empty_so_spelling_handles_it(self) -> None:
        res = self.engine.retrieve("اعز", lang="ar", limit=4)
        print(f"[IR Query 'اعز' (typo)] => {res['suggestions']}")
        self.assertEqual(res["current_fragment"], "اعز")


class TestIRAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("IR", data["active_modules"])

    def test_ir_health_endpoint(self) -> None:
        resp = self.client.get("/api/ir/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["module"], "IR")
        self.assertEqual(data["ar_words"], 12000)
        self.assertEqual(data["en_words"], 10000)

    def test_ir_suggest_arabic(self) -> None:
        resp = self.client.post(
            "/api/ir/suggest",
            json={"text": "انا عايز اش", "lang": "ar", "limit": 4},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["suggestions"][0], "اشرب")
        self.assertEqual(data["mode"], "complete_word")

    def test_ir_suggest_english(self) -> None:
        resp = self.client.post(
            "/api/ir/suggest",
            json={"text": "I want ", "lang": "en", "limit": 4},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["mode"], "next_word")
        self.assertEqual(len(data["suggestions"]), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
