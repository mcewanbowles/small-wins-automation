# Freebie Product Specification

## Overview
The **Freebie** is a free "taster" product designed to attract new customers and funnel them to purchase the full product bundle. It provides a complete preview of all differentiation levels and includes usable content.

---

## Purpose
- **Marketing Tool**: Attract potential customers with a free sample
- **Product Preview**: Show all differentiation levels (1-4)
- **Immediate Value**: Provide usable content (not just screenshots)
- **Conversion Funnel**: Drive customers to purchase the full product
- **"Try Before You Buy"**: Give teachers confidence in product quality

---

## Structure

### Complete Freebie Contains:
1. **Cover Page** (1 page)
   - Freebie-specific branding
   - "FREE SAMPLER" prominent display
   - List of what's included
   - Preview of all levels
   - Call-to-action to full product
   
2. **Sample Activity Pages** (4 pages)
   - Page 1 from Level 1 (Errorless)
   - Page 1 from Level 2 (Easy)
   - Page 1 from Level 3 (Medium)
   - Page 1 from Level 4 (Challenge)
   
3. **All Cutout Pages** (8+ pages typically)
   - Cutout pages from Level 1 (usually 2 pages)
   - Cutout pages from Level 2 (usually 2 pages)
   - Cutout pages from Level 3 (usually 2 pages)
   - Cutout pages from Level 4 (usually 2 pages)
   - Makes freebie immediately usable

**Total:** ~13 pages (1 cover + 4 samples + 8 cutouts)

---

## Cover Page Requirements

### Branding Elements
- **Small Wins Studio** logo/name prominently displayed
- **Theme name** clearly visible
- **Product type** identified
- **Copyright notice**: "© 2025 Small Wins Studio. All rights reserved."
- **PCS® License statement**: "PCS® symbols used with active PCS Maker Personal License."

### Visual Design
- **Font**: Comic Sans MS (primary), with fallback to Arial Rounded MT Bold
- **Colors**: 
  - Navy (#1E3A5F) for primary text
  - Teal (#2AAEAE) for accent elements
  - White for text on colored backgrounds
- **Borders**: Rounded rectangle with 0.12" corner radius
- **Margins**: 0.5" on all sides

### Content Sections
1. **Header Banner** (top)
   - Teal background
   - "FREE SAMPLER" in large, bold text
   - Tagline: "Try Before You Buy!"

2. **Title Section**
   - Product title (e.g., "Brown Bear Matching Activities")
   - Subtitle explaining content

3. **"What's Included" Box**
   - Light blue/teal background box with rounded corners
   - Bulleted list of contents:
     - ✓ Sample pages from each level
     - ✓ All cutouts included
     - ✓ Preview of differentiation
     - ✓ Ready to print and use
     - ✓ Introduction to full product

4. **Level Preview Section**
   - Visual display of all 4 levels with color coding:
     - Level 1: Orange (#F4B400) - Errorless
     - Level 2: Blue (#4285F4) - Easy
     - Level 3: Green (#34A853) - Medium
     - Level 4: Purple (#8C06F2) - Challenge

5. **Call-to-Action**
   - Prominent button/banner
   - "Love it? Get the Full Bundle!"
   - Link to TpT store

6. **Footer**
   - Store URL: teacherspayteachers.com/Store/Small-Wins-Studio
   - Copyright and licensing information
   - Small Wins Studio branding

---

## Page Selection Rules

### Sample Pages
- **Always use Page 1** from each level PDF
- This shows the first actual activity students will encounter
- Demonstrates the activity format and visual design
- Shows differentiation in action

### Cutout Pages
- **Include ALL cutout pages** from all levels
- Typically found at the end of each level PDF
- Usually 2 pages per level (cutouts + storage labels)
- Makes the freebie immediately functional
- Teachers can use these with the sample activities

---

## Technical Implementation

### PDF Merging Order
```
1. Cover page (generated)
2. Level 1 PDF - Page 1
3. Level 2 PDF - Page 1
4. Level 3 PDF - Page 1
5. Level 4 PDF - Page 1
6. Level 1 PDF - Cutout pages (last 2 pages)
7. Level 2 PDF - Cutout pages (last 2 pages)
8. Level 3 PDF - Cutout pages (last 2 pages)
9. Level 4 PDF - Cutout pages (last 2 pages)
```

### Dependencies
- **PyPDF2**: For extracting and merging PDF pages
- **reportlab**: For generating the custom cover page
- **Pillow**: For any image processing needs

### File Naming Convention
```
{theme}_{product_type}_freebie.pdf
```
Example: `brown_bear_matching_freebie.pdf`

### Output Location
```
/review_pdfs/{theme}_{product_type}_freebie.pdf
```

---

## Design Constitution Compliance

All freebie covers must comply with the Design Constitution:

### Typography
- **Primary Font**: Comic Sans MS
- **Fallback Font**: Arial Rounded MT Bold
- **Title Size**: 24-28pt (product name)
- **Subtitle Size**: 16-18pt
- **Body Text**: 12-14pt
- **Footer Text**: 9-10pt

### Spacing
- **Page Margins**: 0.5" all sides
- **Element Spacing**: Consistent 20-30px between sections
- **Border Padding**: 10-15px inside border
- **Line Spacing**: 1.2-1.5 for readability

### Colors
- **Navy (#1E3A5F)**: Primary text, borders
- **Teal (#2AAEAE)**: Accent elements, headers
- **White (#FFFFFF)**: Text on colored backgrounds
- **Light Gray (#999999)**: Secondary text, footer

### Borders & Shapes
- **Border Width**: 2-3px
- **Corner Radius**: 0.12" (consistent with Design Constitution)
- **Rounded Rectangles**: For all boxes and containers
- **Border Color**: Navy or Teal depending on context

---

## Quality Standards

### Visual Quality
- **Print-ready**: 300 DPI minimum
- **Professional appearance**: Clean, aligned, consistent
- **Brand consistency**: Matches full product design
- **Accessibility**: High contrast, clear typography

### Content Quality
- **Representative samples**: First page shows typical activity
- **Complete cutouts**: All pieces needed to use the samples
- **Clear instructions**: Cover explains what's included
- **Value demonstration**: Shows product worth

### Marketing Effectiveness
- **Clear value proposition**: Free sample that's immediately usable
- **Level preview**: Shows all differentiation options
- **Professional quality**: Demonstrates product standards
- **Clear CTA**: Guides to full product purchase

---

## Application to Future Products

### Universal Freebie Rules
1. **Always include**: Cover + Page 1 from each level + All cutouts
2. **Cover branding**: Full Small Wins Studio branding and copyright
3. **Design standards**: Follow Design Constitution for all elements
4. **Usability**: Must be functional, not just a preview
5. **Marketing**: Include clear CTA to full product

### Product-Specific Adaptations
- **Different page counts**: Adapt cutout extraction based on product structure
- **Different level counts**: Some products may have 3 or 5 levels
- **Different content types**: Adapt "what's included" list to product type
- **Theme variations**: Adjust colors/images for theme, but keep branding consistent

### Consistency Across Products
- **Same cover layout**: Use consistent template across all freebies
- **Same branding elements**: Logo, copyright, PCS® statement always present
- **Same fonts**: Comic Sans MS across all products
- **Same quality standards**: Professional, print-ready, accessible

---

## Checklist for New Freebies

When creating a freebie for a new product:

- [ ] Cover page includes "FREE SAMPLER" header
- [ ] Product title and theme clearly displayed
- [ ] "What's included" box with complete list
- [ ] All 4 levels shown with color coding
- [ ] Call-to-action to full product
- [ ] Small Wins Studio branding present
- [ ] Copyright notice included
- [ ] PCS® license statement included
- [ ] Comic Sans MS font used
- [ ] Rounded borders (0.12" radius)
- [ ] Proper margins (0.5" all sides)
- [ ] Page 1 extracted from each level
- [ ] All cutout pages included
- [ ] Professional 300 DPI quality
- [ ] File saved to /review_pdfs/
- [ ] Tested and verified usable

---

## Examples

### Matching Product Freebie
- Cover: Brown Bear Matching FREE SAMPLER
- Page 2: Level 1 matching activity (Brown bear, Blue horse, etc.)
- Page 3: Level 2 matching activity (with 1 distractor)
- Page 4: Level 3 matching activity (with 2 distractors)
- Page 5: Level 4 matching activity (with 3 distractors)
- Pages 6-7: Level 1 cutouts + storage label
- Pages 8-9: Level 2 cutouts + storage label
- Pages 10-11: Level 3 cutouts + storage label
- Pages 12-13: Level 4 cutouts + storage label

**Total: 13 pages of usable, professional content**

---

## Success Metrics

A successful freebie should:
- **Convert viewers to customers**: Clear value demonstration
- **Be immediately usable**: Teachers can print and use
- **Represent product quality**: Matches full product standards
- **Show differentiation**: All levels visible
- **Build trust**: Professional, complete, functional

---

## Version History

- **v1.0** (Feb 2026): Initial specification based on successful Brown Bear Matching freebie
- Structure: Cover + Level samples + All cutouts
- Branding: Full Small Wins Studio compliance
- Design: Comic Sans, rounded borders, proper spacing

---

**This specification serves as the design memory for all future freebie products.**
