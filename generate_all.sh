#!/bin/bash
# Master Generator - Run Complete TpT Product Pipeline
# Generates everything needed for a TpT listing in one command!

set -e  # Exit on error

echo ""
echo "🎨 ========================================="
echo "   COMPLETE TPT PRODUCT GENERATOR"
echo "   Small Wins Studio - Matching Activities"
echo "=========================================== 🎨"
echo ""

# Configuration
THEME="${1:-brown_bear}"
OUTPUT_DIR="exports/${THEME}_matching_complete"

echo "📋 Configuration:"
echo "   Theme: $THEME"
echo "   Output: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🚀 Starting complete product generation..."
echo ""

# Step 1: Generate Main Matching Activities
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Step 1/6: Generating Matching Activities"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python3 generate_matching_constitution.py; then
    echo "   ✅ Matching activities generated!"
else
    echo "   ❌ Failed to generate matching activities"
    exit 1
fi
echo ""

# Step 2: Generate Cover Page
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 Step 2/6: Generating Cover Page"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python3 generate_cover_page.py; then
    echo "   ✅ Cover page generated!"
else
    echo "   ❌ Failed to generate cover page"
    exit 1
fi
echo ""

# Step 3: Generate Freebie Sample
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎁 Step 3/6: Generating Freebie Sample"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python3 generate_freebie.py; then
    echo "   ✅ Freebie sample generated!"
else
    echo "   ❌ Failed to generate freebie"
    exit 1
fi
echo ""

# Step 4: Generate Quick Start Guide
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Step 4/6: Generating Quick Start Guide"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python3 generate_quick_start_professional.py; then
    echo "   ✅ Quick Start guide generated!"
else
    echo "   ⚠️  Quick Start generation failed (continuing...)"
fi
echo ""

# Step 5: Generate TpT Documentation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📜 Step 5/6: Generating TpT Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python3 generate_tpt_documentation.py; then
    echo "   ✅ TpT documentation generated!"
else
    echo "   ⚠️  TpT documentation generation failed (continuing...)"
fi
echo ""

# Step 6: Create ZIP Package (if zip command available)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Step 6/6: Creating ZIP Package"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v zip &> /dev/null; then
    ZIP_NAME="${THEME}_matching_complete_$(date +%Y%m%d).zip"
    
    # Find generated PDFs (customize based on actual output locations)
    if ls *.pdf > /dev/null 2>&1; then
        zip -r "$ZIP_NAME" *.pdf 2>/dev/null || echo "   ⚠️  Some files might not be included"
        echo "   ✅ ZIP package created: $ZIP_NAME"
    else
        echo "   ⚠️  No PDF files found to package"
    fi
else
    echo "   ⚠️  ZIP command not available, skipping packaging"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 GENERATION COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Check your output files:"
echo "   - Matching activities (all 4 levels)"
echo "   - Cover page"
echo "   - Freebie sample"
echo "   - Quick Start guide"
echo "   - TpT documentation"
echo ""
echo "✅ Your TpT product is ready for upload!"
echo ""
echo "📊 Next steps:"
echo "   1. Review generated PDFs"
echo "   2. Create thumbnails for TpT"
echo "   3. Upload to Teachers Pay Teachers"
echo "   4. Share your amazing resources! 🎉"
echo ""
