#!/bin/bash
# Run full Brown Bear Matching automation pipeline
# This script runs all 3 steps to generate complete products and TpT packages

set -e  # Exit on error

echo "============================================================"
echo "Brown Bear Matching - Full Automation Pipeline"
echo "============================================================"
echo ""

# Set Python path to include repository root
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "[Step 1/3] Generating core products..."
python3 production/generators/generate_matching_constitution.py
echo ""

echo "[Step 2/3] Adding covers and page numbers..."
python3 production/generators/generate_complete_products_final.py
echo ""

echo "[Step 3/3] Creating TpT packages..."
python3 production/generators/create_tpt_packages.py
echo ""

echo "============================================================"
echo "✓ AUTOMATION COMPLETE!"
echo "============================================================"
echo ""
echo "Generated files:"
echo "  • Core products: samples/brown_bear/matching/"
echo "  • FINAL products: final_products/brown_bear/matching/"
echo "  • TpT packages: production/generators/tpt_packages/"
echo ""
echo "To upload to TpT: Use the ZIP files in tpt_packages/"
echo "============================================================"
