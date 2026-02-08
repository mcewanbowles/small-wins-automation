# Sorting Mat Improvements Plan

## Based on Design Constitution Review

### Current State
The Universal Sorting Toolkit was created with basic functionality but needs alignment with Small Wins Studio Design Constitution and Master Product Specification standards.

### Issues Identified

#### 1. Page Format ❌
**Current:** A4 Landscape (297mm × 210mm)  
**Required:** US Letter Portrait (8.5" × 11")  
**Design Constitution §1:** All products must use US Letter size

#### 2. Border & Margins ❌
**Current:** No visible border, 12mm margins  
**Required:** 
- 0.5" margins on all sides
- 2-3px rounded rectangle border
- 0.12" corner radius
- Border contains all content

#### 3. Header Area (Above Border) ❌
**Current:** Not implemented  
**Required:**
- Pack code (left): "SWS-SORT" in grey #666666, 8pt
- Page numbers (right): "Page X/Y" in grey #666666, 8pt  
- Brand (center): "Small Wins Studio" in grey #999999, 10pt

#### 4. Accent Stripe ❌
**Current:** Simple title area  
**Required:**
- Height: 0.5" - 0.6"
- Rounded corners: 0.12"
- Padding from border: 0.1" - 0.15" on all sides
- Background: Theme color (e.g., warm orange/teal for sorting)
- Title: Arial Rounded MT Bold, 18pt, Navy
- Subtitle: Arial, 12pt, Dark Grey
- Centered vertically and horizontally

#### 5. Footer (Inside Border) ❌
**Current:** Simple brand text  
**Required:**
- Format: "© 2025 Small Wins Studio. All rights reserved. • PCS® symbols used with active PCS Maker Personal License."
- Position: Inside border, bottom
- Font: Grey #999999, 8pt
- Include Small Wins Studio star logo

#### 6. AAC Edge Strip ⚠️
**Current:** Good implementation but needs adjustment for portrait
- Works well but needs to fit portrait orientation
- May need to reduce from 16 to 12-14 buttons to fit better

#### 7. Sorting Boxes ⚠️
**Current:** Landscape layout  
**Needed:** Redesign for portrait orientation
- 2-way: Side-by-side still works but adjust proportions
- 3-way: Three columns still works
- Yes/No: Adjust for portrait

### Implementation Priority

**Phase 1: Core Layout** (Essential)
1. ✅ Change to US Letter Portrait
2. ✅ Add proper margins (0.5")
3. ✅ Add border with rounded corners
4. ✅ Add header area (pack code, page #, brand)
5. ✅ Add proper footer with copyright

**Phase 2: Accent Stripe** (High Priority)
6. ✅ Implement accent stripe
7. ✅ Center title/subtitle in stripe
8. ✅ Add rounded corners and padding

**Phase 3: Sorting Area** (High Priority)
9. ✅ Adjust 2-way sorting for portrait
10. ✅ Adjust 3-way sorting for portrait
11. ✅ Adjust Yes/No sorting for portrait

**Phase 4: AAC Strip** (Medium Priority)
12. ✅ Adjust AAC button layout for portrait
13. ✅ May reduce to 12 buttons (6 top + 6 bottom)
14. ✅ Ensure icons load and display properly

**Phase 5: Branding** (Medium Priority)
15. ✅ Add Small Wins Studio logo to footer
16. ✅ Ensure all branding elements present
17. ✅ Apply consistent theme colors

**Phase 6: Polish** (Low Priority)
18. ✅ Add instruction page with better formatting
19. ✅ Ensure all pages consistent
20. ✅ Test with various categories

### Design Specifications Reference

**From Design Constitution:**
- Page size: US Letter (8.5" × 11")
- Margins: 0.5" on all sides
- Border: 2–3 px rounded rectangle, 0.12" corner radius
- Accent stripe: 0.5"–0.6" height, rounded corners
- Footer format: Standard copyright with PCS attribution

**From Master Product Specification:**
- Level colors (if applicable): Orange, Blue, Green, Purple
- Branding must be consistent
- All products follow same structure

### Recommended Approach

1. Create new version of generator with all improvements
2. Keep current version as reference
3. Test thoroughly with multiple category sets
4. Compare before/after PDFs
5. Ensure AAC functionality preserved
6. Verify all branding elements present

### Success Criteria

✅ Follows Design Constitution page structure  
✅ Uses US Letter Portrait format  
✅ Has proper borders and margins  
✅ Accent stripe properly implemented  
✅ Footer matches standard format  
✅ AAC buttons functional and visible  
✅ Sorting areas work in portrait  
✅ All branding elements present  
✅ Professional, consistent appearance  
✅ Maintains educational value  

### Notes

- This is a significant refactor, not minor tweaks
- Will improve professionalism and consistency
- Aligns with all other Small Wins Studio products
- May require adjustment of AAC button count
- Portrait orientation better for standard filing

### Timeline

**Estimated:** 2-3 hours for complete implementation  
**Testing:** 30 minutes  
**Documentation:** 30 minutes  
**Total:** ~4 hours

### Files to Modify

- `generators/universal_sorting/universal_sorting_aac.py` - Main generator
- `OUTPUT/sorting/` - Regenerate all PDFs
- `generators/universal_sorting/README.md` - Update documentation

### New Features to Add

1. Pack code generation
2. Page numbering system
3. Border drawing function
4. Accent stripe function
5. Proper footer with logo
6. Theme color system
7. Better instruction page

---

**Status:** Plan created, ready for implementation  
**Next Step:** Begin Phase 1 implementation  
**Owner:** Development team  
**Review:** Design lead approval needed  
