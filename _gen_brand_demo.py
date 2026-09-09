"""Generate the brand demo as 3 separate PDFs (matching StudioForge standard).

PRODUCT STRUCTURE (5 activities + social story formats + support docs):

  Activities PDF (coverless):
    1. Social Story (full-page)
    2. Scenario Sort/Game/Cards (with Yes/No discussion mode)
    3. Choice Board (with cut-out option pieces)
    4. Visual Support Cards (large format + routine strip template)
    5. AAC Board

  Social Story Formats PDF:
    - Half-page story (2-up booklet)
    - Mini book (4-up quarter-page)
    - Participation pieces (cut-out matching)

  Support docs PDF:
    - Cover
    - Teacher Guide & Terms of Use
    - IEP Data Sheet (support document, not an activity)
"""
import json
from dignity_brand import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

TOPIC_JSON = r"D:\Seagate\small-wins-automation\01_ACTIVE_FACTORY\pipeline_products\hands_out_of_pants_ENRICHED_DRAFT_v1.json"
with open(TOPIC_JSON, encoding="utf-8") as f:
    TOPIC = json.load(f)

PACK_CODE = "DN-HOP"

# ──────────────────────────────────────────────────────────────────────────
# 1. ACTIVITIES PDF (coverless, 10 pages)
# ──────────────────────────────────────────────────────────────────────────
activities_path = r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_activities.pdf"
c = canvas.Canvas(activities_path, pagesize=letter)

ACTIVITY_PAGES = 11
pg = 0

# ── ACTIVITY 1: SOCIAL STORY (full-page) ──
pg += 1
draw_dignity_frame(c, title="Social Story", subtitle="Picture Main Layout",
                   pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                   product_type="Social Story")
cx, cy, cw, ch = content_bounds(has_subtitle=True)
story_pages = TOPIC.get("story_pages", [])
first_line = story_pages[0] if story_pages else "My body belongs to me."
draw_wrapped_text(c, first_line, cx, cy + ch - 30, cw, size=18,
                  font=BRAND_FONT_BOLD, align="center")
draw_icon_placeholder(c, cx + 50, cy + 50, cw - 100, ch - 120, "body")
c.showPage()

# ── ACTIVITY 2: SCENARIO SORT/GAME/CARDS (with Yes/No mode) ──
sort_data = TOPIC.get("scenario_sort", {})
sort_scenarios = [(s.get("text", s.get("scenario", "")), s.get("answer", "PUBLIC"))
                  for s in sort_data.get("scenarios", [])]
if not sort_scenarios:
    sort_scenarios = [
        ("I am in the classroom", "PUBLIC"),
        ("I am in the bathroom with door closed", "PRIVATE"),
        ("I am on the playground", "PUBLIC"),
        ("I am in my bedroom alone", "PRIVATE"),
        ("I am on the school bus", "PUBLIC"),
        ("I am in a public toilet cubicle", "PRIVATE"),
        ("I am at the dinner table", "PUBLIC"),
        ("I am getting dressed in my room", "PRIVATE"),
    ]

pg += 1
draw_sort_board(c, title="Scenario Sort", subtitle="Public or Private?",
                pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                scenarios=sort_scenarios)

pg += 1
draw_game_board(c, title="Scenario Game", subtitle="Public or Private?",
                pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                scenarios=sort_scenarios)

pg += 1
card_scenarios = [
    ("I am in the classroom", "PUBLIC", "classroom"),
    ("I am in the bathroom with door closed", "PRIVATE", "bathroom"),
    ("I am on the playground", "PUBLIC", "playground"),
    ("I am in my bedroom alone", "PRIVATE", "bedroom"),
    ("I am on the school bus", "PUBLIC", "school_bus"),
    ("I am in a public toilet cubicle", "PRIVATE"),
    ("I am at the dinner table", "PUBLIC", "dinner"),
    ("I am getting dressed in my room", "PRIVATE"),
    ("I am in the school library", "PUBLIC", "library"),
    ("I am in the shower at home", "PRIVATE", "shower"),
    ("I am at the shops", "PUBLIC", "shops"),
    ("I am on the toilet at home", "PRIVATE"),
    ("I am at a friends house", "PUBLIC", "friends"),
    ("I am changing for PE class", "PRIVATE"),
    ("I am in the car with family", "PUBLIC", "car"),
    ("I am in a changing room", "PRIVATE"),
]
draw_game_cards(c, title="Scenario Cards", subtitle="Cut out for sort and game",
                pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                scenarios=card_scenarios)

# Yes/No discussion mode (same concepts, different mechanic)
yn_data = TOPIC.get("yes_no_sometimes_cards", {})
simple_data = yn_data.get("version_simple", {})
simple_questions = simple_data.get("questions", [])
if not simple_questions:
    simple_questions = [
        {"question": "Is it okay to touch my body in the classroom?", "answer": "no",
         "discussion": "Classroom is public. What can you do instead?", "icon": "classroom"},
        {"question": "Is it okay to touch my body on the bus?", "answer": "no",
         "discussion": "Bus is public.", "icon": "school_bus"},
        {"question": "Is it okay in my bedroom with door closed?", "answer": "yes",
         "discussion": "Bedroom with door closed is private.", "icon": "bedroom"},
        {"question": "Is it okay to have body feelings?", "answer": "yes",
         "discussion": "Everyone has body feelings.", "icon": "body"},
        {"question": "Should I ask for help if uncomfortable?", "answer": "yes",
         "discussion": "Who can you ask?", "icon": "help"},
        {"question": "Is it okay to touch my body at lunch?", "answer": "no",
         "discussion": "Cafeteria is public.", "icon": "dinner"},
    ]

pg += 1
draw_yes_no_cards(c, title="Is This Okay?", subtitle="Discussion cards — YES or NO",
                  pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                  version="simple", questions=simple_questions)

adv_data = yn_data.get("version_advanced", {})
adv_questions = adv_data.get("questions", [])
if not adv_questions:
    adv_questions = [
        {"question": "Is it okay to touch my body in a public toilet cubicle?",
         "answer": "sometimes", "discussion": "Cubicle is private, but bathroom is shared.", "icon": "bathroom"},
        {"question": "Is it okay to fix my clothes in public?",
         "answer": "sometimes", "discussion": "Quick fix is okay. Bathroom for more.", "icon": "door"},
        {"question": "Is it okay to touch my body at a friends house?",
         "answer": "sometimes", "discussion": "Depends on the family's rules.", "icon": "friends"},
        {"question": "Is it okay to have body feelings at school?",
         "answer": "yes", "discussion": "Feelings are okay. The rule is about WHERE.", "icon": "classroom"},
        {"question": "Should I tell someone if I feel unsafe?",
         "answer": "yes", "discussion": "Always tell a safe adult.", "icon": "help"},
        {"question": "Is it okay to touch my body in the classroom?",
         "answer": "no", "discussion": "Classroom is public. Use a replacement behavior.", "icon": "classroom"},
    ]

pg += 1
draw_yes_no_cards(c, title="Is This Okay?", subtitle="Discussion cards — YES, NO, or SOMETIMES",
                  pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                  version="advanced", questions=adv_questions)

# ── ACTIVITY 3: CHOICE BOARD (with cut-out options) ──
pg += 1
choice_data = TOPIC.get("alternative_behavior_options", {})
choice_options = choice_data.get("options", [])
if not choice_options:
    choice_options = [
        {"text": "Ask for a break", "icon": "break", "setting": "school"},
        {"text": "Use a fidget tool", "icon": "fidget", "setting": "school + home"},
        {"text": "Squeeze my hands", "icon": "hands", "setting": "anywhere"},
        {"text": "Do a hands-busy activity", "icon": "activity", "setting": "school"},
        {"text": "Ask for help", "icon": "help", "setting": "anywhere"},
        {"text": "Go to a private place", "icon": "door", "setting": "home"},
    ]
draw_choice_board(c, title="Choice Board", subtitle="Cut out and select replacement behaviors",
                  pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                  options=choice_options)

# ── ACTIVITY 4: VISUAL SUPPORT CARDS (large + routine strip) ──
visual_data = TOPIC.get("visual_support_cards", {})
visual_cards = visual_data.get("cards", [])
if not visual_cards:
    visual_cards = [
        {"text": "My body", "icon": "body", "purpose": "Body ownership"},
        {"text": "Hands out", "icon": "stop", "purpose": "In-the-moment reminder"},
        {"text": "I need a break", "icon": "break", "purpose": "Request sensory break"},
        {"text": "Hands busy", "icon": "fidget", "purpose": "Redirect to replacement"},
        {"text": "Help please", "icon": "help", "purpose": "Ask for adult support"},
        {"text": "Squeeze hands", "icon": "hands", "purpose": "Proprioceptive input"},
        {"text": "Public", "icon": "public", "purpose": "Concept — public places"},
        {"text": "Private", "icon": "private", "purpose": "Concept — private places"},
        {"text": "Door closed", "icon": "door", "purpose": "Private means door closed"},
        {"text": "My bedroom", "icon": "bedroom", "purpose": "Private place at home"},
        {"text": "Bathroom", "icon": "bathroom", "purpose": "For fixing clothes"},
        {"text": "Safe", "icon": "safe", "purpose": "Keeping my body safe"},
    ]

pg += 1
if_then_prompts = [
    {"feeling": "uncomfortable", "action": "ask for a break", "icon": "break"},
    {"feeling": "my hands want to touch", "action": "use a fidget", "icon": "fidget"},
    {"feeling": "unsafe", "action": "tell a safe adult", "icon": "help"},
    {"feeling": "the urge", "action": "squeeze my hands", "icon": "hands"},
]
draw_visual_support_cards(c, title="Visual Support Cards", subtitle="Concepts + if-then behavior prompts",
                          pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                          cards=visual_cards, if_then_prompts=if_then_prompts)

# Routine strip template (same cards, arranged in sentences)
routine_data = TOPIC.get("routine_strip_template", {})
routine_examples = routine_data.get("examples", [])
behavior_pieces = list(set([ex.get("behavior", "") for ex in routine_examples if ex.get("behavior")]))
location_pieces = list(set([ex.get("location", "") for ex in routine_examples if ex.get("location")]))
if not behavior_pieces:
    behavior_pieces = ["Hands out", "Hands busy", "Ask for a break", "Use a fidget",
                       "Squeeze hands", "Private body care", "Wash hands"]
if not location_pieces:
    location_pieces = ["classroom", "at my desk", "when I feel uncomfortable",
                       "when my hands want to touch", "my bedroom, door closed",
                       "the bathroom, door closed", "when I am finished"]

pg += 1
draw_routine_strip(c, title="Routine Strip", subtitle="Build a routine with the visual cards",
                   pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
                   template_text="___ is for ___",
                   behavior_pieces=behavior_pieces,
                   location_pieces=location_pieces,
                   examples=routine_examples)

# ── ACTIVITY 5: AAC BOARD (landscape for larger cells) ──
pg += 1
aac_data = TOPIC.get("aac_board", {})
core_words = aac_data.get("core_words_fixed", [])
fringe_words = aac_data.get("fringe_12", [])
discussion_phrases = aac_data.get("discussion_phrases", [])
if not core_words:
    core_words = ["I", "you", "want", "see", "yes", "no", "same", "different",
                  "more", "help", "like", "dont_like", "go", "stop", "choose",
                  "turn_the_page", "read", "think", "uh_oh", "what", "where",
                  "why", "dont_know", "finished"]
if not fringe_words:
    fringe_words = ["private", "public", "hands", "pants", "body", "touch",
                    "break", "fidget", "door", "bedroom", "bathroom", "safe"]
# Switch to landscape for this page
from reportlab.lib.pagesizes import letter as _letter
c.setPageSize((_letter[1], _letter[0]))  # landscape
draw_aac_board(c, title="My Body Communication Board", subtitle="AAC — color variant",
               pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
               core_words=core_words, fringe_words=fringe_words,
               discussion_phrases=discussion_phrases)

# Hi-vis variant (black on yellow for print accessibility)
pg += 1
c.setPageSize((_letter[1], _letter[0]))  # landscape
draw_aac_board(c, title="My Body Communication Board", subtitle="AAC — high-visibility variant",
               pack_code=PACK_CODE, page_num=pg, total_pages=ACTIVITY_PAGES,
               core_words=core_words, fringe_words=fringe_words,
               discussion_phrases=discussion_phrases, hi_vis=True)
# Reset to portrait for any subsequent pages
c.setPageSize(_letter)

c.save()
print(f"Activities PDF: {activities_path}")
print(f"  Pages: {ACTIVITY_PAGES} (coverless)")

# ──────────────────────────────────────────────────────────────────────────
# 2. SOCIAL STORY FORMATS PDF (half-page + mini book + participation pieces)
# ──────────────────────────────────────────────────────────────────────────
formats_path = r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_social_story_formats.pdf"
c = canvas.Canvas(formats_path, pagesize=letter)

# Build story_pages with icon names
story_icon_map = {
    0: "body", 1: "body", 2: "underwear", 3: "okay", 4: "door",
    5: "people", 6: "door", 7: "classroom", 8: "wait", 9: "hands",
    10: "bathroom", 11: "adults", 12: "talk", 13: "stop",
    14: "okay", 15: "safe",
}
story_pairs = []
for i, text in enumerate(story_pages):
    icon = story_icon_map.get(i, "")
    story_pairs.append((text, icon))

total_story_pages = len(story_pairs)

# ── Half-page story (2-up) ──
total_half_sheets = (total_story_pages + 1) // 2
for sheet_num in range(total_half_sheets):
    pair = story_pairs[sheet_num * 2: sheet_num * 2 + 2]
    while len(pair) < 2:
        pair.append(("", ""))
    draw_half_page_story_sheet(c, pack_code=PACK_CODE, page_num=sheet_num + 1,
                               total_pages=total_story_pages, story_pages=pair)

# ── Mini adapted book (4-up, includes participation pieces) ──
total_mini_sheets = (total_story_pages + 3) // 4
for sheet_num in range(total_mini_sheets):
    quad = story_pairs[sheet_num * 4: sheet_num * 4 + 4]
    while len(quad) < 4:
        quad.append(("", ""))
    draw_mini_book_sheet(c, pack_code=PACK_CODE, sheet_num=sheet_num + 1,
                         total_sheets=total_mini_sheets, story_pages=quad)

# ── Participation pieces (cut-out matching) ──
pieces_data = TOPIC.get("cut_out_pieces", {})
pieces = pieces_data.get("pieces", [])
if not pieces:
    pieces = [
        {"text": "My body", "icon": "body"},
        {"text": "Hands out", "icon": "stop"},
        {"text": "I need a break", "icon": "break"},
        {"text": "Hands busy", "icon": "fidget"},
        {"text": "Help please", "icon": "help"},
        {"text": "Use a fidget", "icon": "fidget"},
        {"text": "Squeeze hands", "icon": "hands"},
        {"text": "Public", "icon": "public"},
        {"text": "Private", "icon": "private"},
        {"text": "Door closed", "icon": "door"},
        {"text": "My bedroom", "icon": "bedroom"},
        {"text": "Bathroom", "icon": "bathroom"},
    ]
# Participation pieces page number continues after mini book
participation_page = total_half_sheets + total_mini_sheets + 1
total_format_pages = participation_page
draw_participation_pieces(c, title="Participation Pieces", subtitle="Cut-out matching for the story",
                          pack_code=PACK_CODE, page_num=participation_page,
                          total_pages=total_format_pages, pieces=pieces)

c.save()
total_format_sheets = total_half_sheets + total_mini_sheets + 1
print(f"Social story formats PDF: {formats_path}")
print(f"  Sheets: {total_format_sheets} (half-page: {total_half_sheets}, mini adapted book: {total_mini_sheets}, participation: 1)")

# ──────────────────────────────────────────────────────────────────────────
# 3. SUPPORT DOCS PDF (cover + teacher guide & TOU + IEP data sheet)
# ──────────────────────────────────────────────────────────────────────────
support_path = r"D:\Seagate\small-wins-automation\Dignity\products\_brand_demo_support.pdf"
c = canvas.Canvas(support_path, pagesize=letter)

SUPPORT_PAGES = 3

draw_dignity_cover(
    c,
    title="Hands Out of Pants in Public",
    subtitle="A social story about private body behavior",
    pack_code=PACK_CODE,
    topic_id="hands_out_of_pants",
    content_warning="Sensitive topic: private touching",
    page_num=1,
    total_pages=SUPPORT_PAGES,
    is_bundle=True,
    components_included=[
        "Social Story — full page (classroom display)",
        "Social Story — half page (personal booklet)",
        "Mini Adapted Book (quarter-page + participation pieces)",
        "Scenario Sort (public vs private)",
        "Scenario Game (board game + discussion cards)",
        "Scenario Cards (with icons for differentiation)",
        "Choice Board (cut-out replacement behaviors)",
        "Visual Support Cards (concepts + if-then prompts)",
        "AAC Board (color + high-visibility variants)",
    ],
    bonus_included=[
        "IEP Monitoring Form (progress tracking)",
        "Teacher Guide & Terms of Use",
    ],
)

draw_support_doc_page(
    c,
    pack_code=PACK_CODE,
    page_num=2,
    total_pages=SUPPORT_PAGES,
    notes=[
        "This resource is a starting point, not a prescription. Select the pages that suit your student.",
        "Social Story: full-page for classroom display, half-page for personal booklet, mini adapted book for pocket-sized take-home.",
        "Mini Adapted Book: includes participation pieces for interactive engagement during read-alouds.",
        "Scenario activity: sort cards into PUBLIC/PRIVATE columns, play the board game, or use discussion cards (YES/NO/SOMETIMES).",
        "Choice Board: cut out replacement behavior options. Student selects what works for them.",
        "Visual Support Cards: concept cards for classroom + lanyard, plus if-then behavior prompts ('If I feel uncomfortable, I can ask for a break').",
        "AAC Board: color and high-visibility variants for print accessibility.",
        "Do not shame the behavior. Teach where and when it is appropriate.",
        "Coordinate with families. Home and school strategies should be consistent.",
    ],
    references=[
        "NSVRC (2018). Sexuality education for people with disabilities: A resource guide.",
        "SIECUS (2018). Guidelines for comprehensive sexuality education for individuals with disabilities.",
        "Walker-Hirsch, L. & Reynolds, J. (2007). The Facts of Life...and More: Sexuality and Intimacy for People with Disabilities.",
    ],
)

# IEP Data Sheet (support document)
iep_data = TOPIC.get("iep_data_sheet", {})
iep_goals = iep_data.get("goals", [])
if not iep_goals:
    iep_goals = [
        {"goal": "Given a visual prompt, STUDENT will keep hands outside pants in public settings.",
         "measurement": "Frequency count + prompt level",
         "baseline": "___ incidents per ___ min", "target": "___ or fewer per ___ min"},
        {"goal": "Given alternative behavior options, STUDENT will select a replacement behavior.",
         "measurement": "Opportunity-based",
         "baseline": "___ of ___ opportunities", "target": "___ of ___ opportunities"},
        {"goal": "Given a scenario card, STUDENT will correctly sort public vs private.",
         "measurement": "Percentage correct per session",
         "baseline": "___% accuracy", "target": "___% accuracy"},
        {"goal": "STUDENT will independently request a break or help using AAC or pictures.",
         "measurement": "Opportunity-based",
         "baseline": "___ of ___ opportunities", "target": "___ of ___ opportunities"},
    ]
draw_iep_data_sheet(c, title="IEP Goals & Data", subtitle="Progress monitoring — support document",
                    pack_code=PACK_CODE, page_num=3, total_pages=SUPPORT_PAGES,
                    goals=iep_goals)

c.save()
print(f"Support docs PDF: {support_path}")
print(f"  Pages: {SUPPORT_PAGES} (cover + teacher guide & TOU + IEP data sheet)")
