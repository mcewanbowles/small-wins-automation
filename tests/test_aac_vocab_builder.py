import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import AAC_VOCAB_BUILDER as builder


def valid_entry():
    words = ["backpack", "pencil", "bus", "wave", "walk", "yellow", "worried", "smile", "desk", "lunch", "teacher"]
    return {
        "hero": {"name": "Lola"},
        "fringe_11": words,
        "fringe_12": ["Lola"] + words,
        "fringe_justifications": {word: f"Lola encounters the {word} in a specific school scene." for word in words},
        "icon_search_terms": {word: f"{word} child" for word in words},
        "grounded": True,
        "searches_used": 1,
        "guardrail_warnings": [],
    }


class AACVocabBuilderTests(unittest.TestCase):
    def test_validate_review_entry_enforces_structure_and_promotion_gates(self):
        self.assertEqual(builder.validate_review_entry(valid_entry()), [])

        bad = valid_entry()
        bad["fringe_11"][0] = "the"
        bad["fringe_12"] = ["Lola"] + bad["fringe_11"]
        bad["searches_used"] = 0
        bad["guardrail_warnings"] = ["missing pub_year"]
        errors = builder.validate_review_entry(bad)
        self.assertTrue(any("banned" in error for error in errors))
        self.assertIn("searches_used must be at least 1", errors)
        self.assertIn("guardrail_warnings must be resolved before promotion", errors)

    def test_focus_books_uses_manifest_order_and_reports_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alpha = root / "alpha"
            beta = root / "beta"
            alpha.mkdir()
            beta.mkdir()
            manifest = root / "focus.json"
            manifest.write_text(json.dumps({"focus_books": [{"slug": "beta"}, {"slug": "missing"}, {"slug": "alpha"}]}), encoding="utf-8")

            selected, missing = builder.focus_books([alpha, beta], manifest)
            self.assertEqual([path.name for path in selected], ["beta", "alpha"])
            self.assertEqual(missing, ["missing"])

    def test_local_metadata_overrides_master_and_survives_promotion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            themes = root / "themes"
            theme = themes / "sample"
            theme.mkdir(parents=True)
            local = {
                "schema_version": 1,
                "slug": "sample",
                "title": "Accurate Local Title",
                "author": "Accurate Author",
                "status": "demand_candidate",
                "production_blocked": True,
                "demand_candidate": {"rights_review": "required"},
            }
            (theme / "book_vocab.json").write_text(json.dumps(local), encoding="utf-8")
            with patch.object(builder, "THEMES_DIR", themes), patch.object(builder, "VOCAB_FILE", root / "master" / "book_vocab.json"):
                merged = builder.load_theme_vocab("sample", {"title": "Wrong Master Title", "author": "Wrong Author"})
                self.assertEqual(merged["title"], "Accurate Local Title")
                self.assertEqual(merged["author"], "Accurate Author")

                generated = valid_entry()
                generated.update({"title": "Model Title", "author": "Model Author", "_searches_used": 1})
                draft = builder.save_needs_review("sample", generated, merged)
                self.assertEqual(draft["vocab_status"], "pending_human_review")
                self.assertEqual(draft["title"], "Accurate Local Title")
                self.assertTrue(draft["production_blocked"])
                self.assertEqual(draft["demand_candidate"], {"rights_review": "required"})

                review = valid_entry()
                review.update({"title": merged["title"], "author": merged["author"], **local})
                (theme / builder.REVIEW_FILENAME).write_text(json.dumps(review), encoding="utf-8")
                self.assertTrue(builder.promote_book("sample"))

                promoted = json.loads((theme / "book_vocab.json").read_text(encoding="utf-8"))
                self.assertEqual(promoted["schema_version"], 1)
                self.assertEqual(promoted["slug"], "sample")
                self.assertEqual(promoted["demand_candidate"], {"rights_review": "required"})
                self.assertTrue(promoted["production_blocked"])
                self.assertEqual(promoted["status"], "demand_candidate")
                self.assertEqual(promoted["vocab_status"], "human_approved")

    def test_promotion_refuses_ungrounded_review_without_touching_real_vocab(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            theme = root / "themes" / "sample"
            theme.mkdir(parents=True)
            original = {"title": "Keep Me", "production_blocked": True}
            real_path = theme / "book_vocab.json"
            real_path.write_text(json.dumps(original), encoding="utf-8")
            review = valid_entry()
            review["grounded"] = False
            (theme / builder.REVIEW_FILENAME).write_text(json.dumps(review), encoding="utf-8")
            with patch.object(builder, "THEMES_DIR", root / "themes"), patch.object(builder, "VOCAB_FILE", root / "master.json"):
                self.assertFalse(builder.promote_book("sample"))
            self.assertEqual(json.loads(real_path.read_text(encoding="utf-8")), original)

    def test_invalid_focus_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "focus.json"
            manifest.write_text('{"focus_books": [{"title": "No slug"}]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "slug is required"):
                builder.focus_books([], manifest)


if __name__ == "__main__":
    unittest.main()
