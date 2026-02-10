#!/usr/bin/env python3
"""Wrapper to run TpT packager with correct paths"""
import os
import sys
from pathlib import Path

# Set up paths relative to repository root
REPO_ROOT = Path(__file__).parent.absolute()
os.chdir(REPO_ROOT)

# Update sys.path
sys.path.insert(0, str(REPO_ROOT))

# Import and patch the paths in create_tpt_packages
import production.generators.create_tpt_packages as tpt_pkg

# Override paths to point to correct locations
tpt_pkg.BASE_DIR = REPO_ROOT
tpt_pkg.SAMPLES_DIR = REPO_ROOT / "final_products" / tpt_pkg.THEME / tpt_pkg.PRODUCT
tpt_pkg.DOCS_DIR = REPO_ROOT / "assets" / "global" / "tpt_support_docs"
tpt_pkg.OUTPUT_DIR = REPO_ROOT / "tpt_packages"

# Run main
if __name__ == "__main__":
    tpt_pkg.main()
