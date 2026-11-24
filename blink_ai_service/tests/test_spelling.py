"""Unit and API tests for the Spelling module (spelling_corrector.py + spelling_router.py + main.py)."""

import sys
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from main import app
from modules.Spelling.spelling_corrector import SpellingCorrector


class TestSpellingCorrector(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        t0 = time.perf_counter()
        cls.corrector = SpellingCorrector()
        cls.load_ms = (time.perf_counter() - t0) * 1000
        print(f"\n[Spelling Setup] Loaded dictionary in {cls.load_ms:.2f} ms")

    def test_arabic_missing_and_extra_letters(self) -> None:
        cases = {
            "عاز": "عايز",
            "مستفي": "مستشفى",
            "اشب": "اشرب",
            "تعبن": "تعبان",
            "ميهه": "ميه",
        }
        for typo, expected in cases.items():
            t0 = time.perf_counter()
            res = self.corrector.correct_word(typo, lang="ar", limit=4)
            ms = (time.perf_counter() - t0) * 1000
            print(f"[Spelling AR '{typo}'] => {res['suggestions']} (best='{res['best_correction']}', {ms:.2f} ms)")
            self.assertEqual(res["best_correction"], expected)
            self.assertLess(ms, 100.0)

    def test_arabic_transposition_typo(self) -> None:
        res = self.corrector.correct_word("دكترو", lang="ar", limit=4)
        print(f"[Spelling AR 'دكترو'] => {res['suggestions']} (best='{res['best_correction']}')")
        self.assertEqual(res["best_correction"], "دكتور")

    def test_context_reranking_helps_disambiguate(self) -> None:
        res = self.corrector.correct_word(
            "اشب", lang="ar", limit=4, context_words=["انا", "عايز"]
        )
        print(f"[Spelling AR 'اشب' with context ['انا', 'عايز']] => {res['results'][0]}")
        self.assertEqual(res["best_correction"], "اشرب")
        self.assertTrue(res["results"][0]["context_match"])

    def test_english_typos(self) -> None:
        cases = {
            "wter": "water",
            "doctr": "doctor",
            "hepl": "help",
            "medcine": "medicine",
        }
        for typo, expected in cases.items():
            t0 = time.perf_counter()
            res = self.corrector.correct_word(typo, lang="en", limit=4)
            ms = (time.perf_counter() - t0) * 1000
            print(f"[Spelling EN '{typo}'] => {res['suggestions']} (best='{res['best_correction']}', {ms:.2f} ms)")
            self.assertEqual(res["best_correction"], expected)

    def test_exact_word_stays_first(self) -> None:
        res = self.corrector.correct_word("عايز", lang="ar", limit=4)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["best_correction"], "عايز")
        self.assertEqual(res["results"][0]["edit_distance"], 0)

    def test_full_sentence_correction(self) -> None:
        res = self.corrector.correct_sentence("انا عاز اشب ميهه", lang="ar")
        print(f"[Sentence Fix] '{res['original_text']}' => '{res['corrected_text']}'")
        self.assertTrue(res["has_changes"])
        self.assertEqual(res["corrected_text"], "انا عايز اشرب ميه")
        self.assertEqual(len(res["corrections"]), 3)


class TestSpellingAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "running")
        self.assertIn("Spelling", data["active_modules"])

    def test_spelling_health_endpoint(self) -> None:
        resp = self.client.get("/api/spelling/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["module"], "Spelling")
        self.assertEqual(data["ar_words"], 12000)
        self.assertEqual(data["en_words"], 10000)

    def test_correct_word_endpoint(self) -> None:
        resp = self.client.post(
            "/api/spelling/correct-word",
            json={"word": "مستفي", "lang": "ar", "limit": 4},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["best_correction"], "مستشفى")
        self.assertFalse(data["is_valid"])

    def test_correct_sentence_endpoint(self) -> None:
        resp = self.client.post(
            "/api/spelling/correct-sentence",
            json={"text": "انا عاز اشب ميهه", "lang": "ar"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["corrected_text"], "انا عايز اشرب ميه")
        self.assertTrue(data["has_changes"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
