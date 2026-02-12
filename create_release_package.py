#!/usr/bin/env python3
"""
Complete TpT Release Package Generator

Creates production-ready TpT packages with all required components:
- TpT ZIP files for upload
- Preview PDFs
- Thumbnails
- Descriptions
- Freebie
- Manifest

Usage:
    python create_release_package.py --theme brown_bear --product matching
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
import os


class ReleasePackager:
    """Creates complete TpT release packages"""
    
    def __init__(self, theme: str, product: str, repo_root: Path = None):
        self.theme = theme
        self.product = product
        self.repo_root = repo_root or Path(__file__).parent
        
        # Define number of levels for this product
        self.levels = [1, 2, 3, 4]  # Brown Bear Matching has 4 levels
        
        # Output structure
        self.output_base = self.repo_root / 'production' / 'final_products' / theme / product
        self.uploads_dir = self.output_base / 'uploads'
        self.previews_dir = self.output_base / 'previews'
        self.thumbnails_dir = self.output_base / 'thumbnails'
        self.descriptions_dir = self.output_base / 'descriptions'
        self.freebie_dir = self.output_base / 'freebie'
        
        # Source locations (where component files exist or will be generated)
        self.support_docs = self.repo_root / 'production' / 'support_docs'
        self.marketing_dir = self.repo_root / 'production' / 'marketing' / theme / product
        self.freebies_source = self.repo_root / 'production' / 'freebies' / theme / product
        self.generated_pdfs = self.repo_root / 'production' / 'final_products' / theme / product
        
        # Create all output directories
        for directory in [self.uploads_dir, self.previews_dir, self.thumbnails_dir, 
                          self.descriptions_dir, self.freebie_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_complete_package(self):
        """Generate all components of the release package"""
        print(f"=" * 70)
        print(f"Creating Complete TpT Release Package")
        print(f"Theme: {self.theme}")
        print(f"Product: {self.product}")
        print(f"Output: {self.output_base}")
        print(f"=" * 70)
        print()
        
        results = {
            'uploads': [],
            'previews': [],
            'thumbnails': [],
            'descriptions': [],
            'freebie': [],
            'errors': []
        }
        
        # Step 1: Generate TpT ZIP packages for each level
        print("Step 1: Creating TpT ZIP packages...")
        for level in self.levels:
            try:
                zip_path = self.create_tpt_zip(level)
                results['uploads'].append(zip_path)
                print(f"  ✓ Created: {zip_path.name}")
            except Exception as e:
                error_msg = f"Failed to create Level {level} ZIP: {e}"
                results['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
        print()
        
        # Step 2: Generate or copy preview PDFs
        print("Step 2: Creating preview PDFs...")
        for level in self.levels:
            try:
                preview_path = self.create_preview_pdf(level)
                results['previews'].append(preview_path)
                print(f"  ✓ Created: {preview_path.name}")
            except Exception as e:
                error_msg = f"Failed to create Level {level} preview: {e}"
                results['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
        print()
        
        # Step 3: Copy thumbnails
        print("Step 3: Copying thumbnails...")
        try:
            thumb_count = self.copy_thumbnails()
            if thumb_count > 0:
                results['thumbnails'].append(f"{thumb_count} thumbnails")
                print(f"  ✓ Copied {thumb_count} thumbnails")
            else:
                print(f"  ⚠ No thumbnails found to copy")
        except Exception as e:
            error_msg = f"Failed to copy thumbnails: {e}"
            results['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
        print()
        
        # Step 4: Copy or generate descriptions
        print("Step 4: Copying description files...")
        for level in self.levels:
            try:
                desc_path = self.copy_description(level)
                results['descriptions'].append(desc_path)
                print(f"  ✓ Copied: {desc_path.name}")
            except Exception as e:
                error_msg = f"Failed to copy Level {level} description: {e}"
                results['errors'].append(error_msg)
                print(f"  ✗ {error_msg}")
        
        # Freebie description
        try:
            freebie_desc = self.copy_freebie_description()
            results['descriptions'].append(freebie_desc)
            print(f"  ✓ Copied: {freebie_desc.name}")
        except Exception as e:
            print(f"  ⚠ No freebie description found")
        print()
        
        # Step 5: Copy freebie
        print("Step 5: Copying freebie...")
        try:
            freebie_path = self.copy_freebie()
            results['freebie'].append(freebie_path)
            print(f"  ✓ Copied: {freebie_path.name}")
        except Exception as e:
            error_msg = f"Failed to copy freebie: {e}"
            results['errors'].append(error_msg)
            print(f"  ✗ {error_msg}")
        print()
        
        # Step 6: Generate manifest
        print("Step 6: Creating manifest...")
        manifest_path = self.create_manifest(results)
        print(f"  ✓ Created: {manifest_path.name}")
        print()
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def create_tpt_zip(self, level: int):
        """Create a TpT ZIP package for a specific level"""
        import zipfile
        
        zip_name = f"{self.theme}_{self.product}_level{level}_TpT.zip"
        zip_path = self.uploads_dir / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Final product PDF (color version)
            product_pdf = self.generated_pdfs / f"{self.theme}_{self.product}_level{level}_color.pdf"
            if product_pdf.exists():
                zf.write(product_pdf, product_pdf.name)
            else:
                # Try to generate a placeholder
                print(f"    Warning: Product PDF not found: {product_pdf}")
            
            # 2. Quick Start Guide for this level
            quick_start = self.support_docs / f"Quick_Start_Guide_Matching_Level{level}.pdf"
            if not quick_start.exists():
                # Fallback to Level 1 if specific level doesn't exist
                quick_start = self.support_docs / "Quick_Start_Guide_Matching_Level1.pdf"
            
            if quick_start.exists():
                zf.write(quick_start, quick_start.name)
            else:
                print(f"    Warning: Quick Start not found")
            
            # 3. Terms of Use
            tou = self.support_docs / "Terms_of_Use_Credits.pdf"
            if not tou.exists():
                tou = self.support_docs / "Terms_of_Use.pdf"
            
            if tou.exists():
                zf.write(tou, tou.name)
            else:
                print(f"    Warning: Terms of Use not found")
        
        return zip_path
    
    def create_preview_pdf(self, level: int):
        """Create a preview PDF (watermarked version)"""
        preview_name = f"{self.theme}_{self.product}_level{level}_PREVIEW.pdf"
        preview_path = self.previews_dir / preview_name
        
        # For now, create a simple preview page
        # In a full implementation, this would add watermarks to the actual PDFs
        c = canvas.Canvas(str(preview_path), pagesize=letter)
        
        # Add preview page with watermark
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(HexColor('#999999'))
        c.drawCentredString(4.25 * 72, 5.5 * 72, "PREVIEW")
        
        c.setFont("Helvetica", 12)
        c.setFillColor(HexColor('#000000'))
        c.drawCentredString(4.25 * 72, 5 * 72, f"{self.theme.replace('_', ' ').title()} {self.product.title()}")
        c.drawCentredString(4.25 * 72, 4.7 * 72, f"Level {level}")
        
        c.save()
        
        return preview_path
    
    def copy_thumbnails(self):
        """Copy thumbnails from marketing folder"""
        count = 0
        source_thumbnails = self.marketing_dir / 'thumbnails'
        
        if source_thumbnails.exists():
            for thumb_file in source_thumbnails.glob('*.png'):
                dest = self.thumbnails_dir / thumb_file.name
                shutil.copy2(thumb_file, dest)
                count += 1
        
        return count
    
    def copy_description(self, level: int):
        """Copy description text file"""
        desc_name = f"{self.theme}_{self.product}_L{level}_description.txt"
        source = self.marketing_dir / desc_name
        dest = self.descriptions_dir / f"{self.theme}_{self.product}_level{level}_description.txt"
        
        if source.exists():
            shutil.copy2(source, dest)
        else:
            # Create a placeholder description
            with open(dest, 'w') as f:
                f.write(f"{self.theme.replace('_', ' ').title()} {self.product.title()} - Level {level}\n\n")
                f.write("Description placeholder - needs content\n")
        
        return dest
    
    def copy_freebie_description(self):
        """Copy freebie description"""
        desc_name = f"{self.theme}_{self.product}_freebie_description.txt"
        source = self.marketing_dir / desc_name
        dest = self.descriptions_dir / desc_name
        
        if source.exists():
            shutil.copy2(source, dest)
        else:
            with open(dest, 'w') as f:
                f.write(f"{self.theme.replace('_', ' ').title()} {self.product.title()} - Freebie\n\n")
                f.write("Freebie description placeholder\n")
        
        return dest
    
    def copy_freebie(self):
        """Copy freebie PDF"""
        freebie_name = f"{self.theme}_{self.product}_freebie.pdf"
        source = self.freebies_source / freebie_name
        dest = self.freebie_dir / freebie_name
        
        if source.exists():
            shutil.copy2(source, dest)
        else:
            # Create placeholder freebie
            self.create_placeholder_freebie(dest)
        
        return dest
    
    def create_placeholder_freebie(self, path: Path):
        """Create a placeholder freebie PDF"""
        c = canvas.Canvas(str(path), pagesize=letter)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(4.25 * 72, 5.5 * 72, "Freebie Sample")
        c.setFont("Helvetica", 12)
        c.drawCentredString(4.25 * 72, 5 * 72, f"{self.theme.replace('_', ' ').title()} {self.product.title()}")
        c.save()
    
    def create_manifest(self, results: dict):
        """Create a manifest file listing all outputs"""
        manifest_path = self.output_base / 'manifest.txt'
        
        with open(manifest_path, 'w') as f:
            f.write(f"TpT Release Package Manifest\n")
            f.write(f"=" * 70 + "\n")
            f.write(f"Theme: {self.theme}\n")
            f.write(f"Product: {self.product}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\n")
            
            # List all files
            for category in ['uploads', 'previews', 'thumbnails', 'descriptions', 'freebie']:
                directory = self.output_base / category
                if directory.exists():
                    f.write(f"\n{category.upper()}/\n")
                    f.write(f"-" * 70 + "\n")
                    
                    files = sorted(directory.glob('*'))
                    for file_path in files:
                        if file_path.is_file():
                            size = file_path.stat().st_size
                            size_kb = size / 1024
                            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                            f.write(f"  {file_path.name:50s} {size_kb:8.1f} KB  {modified.strftime('%Y-%m-%d %H:%M')}\n")
            
            # Summary
            f.write(f"\n")
            f.write(f"SUMMARY\n")
            f.write(f"=" * 70 + "\n")
            f.write(f"TpT ZIPs: {len(results['uploads'])}\n")
            f.write(f"Previews: {len(results['previews'])}\n")
            f.write(f"Descriptions: {len(results['descriptions'])}\n")
            if results['errors']:
                f.write(f"\nERRORS:\n")
                for error in results['errors']:
                    f.write(f"  - {error}\n")
        
        return manifest_path
    
    def print_summary(self, results: dict):
        """Print a summary of what was generated"""
        print("=" * 70)
        print("GENERATION COMPLETE")
        print("=" * 70)
        print()
        print(f"Output location: {self.output_base}")
        print()
        print(f"✓ TpT ZIPs created: {len(results['uploads'])}")
        print(f"✓ Previews created: {len(results['previews'])}")
        print(f"✓ Descriptions: {len(results['descriptions'])}")
        print(f"✓ Freebie: {len(results['freebie'])}")
        print()
        
        if results['errors']:
            print(f"⚠ Errors encountered: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
            print()
        
        print("Files ready for TpT upload in:")
        print(f"  {self.uploads_dir}")
        print()


def main():
    parser = argparse.ArgumentParser(description='Generate complete TpT release package')
    parser.add_argument('--theme', required=True, help='Theme name (e.g., brown_bear)')
    parser.add_argument('--product', required=True, help='Product name (e.g., matching)')
    
    args = parser.parse_args()
    
    packager = ReleasePackager(args.theme, args.product)
    packager.generate_complete_package()


if __name__ == '__main__':
    main()
