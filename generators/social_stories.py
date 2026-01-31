#!/usr/bin/env python3
"""
Social Stories Generator
Generates full-page social stories for sensitive topics using clear, literal, shame-free language.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, HexColor
import os


class SocialStoryGenerator:
    """Generator for creating social stories on sensitive topics."""
    
    def __init__(self, theme_data):
        """Initialize with theme data."""
        self.theme_data = theme_data
        self.theme_name = theme_data.get("theme_name", "Theme")
        self.page_width, self.page_height = letter
        
        # Story database with age-appropriate, shame-free language
        self.story_database = {
            "getting my period": {
                "title": "Getting My Period",
                "pages": [
                    "Sometimes my body will have something called a period.",
                    "A period is when blood comes out of my vagina. This is normal and healthy.",
                    "I might feel my underwear get wet. I might see red or brown on my underwear or on toilet paper.",
                    "I might feel cramping in my belly. I might feel tired or emotional. These feelings are okay.",
                    "When I get my period, I will use a pad or tampon to catch the blood.",
                    "I will tell a trusted adult like my mom, teacher, or school nurse.",
                    "They will help me get supplies and show me what to do.",
                    "If I am not sure what to do, I can always ask a trusted adult for help.",
                    "Getting my period means my body is working the way it should. I am okay."
                ]
            },
            "body odor": {
                "title": "Body Odor and Using Deodorant",
                "pages": [
                    "My body makes sweat. Sweat is liquid that comes out of my skin.",
                    "Sometimes sweat can make a smell. This is called body odor. Everyone has body odor sometimes.",
                    "I might smell body odor on myself or notice other people notice it.",
                    "Body odor is normal, but I can use deodorant to help with the smell.",
                    "I will put deodorant under my arms every morning after I shower or wash.",
                    "Adults can help me choose deodorant and show me how to use it.",
                    "Using deodorant helps me feel clean and confident.",
                    "If I am not sure if I need deodorant, I can ask a trusted adult.",
                    "Taking care of my body is a healthy thing to do."
                ]
            },
            "showering": {
                "title": "Taking a Shower",
                "pages": [
                    "I need to take a shower or bath to keep my body clean.",
                    "Taking a shower means washing my whole body with soap and water.",
                    "I will take a shower alone in the bathroom with the door closed.",
                    "I might feel the water is too hot or too cold at first. I can adjust the temperature.",
                    "I will use soap to wash my body. I will wash my hair with shampoo.",
                    "A trusted adult can help me learn the steps if I need help.",
                    "After my shower, I will dry off and put on clean clothes.",
                    "If I need help or have questions, I can ask a trusted adult.",
                    "Keeping my body clean helps me stay healthy."
                ]
            },
            "private parts": {
                "title": "Private Parts",
                "pages": [
                    "Everyone has private parts. Private parts are parts of my body covered by underwear.",
                    "My private parts are private. That means they are just for me.",
                    "I keep my private parts covered when I am around other people.",
                    "I might touch my private parts when I am alone in private places like my bedroom or bathroom.",
                    "Other people should not touch my private parts. I should not touch other people's private parts.",
                    "Doctors or nurses might need to check my private parts to keep me healthy. A parent or trusted adult will be with me.",
                    "If someone tries to touch my private parts, I will say 'No!' and tell a trusted adult right away.",
                    "If I have questions about my private parts, I can ask a trusted adult.",
                    "My body belongs to me. I am in charge of my body."
                ]
            },
            "using deodorant": {
                "title": "Using Deodorant",
                "pages": [
                    "Deodorant is something I put under my arms to help me smell fresh.",
                    "As I get older, my body makes more sweat. This is normal.",
                    "I will use deodorant every day, usually in the morning.",
                    "I might feel the deodorant is cold or wet at first. That feeling will go away.",
                    "I will lift one arm and rub the deodorant under that arm. Then I will do the other arm.",
                    "A trusted adult can show me which deodorant to use and how to put it on.",
                    "Using deodorant helps me feel confident and clean.",
                    "If the deodorant bothers my skin, I will tell an adult. We can try a different kind.",
                    "Taking care of myself is an important skill I am learning."
                ]
            },
            "wetting accidents": {
                "title": "If I Have a Wetting Accident",
                "pages": [
                    "Sometimes I might have an accident and wet my pants. This can happen to anyone.",
                    "I might feel embarrassed or upset. These feelings are okay.",
                    "If I have an accident, I will tell a trusted adult right away.",
                    "The adult will help me get clean clothes. They will not be angry.",
                    "I will go to the bathroom or a private place to change my clothes.",
                    "Accidents happen. They do not mean I did anything wrong.",
                    "I can prevent accidents by going to the bathroom when I feel like I need to go.",
                    "If accidents happen a lot, a trusted adult can help me figure out why.",
                    "Everyone has accidents sometimes. I am still learning and that's okay."
                ]
            },
            "safe adults": {
                "title": "Safe Adults",
                "pages": [
                    "There are adults in my life who are safe. Safe adults help me and keep me safe.",
                    "Safe adults are people like my parents, teachers, school counselors, and doctors.",
                    "I can talk to safe adults about anything, even if it feels hard to talk about.",
                    "If someone makes me feel uncomfortable or unsafe, I will tell a safe adult.",
                    "Safe adults will listen to me. They will believe me. They will help me.",
                    "If the first safe adult I tell does not help, I will tell another safe adult.",
                    "Safe adults want to keep me healthy and safe. They care about me.",
                    "I can ask safe adults questions about my body, feelings, or anything else.",
                    "Having safe adults in my life helps me feel secure."
                ]
            },
            "privacy": {
                "title": "Privacy",
                "pages": [
                    "Privacy means having time and space to myself.",
                    "I have the right to privacy when I use the bathroom, change clothes, or shower.",
                    "When I need privacy, I can close the door. A closed door means 'private.'",
                    "Other people should knock before opening a closed door. I should knock too.",
                    "I might want privacy when I am upset or need quiet time. That's okay.",
                    "My family and other safe adults will respect my privacy most of the time.",
                    "Sometimes adults need to check on me for safety. That's different from privacy.",
                    "If someone does not respect my privacy, I can tell a safe adult.",
                    "Privacy helps me feel safe and comfortable."
                ]
            }
        }
    
    def generate_story(self, topic, output_dir="output", tone="friendly", age_range="upper elementary", mode="color"):
        """
        Generate a social story PDF for the specified topic.
        
        Args:
            topic: The story topic (e.g., "getting my period")
            output_dir: Directory to save the PDF
            tone: Tone of the story ("clinical", "friendly", "teen-friendly", "simple")
            age_range: Age range ("early childhood", "upper elementary", "teens")
            mode: Output mode - "color" or "bw" (black-and-white)
        """
        # Normalize topic
        topic_key = topic.lower().strip()
        
        # Check if topic exists in database
        if topic_key not in self.story_database:
            print(f"Warning: Topic '{topic}' not found in story database.")
            print(f"Available topics: {', '.join(self.story_database.keys())}")
            return None
        
        story = self.story_database[topic_key]
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with mode suffix
        safe_filename = topic_key.replace(" ", "_").replace("/", "_")
        mode_suffix = f"_{mode}" if mode in ["color", "bw"] else ""
        pdf_filename = os.path.join(output_dir, f"social_story_{safe_filename}{mode_suffix}.pdf")
        
        # Create PDF
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        
        # Generate title page
        self._draw_title_page(c, story["title"], mode=mode)
        c.showPage()
        
        # Generate content pages
        for page_num, content in enumerate(story["pages"], 1):
            self._draw_content_page(c, content, page_num, len(story["pages"]), mode=mode)
            c.showPage()
        
        # Save PDF
        c.save()
        print(f"Generated: {pdf_filename}")
        return pdf_filename
    
    def _draw_title_page(self, c, title, mode="color"):
        """Draw the title page."""
        # Title at top
        c.setFont("Helvetica-Bold", 32)
        title_y = self.page_height - 2 * inch
        
        # Set text color based on mode (black for both, but showing mode-awareness)
        text_color = black if mode == "bw" else black
        
        # Word wrap title if needed
        words = title.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            if c.stringWidth(test_line, "Helvetica-Bold", 32) < self.page_width - 2 * inch:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Center and draw title lines
        for line in lines:
            text_width = c.stringWidth(line, "Helvetica-Bold", 32)
            x = (self.page_width - text_width) / 2
            c.drawString(x, title_y, line)
            title_y -= 40
        
        # Visual placeholder box
        box_size = 4 * inch
        box_x = (self.page_width - box_size) / 2
        box_y = self.page_height / 2 - box_size / 2
        
        c.setStrokeColor(black)
        c.setLineWidth(2)
        c.rect(box_x, box_y, box_size, box_size, stroke=1, fill=0)
        
        # Placeholder text
        c.setFont("Helvetica", 14)
        placeholder_text = "[Visual Support]"
        text_width = c.stringWidth(placeholder_text, "Helvetica", 14)
        c.drawString((self.page_width - text_width) / 2, box_y + box_size / 2, placeholder_text)
        
        # Footer
        self._draw_footer(c, 1, mode=mode)
    
    def _draw_content_page(self, c, content, page_num, total_pages, mode="color"):
        """Draw a content page with text and visual placeholder."""
        margin = 0.75 * inch
        
        # Visual placeholder at top
        box_width = 5 * inch
        box_height = 3 * inch
        box_x = (self.page_width - box_width) / 2
        box_y = self.page_height - margin - box_height - 0.5 * inch
        
        # Set stroke color based on mode
        stroke_color = black if mode == "bw" else black
        c.setStrokeColor(stroke_color)
        c.setLineWidth(2)
        c.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
        
        # Placeholder text in box
        c.setFont("Helvetica", 12)
        placeholder_text = "[Visual Support]"
        text_width = c.stringWidth(placeholder_text, "Helvetica", 12)
        c.drawString((self.page_width - text_width) / 2, box_y + box_height / 2, placeholder_text)
        
        # Content text below box
        text_y = box_y - 0.75 * inch
        
        # Word wrap the content
        c.setFont("Helvetica", 18)
        max_width = self.page_width - 2 * margin
        
        words = content.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            if c.stringWidth(test_line, "Helvetica", 18) < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Draw wrapped lines
        line_height = 28
        for line in lines:
            text_width = c.stringWidth(line, "Helvetica", 18)
            x = (self.page_width - text_width) / 2
            c.drawString(x, text_y, line)
            text_y -= line_height
        
        # Page indicator
        c.setFont("Helvetica", 10)
        page_text = f"Page {page_num} of {total_pages}"
        c.drawString(margin, margin / 2, page_text)
        
        # Footer
        self._draw_footer(c, page_num + 1, mode=mode)
    
    def _draw_footer(self, c, page_num, mode="color"):
        """Draw copyright footer."""
        c.setFont("Helvetica", 9)
        footer_text = "© 2026 Small Wins Studio • For classroom use only"
        text_width = c.stringWidth(footer_text, "Helvetica", 9)
        c.drawString((self.page_width - text_width) / 2, 0.3 * inch, footer_text)
    
    def generate_all_stories(self, output_dir="output", mode="color"):
        """Generate all available social stories."""
        os.makedirs(output_dir, exist_ok=True)
        generated = []
        
        for topic in self.story_database.keys():
            pdf_file = self.generate_story(topic, output_dir, mode=mode)
            if pdf_file:
                generated.append(pdf_file)
        
        print(f"\nGenerated {len(generated)} social stories ({mode} mode) in {output_dir}/")
        return generated


def generate_social_stories_dual_mode(theme_data, output_dir="output"):
    """
    Generate all social stories in both color and black-and-white modes.
    
    Args:
        theme_data: Theme data dictionary
        output_dir: Output directory for PDFs
    
    Returns:
        Dictionary with 'color' and 'bw' lists of generated files
    """
    generator = SocialStoryGenerator(theme_data)
    
    # Generate color versions
    print("\n=== Generating COLOR social stories ===")
    color_files = generator.generate_all_stories(output_dir, mode="color")
    
    # Generate black-and-white versions
    print("\n=== Generating BLACK-AND-WHITE social stories ===")
    bw_files = generator.generate_all_stories(output_dir, mode="bw")
    
    return {
        'color': color_files,
        'bw': bw_files
    }


def main():
    """Main function for testing."""
    # Example theme data
    theme_data = {
        "theme_name": "Brown Bear",
        "primary_color": "#8B4513",
        "secondary_color": "#D2691E"
    }
    
    generator = SocialStoryGenerator(theme_data)
    
    # Generate all stories
    generator.generate_all_stories("output/social_stories")
    
    print("\nSocial Stories Generator - Complete")
    print("\nAvailable topics:")
    for topic in generator.story_database.keys():
        print(f"  - {topic}")


if __name__ == "__main__":
    main()
