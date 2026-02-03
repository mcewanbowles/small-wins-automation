#!/usr/bin/env python3
"""Quick test to generate a single sample."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

output_dir = project_root / 'samples' / 'brown_bear'
output_dir.mkdir(parents=True, exist_ok=True)

print("Testing Vocabulary Cards generator...")
try:
    # Import and test vocab cards
    from generators.vocab_cards import generate_vocab_cards_set_dual_mode
    
    print("Function imported successfully")
    print(f"Output dir: {output_dir}")
    
    # Call with minimal parameters
    result = generate_vocab_cards_set_dual_mode(
        theme_name='brown_bear',
        output_dir=str(output_dir)
    )
    
    print(f"Success! Generated: {result}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
