# Unit 11 Walkthrough: The Internal-Rhyme Scanner, Stage by Stage

**What this is:** a guided trace of one verse through the complete Unit 11
pipeline (`rhyme_schemer/scan.py`), written as the unit was built. Unlike the
other lesson guides, this one was produced *during* the collaborative
implementation, so it documents the design as actually decided — including the
discoveries that forced changes and the warts that remain.

**Pairs with:** `rhyme_schemer/scan.py`, `tests/test_scan.py`.

## The demo verse

```
Every day I wake up, take a cake and shake the state up
Feeling great, no debate, I'm the one who ate the cake up
```

To regenerate the full trace, run each stage and print as you go:

```python
from rhyme_schemer import (
    enumerate_candidates, find_matches, select_matches, scan_verse,
    tokenize_verse,
)
candidates = enumerate_candidates(VERSE)
matches = find_matches(candidates)
selected = select_matches(matches)
scan = scan_verse(VERSE)   # runs all of the above + grouping
```

## The one-paragraph story

Everything before Unit 11 answers *"do these two things rhyme?"*; nothing
answers *"which things should we even ask about?"* The scanner is candidate
generation plus the judgment layers that keep enumeration honest. Its core
maneuver: when the text underdetermines the reading, **enumerate the readings
and let the score decide** — applied here to *performed stress* (the anchor),
exactly as Unit 9 applied it to pronunciation variants. The rest of the unit
is precision engineering: gates, prices, and selection rules that keep
enumerate-everything from meaning report-everything.

---

## Stage 0 — the verse

Plain text in. No markup, no annotation. Every downstream position refers back
to this text, because Unit 12's renderer must highlight *the verse as typed*.

## Stage 1 — `tokenize_verse`: positioned words

```
line 0: ['Every', 'day', 'I', 'wake', 'up', 'take', 'a', 'cake', 'and', 'shake', 'the', 'state', 'up']
line 1: ['Feeling', 'great', 'no', 'debate', "I'm", 'the', 'one', 'who', 'ate', 'the', 'cake', 'up']
```

Deliberately boring, with two non-obvious decisions:

- **Blank lines are preserved as empty entries**, so indices into the result
  are *true line numbers* in the original text. A candidate at `L2` is on
  line 2 of what the user typed, always.
- **Words are runs of letters and apostrophes** (`I'm`, `feelin'`); case is
  kept for display (CMUdict lookup lowercases on its own). Punctuation and
  digits separate words and vanish.

## Stage 2 — `enumerate_candidates`: (span, anchor) pairs with priced readings

82 candidates for this verse. Anatomy of one sample (candidates starting at
"who", line 1 word 7):

```
who @L1:W7+0          ->  tail=HH UW1                          cost=0.0
who ate @L1:W7+0      ->  tail=HH UW1 . EY0 T                  cost=0.0
who ate the @L1:W7+0  ->  tail=HH UW1 . EY0 T . DH AH0  cost=0.0   (x2)
                          tail=HH UW1 . EY0 T . DH IY0  cost=0.0
```

Read off what the notation encodes:

- `@L1:W7+0` = line 1, starting at word 7, anchored at syllable 0 of the
  first word. **A candidate is a (word span, anchor) pair** — the anchor is
  part of its identity, because "spaghetti" anchored at -GHET- and at -TI are
  different rhyme structures.
- The tail is the **performed-stress claim made data**: "who" keeps a
  promoted primary; "ate" shows `EY0` — citation `EY1`, *demoted* by
  `coerce_performed_stress` so it cannot steal the tail back (`rhyme_tail`
  anchors on the *last* primary).
- **Variants multiply readings**: three readings of "who ate the" because
  "the" has three CMUdict variants. Two collapse to the same tail (`DH AH0`
  twice — citation `DH AH0` and `DH AH1` converge once demotion strips the
  digit). Harmless.
- **Every reading is priced.** All `cost=0.0` here: "who" carries citation
  stress and isn't a function word (interrogatives genuinely take beats).
  Compare `up` (`cost=0.15`: coercible particle) and `spaghetti@-TI`
  (`cost=0.15`: promoted citation-unstressed syllable).

Filters applied during enumeration, at two grains:

- **Schwa gate** (per reading): a reduced nucleus (unstressed AH) cannot
  phonologically bear stress, so it never anchors.
- **`NEVER_ANCHOR`** (per span): articles/conjunctions are proclitics and are
  barred outright — necessary because CMUdict lists *emphatic* variants
  ("the" → `DH IY0` "thee", "a" → letter-name `EY1`) that would otherwise let
  every article rhyme with "free" and "day". Coercible function words
  ("up", "I", "me") anchor for a price instead. That's the prosodic
  three-way split: content words free, clitic-ish function words priced,
  proclitics never.

## Stage 3 — `find_matches`: gated, priced, thresholded pairs

121 matches — **redundancy is the design**, not a failure. One perceptual
fact ("line 1's back half rhymes with line 0") appears as ~40 overlapping
descriptions, from `wake up ~ cake up (1.000, 2 syl)` up through the genuine
4-syllable cross-line compound:

```
shake the state up @L0:W9+0 ~ ate the cake up @L1:W8+0 (0.964, 4 syl)
```

`find_matches` applies only the *pair-level* judgments and defers
adjudication:

1. **Proximity window** (`max_line_gap=2`, the minimum that reaches ABAB;
   components chain further).
2. **Disjoint extents** — positional, not lexical: candidates sharing word
   *positions* are competing descriptions of one stretch of audio, never
   partners; sharing word *types* ("plane, man" / "sane, man") is fine.
3. **Seed gate**, per reading pair inside the max: the anchor pair must open
   the rhyme on its own. Two clauses: no rime riche (identical anchor
   syllable — "up"/"up" is repetition, not rhyme; identity is welcome only in
   the *extension*), and anchor **nuclei** within `seed_threshold`.
   Nucleus-only, by necessity: any blended bar strict enough to kill
   wake/give (0.808) also kills lincoln/reason (0.657) — it would punish the
   coda flexibility slant rhyme licenses. This is the mean-vs-gate lesson:
   `rhyme_score`'s average lets a perfect trailing column subsidize a failing
   anchor; the ear treats the anchor as a gate.
4. **Coercion cost** subtracted per side: an unlikely performed-stress claim
   buys its way in. see~me survives one discount (0.85); you~to pays two and
   dies (a provisional call — see ledger item 5). Demotions are deliberately
   *free* — pricing them killed "plane man / sane man" and get up / "setup"
   when tried.

## Stage 4 — `select_matches`: one description per rhyme event

121 → 44. Greedy best-first with **same-event suppression**: accept a match
unless an accepted one overlaps it on *both* sides. Overlap on one side only
means different events — that's how "wake" (partnering "take") and "wake up"
(partnering "state up") both survive: same text, two structures.

**Score comes first — a deliberate inversion of Hirjee & Brown's
longest-first ranking.** Their scores are per-syllable log-odds *sums*, where
longer matches accumulate evidence; ours are *averages*, which makes the
average itself the arbiter:

- an extension joins only if it pulls the average up (`wake up ~ state up`
  0.964 beats its core wake~state 0.928 because up/up earns its seat;
  `cake and ~ state up` 0.83 loses to cake~state 0.88 because and/up is dead
  weight);
- mega-spans gluing multiple rhyme events always average below their best
  internal hit, so chains **auto-split into beats**. The 4-syllable compound
  above dissolves into `shake the ~ ate the (0.964)` + `state up ~ cake up
  (0.964)` — one performed beat per match; compounds reassemble as adjacent
  same-class hits after grouping.

Tiebreaks: **informative length** descending (columns carrying real rhyme
information — a schwa~schwa column with no codas scores a vacuous 1.0, since
every schwa matches every schwa, and must not let "take a ~ shake the"
out-length its core; a schwa column *with* codas, like lincoln/reason's
-coln/-son, still counts), then total length ascending (tightest
description), then nearest. Longest/nearest survive only as tiebreakers.

Note the epistemic status of the tight-extent preference: it is a claim about
*segmental* evidence only. In delivery, flow can bind "take **a**" / "shake
**the**" into the performed rhyme unit — but no segment can show that, so the
tight extent is the honest default under the evidence we have (see ledger
item 6).

## Stage 5 — `scan_verse`: components over the match graph

```
class 0: 'Every'@L0:W0, 'day I'@L0:W1, 'take a'@L0:W5, 'shake the'@L0:W9, 'I'm the'@L1:W4, 'ate the'@L1:W8
class 1: 'wake'@L0:W3, 'take'@L0:W5, 'cake'@L0:W7, 'shake'@L0:W9, 'state'@L0:W11, 'great'@L1:W1, 'debate'@L1:W3, 'ate'@L1:W8, 'cake'@L1:W10
class 2: 'wake up'@L0:W3, 'state up'@L0:W11, 'cake up'@L1:W10
OOV: (none)
```

Two wiring decisions to understand:

- **The edges are the selected matches themselves** — *not* recomputed
  `best_is_rhyme` calls. The scanner's edge test is stricter than the bare
  kernel's (seed-gated, coercion-priced, event-deduplicated); rescoring pairs
  with the plain kernel would readmit everything those layers rejected. The
  original milestone said "feed the same `group_rhymes` unchanged"; the
  *letter* of that would undo the unit, so the *spirit* is honored instead:
  Unit 10's graph engine was extracted as `rhyme.connected_components(count,
  edges)`, `group_rhymes` now delegates to it (behavior identical — the Unit
  10 test file is the proof), and `scan_verse` feeds it the scanner's own
  edges. Judgment and machinery, separated. Components still impose
  transitivity on a non-transitive relation — Unit 10's modeling choice,
  inherited knowingly.
- **Only matched candidates become nodes.** A candidate was an enumerated
  *possibility*, not an observation — no singleton "rhyme classes" of things
  that never rhymed. But an unmatched *word CMUdict doesn't know* is real
  information: surfaced in `VerseScan.oov` so a renderer says "unknown word"
  rather than letting it read as "doesn't rhyme".

The result: **class 1** is the full EY chain across both lines; **class 2**
is the `-ake up` multisyllabic family, *textually overlapping* class 1 — the
overlapping-rhyme-structures observation from the start of the unit,
now the literal output of the program.

## The wart: class 0, the "mush twin"

Class 0 needs a hard look. Some membership is defensible assonance ("EV-ery
DAY" plausibly joins the flow's EY chain). But `take a` sits in class 0 while
`take` sits in class 1 — the same beat, split across classes. Mechanism:
`informative_length` withholds *length* credit from vacuous schwa columns,
but they still count in the *score average* — a~the contributes a free 1.0
column, so `take a ~ ate the` (0.964) outbids the honest `take ~ ate`
(0.928) for the event, and being a different node, the winner lands in a
separate component. The clean fix — excluding vacuous columns from the score
itself — would move scanner scoring further from bare `rhyme_score`; whether
that's worth it is a question for the closing exercise to answer on real
data.

## Open tuning ledger (for the closing exercise and Unit 14)

1. **Vacuous-column score inflation** → mush-twin classes (above).
2. **wake/give at 0.904** survives: our vowel space rates EY/IH at 0.95 (the
   diphthong's glide passes near [ɪ]). Tightening is endorsed — but measured
   against Unit 14's eval, with lincoln/reason protected by dialect
   *variants*, not metric generosity.
3. **EH/EY assonance chains** ("Every ~ shake the" 0.880) selected with mushy
   extents — possibly real percepts, sloppily delimited.
4. day~wake alone scores 0.741 (missing coda zeroes the coda term) — one hair
   under threshold; the coda-weight question.
5. **you~to dies, and shouldn't always** (flagged by the learner: these are
   clear, common rhymes in their everyday pronunciations). The coercion cost
   is a context-free prior, but beat placement is positional: English nuclear
   stress falls at the phrase's right edge, so a *line-final* "to"/"you"
   takes the beat for free — no coercion is actually being claimed there.
   Candidate fix: make the cost **position-sensitive** (waived/reduced for
   line-final candidates, full price mid-line). Requires candidates to know
   their line-final status — the one positional fact they don't yet carry.
   `test_cost_kills_function_word_junk_matches` pins the current behavior and
   must change with this.
6. **Tight vs padded extents are flow-dependent** (flagged by the learner):
   "take a ~ shake the" can genuinely be the delivered rhyme unit under the
   right cadence. Segments alone cannot see that — it needs a beat grid (the
   curriculum's prosody & flow frontier). Mitigations: grouping is unaffected
   (both extents put the same beat in the same class), and Unit 12 can render
   padded extents when adjacent syllables are class-mates. Becomes load-
   bearing only once a rhythm layer exists to adjudicate.

7. **Tail-internal onsets are invisible**: MOP syllabification hands medial
   consonants to the next syllable's onset, and the kernel ignores onsets in
   every column — so sweaty~heavy scores 1.0, indistinguishable from true
   perfect rhyme (identity from the stressed vowel onward). North-star
   consistent, but the top of the scale is overcrowded. Candidate fix: a
   small onset-similarity term for *non-initial* tail columns only (the
   first column's onset must stay ignored — that's what makes cat/hat
   rhyme).

8. **Chaining has no quality gate, so it amplifies threshold-huggers**
   (flagged by the learner, with ground truth attached). On Poe's *Raven*
   stanza 1, `chain_matches` fused there~one (0.826) and "came a"~gently
   (0.825) onto tapping~rapping (1.000) into a three-beat compound — a
   five-syllable rhyme whose only real beat is the third. The learner's
   ear is unequivocal: *there/one and "came a"/gently do not rhyme at all*,
   not even as slant — those scores are vowel-space generosity (EH~AH,
   EY~EH), items 2–3's diagnosis resurfacing one layer up. Structurally:
   `_abuts` is purely positional, and selection's
   extension-must-raise-the-average discipline has no chaining analogue,
   so any two abutting *selected* matches fuse, and a perfect beat lends
   its credibility to its passengers. Candidate knobs: (a) a per-beat
   score floor for joining a chain, above the bare match threshold;
   (b) an average-score condition on the fused chain, mirroring
   selection's; (c) fix the underlying vowel generosity (item 2) and
   remeasure — the passengers may simply die at selection. Decide against
   Unit 14's eval, not by intuition.

Items 5 and 6 share a diagnosis: **performance context (line position, beat
grid) carries information a segment-only scanner cannot see** — the
performed-stress problem, one level up.

## Closing exercise: Lose Yourself (first verse excerpt)

Run at defaults over the famous eight lines ("His palms are sweaty...`blaow`"):
208 candidates → 99 matches → 69 selected → 14 classes, OOV = chokin',
jokin', blaow (Unit 13's motivation, on cue).

**The hit list** (all found, unprompted): the complete -etty chain (sweaty /
heavy / sweater / already / spaghetti / ready / *forgetting*); nervous ~
surface; palms are ~ arms are (0.996); the AA family (palms / arms / mom's /
calm / bombs / drop); vomit ~ "calm and" ~ "bombs but" (a real flow rhyme,
easy to miss by eye); wrote down ~ whole crowd; the AW family (down / crowd /
loud / mouth / out / out); come out ~ run out; knees ~ He's; how ~ now.

**The teachable failures:**

1. **The non-transitivity trap fired live.** At threshold 0.75 the AA class
   swallowed the OW family (wrote / whole / goes / won't) through bridge
   edges like whole~calm (OW~AA nuclei rate ~0.85 in our space, plus L~LM
   coda support). Unit 10's warning, empirically confirmed at verse scale.
2. **The threshold cannot fix it.** The probe:
   - 0.75: AA+OW glued; function-word contamination (are, on, his, looks).
   - 0.80: contamination gone; AA+OW still glued; "down" falls out of the AW
     class (down~crowd is 0.79 — the N~D coda penalty).
   - 0.85: AA and OW cleanly separate — but sweater and forgetting fall out
     of the -etty chain (their edges are genuine ~0.8 slant) and more AW
     members drop.
   No single value yields the gold annotation: the AA/OW bridges score in the
   same band as edges the ear demands (sweater, forgetting, down). The fix
   must come from the **feature space** (AA~OW is too generous), not the
   dial — the empirical confirmation of ledger item 2, and the cleanest
   possible motivation for Unit 14's eval harness.
3. **Compounds decompose into per-beat classes.** "PALMS-are-SWEATY ~
   ARMS-are-HEAVY" is heard as one 4-syllable unit but reported as two
   matches in two classes ('palms are ~ arms are' + 'sweaty ~ heavy'),
   because the internal hit sweaty~heavy (1.0) outbids the 4-syllable span
   (0.998) and same-events it away. By design ("one beat per match;
   compounds are adjacent hits") — but Unit 12 must reassemble adjacent
   same-line runs across classes to render the compound the ear hears.
4. **Tail-internal onsets are invisible** (new ledger item 7): sweaty~heavy
   scores a *perfect* 1.0 because MOP syllabification puts the medial t/v in
   the following syllable's *onset*, and the kernel ignores onsets
   everywhere. Consistent with the vowels-first north star, and why the
   -etty chain coheres — but "perfect" overclaims: identity-from-the-vowel
   (true perfect rhyme) and any-medial-consonant now tie at 1.0.

**Error routing** (the exercise's real deliverable — every miss diagnosed to
a component): AA/OW merge → feature space (item 2); sweater/forgetting loss
at high threshold → keep threshold ≤0.8, fix feature space instead;
down/how/now coda issues → coda weighting (item 4); chokin'/jokin'/blaow →
G2P (Unit 13); compound rendering → Unit 12.

**Gold verdicts from the learner's ear** (the first entries of Unit 14's gold
annotation set):

- *"What he"* does **not** belong in the -etty chain (scanner includes it at
  default threshold via AH~EH nucleus generosity — a feature-space datum,
  *not* a word-class one: interrogatives can genuinely bear beats, so adding
  "what" to FUNCTION_WORDS would be the wrong fix).
- *how/now* **should** share a class with *loud/out/down*. Probe:
  `coda_weight=0.30` (from 0.35) achieves exactly this on this verse with
  zero other changes to the scheme — a validated candidate fix, deliberately
  **not** applied yet: 0.35 is Unit 7's calibrated value and one verse is one
  datapoint. Unit 14's harness decides.

## Design decisions index (as argued during the unit)

| Decision | Choice | Why |
|---|---|---|
| Candidate granularity | Word-level spans, not raw syllable stream | Mid-word-ending rhymes rare to the ear; clean text mapping; pivot only on real false negatives |
| Anchor problem | Enumerate (span, anchor) pairs; coerce stress as data | Citation stress provably underdetermines performance; kernel stays untouched |
| Stress-pattern space | Collapsed 2^n patterns to n anchor positions | Stress's only kernel role is picking the tail start |
| Seed gate | Nucleus-only, per reading pair, no rime riche | Blended gate kills lincoln/reason; identity opens nothing but may extend |
| Coercion cost | Promotions only (0.15); demotions free | Demotion pricing killed the mosaic and get-up/setup flagships |
| Articles | `NEVER_ANCHOR`, categorical | Emphatic CMUdict variants otherwise resurrect them; proclitics carry no beat |
| Selection ranking | Score-first; H&B longest/nearest demoted to tiebreaks | Averages self-arbitrate extension and auto-split chains; sums don't |
| Grouping edges | Selected matches, via extracted `connected_components` | Recomputing with bare `best_is_rhyme` would readmit gated rejections |
