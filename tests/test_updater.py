import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("updater", ROOT / "scripts/update_news.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


class UpdateSafety(unittest.TestCase):
    def setUp(self):
        self.lesson = json.loads((ROOT / "tests/example.json").read_text())
        self.sources = []
        for i, story in enumerate(self.lesson["stories"]):
            source_id = f"S{i}"
            story["english_source_ids"] = [source_id]
            story["arabic_source_ids"] = []
            self.sources.append({"id": source_id, "language": "en", "publisher": "Example fixture", "url": f"https://news.un.org/en/story/example-{i}", "published_at": "2026-09-15T06:00:00+00:00"})

    def test_well_formed_lesson(self):
        updater.validate(self.lesson, self.sources)

    def test_invented_source_rejected(self):
        self.lesson["stories"][0]["english_source_ids"] = ["NOT_IN_REPORTS"]
        with self.assertRaises(ValueError): updater.validate(self.lesson, self.sources)

    def test_wrong_language_reference_rejected(self):
        self.lesson["stories"][0]["arabic_source_ids"] = ["S1"]
        with self.assertRaises(ValueError): updater.validate(self.lesson, self.sources)

    def test_glossary_must_come_from_summary(self):
        self.lesson["glossary"][0]["example_en"] = "This draft agreement never appeared in the source summary."
        with self.assertRaises(ValueError): updater.validate(self.lesson, self.sources)

    def test_public_projection_drops_untrusted_links_and_verification_claims(self):
        self.lesson["stories"][0]["sources"] = [{"url": "javascript:alert(1)"}]
        self.lesson["stories"][0]["reference_note"] = "Human-certified translation"
        result = updater.prepare_public(self.lesson, self.sources, datetime.now(timezone.utc), [])
        self.assertEqual(result["stories"][0]["sources"][0]["url"], self.sources[0]["url"])
        self.assertNotIn("Human-certified", result["stories"][0]["reference_note"])

    def test_network_destinations_are_restricted(self):
        for url in ("http://news.un.org/x", "https://news.un.org.evil.test/x", "https://127.0.0.1/x", "file:///etc/passwd", "https://user:pass@news.un.org/x", "https://news.un.org:8443/x"):
            self.assertFalse(updater.safe_source(url), url)
        self.assertTrue(updater.safe_source("https://news.un.org/en/story/2026/09/example"))

    def test_no_key_means_no_network_or_data_write(self):
        with patch.dict("os.environ", {}, clear=True), patch.object(updater, "collect_sources") as fetch, patch.object(updater, "publish") as publish:
            updater.main(); fetch.assert_not_called(); publish.assert_not_called()

    def test_rejected_review_preserves_last_good_edition(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            original = '{"demo":true,"stories":[]}'
            (folder / "latest.json").write_text(original)
            with patch.object(updater, "DATA", folder), patch.dict("os.environ", {"GEMINI_API_KEY": "test-only-key", "FREE_TIER_CONFIRMED": "true"}), patch.object(updater, "collect_sources", return_value=(self.sources, [])), patch.object(updater, "generate", side_effect=[self.lesson, {"approved": False}]):
                with self.assertRaises(ValueError): updater.main()
            self.assertEqual((folder / "latest.json").read_text(), original)

    def test_repeated_run_skips_ai_after_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "latest.json").write_text(json.dumps({"demo": False, "generated_at": datetime.now(timezone.utc).isoformat()}))
            with patch.object(updater, "DATA", folder), patch.dict("os.environ", {"GEMINI_API_KEY": "test-only-key", "FREE_TIER_CONFIRMED": "true"}), patch.object(updater, "generate") as generate, patch.object(updater, "collect_sources") as fetch:
                updater.main(); generate.assert_not_called(); fetch.assert_not_called()

    def test_archive_and_latest_are_updated_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with patch.object(updater, "DATA", folder): updater.publish(self.lesson, datetime(2026, 9, 15, tzinfo=timezone.utc))
            self.assertEqual(json.loads((folder / "latest.json").read_text()), self.lesson)
            self.assertEqual(json.loads((folder / "editions.json").read_text()), [{"date": "2026-09-15"}])
            self.assertTrue((folder / "editions/2026-09-15.json").is_file())


if __name__ == "__main__": unittest.main()
