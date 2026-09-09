from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import random
import re
import zipfile
from datetime import datetime
from pathlib import Path

import fitz
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from production.generators.generate_book_participation_pieces import _activity_page, _center, _fit, _font, _save_pdf
from utils.UNIVERSAL_STANDARDS import SWS_GOLD, SWS_NAVY, SWS_TEAL, SWS_TEAL_LT
from utils.sws_design import DPI, hex_to_rgb

ROOT = Path(__file__).resolve().parents[2]
THEME = ROOT / "assets" / "themes" / "llama_llama_red_pajama"
OUTPUT = THEME / "OUTPUT"
OVERVIEWS = ROOT / "production" / "generators" / "teacher_overview_examples"
PACKAGE_ROOT = ROOT / "Studioforge" / "_REVIEW" / "FINAL_ACTIVITY_PACKAGES_2026-09-05"
TOU = OUTPUT / "LLRP-TOU_Terms_of_Use.pdf"
BUNDLE_GUIDE = OUTPUT / "LLRP-BUNDLE_Bundle_Start_Here.pdf"

# Suggested TPT pricing (USD) — SPED/literacy norms, sanity-check before listing.
SUGGESTED_PRICES_USD = {
    "aac_board": 3.50, "matching": 4.50, "book_participation": 4.00,
    "sentence_building": 4.00, "sequencing": 3.50, "yes_no": 3.00,
    "inferencing": 3.50, "vocabulary_snap": 3.00, "syllable_awareness": 3.00,
    "decoding": 3.50, "story_grammar": 2.75, "word_search": 3.50,
    "bingo": 4.50, "sorting": 4.00, "print_detective": 4.00,
}
SUGGESTED_BUNDLE_PRICE_USD = 39.99
IEP_MODULE = ROOT / "Studioforge" / "Accurate generators" / "IEP_MONITORING_FORM.py"
MONITORING_FORM = OUTPUT / "LLRP-MON_IEP_MonitoringForm.pdf"


def _ensure_monitoring_form() -> Path:
    """Generate the generic LLRP IEP progress-monitoring sheet once."""
    if MONITORING_FORM.is_file():
        return MONITORING_FORM
    spec = importlib.util.spec_from_file_location("iep_monitoring_form", IEP_MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    generic_sessions = [(str(i), f"Session {i}", "") for i in range(1, 11)]
    module.generate_iep_monitoring_form(
        "llama_llama_red_pajama", "Llama Llama Red Pajama", "LLRP-MON",
        output_dir=str(OUTPUT), sessions=generic_sessions,
    )
    if not MONITORING_FORM.is_file():
        raise FileNotFoundError(MONITORING_FORM)
    return MONITORING_FORM


def _ensure_tou() -> Path:
    """Generate the framed Terms of Use PDF."""
    if TOU.is_file():
        return TOU
    tou_module_path = ROOT / "production" / "generators" / "generators" / "generate_tpt_documentation.py"
    spec = importlib.util.spec_from_file_location("generate_tpt_documentation", tou_module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.generate_tpt_documentation("LLRP-TOU", "Llama Llama Red Pajama", str(OUTPUT))
    if not TOU.is_file():
        raise FileNotFoundError(TOU)
    return TOU


def _ensure_bundle_guide() -> Path:
    """Generate the Bundle Start Here PDF (includes Top Tips as page 8)."""
    if BUNDLE_GUIDE.is_file():
        return BUNDLE_GUIDE
    from production.generators.generate_bundle_start_here import generate_bundle_start_here
    generate_bundle_start_here(
        pack_code="LLRP-BUNDLE",
        book_title="Llama Llama Red Pajama",
        theme_dir=str(THEME),
        output_dir=str(OUTPUT),
    )
    if not BUNDLE_GUIDE.is_file():
        raise FileNotFoundError(BUNDLE_GUIDE)
    return BUNDLE_GUIDE

PRODUCTS = [
    {"id": "aac_board", "name": "AAC Communication Board", "code": "LLRP-AAC-REVIEW", "color": OUTPUT / "LLRP-AAC-REVIEW_AAC_Board_COLOR.pdf", "bw": OUTPUT / "LLRP-AAC-REVIEW_AAC_Board_BW.pdf", "hv_black": OUTPUT / "LLRP-AAC-REVIEW_AAC_Board_COLOR_HIGHVIS_BLACK.pdf", "hv_yellow": OUTPUT / "LLRP-AAC-REVIEW_AAC_Board_COLOR_HIGHVIS_YELLOW.pdf", "overview_data": OVERVIEWS / "boardready_aac.json", "aac": True},
    {"id": "matching", "name": "Matching Cards", "code": "LLRP-MATCH-REVIEW", "color": OUTPUT / "LLRP-MATCH-REVIEW_Matching_COLOR.pdf", "bw": OUTPUT / "LLRP-MATCH-REVIEW_Matching_BW.pdf", "overview_data": OVERVIEWS / "matching.json"},
    {"id": "book_participation", "name": "Interactive Book Participation Pieces", "code": "LLRP-BPP-LAUNCH", "color": OUTPUT / "LLRP-BPP-LAUNCH_BookParticipation_COLOR.pdf", "bw": OUTPUT / "LLRP-BPP-LAUNCH_BookParticipation_BW.pdf", "overview_data": OVERVIEWS / "book_participation_pieces.json", "aac": True},
    {"id": "sentence_building", "name": "AAC Sentence Building", "code": "LLRP-SENT-LAUNCH", "color": OUTPUT / "LLRP-SENT-LAUNCH_AAC_SentenceStrips_COLOR.pdf", "bw": OUTPUT / "LLRP-SENT-LAUNCH_AAC_SentenceStrips_BW.pdf", "overview_data": OVERVIEWS / "sentence_building.json", "aac": True},
    {"id": "sequencing", "name": "Story Sequencing", "code": "LLRP-SEQ-LAUNCH", "color": OUTPUT / "LLRP-SEQ-LAUNCH_Sequencing_COLOR.pdf", "bw": OUTPUT / "LLRP-SEQ-LAUNCH_Sequencing_BW.pdf", "overview_data": OVERVIEWS / "sequencing.json"},
    {"id": "yes_no", "name": "Yes/No Questions", "code": "LLRP-YN-LAUNCH", "color": OUTPUT / "LLRP-YN-LAUNCH_YesNoQuestions_COLOR.pdf", "bw": OUTPUT / "LLRP-YN-LAUNCH_YesNoQuestions_BW.pdf", "overview_data": OVERVIEWS / "yes_no_questions.json"},
    {"id": "inferencing", "name": "Clue, Think, Infer: Inferencing Cards", "code": "LLRP-INF-LAUNCH", "color": OUTPUT / "LLRP-INF-LAUNCH_Inferencing_COLOR.pdf", "bw": OUTPUT / "LLRP-INF-LAUNCH_Inferencing_BW.pdf", "overview_data": OVERVIEWS / "inferencing_cards.json"},
    {"id": "vocabulary_snap", "name": "Vocabulary Snap", "code": "LLRP-VWW-LAUNCH", "color": OUTPUT / "LLRP-VWW-LAUNCH_WordSnap_SymbolText_COLOR.pdf", "bw": OUTPUT / "LLRP-VWW-LAUNCH_WordSnap_SymbolText_BW.pdf", "overview_data": OVERVIEWS / "vocabulary_snap.json"},
    {"id": "syllable_awareness", "name": "Syllable Awareness", "code": "LLRP-SYL-LAUNCH", "color": OUTPUT / "LLRP-SYL-LAUNCH_Syllable_Cards_COLOR.pdf", "bw": OUTPUT / "LLRP-SYL-LAUNCH_Syllable_Cards_BW.pdf", "overview_data": OVERVIEWS / "syllable_awareness.json"},
    {"id": "decoding", "name": "CVC Decode & Build", "code": "LLRP-DEC-LAUNCH", "color": OUTPUT / "LLRP-DEC-LAUNCH_Decoding_COLOR.pdf", "bw": OUTPUT / "LLRP-DEC-LAUNCH_Decoding_BW.pdf", "overview_data": OVERVIEWS / "decoding.json"},
    {"id": "story_grammar", "name": "Story Grammar & Retell", "code": "LLRP-SGM-LAUNCH", "color": OUTPUT / "LLRP-SGM-LAUNCH_Story_Elements_Mat_COLOR.pdf", "bw": OUTPUT / "LLRP-SGM-LAUNCH_Story_Elements_Mat_BW.pdf", "overview_data": OVERVIEWS / "story_grammar.json"},
    {"id": "word_search", "name": "Differentiated Word Search", "code": "LLRP-WS-LAUNCH", "color": OUTPUT / "LLRP-WS-LAUNCH_WordSearch_6Pages.pdf", "bw": OUTPUT / "LLRP-WS-LAUNCH_WordSearch_6Pages_BW.pdf", "overview_data": OVERVIEWS / "word_search.json"},
    {"id": "bingo", "name": "Differentiated Bingo", "code": "LLRP-BINGO-LAUNCH", "color": OUTPUT / "LLRP-BINGO-LAUNCH_Bingo_COLOR.pdf", "bw": OUTPUT / "LLRP-BINGO-LAUNCH_Bingo_BW.pdf", "overview_data": OVERVIEWS / "bingo.json"},
    {"id": "sorting", "name": "Reason & Sort: Category Sorting", "code": "LLRP-SORT-LAUNCH", "color": OUTPUT / "LLRP-SORT-LAUNCH_Sorting_COLOR.pdf", "bw": OUTPUT / "LLRP-SORT-LAUNCH_Sorting_BW.pdf", "overview_data": OVERVIEWS / "sorting.json"},
    {"id": "print_detective", "name": "Print Detective: Letters, Words & First Sounds", "code": "LLRP-PD-LAUNCH", "color": OUTPUT / "LLRP-PD-LAUNCH_PrintDetective_COLOR.pdf", "bw": OUTPUT / "LLRP-PD-LAUNCH_PrintDetective_BW.pdf", "overview_data": OVERVIEWS / "print_detective.json"},
]


def _safe(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 ]", "", value.replace("&", "and").replace("/", " ").replace("-", " "))
    return "_".join(part for part in cleaned.split() if part)


def _sample_indices(page_count: int, key: str, limit: int = 5) -> list[int]:
    if page_count <= limit:
        return list(range(page_count))
    rng = random.Random(int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:16], 16))
    middle = list(range(1, page_count - 1))
    chosen = rng.sample(middle, min(limit - 2, len(middle)))
    return sorted([0, *chosen, page_count - 1])


def _preview(source: Path, destination: Path, key: str) -> tuple[list[int], int]:
    document = fitz.open(source)
    indices = _sample_indices(len(document), key)
    pdf = canvas.Canvas(str(destination))
    for index in indices:
        page = document.load_page(index)
        width, height = page.rect.width, page.rect.height
        pdf.setPageSize((width, height))
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        buffer = io.BytesIO(); image.save(buffer, "PNG"); buffer.seek(0)
        pdf.drawImage(ImageReader(buffer), 0, 0, width=width, height=height)
        pdf.saveState()
        try:
            pdf.setFillAlpha(0.25)
        except Exception:
            pass
        pdf.setFillGray(0.45)
        pdf.setFont("Helvetica-Bold", 52 if width < 700 else 64)
        pdf.translate(width / 2, height / 2)
        pdf.rotate(38)
        pdf.drawCentredString(0, 0, "PREVIEW · SMALL WINS STUDIO")
        pdf.restoreState()
        pdf.showPage()
    pdf.save()
    document.close()
    return indices, len(indices)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, width: int, max_lines: int = 4) -> list[str]:
    lines, current = [], ""
    for word in str(text).split():
        candidate = f"{current} {word}".strip()
        if not current or draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            lines.append(current); current = word
            if len(lines) >= max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines


def _draw_text(draw: ImageDraw.ImageDraw, text: str, box: tuple[int, int, int, int], pt: int, bold: bool = False, max_lines: int = 4):
    font = _font(pt, bold)
    y = box[1]
    for line in _wrap(draw, text, font, box[2] - box[0], max_lines):
        draw.text((box[0], y), line, font=font, fill=hex_to_rgb(SWS_NAVY if bold else "#334E68"))
        y += draw.textbbox((0, 0), line, font=font)[3] + 10


def _quick_start(product: dict, destination: Path) -> None:
    data = json.loads(product["overview_data"].read_text(encoding="utf-8"))
    # Resolve hero icon for the accent strip
    hero_img = None
    try:
        for hp in [THEME / "hero.png", THEME / "hero_header.png"]:
            if hp.exists():
                im = Image.open(hp)
                hero_img = im.convert("RGBA") if im.mode != "RGBA" else im
                break
    except Exception:
        pass
    page = _activity_page("Quick Start", data["product_name"], product["code"], 1, 1, header_left_icon=hero_img)
    draw = ImageDraw.Draw(page)
    sections = [
        ("PREPARE", f"{data['preparation']['label']}. Materials: {data['preparation']['materials']}. Estimated preparation: {data['preparation']['time']}."),
        ("TEACH", " ".join(f"{index + 1}. {step['title']}: {step['detail']}" for index, step in enumerate(data["teaching_steps"]))),
        ("ACCESS", " ".join(data["access"])),
        ("BEST FOR", " · ".join(data["best_for"])),
        ("CHECK", "Review the Color and B&W files, choose the appropriate level, and verify all answer support before teaching."),
    ]
    top = 540
    for heading, body in sections:
        box = (210, top, int(612 * DPI / 72) - 210, top + 470)
        draw.rounded_rectangle(box, radius=38, fill=hex_to_rgb(SWS_TEAL_LT), outline=hex_to_rgb(SWS_TEAL), width=4)
        _draw_text(draw, heading, (275, top + 55, 850, top + 155), 13, True, 1)
        _draw_text(draw, body, (900, top + 55, box[2] - 70, top + 405), 10, False, 4)
        top += 515
    _save_pdf(destination, [page])


def _validate_product(product: dict) -> None:
    for field in ("color", "bw", "overview_data"):
        if not product[field].is_file():
            raise FileNotFoundError(f"{product['name']}: missing {field}: {product[field]}")
    if not TOU.is_file():
        raise FileNotFoundError(TOU)
    if not BUNDLE_GUIDE.is_file():
        raise FileNotFoundError(BUNDLE_GUIDE)


def package_product(product: dict) -> dict:
    _validate_product(product)
    monitoring = _ensure_monitoring_form()
    _ensure_tou()
    _ensure_bundle_guide()
    product_dir = PACKAGE_ROOT / f"{product['code']}_{_safe(product['name'])}"
    product_dir.mkdir(parents=True, exist_ok=True)
    preview = product_dir / f"{product['code']}_{_safe(product['name'])}_PREVIEW.pdf"
    quick_start = product_dir / f"{product['code']}_{_safe(product['name'])}_Quick_Start.pdf"
    indices, preview_pages = _preview(product["color"], preview, product["code"])
    _quick_start(product, quick_start)
    zip_path = PACKAGE_ROOT / f"{product['code']}_{_safe(product['name'])}_REVIEW.zip"
    archive_files = [
        (BUNDLE_GUIDE, "00_ALSO_IN_THIS_BUNDLE/LLRP_Complete_Bundle_Start_Here.pdf"),
        (product["color"], f"01_RESOURCE/{product['color'].name}"),
        (product["bw"], f"02_INK_FRIENDLY/{product['bw'].name}"),
        (quick_start, f"03_TEACHER_SUPPORT/{quick_start.name}"),
        (monitoring, "03_TEACHER_SUPPORT/LLRP_IEP_Progress_Monitoring_Form.pdf"),
        (TOU, "04_LICENSE/Terms of Use.pdf"),
        (preview, f"05_MARKETING_PREVIEW/{preview.name}"),
    ]
    if product.get("aac"):
        # Top Tips are now included as a page in the Bundle Start Here guide
        # Include high-visibility variants for visually impaired students
        hv_black = product.get("hv_black")
        hv_yellow = product.get("hv_yellow")
        if hv_black and Path(hv_black).is_file():
            archive_files.append((hv_black, f"01_RESOURCE/{Path(hv_black).name}"))
        if hv_yellow and Path(hv_yellow).is_file():
            archive_files.append((hv_yellow, f"01_RESOURCE/{Path(hv_yellow).name}"))
    color_pages = len(fitz.open(product["color"]))
    bw_pages = len(fitz.open(product["bw"]))
    manifest = {
        "schema_version": 1,
        "status": "review_ready_not_approved",
        "product_id": product["id"],
        "product_name": product["name"],
        "product_code": product["code"],
        "color_pages": color_pages,
        "bw_pages": bw_pages,
        "preview_pages": preview_pages,
        "preview_source_pages": [index + 1 for index in indices],
        "watermark": "PREVIEW · SMALL WINS STUDIO",
        "suggested_price_usd": SUGGESTED_PRICES_USD.get(product["id"]),
        "files": [{"source": str(path), "archive": arc, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path, arc in archive_files],
    }
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, arc in archive_files:
            archive.write(path, arc)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    manifest_path = product_dir / "package_manifest.json"
    manifest_path.write_text(json.dumps({**manifest, "zip": str(zip_path)}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"name": product["name"], "code": product["code"], "zip": str(zip_path), "manifest": str(manifest_path), "color_pages": color_pages, "preview_pages": preview_pages, "suggested_price_usd": SUGGESTED_PRICES_USD.get(product["id"]), "status": manifest["status"]}


def _review_html(records: list[dict]) -> str:
    rows = "".join(f"<tr><td>{index}</td><td>{record['name']}</td><td>{record['color_pages']}</td><td>{record['preview_pages']}</td><td>${record['suggested_price_usd']:.2f}</td><td><a href='{Path(record['zip']).name}'>Open ZIP</a></td><td>Not reviewed</td></tr>" for index, record in enumerate(records, start=1))
    total = sum(r["suggested_price_usd"] or 0 for r in records)
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>Final Activity Review List</title><style>body{{font-family:Segoe UI,Arial;margin:30px;color:#0D2545}}h1{{color:#006379}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd8df;padding:10px;text-align:left}}th{{background:#31A8A0;color:white}}.note{{background:#e8f8f8;padding:14px;border-left:5px solid #006379}}</style></head><body><h1>Final Activity Review List</h1><p class='note'>These packages are review-ready, not approved for sale. Open each ZIP, check Color, B&W, Quick Start, Bundle Start Here, IEP Monitoring Form, Terms of Use and Preview, then record approval.</p><table><thead><tr><th>#</th><th>Activity</th><th>Color pages</th><th>Preview pages</th><th>Suggested price</th><th>Package</th><th>Decision</th></tr></thead><tbody>{rows}</tbody></table><p class='note'>Suggested individual total: <strong>${total:.2f}</strong> · Suggested bundle price (≈25–30% off): <strong>${SUGGESTED_BUNDLE_PRICE_USD:.2f}</strong> · Free Sampler: <strong>$0.00</strong></p><p><a href='LLRP_COMPLETE_BUNDLE_REVIEW.zip'>Open complete bundle review ZIP</a></p></body></html>"""


def package_suite() -> list[dict]:
    PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    records = [package_product(product) for product in PRODUCTS]
    index = {"schema_version": 1, "status": "review_ready_not_approved", "generated_at": datetime.now().isoformat(timespec="seconds"), "product_count": len(records), "suggested_individual_total_usd": round(sum(r["suggested_price_usd"] or 0 for r in records), 2), "suggested_bundle_price_usd": SUGGESTED_BUNDLE_PRICE_USD, "products": records}
    (PACKAGE_ROOT / "FINAL_ACTIVITY_REVIEW_LIST.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (PACKAGE_ROOT / "FINAL_ACTIVITY_REVIEW_LIST.html").write_text(_review_html(records), encoding="utf-8")
    suite_zip = PACKAGE_ROOT / "LLRP_COMPLETE_BUNDLE_REVIEW.zip"
    with zipfile.ZipFile(suite_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(BUNDLE_GUIDE, f"00_START_HERE/{BUNDLE_GUIDE.name}")
        for record in records:
            archive.write(record["zip"], f"ACTIVITY_PACKAGES/{Path(record['zip']).name}")
        archive.writestr("FINAL_ACTIVITY_REVIEW_LIST.json", json.dumps(index, ensure_ascii=False, indent=2))
    return records


if __name__ == "__main__":
    result = package_suite()
    print(json.dumps({"count": len(result), "output": str(PACKAGE_ROOT)}, indent=2))
