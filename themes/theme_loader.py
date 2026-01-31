"""
CSV-Based Theme Loader - Single Source of Truth for Theme Data

This module provides comprehensive theme loading from a master CSV file,
supporting both color and black-and-white output modes.

Usage:
    from themes.theme_loader import load_theme, load_all_themes
    
    # Load a single theme
    theme = load_theme('brown_bear', mode='color')
    
    # Access theme data
    icons = theme.icons
    vocab = theme.vocab
    colors = theme.colours
    
    # Load in black-and-white mode
    bw_theme = load_theme('brown_bear', mode='bw')
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from PIL import Image, ImageOps
import sys

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.color_helpers import palette_to_grayscale


class Theme:
    """
    Structured theme object containing all theme data and metadata.
    
    Attributes:
        name: Theme display name
        theme_id: Theme identifier (CSV row key)
        icons: List of icon filenames or paths
        real_images: List of real image filenames or paths
        coloring_images: List of coloring image filenames or paths
        colours: List of hex color codes
        fonts: Dictionary with 'heading' and 'body' font names
        vocab: List of vocabulary words
        sequencing: List of sequencing step lists
        adapted_book: List of adapted book sentences
        storage_label_images: List of storage label image paths
        paths: Dictionary of resolved file paths with fallback folders
        metadata: Raw CSV row data
        mode: Output mode ('color' or 'bw')
    """
    
    def __init__(self, row_data: Dict[str, str], csv_dir: Path, mode: str = 'color'):
        """
        Initialize theme from CSV row data.
        
        Args:
            row_data: Dictionary of CSV column values
            csv_dir: Directory containing the CSV file (for resolving relative paths)
            mode: Output mode - 'color' or 'bw' for black-and-white
        """
        self.metadata = row_data
        self.mode = mode
        self.theme_id = row_data.get('theme_id', row_data.get('theme_name', 'unknown'))
        self.name = row_data.get('theme_name', self.theme_id)
        
        # Resolve paths
        self.paths = self._resolve_paths(row_data, csv_dir)
        
        # Load and process data
        self.icons = self._load_icons()
        self.real_images = self._load_real_images()
        self.coloring_images = self._load_coloring_images()
        self.colours = self._parse_colours(row_data.get('colour_palette', ''))
        self.fonts = self._parse_fonts(row_data)
        self.vocab = self._parse_list(row_data.get('key_vocab', ''))
        self.sequencing = self._parse_sequencing(row_data.get('sequencing_steps', ''))
        self.adapted_book = self._parse_adapted_book(row_data.get('adapted_book_sentences', ''))
        self.storage_label_images = self._load_storage_labels()
        
        # Apply black-and-white mode if requested
        if mode == 'bw':
            self._apply_bw_mode()
    
    def _resolve_paths(self, row_data: Dict[str, str], csv_dir: Path) -> Dict[str, Path]:
        """Resolve all file paths from CSV data with new /assets/ structure."""
        paths = {}
        
        # Get repository root (parent of themes folder)
        repo_root = csv_dir.parent
        assets_root = repo_root / 'assets'
        
        # Theme-specific paths (new structure)
        theme_assets = assets_root / 'themes' / self.theme_id
        
        # Icon folders (fallback chain)
        paths['icon_folders'] = []
        
        # 1. Theme-specific icons
        theme_icons = theme_assets / 'icons'
        if theme_icons.exists():
            paths['icon_folders'].append(theme_icons)
        
        # 2. Global AAC core icons
        global_aac_core = assets_root / 'global' / 'aac_core'
        if global_aac_core.exists():
            paths['icon_folders'].append(global_aac_core)
        
        # 3. Global AAC core with text
        global_aac_core_text = assets_root / 'global' / 'aac_core_text'
        if global_aac_core_text.exists():
            paths['icon_folders'].append(global_aac_core_text)
        
        # 4. Global AAC board icons
        global_aac_board = assets_root / 'global' / 'aac_board'
        if global_aac_board.exists():
            paths['icon_folders'].append(global_aac_board)
        
        # 5. Legacy icon folder from CSV (if specified)
        icon_folder = row_data.get('icon_folder', '')
        if icon_folder:
            legacy_icons = (csv_dir / icon_folder).resolve()
            if legacy_icons.exists() and legacy_icons not in paths['icon_folders']:
                paths['icon_folders'].append(legacy_icons)
        
        # Real images folders (fallback chain)
        paths['real_image_folders'] = []
        
        # 1. Theme-specific real images
        theme_real = theme_assets / 'real_images'
        if theme_real.exists():
            paths['real_image_folders'].append(theme_real)
        
        # 2. Legacy real images folder from CSV (if specified)
        real_folder = row_data.get('real_images_folder', '')
        if real_folder:
            legacy_real = (csv_dir / real_folder).resolve()
            if legacy_real.exists() and legacy_real not in paths['real_image_folders']:
                paths['real_image_folders'].append(legacy_real)
        
        # Coloring images folders (fallback chain)
        paths['coloring_folders'] = []
        
        # 1. Theme-specific coloring images
        theme_coloring = theme_assets / 'colouring'
        if theme_coloring.exists():
            paths['coloring_folders'].append(theme_coloring)
        
        # 2. Global coloring images
        global_colors = assets_root / 'global' / 'colours'
        if global_colors.exists():
            paths['coloring_folders'].append(global_colors)
        
        # Storage label folders (fallback chain)
        paths['storage_label_folders'] = []
        
        # 1. Theme-specific storage labels
        theme_storage = theme_assets / 'storage_labels'
        if theme_storage.exists():
            paths['storage_label_folders'].append(theme_storage)
        
        # 2. Use theme icons as fallback
        if paths['icon_folders']:
            paths['storage_label_folders'].extend(paths['icon_folders'])
        
        # 3. Legacy storage folder from CSV (if specified)
        storage_folder = row_data.get('storage_label_images', '')
        if storage_folder:
            legacy_storage = (csv_dir / storage_folder).resolve()
            if legacy_storage.exists() and legacy_storage not in paths['storage_label_folders']:
                paths['storage_label_folders'].append(legacy_storage)
        
        # Black & white generics folder
        paths['bw_generic'] = assets_root / 'global' / 'generic_bw'
        if not paths['bw_generic'].exists():
            paths['bw_generic'] = None
        
        # Backward compatibility: keep single 'icons' path for legacy code
        paths['icons'] = paths['icon_folders'][0] if paths['icon_folders'] else None
        paths['real_images'] = paths['real_image_folders'][0] if paths['real_image_folders'] else None
        paths['storage_labels'] = paths['storage_label_folders'][0] if paths['storage_label_folders'] else None
        
        return paths
    
    def _load_icons(self) -> List[str]:
        """Load list of icon filenames from all icon folders."""
        icon_folders = self.paths.get('icon_folders', [])
        if not icon_folders:
            return []
        
        # Get all unique icon filenames across all folders
        icon_names = set()
        for folder in icon_folders:
            if folder.exists():
                for ext in ['*.png', '*.jpg', '*.jpeg', '*.svg']:
                    icon_names.update(f.name for f in folder.glob(ext))
        
        return sorted(list(icon_names))
    
    def _load_real_images(self) -> List[str]:
        """Load list of real image filenames from all real image folders."""
        image_folders = self.paths.get('real_image_folders', [])
        if not image_folders:
            return []
        
        # Get all unique image filenames across all folders
        image_names = set()
        for folder in image_folders:
            if folder.exists():
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    image_names.update(f.name for f in folder.glob(ext))
        
        return sorted(list(image_names))
    
    def _load_coloring_images(self) -> List[str]:
        """Load list of coloring image filenames from all coloring folders."""
        coloring_folders = self.paths.get('coloring_folders', [])
        if not coloring_folders:
            return []
        
        # Get all unique coloring filenames across all folders
        coloring_names = set()
        for folder in coloring_folders:
            if folder.exists():
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    coloring_names.update(f.name for f in folder.glob(ext))
        
        return sorted(list(coloring_names))
    
    def _load_storage_labels(self) -> List[str]:
        """Load list of storage label image filenames from all storage label folders."""
        label_folders = self.paths.get('storage_label_folders', [])
        if not label_folders:
            return []
        
        # Get all unique label filenames across all folders
        label_names = set()
        for folder in label_folders:
            if folder.exists():
                for ext in ['*.png', '*.jpg', '*.jpeg']:
                    label_names.update(f.name for f in folder.glob(ext))
        
        return sorted(list(label_names))
    
    def _parse_colours(self, colour_str: str) -> List[str]:
        """Parse comma-separated hex color values."""
        if not colour_str:
            return []
        
        colors = [c.strip() for c in colour_str.split(',')]
        # Ensure all colors start with #
        return ['#' + c.lstrip('#') for c in colors if c]
    
    def _parse_fonts(self, row_data: Dict[str, str]) -> Dict[str, str]:
        """Parse font configuration."""
        fonts_str = row_data.get('fonts', '')
        
        if not fonts_str:
            # Default fonts
            return {
                'heading': 'Arial-Bold',
                'body': 'Arial'
            }
        
        # Try to parse as JSON first
        try:
            return json.loads(fonts_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try to parse as comma-separated
        parts = [p.strip() for p in fonts_str.split(',')]
        if len(parts) >= 2:
            return {
                'heading': parts[0],
                'body': parts[1]
            }
        elif len(parts) == 1:
            return {
                'heading': parts[0] + '-Bold',
                'body': parts[0]
            }
        
        return {
            'heading': 'Arial-Bold',
            'body': 'Arial'
        }
    
    def _parse_list(self, list_str: str) -> List[str]:
        """Parse comma-separated list."""
        if not list_str:
            return []
        return [item.strip() for item in list_str.split(',') if item.strip()]
    
    def _parse_sequencing(self, seq_str: str) -> List[List[str]]:
        """Parse sequencing steps (JSON or pipe-separated)."""
        if not seq_str:
            return []
        
        # Try JSON first
        try:
            parsed = json.loads(seq_str)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try pipe-separated lists
        sequences = []
        for sequence in seq_str.split('||'):
            sequence = sequence.strip()
            if sequence:
                steps = [s.strip() for s in sequence.split('|') if s.strip()]
                if steps:
                    sequences.append(steps)
        
        return sequences
    
    def _parse_adapted_book(self, book_str: str) -> List[str]:
        """Parse adapted book sentences (JSON or pipe-separated)."""
        if not book_str:
            return []
        
        # Try JSON first
        try:
            parsed = json.loads(book_str)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try pipe-separated
        sentences = [s.strip() for s in book_str.split('|') if s.strip()]
        return sentences
    
    def _apply_bw_mode(self):
        """Convert theme to black-and-white mode using color_helpers."""
        # Convert colors to grayscale equivalents using standard utility
        if self.colours:
            self.colours = palette_to_grayscale(self.colours)
    
    def get_icon_path(self, icon_name: str) -> Optional[Path]:
        """
        Get full path to an icon file with fallback logic.
        Searches through all icon folders in priority order.
        """
        icon_folders = self.paths.get('icon_folders', [])
        
        for folder in icon_folders:
            if folder.exists():
                icon_path = folder / icon_name
                if icon_path.exists():
                    return icon_path
        
        # Not found in any folder
        return None
    
    def get_real_image_path(self, image_name: str) -> Optional[Path]:
        """
        Get full path to a real image file with fallback logic.
        Searches through all real image folders in priority order.
        """
        image_folders = self.paths.get('real_image_folders', [])
        
        for folder in image_folders:
            if folder.exists():
                image_path = folder / image_name
                if image_path.exists():
                    return image_path
        
        # Not found in any folder
        return None
    
    def get_coloring_image_path(self, image_name: str) -> Optional[Path]:
        """
        Get full path to a coloring image file with fallback logic.
        Searches through all coloring folders in priority order.
        """
        coloring_folders = self.paths.get('coloring_folders', [])
        
        for folder in coloring_folders:
            if folder.exists():
                image_path = folder / image_name
                if image_path.exists():
                    return image_path
        
        # Not found in any folder
        return None
    
    def get_storage_label_path(self, label_name: str) -> Optional[Path]:
        """
        Get full path to a storage label image with fallback logic.
        Searches through all storage label folders in priority order.
        """
        label_folders = self.paths.get('storage_label_folders', [])
        
        for folder in label_folders:
            if folder.exists():
                label_path = folder / label_name
                if label_path.exists():
                    return label_path
        
        # Not found in any folder
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary for JSON serialization."""
        return {
            'theme_id': self.theme_id,
            'name': self.name,
            'mode': self.mode,
            'icons': self.icons,
            'real_images': self.real_images,
            'coloring_images': self.coloring_images,
            'colours': self.colours,
            'fonts': self.fonts,
            'vocab': self.vocab,
            'sequencing': self.sequencing,
            'adapted_book': self.adapted_book,
            'storage_label_images': self.storage_label_images,
            'paths': {k: str(v) if not isinstance(v, list) else [str(p) for p in v] for k, v in self.paths.items() if v},
            'metadata': self.metadata
        }


class ThemeCSVLoader:
    """
    Loads themes from a master CSV file.
    """
    
    def __init__(self, csv_path: str = 'themes/themes.csv'):
        """
        Initialize CSV theme loader.
        
        Args:
            csv_path: Path to the master themes CSV file
        """
        self.csv_path = Path(csv_path)
        self.csv_dir = self.csv_path.parent
        self._themes_cache = {}
        self._csv_data = None
    
    def _load_csv(self):
        """Load and cache the CSV file."""
        if self._csv_data is not None:
            return
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Themes CSV file not found: {self.csv_path}")
        
        self._csv_data = {}
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                theme_id = row.get('theme_id', row.get('theme_name', ''))
                if theme_id:
                    self._csv_data[theme_id] = row
    
    def load_theme(self, theme_id: str, mode: str = 'color') -> Theme:
        """
        Load a theme by ID.
        
        Args:
            theme_id: Theme identifier
            mode: Output mode - 'color' or 'bw'
            
        Returns:
            Theme object
            
        Raises:
            ValueError: If theme not found or invalid mode
        """
        if mode not in ['color', 'bw']:
            raise ValueError(f"Invalid mode: {mode}. Must be 'color' or 'bw'")
        
        # Check cache
        cache_key = f"{theme_id}_{mode}"
        if cache_key in self._themes_cache:
            return self._themes_cache[cache_key]
        
        # Load CSV if not already loaded
        self._load_csv()
        
        if theme_id not in self._csv_data:
            raise ValueError(f"Theme not found: {theme_id}")
        
        # Create theme object
        theme = Theme(self._csv_data[theme_id], self.csv_dir, mode)
        
        # Validate theme
        self._validate_theme(theme)
        
        # Cache and return
        self._themes_cache[cache_key] = theme
        return theme
    
    def _validate_theme(self, theme: Theme):
        """
        Validate theme has required data.
        
        Args:
            theme: Theme object to validate
            
        Raises:
            ValueError: If validation fails
        """
        errors = []
        warnings = []
        
        # Check for icon folders (warn if none exist)
        icon_folders = theme.paths.get('icon_folders', [])
        if not icon_folders or not any(f.exists() for f in icon_folders):
            warnings.append("No icon folders found")
        
        # Check for real images folders (warn if none exist)
        image_folders = theme.paths.get('real_image_folders', [])
        if not image_folders or not any(f.exists() for f in image_folders):
            warnings.append("No real image folders found")
        
        # Warnings are OK, errors would fail
        if warnings and False:  # Disable warnings for now
            print(f"Theme '{theme.name}' warnings: " + "; ".join(warnings))
        
        if errors:
            raise ValueError(f"Theme validation failed for '{theme.name}': " + "; ".join(errors))
    
    def list_themes(self) -> List[str]:
        """
        List all available theme IDs.
        
        Returns:
            List of theme IDs
        """
        self._load_csv()
        return sorted(list(self._csv_data.keys()))
    
    def load_all_themes(self, mode: str = 'color') -> Dict[str, Theme]:
        """
        Load all themes from CSV.
        
        Args:
            mode: Output mode - 'color' or 'bw'
            
        Returns:
            Dictionary mapping theme IDs to Theme objects
        """
        themes = {}
        for theme_id in self.list_themes():
            try:
                themes[theme_id] = self.load_theme(theme_id, mode)
            except Exception as e:
                print(f"Warning: Failed to load theme '{theme_id}': {e}")
        return themes
    
    def clear_cache(self):
        """Clear the theme cache."""
        self._themes_cache.clear()


# Global loader instance
_csv_loader = None


def load_theme(theme_id: str, mode: str = 'color', csv_path: str = 'themes/themes.csv') -> Theme:
    """
    Load a theme from the master CSV file.
    
    Args:
        theme_id: Theme identifier
        mode: Output mode - 'color' or 'bw'
        csv_path: Path to themes CSV file
        
    Returns:
        Theme object
        
    Example:
        theme = load_theme('brown_bear', mode='color')
        print(theme.vocab)
        print(theme.colours)
    """
    global _csv_loader
    if _csv_loader is None or _csv_loader.csv_path != Path(csv_path):
        _csv_loader = ThemeCSVLoader(csv_path)
    return _csv_loader.load_theme(theme_id, mode)


def load_all_themes(mode: str = 'color', csv_path: str = 'themes/themes.csv') -> Dict[str, Theme]:
    """
    Load all themes from the master CSV file.
    
    Args:
        mode: Output mode - 'color' or 'bw'
        csv_path: Path to themes CSV file
        
    Returns:
        Dictionary mapping theme IDs to Theme objects
    """
    global _csv_loader
    if _csv_loader is None or _csv_loader.csv_path != Path(csv_path):
        _csv_loader = ThemeCSVLoader(csv_path)
    return _csv_loader.load_all_themes(mode)


def list_themes(csv_path: str = 'themes/themes.csv') -> List[str]:
    """
    List all available theme IDs.
    
    Args:
        csv_path: Path to themes CSV file
        
    Returns:
        List of theme IDs
    """
    global _csv_loader
    if _csv_loader is None or _csv_loader.csv_path != Path(csv_path):
        _csv_loader = ThemeCSVLoader(csv_path)
    return _csv_loader.list_themes()
