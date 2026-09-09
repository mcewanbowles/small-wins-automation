"""Check icon availability for Dignity vocabulary."""
import sys
sys.path.insert(0, "Dignity/adapters")
from icon_resolver import resolve_icon

alts = {
    "body": ["body", "my body", "person", "human", "my_body"],
    "hands": ["hands", "hand", "palm"],
    "pants": ["pants", "trousers", "jeans"],
    "door": ["door", "closed door", "open door"],
    "bedroom": ["bedroom", "bed room", "bed"],
    "bathroom": ["bathroom", "bath room", "toilet", "restroom"],
    "help": ["help", "help me", "assist"],
    "break": ["break", "take a break", "rest"],
    "stop": ["stop", "stop sign", "stop hand"],
    "safe": ["safe", "safety", "safe place"],
    "people": ["people", "person", "group of people"],
    "adults": ["adults", "adult", "grown up"],
    "wait": ["wait", "waiting", "pause"],
    "finished": ["finished", "done", "complete", "finish"],
    "yes": ["yes", "check", "checkmark", "okay"],
    "no": ["no", "x", "cross", "denied"],
    "friends": ["friends", "friend", "kids playing"],
    "playground": ["playground", "park", "slide", "swing"],
    "private": ["private", "door closed", "alone"],
    "public": ["public", "people", "group"],
    "fidget": ["fidget", "toy", "play"],
    "underwear": ["underwear", "underpants", "panties"],
    "touch": ["touch", "feel", "hand"],
    "okay": ["okay", "ok", "thumbs up", "good"],
    "squeeze": ["squeeze", "press", "grip"],
}

for key, names in alts.items():
    found = None
    for n in names:
        p = resolve_icon(n)
        if p:
            found = (n, p.name)
            break
    if found:
        print(f"  {key:15s} FOUND as '{found[0]}' -> {found[1]}")
    else:
        print(f"  {key:15s} MISSING (tried: {names})")
