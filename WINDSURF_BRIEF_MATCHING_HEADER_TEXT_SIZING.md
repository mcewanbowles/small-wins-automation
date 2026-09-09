# BRIEF: MATCHING_GENERATOR.py — Header Spacing + Label/Text Sizing + Level-Axis Decision
## Status: Send to Windsurf now — do not bundle with other briefs
## Confirmed from: STEL-MATCH-QA_Matching_QA_Page1 (L1/L2/L3) screenshots, July 2026

---

## FIX 1 — Header text block is clipped/squashed (confirmed on all 3 levels)

**Current behaviour:** The header stacks three lines — title ("Matching"),
subtitle ("Stellaluna"), and instruction ("Match the Stellaluna") — with
insufficient vertical spacing. The instruction line is crammed directly
under the subtitle with no breathing room, reads as clipped/overlapping,
and is visually distracting rather than helpful.

**Required behaviour:** Increase the vertical gap between subtitle and
instruction line so all three are clearly separated. Treat this as three
distinct visual tiers, not two:

```
Matching                    <- title, largest, white, bold
Stellaluna                  <- subtitle, medium, navy
Match the Stellaluna         <- instruction, smaller, navy, distinct gap above
```

If header height is fixed, either increase header height slightly to
accommodate three lines properly, or reduce subtitle font size marginally
to free up room — do not let instruction text crowd the subtitle line.

**Also fix on L2:** there is a second, separate "Stellaluna" text heading
rendered large above the target stimulus card (visible on the L2 screenshot,
not present on L1). This duplicates the subtitle immediately above it in
the header and should be removed — the subtitle already establishes the
book name; repeating it above the stimulus card is redundant and adds to
the crowding.

---

## FIX 2 — Level 2 label text is too small to be useful

**Current behaviour:** Labels under each icon ("Nest", "Mango", "Owl",
"Bird", "Stellaluna") are rendered in a very small font relative to the
card size — hard to read at a glance, which defeats the purpose of adding
text support at this level.

**Required behaviour:** Increase label font size substantially. These
labels exist specifically to support reading/word-recognition alongside
the icon — if they're too small to read easily, the level provides no
actual literacy benefit over Level 1. Target roughly 14–16pt (scaled to
DPI) as a starting point, and confirm it's legible at a normal viewing/
printing distance, not just technically present.

---

## FIX 3 — Level 3 text-only cards: text should fill the cell, not float small in the center

**Current behaviour:** With no icon present, Level 3 cards show only a
small centered word ("Nest", "Bird", etc.) in a mostly-empty box — wasted
space, and the text is too small given how much room is available.

**Required behaviour:** When a card has no icon (text-only mode), the word
should scale up to occupy the space the icon would have used — similar
proportions to how the icon fills ~85–90% of the cell in Level 1. Use the
existing shrink-to-fit text logic already in the generator, but with a much
larger starting/base point size for text-only cards specifically, since
there's no competing icon to share space with.

---

## VERIFY THIS WORKED

Regenerate Stellaluna Page 1 at L1, L2 (page 9), and L3 (page 17) and
confirm:

- [ ] Header title/subtitle/instruction have clear, non-overlapping spacing
- [ ] Duplicate "Stellaluna" heading above the L2 stimulus card is removed
- [ ] L2 labels are clearly legible, not squinting-small
- [ ] L3 words are large and visually fill the card, not floating small in empty space

Do not run any other page or level until this screenshot is confirmed correct.

---

## SEPARATE NOTE — level-axis architecture (not part of this fix pass)

Flagging for a follow-on brief, not to be actioned in this pass: the
current L1/L2/L3 structure changes TWO things at once per level — support
type (icon → icon+label → text-only) AND field/distractor composition
(errorless single-target → mixed-category distractors). These are
independent instructional variables in the SPED/AAC literature (symbolic
support fading vs. discrimination-difficulty fading), and collapsing them
into one linear scale limits differentiation flexibility — e.g. there's
currently no way to give a non-reader more distractor challenge, or give
a strong reader errorless practice.

Recommended direction for a future brief: decouple into two independent
parameters — **support type** (icon / icon+label / label+small icon /
text-only) and **field difficulty** (errorless / 1 distractor / 2+
distractors) — so a teacher can combine them per student need rather than
being locked to a fixed ladder. This is a larger architecture change and
should be scoped and sent as its own standalone brief once the current
visual fixes are confirmed working.
