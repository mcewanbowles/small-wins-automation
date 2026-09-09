"""Build a review dashboard HTML for a single book's current OUTPUT folder.

Scans the book's OUTPUT directory for *COLOR*.pdf files, renders up to 5
thumbnails per PDF, and emits an HTML dashboard for visual review.

Usage:
    python _build_book_dashboard.py <book_slug> [output_dir]

If output_dir is omitted, the script resolves it via the standard themes roots.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF (fitz) is required: pip install pymupdf", file=sys.stderr)
    sys.exit(1)


def _extract_product_key(stem: str) -> str:
    """Extract a normalized product key from a PDF stem for deduplication.

    e.g. 'LLR01_Matching_COLOR' -> 'matching'
         'LLRP-MATCH-REVIEW_Matching_COLOR' -> 'matching'
         'LLR01_WordSearch_COLOR' -> 'wordsearch'
    """
    s = stem.lower()
    # Remove common suffixes
    for suffix in ["_color", "_bw", "_preview"]:
        s = s.replace(suffix, "")
    # Known product keywords to match
    keywords = [
        "matching", "wordsearch", "word_search", "findandcover", "find_and_cover",
        "sentences", "sentencestrips", "aac_board", "sequencing", "sorting",
        "bingo", "spincover", "yesno", "yes_no", "inferencing", "inference",
        "wordsnap", "word_snap", "syllable", "printdetective", "print_detective",
        "decoding", "story_elements", "retell", "bookparticipation",
        "adaptedbook", "codewords", "code_words", "patternstrips",
        "labelingworksheets", "qr_scavenger", "scarboroughrope",
    ]
    for kw in keywords:
        if kw in s:
            return kw.replace("_", "")
    # Fallback: use everything after the first separator
    parts = s.replace("-", "_").split("_", 1)
    return parts[1] if len(parts) > 1 else s


def find_book_dir(slug: str) -> Path | None:
    root = Path(__file__).resolve().parent.parent
    candidates = [
        root / "assets" / "themes" / slug,
        root / "production" / "final_products" / slug,
    ]
    env = os.environ.get("SF_THEMES_ROOT", "").strip()
    if env:
        candidates.insert(0, Path(env) / slug)
    for c in candidates:
        if c.exists():
            return c
    return None


def render_thumbs(pdf_path: Path, code: str, assets_dir: Path, max_pages: int = 5) -> list[str]:
    rel_paths: list[str] = []
    if not pdf_path.exists():
        return rel_paths
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        print(f"  ! open failed for {pdf_path.name}: {exc}")
        return rel_paths
    n = min(max_pages, doc.page_count)
    for i in range(n):
        out = assets_dir / f"{code}_p{i + 1}.png"
        try:
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4))
            pix.save(str(out))
            rel_paths.append(f"REVIEW_DASHBOARD_ASSETS/{out.name}")
        except Exception as exc:
            print(f"  ! render failed p{i + 1} of {code}: {exc}")
    doc.close()
    return rel_paths


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python _build_book_dashboard.py <book_slug> [output_dir]", file=sys.stderr)
        sys.exit(1)
    slug = sys.argv[1]
    if len(sys.argv) >= 3:
        output_dir = Path(sys.argv[2])
    else:
        book_dir = find_book_dir(slug)
        if not book_dir:
            print(f"Book directory not found for slug: {slug}", file=sys.stderr)
            sys.exit(1)
        output_dir = book_dir / "OUTPUT"

    if not output_dir.exists():
        print(f"OUTPUT directory not found: {output_dir}", file=sys.stderr)
        sys.exit(1)

    # Dashboard output location: inside the OUTPUT folder
    dash_dir = output_dir / "_REVIEW_DASHBOARD"
    dash_dir.mkdir(exist_ok=True)
    assets_dir = dash_dir / "REVIEW_DASHBOARD_ASSETS"
    assets_dir.mkdir(exist_ok=True)
    out_html = dash_dir / "REVIEW_DASHBOARD.html"

    # Find all COLOR PDFs, sorted by modification time (newest first)
    all_color_pdfs = sorted(output_dir.glob("*COLOR*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)

    # Deduplicate: keep only the newest PDF per product type
    # (multiple pack codes may produce the same product, e.g. LLR01_Matching and LLRP-MATCH-REVIEW_Matching)
    seen_products: dict[str, Path] = {}
    for pdf_path in all_color_pdfs:
        name_lower = pdf_path.name.lower()
        if "highvis" in name_lower:
            continue
        # Extract product type by stripping the pack code prefix
        # Pack code is everything before the first product keyword
        stem = pdf_path.stem
        product_key = _extract_product_key(stem)
        if product_key not in seen_products:
            seen_products[product_key] = pdf_path

    # Use only the deduplicated set (already sorted newest-first)
    color_pdfs = list(seen_products.values())

    # Filter to main products only: exclude WordSnap/WordWall variants that are
    # generated as supplements to the core Vocabulary Snap activity
    _variant_keywords = ("extracopy", "textonly", "symbolonly", "symboltext", "banner")
    color_pdfs = [
        p for p in color_pdfs
        if not any(k in p.stem.lower() for k in _variant_keywords)
    ]

    rows: list[dict] = []
    for pdf_path in color_pdfs:
        code = pdf_path.stem
        # Try to find a matching BW and PREVIEW pdf
        bw_pdf = output_dir / pdf_path.name.replace("_COLOR", "_BW")
        preview_pdf = output_dir / pdf_path.name.replace("_COLOR", "_PREVIEW")
        thumbs = render_thumbs(pdf_path, code, assets_dir, max_pages=5)
        stat = pdf_path.stat()
        rows.append({
            "id": code,
            "name": code.replace("_", " ").replace("LLRP", "").strip(),
            "code": code,
            "color_pdf": pdf_path.name,
            "bw_pdf": bw_pdf.name if bw_pdf.exists() else "",
            "preview_pdf": preview_pdf.name if preview_pdf.exists() else "",
            "size_kb": round(stat.st_size / 1024),
            "modified": str(__import__("datetime").datetime.fromtimestamp(stat.st_mtime)),
            "thumbs": thumbs,
        })

    rows_json = json.dumps(rows, ensure_ascii=False)
    html = build_html(rows_json, slug, str(output_dir))
    out_html.write_text(html, encoding="utf-8")
    print(f"Wrote {out_html}")
    print(f"Thumbnails in {assets_dir}")
    print(f"Found {len(rows)} COLOR PDFs")


def build_html(rows_json: str, slug: str, output_dir: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Activity Review Dashboard - {slug}</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f4f7f9; color: #153047; }}
header {{ position: sticky; top: 0; z-index: 2; background: #fff; border-bottom: 1px solid #ccd8df; padding: 14px 20px; }}
h1 {{ margin: 0 0 8px; color: #006379; }}
.toolbar {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
.stats {{ font-weight: 600; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; padding: 18px; }}
.card {{ background: #fff; border: 1px solid #ccd8df; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px #16304712; }}
.card h2 {{ font-size: 16px; margin: 0 0 4px; }}
.meta {{ font-size: 12px; color: #587080; overflow-wrap: anywhere; }}
.pages {{ display: flex; gap: 8px; overflow-x: auto; margin: 12px 0; min-height: 220px; }}
.pages img {{ height: 220px; border: 1px solid #ccd8df; background: #eee; }}
.flag {{ display: inline-block; padding: 3px 7px; border-radius: 12px; background: #e0eef0; color: #153047; font-size: 12px; margin-right: 5px; }}
.flag.ok {{ background: #dcfce7; color: #166534; }}
.form {{ display: grid; grid-template-columns: 130px 1fr; gap: 8px; align-items: start; margin-top: 8px; }}
.form select, .form textarea {{ font: inherit; padding: 7px; border: 1px solid #aebfc9; border-radius: 6px; }}
.form textarea {{ min-height: 80px; resize: vertical; }}
.empty {{ height: 220px; display: grid; place-items: center; background: #f8fafc; border: 1px dashed #b8c7d0; width: 100%; color: #587080; }}
button, input {{ font: inherit; padding: 7px 10px; }}
a {{ color: #006379; }}
.approved .card {{ border-color: #166534; box-shadow: 0 2px 8px #16653422; }}
.revise .card {{ border-color: #b45309; }}
.retest .card {{ border-color: #b45309; border-style: dashed; }}
.archive .card {{ opacity: 0.6; }}
</style>
</head>
<body>
<header>
  <h1>Activity Review Dashboard</h1>
  <div style="font-size:13px; color:#587080; margin-bottom:8px">Book: <strong>{slug}</strong> &middot; Source: <code>{output_dir}</code></div>
  <div class="toolbar">
    <input id="search" placeholder="Filter activity name or code">
    <select id="statusFilter">
      <option value="">All decisions</option>
      <option>Unreviewed</option>
      <option>Approve</option>
      <option>Revise</option>
      <option>Retest</option>
      <option>Archive</option>
    </select>
    <button id="export">Export decisions (JSON)</button>
    <button id="import">Import decisions</button>
    <input type="file" id="importFile" accept="application/json" style="display:none">
    <span class="stats" id="stats"></span>
  </div>
</header>
<main class="grid" id="grid"></main>
<script>
const rows = {rows_json};
const storeKey = 'book_review_{slug}';
let state = JSON.parse(localStorage.getItem(storeKey) || '{{}}');

function esc(s) {{
  return String(s || '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
}}
function save() {{ localStorage.setItem(storeKey, JSON.stringify(state)); stats(); }}
function stats() {{
  const counts = {{}};
  rows.forEach(r => {{
    const d = (state[r.id] || {{}}).decision || 'Unreviewed';
    counts[d] = (counts[d] || 0) + 1;
  }});
  document.getElementById('stats').textContent =
    Object.entries(counts).map(([k, v]) => k + ': ' + v).join(' | ');
}}
function render() {{
  const q = document.getElementById('search').value.toLowerCase();
  const sf = document.getElementById('statusFilter').value;
  const grid = document.getElementById('grid');
  grid.innerHTML = '';
  rows.forEach(r => {{
    const s = state[r.id] || {{}};
    const decision = s.decision || 'Unreviewed';
    if (q && !(`${{r.name}} ${{r.code}}`.toLowerCase().includes(q))) return;
    if (sf && decision !== sf) return;
    const card = document.createElement('section');
    card.className = 'card ' + decision.toLowerCase();
    const pages = r.thumbs.length
      ? r.thumbs.map((p, i) => `<img src="${{esc(p)}}" alt="Page ${{i + 1}}">`).join('')
      : '<div class="empty">No thumbnail available</div>';
    const colorLink = r.color_pdf
      ? `<a href="../${{esc(r.color_pdf)}}" target="_blank">Open Color PDF</a> &middot; `
      : '';
    const bwLink = r.bw_pdf
      ? `<a href="../${{esc(r.bw_pdf)}}" target="_blank">BW PDF</a> &middot; `
      : '';
    card.innerHTML = `
      <h2>${{esc(r.name)}}</h2>
      <div class="meta">${{esc(r.code)}} &middot; ${{r.size_kb}} KB &middot; ${{r.modified}}</div>
      <div style="margin:6px 0">
        <span class="flag ok">COLOR</span>
        ${{r.bw_pdf ? '<span class="flag">BW</span>' : ''}}
      </div>
      <div style="font-size:12px; margin:6px 0">
        ${{colorLink}}${{bwLink}}
      </div>
      <div class="pages">${{pages}}</div>
      <div class="form">
        <label>Decision</label>
        <select class="decision">
          <option>Unreviewed</option>
          <option>Approve</option>
          <option>Revise</option>
          <option>Retest</option>
          <option>Archive</option>
        </select>
        <label>Problems / notes</label>
        <textarea class="notes" placeholder="Describe any issues: footer, cover, image quality...">${{esc(s.notes || '')}}</textarea>
      </div>`;
    const sel = card.querySelector('.decision');
    sel.value = decision;
    sel.onchange = () => {{
      state[r.id] = {{ ...(state[r.id] || {{}}), decision: sel.value }};
      card.className = 'card ' + sel.value.toLowerCase();
      save();
    }};
    const notes = card.querySelector('.notes');
    notes.oninput = () => {{
      state[r.id] = {{ ...(state[r.id] || {{}}), notes: notes.value }};
      save();
    }};
    grid.appendChild(card);
  }});
  stats();
}}
document.getElementById('search').oninput = render;
document.getElementById('statusFilter').onchange = render;
document.getElementById('export').onclick = () => {{
  const payload = {{
    book: '{slug}',
    exported_at: new Date().toISOString(),
    reviews: state
  }};
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }}));
  a.download = 'book_review_decisions.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 0);
}};
document.getElementById('import').onclick = () => document.getElementById('importFile').click();
document.getElementById('importFile').onchange = (ev) => {{
  const file = ev.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {{
    try {{
      const parsed = JSON.parse(reader.result);
      state = parsed.reviews || parsed;
      localStorage.setItem(storeKey, JSON.stringify(state));
      render();
      alert('Imported ' + Object.keys(state).length + ' decisions');
    }} catch (e) {{
      alert('Invalid JSON: ' + e.message);
    }}
  }};
  reader.readAsText(file);
}};
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
