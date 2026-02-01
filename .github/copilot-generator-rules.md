# Copilot Generator Rules

These rules tell GitHub Copilot how to execute all Small Wins Studio generators.  
This file works alongside the Design Constitution and Master Fix File.

---

## 1. General Rules
- Always follow the Design Constitution and Master Fix File.
- Never guess icon sizes, spacing, or layout — use the Constitution.
- Always regenerate both color and BW versions.
- Always overwrite existing files.

---

## 2. Running a Generator
When asked to run a generator:
1. Locate the generator script in `/generators/{product_type}/`.
2. Load icons from `/assets/{theme}/icons/`.
3. Apply all layout rules from the Design Constitution.
4. Apply all corrections from the Master Fix File.
5. Generate:
   - Level 1–4 pages
   - Cutout pages
   - Storage labels
6. Export PDFs to:
   `/samples/{theme}/{product_type}/`

---

## 3. File Naming
- `{theme}_{product_type}_color.pdf`
- `{theme}_{product_type}_bw.pdf`

---

## 4. Commit Rules
- Commit all regenerated files.
- Include a clear commit message:
  “Regenerated {product_type} for {theme} using Design Constitution.”

---

## 5. Error Handling
If a file is missing, incomplete, or inconsistent:
- Regenerate it.
- Apply Constitution rules.
- Re-run the generator.
