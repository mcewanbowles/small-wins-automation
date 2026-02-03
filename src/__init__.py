"""
SPED TpT Activity Generator System

A comprehensive system for generating Special Education (SPED) 
Teachers Pay Teachers (TpT) activities with accessibility in mind.

Features:
- High contrast, large images at 300 DPI
- Simple, predictable SPED layouts
- Consistent borders and footers
- Multiple activity types: counting mats, bingo, matching, sequencing, 
  coloring, AAC boards, and labels
"""

__version__ = '1.0.0'

from . import utils
from . import generators

__all__ = ['utils', 'generators']
