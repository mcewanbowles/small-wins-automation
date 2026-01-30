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


class Theme:
    """
    Structured theme object containing all theme data and metadata.
    
    Attributes:
        name: Theme display name
        theme_id: Theme identifier (CSV row key)
        icons: List of icon filenames or paths
        real_images: List of real image filenames or paths
        colours: List of hex color codes
        fonts: Dictionary with 'heading' and 'body' font names
        vocab: List of vocabulary words
        sequencing: List of sequencing step lists
        adapted_book: List of adapted book sentences
        storage_label_images: List of storage label image paths
        paths: Dictionary of resolved file paths
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
        """Resolve all file paths from CSV data."""
        paths = {}
        
        # Icon folder
        icon_folder = row_data.get('icon_folder', '')
        if icon_folder:
            paths['icons'] = (csv_dir / icon_folder).resolve()
        else:
            paths['icons'] = None
        
        # Real images folder
        real_folder = row_data.get('real_images_folder', '')
        if real_folder:
            paths['real_images'] = (csv_dir / real_folder).resolve()
        else:
            paths['real_images'] = None
        
        # Storage label images folder
        storage_folder = row_data.get('storage_label_images', '')
        if storage_folder:
            paths['storage_labels'] = (csv_dir / storage_folder).resolve()
        else:
            paths['storage_labels'] = None
        
        return paths
    
    def _load_icons(self) -> List[str]:
        """Load list of icon filenames from icon folder."""
        if not self.paths.get('icons') or not self.paths['icons'].exists():
            return []
        
        # Get all image files
        icon_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.svg']:
            icon_files.extend(self.paths['icons'].glob(ext))
        
        return sorted([f.name for f in icon_files])
    
    def _load_real_images(self) -> List[str]:
        """Load list of real image filenames from real images folder."""
        if not self.paths.get('real_images') or not self.paths['real_images'].exists():
            return []
        
        # Get all image files
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(self.paths['real_images'].glob(ext))
        
        return sorted([f.name for f in image_files])
    
    def _load_storage_labels(self) -> List[str]:
        """Load list of storage label image filenames."""
        if not self.paths.get('storage_labels') or not self.paths['storage_labels'].exists():
            return []
        
        # Get all image files
        label_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            label_files.extend(self.paths['storage_labels'].glob(ext))
        
        return sorted([f.name for f in label_files])
    
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
        """Convert theme to black-and-white mode."""
        # Convert colors to grayscale equivalents
        if self.colours:
            bw_colours = []
            for color in self.colours:
                # Convert hex to RGB
                color = color.lstrip('#')
                if len(color) == 6:
                    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
                    # Convert to grayscale using standard formula
                    gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                    # Ensure high contrast - if too light, darken; if too dark, lighten
                    if gray > 200:
                        gray = max(gray - 50, 128)
                    elif gray < 55:
                        gray = min(gray + 50, 128)
                    bw_hex = f"#{gray:02x}{gray:02x}{gray:02x}"
                    bw_colours.append(bw_hex)
                else:
                    bw_colours.append(color)  # Keep as-is if invalid
            self.colours = bw_colours
    
    def get_icon_path(self, icon_name: str) -> Optional[Path]:
        """Get full path to an icon file."""
        if not self.paths.get('icons'):
            return None
        return self.paths['icons'] / icon_name
    
    def get_real_image_path(self, image_name: str) -> Optional[Path]:
        """Get full path to a real image file."""
        if not self.paths.get('real_images'):
            return None
        return self.paths['real_images'] / image_name
    
    def get_storage_label_path(self, label_name: str) -> Optional[Path]:
        """Get full path to a storage label image."""
        if not self.paths.get('storage_labels'):
            return None
        return self.paths['storage_labels'] / label_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary for JSON serialization."""
        return {
            'theme_id': self.theme_id,
            'name': self.name,
            'mode': self.mode,
            'icons': self.icons,
            'real_images': self.real_images,
            'colours': self.colours,
            'fonts': self.fonts,
            'vocab': self.vocab,
            'sequencing': self.sequencing,
            'adapted_book': self.adapted_book,
            'storage_label_images': self.storage_label_images,
            'paths': {k: str(v) for k, v in self.paths.items() if v},
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
        
        # Check for icon folder if icons are expected
        if theme.paths.get('icons'):
            if not theme.paths['icons'].exists():
                errors.append(f"Icon folder does not exist: {theme.paths['icons']}")
        
        # Check for real images folder if specified
        if theme.paths.get('real_images'):
            if not theme.paths['real_images'].exists():
                errors.append(f"Real images folder does not exist: {theme.paths['real_images']}")
        
        # Warn about optional missing fields but don't fail
        if not theme.vocab:
            # Just a warning, not an error
            pass
        
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
