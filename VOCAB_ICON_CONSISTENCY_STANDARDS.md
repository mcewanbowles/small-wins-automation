# Vocab & Icon Consistency Standards
**Small Wins Studio — locked reference. Load with `@VOCAB_ICON_CONSISTENCY_STANDARDS.md`**

## Why this file exists

Our students use AAC to communicate — for many, it is their only expressive
language route. We are not teaching them to *decode* symbols the way a
reader decodes text; we are teaching a word-to-symbol mapping through
repeated, modeled, consistent exposure, the same way any child learns that
a sound means a thing. The icon does not need to be self-evident. It needs
to be **stable**.

That means the risk we are guarding against is not "this icon looks
arbitrary" (many PCS symbols for abstract words legitimately are, and
that's fine). The risk is:

1. **A word silently gets a different icon** in a different pack or theme,
   breaking the association a student has already built.
2. **A generator bug assigns the wrong icon to a word entirely** —
   this is worse than a normal content bug, because a student may
   internalize an incorrect mapping before anyone catches it in a PDF.

## The one rule that matters

> **The same word must always point to the same PCS symbol, everywhere,
> forever — unless a human (Fi) has explicitly decided to change it, in
> which case every existing pack using the old symbol gets flagged for
> re-issue.**

Everything below exists to make that rule checkable by a generator, not
just something we hope stays true.

## Style variation is not the problem — flag meaning drift, not appearance

Just as a student must eventually recognize "A" in Helvetica, in cursive,
and in someone's handwriting, a PCS symbol can legitimately vary in ways
that don't change what it means:

**Acceptable variation (do NOT flag):**
- Different skin tone / ethnicity depicted in a person-based icon for the
  same word (e.g., "friend," "teacher," "happy")
- Different color, style, or angle of the same object (a red backpack vs.
  a blue backpack, both for "backpack")
- A newer/updated PCS render of the same underlying symbol concept, if
  Boardmaker has revised its own artwork
- Different accessories/context around the same core symbol, as long as
  the core symbol concept is unchanged

**Must be flagged for review (this is a real inconsistency):**
- The same word resolves to a **different symbol concept** entirely
  (e.g., "nervous" shows the shaking-hands-sweat icon in one pack and a
  frowning-face icon in another — different concept, not just different
  rendering)
- A word that should be core (used across many themes) only has an icon
  defined in some theme's local asset set and falls back to something
  else, or nothing, in another
- Any case where the same *symbol* is reused for two *different* words
  across packs (this teaches a false equivalence)

The test for "same concept": would a teacher who has never seen this pack
before immediately agree "yes, that's the icon for nervous" without being
told which pack it came from? If yes, it's a style variant. If they'd
pause and say "wait, is this a different word?" — flag it.

## Word tiers

**Tier 1 — Core vocabulary.** Words that will recur across many/most of
the 50 planned themes (yes, no, want, more, help, stop, go, like,
don't like, happy, sad, nervous, sit, finished, turn the page, read,
think, choose, same, different, I/me, you, see, what, where, why, uh oh,
I don't know). These are the words doing the real communication work, and
consistency here matters most because the repetition *is* the
instruction.

- Locked in a master registry (below) the first time each is used.
- Every future theme must pull the existing symbol for any Tier 1 word
  it needs — never regenerate or re-select it.
- Any theme that can't find an exact registry match for a Tier 1 word
  must flag it rather than silently substituting.

**Tier 2 — Story/fringe vocabulary.** Words specific to one book's content
(backpack, classroom, teacher, llama llama, pencil). These don't need
cross-theme consistency on their first appearance — but the moment the
same fringe word recurs in a second theme (e.g., another book also uses
"backpack" or "teacher"), it graduates to the registry check too, going
forward.

## The registry

A single running file — `/data/vocab_icon_registry.json` (or similar,
Windsurf's call on format) — mapping:

```
word (lowercase, singular) → { symbol_id, first_used_theme, tier }
```

- `symbol_id` should be Boardmaker's actual internal symbol identifier,
  not a filename or a visual hash — filenames get renamed, pixels get
  re-exported at different resolutions, but the symbol ID is the one
  thing that reliably tells you "is this the same underlying icon."
- If Boardmaker doesn't expose a stable ID in our pipeline, the fallback
  is a perceptual hash of the base artwork *before* any per-instance
  styling (color/ethnicity variant) is applied — flag this as a
  Windsurf implementation question rather than assuming it's solved.

## Required check before any pack ships

For every word in a new pack:
1. Look it up in the registry.
2. **Not found** → this is a new word. Add it (tier decided by the rule
   above) and proceed.
3. **Found, same symbol_id** → fine, proceed silently.
4. **Found, different symbol_id** → **stop and flag for Fi.** Do not
   auto-resolve either direction (don't silently keep the new one, don't
   silently revert to the old one). Show both icons side by side with
   the word and both source theme names, and let Fi decide:
   - Accept the variation (style difference, both stay) → note it in
     the registry as an approved alternate for that word, so future
     runs don't re-flag it
   - Standardize to the existing one → discard the new one, use the
     registry's icon
   - Deliberately update the registry going forward → flag every
     *previously shipped* pack using the old symbol for that word as
     needing a re-issue, since this is exactly the kind of change that
     shouldn't happen quietly

## What this doesn't cover

This file is about symbol consistency only. It does not replace:
- Normal icon-mismatch QA (a generator pulling a completely wrong image
  for a word due to a lookup bug) — that's a correctness bug, catch it
  the way we already do, by rendering and eyeballing actual output.
- Vocabulary *selection* (which words to include per theme) — that's a
  separate, content-driven decision per book and isn't constrained by
  this file.

---

## Addendum: target vocabulary count per book needs to be determined, not assumed

### Why this changed

The product set per theme has grown well beyond what a 12-word list can
serve. Different generators have different word-shape needs — Syllable
Cards wants multi-syllable variety, Print Detective's first-sound
matching needs words with genuinely distinct first sounds, Word Search
and Sorting want short concrete nouns, and so on. A 12-word list gets
stretched thin across ~20 generators, and when a generator can't find
enough qualifying words in the list, it has nowhere safe to fall back to.

This is not theoretical: it already happened. Print Detective's Level 3
Picture Cards page shipped with "pajamas, bed, mama, night, cry,
stairs" — vocabulary from *Llama Llama Red Pajama*, a different book in
the same series, not from Llama Llama Back to School at all. Only one of
the seven cards ("llama") actually matched the current book. This is
what a starved word list produces: a generator reaches for *something*
and gets a wrong-book word instead of flagging that it ran out.

**The right number is not yet known.** 25 has come up as an estimate,
but it isn't based on an actual count of what the generators need — it's
a guess that the true number is higher than 12. Before this becomes a
locked standard, Windsurf needs to determine the real requirement rather
than us assuming a round number and hoping it's enough (or over-shooting
and creating unnecessary review work across 50 themes).

### Audit result (replaces placeholder "25")

The audit is complete. Key findings:

- **Fixed generators cap at 12 book-specific icons** (AAC Board fringe, Book Participation).
- **Dynamic generators** (Word Wall, Snap, Find & Cover) consume **all available** book icons — no hard cap.
- **Most generators share the same pool** — they don't need unique words.
- **Print Detective is the hardest constraint**: it needs 7 words with distinct first sounds. If a book's word list doesn't have 7 distinct first letters, that's where more words are needed.
- The 24 AAC core symbols are global (not book-specific) and come from `core_profile.json`.

**Practical target: 12-15 words per book** (up from the original 12). The extra 3 provide:
- Buffer for Print Detective's 7-distinct-first-sound requirement
- Variety for Word Search (which needs short, alpha-only words ≤8 chars)
- Coverage for Syllable Cards (which benefits from multi-syllable words)

The original "25" estimate was based on the assumption that generators need unique words. The audit shows they share heavily, so 12-15 is sufficient for most books. Thin books (Stellaluna) may need Tier 2b extended vocabulary to reach this count.

The mechanism (Tier 1/2/2b, registry checks, validation against the current book's list) is unchanged. Only the target count is now grounded in actual generator requirements rather than a guess.

### How the extra words (once the real count is known) get chosen

The Tier 1 (core, cross-theme) / Tier 2 (fringe, book-specific) split
from the main body of this doc is unchanged. The expansion happens
almost entirely in Tier 2:

- Every additional word must come from **this book's own text or
  illustrations** — something a child would actually see or hear reading
  this specific book. Never pull a word from another book in the same
  series, the same author, or a similar theme, even if it seems like it
  would obviously fit.
- Prioritize words that give generators the *shape* of variety they
  individually need:
  - Multi-syllable words (2–3 syllables) for Syllable Cards
  - Words with clearly distinct first sounds/letters for Print Detective
  - Short, concrete, easily-illustrated nouns for Word Search, Matching,
    Bingo
  - Words that sort cleanly into categories (who/what/where, feeling/
    object, etc.) for Sorting Cards
- Tier 1 core words that genuinely appear in this book (e.g. "happy,"
  "sit," "nervous" for LLB01) count toward the 25 — they don't get
  invented separately, they're just confirmed as present and pulled from
  the registry per the normal Tier 1 rule.

### Hard rule: no generator invents or substitutes outside the locked list

Every generator must treat the book's approved word list (once locked at
~25) as a closed set. Before a generator uses a word, it must confirm
that word is actually in the current book's list.

If a generator needs more qualifying words than the list provides —
e.g., Print Detective wants 7 first-sound-distinct nouns and only 5 in
the list qualify — it must **flag the shortfall for human review**, not
silently reach for a cached word, a generic library default, or (as
happened) a different book's list. A visible gap is recoverable; a
silently wrong word that ships is not.

### This doesn't change the vocab-before-icons sequencing

The existing principle stands: the full word list must be finalized —
now at ~25 words instead of 12 — in one pass, before the Icons tab is
usable. The single AI vocab-generation call should be prompted to
produce 25 words covering the shapes above, not 12, so the icon-matching
pass Fi does by hand only ever has to happen once per book.

### The registry check still applies at the new count

Nothing about the icon-consistency registry mechanism in the main body
of this doc changes. Every word in the now-larger list still gets
checked against the master registry before a pack ships — Tier 1 words
must match the existing registry entry exactly, Tier 2 words get added
fresh on first use and checked on any recurrence. Expanding to 25 just
means more words go through the same check per book, not a different
kind of check.

### Note for Fi

Reviewing icon matches in the Icon Labeler roughly doubles in volume per
book at 25 words vs. 12, across 50 planned themes. Worth asking Windsurf
whether the Icon Labeler UI can support batch-confirm (accept all
high-confidence matches at once, review only the uncertain ones
individually) so this doesn't become a bigger manual bottleneck than the
icon-sourcing backlog already is.

### When a book doesn't have 25 words of literal on-page content

Some books are short, simple, or narrow in scope (Stellaluna is mostly
about one bat, one cave, one night flight) and won't yield 25 genuinely
depicted words no matter how carefully you look. Forcing 25 literal
words out of a thin book risks the opposite failure: padding the list
with tenuous or repetitive entries just to hit the number.

For this case, add a third category, used only as a last resort:

**Tier 2b — Thematically related (extended) vocabulary.** A word that
does not appear in this book's text or illustrations, but is an obvious,
defensible extension of something that does — the kind of connection a
teacher would immediately understand without explanation. For
Stellaluna: the book centers on a fruit bat, so "berries" or "fruit"
extend naturally from that even if the word "berries" is never printed.
"Spaceship" would not — there's no reasonable line from anything in the
book to that word.

Rules for using Tier 2b:

- **Exhaust Tier 1 (core words genuinely present) and literal Tier 2
  (on-page words) first.** Tier 2b only fills the remaining gap to reach
  25 — it is not a shortcut to get there faster.
- **Every Tier 2b word must be explicitly tagged as extended, not
  on-page**, in the book's vocab file (e.g. a `"source": "extended"` flag
  per word, alongside `"source": "on_page"` for the rest). This must be
  visible to whoever reviews the list — a teacher or Fi looking at the
  final word list should be able to tell at a glance which words came
  from the book itself and which were added to round out the set.
- **The test is the same "would a teacher immediately see why this is
  here" bar used elsewhere in this doc.** If justifying the word
  requires more than one short sentence of explanation, it's too much
  of a stretch — pick something more obviously connected, or accept a
  shorter list for that book instead.
- **Cap Tier 2b at a minority of the list** — as a working limit, no more
  than roughly a quarter of the total (so no more than ~6 of 25) should
  ever be extended/thematic rather than literal. If a book needs more
  than that to reach 25, the right answer is a shorter list for that
  book, not a longer stretch into loosely-related territory.
- Tier 2b words still go through the same registry consistency check as
  everything else — if "berries" gets used as extended vocabulary in one
  bat-themed book, it should point to the same icon if another
  bat-themed book later uses it too.
