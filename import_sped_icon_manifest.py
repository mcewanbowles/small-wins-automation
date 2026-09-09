"""
Import the SPED topic icon manifest into the StudioForge Icon Labeler system.

This script:
1. Scans all enriched topic JSONs for required icons
2. Resolves each icon through the guardrails (substitutes, omissions)
3. Writes a manifest file that the Icon Labeler can read
4. Reports which icons are ready, which need sourcing, and which are omitted

Output: assets/symbols/png/Alpha/sped_icon_manifest.json
"""
import json
from pathlib import Path
from collections import defaultdict

# Add bundle_adapters to path for icon_resolver
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "tools" / "bundle_adapters"))
from icon_resolver import resolve_icon, get_icon_status, _normalize_name, OMITTED_ICONS, SUBSTITUTES

REPO = Path(__file__).resolve().parent
PIPELINE = REPO / "Dignity" / "topics"
ICONS_ROOT = REPO / "assets" / "symbols" / "png" / "Alpha"
MANIFEST_OUT = ICONS_ROOT / "sped_icon_manifest.json"


def collect_icons_from_json(data: dict) -> set:
    """Extract all icon names referenced in a topic JSON."""
    icons = set()
    
    for kw in (data.get("icon_keywords") or []):
        icons.add(str(kw).strip())
    
    cop = data.get("cut_out_pieces") or {}
    if isinstance(cop, dict):
        for piece in (cop.get("pieces") or []):
            if isinstance(piece, dict):
                icons.add(str(piece.get("icon", "")).strip())
    
    vsc = data.get("visual_support_cards") or {}
    if isinstance(vsc, dict):
        for card in (vsc.get("cards") or []):
            if isinstance(card, dict):
                icons.add(str(card.get("icon", "")).strip())
    
    abo = data.get("alternative_behavior_options") or {}
    if isinstance(abo, dict):
        for opt in (abo.get("options") or []):
            if isinstance(opt, dict):
                icons.add(str(opt.get("icon", "")).strip())
    
    aac = data.get("aac_board") or {}
    if isinstance(aac, dict):
        for fw in (aac.get("fringe_12") or []):
            icons.add(str(fw).strip())
    
    for cc in (data.get("cue_cards") or []):
        icons.add(str(cc).strip())
    
    for fw in (data.get("fringe_words") or []):
        icons.add(str(fw).strip())
    
    icons.discard("")
    return icons


def main():
    # Scan all enriched drafts
    topics = {}
    for f in PIPELINE.glob("*_ENRICHED_v1.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            topic_id = data.get("topic_id") or f.stem.replace("_ENRICHED_DRAFT_v1", "")
            icons = collect_icons_from_json(data)
            topics[topic_id] = sorted(icons)
        except Exception as e:
            print(f"ERROR reading {f.name}: {e}")
    
    # Build manifest with resolution status
    manifest = {
        "generated": str(Path(__file__).stat().st_mtime),
        "total_topics": len(topics),
        "topics": {},
        "summary": {
            "total_unique_icons": 0,
            "found": 0,
            "substituted": 0,
            "omitted": 0,
            "missing": 0,
        },
    }
    
    all_icons = set()
    status_counts = defaultdict(int)
    
    for topic_id, icons in sorted(topics.items()):
        topic_entry = {
            "icon_count": len(icons),
            "icons": [],
        }
        for icon_name in icons:
            info = get_icon_status(icon_name)
            info["name"] = icon_name
            topic_entry["icons"].append(info)
            all_icons.add(_normalize_name(icon_name))
            status_counts[info["status"]] += 1
        manifest["topics"][topic_id] = topic_entry
    
    manifest["summary"]["total_unique_icons"] = len(all_icons)
    manifest["summary"]["found"] = status_counts["found"]
    manifest["summary"]["substituted"] = status_counts["substitute"]
    manifest["summary"]["omitted"] = status_counts["omitted"]
    manifest["summary"]["missing"] = status_counts["missing"]
    
    # Write manifest
    ICONS_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    # Print summary
    print(f"=== SPED ICON MANIFEST ===")
    print(f"Topics scanned: {len(topics)}")
    print(f"Total unique icons: {len(all_icons)}")
    print(f"  Found in library:    {status_counts['found']}")
    print(f"  Substituted:         {status_counts['substitute']}")
    print(f"  Omitted (text only): {status_counts['omitted']}")
    print(f"  Missing (need src):  {status_counts['missing']}")
    print(f"\nManifest written to: {MANIFEST_OUT}")
    
    # List missing icons
    if status_counts["missing"] > 0:
        print(f"\n=== MISSING ICONS (need to source/create) ===")
        missing = set()
        for topic_id, entry in manifest["topics"].items():
            for ic in entry["icons"]:
                if ic["status"] == "missing":
                    sub = ic.get("substitute", "(no substitute)")
                    missing.add((ic["name"], sub))
        for name, sub in sorted(missing):
            print(f"  {name:25s}  substitute: {sub}")


if __name__ == "__main__":
    main()
