# Terms of Use & Credits Document

This directory contains the professionally designed Terms of Use and Credits document for Small Wins Studio products.

## Files

- **Terms_of_Use_Credits.html** - Main HTML document with Small Wins Studio branding
  - Features teal borders and headers
  - Uses Comic Sans font for branding consistency
  - Two-page layout (Terms of Use + Credits)
  - Print-ready design optimized for US Letter (8.5" × 11")

- **Terms_of_Use_Credits.pdf** - Professional PDF version ready for distribution
  - Generated from HTML using WeasyPrint
  - Includes Small Wins Studio logo on each page
  - Optimized spacing and layout for professional appearance
  - 7-page document with proper page breaks

- **generate_pdf.py** - Python script to regenerate PDF from HTML
  - Requires WeasyPrint: `pip install weasyprint`
  - Run with: `python3 generate_pdf.py`

## Design Features

### Branding Elements
- **Color Scheme**: Teal/turquoise (#20B2AA) borders and headers
- **Typography**: Comic Sans MS for consistent branding
- **Logo**: Small Wins Studio logo displayed on each page
- **Layout**: Rounded borders (0.12" radius) matching Small Wins design standards
- **Structure**: Professional multi-page format with generous spacing

### Page 1: Terms of Use
- Small Wins Studio logo
- Thank you message
- Usage permissions (YOU MAY)
- Usage restrictions (YOU MAY NOT)
- Multiple user license options
- Copyright notice
- TPT credits information
- Follow/support section

### Pages 2-7: Credits & Attributions
- Small Wins Studio logo
- Product creator credit
- PCS (Picture Communication Symbols) attribution
- Boardmaker® license information
- Educational framework references
- Thank you message

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
To customize for a specific product:
1. Edit the HTML file
2. Replace `[YOUR PRODUCT TITLE]` with your actual product title
3. Update `YOUR_STORE_URL` with your TPT store link
4. Adjust the copyright year if needed (currently 2026)
5. Regenerate the PDF using `generate_pdf.py`

## Technical Details

- Page size: US Letter (8.5" × 11")
- Margins: 0.5" on all sides
- Border: 3px teal (#20B2AA) with 0.12" rounded corners
- Responsive design for both screen and print
- CSS print media queries optimize PDF output
- All styling embedded in single HTML file (no external dependencies except logo image)
- PDF generated with WeasyPrint for professional output

## Notes

- The design follows Small Wins Studio Design Constitution standards
- Teal color (#20B2AA) matches branding guidelines
- Rounded corners and professional spacing throughout
- Logo images are referenced from `../../assets/branding/logos/`
- Ready to include in TPT product downloads
