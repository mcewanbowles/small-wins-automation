#!/usr/bin/env python3
"""
IEP Goal Bank Generator
Small Wins Studio

Generates print-friendly IEP goal bank PDFs organized by domain, subdomain, and level.
Follows Small Wins Studio branding and design standards.
"""

import json
import os
import sys
import argparse
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for page numbering in footer"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        """Draw footer with copyright and page numbers"""
        self.saveState()
        self.setFont("Helvetica", 9)
        
        # Left side: copyright
        self.setFillColor(colors.HexColor("#666666"))
        self.drawString(0.75 * inch, 0.5 * inch, "© 2025 Small Wins Studio. All rights reserved.")
        
        # Right side: page number
        page_num = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 0.5 * inch, 0.5 * inch, page_num)
        
        self.restoreState()


class IEPGoalBankGenerator:
    """Generator for IEP Goal Bank PDFs"""
    
    # Level ordering
    LEVEL_ORDER = ["Emerging", "Developing", "Proficient", "Generalisation"]
    
    def __init__(self, data_file):
        """Initialize generator with data file path"""
        self.data_file = data_file
        self.data = None
        self.styles = None
        
    def load_data(self):
        """Load goal data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
            print(f"Loaded data from {self.data_file}")
            return True
        except FileNotFoundError:
            print(f"Error: Data file not found: {self.data_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in data file: {e}")
            return False
    
    def setup_styles(self):
        """Setup custom paragraph styles for the document"""
        styles = getSampleStyleSheet()
        
        # Try to use Comic Sans MS, fallback to Helvetica
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            # Try to register Comic Sans MS (may not be available on all systems)
            # For Linux systems, Comic Sans MS is typically not available
            # We'll use Helvetica as the standard fallback
            primary_font = "Helvetica"
        except:
            primary_font = "Helvetica"
        
        # Title style
        styles.add(ParagraphStyle(
            name='IEPTitle',
            parent=styles['Heading1'],
            fontName=f'{primary_font}-Bold',
            fontSize=20,
            textColor=colors.HexColor("#1E3A5F"),
            spaceAfter=6,
            alignment=TA_CENTER
        ))
        
        # Subtitle style (domain name)
        styles.add(ParagraphStyle(
            name='IEPSubtitle',
            parent=styles['Heading2'],
            fontName=f'{primary_font}-Bold',
            fontSize=15,
            textColor=colors.HexColor("#1E3A5F"),
            spaceAfter=4,
            alignment=TA_CENTER
        ))
        
        # Tagline style
        styles.add(ParagraphStyle(
            name='Tagline',
            parent=styles['Normal'],
            fontName=primary_font,
            fontSize=9,
            textColor=colors.HexColor("#666666"),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        # Subdomain heading style
        styles.add(ParagraphStyle(
            name='SubdomainHeading',
            parent=styles['Heading3'],
            fontName=f'{primary_font}-Bold',
            fontSize=12,
            textColor=colors.HexColor("#1E3A5F"),
            spaceBefore=12,
            spaceAfter=8,
            alignment=TA_LEFT
        ))
        
        # Goal text style
        styles.add(ParagraphStyle(
            name='GoalText',
            parent=styles['Normal'],
            fontName=primary_font,
            fontSize=10,
            textColor=colors.black,
            spaceAfter=6,
            leading=12,
            alignment=TA_LEFT,
            leftIndent=0.25 * inch
        ))
        
        # Goal metadata style (for optional fields)
        styles.add(ParagraphStyle(
            name='GoalMeta',
            parent=styles['Normal'],
            fontName=f'{primary_font}-Oblique',
            fontSize=9,
            textColor=colors.HexColor("#666666"),
            spaceAfter=10,
            alignment=TA_LEFT,
            leftIndent=0.5 * inch
        ))
        
        self.styles = styles
    
    def create_header(self, domain_name=None):
        """Create document header with title and optional domain filter"""
        elements = []
        
        # Title
        title = Paragraph("IEP Goal Bank", self.styles['IEPTitle'])
        elements.append(title)
        
        # Subtitle (domain name if filtered)
        if domain_name:
            subtitle = Paragraph(domain_name, self.styles['IEPSubtitle'])
            elements.append(subtitle)
        
        # Tagline
        tagline = Paragraph("Small Wins Studio — Classroom-Ready IEP Supports", self.styles['Tagline'])
        elements.append(tagline)
        
        return elements
    
    def format_goal_entry(self, goal):
        """Format a single goal entry with level and text"""
        elements = []
        
        # Goal text with bold level label
        level = goal.get('level', 'Unknown')
        goal_text = goal.get('goal_text', '')
        
        formatted_text = f"<b>{level}:</b> {goal_text}"
        para = Paragraph(formatted_text, self.styles['GoalText'])
        elements.append(para)
        
        # Optional metadata fields
        meta_parts = []
        if 'criteria' in goal and goal['criteria']:
            meta_parts.append(f"Criteria: {goal['criteria']}")
        if 'prompt_level' in goal and goal['prompt_level']:
            meta_parts.append(f"Prompt: {goal['prompt_level']}")
        if 'measurement_type' in goal and goal['measurement_type']:
            meta_parts.append(f"Measurement: {goal['measurement_type']}")
        if 'notes' in goal and goal['notes']:
            meta_parts.append(f"Notes: {goal['notes']}")
        
        if meta_parts:
            meta_text = " | ".join(meta_parts)
            meta_para = Paragraph(meta_text, self.styles['GoalMeta'])
            elements.append(meta_para)
        
        return elements
    
    def sort_goals_by_level(self, goals):
        """Sort goals by level according to defined order"""
        def level_sort_key(goal):
            level = goal.get('level', '')
            try:
                return self.LEVEL_ORDER.index(level)
            except ValueError:
                return 999  # Unknown levels go to end
        
        return sorted(goals, key=level_sort_key)
    
    def generate_domain_content(self, domain):
        """Generate content for a single domain"""
        elements = []
        
        # Process each subdomain
        for subdomain in domain.get('subdomains', []):
            subdomain_name = subdomain.get('name', 'Unnamed Subdomain')
            
            # Subdomain heading
            heading = Paragraph(subdomain_name, self.styles['SubdomainHeading'])
            elements.append(heading)
            
            # Sort goals by level
            goals = self.sort_goals_by_level(subdomain.get('goals', []))
            
            # Format each goal
            for goal in goals:
                goal_elements = self.format_goal_entry(goal)
                elements.extend(goal_elements)
            
            # Small spacer between subdomains
            elements.append(Spacer(1, 0.1 * inch))
        
        return elements
    
    def generate_pdf(self, output_file, domain_filter=None):
        """
        Generate PDF document
        
        Args:
            output_file: Path to output PDF file
            domain_filter: Optional domain name to filter by (None for all domains)
        """
        if not self.data:
            print("Error: No data loaded. Call load_data() first.")
            return False
        
        if not self.styles:
            self.setup_styles()
        
        # Create document
        doc = SimpleDocTemplate(
            output_file,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.75 * inch
        )
        
        # Build content
        story = []
        
        # Filter domains if specified
        domains = self.data.get('domains', [])
        if domain_filter:
            domains = [d for d in domains if d.get('name') == domain_filter]
            if not domains:
                print(f"Warning: No domain found with name '{domain_filter}'")
                return False
        
        # Sort domains alphabetically
        domains = sorted(domains, key=lambda d: d.get('name', ''))
        
        # Generate content for each domain
        for i, domain in enumerate(domains):
            domain_name = domain.get('name', 'Unnamed Domain')
            
            # Add header (show domain name in subtitle for filtered view or multi-domain)
            if domain_filter or len(domains) > 1:
                header_elements = self.create_header(domain_name)
            else:
                header_elements = self.create_header()
            
            story.extend(header_elements)
            
            # Add domain content
            content_elements = self.generate_domain_content(domain)
            story.extend(content_elements)
            
            # Page break between domains (except for last domain)
            if i < len(domains) - 1:
                story.append(PageBreak())
        
        # Build PDF with custom canvas for page numbers
        try:
            doc.build(story, canvasmaker=NumberedCanvas)
            print(f"Successfully generated: {output_file}")
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
    
    def generate_all_samples(self, output_dir):
        """Generate all sample PDFs"""
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        # Generate all domains PDF
        all_domains_file = os.path.join(output_dir, "iep_goal_bank_sample_all_domains.pdf")
        success = self.generate_pdf(all_domains_file, domain_filter=None)
        results.append(("All Domains", success))
        
        # Generate individual domain PDFs
        if self.data:
            for domain in self.data.get('domains', []):
                domain_name = domain.get('name', '')
                if domain_name:
                    safe_name = domain_name.lower().replace(' ', '_')
                    domain_file = os.path.join(output_dir, f"iep_goal_bank_sample_{safe_name}.pdf")
                    success = self.generate_pdf(domain_file, domain_filter=domain_name)
                    results.append((domain_name, success))
        
        return results


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='Generate IEP Goal Bank PDFs for Small Wins Studio'
    )
    parser.add_argument(
        '--output',
        choices=['all', 'communication', 'literacy'],
        default='all',
        help='Which PDF(s) to generate (default: all)'
    )
    parser.add_argument(
        '--data',
        default='data/iep_goal_bank/sample_goals.json',
        help='Path to goals data JSON file'
    )
    parser.add_argument(
        '--outdir',
        default='samples/iep_goal_bank',
        help='Output directory for PDFs'
    )
    
    args = parser.parse_args()
    
    # Get absolute paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    data_file = os.path.join(repo_root, args.data)
    output_dir = os.path.join(repo_root, args.outdir)
    
    # Create generator
    generator = IEPGoalBankGenerator(data_file)
    
    # Load data
    if not generator.load_data():
        return 1
    
    generator.setup_styles()
    
    # Generate requested PDFs
    if args.output == 'all':
        print("\nGenerating all sample PDFs...")
        results = generator.generate_all_samples(output_dir)
        
        print("\n=== Generation Summary ===")
        for name, success in results:
            status = "✓" if success else "✗"
            print(f"{status} {name}")
        
        all_success = all(success for _, success in results)
        return 0 if all_success else 1
    
    else:
        # Generate single domain
        domain_name = args.output.capitalize()
        safe_name = args.output.lower()
        output_file = os.path.join(output_dir, f"iep_goal_bank_sample_{safe_name}.pdf")
        
        os.makedirs(output_dir, exist_ok=True)
        success = generator.generate_pdf(output_file, domain_filter=domain_name)
        
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
