"""Generate a branded Terms of Use PDF for Small Wins Studio products."""
import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image, ImageDraw
from utils.sws_design import (
    apply_small_wins_frame, DPI, hex_to_rgb, NAVY_HEX,
    DEFAULT_ACCENT_TEAL_HEX, _brand_font_pt,
)
from pathlib import Path

PAGE_W, PAGE_H = letter
IMG_W = int(PAGE_W * DPI / 72)
IMG_H = int(PAGE_H * DPI / 72)

page = Image.new("RGB", (IMG_W, IMG_H), "white")
d = ImageDraw.Draw(page)
scale = DPI / 72

apply_small_wins_frame(
    page,
    product_title="Terms of Use",
    subtitle="Small Wins Studio",
    pack_code="SWS-TOU",
    page_num=1,
    total_pages=1,
    level=None,
    draw_accent_strip=True,
    draw_header=True,
    draw_subtitle=True,
    draw_footer=True,
    footer_title="Small Wins Studio | Terms of Use",
)

left = int(0.55 * DPI)
right = IMG_W - int(0.55 * DPI)
top = int(1.35 * DPI)
max_w = right - left

y = top
line_h = int(0.20 * DPI)
section_gap = int(0.12 * DPI)

heading_font = _brand_font_pt(13, bold=True, brand="poppins")
body_font = _brand_font_pt(9.5, bold=False, brand="poppins")
small_font = _brand_font_pt(8.5, bold=False, brand="poppins")

navy = hex_to_rgb(NAVY_HEX)
grey = (102, 102, 102)

sections = [
    ("Thank You", [
        "Thank you for purchasing this Small Wins Studio resource. Your support",
        "helps us create accessible, differentiated materials for special education",
        "classrooms, AAC users, and emergent readers.",
    ]),
    ("License", [
        "This product is licensed for single-classroom or single-therapist use.",
        "You may print and copy materials for your own students or clients, share",
        "printed materials with co-teachers in the same classroom, and use the",
        "digital files on your own devices for instruction.",
        "",
        "You may NOT redistribute, sell, or share the digital files; post them on",
        "public websites or shared drives; claim the designs as your own; or",
        "remove the Small Wins Studio branding.",
    ]),
    ("Boardmaker PCS Symbols", [
        "Boardmaker PCS symbols used with active PCS Maker",
        "Personal License. Symbols remain property of Tobii Dynavox.",
    ]),
    ("Differentiated Access", [
        "Many Small Wins Studio activities include differentiated options:",
        "pointing and eye-gaze desk strips, high-visibility AAC board variants,",
        "storage labels for organizing cut-out pieces, and multiple difficulty",
        "levels within each activity. Choose the options that best meet your",
        "students' individual needs.",
    ]),
    ("IEP Monitoring Form", [
        "An IEP Monitoring Form is included as a bonus in the bundle for",
        "tracking student progress across Small Wins Studio activities.",
    ]),
    ("Refunds", [
        "Refunds are governed by the Teachers Pay Teachers platform policy.",
        "If you experience a technical issue with the files, please contact us",
        "through our TPT store for a replacement.",
    ]),
    ("Disclaimer", [
        "This resource is provided 'as is' without warranty of any kind. Small",
        "Wins Studio is not liable for damages arising from the use of this",
        "product. The IEP Monitoring Form is a support tool and does not",
        "constitute professional educational or legal advice.",
    ]),
    ("Questions?", [
        "For licensing questions, custom requests, or bulk purchases,",
        "please contact us through our TPT store.",
    ]),
]

for heading, lines in sections:
    d.text((left, y), heading, fill=navy, font=heading_font)
    y += int(0.26 * DPI)
    for line in lines:
        d.text((left, y), line, fill=navy, font=body_font)
        y += line_h
    y += section_gap

# Note: Do NOT add a duplicate copyright line here.
# The standard footer drawn by apply_small_wins_frame already contains
# "© 2026 Small Wins Studio" — adding another line here overlaps it.

# Save
out_path = Path("assets/global/tpt_support_docs/Terms of Use.pdf")
out_path.parent.mkdir(parents=True, exist_ok=True)

buf = io.BytesIO()
page.save(buf, format="PNG", dpi=(DPI, DPI))
buf.seek(0)

from reportlab.lib.utils import ImageReader
c = canvas.Canvas(str(out_path), pagesize=letter)
c.drawImage(ImageReader(buf), 0, 0, width=PAGE_W, height=PAGE_H)
c.showPage()
c.save()
print(f"Generated: {out_path}")
