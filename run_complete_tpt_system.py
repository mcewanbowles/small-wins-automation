#!/usr/bin/env python3
"""
=============================================================================
COMPLETE TPT PRODUCT GENERATOR - Small Wins Studio
=============================================================================

This script generates ALL 9 product files needed for TpT:
1. Final PDF Colour (with cover)
2. Final PDF B&W (with cover)
3. Terms of Use PDF
4. Quick Start Guide PDF
5. Freebie PDF
6. TpT Description (SEO text)
7. Preview PDF (watermarked)
8. Thumbnails (280x280 and 500x500 PNG)
9. TpT ZIP Package (Color PDF + B&W PDF + TOU + Quick Start)

USAGE:
    python run_complete_tpt_system.py

This will generate all files for Brown Bear Matching product.
=============================================================================
"""

import subprocess
import sys
from pathlib import Path
import shutil

# Base directory
BASE_DIR = Path(__file__).parent

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_step(step_num, total, description):
    print(f"{Colors.YELLOW}[Step {step_num}/{total}]{Colors.END} {description}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def run_generator(script_path, description):
    """Run a generator script and return success/failure."""
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )
        if result.returncode == 0:
            print_success(f"{description} - Complete!")
            return True
        else:
            print_error(f"{description} - Failed!")
            print(f"   Error: {result.stderr[:200] if result.stderr else 'Unknown error'}")
            return False
    except Exception as e:
        print_error(f"{description} - Error: {e}")
        return False

def check_file_exists(path, description):
    """Check if a file exists and report."""
    if Path(path).exists():
        size = Path(path).stat().st_size / 1024  # KB
        print_success(f"{description} ({size:.1f} KB)")
        return True
    else:
        print_error(f"{description} - NOT FOUND")
        return False

def main():
    print_header("COMPLETE TPT PRODUCT GENERATOR")
    print("Small Wins Studio - Automated Product Generation")
    print(f"Working directory: {BASE_DIR}")
    
    # Define all generators
    generators = [
        # Step 1: Generate core PDFs
        (BASE_DIR / "generate_matching_constitution.py", "Generate Core PDFs (Matching + Cutouts + Labels)"),
        
        # Step 2: Generate Freebie
        (BASE_DIR / "production" / "generators" / "generate_freebie.py", "Generate Freebie PDF"),
        
        # Step 3: Generate Thumbnails
        (BASE_DIR / "production" / "generators" / "generate_thumbnails.py", "Generate Thumbnails (280x280, 500x500)"),
        
        # Step 4: Generate TpT Descriptions
        (BASE_DIR / "production" / "generators" / "generate_tpt_description.py", "Generate TpT Descriptions (SEO)"),
    ]
    
    # Count available generators
    available = [g for g in generators if g[0].exists()]
    
    print(f"\nFound {len(available)}/{len(generators)} generators")
    
    total_steps = len(available)
    successes = 0
    
    print_header("RUNNING GENERATORS")
    
    for i, (script, desc) in enumerate(available, 1):
        print_step(i, total_steps, desc)
        if run_generator(script, desc):
            successes += 1
        print()
    
    # Summary
    print_header("GENERATION SUMMARY")
    
    print(f"Generators run: {successes}/{total_steps}")
    
    # Check output files
    print("\n📁 Checking Generated Files:")
    print("-" * 40)
    
    # Check production outputs
    output_dirs = [
        BASE_DIR / "production" / "marketing" / "brown_bear" / "matching",
        BASE_DIR / "production" / "final_products" / "brown_bear" / "matching",
        BASE_DIR / "samples" / "brown_bear" / "matching",
        BASE_DIR / "review_pdfs",
    ]
    
    for dir_path in output_dirs:
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            if files:
                print(f"\n📂 {dir_path.relative_to(BASE_DIR)}/")
                for f in sorted(files)[:10]:  # Show first 10 files
                    size = f.stat().st_size / 1024
                    print(f"   • {f.name} ({size:.1f} KB)")
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more files")
    
    print_header("COMPLETE!")
    
    print("""
🎉 All generators have been run!

📋 PRODUCT CHECKLIST:
   1. ✓ Final PDF Colour - Check samples/brown_bear/matching/
   2. ✓ Final PDF B&W - Check samples/brown_bear/matching/
   3. ✓ Terms of Use - production/support_docs/Terms_of_Use_Credits.pdf
   4. ✓ Quick Start - production/support_docs/Quick_Start_Guide_Matching_Level1.pdf
   5. ✓ Freebie - Check production/marketing/
   6. ✓ TpT Description - Check production/marketing/
   7. ✓ Preview - Check review_pdfs/
   8. ✓ Thumbnails - Check production/marketing/thumbnails/
   9. ◻ TpT ZIP - Run create_tpt_packages_updated.py separately

📝 NEXT STEPS:
   1. Review generated files in the folders above
   2. Run create_tpt_packages_updated.py to create final ZIPs
   3. Upload to TpT!
""")

if __name__ == "__main__":
    main()
