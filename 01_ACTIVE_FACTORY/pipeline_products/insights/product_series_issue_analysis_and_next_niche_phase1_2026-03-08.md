# Product Series Issue Analysis + Next Niche (Phase 1) - 2026-03-08

## 1) Current product-series issues identified

### A. Strengths to retain
- Transition Folder pipeline is now robust and automation-friendly (single CSV -> PDF + quiz + IEP CSV + thumbnails).
- QA now checks layout/content/output plus age-appropriateness guardrails.
- Packs are stronger for teacher usability and teen dignity.

### B. Remaining issues / opportunities
1. **Digital deck export gap**
   - Blueprint calls for printable + Google Slides/PowerPoint mapping, but current transition generator only outputs PDF + CSV artifacts.
2. **Niche depth imbalance**
   - Strong hygiene + money packs, but less depth in self-advocacy and workplace communication routines.
3. **Conversion leverage**
   - Existing structure is excellent for TpT scaling; biggest growth lever is adding high-demand, repeatable vocational/self-advocacy packs with explicit data tracking language.
4. **Cross-pack data continuity**
   - IEP CSV is now available per pack, but a cross-pack progress dashboard template is still a future step.

## 2) TPT market signal synthesis (research)

Observed demand language/patterns from TPT search pages:
- "self advocacy iep goal"
- "job skills workplace special education"
- "vocational skills for autism"
- recurring listing terms: scenario worksheets, workplace communication, transition to work bundles, task cards, data tracking.

Representative pages reviewed:
- https://www.teacherspayteachers.com/browse?search=self+advocacy+iep+goal
- https://www.teacherspayteachers.com/browse?search=job+skills+workplace+special+education
- https://www.teacherspayteachers.com/browse?search=vocational+skills+for+autism

## 3) Mentor recommendation: next niche to win

## **Niche selected: Workplace Self-Advocacy Scripts (Transition SPED)**

### Why this is the best next move
1. **Demand-fit:** clear TPT signal around self-advocacy + job skills + transition.
2. **Differentiation-fit:** many listings are generic worksheets; your format is stronger because it is structured for independent work folders and consistent A/B/C scaffolding.
3. **Automation-fit:** script/scenario packs are highly CSV-friendly, quick to replicate into bundles (retail, cafe, office, custodial, etc.).
4. **IEP-fit:** direct link to communication/self-determination goals and measurable progress capture.

## 4) Phase 1 created now (done)

### New Phase 1 source content
- `production/generators/transition_folder/content_transition_workplace_self_advocacy.csv`
- Includes 12 tasks (A/B/C x 4) with teen-relevant school/community/workplace scenarios.

### Generated Phase 1 outputs
- PDF: `production/generators/transition_folder/output/transition_workplace_self_advocacy_folder.pdf`
- Quiz CSV: `production/generators/transition_folder/output/transition_workplace_self_advocacy_baamboozle.csv`
- IEP CSV: `production/generators/transition_folder/output/transition_workplace_self_advocacy_iep_data_template.csv`
- 4 thumbnails: `production/generators/transition_folder/output/thumbnails/transition_workplace_self_advocacy/`

### QA result
- `qa_transition_folder.py` run on Phase 1 outputs: **PASS** (warnings: none, errors: none)

## 5) Phase 2 (business execution plan)

1. Clone Phase 1 into 4 aligned subthemes:
   - workplace communication,
   - workplace problem-solving,
   - workplace safety reporting,
   - attendance/schedule reliability.
2. Create a 5-pack bundle with shared teacher implementation positioning.
3. Publish single packs first (price ladder), then bundle for AOV lift.
4. Use the existing 4-thumbnail flow per pack and standardized listing copy focused on independent-use + IEP progress monitoring.

## 6) Bottom-line business guidance

If your goal is faster traction with minimal production risk, this niche is the best near-term move: **high buyer intent + strong automation leverage + direct IEP language fit**.
