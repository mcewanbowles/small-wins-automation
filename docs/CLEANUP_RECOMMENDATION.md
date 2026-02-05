# 🧹 Cleanup Decision — CONFIRMED ✅

## User Decisions (February 2026)

### 1. Active Generators (KEEP these only)
- ✅ **Matching** — Final stage, working
- ✅ **Find + Cover** — Final stage, working  
- ✅ **AAC** — Final stage, working
- ⚠️ **Bingo** — Has problems, needs fixing later

### 2. Old Generators 
**Decision: DELETE** (not archive)
- User has other versions saved elsewhere
- Clean repo is preferred

### 3. Test Theme
- **Brown Bear** — Primary test theme for all generators

---

## Current Clean Structure

```
generators/
├── matching/       # ✅ Active
├── find_cover/     # ✅ Active
├── aac/            # ✅ Active
```

No `deprecated_generators/` folder — old code was deleted per user request.

---

## Next Steps

1. ✅ Clean folder structure in place
2. ⏳ Copy working generator code from `copilot/build-python-automation-system`:
   - `matching_cards.py` → `generators/matching/`
   - `find_cover.py` → `generators/find_cover/`
   - `aac_book_board.py` → `generators/aac/`
3. ⏳ Test with Brown Bear theme
4. 🔜 Fix Bingo generator later (once core 3 are stable)

---

## Products Roadmap

Goal: **25 products per theme**

| Status | Product Type |
|--------|--------------|
| ✅ Final | Matching |
| ✅ Final | Find + Cover |
| ✅ Final | AAC |
| ⚠️ Issues | Bingo |
| ❌ Deleted | All others (to be rebuilt later if needed) |
