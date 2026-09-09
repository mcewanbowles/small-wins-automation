"""Build a single-contact review dashboard HTML for the 15 final activity packages.

- Extracts up to 3 preview thumbnails from each package's PREVIEW.pdf using PyMuPDF.
- Emits REVIEW_DASHBOARD.html with per-activity card: thumbnails, decision dropdown,
  notes textarea. Decisions/notes persist to localStorage and can be exported as JSON.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).parent
LIST_JSON = ROOT / "FINAL_ACTIVITY_REVIEW_LIST.json"
OUT_HTML = ROOT / "REVIEW_DASHBOARD.html"
ASSETS_DIR = ROOT / "REVIEW_DASHBOARD_ASSETS"
ASSETS_DIR.mkdir(exist_ok=True)


def render_preview_thumbs(preview_pdf: Path, code: str, max_pages: int = 3) -> list[str]:
    """Render up to max_pages pages from preview_pdf to PNGs; return relative paths."""
    rel_paths: list[str] = []
    if not preview_pdf.exists():
        return rel_paths
    try:
        doc = fitz.open(str(preview_pdf))
    except Exception as exc:  # noqa: BLE001
        print(f"  ! open failed for {preview_pdf.name}: {exc}")
        return rel_paths
    n = min(max_pages, doc.page_count)
    for i in range(n):
        out = ASSETS_DIR / f"{code}_p{i + 1}.png"
        try:
            page = doc.load_page(i)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4))
            pix.save(str(out))
            rel_paths.append(f"REVIEW_DASHBOARD_ASSETS/{out.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! render failed p{i + 1} of {code}: {exc}")
    doc.close()
    return rel_paths


def main() -> None:
    data = json.loads(LIST_JSON.read_text(encoding="utf-8"))
    rows: list[dict] = []
    for prod in data["products"]:
        code = prod["code"]
        name = prod["name"]
        pkg_dir = Path(prod["manifest"]).parent
        # Use COLOR.pdf for thumbnails (the actual activity), not PREVIEW.pdf
        color_pdf = next(pkg_dir.glob("*COLOR.pdf"), None)
        preview_pdf = next(pkg_dir.glob("*PREVIEW.pdf"), None)
        # Render thumbnails from the COLOR PDF (up to 5 pages for better review)
        thumbs = render_preview_thumbs(color_pdf, code, max_pages=5) if color_pdf else (render_preview_thumbs(preview_pdf, code, max_pages=5) if preview_pdf else [])
        color_rel = f"{pkg_dir.name}/{color_pdf.name}" if color_pdf else ""
        preview_rel = f"{pkg_dir.name}/{preview_pdf.name}" if preview_pdf else ""
        rows.append({
            "id": code,
            "name": name,
            "code": code,
            "color_pages": prod["color_pages"],
            "preview_pages": prod["preview_pages"],
            "zip": Path(prod["zip"]).name,
            "pkg_dir": pkg_dir.name,
            "color_pdf": color_rel,
            "preview_pdf": preview_rel,
            "thumbs": thumbs,
        })

    rows_json = json.dumps(rows, ensure_ascii=False)
    html = build_html(rows_json)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"Thumbnails in {ASSETS_DIR}")


def build_html(rows_json: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Final Activity Review Dashboard</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #f4f7f9; color: #153047; }}
header {{ position: sticky; top: 0; z-index: 2; background: #fff; border-bottom: 1px solid #ccd8df; padding: 14px 20px; }}
h1 {{ margin: 0 0 8px; color: #006379; }}
.toolbar {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
.stats {{ font-weight: 600; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 16px; padding: 18px; }}
.card {{ background: #fff; border: 1px solid #ccd8df; border-radius: 10px; padding: 14px; box-shadow: 0 2px 8px #16304712; }}
.card h2 {{ font-size: 18px; margin: 0 0 4px; }}
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
  <h1>Final Activity Review Dashboard</h1>
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
  <p style="margin:6px 0 0; font-size:13px; color:#587080">
    15 finalised activity packages. For each: open the Color PDF / Preview, check pages,
    pick a Decision, and note any problems. Your entries persist in this browser and can be
    exported to <code>final_activity_review_decisions.json</code>.
  </p>
</header>
<main class="grid" id="grid"></main>
<script>
const rows = {rows_json};
const storeKey = 'final_activity_review_2026_09_05';
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
      ? r.thumbs.map((p, i) => `<a href="${{esc(r.color_pdf || r.preview_pdf)}}" target="_blank"><img src="${{esc(p)}}" alt="Page ${{i + 1}}"></a>`).join('')
      : '<div class="empty">No color PDF thumbnail</div>';
    const colorLink = r.color_pdf
      ? `<a href="${{esc(r.color_pdf)}}" target="_blank">Open Color PDF</a> · `
      : '';
    const previewLink = r.preview_pdf
      ? `<a href="${{esc(r.preview_pdf)}}" target="_blank">Open Preview PDF</a> · `
      : '';
    card.innerHTML = `
      <h2>${{esc(r.name)}}</h2>
      <div class="meta">${{esc(r.code)}} · ${{r.color_pages}} color pp · ${{r.preview_pages}} preview pp</div>
      <div style="margin:6px 0">
        <span class="flag ok">${{r.color_pages}} color</span>
        <span class="flag">${{r.preview_pages}} preview</span>
        <span class="flag">${{esc(r.zip)}}</span>
      </div>
      <div style="font-size:12px; margin:6px 0">
        ${{colorLink}}${{previewLink}}<a href="${{esc(r.zip)}}" download>Download ZIP</a>
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
        <textarea class="notes" placeholder="Describe any issues: footer, cover, IEP form, page order, image quality...">${{esc(s.notes || '')}}</textarea>
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
    archive: 'FINAL_ACTIVITY_PACKAGES_2026-09-05',
    exported_at: new Date().toISOString(),
    reviews: state
  }};
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }}));
  a.download = 'final_activity_review_decisions.json';
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
