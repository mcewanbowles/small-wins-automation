"""
File Naming Utility

Provides consistent file naming conventions for SPED resources.
"""

import os
import re
from datetime import datetime


def sanitize_filename(name):
    """
    Sanitize a string to be used as a filename.
    
    Args:
        name: String to sanitize
        
    Returns:
        str: Sanitized filename-safe string
    """
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove multiple underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    
    return name


def generate_resource_filename(theme_name, resource_type, level=None, variant=None, extension='pdf'):
    """
    Generate a standardized filename for a SPED resource.
    
    Args:
        theme_name: Name of the theme (e.g., 'Brown_Bear')
        resource_type: Type of resource (e.g., 'Matching_Cards')
        level: Differentiation level (1-4) or None
        variant: Optional variant descriptor (e.g., 'Identical_Errorless')
        extension: File extension (default: 'pdf')
        
    Returns:
        str: Formatted filename
    """
    parts = [sanitize_filename(theme_name), sanitize_filename(resource_type)]
    
    if level is not None:
        parts.append(f"Level{level}")
    
    if variant:
        parts.append(sanitize_filename(variant))
    
    filename = '_'.join(parts) + f'.{extension}'
    
    return filename


def generate_output_path(output_dir, theme_name, resource_type, level=None, variant=None):
    """
    Generate full output path for a resource.
    
    Args:
        output_dir: Base output directory
        theme_name: Theme name
        resource_type: Resource type
        level: Differentiation level
        variant: Variant descriptor
        
    Returns:
        str: Full path to output file
    """
    filename = generate_resource_filename(theme_name, resource_type, level, variant)
    
    # Create theme-specific subdirectory
    theme_dir = os.path.join(output_dir, sanitize_filename(theme_name))
    os.makedirs(theme_dir, exist_ok=True)
    
    return os.path.join(theme_dir, filename)


def generate_timestamp_filename(prefix='resource', extension='pdf'):
    """
    Generate a filename with timestamp.
    
    Args:
        prefix: Filename prefix
        extension: File extension
        
    Returns:
        str: Filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{sanitize_filename(prefix)}_{timestamp}.{extension}"


def create_organized_structure(base_dir, theme_name, resource_types):
    """
    Create an organized directory structure for a theme's resources.
    
    Args:
        base_dir: Base output directory
        theme_name: Theme name
        resource_types: List of resource type names
        
    Returns:
        dict: Mapping of resource_type -> directory path
    """
    theme_dir = os.path.join(base_dir, sanitize_filename(theme_name))
    
    structure = {}
    for resource_type in resource_types:
        resource_dir = os.path.join(theme_dir, sanitize_filename(resource_type))
        os.makedirs(resource_dir, exist_ok=True)
        structure[resource_type] = resource_dir
    
    return structure


def get_level_description(level):
    """
    Get a human-readable description for a differentiation level.
    
    Args:
        level: Level number (1-4)
        
    Returns:
        str: Level description
    """
    descriptions = {
        1: 'Beginner',
        2: 'Intermediate',
        3: 'Advanced',
        4: 'Expert'
    }
    
    return descriptions.get(level, 'Unknown')


def generate_batch_filenames(theme_name, resource_type, count, start_index=1):
    """
    Generate multiple filenames for a batch of resources.
    
    Args:
        theme_name: Theme name
        resource_type: Resource type
        count: Number of filenames to generate
        start_index: Starting index number
        
    Returns:
        list: List of filenames
    """
    filenames = []
    for i in range(count):
        index = start_index + i
        filename = generate_resource_filename(
            theme_name, 
            resource_type, 
            variant=f"Page_{index:02d}"
        )
        filenames.append(filename)
    
    return filenames
