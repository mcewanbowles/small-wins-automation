# 🎨 Logo Integration Guide
## Adding Small Wins Studio Logo to Product Covers

**Last Updated:** February 3, 2026

---

## Quick Start

Want to add your Small Wins Studio logo to all product covers? Here's how:

### 3-Step Process

**Step 1: Save Your Logo**
```bash
# Create the branding folder
mkdir -p assets/branding

# Add your logo file
cp /path/to/your/logo.png assets/branding/small_wins_logo.png
```

**Step 2: Commit to Repository**
```bash
git add assets/branding/small_wins_logo.png
git commit -m "Add Small Wins Studio logo"
git push
```

**Step 3: Regenerate Covers**
```bash
python3 generate_product_covers.py
```

**Done!** Your logo is now on all covers! 🎉

---

## Logo Specifications

### Recommended Format

**File Format:**
- **Primary:** PNG with transparent background
- **Alternative:** PNG with white background
- **Not recommended:** JPG (lossy compression)

**Dimensions:**
- **Width:** 200-400 pixels (recommended)
- **Height:** Proportional to width
- **Minimum:** 150 pixels wide
- **Maximum:** 600 pixels wide

**Resolution:**
- **Print:** 300 DPI
- **Web:** 150 DPI minimum
- **High quality:** 300+ DPI

**File Size:**
- **Target:** Under 500KB
- **Maximum:** 2MB
- **Optimized:** Use PNG compression

**Aspect Ratio:**
- **Any ratio works** - will be scaled proportionally
- **Recommended:** Square or horizontal rectangle
- **Examples:** 1:1, 16:9, 4:3, 2:1

---

## File Placement

### Where to Put Your Logo

The cover generator checks for logos in these locations (in order):

**Priority 1: Branding Folder** (Recommended)
```
assets/branding/small_wins_logo.png
```

**Priority 2: Named Logo**
```
assets/branding/logo.png
```

**Priority 3: Root Assets**
```
assets/logo.png
```

**Recommended:** Use `assets/branding/small_wins_logo.png` for clarity.

---

## Adding Logo to Repository

### Method 1: Direct Copy (Local)

```bash
# Navigate to repository
cd /path/to/small-wins-automation

# Create branding folder if needed
mkdir -p assets/branding

# Copy your logo
cp ~/Downloads/my_logo.png assets/branding/small_wins_logo.png

# Verify
ls -lh assets/branding/small_wins_logo.png

# Add to git
git add assets/branding/
git commit -m "Add Small Wins Studio logo"
git push
```

### Method 2: GitHub Upload

1. Go to your repository on GitHub
2. Navigate to `assets/branding/` (create if needed)
3. Click "Add file" → "Upload files"
4. Drag and drop `small_wins_logo.png`
5. Commit the upload
6. Pull changes to local: `git pull`

### Method 3: Tell Me!

Simply upload your logo somewhere accessible (Google Drive, Dropbox, etc.) and share the link. I can help you integrate it!

---

## Logo Integration Details

### Automatic Integration

The cover generator (`generate_product_covers.py`) now includes:

```python
def add_logo_if_available(canvas, x, y, width):
    """Add logo to cover if available"""
    logo_paths = [
        'assets/branding/small_wins_logo.png',
        'assets/branding/logo.png',
        'assets/logo.png'
    ]
    
    for logo_path in logo_paths:
        if os.path.exists(logo_path):
            # Add logo to cover
            canvas.drawImage(logo_path, x, y, width=width, 
                           height=None, preserveAspectRatio=True,
                           mask='auto')
            return True
    return False
```

**Features:**
- ✅ Automatic detection
- ✅ Graceful fallback if missing
- ✅ Maintains aspect ratio
- ✅ Transparent background support
- ✅ Professional scaling

---

## Logo Placement Options

### Current Implementation

**Location:** Top center of cover page

**Specifications:**
- **Position:** Center aligned, below "Small Wins Studio" text
- **Size:** 150 pixels wide (scaled proportionally)
- **Margin:** 0.5 inch from top
- **Background:** Transparent or matches cover

### Alternative Placements (Customizable)

**Top Left:**
```python
# Professional, classic
x = 0.5 * inch
y = PAGE_HEIGHT - 1.5 * inch
width = 1.5 * inch
```

**Top Center:**
```python
# Prominent, branded
x = (PAGE_WIDTH - logo_width) / 2
y = PAGE_HEIGHT - 1.5 * inch
width = 2 * inch
```

**Top Right:**
```python
# Subtle, modern
x = PAGE_WIDTH - logo_width - 0.5 * inch
y = PAGE_HEIGHT - 1.5 * inch
width = 1.5 * inch
```

**Header Integration:**
```python
# Part of turquoise header
x = 0.5 * inch
y = PAGE_HEIGHT - 1 * inch
width = 1.2 * inch
```

---

## Best Practices

### Logo Design

✅ **Do:**
- Use transparent background (PNG)
- Keep it simple and recognizable
- Ensure it works in small sizes
- Test on both light and dark backgrounds
- Use high resolution (300 DPI)

❌ **Don't:**
- Use complex gradients (may not scale well)
- Include small text (becomes unreadable)
- Use too many colors
- Create overly large files
- Use low resolution images

### File Management

✅ **Do:**
- Use descriptive filename (`small_wins_logo.png`)
- Keep original high-res version
- Optimize file size
- Version control your logo
- Document logo changes

❌ **Don't:**
- Use generic names (`logo.png`, `image.png`)
- Delete original files
- Commit extremely large files (>2MB)
- Change logo frequently without tracking

---

## Regenerating Covers

### When to Regenerate

Regenerate covers after:
- Adding logo for the first time
- Updating logo design
- Changing logo placement
- Modifying cover design

### How to Regenerate

```bash
# Regenerate all covers
python3 generate_product_covers.py

# Output
✓ Generated 7 covers with logo
✓ Logo automatically integrated
✓ Professional quality maintained
```

### What Gets Updated

When you regenerate:
- ✅ All 7 product covers (Matching L1-4, Find & Cover L1-3)
- ✅ Logo added to each cover
- ✅ Professional placement
- ✅ Consistent branding
- ✅ High-quality output

---

## Troubleshooting

### Logo Not Appearing

**Problem:** Logo doesn't show on covers

**Solutions:**
1. Check file path: `ls -la assets/branding/small_wins_logo.png`
2. Verify filename exactly: `small_wins_logo.png`
3. Check file format: Should be PNG
4. Regenerate covers: `python3 generate_product_covers.py`
5. Check console output for errors

### Logo Looks Blurry

**Problem:** Logo appears pixelated or low quality

**Solutions:**
1. Use higher resolution source (300 DPI)
2. Increase logo dimensions (400+ pixels wide)
3. Save as PNG, not JPG
4. Check original file quality

### Logo Too Large/Small

**Problem:** Logo sizing is wrong

**Solutions:**
1. Check logo dimensions in file
2. Modify width parameter in script
3. Ensure aspect ratio is preserved
4. Test with different sizes

### Transparent Background Not Working

**Problem:** Logo has white box around it

**Solutions:**
1. Re-save as PNG with transparency
2. Use image editor to remove background
3. Check `mask='auto'` parameter in script
4. Verify PNG has alpha channel

---

## Examples

### Example 1: Simple Logo

**Scenario:** Simple text-based logo

**File:** `small_wins_logo.png`
- Width: 300 pixels
- Height: 100 pixels
- Format: PNG transparent
- Size: 25KB

**Result:** Clean, professional, readable at all sizes

### Example 2: Icon + Text Logo

**Scenario:** Logo with icon and text

**File:** `small_wins_logo.png`
- Width: 400 pixels
- Height: 150 pixels  
- Format: PNG transparent
- Size: 45KB

**Result:** Branded, recognizable, professional

### Example 3: Complex Logo

**Scenario:** Detailed logo with multiple elements

**File:** `small_wins_logo.png`
- Width: 500 pixels
- Height: 200 pixels
- Format: PNG transparent
- Size: 120KB

**Result:** Full branding, high quality, impressive

---

## Customization

### Want Different Placement?

Edit `generate_product_covers.py`:

```python
# Find the logo placement section
logo_x = (PAGE_WIDTH - logo_width) / 2  # Center
logo_y = PAGE_HEIGHT - 2.5 * inch        # Position
logo_width = 2 * inch                    # Size

# Change to your preferences
logo_x = 0.5 * inch           # Left aligned
logo_y = PAGE_HEIGHT - 1 * inch  # Higher
logo_width = 1.5 * inch          # Smaller
```

### Want Logo on Different Elements?

Logo can be added to:
- Product covers (current)
- Activity pages (custom)
- Storage labels (custom)
- Marketing materials (custom)
- Thumbnails (custom)

Just ask for customization!

---

## Quick Reference

### Checklist for Adding Logo

- [ ] Logo saved as PNG
- [ ] Transparent background (if possible)
- [ ] 200-400 pixels wide
- [ ] 300 DPI resolution
- [ ] File under 500KB
- [ ] Placed in `assets/branding/`
- [ ] Named `small_wins_logo.png`
- [ ] Committed to repository
- [ ] Covers regenerated
- [ ] Results verified

---

## Support

### Need Help?

If you need assistance with:
- Creating a logo
- Optimizing logo file
- Custom placement
- Design advice
- Technical issues

Just ask! I can help with logo integration and customization.

---

## Summary

**Logo integration is:**
- ✅ Simple (3 steps)
- ✅ Automatic (detects logo)
- ✅ Professional (scales correctly)
- ✅ Flexible (customizable)
- ✅ Quality (maintains resolution)

**To add your logo:**
1. Save as PNG with transparency
2. Place in `assets/branding/small_wins_logo.png`
3. Commit to repository
4. Run `python3 generate_product_covers.py`

**Your covers will be professionally branded!** 🎨

---

**Questions?** Refer to this guide or ask for help!
