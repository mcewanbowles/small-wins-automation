#!/usr/bin/env python3
"""
PDF Generation Script for Quick Start Guides
Converts HTML to PDF using WeasyPrint
"""

from weasyprint import HTML
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Input and output files
html_file = os.path.join(script_dir, 'Quick_Start_Guide_Matching_Level1.html')
pdf_file = os.path.join(script_dir, 'Quick_Start_Guide_Matching_Level1.pdf')

# Generate PDF
print(f"Generating PDF from {html_file}...")
HTML(filename=html_file).write_pdf(pdf_file)
print(f"PDF created successfully: {pdf_file}")

# Get file size
file_size = os.path.getsize(pdf_file)
print(f"PDF size: {file_size / 1024:.1f} KB ({file_size:,} bytes)")
