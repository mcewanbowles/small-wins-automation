# Product Type Standards

This document defines the standard structure and requirements for all Small Wins Studio product generators.

> **📋 Master Specification:** See `/design/Master-Product-Specification.md` for the complete requirements including branding, level color-coding, required outputs, and TpT packaging.

## Reference Implementations

The **`matching`** and **`find_cover`** generators are the reference models. All new product types MUST follow their patterns.

## Required Standards for All Generators

### 1. Config-Driven Design

Every generator must:
- Load theme settings from `/themes/<theme>.json`
- Support a product-specific configuration key (e.g., `"matching"`, `"find_cover"`)
- Have no hardcoded theme values

Example theme config entry:
```json
{
  "matching": {
    "levels": ["errorless", "identical", "field_of_6"]
  },
  "find_cover": {
    "grid_size": "4x4",
    "levels": ["errorless", "mixed", "field_of_6", "cut_paste"]
  }
}
```

### 2. Export Folder Structure

All outputs must go to:
```
exports/<date>_<theme>/<product_type>/
```

Example:
```
exports/20260205_brown_bear/matching/
exports/20260205_brown_bear/find_cover/
exports/20260205_brown_bear/aac/
```

### 3. Required Outputs Per Level

Every level must produce (see Master-Product-Specification.md for details):

| Output | Color | B&W | Required |
|--------|-------|-----|----------|
| Activity Pages | ✅ | ✅ | Yes |
| Storage Labels | ✅ | ✅ | Yes |
| Cover Page | ✅ | — | Yes |
| Thumbnail PNG | ✅ | — | Yes |
| Preview Images | ✅ | — | Yes |
| Instructions | ✅ | — | Yes |
| TpT ZIP | — | — | Yes |
| SEO Text | — | — | Yes |

### 4. Level Color Coding

| Level | Name | Color |
|-------|------|-------|
| Level 1 | Errorless | 🟢 Green |
| Level 2 | Easy | 🔵 Blue |
| Level 3 | Medium | 🟡 Yellow/Orange |
| Level 4 | Hard | 🔴 Red/Pink |

### 5. Naming Conventions

File naming pattern:
```
<theme>_<product_type>_<level>_<variant>_<color_mode>.pdf
```

Examples:
- `brown_bear_matching_level1_activity_color.pdf`
- `brown_bear_matching_level1_activity_bw.pdf`
- `brown_bear_matching_level1_storage_color.pdf`

### 6. Special Packs

After all levels are complete, also generate:

| Pack | Purpose |
|------|---------|
| **Freebie** | 1 page from each level (3-4 pages) to drive bundle sales |
| **Bundle** | All levels combined at discount |

## Active Generators

| Generator | Location | Status |
|-----------|----------|--------|
| Matching | `generators/matching/` | ✅ Active |
| Find + Cover | `generators/find_cover/` | ✅ Active |
| AAC | `generators/aac/` | ✅ Active |

## Creating New Product Types

When creating a new product type:

1. **Copy structure from `matching` or `find_cover`**
2. Create folder: `generators/<new_product>/`
3. Add README.md documenting the generator
4. Add product-specific spec to `/design/product_specs/<product>.md`
5. Ensure config key exists in theme JSON files
6. Follow Master-Product-Specification.md
7. Test with Brown Bear theme before merging

## Design Resources

- `/design/Master-Product-Specification.md` — **Complete product requirements**
- `/design/Design-Constitution.md` — Universal design standards
- `/design/product_specs/` — Product-specific specifications
- `/docs/exports-workflow.md` — Export conventions
