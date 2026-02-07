"""Command-line interface for generators"""
import sys
from pathlib import Path

def main():
    """Main entry point for generator commands"""
    if len(sys.argv) < 2:
        print("Small Wins Studio Generator System")
        print("\nUsage:")
        print("  python -m generators.matching --theme <theme> --output <dir>")
        print("  python -m generators.find_cover --theme <theme> --output <dir>")
        print("  python -m generators.aac --theme <theme> --output <dir>")
        print("\nExamples:")
        print("  python -m generators.matching --theme brown_bear --output exports/")
        print("  python -m generators.matching --theme brown_bear --output exports/ --level 1")
        sys.exit(1)

if __name__ == '__main__':
    main()
