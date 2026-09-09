param()
$ErrorActionPreference = 'Stop'

$File = 'D:\Seagate\small-wins-automation\Studioforge\WINDSURF_TOOL_LAUNCHER.py'
if (-not (Test-Path -LiteralPath $File)) { throw "Not found: $File" }

$content = Get-Content -LiteralPath $File -Raw -Encoding UTF8
$orig = $content
$changes = @()

# 1) Header Diagnostics button
if ($content -notmatch 'Diagnostics", command=self._show_diagnostics') {
  $patternHeader = '(?ms)(tk\.Label\(header,\s*text="Small Wins Studio — Tool Launcher"[\s\S]*?anchor="w"\)\r?\n)'
  $insertHeader = @'
        btn_row = tk.Frame(header, bg=SWS_TEAL)
        btn_row.pack(side="right", padx=8, pady=8)
        tk.Button(btn_row, text="Diagnostics", command=self._show_diagnostics).pack(side="left")
'@
  $new1 = [Regex]::Replace($content, $patternHeader, "`$1$insertHeader", 1)
  if ($new1 -ne $content) { $content = $new1; $changes += 'header_diagnostics' }
}

# 2) Remember last-selected book after reading books
if ($content -notmatch '_last_book_slug') {
  $patternBooks = '(?ms)(self\.books\s*=\s*_list_books\(\)\r?\n)'
  $insertBooks = @'
        try:
            self._last_book_slug = _read_log().get("_last_book")
        except Exception:
            self._last_book_slug = None
'@
  $new2 = [Regex]::Replace($content, $patternBooks, "`$1$insertBooks", 1)
  if ($new2 -ne $content) { $content = $new2; $changes += 'remember_books_read' }
}

# 3) Default selection uses last-selected slug
$needleDisp = '        disp_var = tk.StringVar(value=(labels[0] if labels else ""))'
if ($content -like "*${needleDisp}*") {
  $replacementDisp = @'
        default_label = (labels[0] if labels else "")
        try:
            last = getattr(self, "_last_book_slug", None)
            if last:
                for lab, s in label2slug.items():
                    if s == last:
                        default_label = lab
                        break
        except Exception:
            pass
        disp_var = tk.StringVar(value=default_label)
'@
  $content = $content -replace [Regex]::Escape($needleDisp), [Regex]::Escape($replacementDisp) -replace '\\r\\n', "`r`n"
  $changes += 'combo_default_last_book'
}

# 4) Board Ready: add Open Theme & Open Output buttons after Launch
if ($content -notmatch 'Open Output Folder.*_launch_board_ready') {
  $patternBR = '(?ms)(def\s+_init_board_tab\([\s\S]*?btn\.pack\(anchor="w",\s*pady=12\)\r?\n)'
  $insertBR = @'
        tk.Button(card, text="Open Theme Folder", command=lambda: self._open_theme_folder(slug_var.get())).pack(anchor="w")
        tk.Button(card, text="Open Output Folder", command=lambda: self._open_output_for(slug_var.get(), code_var.get())).pack(anchor="w")
'@
  $new4 = [Regex]::Replace($content, $patternBR, "`$1$insertBR", 1)
  if ($new4 -ne $content) { $content = $new4; $changes += 'board_buttons' }
}

# 5) Matching: add Open Output after existing Open Theme Folder
if ($content -match 'def\s+_init_matching_tab\(' -and $content -notmatch 'def\s+_init_matching_tab[\s\S]*Open Output Folder') {
  $patternMT = '(?ms)(def\s+_init_matching_tab\([\s\S]*?Open Theme Folder".*?\)\.pack\(anchor="w"\)\r?\n)'
  $insertMT = '        tk.Button(card, text="Open Output Folder", command=lambda: self._open_output_for(slug_var.get(), code_var.get())).pack(anchor="w")' + "`r`n"
  $new5 = [Regex]::Replace($content, $patternMT, "`$1$insertMT", 1)
  if ($new5 -ne $content) { $content = $new5; $changes += 'matching_output_btn' }
}

# 6) Listing: add Open Output after existing Open Theme Folder
if ($content -match 'def\s+_init_listing_tab\(' -and $content -notmatch 'def\s+_init_listing_tab[\s\S]*Open Output Folder') {
  $patternLT = '(?ms)(def\s+_init_listing_tab\([\s\S]*?Open Theme Folder".*?\)\.pack\(anchor="w"\)\r?\n)'
  $insertLT = '        tk.Button(card, text="Open Output Folder", command=lambda: self._open_output_for(slug_var.get(), code_var.get())).pack(anchor="w")' + "`r`n"
  $new6 = [Regex]::Replace($content, $patternLT, "`$1$insertLT", 1)
  if ($new6 -ne $content) { $content = $new6; $changes += 'listing_output_btn' }
}

# 7) Insert _open_output_for and _remember_last_book helpers after _open_theme_folder
if ($content -notmatch 'def\s+_open_output_for\(') {
  $patternIns = '(?ms)(def\s+_open_theme_folder\([\s\S]*?self\._open_path\(base\)\r?\n)'
  $helpers = @'
    def _open_output_for(self, slug, code):
        if not slug:
            messagebox.showwarning("Select book", "Please choose a book slug.")
            return
        pack_code = code or (slug[:3].upper() + "1")
        cands = [
            STUDIOFORGE_DIR / "OUTPUT" / str(pack_code),
            THEMES_DIR / slug / "OUTPUT",
            THEMES_DIR / slug / "05 outputs",
            THEMES_DIR / slug / "output",
        ]
        for p in cands:
            try:
                if p.exists():
                    self._open_path(p)
                    return
            except Exception:
                continue
        self._open_path(STUDIOFORGE_DIR / "OUTPUT")

    def _remember_last_book(self, slug):
        try:
            data = _read_log()
            data["_last_book"] = slug
            _write_log(data)
            self._last_book_slug = slug
        except Exception:
            pass
'@
  $new7 = [Regex]::Replace($content, $patternIns, "`$1$helpers", 1)
  if ($new7 -ne $content) { $content = $new7; $changes += 'helpers_added' }
}

# 8) Remember last book on successful launches
$replacements = @(
  @{ pat = 'if ok:\r?\n\s{12}_touch_used\("board_ready"\)'; rep = "if ok:`r`n            self._remember_last_book(slug)`r`n            _touch_used(\"board_ready\")" },
  @{ pat = 'if ok:\r?\n\s{12}_touch_used\("matching"\)'; rep = "if ok:`r`n            self._remember_last_book(slug)`r`n            _touch_used(\"matching\")" },
  @{ pat = 'if ok:\r?\n\s{12}_touch_used\("listing_generator"\)'; rep = "if ok:`r`n            self._remember_last_book(slug)`r`n            _touch_used(\"listing_generator\")" }
)
foreach ($r in $replacements) {
  $new = [Regex]::Replace($content, $r.pat, $r.rep, 1)
  if ($new -ne $content) { $content = $new; $changes += 'remember_on_launch' }
}

if ($content -ne $orig) {
  Set-Content -LiteralPath $File -Encoding UTF8 -NoNewline -Value $content
  Write-Output ("Patched: " + ($changes -join ', '))
} else {
  Write-Output 'No changes made (already patched or patterns not found)'
}
