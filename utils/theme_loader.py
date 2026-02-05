"""
Theme Loader Utility

Loads and manages theme configurations for SPED resources.
"""

import json
import os


class ThemeLoader:
    """
    Loads and manages theme configurations from JSON files.
    """
    
    def __init__(self, themes_dir='themes'):
        """
        Initialize theme loader.
        
        Args:
            themes_dir: Directory containing theme JSON files
        """
        self.themes_dir = themes_dir
        self.themes_cache = {}
    
    def load_theme(self, theme_name):
        """
        Load a theme configuration from JSON file.
        
        Args:
            theme_name: Name of the theme (without .json extension)
            
        Returns:
            dict: Theme configuration
        """
        # Check cache first
        if theme_name in self.themes_cache:
            return self.themes_cache[theme_name]
        
        # Load from file
        theme_path = os.path.join(self.themes_dir, f"{theme_name}.json")
        
        if not os.path.exists(theme_path):
            raise FileNotFoundError(f"Theme file not found: {theme_path}")
        
        with open(theme_path, 'r', encoding='utf-8') as f:
            theme_data = json.load(f)
        
        # Cache the theme
        self.themes_cache[theme_name] = theme_data
        
        return theme_data
    
    def get_theme_items(self, theme_name):
        """
        Get the items list from a theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            list: List of item dictionaries
        """
        theme = self.load_theme(theme_name)
        return theme.get('items', [])
    
    def get_theme_metadata(self, theme_name):
        """
        Get metadata about a theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            dict: Theme metadata
        """
        theme = self.load_theme(theme_name)
        return {
            'name': theme.get('name', theme_name),
            'description': theme.get('description', ''),
            'author': theme.get('author', ''),
            'version': theme.get('version', '1.0'),
            'item_count': len(theme.get('items', []))
        }
    
    def list_available_themes(self):
        """
        List all available themes in the themes directory.
        
        Returns:
            list: List of theme names (without .json extension)
        """
        if not os.path.exists(self.themes_dir):
            return []
        
        themes = []
        for filename in os.listdir(self.themes_dir):
            if filename.endswith('.json'):
                theme_name = filename[:-5]  # Remove .json
                themes.append(theme_name)
        
        return sorted(themes)
    
    def validate_theme(self, theme_name):
        """
        Validate that a theme has required fields.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            theme = self.load_theme(theme_name)
            
            # Check required fields
            if 'items' not in theme:
                return (False, "Theme missing 'items' field")
            
            if not isinstance(theme['items'], list):
                return (False, "'items' must be a list")
            
            if len(theme['items']) == 0:
                return (False, "Theme has no items")
            
            # Validate each item
            for idx, item in enumerate(theme['items']):
                if 'image' not in item:
                    return (False, f"Item {idx} missing 'image' field")
                if 'label' not in item:
                    return (False, f"Item {idx} missing 'label' field")
            
            return (True, "Theme is valid")
            
        except Exception as e:
            return (False, str(e))
    
    def clear_cache(self):
        """Clear the theme cache."""
        self.themes_cache.clear()


def create_theme_template(theme_name, items, description='', author='', output_dir='themes'):
    """
    Create a new theme JSON file from template.
    
    Args:
        theme_name: Name for the theme
        items: List of item dictionaries with 'image' and 'label' keys
        description: Theme description
        author: Theme author
        output_dir: Directory to save theme file
        
    Returns:
        str: Path to created theme file
    """
    theme_data = {
        'name': theme_name,
        'description': description,
        'author': author,
        'version': '1.0',
        'items': items
    }
    
    os.makedirs(output_dir, exist_ok=True)
    theme_path = os.path.join(output_dir, f"{theme_name}.json")
    
    with open(theme_path, 'w', encoding='utf-8') as f:
        json.dump(theme_data, f, indent=2, ensure_ascii=False)
    
    return theme_path


# Global theme loader instance
_theme_loader = None

def get_theme_loader(themes_dir='themes'):
    """
    Get the global theme loader instance.
    
    Args:
        themes_dir: Directory containing themes
        
    Returns:
        ThemeLoader: Global theme loader
    """
    global _theme_loader
    if _theme_loader is None:
        _theme_loader = ThemeLoader(themes_dir)
    return _theme_loader
