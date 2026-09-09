# 01_ACTIVE_FACTORY — FROZEN ARCHIVE

**Status: FROZEN — Do not add new products here. Do not delete.**

This directory contains legacy outputs from the previous architecture.
It is kept as a reference archive only.

## What's here

- `products/` — 63 legacy topic directories with mixed old-architecture outputs
  (task cards, sequencing, matching, quick checks, family packs, cue cards, lanyards, etc.)
- `pipeline_products/` — Legacy enriched drafts and reference materials
- `bundles/` — Legacy bundle packages
- `topics/` — Legacy topic source data

## Where things live now

- **Dignity products** → `Dignity/products/`
- **Dignity adapters** → `Dignity/adapters/`
- **Dignity topic JSONs** → `Dignity/topics/`
- **Dignity config** → `Dignity/config/`
- **Dignity guardrails** → `Dignity/GUARDRAILS.md`
- **Book companions** → `Studioforge/OUTPUT/` (unchanged, separate product line)

## Why it's frozen

The old architecture mixed legacy products (task cards, sequencing, matching,
quick checks, family packs) with the new 9-product architecture. This made it
difficult to distinguish current from obsolete outputs.

The `Dignity/` folder is a clean home with ONLY the 9-product architecture.
This directory remains as a historical reference and backup.

## When it can be deleted

Only after:
1. All 63 topics have been migrated to the Dignity architecture
2. All enriched topic JSONs have been moved to `Dignity/topics/`
3. The user has verified no needed content is missing
4. A full backup has been made

Until then, treat as read-only reference.
