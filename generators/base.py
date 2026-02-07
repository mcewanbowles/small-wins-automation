"""Base utilities for all generators"""
import json
import os
from pathlib import Path
from typing import Dict, Any


class BaseGenerator:
    """Base class for all product generators"""
    
    def __init__(self, theme: str, output_dir: str):
        self.theme = theme
        self.output_dir = Path(output_dir)
        self.repo_root = Path(__file__).parent.parent
        
        # Load theme config
        self.theme_config = self._load_theme_config()
        self.global_config = self._load_global_config()
        
        # Page constants from Design Constitution
        self.PAGE_WIDTH = 8.5 * 72  # US Letter in points
        self.PAGE_HEIGHT = 11 * 72
        self.MARGIN = 0.5 * 72  # 0.5 inch margins
        self.BORDER_RADIUS = 0.12 * 72
        self.BORDER_WIDTH = 2
        
        # Accent stripe constants
        self.STRIPE_HEIGHT = 0.55 * 72  # 0.5-0.6 inch
        self.STRIPE_PADDING = 0.12 * 72
        
        # Level colors (from Master Product Specification)
        self.LEVEL_COLORS = {
            'L1': '#F4B400',  # Orange - Errorless
            'L2': '#4285F4',  # Blue - Distractors
            'L3': '#34A853',  # Green - Picture + Text
            'L4': '#8C06F2',  # Purple - Generalisation
        }
        
    def _load_theme_config(self) -> Dict[str, Any]:
        """Load theme-specific configuration"""
        theme_path = self.repo_root / 'themes' / f'{self.theme}.json'
        if not theme_path.exists():
            raise FileNotFoundError(f"Theme config not found: {theme_path}")
        
        with open(theme_path, 'r') as f:
            return json.load(f)
    
    def _load_global_config(self) -> Dict[str, Any]:
        """Load global configuration"""
        global_path = self.repo_root / 'themes' / 'global_config.json'
        if global_path.exists():
            with open(global_path, 'r') as f:
                return json.load(f)
        return {}
    
    def get_icon_path(self, icon_name: str, icon_type: str = 'icons') -> Path:
        """Get path to an icon file
        
        Args:
            icon_name: Name of the icon (e.g., 'bear.png')
            icon_type: Type of icon ('icons', 'real_images', 'colouring')
        """
        icon_path = self.repo_root / 'assets' / 'themes' / self.theme / icon_type / icon_name
        if not icon_path.exists():
            raise FileNotFoundError(f"Icon not found: {icon_path}")
        return icon_path
    
    def ensure_output_dir(self, *subdirs):
        """Ensure output directory exists"""
        output_path = self.output_dir.joinpath(*subdirs)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple (0-1 range for ReportLab)"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (r/255, g/255, b/255)
