"""
Configuration loader for TpT Automation System

Loads theme configurations (brown_bear.json, etc.) and global settings (global_config.json)
following the structure defined in /themes directory.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # Go up from utils/ to project root
    return current_file.parent.parent


def load_json_config(filepath: Path) -> Dict[str, Any]:
    """Load JSON configuration file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")


def load_theme_config(theme_name: str) -> Dict[str, Any]:
    """
    Load theme configuration from /themes/{theme_name}.json
    
    Args:
        theme_name: Name of the theme (e.g., "brown_bear")
        
    Returns:
        Dictionary containing theme configuration
    """
    root = get_project_root()
    theme_path = root / "themes" / f"{theme_name}.json"
    
    if not theme_path.exists():
        raise FileNotFoundError(f"Theme not found: {theme_name} at {theme_path}")
    
    return load_json_config(theme_path)


def load_global_config() -> Dict[str, Any]:
    """
    Load global configuration from /themes/global_config.json
    
    Returns:
        Dictionary containing global settings (branding, level colors, etc.)
    """
    root = get_project_root()
    global_path = root / "themes" / "global_config.json"
    
    if not global_path.exists():
        raise FileNotFoundError(f"Global config not found at {global_path}")
    
    return load_json_config(global_path)


def get_level_color(level: int, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the color code for a specific level.
    
    Args:
        level: Level number (1-4)
        config: Optional global config dict (will load if not provided)
        
    Returns:
        Hex color code (e.g., "#F4B400")
    """
    if config is None:
        config = load_global_config()
    
    level_colors = config.get("level_colors", {})
    level_key = f"level_{level}"
    
    if level_key not in level_colors:
        # Fallback colors
        fallback_colors = {
            "level_1": "#F4B400",  # Orange
            "level_2": "#4285F4",  # Blue
            "level_3": "#34A853",  # Green
            "level_4": "#8C06F2",  # Purple
        }
        return fallback_colors.get(level_key, "#000000")
    
    return level_colors[level_key].get("hex", "#000000")


def get_branding_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get branding configuration (Small Wins Studio colors, logos, etc.)
    
    Args:
        config: Optional global config dict (will load if not provided)
        
    Returns:
        Dictionary containing branding information
    """
    if config is None:
        config = load_global_config()
    
    return config.get("branding", {})


def get_asset_path(asset_type: str, filename: str = "") -> Path:
    """
    Get path to an asset file.
    
    Args:
        asset_type: Type of asset ("branding", "global", "themes", etc.)
        filename: Optional filename within the asset directory
        
    Returns:
        Path to the asset
    """
    root = get_project_root()
    base_path = root / "assets" / asset_type
    
    if filename:
        return base_path / filename
    return base_path
