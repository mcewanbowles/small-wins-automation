# small-wins-automation
Automated TpT resource generators for Small Wins Studio

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run quick start example
python quick_start.py

# Generate all matching levels
python -m generators.matching --theme brown_bear --output exports/
```

## 📚 Documentation

- **[Generator Documentation](GENERATOR_README.md)** - Complete guide to using the generator system
- **[Design Constitution](design/Design-Constitution.md)** - Visual and structural standards
- **[Master Product Specification](design/Master-Product-Specification.md)** - Complete product requirements
- **[Getting Started](docs/GETTING_STARTED.md)** - Workflow and next steps

## ✅ Current Status

| Component | Status |
|-----------|--------|
| Folder structure | ✅ Complete |
| Product specs | ✅ Complete |
| Theme config (Brown Bear) | ✅ Complete |
| Brown Bear icons | ✅ Complete |
| **Matching generator** | ✅ **Working** |
| Find & Cover generator | ⏳ TODO |
| AAC generator | ⏳ TODO |

## 🎯 What Works Now

The **Matching generator** is fully functional and can generate:
- ✅ 4 difficulty levels (Errorless, Distractors, Picture+Text, Generalisation)
- ✅ Color and B&W versions
- ✅ Cutout pieces page
- ✅ Storage labels page
- ✅ Compliant with Design Constitution
- ✅ Level-coded accent stripes
- ✅ Professional page layouts

## 📦 Generated Output

Running the matching generator creates:
```
exports/matching/
├── brown_bear_matching_level1_color.pdf
├── brown_bear_matching_level1_bw.pdf
├── brown_bear_matching_level2_color.pdf
├── brown_bear_matching_level2_bw.pdf
├── brown_bear_matching_level3_color.pdf
├── brown_bear_matching_level3_bw.pdf
├── brown_bear_matching_level4_color.pdf
├── brown_bear_matching_level4_bw.pdf
├── brown_bear_matching_cutouts.pdf
└── brown_bear_matching_storage_labels.pdf
```

## 🛠️ Next Steps

1. ⏳ Implement Find & Cover generator
2. ⏳ Implement AAC generator  
3. ⏳ Add cover page generation
4. ⏳ Add Quick Start instructions page
5. ⏳ Generate thumbnails and previews
6. ⏳ Create ZIP packaging

See **[GENERATOR_README.md](GENERATOR_README.md)** for detailed usage instructions.
