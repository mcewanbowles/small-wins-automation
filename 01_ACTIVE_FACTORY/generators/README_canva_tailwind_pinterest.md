# Canva + Tailwind + Pinterest Automation (Starter)

## 1) Prepare Canva Autofill CSV
Use:
- `production/generators/templates/canva_autofill_input_template.csv`

Conventions:
- `template_id`: Canva Brand Template ID (or provide `CANVA_BRAND_TEMPLATE_ID` env var)
- `text__FIELD_NAME`: maps to Canva text dataset fields
- `image__FIELD_NAME`: maps to Canva image dataset fields (expects Canva `asset_id`)
- keep marketing metadata columns (`title`, `description`, `destination_url`, `board`, `image_path`) for downstream Tailwind usage

## 2) Run Canva Autofill in background-safe mode
Dry run (no API calls):

```powershell
python -m production.generators.canva_autofill_bulk --input-csv production/generators/templates/canva_autofill_input_template.csv --dry-run
```

Live run (create jobs):

```powershell
$env:CANVA_ACCESS_TOKEN="<token>"
$env:CANVA_BRAND_TEMPLATE_ID="<optional-default-template-id>"
python -m production.generators.canva_autofill_bulk --input-csv production/generators/templates/canva_autofill_input_template.csv --poll --poll-timeout 240
```

Output:
- `production/marketing/canva_autofill_results.csv` (job statuses + design URLs)

## 3) Generate Pinterest templates + Tailwind CSV from existing product outputs
Per-product (already wired in package scripts via `ensure_standard_product_assets`):
- creates `marketing/pins_1000x1500/*.png`
- creates `marketing/tailwind_upload.csv`

Manual backfill across all products:

```powershell
python -m production.generators.generate_pinterest_pins --mode backfill-standard
python -m production.generators.generate_pinterest_pins --mode backfill-tailwind-csv --manifest-out production/marketing/tailwind/tailwind_pin_manifest.csv
```

## 4) Tailwind import flow
- Import `tailwind_upload.csv` (or global `tailwind_pin_manifest.csv`) into Tailwind
- Map columns:
  - `image_path` -> Pin image
  - `title` -> Pin title
  - `description` -> Pin description
  - `destination_url` -> Target URL
  - `board` -> Board

## 5) Pinterest publishing flow
- If scheduling via Tailwind: publish from Tailwind queues/board assignments
- If direct Pinterest upload: use generated pin images in each product `marketing/pins_1000x1500/`
