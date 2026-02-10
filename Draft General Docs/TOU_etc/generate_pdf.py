#!/usr/bin/env python3
"""
Generate PDF from HTML for Small Wins Studio Terms of Use & Credits
Uses WeasyPrint for professional PDF output with proper spacing and branding
"""

from weasyprint import HTML, CSS
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Input and output paths
html_file = os.path.join(script_dir, 'Terms_of_Use_Credits.html')
pdf_file = os.path.join(script_dir, 'Terms_of_Use_Credits.pdf')

print("🎨 Small Wins Studio - PDF Generator")
print("=" * 50)
print(f"📄 Input HTML: {html_file}")
print(f"📑 Output PDF: {pdf_file}")
print()

# Additional CSS for better PDF output
extra_css = CSS(string="""
    @page {
        size: letter;
        margin: 0.5in;
    }
    
    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
""")

try:
    # Generate PDF
    print("⚙️  Generating PDF...")
    HTML(filename=html_file, base_url=script_dir).write_pdf(
        pdf_file,
        stylesheets=[extra_css]
    )
    
    # Check file size
    file_size = os.path.getsize(pdf_file)
    file_size_kb = file_size / 1024
    
    print(f"✅ PDF generated successfully!")
    print(f"📦 File size: {file_size_kb:.1f} KB")
    print(f"💾 Saved to: {pdf_file}")
    print()
    print("🎉 Done! Your professional Terms of Use & Credits PDF is ready.")
    
except Exception as e:
    print(f"❌ Error generating PDF: {e}")
    raise
