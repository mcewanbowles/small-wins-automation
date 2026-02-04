# Product Type Standards

This document defines the standard structure and requirements for all Small Wins Studio product generators.

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

### 3. TpT Listing Package

Each TpT listing = ONE ZIP file containing:
- All PDF files for the product (color + B&W)
- Terms of Use (TOU) document
- Credits page
- Optional: Thumbnail/preview images

ZIP naming: `<theme>_<product_type>.zip`

### 4. Required Outputs

Every generator must produce:
| Output | Required |
|--------|----------|
| Color PDF(s) | ✅ Yes |
| B&W PDF(s) | ✅ Yes |
| Storage Labels | ✅ Yes |
| Thumbnail | Optional |
| Preview Image | Optional |

### 5. Differentiation Levels

Where applicable, products should support multiple difficulty levels:
- Level 1: Errorless (scaffolded)
- Level 2: Easy
- Level 3: Medium
- Level 4: Hard

### 6. Naming Conventions

File naming pattern:
```
<theme>_<product_type>_<variant>_<color_mode>.pdf
```

Examples:
- `brown_bear_matching_level1_color.pdf`
- `brown_bear_matching_level1_bw.pdf`
- `brown_bear_find_cover_level2_color.pdf`

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
6. Follow all standards above
7. Test with at least one theme before merging

## Design Resources

- `/design/Design-Constitution.md` — Universal design standards
- `/design/product_specs/` — Product-specific specifications
- `/docs/exports-workflow.md` — Export conventions

## Deprecated Generators

Generators that are no longer active are moved (not deleted) to:
```
deprecated_generators/
```

See `/deprecated_generators/README.md` for details.
