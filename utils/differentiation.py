"""
Differentiation Utility

Manages differentiation levels and rules for SPED resources.
"""

from utils.config import DIFFERENTIATION_LEVELS


class DifferentiationManager:
    """
    Manages differentiation levels and provides level-specific configurations.
    """
    
    def __init__(self):
        """Initialize differentiation manager."""
        self.levels = DIFFERENTIATION_LEVELS
    
    def get_level_config(self, level):
        """
        Get configuration for a specific level.
        
        Args:
            level: Level number (1-4)
            
        Returns:
            dict: Level configuration
        """
        if level not in self.levels:
            raise ValueError(f"Invalid level: {level}. Must be 1-4.")
        
        return self.levels[level].copy()
    
    def should_show_visual_cues(self, level):
        """
        Determine if visual cues should be shown for a level.
        
        Args:
            level: Level number
            
        Returns:
            bool: True if visual cues should be shown
        """
        config = self.get_level_config(level)
        return config.get('visual_cues', False)
    
    def get_difficulty_modifier(self, level):
        """
        Get difficulty modifier for a level.
        
        Args:
            level: Level number
            
        Returns:
            str: 'easy', 'medium', 'hard'
        """
        if level == 1:
            return 'easy'
        elif level == 2:
            return 'medium'
        else:
            return 'hard'
    
    def get_level_description(self, level):
        """
        Get human-readable description of a level.
        
        Args:
            level: Level number
            
        Returns:
            str: Level description
        """
        config = self.get_level_config(level)
        return config.get('description', f'Level {level}')
    
    def get_recommended_settings(self, level, resource_type):
        """
        Get recommended settings for a specific resource type and level.
        
        Args:
            level: Level number
            resource_type: Type of resource (e.g., 'matching', 'sorting')
            
        Returns:
            dict: Recommended settings
        """
        base_settings = {
            'show_labels': level == 1,
            'show_borders': True,
            'use_color': level <= 2,
            'complexity': self.get_difficulty_modifier(level)
        }
        
        # Resource-specific adjustments
        if resource_type == 'matching':
            base_settings.update({
                'card_size': 'large' if level <= 2 else 'standard',
                'cards_per_page': 6 if level == 1 else 9
            })
        elif resource_type == 'sorting':
            base_settings.update({
                'categories': 2 if level == 1 else (3 if level == 2 else 4),
                'items_per_category': 3 if level == 1 else 5
            })
        
        return base_settings
    
    def get_all_levels(self):
        """
        Get all available differentiation levels.
        
        Returns:
            list: List of level numbers
        """
        return sorted(self.levels.keys())
    
    def validate_level(self, level):
        """
        Validate that a level number is valid.
        
        Args:
            level: Level number to validate
            
        Returns:
            bool: True if valid
        """
        return level in self.levels


def apply_level_specific_layout(level, base_layout):
    """
    Apply level-specific modifications to a layout.
    
    Args:
        level: Differentiation level
        base_layout: Base layout configuration dict
        
    Returns:
        dict: Modified layout configuration
    """
    layout = base_layout.copy()
    
    if level == 1:
        # Level 1: Maximum support
        layout['spacing'] = layout.get('spacing', 30) * 1.2  # More spacing
        layout['image_size'] = layout.get('image_size', 100) * 1.2  # Larger images
        layout['show_labels'] = True
    elif level == 2:
        # Level 2: Moderate support
        layout['show_labels'] = False
    else:
        # Level 3: Minimal support
        layout['spacing'] = layout.get('spacing', 30) * 0.8  # Less spacing
        layout['image_size'] = layout.get('image_size', 100) * 0.8  # Smaller images
        layout['show_labels'] = False
        layout['increased_items'] = True
    
    return layout


def get_level_color_scheme(level):
    """
    Get color scheme based on differentiation level.
    
    Args:
        level: Level number
        
    Returns:
        dict: Color scheme with 'primary', 'secondary', 'accent' keys
    """
    schemes = {
        1: {
            'primary': (70, 130, 180),    # Steel blue
            'secondary': (255, 255, 255),  # White
            'accent': (255, 215, 0)        # Gold
        },
        2: {
            'primary': (60, 179, 113),     # Medium sea green
            'secondary': (255, 255, 255),  # White
            'accent': (255, 140, 0)        # Dark orange
        },
        3: {
            'primary': (147, 112, 219),    # Medium purple
            'secondary': (255, 255, 255),  # White
            'accent': (220, 20, 60)        # Crimson
        }
    }
    
    return schemes.get(level, schemes[1])


# Global differentiation manager instance
_diff_manager = None

def get_differentiation_manager():
    """
    Get the global differentiation manager instance.
    
    Returns:
        DifferentiationManager: Global manager
    """
    global _diff_manager
    if _diff_manager is None:
        _diff_manager = DifferentiationManager()
    return _diff_manager