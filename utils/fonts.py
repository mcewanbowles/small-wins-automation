"""
Font management utilities for SPED-compliant resources.

Provides functions for loading and managing fonts with accessibility in mind.
Uses clear, readable fonts suitable for special education materials.
"""

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
import os


class FontManager:
    """Manages fonts for PDF generation."""
    
    def __init__(self):
        self.fonts_registered = False
        self._register_default_fonts()
    
    def _register_default_fonts(self):
        """Register default fonts that come with reportlab."""
        if not self.fonts_registered:
            # ReportLab comes with standard fonts, we'll use Helvetica family
            # which is clear and accessible
            self.fonts_registered = True
    
    def get_font(self, weight='normal', size=24):
        """
        Get a font name and size for use in PDF generation.
        
        Args:
            weight: 'normal' or 'bold'
            size: Font size in points
            
        Returns:
            tuple: (font_name, font_size)
        """
        if weight == 'bold':
            font_name = 'Helvetica-Bold'
        else:
            font_name = 'Helvetica'
        
        return (font_name, size)
    
    def get_title_font(self):
        """Get font for titles."""
        from utils.config import FONT_SIZES
        return self.get_font('bold', FONT_SIZES['title'])
    
    def get_heading_font(self):
        """Get font for headings."""
        from utils.config import FONT_SIZES
        return self.get_font('bold', FONT_SIZES['heading'])
    
    def get_body_font(self):
        """Get font for body text."""
        from utils.config import FONT_SIZES
        return self.get_font('normal', FONT_SIZES['body'])
    
    def get_small_font(self):
        """Get font for small text."""
        from utils.config import FONT_SIZES
        return self.get_font('normal', FONT_SIZES['small'])
    
    def get_footer_font(self):
        """Get font for footer text."""
        from utils.config import FONT_SIZES
        return self.get_font('normal', FONT_SIZES['footer'])


# Global font manager instance
_font_manager = None

def get_font_manager():
    """Get the global font manager instance."""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager
