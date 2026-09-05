# AAC Vocab Builder Report — NEEDS_REVIEW batch
**Generated:** 05 Sep 2026 21:50
**Books processed:** 1
**Failed:** 0
**Total ambiguous words flagged:** 3

⚠️ **Nothing here has been written to real book_vocab.json.** Every book
below is sitting in its own `needs_review_vocab.json`. Read this report,
spot-check the summaries against books you know, then run:
`python AAC_VOCAB_BUILDER.py --promote <slug>` (or `--promote-all`)
for the ones you're happy with.

## ⚠️ Ambiguous Words — Review These

| Book | Word | Issue | Preferred Icon | Reason |
|------|------|-------|----------------|--------|
| Chrysanthemum | **blossom** | Could depict a flower blooming or a figurative 'blossoming' of confidence/happiness in a character | `mouse blossoming/glowing with confidence` | The book uses 'blossomed' figuratively to describe Chrysanthemum's restored confidence after Mrs. Twinkle's support, not a literal plant |
| Chrysanthemum | **petals** | Could be interpreted as a real flower's petals vs. the fantastical image of petals sprouting from the character in her nightmare | `petals sprouting from mouse (nightmare scene)` | In the book, petals appear specifically in Chrysanthemum's nightmare as parts of her own body, tied to the bullying threat to 'pluck' her |
| Chrysanthemum | **wilt** | Could depict a literal plant wilting or a character/emotional wilting (drooping posture, feeling crushed) | `mouse drooping/wilting posture` | In the book it describes Chrysanthemum's emotional reaction to teasing, illustrated as her drooping like a flower — pair image should show the mouse character wilting, not a houseplant |

## 🎭 Hero Images to Source — PRIORITY

| Book | Hero Character | Search Term | Notes |
|------|---------------|-------------|-------|
| Chrysanthemum | **Chrysanthemum** | `Chrysanthemum mouse Kevin Henkes` | Distinctive Henkes mouse illustration style — generic Boardmaker mouse will not match the character children recognize from the cover; source from Kevin Henkes fan art / TPT clip art if available |

## 📚 Full Vocab by Book (all NEEDS_REVIEW)

### Chrysanthemum
**Slug:** `chrysanthemum` | **Author:** Kevin Henkes | **Year:** 1991
**Summary (check this first):** Chrysanthemum is a young mouse who is <cite index="11-3,11-4,11-5">a perfect baby, and she had a perfect name... When she was old enough to appreciate it, Chrysanthemum loved her name. And then she started school.</cite> Classmate <cite index="11-17,11-18">Victoria, a particularly observant and mean-spirited classmate, announces that Chrysanthemum's name takes up 13 letters... "That's half the letters in the alphabet!"</cite> leading other kids to tease her, but everything changes when <cite index="11-12,11-13,11-14">the students were introduced to their music teacher, Mrs. Twinkle. Mrs. Delphinium Twinkle. And suddenly, Chrysanthemum blossomed.</cite>
**Hero (slot 1):** Chrysanthemum — search `Chrysanthemum mouse Kevin Henkes` [⚠️ needs sourcing]
**Fringe words + why (slots 2–12):**
  - **name** — Central conflict of the whole book — Chrysanthemum loved her name until classmates mocked it; the story's plot literally revolves around her name.
  - **school** — The teasing only begins once Chrysanthemum starts school, per the book's own turning point: 'And then she started school.'
  - **tease** — Victoria, Jo, and Rita repeatedly tease Chrysanthemum about her name being 'too long' and 'named after a flower.'
  - **flower** — Chrysanthemum is named after the chrysanthemum flower, which Victoria mocks by saying 'You're named after a flower' — the root of every taunt in the book.
  - **sad** — Chrysanthemum feels sad and self-conscious each time Victoria and Jo tease her, deflating her earlier confidence.
  - **happy** — Before starting school, Chrysanthemum was happy and proud of her name, per the opening pages describing her joy in it.
  - **teacher** — Mrs. Twinkle, the new music teacher, is the character who ultimately helps Chrysanthemum feel proud of her name again.
  - **wilt** — The book's exact recurring phrase 'Chrysanthemum wilted' describes her reaction each time she is teased about her name.
  - **blossom** — The resolution line 'And suddenly, Chrysanthemum blossomed' marks the moment her confidence is restored by Mrs. Twinkle.
  - **petals** — In her nightmare, Chrysanthemum sprouts petals like the flower she's named for, and Victoria picks them off one by one — a key fantastical scene in the book.
  - **baby** — The book ends with Mrs. Twinkle giving birth to a baby girl whom she names Chrysanthemum, mirroring and validating the title character's name.
**⚠️ Ambiguous:** `wilt` → use `mouse drooping/wilting posture` (In the book it describes Chrysanthemum's emotional reaction to teasing, illustrated as her drooping like a flower — pair image should show the mouse character wilting, not a houseplant)
**⚠️ Ambiguous:** `blossom` → use `mouse blossoming/glowing with confidence` (The book uses 'blossomed' figuratively to describe Chrysanthemum's restored confidence after Mrs. Twinkle's support, not a literal plant)
**⚠️ Ambiguous:** `petals` → use `petals sprouting from mouse (nightmare scene)` (In the book, petals appear specifically in Chrysanthemum's nightmare as parts of her own body, tied to the bullying threat to 'pluck' her)
**Notes:** Existing activity_images already cover 'flower, name, school, tease, sad, happy' and aac_extras cover 'teacher, heart, perfect, long, special' — 'special' was intentionally excluded from new fringe per vocabulary rules (rejected generic abstraction), though it remains available as an extra. New icons needed: wilt, blossom, petals, baby, plus a custom Chrysanthemum mouse hero image. 'Perfect' and 'long' from existing extras could be used as bonus/backup descriptors tied to 'a perfect name' and the '13-letter, half the alphabet' name joke, but were not required to hit the 11-word cap.
