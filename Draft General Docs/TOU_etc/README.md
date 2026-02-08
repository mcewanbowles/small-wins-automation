# Terms of Use & Credits Document

This directory contains the professionally designed Terms of Use and Credits document for Small Wins Studio products.

## Files

- **Terms_of_Use_Credits.html** - Main HTML document with Small Wins Studio branding
  - Features teal borders and headers
  - Uses Comic Sans font for branding consistency
  - Compact 2-page layout (Terms of Use + Credits)
  - Print-ready design optimized for US Letter (8.5" × 11")
  - Each page has its own complete border with footer

- **Terms_of_Use_Credits.pdf** - Professional PDF version ready for distribution
  - Generated from HTML using WeasyPrint
  - Includes Small Wins Studio logo on each page
  - Compact spacing for fewer pages
  - Each page has footer with copyright and page numbers inside the border
  - 2-page document (reduced from 7 pages)

- **generate_pdf.py** - Python script to regenerate PDF from HTML
  - Requires WeasyPrint: `pip install weasyprint`
  - Run with: `python3 generate_pdf.py`

## Design Features

### Branding Elements
- **Color Scheme**: Teal/turquoise (#20B2AA) borders and headers
- **Typography**: Comic Sans MS for consistent branding
- **Logo**: Small Wins Studio logo displayed on each page
- **Layout**: Rounded borders (0.12" radius) matching Small Wins design standards
- **Structure**: Professional compact 2-page format

### Page 1: Terms of Use
- Small Wins Studio logo
- Generic title (no product-specific placeholder)
- Thank you message
- Usage permissions (YOU MAY)
- Usage restrictions (YOU MAY NOT)
- Multiple user license options
- Copyright notice
- TPT credits information
- Follow/support section
- Footer with copyright, PCS license info, and page number

### Page 2: Credits & Attributions
- Small Wins Studio logo
- Product creator credit
- PCS (Picture Communication Symbols) attribution
- Boardmaker® license information
- Educational framework references
- Thank you message
- Footer with copyright, PCS license info, and page number

## Key Improvements

✅ **Compact Design**: Reduced from 7 pages to 2 pages with tighter spacing
✅ **Generic Template**: Removed product-specific placeholders for universal use
✅ **Page Footers**: Each page has its own footer inside the border with:
  - Copyright information
  - PCS license statement
  - Page numbers

## How to Use

### Use the PDF directly
Simply use `Terms_of_Use_Credits.pdf` - it's ready to include in your TPT product downloads.

### Regenerate PDF
If you modify the HTML:
1. Install WeasyPrint: `pip install weasyprint`
2. Run: `python3 generate_pdf.py`
3. New PDF will be generated in the same directory

### View in Browser
Open `Terms_of_Use_Credits.html` in any web browser to preview.

### Customization
The document is now generic and ready to use as-is. To further customize:
1. Edit the HTML file
2. Update `YOUR_STORE_URL` with your TPT store link if desired
3. Adjust the copyright year if needed (currently 2026)
4. Regenerate the PDF using `generate_pdf.py`

## Technical Details

- Page size: US Letter (8.5" × 11")
- Margins: 0.5" on all sides
- Border: 3px teal (#20B2AA) with 0.12" rounded corners on each page
- Compact spacing with 1.5 line height
- Each page is self-contained with header, content, and footer
- CSS print media queries optimize PDF output
- All styling embedded in single HTML file (logo images referenced from assets)
- PDF generated with WeasyPrint for professional output

## Notes

- The design follows Small Wins Studio Design Constitution standards
- Teal color (#20B2AA) matches branding guidelines
- Compact spacing reduces page count while maintaining readability
- Each page has complete border and footer for professional appearance
- Logo images are referenced from `../../assets/branding/logos/`
- Ready to include in TPT product downloads
