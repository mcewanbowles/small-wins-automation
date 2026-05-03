from __future__ import annotations
import sys
from pathlib import Path

P = Path(__file__).with_name('studioforge_app.py')
text = P.read_text(encoding='utf-8')
lines = text.splitlines()
changed = False

def find_idx(substr: str, start: int = 0) -> int:
    for i in range(max(0, start), len(lines)):
        if substr in lines[i]:
            return i
    return -1

def get_indent(s: str) -> str:
    i = 0
    while i < len(s) and s[i] in (' ', '\t'):
        i += 1
    return s[:i]

def insert_lines(at: int, new_lines: list[str]):
    global lines
    lines = lines[:at] + new_lines + lines[at:]

def remove_range(a: int, b: int):
    # remove lines [a, b) (b is exclusive)
    global lines
    if a < 0 or b < 0 or a >= b:
        return
    lines = lines[:a] + lines[b:]

# 1) Ensure urllib.request import directly after urllib.parse
if 'import urllib.request' not in text:
    idx = find_idx('import urllib.parse')
    if idx >= 0:
        lines.insert(idx + 1, 'import urllib.request')
        changed = True

# 2) Add bulk status actions after Mark Uploaded safe_rerun()
if 'trk_mark_not_started' not in text and 'trk_mark_needs_update' not in text and 'trk_mark_paused' not in text:
    idx_mu = find_idx('key="trk_mark_uploaded"')
    if idx_mu >= 0:
        # find first safe_rerun() after this
        idx_sr = -1
        for j in range(idx_mu, min(idx_mu + 80, len(lines))):
            if lines[j].strip() == 'safe_rerun()':
                idx_sr = j
                break
        if idx_sr >= 0:
            ind = get_indent(lines[idx_mu])
            block = [
                ind + 'if st.button("Mark Not Started", key="trk_mark_not_started", disabled=not sel_ids):',
                ind + '    for rid in list(sel_ids):',
                ind + '        update_tracker_record(rid, {"status": "not_started", "uploaded_date": None})',
                ind + '    show_toast("success", f"Updated {len(sel_ids)} record(s) -> Not started")',
                ind + '    safe_rerun()',
                ind + 'if st.button("Mark Needs Update", key="trk_mark_needs_update", disabled=not sel_ids):',
                ind + '    for rid in list(sel_ids):',
                ind + '        update_tracker_record(rid, {"status": "needs_update"})',
                ind + '    show_toast("success", f"Updated {len(sel_ids)} record(s) -> Needs update")',
                ind + '    safe_rerun()',
                ind + 'if st.button("Mark Paused", key="trk_mark_paused", disabled=not sel_ids):',
                ind + '    for rid in list(sel_ids):',
                ind + '        update_tracker_record(rid, {"status": "paused"})',
                ind + '    show_toast("success", f"Updated {len(sel_ids)} record(s) -> Paused")',
                ind + '    safe_rerun()',
            ]
            insert_lines(idx_sr + 1, block)
            changed = True

# 3) Fix/Insert Pending navigation block
has_pending_nav = 'trk_prev_pending' in text or 'trk_next_pending' in text
broken_start = find_idx('pending_ids = [str(r.get(id)) for r in filt')
if broken_start >= 0:
    idx_nf = find_idx('if not filt:', broken_start)
    if idx_nf == -1:
        idx_nf = broken_start
    ind = get_indent(lines[broken_start])
    correct = [
        ind + 'pending_ids = [str(r.get("id")) for r in filt if str(r.get("status") or "not_started").strip().lower() in {"not_started","ready","needs_update"} and r.get("id")]',
        ind + 'st.session_state["trk_pending_ids"] = pending_ids',
        ind + 'fp1, fp2, fp3 = st.columns([1, 1, 2])',
        ind + 'with fp1:',
        ind + '    if st.button("Prev Pending", key="trk_prev_pending", disabled=not pending_ids):',
        ind + '        idx = int(st.session_state.get("trk_focus_idx", 0) or 0)',
        ind + '        idx = (idx - 1) % len(pending_ids) if pending_ids else 0',
        ind + '        st.session_state["trk_focus_idx"] = idx',
        ind + '        st.session_state["trk_focus_id"] = pending_ids[idx] if pending_ids else None',
        ind + '        safe_rerun()',
        ind + 'with fp2:',
        ind + '    if st.button("Next Pending", key="trk_next_pending", disabled=not pending_ids):',
        ind + '        idx = int(st.session_state.get("trk_focus_idx", -1) or -1)',
        ind + '        idx = (idx + 1) % len(pending_ids) if pending_ids else 0',
        ind + '        st.session_state["trk_focus_idx"] = idx',
        ind + '        st.session_state["trk_focus_id"] = pending_ids[idx] if pending_ids else None',
        ind + '        safe_rerun()',
        ind + 'with fp3:',
        ind + '    if pending_ids:',
        ind + '        cur = int(st.session_state.get("trk_focus_idx", 0) or 0) % len(pending_ids)',
        ind + '        st.caption(f"Pending focus: {cur+1}/{len(pending_ids)}")',
    ]
    remove_range(broken_start, idx_nf)
    insert_lines(broken_start, correct)
    changed = True
elif not has_pending_nav:
    idx_nf = find_idx('if not filt:')
    if idx_nf >= 0:
        ind = get_indent(lines[idx_nf])
        correct = [
            ind + 'pending_ids = [str(r.get("id")) for r in filt if str(r.get("status") or "not_started").strip().lower() in {"not_started","ready","needs_update"} and r.get("id")]',
            ind + 'st.session_state["trk_pending_ids"] = pending_ids',
            ind + 'fp1, fp2, fp3 = st.columns([1, 1, 2])',
            ind + 'with fp1:',
            ind + '    if st.button("Prev Pending", key="trk_prev_pending", disabled=not pending_ids):',
            ind + '        idx = int(st.session_state.get("trk_focus_idx", 0) or 0)',
            ind + '        idx = (idx - 1) % len(pending_ids) if pending_ids else 0',
            ind + '        st.session_state["trk_focus_idx"] = idx',
            ind + '        st.session_state["trk_focus_id"] = pending_ids[idx] if pending_ids else None',
            ind + '        safe_rerun()',
            ind + 'with fp2:',
            ind + '    if st.button("Next Pending", key="trk_next_pending", disabled=not pending_ids):',
            ind + '        idx = int(st.session_state.get("trk_focus_idx", -1) or -1)',
            ind + '        idx = (idx + 1) % len(pending_ids) if pending_ids else 0',
            ind + '        st.session_state["trk_focus_idx"] = idx',
            ind + '        st.session_state["trk_focus_id"] = pending_ids[idx] if pending_ids else None',
            ind + '        safe_rerun()',
            ind + 'with fp3:',
            ind + '    if pending_ids:',
            ind + '        cur = int(st.session_state.get("trk_focus_idx", 0) or 0) % len(pending_ids)',
            ind + '        st.caption(f"Pending focus: {cur+1}/{len(pending_ids)}")',
        ]
        insert_lines(idx_nf, correct)
        changed = True

# 4) Add TPT URL Check button after Open link
if 'trk_url_chk_' not in text:
    idx_open = find_idx('st.markdown(f"[Open]({tpt_url})")')
    if idx_open >= 0:
        ind = get_indent(lines[idx_open])
        block = [
            ind + 'if st.button("Check", key=f"trk_url_chk_{rid}"):',
            ind + '    try:',
            ind + '        urllib.request.urlopen(tpt_url, timeout=5)',
            ind + '        show_toast("success", "URL reachable")',
            ind + '    except Exception:',
            ind + '        show_toast("warning", "URL not reachable")',
        ]
        insert_lines(idx_open + 1, block)
        changed = True

# 5) Auto-expand Edit expander
idx_exp = find_idx('st.expander("Edit", expanded=False)')
if idx_exp >= 0 and 'trk_focus_id' not in lines[idx_exp]:
    lines[idx_exp] = lines[idx_exp].replace('expanded=False', 'expanded=(rid == st.session_state.get("trk_focus_id"))')
    changed = True

# 6) Per-record open folder buttons after notes text_area
if 'trk_row_open_upload_' not in text and 'trk_row_open_final_' not in text:
    idx_notes = find_idx('key=f"trk_notes_{rid}"')
    if idx_notes >= 0:
        ind = get_indent(lines[idx_notes])
        block = [
            ind + 'ro1, ro2 = st.columns([1, 1])',
            ind + 'with ro1:',
            ind + '    if st.button("Open TPT_UPLOAD", key=f"trk_row_open_upload_{rid}"):',
            ind + '        outp = output_dir_for_book(str(r.get("book_slug") or ""))',
            ind + '        up = (outp / "TPT_UPLOAD") if outp else None',
            ind + '        if up and up.exists():',
            ind + '            open_folder(up)',
            ind + '        else:',
            ind + '            show_toast("info", "TPT_UPLOAD not found")',
            ind + 'with ro2:',
            ind + '    if st.button("Open FINAL", key=f"trk_row_open_final_{rid}"):',
            ind + '        outp = output_dir_for_book(str(r.get("book_slug") or ""))',
            ind + '        fi = (outp / "FINAL") if outp else None',
            ind + '        if fi and fi.exists():',
            ind + '            open_folder(fi)',
            ind + '        else:',
            ind + '            show_toast("info", "FINAL not found")',
        ]
        insert_lines(idx_notes + 1, block)
        changed = True

if changed:
    P.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('OK: tracker enhancements adjusted')
else:
    print('NOCHANGE: nothing to do')
