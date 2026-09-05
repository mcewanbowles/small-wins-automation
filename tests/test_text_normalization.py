import importlib
import json

from Studioforge.boardready.modules import qa_logic
import studioforge_app as sf
from studioforge_app import next_production_stage, normalize_build_stage, product_readiness, theme_ambiguous_words, theme_vocab_words
from utils.sws_design import normalize_text


def test_normalize_quotes_dashes_and_spaces():
    s = "Curly “quotes” — and – dashes\u00A0and\u200bzwsp"
    out = normalize_text(s)
    assert '“' not in out and '”' not in out
    assert '—' not in out and '–' not in out
    assert '\u200b' not in out
    assert "  " not in out
    assert out.startswith("Curly \"quotes\" - and - dashes")


def test_product_readiness_uses_generator_specific_icon_minimums():
    readiness = product_readiness(4, True)
    assert readiness["Matching"]["ready"] is True
    assert readiness["Sequencing"]["missing_icons"] == 1
    assert readiness["Book Participation Pieces"]["missing_icons"] == 4
    assert readiness["Bingo"]["missing_icons"] == 4
    assert readiness["Spin & Cover"]["missing_icons"] == 2


def test_only_canonical_active_products_are_identified_separately_from_pilots():
    readiness = product_readiness(20, True)
    assert readiness["Matching"]["ready"] is True
    assert readiness["AAC Board"]["production_ready"] is False
    assert readiness["Book Participation Pieces"]["ready"] is True
    assert readiness["Book Participation Pieces"]["production_ready"] is False
    assert {spec["name"] for spec in sf.PRODUCT_SPECS if spec["production_status"] == "active"} == {"Matching"}


def test_disabled_product_builds_are_blocked_before_touching_outputs():
    ok, message = sf.run_product_build("anything", "Find & Cover", "Anything")
    assert ok is False
    assert "not enabled" in message


def test_product_readiness_requires_qa_even_with_enough_icons():
    readiness = product_readiness(15, False)
    assert all(info["ready"] is False for info in readiness.values())
    assert all(info["missing_icons"] == 0 for info in readiness.values())


def test_stage_guidance_defines_action_completion_and_tip_for_every_stage():
    for stage in sf.BUILD_STAGE_KEYS:
        guidance = sf.production_stage_guidance(stage)
        assert set(guidance) == {"purpose", "action", "done", "tip"}
        assert all(str(value).strip() for value in guidance.values())
    assert sf.production_stage_guidance("unknown") == sf.production_stage_guidance("setup")


def test_next_production_stage_follows_the_guided_flow():
    empty = {"Matching": False, "AAC Board": False}
    assert next_production_stage(4, False, empty, False, setup_complete=False) == "setup"
    assert next_production_stage(4, False, empty, False, content_approved=False) == "content"
    assert next_production_stage(3, False, empty, False) == "icons"
    assert next_production_stage(15, False, empty, False, icon_review_complete=False) == "icons"
    assert next_production_stage(4, False, empty, False, boardready_confirmed=False) == "boardready"
    assert next_production_stage(4, False, empty, False) == "qa"
    assert next_production_stage(4, True, empty, False) == "build"
    assert next_production_stage(4, True, {"Matching": True}, False) == "listing"
    assert next_production_stage(4, True, {"Matching": True}, True) == "tracker"


def test_boardready_wrapper_uses_topic_vocab_and_canonical_flags(tmp_path, monkeypatch):
    from Generators import aac_book_board

    theme = tmp_path / "topic_test"
    images = theme / "activity_images"
    images.mkdir(parents=True)
    (theme / "book_vocab.json").write_text(json.dumps({"title": "Test", "fringe_12": [f"word{i}" for i in range(12)]}), encoding="utf-8")
    captured = {}

    class FakeBoardReady:
        @staticmethod
        def main():
            captured["argv"] = list(aac_book_board.sys.argv)

    monkeypatch.setattr(aac_book_board, "_load_boardready_module", lambda: FakeBoardReady)
    assert aac_book_board.generate_aac_board_pack(str(images), "TEST01", "Test") is True
    argv = captured["argv"]
    vocab_path = argv[argv.index("--vocab") + 1]
    assert json.loads(sf.Path(vocab_path).read_text(encoding="utf-8"))["topic_test"]["fringe_12"] == [f"word{i}" for i in range(12)]
    assert {"--windsurf", "--no-accent-strip", "--pack-code"}.issubset(argv)


def test_support_document_service_includes_finished_aac_tips_only():
    documents, warnings = sf.support_documents_for_product("sample", "AAC Board")
    archive_names = {name for _path, name in documents}
    source_names = {path.name for path, _name in documents}
    assert "Terms of Use.pdf" in archive_names
    assert "SWS_Top_Tips_AAC_Communication_Partners.pdf" in archive_names
    assert all("REFERENCE" not in name for name in archive_names)
    assert all("V2" not in name for name in source_names)
    assert any("Quick Start" in warning for warning in warnings)


def test_pack_codes_are_safe_for_output_filenames():
    assert sf.sanitise_pack_code(" stel 01 / a ") == "STEL01A"
    assert sf.sanitise_pack_code("abc-123_test-too-long") == "ABC-123_TEST"
    assert sf.sanitise_pack_code("***") == ""


def test_new_topic_profile_requires_human_content_and_boardready_review(tmp_path, monkeypatch):
    monkeypatch.setenv("SF_THEMES_ROOT", str(tmp_path))
    profile = {
        "topic": "Motorsport Pit Stops",
        "title": "Motorsport Pit Stops",
        "age_band": "Years 7–10 (teen SPED)",
        "instructional_reading_level": "Emergent to functional literacy",
        "communication_modes": ["AAC"],
        "support_level": "Differentiated",
        "learning_targets": ["Identify safe teamwork actions"],
        "sensitive_content": False,
    }
    ok, _message, slug = sf.create_topic_project(profile)
    assert ok is True
    assert slug == "topic_motorsport_pit_stops"
    gates = sf.workflow_gate_status(slug)
    assert gates["setup"] is True
    assert gates["content"] is False
    assert gates["boardready"] is False
    assert (tmp_path / slug / "config" / "project_profile.json").exists()


def test_build_stage_normalization_rejects_unknown_routes():
    assert normalize_build_stage("listing") == "listing"
    assert normalize_build_stage("unknown") == "setup"
    assert normalize_build_stage(None) == "setup"


def test_theme_vocab_words_prefers_complete_api_vocab_without_duplicates():
    data = {
        "fringe_12": ["David", "school", "sit down"],
        "activity_images": ["school", "teacher"],
        "aac_extras": ["sit down", "listen"],
    }
    assert theme_vocab_words(data) == ["David", "school", "sit down", "teacher", "listen"]


def test_theme_ambiguous_words_are_normalized_for_manual_review():
    data = {"ambiguous": [{"word": "Recess"}, "Bat", {"issue": "missing word"}]}
    assert theme_ambiguous_words(data) == {"recess", "bat"}


def test_banned_library_image_is_excluded_from_candidates(tmp_path, monkeypatch):
    bad = tmp_path / "sit_down.png"
    good = tmp_path / "sit_down_boy.png"
    bad.touch()
    good.touch()
    monkeypatch.setattr(qa_logic, "QA_BANLIST_PATH", tmp_path / "qa_banlist.json")
    qa_logic.add_to_banlist(str(bad))
    results = qa_logic.search_png_library("sit down", paths=[bad, good], top_k=5)
    assert [item["path"] for item in results] == [str(good)]


def test_saved_banned_path_is_replaced_in_required_icons(tmp_path, monkeypatch):
    bad = tmp_path / "sit_down.png"
    good = tmp_path / "sit_down_boy.png"
    bad.touch()
    good.touch()
    monkeypatch.setattr(qa_logic, "QA_BANLIST_PATH", tmp_path / "qa_banlist.json")
    monkeypatch.setattr(qa_logic, "_required_words_for_book", lambda book_key, include_core=False: ["sit down"])
    monkeypatch.setattr(qa_logic, "load_theme_vocab", lambda book_key: {})
    monkeypatch.setattr(qa_logic, "load_qa_log", lambda: {"book": {"words": {"sit down": {"status": "keep", "path": str(bad)}}}})
    monkeypatch.setattr(qa_logic, "_library_paths", lambda book_key=None: [bad, good])
    qa_logic.add_to_banlist(str(bad))
    result = qa_logic.get_icons_for_book("book", include_context=False)
    assert result[0]["current_path"] == str(good)
    assert result[0]["status"] == "auto"


def test_icon_candidates_use_api_search_terms(monkeypatch):
    searched = []

    def fake_search(term, book_key=None, top_k=6):
        searched.append((term, book_key))
        score = 0.95 if term == "playground" else 0.7
        return [{"label": term, "path": f"C:/{term}.png", "score": score}]

    monkeypatch.setattr(sf, "theme_vocab_source", lambda slug: (None, {"icon_search_terms": {"recess": "playground"}}))
    monkeypatch.setattr(sf.icon_qa_logic, "search_png_library", fake_search)
    results = sf.icon_candidates_for_word("recess", "david_goes_to_school", limit=4)
    assert searched == [("playground", "david_goes_to_school"), ("recess", "david_goes_to_school")]
    assert results[0]["label"] == "playground"


def test_replace_theme_vocab_word_preserves_api_vocab_structure(tmp_path, monkeypatch):
    path = tmp_path / "book_vocab.json"
    data = {
        "title": "David Goes to School",
        "fringe_12": ["teacher", "sit down"],
        "activity_images": ["sit down"],
        "icon_search_terms": {"sit down": "sit down"},
        "notes": "keep this",
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(sf, "theme_vocab_source", lambda slug: (path, json.loads(path.read_text(encoding="utf-8"))))
    ok, _message = sf.replace_theme_vocab_word("david_goes_to_school", "sit down", "sitting")
    revised = json.loads(path.read_text(encoding="utf-8"))
    assert ok is True
    assert revised["fringe_12"] == ["teacher", "sitting"]
    assert revised["activity_images"] == ["sitting"]
    assert revised["icon_search_terms"] == {"sitting": "sitting"}
    assert revised["notes"] == "keep this"


def test_tpt_marketing_pages_create_four_upload_ready_squares(tmp_path, monkeypatch):
    source = tmp_path / "activity.pdf"
    source.touch()
    monkeypatch.setattr(sf, "_product_output_files", lambda out_dir, name: {"color": source, "bw": source, "preview": source})
    monkeypatch.setattr(sf, "_pdf_page_count", lambda path: 8)
    monkeypatch.setattr(sf, "_pdf_page_image", lambda path, page_index=0, scale=1.7: sf.Image.new("RGB", (850, 1100), "#E8F5F4"))
    built = {"Matching": {"built": True}, "Find & Cover": {"built": True}, "AAC Board": {"built": True}}
    paths = sf.generate_tpt_marketing_pages("sample_resource", "SWS-TEST", tmp_path, built, "A Long Sample Resource Title for Teachers")
    assert len(paths) == 4
    assert [path.name for path in paths] == [
        "SWS-TEST_1_cover.png",
        "SWS-TEST_2_whats_included.png",
        "SWS-TEST_3_closer_look.png",
        "SWS-TEST_4_teacher_confidence.png",
    ]
    assert all(sf.Image.open(path).size == (1200, 1200) for path in paths)
    assert all(path.stat().st_size < 4_000_000 for path in paths)
    output = tmp_path / "TPT_UPLOAD" / "IMAGES" / "SWS-TEST"
    assert (output / "SWS-TEST_captions.csv").exists()
    assert (output / "SWS-TEST_preview.pdf").exists()


def test_icon_labeller_url_embeds_the_active_book():
    assert sf.icon_labeler_url("/pdf", "room on the broom") == "http://127.0.0.1:5053/pdf?book=room%20on%20the%20broom"


def test_cached_icon_candidates_scan_library_once_and_return_multiple_options(tmp_path, monkeypatch):
    paths = [tmp_path / f"sit_{index}.png" for index in range(6)]
    for path in paths:
        path.touch()
    calls = {"paths": 0}

    def fake_paths(slug):
        calls["paths"] += 1
        return paths

    def fake_search(term, book_key=None, top_k=5, paths=None):
        return [{"label": path.stem, "path": str(path), "score": 0.9 - index * 0.01} for index, path in enumerate(paths)]

    monkeypatch.setattr(sf, "theme_vocab_source", lambda slug: (None, {}))
    monkeypatch.setattr(sf.icon_qa_logic, "_library_paths", fake_paths)
    monkeypatch.setattr(sf.icon_qa_logic, "search_png_library", fake_search)
    sf.clear_icon_candidate_cache()
    result = sf.cached_icon_candidate_map("book", ("sit down", "listen"), 6)
    assert calls["paths"] == 1
    assert len(result["sit down"]) == 6
    assert len(result["listen"]) == 6


def test_studioforge_reads_icon_labeller_decisions(tmp_path, monkeypatch):
    replacement = tmp_path / "help.png"
    replacement.touch()
    monkeypatch.setattr(sf, "read_book_state", lambda slug: {"icon_decisions": {}})
    monkeypatch.setattr(sf, "images_dir_for_book", lambda slug: tmp_path / "theme")
    monkeypatch.setattr(sf.icon_qa_logic, "load_qa_log", lambda: {"book": {"words": {"help": {"status": "replaced", "path": str(replacement)}, "wait": {"status": "skip"}}}})
    assert sf.icon_word_decision("book", "wait")["status"] == "skipped"
    assert sf.accepted_icon_for_word("book", "help") == replacement


def test_icon_search_uses_true_labels_for_duplicate_files(tmp_path, monkeypatch):
    alpha = tmp_path / "symbols" / "png" / "Alpha"
    alpha.mkdir(parents=True)
    duplicate = alpha / "f" / "fish_2.png"
    duplicate.parent.mkdir()
    duplicate.touch()
    (alpha / "icon_labels.json").write_text(json.dumps({str(duplicate): "fish"}), encoding="utf-8")
    monkeypatch.setattr(qa_logic, "ASSETS_DIR", tmp_path)
    qa_logic._ICON_LABEL_INDEX_CACHE.update({"mtime": None, "labels": {}})
    results = qa_logic.search_png_library("fish", paths=[duplicate], top_k=3)
    assert results[0]["path"] == str(duplicate)
    assert results[0]["score"] == 1.0


def test_boardmaker_grid_preview_extracts_every_cell_and_detects_text():
    document = sf.fitz.open()
    page = document.new_page(width=200, height=200)
    page.insert_text((20, 40), "cat")
    page.insert_text((120, 40), "dog")
    pdf_data = document.tobytes()
    document.close()
    tiles = sf.extract_boardmaker_grid(pdf_data, rows=2, cols=2, padding_percent=2)
    assert len(tiles) == 4
    assert tiles[0]["image"].startswith(b"\x89PNG")
    assert tiles[0]["detected_label"] == "cat"
    assert tiles[1]["detected_label"] == "dog"


def test_unlabelled_boardmaker_tiles_can_be_saved_and_resumed(tmp_path, monkeypatch):
    theme = tmp_path / "book"
    theme.mkdir()
    monkeypatch.setattr(sf, "find_book_dir", lambda slug: theme)
    image = sf.Image.new("RGB", (40, 40), "white")
    buffer = sf.io.BytesIO()
    image.save(buffer, format="PNG")
    tiles = [
        {"image": buffer.getvalue(), "page": 1, "row": 1, "col": 1},
        {"image": buffer.getvalue(), "page": 1, "row": 1, "col": 2},
    ]
    ok, _message, batch_dir = sf.save_boardmaker_tiles_for_later("book", "symbols.pdf", tiles, 1, 2)
    assert ok is True
    assert batch_dir is not None
    batches = sf.boardmaker_batches_waiting_for_labels("book")
    assert len(batches) == 1
    loaded = sf.load_boardmaker_pending_tiles(batches[0])
    assert len(loaded) == 2
    assert all(tile["image"].startswith(b"\x89PNG") for tile in loaded)
    sf.save_boardmaker_batch_labels(batches[0]["manifest_path"], ["cat", ""])
    saved_manifest = json.loads((batch_dir / "manifest.json").read_text(encoding="utf-8"))
    assert saved_manifest["tiles"][0]["label"] == "cat"
    assert saved_manifest["status"] == "waiting_for_labels"
    sf.save_boardmaker_batch_labels(batches[0]["manifest_path"], ["cat", ""], complete=True)
    assert sf.boardmaker_batches_waiting_for_labels("book") == []


def test_icon_only_book_can_complete_icon_review(monkeypatch):
    monkeypatch.setattr(sf, "extract_book_vocab", lambda slug: None)
    monkeypatch.setattr(sf, "read_book_state", lambda slug: {"icons_kit": ["one.png", "two.png"]})
    summary = sf.icon_review_summary("icon_only_book")
    assert summary["total"] == 2
    assert summary["complete"] is True


def test_required_builds_do_not_complete_from_a_pilot_only():
    assert sf.required_builds_complete({"Vocabulary Snap": True, "Matching": False}) is False
    assert sf.required_builds_complete({"Vocabulary Snap": False, "Matching": True}) is True


def test_enabled_product_modules_and_functions_are_importable():
    enabled = [spec for spec in sf.PRODUCT_SPECS if spec.get("build_enabled", spec.get("production_status") == "active")]
    for spec in enabled:
        module = importlib.import_module(spec["module"])
        assert callable(getattr(module, spec["func"]))


def test_product_preflight_reports_missing_reviewed_config(tmp_path, monkeypatch):
    monkeypatch.setattr(sf, "find_book_dir", lambda slug: tmp_path)
    ok, message = sf.product_preflight("book", "CVC Decode & Build")
    assert ok is False
    assert "decoding.json" in message


def test_tpt_product_url_validation_rejects_store_and_lookalike_domains():
    assert sf.is_tpt_product_url("https://www.teacherspayteachers.com/Product/Example-123") is True
    assert sf.is_tpt_product_url("https://www.teacherspayteachers.com/Store/SmallWinsStudios") is False
    assert sf.is_tpt_product_url("https://evilteacherspayteachers.com/Product/Example-123") is False


def test_guided_pinterest_campaign_creates_six_reviewable_fresh_pins(tmp_path, monkeypatch):
    out_dir = tmp_path / "OUTPUT"
    images_dir = out_dir / "TPT_UPLOAD" / "IMAGES" / "TEST01"
    images_dir.mkdir(parents=True)
    for index, colour in enumerate(("#31A8A0", "#F5C518"), start=1):
        sf.Image.new("RGB", (1200, 1200), colour).save(images_dir / f"source_{index}.png")
    ok, message, campaign_dir = sf.generate_guided_pinterest_campaign(
        "sample_book",
        "TEST01",
        out_dir,
        {"tpt_title": "Sample Book Visual Resource", "description": "Accessible visual activities for supported learning."},
        images_dir,
        "https://www.teacherspayteachers.com/Product/Sample-Book-123",
        "",
    )
    assert ok is True
    assert "6 fresh Pin drafts" in message
    assert campaign_dir is not None
    pins = sorted(campaign_dir.glob("TEST01_pin_*.png"))
    assert len(pins) == 6
    assert all(sf.Image.open(path).size == (1000, 1500) for path in pins)
    assert len({sf.hashlib.sha256(path.read_bytes()).hexdigest() for path in pins}) == 6
    manifest = json.loads((campaign_dir / "TEST01_campaign.json").read_text(encoding="utf-8"))
    assert len(manifest["pins"]) == 6
    assert all(row["destination_url"].endswith("/Product/Sample-Book-123") for row in manifest["pins"])
    assert all(len(row["pin_title"]) <= 100 and len(row["pin_description"]) <= 500 for row in manifest["pins"])
    assert (campaign_dir / "TEST01_guided_upload_review.csv").exists()
    assert (campaign_dir / "REVIEW_CAMPAIGN.html").exists()
    assert (campaign_dir / "TEST01_guided_tailwind_upload.zip").exists()
    monkeypatch.setattr(sf, "output_dir_for_book", lambda slug: out_dir)
    assert sf.marketing_campaign_ready("sample_book") is False
    manifest["status"] = "approved"
    (campaign_dir / "TEST01_campaign.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert sf.marketing_campaign_ready("sample_book") is True


def test_workflow_requires_promotion_after_listing_when_campaign_missing():
    built = {"Matching": True}
    assert next_production_stage(8, True, built, True, promotion_ready=False) == "promote"
    assert next_production_stage(8, True, built, True, promotion_ready=True) == "tracker"


def test_vocab_review_accepts_concrete_story_words_and_rejects_vague_words():
    words = ["backpack", "pencil", "bus", "wave", "walk", "yellow", "worried", "smile", "desk", "lunch", "teacher"]
    entry = {
        "title": "Lola Goes to School",
        "author": "Anna McQuinn",
        "pub_year": "2019",
        "book_summary": "Lola prepares for her first day and takes part in specific classroom routines at school.",
        "hero": {"name": "Lola"},
        "fringe_11": words,
        "fringe_12": ["Lola"] + words,
        "fringe_justifications": {word: f"Lola encounters {word} during a specific school scene." for word in words},
        "icon_search_terms": {word: word for word in words},
        "grounded": True,
        "searches_used": 1,
    }
    assert sf.vocab_review_issues(entry) == []
    entry["fringe_11"][0] = "thing"
    entry["fringe_12"] = ["Lola"] + entry["fringe_11"]
    assert any("unsuitable" in issue for issue in sf.vocab_review_issues(entry))


def test_demand_candidate_content_gate_requires_human_approved_vocab(tmp_path, monkeypatch):
    root = tmp_path / "themes"
    theme = root / "candidate"
    theme.mkdir(parents=True)
    vocab_path = theme / "book_vocab.json"
    vocab_path.write_text(json.dumps({"status": "demand_candidate", "vocab_status": "pending_human_review"}), encoding="utf-8")
    monkeypatch.setattr(sf, "project_root", lambda: tmp_path)
    monkeypatch.setenv("SF_THEMES_ROOT", str(root))
    assert sf.workflow_gate_status("candidate")["content"] is False
    vocab_path.write_text(json.dumps({"status": "demand_candidate", "vocab_status": "human_approved"}), encoding="utf-8")
    assert sf.workflow_gate_status("candidate")["content"] is True


def test_vocab_queue_flags_existing_missing_extra_and_unsuitable_words(tmp_path, monkeypatch):
    monkeypatch.setattr(sf, "find_book_dir", lambda slug: tmp_path)
    path = tmp_path / "book_vocab.json"
    path.write_text(json.dumps({"fringe_12": ["Hero", "book"]}), encoding="utf-8")
    assert sf._vocab_queue_status("book") == "Needs 10 more words"
    words = ["thing"] + [f"object {index}" for index in range(10)]
    path.write_text(json.dumps({"fringe_12": ["Hero"] + words, "fringe_11": words}), encoding="utf-8")
    assert sf._vocab_queue_status("book").startswith("Replace unsuitable: thing")
    words.append("extra")
    path.write_text(json.dumps({"fringe_12": ["Hero"] + words, "fringe_11": words}), encoding="utf-8")
    assert sf._vocab_queue_status("book") == "Remove 1 extra word"
