import sys
import json
import os
import mimetypes
import shutil
import urllib.parse as _u
import urllib.request as _urlreq
import urllib.error as _urlerr
import io
import re
import webbrowser
import threading
import time
import uuid
import base64
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import datetime as _dt
import importlib.util as _ilu

try:
    from boardready.modules import qa_logic  # type: ignore
except Exception:
    pkg_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(pkg_root))
    import modules.qa_logic as qa_logic  # type: ignore

BASE = qa_logic.BASE
ASSETS = qa_logic.ASSETS_DIR

# PDF extractor configuration/state (ported from legacy tool)
try:
    from PIL import Image, ImageDraw  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
try:
    import fitz  # PyMuPDF  # type: ignore
except Exception:  # pragma: no cover
    fitz = None  # type: ignore

try:
    import vocab_review_bridge as _vrb  # type: ignore
except Exception:
    _vrb = None  # type: ignore

try:
    from tools import ai_prep_runner as _aip  # type: ignore
except Exception:
    _aip = None  # type: ignore
    try:
        _p = Path(__file__).resolve().parent / "tools" / "ai_prep_runner.py"
        if _p.exists():
            _spec = _ilu.spec_from_file_location("ai_prep_runner_mod", str(_p))
            if _spec and _spec.loader:
                _m = _ilu.module_from_spec(_spec)
                _spec.loader.exec_module(_m)  # type: ignore[attr-defined]
                _aip = _m  # type: ignore
    except Exception:
        _aip = None  # type: ignore

def _pick_pdf_source_folder() -> Path:
    cands = [
        BASE / "Boardmaker_pdfs",
        Path(r"D:\Seagate\Boardmaker_pdfs"),
    ]
    for c in cands:
        try:
            if c.exists():
                return c
        except Exception:
            continue
    return cands[0]

PDF_SOURCE_FOLDER = _pick_pdf_source_folder()
SYMBOLS_ALPHA_ROOT = ASSETS / "symbols" / "png" / "Alpha"
PROVENANCE_FILE = SYMBOLS_ALPHA_ROOT / "icon_provenance.json"
LABELS_FILE = SYMBOLS_ALPHA_ROOT / "icon_labels.json"
EXTRACTED_LOG_FILE = SYMBOLS_ALPHA_ROOT / "extracted_pdfs_log.json"
WORK_DIR = BASE / "Studioforge" / "_icon_labeler_work"
SETTINGS_FILE = WORK_DIR / "settings.json"

# In-memory extractor state (session-scoped)
PDF_STATE = {
    "tiles": {},   # tile_id -> {path: str, w: int, h: int}
    "__notes__": """
async function autoFillOverview(){ const bk=$('#book').value; const t=document.getElementById('overview'); if(!bk||!t){ return; } try{ const r=await j('/api/ai_preview?book='+encodeURIComponent(bk)); if(!r.ok){ alert(r.error||'Backend not available'); return; } const s=r.suggestion||{}; const uniq=(arr)=>{ const seen={}; const out=[]; (arr||[]).forEach(x=>{ const k=String(x||'').trim(); if(k && !seen[k.toLowerCase()]){ seen[k.toLowerCase()]=1; out.push(k); } }); return out; }; const core=uniq(s.core_verbs||[]).slice(0,12); const fringe=uniq(s.aac_fringe_vocab||[]).slice(0,24); const ws=uniq(s.word_search_words||[]).slice(0,16); const lines=[]; if(typeof s.summary==='string' && s.summary.trim()){ lines.push(s.summary.trim()); } if(core.length||fringe.length){ lines.push('Key vocab: '+uniq(core.concat(fringe)).join(', ')); } if(ws.length){ lines.push('Word search: '+ws.join(', ')); } lines.push('WH prompts: Who is in the story? What happened? Where is it set? When does it happen? Why did it happen? How do they feel?'); lines.push('Yes/No prompts: Can you find the '+(fringe[0]||'item')+'? Do you see it now? Is this the right one?'); t.value=lines.join('\n\n'); }catch(e){ alert('Auto-fill failed (backend not running)'); } }
""",
    "groups": [],  # [{pdf: str, tiles: [tile_id], suggested_book: str}]
}
PDF_TILE_DIR = WORK_DIR / "tiles"

# Background job registry for vocab ops
VOCAB_JOBS = {}

def _new_job(kind: str, total: int = 0) -> str:
    jid = f"{kind}-{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"
    VOCAB_JOBS[jid] = {"status": "running", "done": 0, "total": int(total or 0), "results": []}
    return jid

def _set_job(jid: str, **kw):
    try:
        st = VOCAB_JOBS.get(jid)
        if not isinstance(st, dict):
            return
        st.update(kw)
    except Exception:
        pass

def _append_job_result(jid: str, item):
    try:
        st = VOCAB_JOBS.get(jid)
        if not isinstance(st, dict):
            return
        arr = st.get("results") if isinstance(st.get("results"), list) else []
        arr.append(item)
        st["results"] = arr
    except Exception:
        pass

def _pdf_default_settings() -> dict:
    return {
        "rows": 6,
        "cols": 6,
        "col_gap_pct": 0.0,
        "row_gap_pct": 0.0,
        "cell_mt": 4.0,
        "cell_mb": 18.0,
        "cell_ml": 4.0,
        "cell_mr": 4.0,
        "remove_labels": True,
        "keep_labels": False,
        "last_bottom_mb": 18.0,
        "corners": [[0.03, 0.03], [0.97, 0.03], [0.97, 0.82], [0.03, 0.82]],
    }

def _pdf_load_settings() -> dict:
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return _pdf_default_settings()

def _pdf_save_settings(data: dict) -> None:
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        base = _pdf_default_settings()
        if isinstance(data, dict):
            base.update(data)
        SETTINGS_FILE.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def _normalize_label(label: str) -> str:
    w = str(label).strip().lower()
    w = re.sub(r"[\s_\-]+", "_", w)
    w = re.sub(r"[^a-z0-9_]", "", w)
    return w.strip("_")

def _alpha_bucket_for(label: str) -> str:
    first = label[0] if label else "#"
    return first if ("a" <= first <= "z") else "#"

def _load_provenance() -> dict:
    if PROVENANCE_FILE.exists():
        try:
            return json.loads(PROVENANCE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_provenance(data: dict) -> None:
    PROVENANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _load_label_index() -> dict:
    if LABELS_FILE.exists():
        try:
            return json.loads(LABELS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_label_index(data: dict) -> None:
    LABELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LABELS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _load_extracted_log() -> dict:
    if EXTRACTED_LOG_FILE.exists():
        try:
            data = json.loads(EXTRACTED_LOG_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _save_extracted_log(data: dict) -> None:
    EXTRACTED_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    EXTRACTED_LOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _ok_json(h, obj, code=200):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    h.send_response(code)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)

def _text(h, s, code=200, ctype="text/plain; charset=utf-8"):
    data = s.encode("utf-8")
    h.send_response(code)
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)

def _html_index() -> str:
    return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Icon Labeler</title><style>body{font-family:Segoe UI,system-ui,Arial;margin:18px;color:#0D2545;background:#fafafa}h1{color:#31A8A0;margin:0 0 8px 0}*{box-sizing:border-box}.row{display:flex;gap:10px;align-items:center;margin:8px 0;flex-wrap:wrap}select,input,button,textarea{font:inherit;padding:6px 10px;max-width:100%}select#book{min-width:280px;max-width:70vw}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-top:12px}.card{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px;text-align:center;min-width:0}.card .muted{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}.card input.lbl{width:100%;font-size:12px;padding:4px 6px;margin-top:4px}.tile{width:160px;height:160px;display:flex;align-items:center;justify-content:center;margin:0 auto 6px auto;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:6px;position:relative}.tile img{max-width:140px;max-height:140px;object-fit:contain}.muted{color:#64748b;font-size:12px}.pill{display:inline-block;padding:2px 6px;border-radius:999px;border:1px solid #cbd5e1;margin:2px 4px;font-size:12px}.pill.ok{background:#dcfce7;border-color:#86efac;color:#166534}.pill.auto{background:#e0f2fe;border-color:#7dd3fc;color:#075985}.pill.miss{background:#fee2e2;border-color:#fca5a5;color:#991b1b}.ok{background:#e6fffa;border-color:#99f6e4}.miss{background:#fff1f2;border-color:#fecdd3}.panel{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin-top:12px}  :focus-visible { outline: 2px solid #0F766E; outline-offset: 2px; }.pill.skip{background:#f1f5f9;border-color:#cbd5e1;color:#475569}body{font-size:15px}button,.btn{min-height:36px;border:1px solid #cbd5e1;border-radius:6px;background:#fff;cursor:pointer}button:hover,.btn:hover{background:#f8fafc}.btn.primary,button.primary{background:#31A8A0;border-color:#31A8A0;color:#fff;font-weight:600}.btn.primary:hover,button.primary:hover{background:#2a938c}.sticky{position:sticky;top:0;z-index:5;box-shadow:0 2px 6px rgba(13,37,69,.08)}details.panel summary{cursor:pointer;padding:4px 0}.req-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;margin-top:10px}.req-card{background:#fff;border:2px solid #e2e8f0;border-radius:10px;padding:10px;display:flex;flex-direction:column;gap:8px;min-width:0}.req-card:focus-within,.req-card:focus{border-color:#31A8A0}.req-card[data-status='skip']{opacity:.6}.req-card[data-status='skip'] .req-thumb{filter:grayscale(1)}.req-card[data-status='missing']{border-color:#fca5a5;background:#fff7f7}.req-thumb{width:100%;aspect-ratio:1/1;max-height:190px;display:flex;align-items:center;justify-content:center;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:8px;overflow:hidden}.req-thumb img{max-width:92%;max-height:92%;object-fit:contain}.req-word{font-size:17px;font-weight:700;line-height:1.2;word-break:break-word}.req-file{font-size:12px;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.req-actions{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}.req-actions button{padding:6px 4px;font-size:14px}.req-act[data-a='keep'].is-on{background:#dcfce7;border-color:#86efac}.req-act[data-a='skip'].is-on{background:#e2e8f0}.req-sugg .card{cursor:pointer}.req-sugg .card:hover{border-color:#31A8A0}.req-more{font-size:13px}.req-more summary{color:#64748b;cursor:pointer}.req-more .row{margin:6px 0}.summary-bar{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.summary-bar .stats{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:14px}.summary-bar .stats .pill{font-size:13px;padding:3px 9px}
</style></head><body><header class='row' style='justify-content:space-between;margin-bottom:4px'><div class='row' style='margin:0'><h1 style='margin:0'>Icon Labeler</h1><label for='book' style='margin-left:16px'>Book:&nbsp;</label><select id='book' aria-label='Book'></select><button id='load' class='btn'>Load</button></div><div class='row' style='margin:0'><button id='guides' class='btn'>Guides</button><button id='pdf' class='btn'>PDF Extractor</button></div></header><div id='status_strip' class='panel sticky' style='display:none'></div><div id='required_panel' class='panel' style='display:none'></div><div id='theme_panel' class='panel' style='display:none'></div><details class='panel' id='overview_details'><summary><b>Overview notes</b> <span class='muted'>(optional)</span></summary><div id='overview_panel' style='display:none'><div class='row' style='align-items:flex-start'><label for='overview' style='min-width:80px'>Overview</label><textarea id='overview' rows='2' style='flex:1;min-width:320px'></textarea><button id='save_overview' class='btn'>Save</button><button id='fill_overview' class='btn'>Auto-fill</button></div></div></details><details class='panel' id='library_details'><summary><b>Icon library</b> <span class='muted'>browse and add extra icons</span> <span id='count' class='muted'></span></summary><div class='row'><label for='flt'>Filter:&nbsp;</label><input id='flt' placeholder='type to filter' aria-label='Filter library'><label class='muted'><input type='checkbox' id='theme_only'> this book only</label><button id='save' class='btn primary'>Save Selected</button><button id='select_all' class='btn'>Select All</button><button id='clear_sel' class='btn'>Clear</button><span id='selcount' class='muted'></span><button id='refresh' class='btn'>Refresh from Library</button><button id='ai' class='btn'>AI Preview</button></div><div id='grid' class='grid'></div></details><div id='ai_preview' class='panel' style='display:none'></div><script>
const $=s=>document.querySelector(s);
async function j(url,opts){const r=await fetch(url,opts);if(!r.ok)throw new Error(await r.text());return await r.json()}
function updateSelectedCount(){ try{ const n=[...document.querySelectorAll('.card .chk')].filter(x=>x.checked).length; const sp=$('#selcount'); if(sp) sp.textContent = n ? (n+' selected') : ''; }catch(_){ } }
function debounce(fn,ms){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn.apply(null,a), ms); }; }
function ensureTopBarExtras(){ try{ const row=document.querySelector('body .row'); if(!row) return; const sel=document.getElementById('select_all'); if(sel){ try{ sel.textContent='Select Visible'; }catch(_){ } } const exp=document.getElementById('export_csv'); if(!exp){ const btn=document.createElement('button'); btn.id='export_csv'; btn.textContent='Export CSV'; btn.style.marginLeft='8px'; row.appendChild(btn); } }catch(_){ } }
function exportReqCsv(){ try{ const bk=($('#book').value||''); const arr=Array.isArray(reqCache)? reqCache: []; if(!arr.length){ try{ showToast('Load a book first','info'); }catch(_){ } return; } const rows=[["book","word","status","current_path","missing"]]; arr.forEach(it=>{ try{ const w=String((it&&it.word)||''); const s=String((it&&it.status)||''); const p=String((it&&it.current_path)||''); const low=s.toLowerCase(); const missing = (low==='keep'||low==='kept'||low==='replaced')? '': '1'; rows.push([bk,w,s,p,missing]); }catch(_){ } }); const csv="\uFEFF"+rows.map(r=>r.map(x=>'"'+String(x||'').replace(/"/g,'""')+'"').join(',')).join('\\r\\n'); const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})); a.download=`icon_labeler_${bk||'book'}_required.csv`; document.body.appendChild(a); a.click(); setTimeout(()=>{ try{ URL.revokeObjectURL(a.href); a.remove(); }catch(_){ } },0); try{ showToast('Required CSV exported','success'); }catch(_){ } }catch(e){ try{ showToast('Export failed','error'); }catch(_){ } console.error(e); } }
async function loadMeta(bk){ try{ window.__ilMeta = await j('/api/meta?book='+encodeURIComponent(bk)); }catch(_){ window.__ilMeta = {}; } }
async function saveMeta(bk, hero, cover){ try{ await j('/api/meta/save',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, hero, cover})}); }catch(_){ } }
async function loadBooks(){
  const b=$('#book'); b.innerHTML=''; let r;
  try{ r=await j('/api/books'); }catch(e){ console.error(e); $('#count').textContent='Failed to load books'; return []; }
  const arr=Array.isArray(r.books)? r.books: [];
  arr.forEach(x=>{ const o=document.createElement('option'); o.value=x.slug; o.textContent=x.title||x.slug; b.appendChild(o); });
  try{
    const params=new URLSearchParams(location.search);
    const want=(params.get('book')||'').trim().toLowerCase();
    if(want){ const hit=arr.find(x=>String(x.slug||'').toLowerCase()===want); if(hit){ b.value=hit.slug; return arr; } }
  }catch(_){ }
  try{
    const last=(localStorage.getItem('il:last_book')||'').toLowerCase();
    if(last){ const hit=arr.find(x=>String(x.slug||'').toLowerCase()===last); if(hit){ b.value=hit.slug; } }
  }catch(_){ }
  if(arr.length && !b.value){ b.value=arr[0].slug }
  return arr
}
function render(items){
  const g=$('#grid'); g.innerHTML='';
  const f=($('#flt').value||'').toLowerCase();
  let themeOnly=false; try{ themeOnly=!!document.getElementById('theme_only').checked; }catch(_){ }
  const bk=$('#book').value||'';
  const meta=window.__ilMeta||{};
  let hero=String(meta.hero||'');
  let cover=String(meta.cover||'');
  if(!hero){ try{ hero=localStorage.getItem('il:hero:'+bk)||''; }catch(_){ } }
  if(!cover){ try{ cover=localStorage.getItem('il:cover:'+bk)||''; }catch(_){ } }
  let n=0;
  items.forEach(it=>{
    if(f && !it.name.toLowerCase().includes(f)) return; if(themeOnly){ try{ if(!(String(it.path||'').toLowerCase().includes('/activity_images/')||String(it.path||'').toLowerCase().includes('\\\\activity_images\\\\'))) return; }catch(_){ } } n++;
    const c=document.createElement('div'); c.className='card'; c.setAttribute('data-path', it.path||'');
    const showHero=(it.name===hero);
    const showCover=(it.name===cover);
    c.innerHTML = `<div class='tile'><img src='/file?path=${encodeURIComponent(it.path)}'><div class='hero-badge' style='position:absolute;top:6px;right:6px;${showHero?'':'display:none;'}'>&#9733;</div><div class='cover-badge' style='position:absolute;top:6px;left:6px;${showCover?'':'display:none;'}'>&#128216;</div></div><div class='muted' title='${it.name}'>${it.name}</div><div><button class='hero-btn ${showHero?'on':''}' title='Toggle hero' style='font-size:12px;padding:2px 8px;border:1px solid #e5e7eb;border-radius:999px;background:#fff;cursor:pointer'>&#9733;</button><label style='margin-left:8px'><input type='radio' name='cover-${bk}' class='cover-radio' value='${it.name}' ${showCover?'checked':''}> set as cover</label></div><input class='lbl' placeholder='new label (a-z 0 9 _ )' value=''> <label><input type='checkbox' class='chk'> select</label>`;
    g.appendChild(c);
    try{
      const chk=c.querySelector('.chk');
      if(chk){
        chk.addEventListener('change', ()=>{
          try{
            if(chk.checked){
              const lbl=c.querySelector('.lbl');
              if(lbl && !lbl.value.trim()){
                const nm=(it.name||'');
                const def=nm.toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,'');
                lbl.value = def;
              }
            }
          }catch(_){ }
          updateSelectedCount();
        });
      }
      const lbl=c.querySelector('.lbl');
      if(lbl){
        lbl.addEventListener('keydown', (e)=>{
          if(e.key==='Enter'){
            e.preventDefault();
            const ck=c.querySelector('.chk');
            if(ck){ ck.checked=!ck.checked; ck.dispatchEvent(new Event('change')); }
          }
        });
      }
    }catch(_){ }
    const heroBtn=c.querySelector('.hero-btn');
    const coverRadio=c.querySelector('.cover-radio');
    if(heroBtn){ heroBtn.onclick=async ()=>{ try{ const cur=(window.__ilMeta&&window.__ilMeta.hero)||''; const next=(cur===it.name)? '': it.name; try{ if(next){ localStorage.setItem('il:hero:'+bk, next); } else { localStorage.removeItem('il:hero:'+bk); } }catch(_){ } await saveMeta(bk, next, ((window.__ilMeta&&window.__ilMeta.cover)||'')); window.__ilMeta=window.__ilMeta||{}; window.__ilMeta.hero=next; }catch(_){ } render(items); }; }
    if(coverRadio){ coverRadio.onchange=async ()=>{ if(coverRadio.checked){ try{ localStorage.setItem('il:cover:'+bk, it.name); }catch(_){ } const curHero=(window.__ilMeta&&window.__ilMeta.hero)||''; await saveMeta(bk, curHero, it.name); window.__ilMeta=window.__ilMeta||{}; window.__ilMeta.cover=it.name; render(items); } }; }
  });
  $('#count').textContent=n+' shown';
  updateSelectedCount();
}let cur=[]; let reqCache=[]; let themeItemsCache=[]; async function loadList(){const bk=$('#book').value; if(!bk){ return; } try{ const rp=document.getElementById('required_panel'); if(rp){ rp.innerHTML="<div class='row'><b>Required Icons</b> <span class='muted'>loading\u2026 (first load scans the icon library)</span></div>"; rp.style.display='block'; } }catch(_){ } await loadMeta(bk); renderOverview(); await loadRequired(); await loadThemeItems(); updateStatusStrip(); const r=await j('/api/list?book='+encodeURIComponent(bk)); cur=r.items||[]; render(cur); try{ ensureThemeExportButton(); }catch(_){ } try{ ensureUploadControls(); }catch(_){ } updateStatusStrip();} 
function renderOverview(){const p=document.getElementById('overview_panel'); if(!p) return; const bk=$('#book').value||''; const meta=window.__ilMeta||{}; const ov=String(meta.overview||''); const t=document.getElementById('overview'); if(t) t.value=ov; p.style.display=bk?'block':'none'; const btn=document.getElementById('save_overview'); if(btn) btn.onclick=async()=>{ const v=(document.getElementById('overview').value||''); const m=window.__ilMeta||{}; try{ await j('/api/meta/save',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, hero: (m.hero||''), cover: (m.cover||''), overview: v})}); window.__ilMeta=Object.assign({}, m, {overview: v}); }catch(e){} }; const fill=document.getElementById('fill_overview'); if(fill) fill.onclick=autoFillOverview;}
async function loadRequired(){const bk=$('#book').value; const p=document.getElementById('required_panel'); if(!bk||!p){ if(p) p.style.display='none'; return; } let core=false; try{ const el=document.getElementById('req_core'); if(el) core=!!el.checked; }catch(_){ } let r; try{ r=await j('/api/required?book='+encodeURIComponent(bk)+(core?'&core=1':'')); }catch(e){ r={items:[]}; } const arr=Array.isArray(r.items)?r.items:[]; reqCache = arr; const hdr=`<div class='row' style='justify-content:space-between'><div><b>Required Icons</b> <span class='muted'>${arr.length}</span></div><div style='display:flex;align-items:center;gap:8px'><label class='muted'><input type='checkbox' id='req_core' ${core?'checked':''}> include core</label><button id='req_reload' class='btn'>Reload</button><button id='req_apply' class='btn primary' title='Copy every kept / pre-chosen icon into this book'>Save icons to book</button></div></div>`; const body=`<div class='req-grid'>`+arr.map(it=>{const w=String(it&&it.word||''); const pth=String(it&&it.current_path||''); const st=String(it&&it.status||'').toLowerCase(); const lbl=String(it&&it.target_label||''); const fn=pth?(pth.split(/[\\/]/).pop()||''):''; const isKept=(st==='keep'||st==='kept'||st==='replaced'); const pillCls=isKept?'ok':(st==='auto'?'auto':(st==='skip'?'skip':'miss')); const pillTxt=(st==='auto')?'pre-chosen':(st==='skip'?'skipped':(isKept?(st==='replaced'?'replaced':'kept'):'no icon found')); const thumb=pth?`<div class='req-thumb'><img src='/file?path=${encodeURIComponent(pth)}' alt='${w}' title='${fn}'></div>`:`<div class='req-thumb muted'>no icon found</div>`; return `<div class='req-card' data-w='${w}' data-status='${st}' tabindex='0' role='group' aria-label='${w}: ${pillTxt}'>${thumb}<div><div class='req-word'>${w} <span class='pill ${pillCls}'>${pillTxt}</span></div><div class='req-file'>${lbl?('save as: '+lbl+'.png'):(fn||'')}</div></div><div class='req-row' data-w='${w}' data-status='${st}'><div class='req-actions'><button class='req-act ${isKept?'is-on':''}' data-a='keep' data-w='${w}' aria-label='Keep icon for ${w}' title='Keep (K)'>&#10003; Keep</button><button class='req-act ${st==='skip'?'is-on':''}' data-a='skip' data-w='${w}' aria-label='Skip ${w}' title='Skip (S)'>&#10007; Skip</button><button class='req-replace' data-w='${w}' aria-label='Replace icon for ${w}' title='Replace (R)'>&#8644; Replace</button></div></div><div class='req-sugg' style='display:none; padding:8px 0;'></div></div>`;}).join('')+`</div>`; p.innerHTML=hdr+body; p.style.display='block'; const coreEl=document.getElementById('req_core'); if(coreEl) coreEl.onchange=()=>{ loadRequired(); }; const rl=document.getElementById('req_reload'); if(rl) rl.onclick=()=>{ loadRequired(); }; const ap=document.getElementById('req_apply'); if(ap) ap.onclick=async()=>{ try{ await j('/api/apply',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk})}); try{ localStorage.setItem('il:last_applied:'+bk, String(Date.now())); }catch(_){ } await loadList(); }catch(e){} }; const acts=[...document.querySelectorAll('.req-act')]; acts.forEach(btn=>{ btn.onclick=async()=>{ const w=btn.getAttribute('data-w')||''; const a=btn.getAttribute('data-a')||''; if(!w||!a) return; try{ await j('/api/decision',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, word: w, decision: a})}); try{ showToast((a==='skip'?'Skipped ':'Kept ')+w,'success'); }catch(_){ } await loadRequired(); updateStatusStrip(); }catch(e){} }; }); const rep=[...document.querySelectorAll('.req-replace')]; rep.forEach(btn=>{ btn.onclick=async()=>{ const w=btn.getAttribute('data-w')||''; const card=btn.closest('.req-card'); const cont=card?card.querySelector('.req-sugg'):null; if(!cont){ return; } if(cont.style.display==='block'){ cont.style.display='none'; cont.innerHTML=''; return; } cont.style.display='block'; cont.innerHTML='<div class="muted">Loading…</div>'; let sr; try{ sr=await j('/api/suggest?book='+encodeURIComponent(bk)+'&word='+encodeURIComponent(w)+'&k=12'); }catch(e){ sr={items:[]}; } const items=Array.isArray(sr.items)?sr.items:[]; const cards=items.map(it=>{const pth=String(it&&it.path||''); const nm=(String(it&&it.stem||'')||String(it&&it.name||'')); return `<div class='card' data-path='${pth}' role='button' tabindex='0' aria-label='Use ${nm}' style='width:104px;padding:6px'><div class='tile' style='width:88px;height:88px'><img src='/file?path=${encodeURIComponent(pth)}' alt='${nm}'></div><div class='muted' style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>${nm||''}</div></div>`; }).join(''); cont.innerHTML = `<div class='muted' style='margin-bottom:4px'>Click a picture to use it for <b>${w}</b>:</div><div class='row' style='gap:8px;align-items:center'><input type='text' class='rep-label' placeholder='rename (optional)' aria-label='New label for ${w}'><button class='rep-close btn'>Close</button></div><div style='display:flex;flex-wrap:wrap;gap:4px'>${cards||'<div class="muted">No suggestions found. Try the Icon library section below, or Upload PNGs in Theme set.</div>'}</div>`; const closeBtn=cont.querySelector('.rep-close'); if(closeBtn){ closeBtn.onclick=()=>{ cont.style.display='none'; cont.innerHTML=''; }; } const picks=[...cont.querySelectorAll('.card')]; picks.forEach(el=>{ el.onkeydown=(ev)=>{ if(ev.key==='Enter'||ev.key===' '){ ev.preventDefault(); el.click(); } }; el.onclick=async()=>{ const pth=el.getAttribute('data-path')||''; const lblEl=cont.querySelector('.rep-label'); const lbl=lblEl?lblEl.value.trim():''; try{ await j('/api/decision',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, word: w, decision: 'replaced', path: pth, label: lbl})}); cont.style.display='none'; cont.innerHTML=''; await loadRequired(); updateStatusStrip(); }catch(e){} }; }); }; }); updateStatusStrip();}
function updateStatusStrip(){const el=document.getElementById('status_strip'); const bk=$('#book').value||''; if(!bk||!el){ if(el) el.style.display='none'; return; } const n=Array.isArray(themeItemsCache)?themeItemsCache.length:0; let m=0; try{ if(Array.isArray(reqCache)){ m=reqCache.filter(it=>{ const s=String((it&&it.status)||'').toLowerCase(); return !(s==='keep'||s==='kept'||s==='replaced'||s==='auto'||s==='skip'); }).length; } }catch(_){ m=Array.isArray(reqCache)?reqCache.length:0; } let ts=''; try{ const v=localStorage.getItem('il:last_applied:'+bk); if(v){ const d=new Date(parseInt(v,10)); ts = d.toLocaleString(); } }catch(_){ } let cAuto=0,cKept=0,cSkip=0; try{ (reqCache||[]).forEach(it=>{ const s=String((it&&it.status)||'').toLowerCase(); if(s==='auto') cAuto++; else if(s==='keep'||s==='kept'||s==='replaced') cKept++; else if(s==='skip') cSkip++; }); }catch(_){ } const total=Array.isArray(reqCache)?reqCache.length:0; const right=`<div style='display:flex;gap:8px;align-items:center'><button id='apply_now' class='btn primary' title='Copy every kept / pre-chosen icon into this book'>Save icons to book</button></div>`; el.innerHTML=`<div class='summary-bar'><div class='stats'><b>${total} words</b> <span class='pill auto'>${cAuto} pre-chosen</span><span class='pill ok'>${cKept} kept</span><span class='pill skip'>${cSkip} skipped</span><span class='pill miss'>${m} no icon</span> <span style='margin-left:8px'><b>In book</b> <span class='pill ok'>${n}/15</span></span> <span class='muted' style='margin-left:8px'>${ts?('Last saved '+ts):'Not saved yet'}</span></div>${right}</div>`; el.style.display='block'; const ap=document.getElementById('apply_now'); if(ap) ap.onclick=async()=>{ ap.disabled=true; const bk=$('#book').value; try{ await j('/api/apply',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk})}); try{ localStorage.setItem('il:last_applied:'+bk, String(Date.now())); }catch(_){ } try{ showToast('Icons saved to book','success'); }catch(_){ } await loadList(); }catch(e){ try{ showToast('Save failed','error'); }catch(_){ } } finally { ap.disabled=false; } };}
async function loadThemeItems(){const bk=$('#book').value; const p=document.getElementById('theme_panel'); if(!bk||!p){ if(p) p.style.display='none'; return; } let r; try{ r=await j('/api/theme_items?book='+encodeURIComponent(bk)); }catch(e){ r={items:[]}; } themeItemsCache = Array.isArray(r.items)? r.items: []; const hdr=`<div class='row' style='justify-content:space-between'><div><b>Theme set</b> <span class='muted'>${themeItemsCache.length}</span></div><div><button id='open_theme'>Open Theme</button><button id='reload_theme' style='margin-left:8px'>Reload</button></div></div>`; const body=themeItemsCache.map(it=>{const nm=String(it&&it.name||''); return `<div class='row' style='gap:8px;align-items:center'><div style='min-width:200px'>${nm}.png</div><input type='text' class='tm-rename' data-old='${nm}' placeholder='new label'><button class='tm-rename-btn' data-old='${nm}'>Rename</button><button class='tm-del' data-name='${nm}' style='margin-left:4px'>Delete</button></div>`;}).join(''); p.innerHTML=hdr+body; p.style.display='block'; const ot=document.getElementById('open_theme'); if(ot) ot.onclick=async()=>{ try{ await j('/api/open_theme',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk})}); }catch(e){} }; const rl=document.getElementById('reload_theme'); if(rl) rl.onclick=()=>{ loadThemeItems(); }; const rb=[...document.querySelectorAll('.tm-rename-btn')]; rb.forEach(btn=>{ btn.onclick=async()=>{ const old=btn.getAttribute('data-old')||''; const inp=[...document.querySelectorAll('.tm-rename')].find(x=>x.getAttribute('data-old')===old); const v=inp?inp.value.trim():''; if(!v) return; const bk=$('#book').value; try{ await j('/api/theme_rename',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, old: old, new: v})}); await loadThemeItems(); await loadList(); }catch(e){} }; }); const db=[...document.querySelectorAll('.tm-del')]; db.forEach(btn=>{ btn.onclick=async()=>{ const nm=btn.getAttribute('data-name')||''; if(!nm) return; const bk=$('#book').value; try{ await j('/api/theme_delete',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, name: nm})}); await loadThemeItems(); await loadList(); }catch(e){} }; }); updateStatusStrip();}
try{ ensureTopBarExtras(); }catch(_){ }
const ld=document.getElementById('load'); if(ld) ld.onclick=async ()=>{ ld.disabled=true; try{ await loadList(); try{ showToast('Loaded','success'); }catch(_){ } } finally { ld.disabled=false; } };
const flt=document.getElementById('flt'); if(flt){ const deb=debounce(()=>render(cur),150); flt.addEventListener('input', deb); }
const to=document.getElementById('theme_only'); if(to){
  try{ const v=localStorage.getItem('il:theme_only'); to.checked = (v===null) ? true : (v==='1'); }catch(_){ to.checked=true; }
  to.onchange=()=>{ try{ localStorage.setItem('il:theme_only', to.checked?'1':'0'); }catch(_){ } render(cur); };
}
const selAll=document.getElementById('select_all'); if(selAll) selAll.onclick=()=>{ [...document.querySelectorAll('.card .chk')].forEach(ch=>{ ch.checked=true; }); updateSelectedCount(); };
const clr=document.getElementById('clear_sel'); if(clr) clr.onclick=()=>{ [...document.querySelectorAll('.card .chk')].forEach(ch=>{ ch.checked=false; }); updateSelectedCount(); };
const exp=document.getElementById('export_csv'); if(exp) exp.onclick=exportReqCsv;
document.addEventListener('keydown', (e)=>{ try{ if(e.key==='/' && !e.ctrlKey && !e.metaKey && !e.altKey){ const f=$('#flt'); if(f){ e.preventDefault(); f.focus(); f.select(); } } if((e.ctrlKey||e.metaKey) && e.key.toLowerCase()==='f'){ const f=$('#flt'); if(f){ e.preventDefault(); f.focus(); f.select(); } } }catch(_){ } });
document.addEventListener('click', (e)=>{ try{ const t=e.target; if(t && t.id==='export_theme_csv'){ e.preventDefault(); exportThemeCsv(); } if(t && t.id==='reload_theme'){ setTimeout(()=>{ try{ ensureThemeExportButton(); }catch(_){ } try{ ensureUploadControls(); }catch(_){ } }, 0); } }catch(_){ } });
$('#save').onclick=async ()=>{const cards=[...document.querySelectorAll('.card')];const items=[];cards.forEach((c)=>{const chk=c.querySelector('.chk');if(!chk||!chk.checked) return; const lbl=(c.querySelector('.lbl')||{}).value||''; const v=String(lbl).trim(); if(!v) return; const src=c.getAttribute('data-path')||''; if(!src) return; items.push({src:src,label:v});}); if(!items.length){ try{ showToast('No items selected','info'); }catch(_){ } return;} const bk=$('#book').value; const r=await j('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({book:bk,items})}); try{ showToast('Saved: '+r.copied+' copied, '+r.updated+' updated.','success'); }catch(_){ }};
const rf=document.getElementById('refresh'); if(rf) rf.onclick=async ()=>{ rf.disabled=true; const bk=$('#book').value; try{ const r=await j('/api/refresh',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk})}); try{ showToast('Refreshed: '+r.copied+' copied, '+r.updated+' updated.','success'); }catch(_){ } await loadList(); }catch(e){ try{ showToast('Refresh failed','error'); }catch(_){ } console.error(e); } finally { rf.disabled=false; } };
async function aiPreview(){
  const el=$('#ai_preview'); el.style.display='block'; el.textContent='Loading AI suggestion...';
  const bk=$('#book').value; if(!bk){ el.textContent='Select a book first.'; return; }
  try{
    const r=await j('/api/ai_preview?book='+encodeURIComponent(bk));
    if(!r.ok){ el.textContent=(r.error||'Preview failed'); return; }
    const sug=r.suggestion||{}; const avail=r.available_icons||[]; const inSet=r.in_set||[]; const outSet=r.out_set||[];
    function list(arr,cls){ return (arr||[]).map(x=>`<span class='pill ${cls||''}'>${String(x)}</span>`).join(''); }
    let scHtml='';
    if (sug.sorting_categories && !Array.isArray(sug.sorting_categories)){
      const obj=sug.sorting_categories; for (const k in obj){ if(Object.prototype.hasOwnProperty.call(obj,k)){ const vs=obj[k]||[]; scHtml += `<div><b>${k}</b><div>${list(vs,'')}</div></div>`; } }
    } else if (Array.isArray(sug.sorting_categories)){
      scHtml = `<pre>${JSON.stringify(sug.sorting_categories,null,2)}</pre>`;
    }
    el.innerHTML = `
      <div><b>Available icons (${avail.length})</b>: ${list(avail,'')}</div>
      <div style='margin-top:8px'><b>In set (${inSet.length})</b>: ${list(inSet,'ok')}</div>
      <div style='margin-top:4px'><b>Out of set (${outSet.length})</b>: ${list(outSet,'miss')}</div>
      <hr>
      <div><b>Sorting categories</b> ${scHtml||'<i>none</i>'}</div>
      <div style='margin-top:8px'><b>Core verbs</b>: ${list(sug.core_verbs||[],'')}</div>
      <div style='margin-top:4px'><b>AAC fringe vocab</b>: ${list(sug.aac_fringe_vocab||[],'')}</div>
      <div style='margin-top:4px'><b>Word search words</b>: ${list(sug.word_search_words||[],'')}</div>
      <div style='margin-top:4px'><b>Sequence order</b>: <pre style='white-space:pre-wrap'>${(sug.sequence_order||[]).join('\\n')}</pre></div>
    `;
  }catch(e){ console.error(e); el.textContent='Preview failed (network error)'; }
}
async function autoFillOverview(){
  const bk=$('#book').value; const t=document.getElementById('overview'); if(!bk||!t){ return; }
  try{
    const r=await j('/api/ai_preview?book='+encodeURIComponent(bk));
    if(!r.ok){ alert(r.error||'Backend not available'); return; }
    const s=r.suggestion||{};
    const uniq=(arr)=>{ const seen={}; const out=[]; (arr||[]).forEach(x=>{ const k=String(x||'').trim(); if(k && !seen[k.toLowerCase()]){ seen[k.toLowerCase()]=1; out.push(k); } }); return out; };
    const core=uniq(s.core_verbs||[]).slice(0,12);
    const fringe=uniq(s.aac_fringe_vocab||[]).slice(0,24);
    const ws=uniq(s.word_search_words||[]).slice(0,16);
    const lines=[];
    if (typeof s.summary === 'string' && s.summary.trim()){
      lines.push(s.summary.trim());
    }
    if (core.length || fringe.length){
      lines.push('Key vocab: '+uniq(core.concat(fringe)).join(', '));
    }
    if (ws.length){
      lines.push('Word search: '+ws.join(', '));
    }
    lines.push('WH prompts: Who is in the story? What happened? Where is it set? When does it happen? Why did it happen? How do they feel?');
    lines.push('Yes/No prompts: Can you find the '+(fringe[0]||'item')+'? Do you see it now? Is this the right one?');
    t.value = lines.join('\\n\\n');
  }catch(e){ try{ showToast('Auto-fill failed (backend not running)','error'); }catch(_){ } }
}
function ensureToast(){ try{ if(document.getElementById('toast-wrap')) return; const wrap=document.createElement('div'); wrap.id='toast-wrap'; wrap.style.position='fixed'; wrap.style.top='14px'; wrap.style.right='14px'; wrap.style.zIndex='9999'; wrap.style.display='flex'; wrap.style.flexDirection='column'; wrap.style.gap='8px'; document.body.appendChild(wrap); }catch(_){ } }
function showToast(msg, kind){ try{ ensureToast(); const w=document.getElementById('toast-wrap'); const t=document.createElement('div'); t.textContent=String(msg||''); t.style.padding='8px 12px'; t.style.borderRadius='8px'; t.style.font='13px Segoe UI, system-ui, Arial'; t.style.color='#0D2545'; t.style.background=(kind==='error')?'#FEE2E2':(kind==='success')?'#E6FFFB':'#F1F5F9'; t.style.border='1px solid '+((kind==='error')?'#FCA5A5':(kind==='success')?'#99F6E4':'#CBD5E1'); t.style.boxShadow='0 2px 6px rgba(0,0,0,0.08)'; w.appendChild(t); setTimeout(()=>{ try{ t.remove(); }catch(_){ } }, 2400); }catch(_){ } }
function exportThemeCsv(){ try{ const bk=($('#book').value||''); const arr=Array.isArray(themeItemsCache)? themeItemsCache: []; if(!arr.length){ try{ showToast('No theme items to export','info'); }catch(_){ } return; } const rows=[["book","name","path"]]; arr.forEach(it=>{ try{ rows.push([bk, String((it&&it.name)||''), String((it&&it.path)||'')]); }catch(_){ } }); const csv="\uFEFF"+rows.map(r=>r.map(x=>'"'+String(x||'').replace(/"/g,'""')+'"').join(',')).join('\\r\\n'); const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})); a.download=`icon_labeler_${bk||'book'}_theme.csv`; document.body.appendChild(a); a.click(); setTimeout(()=>{ try{ URL.revokeObjectURL(a.href); a.remove(); }catch(_){ } },0); try{ showToast('Theme CSV exported','success'); }catch(_){ } }catch(e){ try{ showToast('Export failed','error'); }catch(_){ } console.error(e); } }
function ensureThemeExportButton(){ try{ const p=document.getElementById('theme_panel'); if(!p) return; if(document.getElementById('export_theme_csv')) return; const hdr=p.querySelector('.row'); if(!hdr) return; let act = null; try{ const rel=p.querySelector('#reload_theme'); act = rel? rel.parentElement: hdr; }catch(_){ act = hdr; } const btn=document.createElement('button'); btn.id='export_theme_csv'; btn.textContent='Export CSV'; btn.style.marginLeft='8px'; act.appendChild(btn); }catch(_){ } }
function ensureUploadControls(){ try{ const p=document.getElementById('theme_panel'); if(!p) return; const bk=(document.getElementById('book')||{}).value||''; if(!bk) return; const hdr=p.querySelector('.row'); if(hdr){ if(!document.getElementById('upload')){ const up=document.createElement('button'); up.id='upload'; up.textContent='Upload PNGs'; up.style.marginLeft='8px'; hdr.appendChild(up); let ip=document.getElementById('il_hidden_upload'); if(!ip){ ip=document.createElement('input'); ip.type='file'; ip.id='il_hidden_upload'; ip.accept='image/png'; ip.multiple=true; ip.style.display='none'; document.body.appendChild(ip); } async function doUpload(fs){ const list=[]; for(let i=0;i<(fs&&fs.length||0);i++){ const f=fs[i]; if(!f) continue; const t=(f.type||'').toLowerCase(); const nm=String(f.name||''); if(t!=='image/png' && !nm.toLowerCase().endsWith('.png')) continue; const data=await new Promise(res=>{ const rd=new FileReader(); rd.onload=()=>res(String(rd.result||'')); rd.readAsDataURL(f); }); list.push({name:nm, data}); } if(!list.length){ try{ showToast('No PNGs selected','info'); }catch(_){ } return; } try{ await j('/api/upload',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, files: list})}); try{ showToast('Uploaded '+list.length+' file(s)','success'); }catch(_){ } await loadThemeItems(); await loadList(); }catch(e){ try{ showToast('Upload failed','error'); }catch(_){ } } }
up.addEventListener('click', ()=>{ try{ ip.click(); }catch(_){ } }); ip.addEventListener('change', async ()=>{ const fs=ip.files; if(!fs||!fs.length) return; await doUpload(fs); try{ ip.value=''; }catch(_){ } }); }
if(!document.getElementById('drop_zone')){ const dz=document.createElement('div'); dz.id='drop_zone'; dz.textContent='Drop PNGs here'; dz.style.marginTop='8px'; dz.style.border='2px dashed #94a3b8'; dz.style.borderRadius='10px'; dz.style.padding='12px'; dz.style.background='#f8fafc'; dz.style.textAlign='center'; try{ p.insertBefore(dz, p.children[1]||null); }catch(_){ p.appendChild(dz); } dz.addEventListener('dragover',(e)=>{ try{ e.preventDefault(); dz.style.background='#e0f2fe'; dz.style.borderColor='#38bdf8'; }catch(_){ } }); dz.addEventListener('dragleave',()=>{ try{ dz.style.background='#f8fafc'; dz.style.borderColor='#94a3b8'; }catch(_){ } }); dz.addEventListener('drop', async (e)=>{ try{ e.preventDefault(); dz.style.background='#f8fafc'; dz.style.borderColor='#94a3b8'; const fs=(e.dataTransfer&&e.dataTransfer.files)||[]; if(!fs||!fs.length) return; await doUpload(fs); }catch(_){ } }); } } }catch(_){ } }
function insertTipsPanel(){
  try{
    const count=document.getElementById('count');
    if(!count) return;
    if(document.getElementById('tips_panel')) return;
    const p=document.createElement('div');
    p.id='tips_panel'; p.className='panel';
    p.innerHTML = "<details><summary><b>How to use Icon Labeler</b></summary>"
      + "<div class='muted' style='margin-top:6px;line-height:1.45'>"
      + "<div><b>1.</b> Each word in <b>Required Icons</b> already has a pre-chosen icon. Check the pictures.</div>"
      + "<div><b>2.</b> Wrong picture? click <b>Replace</b> and pick another. Don't want the word? click <b>Skip</b>. Happy? leave it (or click <b>Keep</b>).</div>"
      + "<div><b>3.</b> Click <b>Save icons to book</b>. That copies every kept/pre-chosen icon into this book's activity_images.</div>"
      + "<div style='margin-top:4px'><b>Keyboard</b>: focus a card, then K = keep, S = skip, R = replace.</div>"
      + "<div><b>Overview</b>: optional notes about replacements or unsuitable words. Use <b>Auto‑fill</b> to draft summary, key vocab and prompts.</div>"
      + "<div style='margin-top:4px'><b>Action semantics</b>: <i>Skip</i> excludes the word from activities (keeps it in vocab). <i>Replace</i> selects a different image (optionally relabel). <i>Delete from theme</i> removes the PNG from this book’s activity_images only (word stays required/filled as appropriate). <i>Ban image</i> permanently excludes a specific file path from suggestions and future use across books; library files outside activity_images may be deleted.</div>"
      + "<div><b>Theme set</b>: Rename/Delete icons and use <b>Open Theme</b> to view the folder.</div>"
      + "<div><b>Status</b>: Activities count, Missing, and Last applied. Use <b>Apply now</b> to sync.</div>"
      + "</div></details>";
    try{ const anchor=document.getElementById('theme_panel'); anchor.parentNode.insertBefore(p, anchor.nextSibling); }catch(_){ }
  }catch(_){ }
}
function enhanceRequiredUI(){
  const p=document.getElementById('required_panel'); if(!p) return;
  // Inject 'missing only' toggle in header and apply filter
  try{
    if(!document.getElementById('req_missing_only')){
      const hdr=p.querySelector('.row');
      if(hdr){
        const lab=document.createElement('label'); lab.className='muted'; lab.style.marginLeft='8px';
        lab.innerHTML="<input type='checkbox' id='req_missing_only'> missing only";
        try{ (hdr.lastElementChild||hdr).appendChild(lab); }catch(_){ hdr.appendChild(lab); }
        const missEl=document.getElementById('req_missing_only');
        try{ missEl.checked=(localStorage.getItem('il:req_missing_only')==='1'); }catch(_){ }
        missEl.addEventListener('change', ()=>{ try{ localStorage.setItem('il:req_missing_only', missEl.checked?'1':'0'); }catch(_){ } try{ __applyReqMissingFilter(); }catch(_){ } });
      }
    }
  }catch(_){ }
  // Header batch controls: Select Visible / Clear and Keep/Skip Selected + counter
  try{
    const hdr=p.querySelector('.row');
    if(hdr){
      const right = hdr.lastElementChild || hdr;
      if(!document.getElementById('req_select_visible')){
        const b1=document.createElement('button'); b1.id='req_select_visible'; b1.textContent='Select Visible'; b1.style.marginLeft='8px'; right.appendChild(b1);
      }
      if(!document.getElementById('req_clear_sel')){
        const b2=document.createElement('button'); b2.id='req_clear_sel'; b2.textContent='Clear'; b2.style.marginLeft='4px'; right.appendChild(b2);
      }
      if(!document.getElementById('req_selcount')){
        const sc=document.createElement('span'); sc.id='req_selcount'; sc.className='muted'; sc.style.marginLeft='8px'; right.appendChild(sc);
      }
      if(!document.getElementById('req_batch_keep')){
        const bk=document.createElement('button'); bk.id='req_batch_keep'; bk.textContent='Keep Selected'; bk.style.marginLeft='8px'; right.appendChild(bk);
      }
      if(!document.getElementById('req_batch_skip')){
        const bs=document.createElement('button'); bs.id='req_batch_skip'; bs.textContent='Skip Selected'; bs.style.marginLeft='4px'; right.appendChild(bs);
      }
    }
  }catch(_){ }
  function __applyReqMissingFilter(){ try{ const missEl=document.getElementById('req_missing_only'); const showMissing=!!(missEl&&missEl.checked); const byW={}; (window.reqCache||[]).forEach(it=>{ byW[String((it&&it.word)||'')]=String((it&&it.status)||'').toLowerCase(); }); const rows=[...p.querySelectorAll('.req-row')]; rows.forEach(row=>{ const w=row.getAttribute('data-w')||''; const s=byW[w]||''; const missing=!(s==='keep'||s==='kept'||s==='replaced'||s==='auto'||s==='skip'); const vis = (!showMissing)||missing; const card=row.closest('.req-card')||row; card.style.display = vis? '': 'none'; }); }catch(_){ } }
  const bk=(document.getElementById('book')||{}).value||'';
  const rows=[...p.querySelectorAll('.req-row')];
  rows.forEach(row=>{
    if(row.getAttribute('data-enhanced')) return; row.setAttribute('data-enhanced','1');
    const w=row.getAttribute('data-w')||'';
    // Add a selection checkbox to each required row for batch actions
    try{
      const chkWrap=document.createElement('label'); chkWrap.style.marginRight='6px';
      const cb=document.createElement('input'); cb.type='checkbox'; cb.className='req-chk';
      chkWrap.appendChild(cb);
      row.insertBefore(chkWrap, row.firstChild);
      cb.addEventListener('change', ()=>{ try{ __reqUpdateSelectedCount(); }catch(_){ } });
    }catch(_){ }
    const grp=document.createElement('details'); grp.className='req-more';
    grp.innerHTML = "<summary>rename / delete / ban\u2026</summary>"
      + "<div class='row'><input type='text' class='req-rename' placeholder='new label' aria-label='New label for "+w+"' style='flex:1;min-width:90px'>"
      + "<button class='req-keep-rename btn' title='Keep this icon but save it under a different name'>Keep + rename</button></div>"
      + "<div class='row'><button class='req-del-theme btn' title='Remove this PNG from the book only'>Delete from theme</button>"
      + "<button class='req-ban-img btn' title='Never suggest this image again, in any book'>Ban image</button></div>";
    try{ const card=row.closest('.req-card'); const sugg=card?card.querySelector('.req-sugg'):null; if(card&&sugg){ card.insertBefore(grp, sugg); } else { row.parentNode.insertBefore(grp, row.nextSibling); } }catch(_){ row.appendChild(grp); }
    try{ const card=row.closest('.req-card'); if(card){ card.addEventListener('keydown',(ev)=>{ try{ if(ev.target && (ev.target.tagName==='INPUT'||ev.target.tagName==='TEXTAREA')) return; const k=String(ev.key||'').toLowerCase(); let btn=null; if(k==='k') btn=card.querySelector(".req-act[data-a='keep']"); else if(k==='s') btn=card.querySelector(".req-act[data-a='skip']"); else if(k==='r') btn=card.querySelector('.req-replace'); if(btn){ ev.preventDefault(); btn.click(); } }catch(_){ } }); } }catch(_){ }
    const inp=grp.querySelector('.req-rename');
    const btnKR=grp.querySelector('.req-keep-rename');
    const btnDel=grp.querySelector('.req-del-theme');
    const btnBan=grp.querySelector('.req-ban-img');
    if(btnKR){ btnKR.onclick=async ()=>{ const v=(inp&&inp.value||'').trim(); if(!v){ alert('Enter a new label'); return; } try{ await j('/api/decision',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, word: w, decision: 'keep', label: v})}); await loadRequired(); try{ enhanceRequiredUI(); }catch(_){ } updateStatusStrip(); }catch(e){} }; }
    if(btnDel){ btnDel.onclick=async ()=>{ let name=''; try{ const it=(reqCache||[]).find(x=>String((x&&x.word)||'')===w); const pth=String((it&&it.current_path)||''); if(pth){ const tail=pth.split('/').pop()||''; name=tail.replace(/\.png$/i,''); } }catch(_){ }
      if(!name){ name=w.toLowerCase().replace(/[^a-z0-9]+/g,'_').replace(/^_+|_+$/g,''); }
      if(!name){ alert('No theme image found to delete for '+w); return; }
      if(!(window.confirm&&confirm('Delete '+name+'.png from theme?'))) return;
      try{ await j('/api/theme_delete',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, name})}); await loadThemeItems(); await loadRequired(); try{ enhanceRequiredUI(); }catch(_){ } updateStatusStrip(); }catch(e){} } }
    if(btnBan){ btnBan.onclick=async ()=>{ let pth=''; try{ const it=(reqCache||[]).find(x=>String((x&&x.word)||'')===w); pth=String((it&&it.current_path)||''); }catch(_){ }
      if(!pth){ alert('No current image found to ban for '+w+' — use Replace to pick and then ban if needed.'); return; }
      if(!(window.confirm&&confirm('Ban this image globally so it is never suggested or used again?'))) return;
      try{ await j('/api/ban',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({path: pth, delete_file: true})}); await loadRequired(); await loadThemeItems(); try{ enhanceRequiredUI(); }catch(_){ } updateStatusStrip(); }catch(e){} } }
  });
  // Selected counter + helpers
  function __isVisibleRow(r){ try{ return r && r.style.display !== 'none'; }catch(_){ return true; } }
  function __reqUpdateSelectedCount(){ try{ const n=[...p.querySelectorAll('.req-row')].filter(__isVisibleRow).map(r=>{ const cb=r.querySelector('.req-chk'); return cb&&cb.checked?1:0; }).reduce((a,b)=>a+b,0); const sp=document.getElementById('req_selcount'); if(sp) sp.textContent = n? (n+' selected') : ''; }catch(_){ } }
  try{ __reqUpdateSelectedCount(); }catch(_){ }
  // Wire header batch buttons
  try{
    const selBtn=document.getElementById('req_select_visible');
    if(selBtn && !selBtn.getAttribute('data-wired')){
      selBtn.setAttribute('data-wired','1');
      selBtn.onclick=()=>{ try{ [...p.querySelectorAll('.req-row')].filter(__isVisibleRow).forEach(r=>{ const cb=r.querySelector('.req-chk'); if(cb) cb.checked=true; }); __reqUpdateSelectedCount(); }catch(_){ } };
    }
    const clrBtn=document.getElementById('req_clear_sel');
    if(clrBtn && !clrBtn.getAttribute('data-wired')){
      clrBtn.setAttribute('data-wired','1');
      clrBtn.onclick=()=>{ try{ [...p.querySelectorAll('.req-row')].forEach(r=>{ const cb=r.querySelector('.req-chk'); if(cb) cb.checked=false; }); __reqUpdateSelectedCount(); }catch(_){ } };
    }
    async function __batch(decision){
      const rows=[...p.querySelectorAll('.req-row')].filter(__isVisibleRow);
      const picks=rows.map(r=>{ const cb=r.querySelector('.req-chk'); return (cb&&cb.checked)? (r.getAttribute('data-w')||'') : ''; }).filter(Boolean);
      if(!picks.length){ try{ showToast('No required items selected','info'); }catch(_){ } return; }
      const keepBtn=document.getElementById('req_batch_keep'); const skipBtn=document.getElementById('req_batch_skip');
      try{ if(keepBtn) keepBtn.disabled=true; if(skipBtn) skipBtn.disabled=true; }catch(_){ }
      let ok=0, fail=0;
      for(const w of picks){
        try{ await j('/api/decision',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk, word: w, decision})}); ok++; }
        catch(e){ fail++; }
      }
      try{ showToast(`Batch ${decision}: ${ok} ok${fail? ', '+fail+' failed':''}`,'success'); }catch(_){ }
      try{ await loadRequired(); enhanceRequiredUI(); updateStatusStrip(); }catch(_){ }
      try{ if(keepBtn) keepBtn.disabled=false; if(skipBtn) skipBtn.disabled=false; }catch(_){ }
    }
    const bkBtn=document.getElementById('req_batch_keep'); if(bkBtn && !bkBtn.getAttribute('data-wired')){ bkBtn.setAttribute('data-wired','1'); bkBtn.onclick=()=>__batch('keep'); }
    const bsBtn=document.getElementById('req_batch_skip'); if(bsBtn && !bsBtn.getAttribute('data-wired')){ bsBtn.setAttribute('data-wired','1'); bsBtn.onclick=()=>__batch('skip'); }
  }catch(_){ }
  try{ __applyReqMissingFilter(); }catch(_){ }
}
const __origLoadRequired=loadRequired; loadRequired=async function(){ await __origLoadRequired(); try{ enhanceRequiredUI(); }catch(_){ } };
function boot(){
  try{ insertTipsPanel(); }catch(_){ }
  loadBooks().then(()=>loadList()).catch(e=>console.error(e));
  const ai=document.getElementById('ai'); if(ai) ai.onclick=async ()=>{ ai.disabled=true; try{ await aiPreview(); } finally { ai.disabled=false; } };
  const gd=document.getElementById('guides'); if(gd) gd.onclick=()=>{ const bk=document.getElementById('book').value; if(!bk){ try{ showToast('Select a book first.','info'); }catch(_){ } return; } location.href='/guides?book='+encodeURIComponent(bk); };
  const pdf=document.getElementById('pdf'); if(pdf) pdf.onclick=()=>{ location.href='/pdf'; };
  const bsel=document.getElementById('book'); if(bsel) bsel.onchange=()=>{ try{ localStorage.setItem('il:last_book', bsel.value); }catch(_){ } loadList().catch(()=>{}); };
}
document.addEventListener('DOMContentLoaded', boot, false);
if (document.readyState !== 'loading') { boot(); }
</script></body></html>"""

def _html_pdf() -> str:
    return r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Icon Labeler</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, Segoe UI, sans-serif; max-width: 1100px; margin: 0 auto; padding: 24px; color: #222; }
  h1 { font-size: 20px; font-weight: 500; }
  h2 { font-size: 16px; font-weight: 500; margin-top: 2rem; }
  label { font-size: 13px; color: #555; display: block; margin-bottom: 4px; }
  select, input[type=text], input[type=number] { font-size: 14px; padding: 6px 8px; border: 1px solid #ccc; border-radius: 6px; }
  button { font-size: 14px; padding: 8px 14px; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; }
  button:hover { background: #f5f5f5; }
  button.primary { background: #31A8A0; color: white; border-color: #31A8A0; }
  button.primary:hover { background: #2a9189; }
  ul.help { font-size: 13px; color: #555; margin: 8px 0 16px 18px; }
  ul.help li { margin: 2px 0; }
  .row { display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 12px; }
  .field { display: flex; flex-direction: column; }
  #preview-img { max-width: 100%; border: 1px solid #ddd; border-radius: 8px; margin-top: 8px; }
  #grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-top: 16px; }
  .tile { background: #fafafa; border: 1px solid #e5e5e5; border-radius: 8px; padding: 8px; display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 0; position: relative; }
  .tile img { width: 80px; height: 80px; object-fit: contain; background: white; border: 1px solid #eee; border-radius: 4px; }
  .tile-input-row { display: flex; gap: 4px; width: 100%; }
  .tile input[type=text] { flex: 1 1 auto; min-width: 0; width: auto; font-size: 12px; padding: 4px 6px; }
  .mic-btn { width: 28px; height: 28px; flex-shrink: 0; padding: 0; display: flex; align-items: center; justify-content: center; }
  .mic-btn.listening { background: #ffe0e0; border-color: #e24b4a; }
  #status { font-size: 13px; color: #555; margin-top: 8px; min-height: 18px; }
  #save-summary { font-size: 13px; padding: 8px 12px; background: #e1f5ee; border-radius: 6px; margin-top: 12px; display: none; }
  #batch-progress { display: none; margin-top: 8px; align-items: center; gap: 10px; }
  #batch-bar-outer { width: 260px; height: 10px; background: #eee; border-radius: 6px; overflow: hidden; border: 1px solid #ddd; }
  #batch-bar-inner { height: 100%; width: 0%; background: #31A8A0; }
  #batch-text { font-size: 12px; color: #555; }
</style>
</head>
<body>
<h1>Icon Labeler</h1>
<p style="font-size:13px; color:#555;">Standalone bulk extraction and labeling tool. Saves directly into the symbol library -- works whether or not StudioForge is running.</p>

<div class="row" style="margin-top:6px;">
  <button id="hard-reload" title="Bypass browser cache and reload the app">Reload app (force refresh)</button>
  <div style="font-size:12px; color:#777;">Use this if your browser isn’t picking up updates.</div>
</div>

<ul class="help">
  <li>Pick or set the PDF source folder; select one or more PDFs.</li>
  <li>Set rows/cols and gaps; drag the 4 red corners to align the grid.</li>
  <li>Adjust trims or tick “Remove label text” to crop away under-icon words.</li>
  <li>Click Extract → enter labels (type or mic) → Save all labels.</li>
  <li>Use Open OUTPUT to review saved icons.</li>
  <li>Settings and per‑PDF profiles are remembered for next time.</li>
</ul>

<h2>1. Choose PDFs</h2>
<p style="font-size:13px; color:#555;">Check several PDFs that share the same grid layout to extract them all in one batch.</p>
<div class="row">
  <div class="field">
    <button id="select-all-pdfs">Select all</button>
  </div>
  <div class="field">
    <button id="clear-all-pdfs">Clear all</button>
  </div>
</div>
<div class="row">
  <div class="field" style="min-width:420px;">
    <label>Source folder for Boardmaker PDFs</label>
    <input type="text" id="src-folder" style="width:420px;">
  </div>
  <button id="save-src-folder">Save</button>
  <button id="open-src-folder">Open</button>
</div>
<div id="pdf-list" style="max-height:220px; overflow-y:auto; border:1px solid #ddd; border-radius:8px; padding:8px; background:#fafafa;"></div>
<p id="pdf-count" style="font-size:12px; color:#777; margin-top:6px;"></p>

<h2>2. Set up grid (applied to every selected PDF)</h2>
<div class="row">
  <div class="field"><label>Preview against</label><select id="preview-pdf-select" style="min-width:240px;"></select></div>
  <div class="field"><label>Page</label><select id="page-select" style="min-width:80px;"></select></div>
</div>
<div class="row">
  <div class="field"><label>Rows</label><input type="number" id="rows" value="6" min="1" max="12" style="width:60px;"></div>
  <div class="field"><label>Columns</label><input type="number" id="cols" value="6" min="1" max="12" style="width:60px;"></div>
  <div class="field"><label>Gap between columns %</label><input type="number" id="col_gap_pct" value="0" step="0.5" min="0" style="width:80px;"></div>
  <div class="field"><label>Gap between rows %</label><input type="number" id="row_gap_pct" value="0" step="0.5" min="0" style="width:80px;"></div>
  <button id="reset-corners">Reset corners</button>
</div>
<p style="font-size:12px; color:#777;">If there's visible whitespace BETWEEN icon boxes (not just inside each box), set the gap percentages above zero -- the orange lines on the preview show where each gap starts and ends. Leave at 0 if cells touch edge-to-edge.</p>
<div id="preview-wrap" style="position:relative; display:inline-block; max-width:100%;">
  <img id="preview-img" style="max-width:100%; display:block;" />
</div>
<div class="row" style="margin-top:12px;">
  <div class="field"><label>Cell top trim %</label><input type="number" id="cell_mt" value="4" step="0.5" style="width:70px;"></div>
  <div class="field"><label>Cell bottom trim % (clears label text)</label><input type="number" id="cell_mb" value="18" step="0.5" style="width:70px;"></div>
  <div class="field"><label>Cell left trim %</label><input type="number" id="cell_ml" value="4" step="0.5" style="width:70px;"></div>
  <div class="field"><label>Cell right trim %</label><input type="number" id="cell_mr" value="4" step="0.5" style="width:70px;"></div>
</div>
<p style="font-size:12px; color:#777;">These trim a bit off each individual cell after slicing, to clear the cell's own border and the label word underneath the icon. Same trim applies to every cell in the grid.</p>

<div class="row" style="margin-top:6px;">
  <div class="field" style="flex-direction:row; align-items:center; gap:6px;">
    <input type="checkbox" id="remove-labels" style="width:auto;">
    <label style="margin:0;">Remove label text under icons (sets bottom trim to ~18%)</label>
  </div>
  <div class="field" style="font-size:12px; color:#777;">Unchecked keeps under-icon labels (bottom trim = 0%).</div>
</div>

<h2>3. Extract</h2>
<p style="font-size:13px; color:#555; background:#e8f8f8; padding:8px 12px; border-radius:6px; border-left:4px solid #31A8A0;">After extracting, click the <strong>★ star</strong> on any tile to mark it as the hero image for that book. The star turns <strong>gold</strong> when selected. Then label each icon and click <strong>Save all labels</strong>.</p>
<div class="row">
  <div class="field">
    <label>Which pages?</label>
    <select id="page-mode" style="min-width:160px;">
      <option value="all">All pages</option>
      <option value="current">Current page only</option>
      <option value="range">Page range</option>
    </select>
  </div>
  <div class="field" id="page-range-field" style="display:none;">
    <label>Page range (e.g. 1-3, 5, 7-9)</label>
    <input type="text" id="page-range-input" style="width:140px;" placeholder="1-3, 5">
  </div>
  <button class="primary" id="extract-btn">Extract symbols from selected PDFs</button>
  <button id="extract-all-btn" title="Runs current grid/corners on every PDF in the source folder">Batch extract all PDFs in source folder</button>
</div>
<div id="status"></div>
<div id="batch-progress" style="display:none;">
  <div id="batch-bar-outer"><div id="batch-bar-inner"></div></div>
  <span id="batch-text">0/0</span>
  <button id="batch-cancel">Cancel</button>
</div>

<h2>4. Label and save</h2>
<p style="font-size:13px; color:#555;">Tiles are grouped by source PDF below. The book name is recorded automatically per group for provenance -- it's not added to filenames.</p>
<div id="grid-groups"></div>
<button class="primary" id="save-btn" style="margin-top:16px; display:none;">Save all labels</button>
<button id="open-output-btn" style="margin-top:16px; margin-left:8px; display:none;">Open OUTPUT</button>
<div id="save-summary"></div>

<h2>5. Save to Theme (+ Quick Autolabel)</h2>
<div class="row" style="align-items:flex-start">
  <div class="field" style="min-width:260px">
    <label>Book</label>
    <select id="book-select" style="min-width:260px"></select>
  </div>
  <div class="field" style="flex:1; min-width:300px">
    <label>Quick Autolabel (comma or newline separated)</label>
    <textarea id="quick-labels" rows="3" style="width:100%"></textarea>
  </div>
  <div class="field" style="min-width:220px">
    <label style="display:flex; gap:8px; align-items:center"><input type="checkbox" id="also-lib" style="width:auto"> Also save to Library (Alpha)</label>
    <div style="margin-top:8px; display:flex; gap:8px; flex-wrap:wrap">
      <button id="open-theme-btn">Open Theme</button>
      <button class="primary" id="save-theme-btn">Save to Theme (+ Quick Autolabel)</button>
    </div>
  </div>
</div>

<script>
let allPdfs = [];
let extractedPdfs = {};
let selectedPdfs = new Set();
let lastBottomMb = 18; // remembers last non-zero bottom trim when toggling
let settingsLoaded = false;
let settingsBase = {};
let profiles = {};
let currentPdfKey = null;
let batchCancel = false;
let batchRunning = false;

async function loadBooksForPdf(){
  try{
    const r = await fetch('/api/books');
    const d = await r.json();
    const sel = document.getElementById('book-select');
    if(!sel) return;
    sel.innerHTML='';
    const arr = Array.isArray(d.books)? d.books: [];
    arr.forEach(x=>{ const o=document.createElement('option'); o.value=x.slug; o.textContent=x.title||x.slug; sel.appendChild(o); });
    try{ const p=new URLSearchParams(location.search); const want=(p.get('book')||'').trim().toLowerCase(); if(want){ const hit=arr.find(x=>String(x.slug||'').toLowerCase()===want); if(hit){ sel.value=hit.slug; } } }catch(_){ }
    if(arr.length && !sel.value){ sel.value = arr[0].slug; }
  }catch(_){ }
}

function parseQuickLabels(text){
  try{
    let s = String(text||'');
    s = s.replace(/\r\n/g,'\n').replace(/,/g,'\n');
    const out = s.split('\n').map(t=>t.trim()).filter(Boolean);
    return out;
  }catch(_){ return []; }
}

async function loadPdfs() {
  const res = await fetch('/api/pdfs');
  const data = await res.json();
  if (data.error) {
    document.getElementById('status').textContent = data.error;
    return;
  }
  allPdfs = data.pdfs;
  extractedPdfs = (data.extracted && typeof data.extracted === 'object') ? data.extracted : {};
  renderPdfList();
  if (allPdfs.length) {
    selectedPdfs.add(allPdfs[0]);
    renderPdfList();
    await refreshPreviewDropdown();
  }
}

async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    const s = await res.json();
    if (s && typeof s === 'object') {
      settingsBase = s;
      profiles = s.profiles || {};
      applySettingsObject(s);
      settingsLoaded = true;
    }
  } catch (e) { /* ignore */ }
}

function applySettingsObject(s) {
  document.getElementById('rows').value = s.rows ?? 6;
  document.getElementById('cols').value = s.cols ?? 6;
  document.getElementById('col_gap_pct').value = s.col_gap_pct ?? 0;
  document.getElementById('row_gap_pct').value = s.row_gap_pct ?? 0;
  document.getElementById('cell_mt').value = s.cell_mt ?? 4;
  document.getElementById('cell_ml').value = s.cell_ml ?? 4;
  document.getElementById('cell_mr').value = s.cell_mr ?? 4;
  document.getElementById('cell_mb').value = s.cell_mb ?? 18;
  lastBottomMb = isFinite(s.last_bottom_mb) ? s.last_bottom_mb : 18;
  if (Array.isArray(s.corners) && s.corners.length === 4) {
    corners = s.corners;
  }
  const remove = (Object.prototype.hasOwnProperty.call(s, 'remove_labels') ? !!s.remove_labels : !s.keep_labels);
  const cb = document.getElementById('remove-labels');
  cb.checked = remove;
  const mb = document.getElementById('cell_mb');
  if (remove) {
    mb.disabled = false;
    const v = parseFloat(mb.value);
    if (isNaN(v) || v === 0) {
      mb.value = (isFinite(lastBottomMb) && lastBottomMb > 0) ? lastBottomMb : 18;
    }
  } else {
    const prev = parseFloat(mb.value);
    if (!isNaN(prev) && prev > 0) lastBottomMb = prev;
    mb.value = 0; mb.disabled = true;
  }
}

function applyProfileFor(pdfName) {
  const prof = profiles && profiles[pdfName];
  if (prof) {
    applySettingsObject(Object.assign({}, settingsBase, prof));
  } else {
    applySettingsObject(settingsBase);
  }
}

async function saveSettings() {
  if (!settingsLoaded) return;
  const payload = {
    rows: parseInt(document.getElementById('rows').value),
    cols: parseInt(document.getElementById('cols').value),
    col_gap_pct: parseFloat(document.getElementById('col_gap_pct').value || 0),
    row_gap_pct: parseFloat(document.getElementById('row_gap_pct').value || 0),
    cell_mt: parseFloat(document.getElementById('cell_mt').value),
    cell_mb: parseFloat(document.getElementById('cell_mb').value),
    cell_ml: parseFloat(document.getElementById('cell_ml').value),
    cell_mr: parseFloat(document.getElementById('cell_mr').value),
    remove_labels: document.getElementById('remove-labels').checked,
    keep_labels: !document.getElementById('remove-labels').checked,
    last_bottom_mb: lastBottomMb,
    corners: corners,
    pdf_key: currentPdfKey,
  };
  try {
    await fetch('/api/settings', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  } catch (e) { /* ignore */ }
}

function renderPdfList() {
  const list = document.getElementById('pdf-list');
  list.innerHTML = '';
  allPdfs.forEach(p => {
    const row = document.createElement('label');
    row.style.cssText = 'display:flex; align-items:center; gap:8px; padding:3px 0; font-size:13px; cursor:pointer;';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = selectedPdfs.has(p);
    cb.style.width = 'auto';
    cb.addEventListener('change', () => {
      if (cb.checked) selectedPdfs.add(p); else selectedPdfs.delete(p);
      document.getElementById('pdf-count').textContent = selectedPdfs.size + ' selected';
      refreshPreviewDropdown();
    });
    row.appendChild(cb);
    const done = extractedPdfs[p];
    row.appendChild(document.createTextNode((done ? '✓ ' : '') + p));
    if(done){ row.title = `${done.saved_count||0} icons saved • ${done.last_saved||''}`; }
    list.appendChild(row);
  });
  document.getElementById('pdf-count').textContent = selectedPdfs.size + ' selected';
}

document.getElementById('select-all-pdfs').addEventListener('click', () => {
  allPdfs.forEach(p => selectedPdfs.add(p));
  renderPdfList();
  refreshPreviewDropdown();
});
document.getElementById('clear-all-pdfs').addEventListener('click', () => {
  selectedPdfs.clear();
  renderPdfList();
});

async function refreshPreviewDropdown() {
  const sel = document.getElementById('preview-pdf-select');
  const prev = sel.value;
  sel.innerHTML = '';
  [...selectedPdfs].forEach(p => {
    const opt = document.createElement('option');
    opt.value = p; opt.textContent = p;
    sel.appendChild(opt);
  });
  if ([...selectedPdfs].includes(prev)) sel.value = prev;
  if (sel.value) await onPreviewPdfChange();
}

async function onPreviewPdfChange() {
  const pdf = document.getElementById('preview-pdf-select').value;
  if (!pdf) return;
  const res = await fetch('/api/pdf_info?pdf=' + encodeURIComponent(pdf));
  const data = await res.json();
  const pageSel = document.getElementById('page-select');
  pageSel.innerHTML = '';
  for (let i = 0; i < data.page_count; i++) {
    const opt = document.createElement('option');
    opt.value = i; opt.textContent = 'Page ' + (i + 1);
    pageSel.appendChild(opt);
  }
  resetCorners();
  currentPdfKey = pdf;
  applyProfileFor(pdf);
  await refreshPreview();
}

let corners = [[0.03, 0.03], [0.97, 0.03], [0.97, 0.82], [0.03, 0.82]];
let handleEls = [];

function resetCorners() {
  corners = [[0.03, 0.03], [0.97, 0.03], [0.97, 0.82], [0.03, 0.82]];
}
document.getElementById('reset-corners').addEventListener('click', () => { resetCorners(); refreshPreview(); saveSettings(); });

function ensureHandles() {
  const wrap = document.getElementById('preview-wrap');
  handleEls.forEach(h => h.remove());
  handleEls = [];
  corners.forEach((c, i) => {
    const h = document.createElement('div');
    h.style.cssText = 'position:absolute; width:18px; height:18px; margin:-9px; border-radius:50%; background:rgba(220,40,40,0.85); border:2px solid white; cursor:grab; touch-action:none;';
    h.dataset.idx = i;
    wrap.appendChild(h);
    handleEls.push(h);
    h.addEventListener('pointerdown', onHandleDown);
  });
  positionHandles();
}

function positionHandles() {
  const img = document.getElementById('preview-img');
  const rect = img.getBoundingClientRect();
  handleEls.forEach((h, i) => {
    const [fx, fy] = corners[i];
    h.style.left = (fx * rect.width) + 'px';
    h.style.top = (fy * rect.height) + 'px';
  });
}

let draggingIdx = null;
function onHandleDown(e) {
  draggingIdx = parseInt(e.target.dataset.idx);
  e.target.style.cursor = 'grabbing';
  e.target.setPointerCapture(e.pointerId);
}
document.addEventListener('pointermove', (e) => {
  if (draggingIdx === null) return;
  const img = document.getElementById('preview-img');
  const rect = img.getBoundingClientRect();
  let fx = (e.clientX - rect.left) / rect.width;
  let fy = (e.clientY - rect.top) / rect.height;
  fx = Math.max(0, Math.min(1, fx));
  fy = Math.max(0, Math.min(1, fy));
  corners[draggingIdx] = [fx, fy];
  positionHandles();
});
document.addEventListener('pointerup', () => {
  if (draggingIdx !== null) {
    handleEls[draggingIdx].style.cursor = 'grab';
    draggingIdx = null;
    refreshPreview();
    saveSettings();
  }
});

async function refreshPreview() {
  const pdf = document.getElementById('preview-pdf-select').value;
  if (!pdf) return;
  const rows = document.getElementById('rows').value;
  const cols = document.getElementById('cols').value;
  const page = document.getElementById('page-select').value || 0;
  const colGap = document.getElementById('col_gap_pct').value || 0;
  const rowGap = document.getElementById('row_gap_pct').value || 0;
  const cornersParam = encodeURIComponent(JSON.stringify(corners));
  const url = `/api/preview?pdf=${encodeURIComponent(pdf)}&rows=${rows}&cols=${cols}&page=${page}&corners=${cornersParam}&col_gap_pct=${colGap}&row_gap_pct=${rowGap}&t=${Date.now()}`;
  const img = document.getElementById('preview-img');
  img.onload = () => { ensureHandles(); };
  img.src = url;
  saveSettings();
}

document.getElementById('preview-pdf-select').addEventListener('change', onPreviewPdfChange);
document.getElementById('page-select').addEventListener('change', refreshPreview);
document.getElementById('rows').addEventListener('change', refreshPreview);
document.getElementById('cols').addEventListener('change', refreshPreview);
document.getElementById('col_gap_pct').addEventListener('change', refreshPreview);
document.getElementById('row_gap_pct').addEventListener('change', refreshPreview);
window.addEventListener('resize', positionHandles);
document.getElementById('cell_mt').addEventListener('change', saveSettings);
document.getElementById('cell_mb').addEventListener('change', saveSettings);
document.getElementById('cell_ml').addEventListener('change', saveSettings);
document.getElementById('cell_mr').addEventListener('change', saveSettings);

async function loadSourceFolder() {
  try {
    const res = await fetch('/api/source_folder');
    const d = await res.json();
    if (d && d.path) document.getElementById('src-folder').value = d.path;
  } catch (e) { /* ignore */ }
}
document.getElementById('save-src-folder').addEventListener('click', async () => {
  const path = document.getElementById('src-folder').value.trim();
  if (!path) return;
  const res = await fetch('/api/source_folder', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ path }) });
  const data = await res.json();
  if (data && data.ok) { await loadPdfs(); await refreshPreviewDropdown(); }
  else if (data && data.error) { document.getElementById('status').textContent = data.error; }
});
document.getElementById('open-src-folder').addEventListener('click', async () => {
  try {
    const res = await fetch('/api/source_folder');
    const d = await res.json();
    if (d && d.path) {
      await fetch('/api/open_path', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ path: d.path }) });
    }
  } catch (e) { /* ignore */ }
});

document.getElementById('remove-labels').addEventListener('change', (e) => {
  const mb = document.getElementById('cell_mb');
  if (e.target.checked) {
    mb.disabled = false;
    const prev = parseFloat(mb.value);
    if (isNaN(prev) || prev === 0) {
      mb.value = (isFinite(lastBottomMb) && lastBottomMb > 0) ? lastBottomMb : 18;
    }
  } else {
    const prev = parseFloat(mb.value);
    if (!isNaN(prev) && prev > 0) lastBottomMb = prev;
    mb.value = 0;
    mb.disabled = true;
  }
  saveSettings();
});

document.getElementById('page-mode').addEventListener('change', () => {
  const mode = document.getElementById('page-mode').value;
  document.getElementById('page-range-field').style.display = (mode === 'range') ? 'flex' : 'none';
});

function parsePageRange(text, maxPages) {
  // Parse "1-3, 5, 7-9" into [0,1,2,4,6,7,8] (0-indexed)
  const result = [];
  const parts = text.split(',').map(s => s.trim()).filter(Boolean);
  for (const part of parts) {
    const m = part.match(/^(\d+)\s*-\s*(\d+)$/);
    if (m) {
      const a = Math.max(1, parseInt(m[1]));
      const b = Math.min(maxPages, parseInt(m[2]));
      for (let i = a; i <= b; i++) result.push(i - 1);
    } else {
      const n = parseInt(part);
      if (!isNaN(n) && n >= 1 && n <= maxPages) result.push(n - 1);
    }
  }
  return [...new Set(result)].sort((a, b) => a - b);
}

function buildPageParams() {
  const mode = document.getElementById('page-mode').value;
  if (mode === 'all') return { page_mode: 'all' };
  if (mode === 'current') {
    const pageSel = document.getElementById('page-select');
    return { page_mode: 'current', page_index: parseInt(pageSel.value || '0') };
  }
  if (mode === 'range') {
    const raw = document.getElementById('page-range-input').value || '';
    return { page_mode: 'range', page_range: raw };
  }
  return { page_mode: 'all' };
}

document.getElementById('extract-btn').addEventListener('click', async () => {
  if (!selectedPdfs.size) { document.getElementById('status').textContent = 'Select at least one PDF first.'; return; }
  document.getElementById('status').textContent = 'Extracting from ' + selectedPdfs.size + ' PDF(s)...';
  const pageParams = buildPageParams();
  const body = {
    pdfs: [...selectedPdfs],
    rows: parseInt(document.getElementById('rows').value),
    cols: parseInt(document.getElementById('cols').value),
    corners: corners,
    col_gap_pct: parseFloat(document.getElementById('col_gap_pct').value || 0),
    row_gap_pct: parseFloat(document.getElementById('row_gap_pct').value || 0),
    cell_mt: parseFloat(document.getElementById('cell_mt').value),
    cell_mb: parseFloat(document.getElementById('cell_mb').value),
    cell_ml: parseFloat(document.getElementById('cell_ml').value),
    cell_mr: parseFloat(document.getElementById('cell_mr').value),
    page_mode: pageParams.page_mode,
    page_index: pageParams.page_index,
    page_range: pageParams.page_range,
  };
  const res = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  const data = await res.json();
  if (data.error) { document.getElementById('status').textContent = data.error; return; }
  let statusMsg = `Extracted ${data.count} tile(s) across ${data.groups.length} PDF(s).`;
  if (data.errors && data.errors.length) statusMsg += ' Errors: ' + data.errors.join('; ');
  document.getElementById('status').textContent = statusMsg;
  renderGroups(data.groups);
  document.getElementById('save-btn').style.display = data.count ? 'inline-block' : 'none';
});

function setBatchProgress(show, done = 0, total = 0) {
  const wrap = document.getElementById('batch-progress');
  if (show) {
    wrap.style.display = 'flex';
    const pct = total ? Math.floor((done / total) * 100) : 0;
    document.getElementById('batch-bar-inner').style.width = pct + '%';
    document.getElementById('batch-text').textContent = `${done}/${total}`;
  } else {
    wrap.style.display = 'none';
    document.getElementById('batch-bar-inner').style.width = '0%';
    document.getElementById('batch-text').textContent = '0/0';
  }
}

async function runBatchExtract(pdfs) {
  if (!pdfs || !pdfs.length) { document.getElementById('status').textContent = 'No PDFs found in the source folder.'; return; }
  if (batchRunning) return;
  batchRunning = true;
  batchCancel = false;
  const total = pdfs.length;
  let done = 0;
  setBatchProgress(true, 0, total);
  document.getElementById('status').textContent = `Extracting from ${total} PDF(s)...`;

  const common = {
    rows: parseInt(document.getElementById('rows').value),
    cols: parseInt(document.getElementById('cols').value),
    corners: corners,
    col_gap_pct: parseFloat(document.getElementById('col_gap_pct').value || 0),
    row_gap_pct: parseFloat(document.getElementById('row_gap_pct').value || 0),
    cell_mt: parseFloat(document.getElementById('cell_mt').value),
    cell_mb: parseFloat(document.getElementById('cell_mb').value),
    cell_ml: parseFloat(document.getElementById('cell_ml').value),
    cell_mr: parseFloat(document.getElementById('cell_mr').value),
  };
  Object.assign(common, buildPageParams());

  const allGroups = [];
  let totalTiles = 0;
  const errors = [];

  for (const pdf of pdfs) {
    if (batchCancel) break;
    try {
      const body = Object.assign({ pdf }, common);
      const res = await fetch('/api/extract', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
      const data = await res.json();
      if (data.error) { errors.push(data.error); }
      if (Array.isArray(data.groups)) {
        allGroups.push(...data.groups);
        totalTiles += (data.count || 0);
      }
      if (Array.isArray(data.errors) && data.errors.length) {
        errors.push(...data.errors);
      }
    } catch (e) {
      errors.push(String(e));
    }
    done += 1;
    setBatchProgress(true, done, total);
  }

  batchRunning = false;
  setBatchProgress(false);
  let msg;
  if (batchCancel) {
    msg = `Cancelled after ${done} of ${total} PDF(s). Extracted ${totalTiles} tile(s).`;
  } else {
    msg = `Extracted ${totalTiles} tile(s) across ${done} PDF(s).`;
  }
  if (errors.length) msg += ' Errors: ' + errors.join('; ');
  document.getElementById('status').textContent = msg;
  if (allGroups.length) {
    renderGroups(allGroups);
    document.getElementById('save-btn').style.display = 'inline-block';
  }
}

document.getElementById('batch-cancel').addEventListener('click', () => { batchCancel = true; document.getElementById('status').textContent = 'Cancelling…'; });

document.getElementById('extract-all-btn').addEventListener('click', async () => {
  if (!allPdfs.length) { document.getElementById('status').textContent = 'No PDFs found in the source folder.'; return; }
  const ok = confirm('Batch extract all ' + allPdfs.length + ' PDF(s) in the source folder using the current grid/corners?');
  if (!ok) return;
  await runBatchExtract(allPdfs);
});

function renderGroups(groups) {
  const container = document.getElementById('grid-groups');
  container.innerHTML = '';
  try{ window.__pdfGroups = groups||[]; }catch(_){ }
  if (!window.__pdfHero) window.__pdfHero = {}; // { pdf: tileId }
  groups.forEach(g => {
    if (!g.tiles.length) return;
    const section = document.createElement('div');
    section.style.marginBottom = '24px';

    const heading = document.createElement('div');
    heading.style.cssText = 'display:flex; align-items:center; gap:10px; margin:16px 0 8px; padding-bottom:6px; border-bottom:2px solid #31A8A0;';
    heading.innerHTML = `<strong style="font-size:14px;">${g.pdf}</strong> <span style="font-size:12px; color:#777;">${g.tiles.length} tile(s)</span>`;
    section.appendChild(heading);

    const bookRow = document.createElement('div');
    bookRow.style.cssText = 'margin-bottom:8px;';
    bookRow.innerHTML = `<label style="display:inline-block; margin-right:6px;">Book name for this group:</label><input type="text" class="source-book-input" data-pdf="${g.pdf}" value="${g.suggested_book}" style="width:200px;">`;
    section.appendChild(bookRow);

    const grid = document.createElement('div');
    grid.id = 'grid';
    grid.style.cssText = 'display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:12px;';
    g.tiles.forEach(t => {
      const cell = document.createElement('div');
      cell.className = 'tile';
      cell.innerHTML = `
        <img src="/api/tile/${t.id}" />
        <button class="hero-star-btn" data-tile="${t.id}" data-pdf="${g.pdf}" title="Mark as hero image" style="position:absolute;top:2px;right:2px;font-size:22px;background:rgba(255,255,255,0.9);border:1px solid #cbd5e1;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;cursor:pointer;color:#94a3b8;padding:0;line-height:1;z-index:10;">&#9733;</button>
        <div class="tile-input-row">
          <input type="text" data-tile="${t.id}" data-pdf="${g.pdf}" placeholder="label" />
          <button class="mic-btn" data-tile="${t.id}" title="Speak label">🎤</button>
        </div>
      `;
      grid.appendChild(cell);
    });
    section.appendChild(grid);
    container.appendChild(section);
  });
  wireMics();
  wireHeroStars();
}

function wireHeroStars() {
  document.querySelectorAll('.hero-star-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tileId = btn.getAttribute('data-tile');
      const pdf = btn.getAttribute('data-pdf');
      if (!window.__pdfHero) window.__pdfHero = {};
      const current = window.__pdfHero[pdf];
      if (current === tileId) {
        // Unset
        delete window.__pdfHero[pdf];
        btn.style.color = '#94a3b8';
        btn.style.background = 'rgba(255,255,255,0.9)';
        btn.style.borderColor = '#cbd5e1';
        btn.title = 'Mark as hero image';
      } else {
        // Set new hero, clear previous
        window.__pdfHero[pdf] = tileId;
        btn.style.color = '#fff';
        btn.style.background = '#E1B42D';
        btn.style.borderColor = '#E1B42D';
        btn.title = 'Hero image (click to unset)';
        // Clear previous star in same group
        document.querySelectorAll(`.hero-star-btn[data-pdf="${pdf}"]`).forEach(b => {
          if (b !== btn) {
            b.style.color = '#94a3b8';
            b.style.background = 'rgba(255,255,255,0.9)';
            b.style.borderColor = '#cbd5e1';
            b.title = 'Mark as hero image';
          }
        });
      }
    });
  });
}

function wireMics() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  document.querySelectorAll('.mic-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!SR) { alert('Voice input not supported in this browser. Try Chrome or Edge.'); return; }
      const rec = new SR();
      rec.continuous = false;
      rec.interimResults = false;
      rec.lang = 'en-US';
      const tileId = btn.getAttribute('data-tile');
      const input = document.querySelector(`input[data-tile="${tileId}"]`);
      btn.classList.add('listening');
      rec.onresult = (e) => { input.value = e.results[0][0].transcript; };
      rec.onend = () => { btn.classList.remove('listening'); };
      rec.onerror = () => { btn.classList.remove('listening'); };
      rec.start();
    });
  });
}

document.getElementById('save-btn').addEventListener('click', async () => {
  const labels = {};
  const tileSources = {};
  const bookByPdf = {};
  document.querySelectorAll('.source-book-input').forEach(inp => {
    bookByPdf[inp.getAttribute('data-pdf')] = inp.value.trim();
  });
  document.querySelectorAll('#grid-groups input[data-tile]').forEach(inp => {
    const tileId = inp.getAttribute('data-tile');
    labels[tileId] = inp.value;
    tileSources[tileId] = bookByPdf[inp.getAttribute('data-pdf')] || '';
  });
  const res = await fetch('/api/save_labels', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ labels, tile_sources: tileSources }) });
  const data = await res.json();
  const summary = document.getElementById('save-summary');
  summary.style.display = 'block';
  let msg = `Saved ${data.saved_count} icon(s). Skipped ${data.skipped_empty} empty box(es).`;
  if (data.duplicate_count > 0) {
    msg += ` ${data.duplicate_count} label(s) already existed -- those were kept as extra copies (not overwritten, not merged), so you can compare and choose between them later.`;
  }

  // Save hero selections via /api/meta/save for each book that has a starred tile
  if (window.__pdfHero) {
    for (const [pdf, heroTileId] of Object.entries(window.__pdfHero)) {
      const heroLabel = labels[heroTileId] || '';
      const bookName = bookByPdf[pdf] || '';
      if (heroLabel && bookName) {
        try {
          await fetch('/api/meta/save', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ book: bookName, hero: heroLabel, cover: '' }) });
          msg += ` Hero set for ${bookName}: ${heroLabel}.`;
        } catch (_) { /* ignore hero save errors */ }
      }
    }
  }

  summary.textContent = msg;
  document.getElementById('open-output-btn').style.display = 'inline-block';
});

document.getElementById('open-output-btn').addEventListener('click', async () => {
  try { await fetch('/api/open_output', { method: 'POST' }); } catch (e) { /* ignore */ }
});

document.getElementById('open-theme-btn').addEventListener('click', async () => {
  const sel = document.getElementById('book-select');
  const bk = sel? sel.value: '';
  if(!bk){ alert('Pick a book'); return; }
  try{ await fetch('/api/open_theme', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: bk}) }); }catch(_){ }
});

document.getElementById('save-theme-btn').addEventListener('click', async () => {
  const sel = document.getElementById('book-select');
  const bk = sel? sel.value: '';
  if(!bk){ alert('Pick a book'); return; }
  const labels = parseQuickLabels(document.getElementById('quick-labels').value||'');
  const alsoLib = !!(document.getElementById('also-lib')&&document.getElementById('also-lib').checked);
  // Build tile IDs in reading order across groups
  const groups = window.__pdfGroups || [];
  const tileIds = [];
  const tileSources = {};
  // Per-group source book (for provenance)
  const bookByPdf = {};
  document.querySelectorAll('.source-book-input').forEach(inp=>{ bookByPdf[inp.getAttribute('data-pdf')] = (inp.value||'').trim(); });
  groups.forEach(g=>{ (g.tiles||[]).forEach(t=>{ if(t&&t.id){ tileIds.push(t.id); tileSources[t.id] = bookByPdf[g.pdf]||''; } }); });
  if(!tileIds.length){ alert('Extract tiles first.'); return; }
  try{
    const res = await fetch('/api/pdf_save_to_theme', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ book: bk, tile_ids: tileIds, labels: labels, tile_sources: tileSources, also_library: alsoLib }) });
    const data = await res.json();
    const sum = document.getElementById('save-summary');
    sum.style.display='block';
    sum.textContent = `Saved to theme ${data.saved_theme||0} icon(s)`
      + (data.dup_theme? `, ${data.dup_theme} duplicate name(s) auto-suffixed`: '')
      + (data.auto_named? `, ${data.auto_named} auto-named`: '')
      + (alsoLib? `; library: ${data.saved_library||0} saved${data.dup_library? ', '+data.dup_library+' dup':''}`: '');
  }catch(e){ alert('Save failed'); }
});

document.getElementById('hard-reload').addEventListener('click', () => {
  const url = window.location.origin + window.location.pathname + '?t=' + Date.now();
  window.location.replace(url);
});

loadBooksForPdf().then(()=> loadSettings()).then(() => loadSourceFolder()).then(() => loadPdfs()).then(() => refreshPreview());
</script>
</body>
</html>"""

def _crop_quad_to_rect(img):
    W, H = img.width, img.height
    def _do(corners):
        pts = [(c[0] * W, c[1] * H) for c in corners]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        out_w = max(10, int(max(xs) - min(xs)))
        out_h = max(10, int(max(ys) - min(ys)))
        tl, tr, br, bl = pts
        quad = (tl[0], tl[1], bl[0], bl[1], br[0], br[1], tr[0], tr[1])
        return img.transform((out_w, out_h), Image.QUAD, quad, resample=Image.BICUBIC)
    return _do

def _make_background_transparent(tile, tolerance: int = 30):
    img = tile.convert("RGBA")
    w, h = img.size
    px = img.load()
    corner_pts = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    samples = [px[x, y][:3] for x, y in corner_pts]
    bg = tuple(sum(c[i] for c in samples) // len(samples) for i in range(3))
    out = Image.new("RGBA", (w, h))
    out_px = out.load()
    tol = tolerance
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if abs(r - bg[0]) <= tol and abs(g - bg[1]) <= tol and abs(b - bg[2]) <= tol:
                out_px[x, y] = (r, g, b, 0)
            else:
                out_px[x, y] = (r, g, b, 255)
    return out

def _html_guides() -> str:
    return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Icon Labeler Guides</title><style>body{font-family:Segoe UI,system-ui,Arial;margin:18px;color:#0D2545;background:#fafafa}h1{color:#31A8A0;margin:0 0 8px 0}.row{display:flex;gap:10px;align-items:center;margin:8px 0}.pill{display:inline-block;padding:2px 6px;border-radius:999px;border:1px solid #cbd5e1;margin:2px 4px;font-size:12px}.pill.ok{background:#dcfce7;border-color:#86efac;color:#166534}.pill.auto{background:#e0f2fe;border-color:#7dd3fc;color:#075985}.pill.miss{background:#fee2e2;border-color:#fca5a5;color:#991b1b}.ok{background:#e6fffa;border-color:#99f6e4}.miss{background:#fff1f2;border-color:#fecdd3}.panel{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin-top:12px}.tile{width:90px;height:90px;display:flex;align-items:center;justify-content:center;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:6px}.tile img{max-width:80px;max-height:80px;object-fit:contain}.card{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px}  :focus-visible { outline: 2px solid #0F766E; outline-offset: 2px; }
</style></head><body><h1>Required from vocab</h1><div class='row'><div><b>Book:</b> <span id='bk'></span></div><button id='reload' style='margin-left:8px'>Reload</button><button id='apply' style='margin-left:8px'>Apply to activity_images</button></div><div id='status' class='panel muted'></div><div style='display:flex;gap:12px;align-items:flex-start'><div id='words' style='flex:1;max-height:70vh;overflow:auto;border:1px solid #e2e8f0;border-radius:6px;padding:6px'></div><div id='sug' style='flex:2'></div></div><script>const $=s=>document.querySelector(s);async function j(u,o){const r=await fetch(u,o);if(!r.ok)throw new Error(await r.text());return await r.json()}function qp(n){const p=new URLSearchParams(location.search);return (p.get(n)||'').trim()}let items=[];let cur='';async function load(){const b=qp('book'); if(!b){$('#status').textContent='Missing ?book='; return;} $('#bk').textContent=b; try{ const r=await j('/api/required?book='+encodeURIComponent(b)); items=r.items||[]; renderList(); }catch(e){ console.error(e); $('#status').textContent='Failed'; }}function renderList(){ const el=$('#words'); el.innerHTML=''; let have=0; items.forEach(it=>{ const d=document.createElement('div'); d.className='pill '+(it.current_path?'ok':'miss'); d.style.cursor='pointer'; d.textContent=it.word; d.onclick=()=>sel(it.word); el.appendChild(d); if(it.current_path) have++; }); $('#status').textContent = (items.length||0)+' required, '+have+' with icons'; $('#sug').innerHTML=''; }async function sel(w){ cur=w; const b=qp('book'); const r=await j('/api/suggest?book='+encodeURIComponent(b)+'&word='+encodeURIComponent(w)+'&k=8'); const arr=r.items||[]; const rows=arr.map((it,i)=>`<div class='card' style='display:flex;gap:8px;align-items:center;margin-bottom:8px'><div class='tile'><img src='/file?path=${encodeURIComponent(it.path)}'></div><div style='flex:1'><div class='muted'>${it.label||it.path} ${it.score!==undefined? '('+it.score+')':''}</div><div style='margin-top:4px'><button data-i='${i}' class='a'>Accept</button><input placeholder='rename' data-i='${i}' class='r' style='margin-left:6px'><button data-i='${i}' class='ar' style='margin-left:6px'>Accept+rename</button></div></div></div>`).join(''); $('#sug').innerHTML = `<div><b>Word:</b> ${w}</div><div style='margin:6px 0'><button class='sk'>Skip</button><button class='ms' style='margin-left:6px'>Mark missing</button></div>${rows||'<i>No suggestions</i>'}`; $('#sug').querySelectorAll('.a').forEach(btn=>{ btn.onclick=async()=>{ const i=parseInt(btn.getAttribute('data-i')); const it=arr[i]; await dec(w,'replaced',it.path,''); alert('Saved'); }; }); $('#sug').querySelectorAll('.ar').forEach(btn=>{ btn.onclick=async()=>{ const i=parseInt(btn.getAttribute('data-i')); const it=arr[i]; const input=$('#sug').querySelector('.r[data-i="'+i+'"]'); const lbl=(input&&input.value)||''; await dec(w,'replaced',it.path,lbl); alert('Saved'); }; }); const sk=$('#sug').querySelector('.sk'); if(sk) sk.onclick=async()=>{ await dec(w,'skip','',''); alert('Saved'); }; const ms=$('#sug').querySelector('.ms'); if(ms) ms.onclick=async()=>{ await dec(w,'missing','',''); alert('Saved'); }; }async function dec(word, decision, path, label){ const b=qp('book'); await j('/api/decision',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book:b, word, decision, path, label})}); }async function applyAll(){ const b=qp('book'); const r=await j('/api/apply',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book:b})}); alert('Applied: '+(r.copied||0)+' copied, '+(r.updated||0)+' updated'); await load(); }document.addEventListener('DOMContentLoaded',()=>{ const b=qp('book'); if(!b){ $('#status').textContent='Missing ?book='; return; } document.getElementById('reload').onclick=load; document.getElementById('apply').onclick=applyAll; load(); }, false);</script></body></html>"""
def _sanitize_label(s: str) -> str:
    t = "".join(ch if ch.isalnum() else "_" for ch in s.lower())
    t = "_".join([p for p in t.split("_") if p])
    return t or "icon"

# Minimal Vocab Review UI (queue + approve/reject + inline hero/cover picker)
def _html_vocab() -> str:
    return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Icon Labeler — Vocab Review</title>
<style>
  body{font-family:Segoe UI,system-ui,Arial;margin:18px;color:#0D2545;background:#fafafa}
  h1{color:#31A8A0;margin:0 0 8px 0}
  .row{display:flex;gap:10px;align-items:center;margin:8px 0;flex-wrap:wrap}
  button,select,input{font:inherit;padding:6px 10px}
  .lists{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .card{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:12px}
  .muted{color:#64748b;font-size:12px}
  .warn{background:#fff7ed;border:1px solid #fdba74;color:#9a3412;padding:6px 8px;border-radius:6px;margin:6px 0}
  .err{background:#fef2f2;border:1px solid #fecaca;color:#7f1d1d;padding:6px 8px;border-radius:6px;margin:6px 0}
  .ok{background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46;padding:6px 8px;border-radius:6px;margin:6px 0}
  .kvs{font-size:13px}
  .kv{margin:2px 0}
  .fr{margin:2px 0}
  .hero-panel{margin-top:10px;padding:10px;border:1px dashed #cbd5e1;border-radius:8px;background:#f8fafc}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-top:8px}
  .tile{background:#f1f5f9;border:1px solid #cbd5e1;border-radius:6px;padding:6px;text-align:center}
  .tile img{max-width:110px;max-height:110px;object-fit:contain}
  .pill{display:inline-block;padding:2px 6px;border-radius:999px;border:1px solid #cbd5e1;margin:2px 4px;font-size:12px}.pill.ok{background:#dcfce7;border-color:#86efac;color:#166534}.pill.auto{background:#e0f2fe;border-color:#7dd3fc;color:#075985}.pill.miss{background:#fee2e2;border-color:#fca5a5;color:#991b1b}
  .btn{padding:6px 10px;border:1px solid #cbd5e1;border-radius:6px;background:#fff;cursor:pointer}
  .btn.primary{background:#31A8A0;border-color:#31A8A0;color:#fff}
  .sep{height:1px;background:#e5e7eb;margin:10px 0}
</style></head><body>
<h1>Vocab Review</h1>
<div class='muted' style='margin:6px 0 10px 0'>
  Use <b>Generate</b> to create a pending review for a book. When done, it moves to <b>Needs your review</b>.
  Click <b>Approve</b> to promote, then pick <b>hero</b>/<b>cover</b> inline. To review per‑word icons (accept/rename/search), open <b>/guides?book=&lt;slug&gt;</b> after promotion.
</div>
<div class='row'>
  <button id='reload' class='btn'>Reload</button>
  <button id='gen-missing' class='btn'>Generate missing (background)</button>
  <span class='muted' id='status'></span>
  <span style='flex:1'></span>
  <input id='slug' list='sluglist' placeholder='slug to generate'>
  <datalist id='sluglist'></datalist>
  <label class='muted' style='display:flex;align-items:center;gap:6px'><input type='checkbox' id='ovw'> overwrite if promoted</label>
  <button id='gen-one' class='btn primary'>Generate for slug</button>
</div>
<div class='lists'>
  <div>
    <h3>Needs your review</h3>
    <div id='list-pending'></div>
  </div>
  <div>
    <h3>No vocab yet</h3>
    <div id='list-missing'></div>
  </div>
  
</div>
<script>
const $=s=>document.querySelector(s);
async function j(url,opts){const r=await fetch(url,opts);if(!r.ok)throw new Error(await r.text());return await r.json()}
function esc(s){return String(s||'').replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))}
let JOBS={};
let MISSING=[];

async function loadQueue(){
  try{
    const d=await j('/api/vocab_queue');
    renderPending(d.pending||[]);
    renderMissing(d.missing||[]);
    MISSING = d.missing||[];
    try{
      const dl=document.getElementById('sluglist');
      if(dl){ dl.innerHTML=''; (MISSING||[]).forEach(it=>{ const o=document.createElement('option'); o.value=String(it.slug||''); dl.appendChild(o); }); }
    }catch(_){ }
    $('#status').textContent='';
  }catch(e){ $('#status').textContent='Failed to load'; }
}

function renderPending(arr){
  const el=$('#list-pending'); el.innerHTML='';
  if(!arr.length){ el.innerHTML = '<div class="muted">None pending</div>'; return; }
  arr.forEach(it=>{
    const d=document.createElement('div'); d.className='card';
    const warns=(it.guardrail_warnings||[]); const grounded=!!it.grounded;
    const ambc = Number(it.ambiguous_count||0);
    d.innerHTML = `
      <div class='kvs'>
        <div class='kv'><b>${esc(it.title||it.slug)}</b> <span class='muted'>(slug: ${esc(it.slug)})</span></div>
        <div class='kv'>Author: ${esc(it.author||'')}</div>
        <div class='kv'>Year: ${esc(it.pub_year||'')}</div>
      </div>
      <div class='sep'></div>
      <div><b>Summary</b></div>
      <div class='kv'>${esc(it.book_summary||'(no summary)')}</div>
      ${warns.length? `<div class='warn'>Guardrail warnings: ${esc(warns.join(', '))}</div>`:''}
      ${!grounded? `<div class='warn'>Ungrounded — verify before approving</div>`:''}
      ${ambc? `<div class='warn'>Ambiguous words: ${ambc}</div>`:''}
      <div class='sep'></div>
      <div><b>Fringe (11) + why</b></div>
      <div>${(it.fringe_11||[]).map(w=>`<div class='fr'><span class='pill'>${esc(w)}</span> — ${esc((it.fringe_justifications||{})[w]||'')}</div>`).join('')}</div>
      <div class='sep'></div>
      <div class='row'>
        <button class='btn primary' data-act='approve'>Approve</button>
        <button class='btn' data-act='reject'>Reject</button>
      </div>
      <div class='hero-panel' style='display:none'></div>
    `;
    const panel=d.querySelector('.hero-panel');
    d.querySelector("[data-act='approve']").onclick=async()=>{
      try{ const r=await j('/api/vocab_promote/'+encodeURIComponent(it.slug),{method:'POST'}); if(!r.ok){ alert(r.error||'Failed'); return; } }catch(e){ alert('Failed'); return; }
      // Show inline hero/cover picker
      panel.style.display='block';
      panel.innerHTML = `<div class='muted'>Approved. Pick hero and cover below for ${esc(it.slug)}.</div><div class='grid' id='grid-${esc(it.slug)}'></div>`;
      renderHeroPicker(it.slug, panel.querySelector(`#grid-${CSS.escape(it.slug)}`));
    };
    d.querySelector("[data-act='reject']").onclick=async()=>{
      try{ const r=await j('/api/vocab_reject/'+encodeURIComponent(it.slug),{method:'POST'}); if(!r.ok){ alert(r.error||'Failed'); return; } }catch(e){ alert('Failed'); return; }
      await loadQueue();
    };
    el.appendChild(d);
  });
}

async function renderHeroPicker(slug, gridEl){
  try{
    const meta = await j('/api/meta?book='+encodeURIComponent(slug));
    const r = await j('/api/list?book='+encodeURIComponent(slug));
    const items = r.items||[];
    gridEl.innerHTML='';
    items.forEach(it=>{
      const c=document.createElement('div'); c.className='tile';
      const isHero = (String(meta.hero||'')===it.name);
      const isCover = (String(meta.cover||'')===it.name);
      c.innerHTML = `
        <div><img src='/file?path=${encodeURIComponent(it.path)}'></div>
        <div class='muted'>${esc(it.name)}</div>
        <div style='font-size:12px;margin-top:6px'>
          <button class='btn' data-act='hero'>${isHero? 'Unset hero':'Set hero'}</button>
          <label style='margin-left:6px'><input type='radio' name='cover-${esc(slug)}' ${isCover? 'checked':''}> cover</label>
        </div>`;
      const heroBtn=c.querySelector("[data-act='hero']");
      const cover=c.querySelector("input[type='radio']");
      heroBtn.onclick=async()=>{
        const next = isHero? '': it.name;
        try{ await j('/api/meta/save',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: slug, hero: next, cover: meta.cover||''})}); meta.hero = next; renderHeroPicker(slug, gridEl); }catch(e){ alert('Failed'); }
      };
      cover.onchange=async()=>{
        if(!cover.checked) return; try{ await j('/api/meta/save',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: slug, hero: meta.hero||'', cover: it.name})}); meta.cover = it.name; renderHeroPicker(slug, gridEl); }catch(e){ alert('Failed'); }
      };
      gridEl.appendChild(c);
    });
  }catch(e){ gridEl.innerHTML = '<div class="err">Failed to load hero/cover picker.</div>'; }
}

function renderMissing(arr){
  const el=$('#list-missing'); el.innerHTML='';
  if(!arr.length){ el.innerHTML = '<div class="muted">All books have vocab or a pending review.</div>'; return; }
  arr.forEach(it=>{
    const d=document.createElement('div'); d.className='card';
    d.innerHTML = `
      <div><b>${esc(it.slug)}</b> <span class='muted'>(icons: ${Number(it.icon_count||0)})</span></div>
      <div class='row'><button class='btn' data-act='gen'>Generate</button></div>
      <div class='muted job' style='display:none'></div>
    `;
    const jobEl = d.querySelector('.job');
    d.querySelector("[data-act='gen']").onclick=async()=>{
      jobEl.style.display='block'; jobEl.textContent='Starting…';
      let jid='';
      try{ const r=await j('/api/vocab_generate',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({slug: it.slug})}); jid=r.id; }catch(e){ jobEl.textContent='Failed to start'; return; }
      pollJob(jid, jobEl, async ()=>{ await loadQueue(); });
    };
    el.appendChild(d);
  });
}

async function pollJob(id, el, onDone){
  try{
    const r = await j('/api/vocab_job_status/'+encodeURIComponent(id));
    if(r.status==='running'){
      el.textContent = `Running… ${r.done||0}/${r.total||0}`;
      setTimeout(()=>pollJob(id, el, onDone), 1200);
    }else{
      const res = Array.isArray(r.results)? r.results: [];
      const oks = res.filter(x=>x&&x.ok).length;
      const fails = res.filter(x=>!x||x.ok===false).length;
      let msg = `Complete. ${oks} ok` + (fails? `, ${fails} failed`: '');
      if(fails){
        const ff = res.find(x=>!x||x.ok===false);
        if(ff && ff.error){ msg += ` — ${String(ff.error)}`; }
      }
      el.textContent = msg;
      if(onDone) onDone();
    }
  }catch(e){ el.textContent='Failed'; }
}

$('#reload').onclick=loadQueue;
$('#gen-missing').onclick=async()=>{
  $('#status').textContent='Starting background job…';
  try{ const r=await j('/api/vocab_generate',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({missing_only:true})}); const id=r.id; $('#status').textContent='Job '+id+' started'; pollJob(id,$('#status'),loadQueue); }catch(e){ $('#status').textContent='Failed to start'; }
};
$('#gen-one').onclick=async()=>{
  const slug=($('#slug').value||'').trim(); if(!slug){ alert('Enter a slug'); return; }
  $('#status').textContent='Starting '+slug+'…';
  try{ const ovw = !!(document.getElementById('ovw') && document.getElementById('ovw').checked); const r=await j('/api/vocab_generate',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({slug, overwrite: ovw})}); const id=r.id; pollJob(id,$('#status'),loadQueue); }catch(e){ $('#status').textContent='Failed to start'; }
};

loadQueue().catch(()=>{});
</script>
</body></html>"""

def _file_under_base(p: Path) -> bool:
    try:
        return BASE in p.resolve().parents or p.resolve() == BASE
    except Exception:
        return False

def _bingo_incomplete_cells(val, required: int = 9) -> bool:
    try:
        cards = _bingo_extract_card_labels(val)
        for lst in cards:
            if not lst:
                return True
            if len(lst) < required:
                return True
            # also ensure unique count is still == required
            if len(set(lst)) < required:
                return True
    except Exception:
        return True
    return False

def _apply_deterministic_post_checks(finals: dict):
    """Move hard-violating items from finals to needs and return (finals2, needs_add, hard_fields).
    Hard rules:
    - bingo_card_sets: no duplicates per card
    - code_words_puzzles: no self-reference between target and clue icons
    - matching_pairs: no identical left/right
    """
    try:
        import copy as _copy
        finals2 = _copy.deepcopy(finals or {})
    except Exception:
        finals2 = dict(finals or {})
    needs_add: dict = {"book_vocab": {}}
    hard_fields: set[str] = set()

    def _move(field: str, idx: int, val, reason: str):
        hard_fields.add(field)
        # Remove from finals2
        try:
            arr = list((finals2.get("book_vocab", {}) or {}).get(field) or [])
            if 0 <= idx < len(arr):
                arr.pop(idx)
            finals2.setdefault("book_vocab", {})[field] = arr
        except Exception:
            pass
        # Add to needs with deterministic reason flag
        try:
            it = val if isinstance(val, dict) else {"text": val}
            if isinstance(it, dict):
                it = dict(it)
                it.setdefault("guardrail_flags", [])
                try:
                    if isinstance(it["guardrail_flags"], list):
                        it["guardrail_flags"].append(f"deterministic:{reason}")
                except Exception:
                    it["guardrail_flags"] = [f"deterministic:{reason}"]
            needs_add.setdefault("book_vocab", {}).setdefault(field, []).append(it)
        except Exception:
            pass

    bv = (finals or {}).get("book_vocab", {}) or {}
    # bingo duplicates or too few cells
    arr = list(bv.get("bingo_card_sets") or [])
    for i, v in enumerate(arr):
        try:
            if _bingo_has_duplicates(v) or _bingo_incomplete_cells(v, required=9):
                why = "bingo_incomplete_or_duplicate" if _bingo_incomplete_cells(v, 9) else "bingo_duplicate_icons"
                _move("bingo_card_sets", i, v, why)
        except Exception:
            continue
    # code-words self reference
    arr = list(bv.get("code_words_puzzles") or [])
    for i, v in enumerate(arr):
        try:
            if _codewords_has_self_reference(v):
                _move("code_words_puzzles", i, v, "codewords_self_reference")
        except Exception:
            continue
    # matching_pairs trivial identity
    arr = list(bv.get("matching_pairs") or [])
    for i, v in enumerate(arr):
        try:
            if _pairs_have_identity(v):
                _move("matching_pairs", i, v, "matching_pairs_identity")
        except Exception:
            continue
    return finals2, needs_add, hard_fields

def _iter_pngs(paths):
    for d in paths:
        if not d.exists():
            continue
        if d.is_file() and d.suffix.lower() == ".png":
            yield d
            continue
        try:
            for p in d.rglob("*.png"):
                if p.is_file():
                    yield p
        except Exception:
            continue

def _theme_dir(slug: str) -> Path:
    return ASSETS / "themes" / str(slug)

def _vs_path(slug: str) -> Path:
    return _theme_dir(slug) / "vocab_suggestions.json"

def _json_load(path: Path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None

def _json_save(path: Path, obj: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def _book_vocab_path(slug: str) -> Path:
    p = ASSETS / "themes" / slug / "book_vocab.json"
    if p.exists():
        return p
    return ASSETS / "themes" / slug / "config" / "book_vocab.json"

# Deterministic guardrail helpers for Vocab Suggestions
def _norm_label(s) -> str:
    try:
        import re as _re
        return _re.sub(r"[^a-z0-9]+", "", str(s or "").strip().lower())
    except Exception:
        return str(s or "").strip().lower()

def _bingo_extract_card_labels(val):
    cards: list[list[str]] = []
    try:
        v = val or {}
        # Common shapes: {cards: [[..],[..]]} or {grid: [[..]]} or {words: [...]} or plain list
        if isinstance(v, dict):
            if isinstance(v.get("cards"), list):
                for c in v.get("cards") or []:
                    lst = []
                    for it in (c or []):
                        if isinstance(it, str):
                            lst.append(_norm_label(it))
                        elif isinstance(it, dict):
                            for k in ("word","label","icon","name","text"):
                                if it.get(k) is not None:
                                    lst.append(_norm_label(it.get(k)))
                                    break
                    if lst:
                        cards.append(lst)
            elif isinstance(v.get("grid"), list):
                for row in v.get("grid") or []:
                    lst = []
                    for it in (row or []):
                        if isinstance(it, str):
                            lst.append(_norm_label(it))
                        elif isinstance(it, dict):
                            for k in ("word","label","icon","name","text"):
                                if it.get(k) is not None:
                                    lst.append(_norm_label(it.get(k)))
                                    break
                    if lst:
                        cards.append(lst)
            elif isinstance(v.get("words"), list):
                lst = [_norm_label(x) for x in (v.get("words") or [])]
                if lst:
                    cards.append(lst)
            elif isinstance(v.get("items"), list):
                lst = []
                for it in v.get("items") or []:
                    if isinstance(it, str):
                        lst.append(_norm_label(it))
                    elif isinstance(it, dict):
                        for k in ("word","label","icon","name","text"):
                            if it.get(k) is not None:
                                lst.append(_norm_label(it.get(k)))
                                break
                if lst:
                    cards.append(lst)
        elif isinstance(v, list):
            cards.append([_norm_label(x) for x in v])
    except Exception:
        return cards
    return cards

def _bingo_extract_card_originals(val):
    """Extract raw string labels for bingo cards (best effort)."""
    cards: list[list[str]] = []
    try:
        v = val or {}
        def _raw(it):
            if isinstance(it, str):
                return it
            if isinstance(it, dict):
                for k in ("word","label","icon","name","text"):
                    if it.get(k) is not None:
                        return str(it.get(k))
            return None
        if isinstance(v, dict):
            if isinstance(v.get("cards"), list):
                for c in v.get("cards") or []:
                    row = []
                    for it in (c or []):
                        r = _raw(it)
                        if r:
                            row.append(r)
                    if row:
                        cards.append(row)
            elif isinstance(v.get("grid"), list):
                for c in v.get("grid") or []:
                    row = []
                    for it in (c or []):
                        r = _raw(it)
                        if r:
                            row.append(r)
                    if row:
                        cards.append(row)
            elif isinstance(v.get("words"), list):
                row = []
                for it in (v.get("words") or []):
                    r = _raw(it)
                    if r:
                        row.append(r)
                if row:
                    cards.append(row)
            elif isinstance(v.get("items"), list):
                row = []
                for it in (v.get("items") or []):
                    r = _raw(it)
                    if r:
                        row.append(r)
                if row:
                    cards.append(row)
        elif isinstance(v, list):
            row = []
            for it in v:
                r = _raw(it)
                if r:
                    row.append(r)
            if row:
                cards.append(row)
    except Exception:
        return cards
    return cards

def _bingo_has_duplicates(val) -> bool:
    try:
        cards = _bingo_extract_card_labels(val)
        for lst in cards:
            if not lst:
                continue
            if len(set(lst)) != len(lst):
                return True
    except Exception:
        return False
    return False

def _codewords_has_self_reference(val) -> bool:
    try:
        v = val or {}
        tw = None
        if isinstance(v, dict):
            for k in ("target","target_word","word","answer"):
                if v.get(k) is not None:
                    tw = _norm_label(v.get(k))
                    break
            if not tw:
                return False
            icons = []
            for k in ("clue_icons","clues","icons","clue_words"):
                if isinstance(v.get(k), list):
                    icons = v.get(k) or []
                    break
            for it in icons:
                if isinstance(it, str):
                    if _norm_label(it) == tw:
                        return True
                elif isinstance(it, dict):
                    for kk in ("word","label","icon","name","text"):
                        if it.get(kk) is not None and _norm_label(it.get(kk)) == tw:
                            return True
    except Exception:
        return False
    return False

def _pairs_have_identity(val) -> bool:
    try:
        v = val or {}
        if isinstance(v, dict) and isinstance(v.get("pairs"), list):
            for p in (v.get("pairs") or []):
                if isinstance(p, list) and len(p) >= 2:
                    if _norm_label(p[0]) == _norm_label(p[1]):
                        return True
                elif isinstance(p, dict):
                    l = p.get("left")
                    r = p.get("right")
                    if _norm_label(l) == _norm_label(r) and (l is not None and r is not None):
                        return True
    except Exception:
        return False
    return False

def _vs_build_items(slug: str, finals: dict, needs: dict) -> dict:
    items = []
    fields = [
        "word_search_words","starting_sight_words","sequence_order","sorting_categories",
        "sequencing_strips_verbs","adapted_book_sentences","wh_questions","yes_no_questions",
        "aac_fringe_vocab","inferencing_questions",
        "rhyme_sets","matching_pairs","bingo_card_sets","code_words_puzzles","syllable_breaks",
    ]
    def _flags_for(activity: str, val) -> list:
        fl = []
        try:
            if activity == "matching_pairs":
                st = str((val or {}).get("trivial_identity_check", "")).lower()
                if st and st != "pass":
                    fl.append(f"trivial_identity_check:{st}")
                # Deterministic post-check
                if _pairs_have_identity(val):
                    fl.append("trivial_identity_check:fail")
            elif activity == "bingo_card_sets":
                st = str((val or {}).get("duplicate_check", "")).lower()
                if st and st != "pass":
                    fl.append(f"duplicate_check:{st}")
                # Deterministic post-check
                if _bingo_has_duplicates(val):
                    fl.append("duplicate_icons:fail")
            elif activity == "code_words_puzzles":
                st = str((val or {}).get("self_reference_check", "")).lower()
                if st and st != "pass":
                    fl.append(f"self_reference_check:{st}")
                # Deterministic post-check
                if _codewords_has_self_reference(val):
                    fl.append("self_reference_check:fail")
            elif activity == "rhyme_sets":
                m = val.get("icon_available", {}) if isinstance(val, dict) else {}
                if isinstance(m, dict) and any(v is False for v in m.values()):
                    fl.append("icon_available:false")
                # Deterministic: verify icons resolvable for words
                try:
                    words = []
                    if isinstance(val, dict):
                        for k in ("words","set","items","list"):
                            if isinstance(val.get(k), list):
                                for x in (val.get(k) or []):
                                    if isinstance(x, str):
                                        words.append(x)
                                    elif isinstance(x, dict):
                                        for kk in ("word","label","name","text"):
                                            if x.get(kk) is not None:
                                                words.append(str(x.get(kk)))
                                                break
                        if isinstance(val.get("pairs"), list):
                            for p in (val.get("pairs") or []):
                                if isinstance(p, list):
                                    for x in p:
                                        if isinstance(x, str):
                                            words.append(x)
                                elif isinstance(p, dict):
                                    for kk in ("left","right"):
                                        if p.get(kk) is not None:
                                            words.append(str(p.get(kk)))
                    miss = False
                    for w in words:
                        try:
                            rp = qa_logic._resolve_icon_path_for_word(slug, w)  # type: ignore[attr-defined]
                        except Exception:
                            rp = None
                        if not rp:
                            miss = True; break
                    if miss:
                        fl.append("icon_available:false")
                except Exception:
                    pass
            elif activity == "syllable_breaks":
                conf = str((val or {}).get("confidence", "")).lower()
                if conf and conf != "high":
                    fl.append(f"confidence:{conf}")
        except Exception:
            pass
        return fl
    bv_final = (finals or {}).get("book_vocab", {})
    bv_need = (needs or {}).get("book_vocab", {})
    for f in fields:
        arr_f = list(bv_final.get(f) or [])
        for i, v in enumerate(arr_f):
            gid = f"{f}:f:{i}"
            grounded = (v.get("grounded") if isinstance(v, dict) else None)
            it = {
                "id": gid,
                "activity": f,
                "value": v,
                "grounded": grounded if grounded is not None else True,
                "confidence": ("high" if grounded else "low") if grounded is not None else "high",
                "guardrail_flags": _flags_for(f, v),
                "review_status": "pending",
                "human_amended": False,
            }
            items.append(it)
        arr_n = list(bv_need.get(f) or [])
        for i, v in enumerate(arr_n):
            gid = f"{f}:n:{i}"
            grounded = (v.get("grounded") if isinstance(v, dict) else None)
            fl = ["needs_review:low_confidence_or_uncited"] + _flags_for(f, v)
            it = {
                "id": gid,
                "activity": f,
                "value": v,
                "grounded": grounded if grounded is not None else False,
                "confidence": ("low"),
                "guardrail_flags": fl,
                "review_status": "pending",
                "human_amended": False,
            }
            items.append(it)
    return {
        "slug": slug,
        "created_at": _dt.datetime.utcnow().isoformat() + "Z",
        "items": items,
        "meta": {"source": "ai_prep_runner"},
    }

def _vs_commit_to_vocab(slug: str, vs: dict) -> dict:
    tv = qa_logic.load_theme_vocab(slug)
    items = list((vs or {}).get("items") or [])
    chosen = [it for it in items if str(it.get("review_status", "")).lower() in ("approved", "amended")]
    grouped = {}
    for it in chosen:
        a = str(it.get("activity", "")).strip()
        if not a:
            continue
        grouped.setdefault(a, []).append(it)
    def _uniq(seq):
        out = []
        seen = set()
        for x in seq:
            key = json.dumps(x, sort_keys=True) if isinstance(x, (dict, list)) else str(x)
            if key not in seen:
                seen.add(key)
                out.append(x)
        return out
    for a, arr in grouped.items():
        vals = []
        for it in arr:
            v = it.get("value")
            if isinstance(v, dict) and "text" in v and len(v.keys()) == 1:
                vals.append(v.get("text"))
            else:
                vals.append(v)
        if a == "sorting_categories":
            base = tv.get(a) if isinstance(tv.get(a), dict) else {}
            merged = dict(base)
            for v in vals:
                if isinstance(v, dict):
                    for k, lst in v.items():
                        cur = list(merged.get(k) or [])
                        if isinstance(lst, list):
                            cur.extend(lst)
                        merged[k] = list(dict.fromkeys(cur))
            tv[a] = merged
        else:
            base = tv.get(a)
            if not isinstance(base, list):
                base = []
            vals2 = base + vals
            tv[a] = _uniq(vals2)
    bp = _book_vocab_path(slug)
    bp.parent.mkdir(parents=True, exist_ok=True)
    bp.write_text(json.dumps(tv, ensure_ascii=False, indent=2), encoding="utf-8")
    # Auto-assign icons for all relevant activities, not just aac_fringe_vocab
    words_set = set()
    try:
        if isinstance(tv.get("aac_fringe_vocab"), list):
            for w in tv.get("aac_fringe_vocab"):
                try:
                    words_set.add(str(w))
                except Exception:
                    pass
    except Exception:
        pass
    # rhyme_sets: collect all string-like members
    try:
        for it in (tv.get("rhyme_sets") or []):
            if isinstance(it, dict):
                for k in ("words","set","items","list"):
                    if isinstance(it.get(k), list):
                        for x in (it.get(k) or []):
                            if isinstance(x, str):
                                words_set.add(x)
                            elif isinstance(x, dict):
                                for kk in ("word","label","name","text"):
                                    if x.get(kk) is not None:
                                        words_set.add(str(x.get(kk)))
                                        break
                if isinstance(it.get("pairs"), list):
                    for p in (it.get("pairs") or []):
                        if isinstance(p, list):
                            for x in p:
                                if isinstance(x, str):
                                    words_set.add(x)
                        elif isinstance(p, dict):
                            for kk in ("left","right"):
                                if p.get(kk) is not None:
                                    words_set.add(str(p.get(kk)))
            elif isinstance(it, list):
                for x in it:
                    if isinstance(x, str):
                        words_set.add(x)
    except Exception:
        pass
    # matching_pairs: collect both sides
    try:
        for it in (tv.get("matching_pairs") or []):
            if isinstance(it, dict) and isinstance(it.get("pairs"), list):
                for p in (it.get("pairs") or []):
                    if isinstance(p, list):
                        for x in p[:2]:
                            if isinstance(x, str):
                                words_set.add(x)
                    elif isinstance(p, dict):
                        for kk in ("left","right"):
                            if p.get(kk) is not None:
                                words_set.add(str(p.get(kk)))
    except Exception:
        pass
    # bingo_card_sets: collect all icon labels on cards (use original labels where possible)
    try:
        for it in (tv.get("bingo_card_sets") or []):
            rows = _bingo_extract_card_originals(it) or _bingo_extract_card_labels(it)
            for card in rows:
                for lab in card:
                    if lab:
                        try:
                            words_set.add(str(lab))
                        except Exception:
                            pass
    except Exception:
        pass
    # code_words_puzzles: collect all clue icons (not target word)
    try:
        for it in (tv.get("code_words_puzzles") or []):
            if isinstance(it, dict):
                arr = None
                for k in ("clue_icons","clues","icons","clue_words"):
                    if isinstance(it.get(k), list):
                        arr = it.get(k) or []
                        break
                for x in (arr or []):
                    if isinstance(x, str):
                        words_set.add(x)
                    elif isinstance(x, dict):
                        for kk in ("word","label","name","text"):
                            if x.get(kk) is not None:
                                words_set.add(str(x.get(kk)))
                                break
    except Exception:
        pass
    words = list(words_set)
    qa = qa_logic.load_qa_log()
    b = qa.setdefault(slug, {"words": {}, "completed": False})
    for w in words:
        try:
            rp = qa_logic._resolve_icon_path_for_word(slug, w)  # type: ignore[attr-defined]
        except Exception:
            rp = None
        st = b["words"].setdefault(w, {})
        if rp:
            st["status"] = "kept"
            st["path"] = str(rp)
        else:
            st["status"] = "missing"
    qa_logic.save_qa_log(qa)
    dest = ASSETS / "themes" / slug / "activity_images"
    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    updated = 0
    for w, info in b["words"].items():
        try:
            if info.get("status") not in ("replaced", "keep", "kept"):
                continue
            src = Path(str(info.get("path", "")))
            if (not src.exists() or not _file_under_base(src)) and info.get("status") in ("keep", "kept"):
                try:
                    rp = qa_logic._resolve_icon_path_for_word(slug, w)  # type: ignore[attr-defined]
                except Exception:
                    rp = None
                if rp:
                    src = Path(str(rp))
            if not src.exists() or not _file_under_base(src):
                continue
            try:
                fname = qa_logic._sanitized_png_name(w)  # type: ignore
                if not isinstance(fname, str) or not fname.endswith(".png"):
                    raise Exception("bad fname")
            except Exception:
                fname = re.sub(r"[^a-z0-9]+", "_", str(w).lower()).strip("_") + ".png"
            dst = dest / fname
            existed = dst.exists()
            shutil.copy2(src, dst)
            if not existed:
                copied += 1
            info["path"] = str(dst)
            updated += 1
        except Exception:
            continue
    if updated:
        qa_logic.save_qa_log(qa)
    return {"updated": True, "copied": copied, "updated_files": updated}

def _html_vocab_suggestions() -> str:
    return """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Icon Labeler — Vocab Suggestions</title>
<style>body{font-family:Segoe UI,system-ui,Arial;margin:18px;color:#0D2545;background:#fafafa}h1{color:#31A8A0;margin:0 0 8px 0}.row{display:flex;gap:10px;align-items:center;margin:8px 0}select,input,button,textarea{font:inherit;padding:6px 10px}select#book{min-width:380px;max-width:70vw}.card{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin:8px 0}.badge{display:inline-block;padding:2px 6px;border-radius:999px;border:1px solid #cbd5e1;margin:0 4px;font-size:12px}.warn{background:#fff1f2;border-color:#fecdd3}.ok{background:#e6fffa;border-color:#99f6e4}.muted{color:#64748b;font-size:12px}</style></head>
<body><h1>Vocab Suggestions</h1>
<div class='row'><label>Book:&nbsp;</label><select id='book'></select><button id='load'>Load</button><button id='gen'>Suggest vocab & content</button><button id='commit'>Commit approved</button><span id='status' class='muted'></span></div>
<div id='content'></div>
<script>
const $=s=>document.querySelector(s);
async function j(url,opts){const r=await fetch(url,opts);if(!r.ok)throw new Error(await r.text());return await r.json()}
async function loadBooks(){ const b=$('#book'); b.innerHTML=''; let r; try{ r=await j('/api/books'); }catch(e){ return; } const arr=Array.isArray(r.books)? r.books: []; arr.forEach(x=>{ const o=document.createElement('option'); o.value=x.slug; o.textContent=x.title||x.slug; b.appendChild(o); }); try{ const params=new URLSearchParams(location.search); const want=(params.get('book')||'').trim().toLowerCase(); if(want){ const hit=arr.find(x=>String(x.slug||'').toLowerCase()===want); if(hit){ b.value=hit.slug; } } }catch(_){ } if(arr.length && !b.value){ b.value=arr[0].slug } }
function esc(s){return String(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function groupByAct(items){ const g={}; (items||[]).forEach(it=>{ const a=String(it.activity||''); (g[a]=g[a]||[]).push(it); }); return g; }
async function load(){ const bk=$('#book').value; if(!bk) return; $('#status').textContent='Loading…'; let r; try{ r=await j('/api/vs_list?book='+encodeURIComponent(bk)); }catch(e){ $('#status').textContent='Failed'; return; } $('#status').textContent=''; const items=(r.items||[]); const g=groupByAct(items); const cont=$('#content'); cont.innerHTML=''; Object.keys(g).forEach(act=>{ const arr=g[act]; const card=document.createElement('div'); card.className='card'; card.innerHTML = `<div class='row' style='justify-content:space-between'><div><b>${esc(act)}</b> <span class='muted'>${arr.length}</span></div><div><button data-act='accept_clean' data-name='${esc(act)}'>Accept unflagged</button></div></div>`; arr.forEach(it=>{ const fl=Array.isArray(it.guardrail_flags)? it.guardrail_flags: []; const flHtml=fl.map(x=>`<span class='badge warn'>${esc(x)}</span>`).join(''); const val=(typeof it.value==='string')? it.value: JSON.stringify(it.value); const row=document.createElement('div'); row.className='row'; row.style.alignItems='flex-start'; row.innerHTML = `<div style='flex:1;white-space:pre-wrap'>${esc(val)}</div><div>${flHtml||''}</div><div><button data-do='approve' data-id='${esc(it.id)}'>Accept</button><button data-do='delete' data-id='${esc(it.id)}' style='margin-left:6px'>Delete</button><button data-do='amend' data-id='${esc(it.id)}' style='margin-left:6px'>Amend…</button></div>`; card.appendChild(row); }); cont.appendChild(card); }); cont.addEventListener('click', async (e)=>{ const t=e.target; if(!t||!t.getAttribute) return; const did=t.getAttribute('data-do'); const id=t.getAttribute('data-id'); const act=t.getAttribute('data-act'); if(did && id){ if(did==='amend'){ const v=prompt('New value (string or JSON)'); if(v===null) return; let payload=v; try{ payload=JSON.parse(v); }catch(_){ } try{ await j('/api/vs_save',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: $('#book').value, id, review_status:'amended', amended_value: payload})}); }catch(_){ alert('Failed'); } await load(); return; } const st = (did==='approve')?'approved':'deleted'; try{ await j('/api/vs_save',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: $('#book').value, id, review_status: st})}); }catch(_){ alert('Failed'); } await load(); }
  if(act==='accept_clean'){ const name=t.getAttribute('data-name'); const arr=items.filter(x=>(x.activity===name)&&(!Array.isArray(x.guardrail_flags)||x.guardrail_flags.length===0)); for(const it of arr){ try{ await j('/api/vs_save',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({book: $('#book').value, id: it.id, review_status:'approved'})}); }catch(_){ } } await load(); }
 }); }
$('#load').onclick=load;
$('#gen').onclick=async()=>{ const bk=$('#book').value; if(!bk){ alert('Pick a book'); return; } $('#status').textContent='Starting…'; let jid=null; try{ const r=await j('/api/vs_generate',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({slug: bk})}); if(!r.ok){ alert(r.error||'Failed'); $('#status').textContent=''; return; } jid=r.id||null; }catch(_){ alert('Failed'); $('#status').textContent=''; return; } if(!jid){ $('#status').textContent=''; await load(); return; } let stop=false; async function poll(){ if(stop) return; try{ const s=await j('/api/vocab_job_status/'+jid); const done=Number(s.done||0), total=Number(s.total||1); const st=String(s.status||''); $('#status').textContent = (st==='done')? 'Done' : ('Generating… '+done+'/'+total); if(st==='done'){ stop=true; await load(); $('#status').textContent=''; return; } }catch(_){ } setTimeout(poll, 1500); } poll(); };
$('#commit').onclick=async()=>{ const bk=$('#book').value; if(!bk){ alert('Pick a book'); return; } $('#status').textContent='Committing…'; try{ const r=await j('/api/vs_commit',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({slug: bk})}); }catch(_){ alert('Failed'); } $('#status').textContent=''; };
loadBooks().then(async()=>{ await load(); try{ const p=new URLSearchParams(location.search); if(p.get('autogen')==='1'){ document.getElementById('gen').click(); } }catch(_){ } }).catch(()=>{});
</script></body></html>"""

class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        # Default implementation writes to sys.stderr, which is None under pythonw.exe
        # and would abort every request before a response is sent.
        return

    def do_GET(self):  # noqa: N802
        try:
            parsed = _u.urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                html = _html_index()
                data = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if parsed.path.startswith("/api/vocab_job_status/"):
                jid = parsed.path.split("/api/vocab_job_status/")[-1].strip()
                st = VOCAB_JOBS.get(jid)
                if not st:
                    return _ok_json(self, {"status": "unknown", "id": jid})
                return _ok_json(self, dict(st, id=jid))
            if parsed.path == "/guides":
                html = _html_guides()
                # Inject lightweight event bindings for Reload and Apply buttons
                html += (
                    "<script>"
                    "window.addEventListener('load',function(){try{"
                    "var reloadBtn=document.getElementById('reload');"
                    "if(reloadBtn){reloadBtn.onclick=function(){try{if(typeof load==='function'){load();}}catch(e){}}}"
                    "var applyBtn=document.getElementById('apply');"
                    "if(applyBtn){applyBtn.onclick=async function(){try{var b=(new URLSearchParams(location.search).get('book')||'').trim();if(!b){alert('Missing ?book=');return;}var r=await fetch('/api/apply',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({book:b})});var j=await r.json();if(!r.ok){alert('Apply failed');return;}alert('Applied: '+(j.copied||0)+' copied, '+(j.updated||0)+' updated.');}catch(e){alert('Apply failed');}}}"
                    "// Normalize items shape before rendering (support string[] or {word,...}[])\n"
                    "try{var rl=window.renderList;if(typeof rl==='function'){window.renderList=function(){try{if(Array.isArray(window.items)){window.items=window.items.map(function(it){return (typeof it==='string')?{word:it,current_path:''}:it;});}}catch(_){ } return rl.apply(this, arguments);};}}catch(_){ }"
                    "}catch(e){}});"
                    "</script>"
                )
                data = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            pp = (parsed.path or "").strip()
            if pp.lower().rstrip("/") == "/pdf":
                html = _html_pdf()
                data = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if pp.lower().rstrip("/") == "/vocab":
                if _vrb is None:
                    return _text(self, "Vocab Review unavailable: vocab_review_bridge.py not loaded", 503)
                html = _html_vocab()
                data = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if pp.lower().rstrip("/") == "/vocab_suggestions":
                html = _html_vocab_suggestions()
                data = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if parsed.path == "/api/books":
                try:
                    vocab = qa_logic.load_vocab()
                except Exception:
                    vocab = {}
                books = []
                # Prefer authoritative list from qa_logic (merges themes + vocab)
                slugs = []
                try:
                    slugs = list(qa_logic.get_all_book_keys())
                except Exception:
                    slugs = []
                # Fallback to filesystem scan if helper unavailable
                if not slugs:
                    try:
                        themes = ASSETS / "themes"
                        if themes.exists():
                            for p in sorted(themes.iterdir()):
                                try:
                                    if p.is_dir() and not p.name.startswith(('.','_')):
                                        has_assets = any((p / sub).exists() for sub in ("activity_images", "icons", "real_images", "aac_boards"))
                                        has_vocab = (p / "book_vocab.json").exists() or (p / "config" / "book_vocab.json").exists()
                                        if has_assets or has_vocab:
                                            slugs.append(p.name)
                                except OSError:
                                    # Unreadable folder (e.g. disk CRC error): skip it, keep listing the rest
                                    continue
                    except Exception:
                        pass
                for slug in slugs:
                    title = slug.replace("_", " ").title()
                    try:
                        vt = str((vocab.get(slug, {}) or {}).get("title", "")).strip()
                        if vt:
                            title = vt
                    except Exception:
                        pass
                    books.append({"slug": slug, "title": title})
                try:
                    books.sort(key=lambda x: str((x.get("title") or x.get("slug") or "")).lower())
                except Exception:
                    pass
                return _ok_json(self, {"books": books})
            if parsed.path == "/api/vs_list":
                q = _u.parse_qs(parsed.query)
                book = (q.get("book", [""])[0] or "").strip()
                if not book:
                    return _ok_json(self, {"ok": False, "error": "Missing 'book'"}, code=400)
                path = _vs_path(book)
                vs = _json_load(path) or {"slug": book, "items": []}
                items = list((vs or {}).get("items") or [])
                try:
                    for it in items:
                        if not isinstance(it.get("guardrail_flags"), list):
                            it["guardrail_flags"] = []
                except Exception:
                    pass
                return _ok_json(self, {"slug": book, "items": items})
            if parsed.path == "/api/ping":
                return _ok_json(self, {"ok": True})
            if parsed.path == "/api/pdf_save_to_theme":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                tile_ids = obj.get("tile_ids") or []
                labels_in = obj.get("labels") or []
                also_library = bool(obj.get("also_library", False))
                tile_sources = obj.get("tile_sources") or {}
                if not book or not isinstance(tile_ids, list):
                    return _text(self, "Missing fields", 400)
                dest = ASSETS / "themes" / book / "activity_images"
                try:
                    dest.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                # Prepare library indices if needed
                if also_library:
                    prov = _load_provenance()
                    labidx = _load_label_index()
                else:
                    prov = {}
                    labidx = {}
                saved_theme = dup_theme = auto_named = 0
                saved_lib = dup_lib = 0
                auto_seq = 1
                # Normalize input labels
                lab_list = []
                try:
                    for s in labels_in:
                        lab = _sanitize_label(str(s or ""))
                        if lab:
                            lab_list.append(lab)
                except Exception:
                    lab_list = []
                for idx, tid in enumerate(tile_ids):
                    try:
                        meta = PDF_STATE.get("tiles", {}).get(str(tid))
                        if not meta:
                            continue
                        src_img = Path(str(meta.get("path", "")))
                        if not src_img.exists():
                            continue
                        # Choose label or auto-name
                        name = lab_list[idx] if idx < len(lab_list) else ""
                        if not name:
                            name = f"icon_{auto_seq}"
                            auto_seq += 1
                            auto_named += 1
                        # Theme save with de-dup suffixing
                        dst = dest / f"{name}.png"
                        if dst.exists():
                            k = 2
                            while True:
                                alt = dest / f"{name}_{k}.png"
                                if not alt.exists():
                                    dst = alt
                                    dup_theme += 1
                                    break
                                k += 1
                        shutil.copy2(src_img, dst)
                        saved_theme += 1
                        # Optional: also save to library
                        if also_library:
                            bucket = _alpha_bucket_for(name)
                            out_dir = SYMBOLS_ALPHA_ROOT / bucket
                            try:
                                out_dir.mkdir(parents=True, exist_ok=True)
                            except Exception:
                                pass
                            lib_dst = out_dir / f"{name}.png"
                            if lib_dst.exists():
                                k = 2
                                while True:
                                    alt = out_dir / f"{name}_{k}.png"
                                    if not alt.exists():
                                        lib_dst = alt
                                        dup_lib += 1
                                        break
                                    k += 1
                            shutil.copy2(src_img, lib_dst)
                            saved_lib += 1
                            # Update indices
                            try:
                                bsrc = str(tile_sources.get(tid, "")).strip()
                            except Exception:
                                bsrc = ""
                            try:
                                prov[str(lib_dst)] = {"book": bsrc} if bsrc else {"book": ""}
                            except Exception:
                                prov[str(lib_dst)] = bsrc or ""
                            labidx[str(lib_dst)] = name
                    except Exception:
                        continue
                # Persist indices if library was touched
                if also_library:
                    try:
                        _save_provenance(prov)
                    except Exception:
                        pass
                    try:
                        _save_label_index(labidx)
                    except Exception:
                        pass
                return _ok_json(self, {
                    "saved_theme": saved_theme,
                    "dup_theme": dup_theme,
                    "auto_named": auto_named,
                    "saved_library": saved_lib,
                    "dup_library": dup_lib,
                })
            if parsed.path == "/api/diag":
                try:
                    themes = ASSETS / "themes"
                    di = {
                        "base": str(BASE),
                        "assets": str(ASSETS),
                        "themes_path": str(themes),
                        "themes_exists": themes.exists(),
                        "themes_count": sum(1 for p in themes.iterdir() if p.is_dir()) if themes.exists() else 0,
                    }
                except Exception:
                    di = {"base": str(BASE), "assets": str(ASSETS)}
                return _ok_json(self, di)
            if parsed.path == "/api/vocab_queue":
                if _vrb is None:
                    return _ok_json(self, {"ok": False, "error": "Vocab bridge not available"}, code=503)
                try:
                    pending = _vrb.list_pending_reviews()  # type: ignore
                except Exception:
                    pending = []
                try:
                    missing = _vrb.list_missing_vocab()  # type: ignore
                except Exception:
                    missing = []
                return _ok_json(self, {"pending": pending, "missing": missing})
            if parsed.path == "/api/settings":
                s = _pdf_load_settings()
                # Inject source folder and any per-PDF profiles if present
                try:
                    s["pdf_source"] = str(PDF_SOURCE_FOLDER)
                except Exception:
                    s["pdf_source"] = ""
                try:
                    if not isinstance(s.get("profiles"), dict):
                        s["profiles"] = {}
                except Exception:
                    s["profiles"] = {}
                return _ok_json(self, s)
            if parsed.path == "/api/source_folder":
                return _ok_json(self, {"path": str(PDF_SOURCE_FOLDER)})
            if parsed.path == "/api/pdfs":
                try:
                    root = PDF_SOURCE_FOLDER
                    pdfs = []
                    if root.exists():
                        for p in sorted(root.rglob("*.pdf")):
                            # cap the list to avoid huge payloads
                            pdfs.append(str(p.relative_to(root)))
                            if len(pdfs) >= 500:
                                break
                    return _ok_json(self, {"pdfs": pdfs, "extracted": _load_extracted_log()})
                except Exception as e:
                    return _ok_json(self, {"error": f"Failed to list PDFs: {e}"}, code=500)
            if parsed.path == "/api/pdf_info":
                if fitz is None:
                    return _ok_json(self, {"error": "PyMuPDF not installed"}, code=500)
                q = _u.parse_qs(parsed.query)
                name = (q.get("pdf", [""])[0] or "").strip()
                if not name:
                    return _ok_json(self, {"error": "Missing 'pdf'"}, code=400)
                pdf_path = (PDF_SOURCE_FOLDER / name).resolve()
                if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
                    return _ok_json(self, {"error": "PDF not found"}, code=404)
                try:
                    with fitz.open(str(pdf_path)) as doc:
                        return _ok_json(self, {"page_count": doc.page_count})
                except Exception as e:
                    return _ok_json(self, {"error": f"Failed to open PDF: {e}"}, code=500)
            if parsed.path == "/api/preview":
                if fitz is None or Image is None or ImageDraw is None:
                    return _text(self, "Preview unavailable (missing dependencies)", 500)
                q = _u.parse_qs(parsed.query)
                name = (q.get("pdf", [""])[0] or "").strip()
                rows = int((q.get("rows", ["6"])[0] or "6"))
                cols = int((q.get("cols", ["6"])[0] or "6"))
                page_idx = int((q.get("page", ["0"])[0] or "0"))
                col_gap_pct = float((q.get("col_gap_pct", ["0"]) or ["0"])[0] or 0)
                row_gap_pct = float((q.get("row_gap_pct", ["0"]) or ["0"])[0] or 0)
                try:
                    corners = json.loads((q.get("corners", [""])[0] or ""))
                except Exception:
                    corners = [[0.03, 0.03], [0.97, 0.03], [0.97, 0.82], [0.03, 0.82]]
                if not name:
                    return _text(self, "Missing pdf", 400)
                pdf_path = (PDF_SOURCE_FOLDER / name).resolve()
                if not pdf_path.exists():
                    return _text(self, "Not found", 404)
                try:
                    with fitz.open(str(pdf_path)) as doc:
                        page_idx = max(0, min(page_idx, doc.page_count - 1))
                        p = doc.load_page(page_idx)
                        pm = p.get_pixmap(alpha=False)
                        img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
                except Exception:
                    return _text(self, "Failed to render", 500)
                # Crop with quad
                try:
                    crop = _crop_quad_to_rect(img)(corners)
                except Exception:
                    crop = img
                W, H = crop.size
                draw = ImageDraw.Draw(crop, "RGBA")
                # Compute grid lines
                gap_w = (max(0, cols - 1)) * (col_gap_pct / 100.0) * W
                gap_h = (max(0, rows - 1)) * (row_gap_pct / 100.0) * H
                cw = max(1, (W - gap_w) / max(1, cols))
                ch = max(1, (H - gap_h) / max(1, rows))
                # Draw outer border
                draw.rectangle([0, 0, W - 1, H - 1], outline=(220, 64, 64, 220), width=3)
                # Draw vertical cell boundaries and gap spans (orange overlay)
                x = 0.0
                for i in range(cols - 1):
                    x += cw
                    gx0 = x
                    gx1 = gx0 + (col_gap_pct / 100.0) * W
                    draw.rectangle([gx0, 0, gx1, H], outline=(245, 158, 11, 200), width=1, fill=(245, 158, 11, 40))
                    x = gx1
                # Draw horizontal cell boundaries and gap spans
                y = 0.0
                for j in range(rows - 1):
                    y += ch
                    gy0 = y
                    gy1 = gy0 + (row_gap_pct / 100.0) * H
                    draw.rectangle([0, gy0, W, gy1], outline=(245, 158, 11, 200), width=1, fill=(245, 158, 11, 40))
                    y = gy1
                # Return image
                buf = io.BytesIO()
                crop.save(buf, format="PNG")
                data = buf.getvalue()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if parsed.path.startswith("/api/tile/"):
                tid = parsed.path.split("/api/tile/")[-1].strip()
                meta = PDF_STATE.get("tiles", {}).get(tid)
                if not meta:
                    return _text(self, "Not found", 404)
                try:
                    p = Path(meta.get("path", ""))
                except Exception:
                    p = None
                if not p or not p.exists():
                    return _text(self, "Not found", 404)
                data = p.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if parsed.path == "/api/meta":
                q = _u.parse_qs(parsed.query)
                book = (q.get("book", [""])[0] or "").strip()
                if not book:
                    return _ok_json(self, {"ok": False, "error": "Missing 'book'"}, code=400)
                theme = ASSETS / "themes" / book
                meta_path = theme / "book_meta.json"
                meta = {}
                try:
                    if meta_path.exists():
                        with meta_path.open("r", encoding="utf-8") as f:
                            meta = json.load(f) or {}
                except Exception:
                    meta = {}
                hero = str(meta.get("hero", "")) if isinstance(meta, dict) else ""
                cover = str(meta.get("cover", "")) if isinstance(meta, dict) else ""
                overview = str(meta.get("overview", "")) if isinstance(meta, dict) else ""
                return _ok_json(self, {"hero": hero, "cover": cover, "overview": overview})
            if parsed.path == "/api/list":
                q = _u.parse_qs(parsed.query)
                book = (q.get("book", [""])[0] or "").strip()
                items = []
                if book:
                    # Prefer the comprehensive candidate set used by qa_logic
                    try:
                        cands = qa_logic._candidate_png_dirs(book)  # type: ignore[attr-defined]
                    except Exception:
                        cands = []
                    # Fallback to prior local/global lists if helper unavailable
                    if not cands:
                        theme = ASSETS / "themes" / book
                        cands = [
                            theme / "activity_images",
                            theme / "icons_colored",
                            theme / "icons",
                            theme / "png_raw",
                            theme / "real_images",
                            theme / "icons_ai",
                            ASSETS / "symbols" / "png",
                            ASSETS / "global",
                            ASSETS / "png_raw",
                            BASE / "Studioforge" / "assets" / "symbols" / "png",
                            BASE / "Studioforge" / "assets" / "global",
                            BASE / "Studioforge" / "assets" / "png_raw",
                        ]
                    # Ensure theme-level icons_ai is included even if qa_logic doesn't list it
                    try:
                        ai_dir = ASSETS / "themes" / book / "icons_ai"
                        if ai_dir.exists() and ai_dir not in cands:
                            cands.insert(0, ai_dir)
                    except Exception:
                        pass
                    seen = set()
                    for p in _iter_pngs(cands):
                        try:
                            stem = p.stem
                            if p.name in seen:
                                continue
                            seen.add(p.name)
                            items.append({"path": str(p), "name": stem})
                            # Cap to a reasonable number to keep UI responsive
                            if len(items) >= 600:
                                break
                        except Exception:
                            continue
                try:
                    items.sort(key=lambda d: str(d.get("name", "")).lower())
                except Exception:
                    pass
                return _ok_json(self, {"items": items})
            if parsed.path.startswith("/api/vocab_review/"):
                if _vrb is None:
                    return _ok_json(self, {"ok": False, "error": "Vocab bridge not available"}, code=503)
                slug = parsed.path.split("/api/vocab_review/")[-1].strip()
                if not slug:
                    return _ok_json(self, {"ok": False, "error": "Missing slug"}, code=400)
                try:
                    detail = _vrb.get_review_detail(slug)  # type: ignore
                except Exception as e:
                    return _ok_json(self, {"ok": False, "error": str(e)}, code=500)
                if not detail:
                    return _ok_json(self, {"ok": False, "error": "Not found"}, code=404)
                return _ok_json(self, detail)
            if parsed.path == "/api/ai_preview":
                q = _u.parse_qs(parsed.query)
                book = (q.get("book", [""])[0] or "").strip()
                if not book:
                    return _ok_json(self, {"ok": False, "error": "Missing 'book'"}, code=400)
                backend = os.environ.get("STUDIOFORGE_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
                url = f"{backend}/api/vocab/{book}/preview"
                try:
                    req = _urlreq.Request(url=url, headers={"Accept": "application/json"}, method="GET")
                    with _urlreq.urlopen(req, timeout=10) as resp:
                        status = resp.getcode()
                        txt = resp.read().decode("utf-8", errors="ignore")
                    try:
                        data = json.loads(txt)
                    except Exception:
                        data = {"ok": False, "error": "Backend returned non-JSON"}
                    if status != 200:
                        if isinstance(data, dict):
                            data.setdefault("ok", False)
                            data.setdefault("error", f"Backend responded {status}")
                        return _ok_json(self, data)
                    return _ok_json(self, data)
                except Exception:
                    return _ok_json(self, {"ok": False, "error": "Backend not running"})

            if parsed.path == "/api/required":
                q = _u.parse_qs(parsed.query)
                book = (q.get("book", [""])[0] or "").strip()
                if not book:
                    return _ok_json(self, {"ok": False, "error": "Missing 'book'"}, code=400)
                # Load full items from qa_logic so UI can show auto-identified icons and states
                try:
                    include_core = False
                    try:
                        include_core = bool(int((q.get("core", ["0"])[0] or "0")))
                    except Exception:
                        include_core = False
                    full = qa_logic.get_icons_for_book(book, include_core=include_core, include_context=False)
                except Exception:
                    full = []
                # Filter out words explicitly excluded for activities in the QA log
                excluded = []
                try:
                    qa = qa_logic.load_qa_log()
                    book_ent = qa.get(book, {}) if isinstance(qa, dict) else {}
                    wmap = book_ent.get("words", {}) if isinstance(book_ent, dict) else {}
                    excluded = [w for w, info in wmap.items() if isinstance(info, dict) and info.get("exclude_activities")]
                except Exception:
                    excluded = []
                if excluded and isinstance(full, list):
                    try:
                        ex = set(excluded)
                        full = [it for it in full if isinstance(it, dict) and str(it.get("word", "")).strip() not in ex]
                    except Exception:
                        pass
                return _ok_json(self, {"items": full, "excluded": excluded})
            if parsed.path == "/api/theme_items":
                q = _u.parse_qs(parsed.query)
                book = (q.get("book", [""])[0] or "").strip()
                if not book:
                    return _ok_json(self, {"ok": False, "error": "Missing 'book'"}, code=400)
                items = []
                try:
                    d = ASSETS / "themes" / book / "activity_images"
                    if d.exists():
                        for p in sorted(d.glob("*.png")):
                            try:
                                if not _file_under_base(p):
                                    continue
                                items.append({"name": p.stem, "path": str(p)})
                            except Exception:
                                continue
                except Exception:
                    items = []
                return _ok_json(self, {"items": items})
            if parsed.path == "/api/suggest":
                q = _u.parse_qs(parsed.query)
                book = (q.get("book", [""])[0] or "").strip()
                word = (q.get("word", [""])[0] or "").strip()
                if not book or not word:
                    return _ok_json(self, {"ok": False, "error": "Missing 'book' or 'word'"}, code=400)
                try:
                    try:
                        k = int((q.get("k", ["8"])[0] or "8"))
                    except Exception:
                        k = 8
                    # Build candidate search terms from theme vocab icon_search_terms + literal word
                    terms = []
                    try:
                        tv = qa_logic.load_theme_vocab(book)
                        st = (tv.get("icon_search_terms", {}) or {}).get(word)
                        if isinstance(st, list):
                            for x in st:
                                xs = str(x).strip()
                                if xs:
                                    terms.append(xs)
                        elif isinstance(st, str) and st.strip():
                            terms.append(st.strip())
                    except Exception:
                        pass
                    if word and word.strip():
                        terms.append(word.strip())
                    # Dedup terms while preserving order
                    seen_t = set()
                    terms2 = []
                    for t in terms:
                        tl = t.lower()
                        if tl and tl not in seen_t:
                            seen_t.add(tl)
                            terms2.append(t)
                    terms = terms2 or [word]
                    # Query across terms and combine results
                    agg = []
                    seen_paths = set()
                    for t in terms:
                        try:
                            cand = qa_logic.search_png_library(t, book_key=book, top_k=max(3, k))
                        except Exception:
                            cand = []
                        for it in cand:
                            p = str(it.get("path", ""))
                            if not p or p in seen_paths:
                                continue
                            seen_paths.add(p)
                            agg.append(it)
                    # Sort by score desc and trim to k
                    try:
                        agg.sort(key=lambda d: float(d.get("score", 0.0)), reverse=True)
                    except Exception:
                        pass
                    items = agg[:k]
                except Exception:
                    items = []
                return _ok_json(self, {"items": items})
            if parsed.path == "/file":
                q = _u.parse_qs(parsed.query)
                raw = q.get("path", [""])[0]
                p = Path(_u.unquote(raw))
                if not p.exists() or not _file_under_base(p):
                    return _text(self, "Not found", 404)
                ctype = mimetypes.guess_type(str(p))[0] or "application/octet-stream"
                data = p.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_error(404, "Not Found")
        except Exception:
            try:
                self.send_error(500, "Server error")
            except Exception:
                pass

    def do_POST(self):  # noqa: N802
        try:
            parsed = _u.urlparse(self.path)
            if parsed.path == "/api/vs_generate":
                if _aip is None:
                    return _ok_json(self, {"ok": False, "error": "AI runner not available"}, code=503)
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    obj = {}
                slug = str((obj.get("slug") or "")).strip()
                if not slug:
                    return _ok_json(self, {"ok": False, "error": "Missing 'slug'"}, code=400)
                jid = _new_job("vs-gen", total=1)
                def _worker(ids, s):
                    try:
                        title = s.replace("_", " ").title()
                        try:
                            tv = qa_logic.load_theme_vocab(s)
                            t2 = str((tv.get("title") or "")).strip()
                            if t2:
                                title = t2
                        except Exception:
                            pass
                        try:
                            code = str((qa_logic.load_vocab().get(s, {}) or {}).get("code") or "") or None
                        except Exception:
                            code = None
                        payload = _aip.build_payload(s, title, code)
                        evidence = _aip._collect_grounding_sources(s, title, payload)
                        ok, raw, _obj = _aip.call_claude(payload, evidence=evidence)
                        if not ok or not raw:
                            _append_job_result(ids, {"ok": False, "error": raw or "call failed"})
                            _set_job(ids, done=1, status="done")
                            return
                        finals, needs, _full = _aip.partition_result(s, raw, require_citations=True)
                        # Deterministic hard checks; optionally trigger one regen with corrective hint
                        finals2, needs_add, hard_fields = _apply_deterministic_post_checks(finals)
                        # Merge needs_add into needs
                        try:
                            nbv = needs.setdefault("book_vocab", {})
                            for k, v in (needs_add.get("book_vocab", {}) or {}).items():
                                nbv.setdefault(k, []).extend(v)
                        except Exception:
                            pass
                        finals = finals2
                        # If hard violations exist, attempt a single corrective regen
                        if hard_fields:
                            try:
                                hint = {
                                    "corrections": {
                                        "bingo_card_sets": "Ensure each card has distinct icons; remove duplicates.",
                                        "code_words_puzzles": "Clue icons must not equal the target word.",
                                        "matching_pairs": "Do not pair identical items left/right."
                                    },
                                    "hard_fields": sorted(list(hard_fields)),
                                }
                                payload2 = dict(payload)
                                payload2["postcheck_hint"] = hint
                                ok2, raw2, _obj2 = _aip.call_claude(payload2, evidence=evidence)
                                if ok2 and raw2:
                                    finals_r, needs_r, _ = _aip.partition_result(s, raw2, require_citations=True)
                                    finals_r2, needs_r_add, _ = _apply_deterministic_post_checks(finals_r)
                                    # Prefer corrected finals when they reduce hard violations
                                    finals = finals_r2 or finals
                                    try:
                                        nbv = needs.setdefault("book_vocab", {})
                                        for k, v in (needs_r.get("book_vocab", {}) or {}).items():
                                            nbv.setdefault(k, []).extend(v)
                                        for k, v in (needs_r_add.get("book_vocab", {}) or {}).items():
                                            nbv.setdefault(k, []).extend(v)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                        vs = _vs_build_items(s, finals, needs)
                        _json_save(_vs_path(s), vs)
                        _append_job_result(ids, {"ok": True, "slug": s, "count": len(vs.get("items") or [])})
                    except BaseException as e:
                        try:
                            _append_job_result(ids, {"ok": False, "error": f"{type(e).__name__}: {e}"})
                        except Exception:
                            pass
                    finally:
                        _set_job(ids, done=1, status="done")
                th = threading.Thread(target=_worker, args=(jid, slug), daemon=True)
                th.start()
                return _ok_json(self, {"ok": True, "id": jid})
            if parsed.path == "/api/vs_save":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    obj = {}
                book = str((obj.get("book") or "")).strip()
                iid = str((obj.get("id") or "")).strip()
                st = str((obj.get("review_status") or "")).strip().lower()
                amended = obj.get("amended_value") if ("amended_value" in obj) else None
                if not book or not iid or st not in {"approved", "deleted", "amended"}:
                    return _ok_json(self, {"ok": False, "error": "Missing book/id or invalid status"}, code=400)
                path = _vs_path(book)
                vs = _json_load(path) or {"slug": book, "items": []}
                changed = False
                arr = list((vs or {}).get("items") or [])
                for it in arr:
                    try:
                        if str(it.get("id")) != iid:
                            continue
                        it["review_status"] = ("amended" if st == "amended" else st)
                        if st == "amended" and amended is not None:
                            it["value"] = amended
                            it["human_amended"] = True
                        changed = True
                        break
                    except Exception:
                        continue
                if changed:
                    vs["items"] = arr
                    _json_save(path, vs)
                return _ok_json(self, {"ok": True, "changed": changed})
            if parsed.path == "/api/vs_commit":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    obj = {}
                slug = str((obj.get("slug") or "")).strip()
                if not slug:
                    return _ok_json(self, {"ok": False, "error": "Missing 'slug'"}, code=400)
                vs = _json_load(_vs_path(slug)) or {"slug": slug, "items": []}
                r = _vs_commit_to_vocab(slug, vs)
                return _ok_json(self, {"ok": True, **(r or {})})
            if parsed.path == "/api/vocab_generate":
                if _vrb is None:
                    return _ok_json(self, {"ok": False, "error": "Vocab bridge not available"}, code=503)
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    obj = {}
                missing_only = bool(obj.get("missing_only"))
                overwrite = bool(obj.get("overwrite"))
                slugs = []
                if missing_only:
                    try:
                        q = _vrb.list_missing_vocab()  # type: ignore
                    except Exception:
                        q = []
                    slugs = [str(it.get("slug", "")).strip() for it in (q or []) if str(it.get("slug", "")).strip()]
                else:
                    one = str(obj.get("slug", "")).strip()
                    if one:
                        slugs = [one]
                if not slugs:
                    return _ok_json(self, {"ok": False, "error": "No slugs to generate"}, code=400)
                jid = _new_job("vocab-gen", total=len(slugs))
                def _worker(ids, books, ovw):
                    done = 0
                    for s in books:
                        try:
                            res = _vrb.generate_vocab_for_slug(s, overwrite=ovw)  # type: ignore
                        except BaseException as e:
                            try:
                                err = f"{type(e).__name__}: {e}"
                            except Exception:
                                err = "Unhandled error"
                            res = {"ok": False, "error": err}
                        _append_job_result(ids, {"slug": s, **(res or {})})
                        done += 1
                        _set_job(ids, done=done)
                    _set_job(ids, status="done")
                th = threading.Thread(target=_worker, args=(jid, slugs, overwrite), daemon=True)
                th.start()
                return _ok_json(self, {"id": jid})
            if parsed.path == "/api/vocab_identity_check":
                if _vrb is None:
                    return _ok_json(self, {"ok": False, "error": "Vocab bridge not available"}, code=503)
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    obj = {}
                slug = str((obj.get("slug") or "")).strip()
                if not slug:
                    # Allow query param fallback
                    q = _u.parse_qs(parsed.query)
                    slug = (q.get("slug", [""])[0] or "").strip()
                if not slug:
                    return _ok_json(self, {"ok": False, "error": "Missing slug"}, code=400)
                jid = _new_job("vocab-ident", total=1)
                def _worker(ids, s):
                    try:
                        res = _vrb.run_identity_check_for_slug(s)  # type: ignore
                    except Exception as e:
                        res = {"ok": False, "error": str(e)}
                    _append_job_result(ids, {"slug": s, **(res or {})})
                    _set_job(ids, done=1, status="done")
                th = threading.Thread(target=_worker, args=(jid, slug), daemon=True)
                th.start()
                return _ok_json(self, {"id": jid})
            if parsed.path == "/api/settings":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                # Persist as default settings, and attach/merge into profiles if pdf_key present
                try:
                    cur = _pdf_load_settings()
                except Exception:
                    cur = _pdf_default_settings()
                if not isinstance(cur, dict):
                    cur = _pdf_default_settings()
                pdf_key = str(obj.get("pdf_key", "") or "").strip()
                # Merge base
                for k in ("rows","cols","col_gap_pct","row_gap_pct","cell_mt","cell_mb","cell_ml","cell_mr","remove_labels","keep_labels","last_bottom_mb","corners"):
                    if k in obj:
                        cur[k] = obj[k]
                # Profiles
                profs = cur.get("profiles") if isinstance(cur.get("profiles"), dict) else {}
                if pdf_key:
                    prof = {k: cur.get(k) for k in ("rows","cols","col_gap_pct","row_gap_pct","cell_mt","cell_mb","cell_ml","cell_mr","remove_labels","keep_labels","last_bottom_mb","corners")}
                    profs[pdf_key] = prof
                cur["profiles"] = profs
                _pdf_save_settings(cur)
                return _ok_json(self, {"ok": True})
            if parsed.path == "/api/source_folder":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                path = str(obj.get("path", "")).strip()
                if not path:
                    return _ok_json(self, {"error": "Missing path"}, code=400)
                p = Path(path)
                if not p.exists() or not p.is_dir():
                    return _ok_json(self, {"error": "Folder does not exist"}, code=400)
                # Update global and persist in settings
                global PDF_SOURCE_FOLDER
                PDF_SOURCE_FOLDER = p.resolve()
                cur = _pdf_load_settings()
                cur["pdf_source"] = str(PDF_SOURCE_FOLDER)
                _pdf_save_settings(cur)
                return _ok_json(self, {"ok": True, "path": str(PDF_SOURCE_FOLDER)})
            if parsed.path == "/api/extract":
                if fitz is None or Image is None:
                    return _ok_json(self, {"error": "Missing Pillow or PyMuPDF"}, code=500)
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                rows = int(obj.get("rows", 6))
                cols = int(obj.get("cols", 6))
                col_gap_pct = float(obj.get("col_gap_pct", 0) or 0)
                row_gap_pct = float(obj.get("row_gap_pct", 0) or 0)
                cell_mt = float(obj.get("cell_mt", 4) or 0)
                cell_mb = float(obj.get("cell_mb", 18) or 0)
                cell_ml = float(obj.get("cell_ml", 4) or 0)
                cell_mr = float(obj.get("cell_mr", 4) or 0)
                all_pages = bool(obj.get("all_pages", True))
                page_mode = str(obj.get("page_mode", "all") or "all")
                page_index = int(obj.get("page_index", 0) or 0)
                page_range_raw = str(obj.get("page_range", "") or "")
                corners = obj.get("corners") or [[0.03,0.03],[0.97,0.03],[0.97,0.82],[0.03,0.82]]
                want_list = obj.get("pdfs") or []
                if obj.get("pdf") and not want_list:
                    want_list = [obj.get("pdf")]
                if not want_list:
                    return _ok_json(self, {"error": "No PDFs specified"}, code=400)
                PDF_TILE_DIR.mkdir(parents=True, exist_ok=True)
                PDF_STATE["tiles"].clear()
                PDF_STATE["groups"].clear()
                errors = []
                tid_seq = 1
                total_tiles = 0
                groups = []
                for name in want_list:
                    try:
                        pdf_path = (PDF_SOURCE_FOLDER / str(name)).resolve()
                        if not pdf_path.exists():
                            errors.append(f"Missing: {name}")
                            continue
                        with fitz.open(str(pdf_path)) as doc:
                            # Determine which pages to extract
                            if page_mode == "current":
                                pages = [max(0, min(page_index, doc.page_count - 1))]
                            elif page_mode == "range":
                                # Parse "1-3, 5, 7-9" into 0-indexed list
                                parsed = []
                                for part in page_range_raw.split(","):
                                    part = part.strip()
                                    if not part:
                                        continue
                                    m = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
                                    if m:
                                        a = max(1, int(m.group(1)))
                                        b = min(doc.page_count, int(m.group(2)))
                                        for i in range(a, b + 1):
                                            parsed.append(i - 1)
                                    else:
                                        try:
                                            n = int(part)
                                            if 1 <= n <= doc.page_count:
                                                parsed.append(n - 1)
                                        except ValueError:
                                            pass
                                pages = sorted(set(parsed)) if parsed else [0]
                            else:
                                # "all" mode (default, also handles legacy all_pages=True)
                                pages = range(doc.page_count)
                            g_tiles = []
                            for pi in pages:
                                try:
                                    p = doc.load_page(int(pi))
                                    pm = p.get_pixmap(alpha=False)
                                    base = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
                                    try:
                                        crop = _crop_quad_to_rect(base)(corners)
                                    except Exception:
                                        crop = base
                                    W, H = crop.size
                                    gap_w = (max(0, cols - 1)) * (col_gap_pct / 100.0) * W
                                    gap_h = (max(0, rows - 1)) * (row_gap_pct / 100.0) * H
                                    cw = max(1, int(round((W - gap_w) / max(1, cols))))
                                    ch = max(1, int(round((H - gap_h) / max(1, rows))))
                                    # loop cells
                                    for r in range(rows):
                                        for c in range(cols):
                                            x0 = c * cw + c * int(round((col_gap_pct / 100.0) * W))
                                            y0 = r * ch + r * int(round((row_gap_pct / 100.0) * H))
                                            x1 = x0 + cw
                                            y1 = y0 + ch
                                            # apply per-cell trims
                                            tw = max(1, x1 - x0)
                                            th = max(1, y1 - y0)
                                            mt = int(round((cell_mt / 100.0) * th))
                                            mb = int(round((cell_mb / 100.0) * th))
                                            ml = int(round((cell_ml / 100.0) * tw))
                                            mr = int(round((cell_mr / 100.0) * tw))
                                            xx0 = max(0, x0 + ml)
                                            yy0 = max(0, y0 + mt)
                                            xx1 = min(W, x1 - mr)
                                            yy1 = min(H, y1 - mb)
                                            if xx1 <= xx0 or yy1 <= yy0:
                                                continue
                                            tile = crop.crop((xx0, yy0, xx1, yy1))
                                            try:
                                                tile = _make_background_transparent(tile, tolerance=30)
                                            except Exception:
                                                pass
                                            tid = f"t{tid_seq:06d}"
                                            outp = PDF_TILE_DIR / f"{tid}.png"
                                            tile.save(str(outp), format="PNG")
                                            PDF_STATE["tiles"][tid] = {"path": str(outp), "w": tile.width, "h": tile.height, "pdf": str(name)}
                                            g_tiles.append({"id": tid})
                                            tid_seq += 1
                                            total_tiles += 1
                                except Exception as e:
                                    errors.append(f"{name} p{pi+1}: {e}")
                            groups.append({
                                "pdf": str(name),
                                "tiles": g_tiles,
                                "suggested_book": Path(str(name)).stem,
                            })
                    except Exception as e:
                        errors.append(f"{name}: {e}")
                PDF_STATE["groups"] = groups
                return _ok_json(self, {"groups": groups, "count": total_tiles, "errors": errors})
            if parsed.path == "/api/save_labels":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                labels = obj.get("labels") or {}
                tile_sources = obj.get("tile_sources") or {}
                if not isinstance(labels, dict):
                    return _text(self, "Bad JSON", 400)
                saved = 0
                dup = 0
                skipped = 0
                prov = _load_provenance()
                labidx = _load_label_index()
                saved_by_source = {}
                SYMBOLS_ALPHA_ROOT.mkdir(parents=True, exist_ok=True)
                for tid, raw in labels.items():
                    try:
                        label = _normalize_label(str(raw or ""))
                        if not label:
                            skipped += 1
                            continue
                        meta = PDF_STATE.get("tiles", {}).get(tid)
                        if not meta:
                            skipped += 1
                            continue
                        src_img = Path(meta.get("path", ""))
                        if not src_img.exists():
                            skipped += 1
                            continue
                        bucket = _alpha_bucket_for(label)
                        out_dir = SYMBOLS_ALPHA_ROOT / bucket
                        out_dir.mkdir(parents=True, exist_ok=True)
                        dst = out_dir / f"{label}.png"
                        if dst.exists():
                            # find next suffix
                            k = 2
                            while True:
                                alt = out_dir / f"{label}_{k}.png"
                                if not alt.exists():
                                    dst = alt
                                    dup += 1
                                    break
                                k += 1
                        shutil.copy2(src_img, dst)
                        saved += 1
                        # Update indices
                        book = str(tile_sources.get(tid, "")).strip()
                        source_pdf = str(meta.get("pdf", "")).strip()
                        if source_pdf:
                            saved_by_source[source_pdf] = int(saved_by_source.get(source_pdf, 0)) + 1
                        try:
                            prov[str(dst)] = {"book": book} if book else {"book": ""}
                        except Exception:
                            prov[str(dst)] = book or ""
                        labidx[str(dst)] = label
                    except Exception:
                        continue
                try:
                    _save_provenance(prov)
                except Exception:
                    pass
                try:
                    _save_label_index(labidx)
                except Exception:
                    pass
                try:
                    extracted = _load_extracted_log()
                    for source, count in saved_by_source.items():
                        previous = extracted.get(source, {}) if isinstance(extracted.get(source), dict) else {}
                        extracted[source] = {
                            "saved_count": int(previous.get("saved_count", 0)) + int(count),
                            "last_saved": _dt.datetime.now().isoformat(timespec="seconds"),
                        }
                    _save_extracted_log(extracted)
                except Exception:
                    pass
                return _ok_json(self, {"saved_count": saved, "duplicate_count": dup, "skipped_empty": skipped})
            if parsed.path == "/api/open_output":
                try:
                    path = str(SYMBOLS_ALPHA_ROOT)
                    if os.name == "nt":
                        os.startfile(path)  # type: ignore[attr-defined]
                    else:
                        _urlreq.urlopen(f"file://{path}")
                except Exception:
                    try:
                        webbrowser.open(path)
                    except Exception:
                        pass
                return _ok_json(self, {"ok": True})
            if parsed.path.startswith("/api/vocab_promote/"):
                if _vrb is None:
                    return _ok_json(self, {"ok": False, "error": "Vocab bridge not available"}, code=503)
                slug = parsed.path.split("/api/vocab_promote/")[-1].strip()
                if not slug:
                    return _ok_json(self, {"ok": False, "error": "Missing slug"}, code=400)
                try:
                    r = _vrb.promote_slug(slug)  # type: ignore
                except Exception as e:
                    return _ok_json(self, {"ok": False, "error": str(e)}, code=500)
                if not r.get("ok"):
                    return _ok_json(self, r, code=400)
                return _ok_json(self, r)
            if parsed.path.startswith("/api/vocab_reject/"):
                if _vrb is None:
                    return _ok_json(self, {"ok": False, "error": "Vocab bridge not available"}, code=503)
                slug = parsed.path.split("/api/vocab_reject/")[-1].strip()
                if not slug:
                    return _ok_json(self, {"ok": False, "error": "Missing slug"}, code=400)
                try:
                    r = _vrb.reject_slug(slug)  # type: ignore
                except Exception as e:
                    return _ok_json(self, {"ok": False, "error": str(e)}, code=500)
                if not r.get("ok"):
                    return _ok_json(self, r, code=400)
                return _ok_json(self, r)
            if parsed.path == "/api/open_path":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                path = str(obj.get("path", "")).strip()
                if not path:
                    return _ok_json(self, {"error": "Missing path"}, code=400)
                try:
                    if os.name == "nt":
                        os.startfile(path)  # type: ignore[attr-defined]
                    else:
                        _urlreq.urlopen(f"file://{path}")
                except Exception:
                    try:
                        webbrowser.open(path)
                    except Exception:
                        pass
                return _ok_json(self, {"ok": True})
            if parsed.path == "/api/meta/save":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                if not book:
                    return _text(self, "Missing book", 400)
                hero = str(obj.get("hero", ""))
                cover = str(obj.get("cover", ""))
                overview_present = isinstance(obj, dict) and ("overview" in obj)
                overview_val = str(obj.get("overview", "")) if overview_present else None
                theme = ASSETS / "themes" / book
                theme.mkdir(parents=True, exist_ok=True)
                meta_path = theme / "book_meta.json"
                meta = {}
                try:
                    if meta_path.exists():
                        with meta_path.open("r", encoding="utf-8") as f:
                            meta = json.load(f) or {}
                except Exception:
                    meta = {}
                if not isinstance(meta, dict):
                    meta = {}
                meta["hero"] = hero
                meta["cover"] = cover
                if overview_present:
                    meta["overview"] = overview_val if overview_val is not None else ""
                try:
                    with meta_path.open("w", encoding="utf-8") as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                except Exception:
                    return _text(self, "Failed to save meta", 500)
                return _ok_json(self, {"ok": True})
            if parsed.path == "/api/save":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                items = obj.get("items") or []
                if not book or not isinstance(items, list):
                    return _text(self, "Missing fields", 400)
                dest = ASSETS / "themes" / book / "activity_images"
                dest.mkdir(parents=True, exist_ok=True)
                copied = 0
                updated = 0
                for it in items:
                    try:
                        src = Path(str(it.get("src", "")))
                        label = str(it.get("label", "")).strip()
                        label = "".join(ch if ch.isalnum() else "_" for ch in label.lower())
                        label = "_".join([p for p in label.split("_") if p]) or "icon"
                        if not src.exists() or not _file_under_base(src) or not label:
                            continue
                        dst = dest / f"{label}.png"
                        if not dst.exists():
                            shutil.copy2(src, dst)
                            copied += 1
                        else:
                            shutil.copy2(src, dst)
                            updated += 1
                    except Exception:
                        continue
                return _ok_json(self, {"copied": copied, "updated": updated})
            if parsed.path == "/api/refresh":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                if not book:
                    return _text(self, "Missing book", 400)
                qa = qa_logic.load_qa_log()
                b = qa.get(book, {})
                words = b.get("words", {}) if isinstance(b, dict) else {}
                dest = ASSETS / "themes" / book / "activity_images"
                dest.mkdir(parents=True, exist_ok=True)
                copied = 0
                updated = 0
                for w, info in words.items():
                    try:
                        if (
                            not isinstance(info, dict)
                            or info.get("status") != "replaced"
                            or info.get("exclude_activities")
                        ):
                            continue
                        src = Path(str(info.get("path", "")))
                        if not src.exists() or not _file_under_base(src):
                            continue
                        try:
                            fname = qa_logic._sanitized_png_name(w)  # type: ignore
                            if not isinstance(fname, str) or not fname.endswith(".png"):
                                raise Exception("bad fname")
                        except Exception:
                            fname = _sanitize_label(str(w)) + ".png"
                        dst = dest / fname
                        existed = dst.exists()
                        shutil.copy2(src, dst)
                        if not existed:
                            copied += 1
                        info["path"] = str(dst)
                        updated += 1
                    except Exception:
                        continue
                if updated:
                    qa_logic.save_qa_log(qa)
                return _ok_json(self, {"copied": copied, "updated": updated})

            if parsed.path == "/api/theme_rename":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                old = str(obj.get("old", "")).strip()
                new = str(obj.get("new", "")).strip()
                if not book or not old or not new:
                    return _text(self, "Missing fields", 400)
                dest = ASSETS / "themes" / book / "activity_images"
                src = dest / f"{old}.png"
                if not src.exists() or not _file_under_base(src):
                    return _text(self, "Not found", 404)
                new_label = _sanitize_label(new)
                if not new_label:
                    return _text(self, "Bad name", 400)
                dst = dest / f"{new_label}.png"
                try:
                    if dst.exists() and dst.resolve() != src.resolve():
                        try:
                            dst.unlink()
                        except Exception:
                            pass
                    os.replace(str(src), str(dst))
                except Exception:
                    return _text(self, "Failed", 500)
                return _ok_json(self, {"ok": True})

            if parsed.path == "/api/theme_delete":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                name = str(obj.get("name", "")).strip()
                if not book or not name:
                    return _text(self, "Missing fields", 400)
                dest = ASSETS / "themes" / book / "activity_images"
                p = dest / f"{name}.png"
                if not p.exists() or not _file_under_base(p):
                    return _text(self, "Not found", 404)
                try:
                    p.unlink()
                except Exception:
                    return _text(self, "Failed", 500)
                return _ok_json(self, {"ok": True})

            if parsed.path == "/api/ban":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                raw = str(obj.get("path", "")).strip()
                delete_file = bool(obj.get("delete_file", False))
                if not raw:
                    return _text(self, "Missing path", 400)
                p = Path(_u.unquote(raw))
                try:
                    rp = p.resolve()
                except Exception:
                    rp = p
                if not _file_under_base(rp):
                    return _text(self, "Out of scope", 400)
                try:
                    qa_logic.add_to_banlist(str(rp))
                except Exception:
                    pass
                deleted = False
                if delete_file:
                    try:
                        parts = [x.lower() for x in rp.parts]
                        if rp.exists() and ("activity_images" not in parts or "themes" not in parts):
                            try:
                                rp.unlink()
                                deleted = True
                            except Exception:
                                deleted = False
                    except Exception:
                        deleted = False
                return _ok_json(self, {"ok": True, "banned": str(rp), "deleted": deleted})

            if parsed.path == "/api/open_theme":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    obj = {}
                book = str(obj.get("book", "")).strip()
                if not book:
                    return _text(self, "Missing book", 400)
                dest = ASSETS / "themes" / book / "activity_images"
                try:
                    dest.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                try:
                    if os.name == "nt":
                        os.startfile(str(dest))  # type: ignore[attr-defined]
                    else:
                        try:
                            webbrowser.open(dest.as_uri())
                        except Exception:
                            pass
                except Exception:
                    try:
                        webbrowser.open(dest.as_uri())
                    except Exception:
                        pass
                return _ok_json(self, {"ok": True, "path": str(dest)})

            if parsed.path == "/api/upload":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str((obj.get("book") or "")).strip()
                files = obj.get("files") or []
                if not book or not isinstance(files, list):
                    return _text(self, "Missing fields", 400)
                dest = ASSETS / "themes" / book / "activity_images"
                try:
                    dest.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                png_sig = b"\x89PNG\r\n\x1a\n"
                saved = 0
                skipped = 0
                items = []
                for ent in files:
                    try:
                        name = str((ent.get("name") or "")).strip()
                        if not name:
                            name = f"upload_{uuid.uuid4().hex[:8]}.png"
                        stem = _sanitize_label(Path(name).stem)
                        if not stem:
                            stem = f"icon_{uuid.uuid4().hex[:6]}"
                        data = ent.get("data") or ""
                        s = str(data)
                        if s.startswith("data:"):
                            i = s.find(",")
                            s = s[i+1:] if i >= 0 else s
                        try:
                            raw = base64.b64decode(s)
                        except Exception:
                            skipped += 1
                            continue
                        if not raw or len(raw) < 8 or raw[:8] != png_sig:
                            skipped += 1
                            continue
                        dst = dest / f"{stem}.png"
                        if dst.exists():
                            k = 2
                            while True:
                                alt = dest / f"{stem}_{k}.png"
                                if not alt.exists():
                                    dst = alt
                                    break
                                k += 1
                        with open(dst, "wb") as outf:
                            outf.write(raw)
                        saved += 1
                        items.append({"name": dst.name, "path": str(dst)})
                    except Exception:
                        skipped += 1
                        continue
                return _ok_json(self, {"saved": saved, "skipped": skipped, "items": items})

            if parsed.path == "/api/decision":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                word = str(obj.get("word", "")).strip()
                decision = str(obj.get("decision", "")).strip().lower()
                replacement_path = str(obj.get("path", "")).strip()
                target_label = str(obj.get("label", "")).strip()
                try:
                    exclude_flag = obj.get("exclude_activities")
                except Exception:
                    exclude_flag = None
                if not book or not word or decision not in ("keep", "skip", "missing", "replaced"):
                    return _text(self, "Missing or invalid fields", 400)
                try:
                    qa_logic.save_decision(book, word, decision, replacement_path or None)
                except Exception:
                    pass
                try:
                    qa = qa_logic.load_qa_log()
                    b = qa.setdefault(book, {"words": {}, "completed": False})
                    w = b["words"].setdefault(word, {})
                    if target_label:
                        w["target_label"] = _sanitize_label(target_label)
                    if exclude_flag is not None:
                        try:
                            w["exclude_activities"] = bool(exclude_flag)
                        except Exception:
                            w["exclude_activities"] = True if str(exclude_flag).strip() in ("1", "true", "True") else False
                    else:
                        # Default behavior: mark Skip as excluded; clear exclusion on keep/replaced
                        if decision == "skip":
                            w["exclude_activities"] = True
                        elif decision in ("keep", "replaced"):
                            if isinstance(w, dict) and "exclude_activities" in w:
                                try:
                                    del w["exclude_activities"]
                                except Exception:
                                    pass
                    qa_logic.save_qa_log(qa)
                except Exception:
                    pass
                return _ok_json(self, {"ok": True})
            if parsed.path == "/api/apply":
                ln = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(ln) if ln else b"{}"
                try:
                    obj = json.loads(body.decode("utf-8"))
                except Exception:
                    return _text(self, "Bad JSON", 400)
                book = str(obj.get("book", "")).strip()
                if not book:
                    return _text(self, "Missing book", 400)
                qa = qa_logic.load_qa_log()
                book_ent = qa.setdefault(book, {"words": {}, "completed": False})
                words = book_ent.setdefault("words", {}) if isinstance(book_ent, dict) else {}
                # Pre-chosen (auto-resolved) icons count as selected unless the user skipped them
                try:
                    req_items = qa_logic.get_icons_for_book(book, include_core=False, include_context=False)
                except Exception:
                    req_items = []
                auto_paths = {}
                for it in req_items:
                    try:
                        if isinstance(it, dict) and it.get("current_path"):
                            auto_paths[str(it.get("word", ""))] = str(it.get("current_path"))
                    except Exception:
                        continue
                dest = ASSETS / "themes" / book / "activity_images"
                dest.mkdir(parents=True, exist_ok=True)
                copied = 0
                updated = 0
                for w in list(dict.fromkeys(list(words.keys()) + list(auto_paths.keys()))):
                    try:
                        info = words.get(w)
                        if info is None:
                            info = {}
                        if (not isinstance(info, dict)):
                            continue
                        if info.get("exclude_activities"):
                            continue
                        status = str(info.get("status", "")).lower()
                        if status in ("skip", "missing"):
                            continue
                        if status not in ("replaced", "keep", "kept") and w not in auto_paths:
                            continue
                        # Determine source image
                        src = Path(str(info.get("path", "")))
                        if not src.exists() or not _file_under_base(src):
                            rp = auto_paths.get(w)
                            if not rp:
                                try:
                                    rp = qa_logic._resolve_icon_path_for_word(book, w)  # type: ignore[attr-defined]
                                except Exception:
                                    rp = None
                            if rp:
                                src = Path(str(rp))
                        if not src.exists() or not _file_under_base(src):
                            continue
                        if not status:
                            info["status"] = "keep"
                        words[w] = info
                        lbl = str(info.get("target_label", "")).strip()
                        if lbl:
                            fname = _sanitize_label(lbl) + ".png"
                        else:
                            try:
                                fname = qa_logic._sanitized_png_name(w)  # type: ignore
                                if not isinstance(fname, str) or not fname.endswith(".png"):
                                    raise Exception("bad fname")
                            except Exception:
                                fname = _sanitize_label(str(w)) + ".png"
                        dst = dest / fname
                        existed = dst.exists()
                        shutil.copy2(src, dst)
                        if not existed:
                            copied += 1
                        info["path"] = str(dst)
                        updated += 1
                    except Exception:
                        continue
                if updated:
                    qa_logic.save_qa_log(qa)
                return _ok_json(self, {"copied": copied, "updated": updated})

            self.send_error(404, "Not Found")
        except Exception:
            try:
                self.send_error(500, "Server error")
            except Exception:
                pass


def _prewarm_library():
    try:
        qa_logic._library_paths(None)  # type: ignore[attr-defined]
    except Exception:
        pass


def _ensure_stdio():
    # pythonw.exe (used by the Tool Launcher) has no console: stdout/stderr are None.
    # Route them to a log file so prints/tracebacks never raise or vanish.
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        log_path = Path(__file__).resolve().parent / "icon_labeler_server.log"
        f = open(log_path, "a", encoding="utf-8", buffering=1)
    except Exception:
        f = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = f
    if sys.stderr is None:
        sys.stderr = f


def main(port: int = 5052):
    _ensure_stdio()
    srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    srv.daemon_threads = True
    print(f"Icon Labeler running on http://127.0.0.1:{port}")
    try:
        threading.Thread(target=_prewarm_library, daemon=True).start()
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    p = 5052
    if len(sys.argv) >= 2:
        try:
            p = int(sys.argv[1])
        except Exception:
            pass
    main(p)













