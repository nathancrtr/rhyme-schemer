# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

rhyme-schemer takes hip-hop lyrics as plain text and surfaces their rhyme scheme,
in the spirit of the Vox/Pudding *"Hypnotize"* rhyme visualizations. The north
star is **slant rhyme and assonance, not just perfect rhyme**: hip-hop rhyme
matches *vowel sounds* and treats consonants as flexible texture, so "Lincoln" /
"reason" must count.

It is first and foremost a **learning project** — code is written to be read.
Optimize edits for clarity and pedagogy over cleverness. Module and function
docstrings carry real explanatory weight (the *why*, not just the *what*); keep
them current when you change behavior.

## Commands

```bash
source .venv/bin/activate                # dev environment lives in .venv/
pip install -r requirements.txt          # only runtime dep is `pronouncing` (CMUdict)
python -m unittest discover tests        # run all tests
python -m unittest tests.test_syllabify  # run one test module
python -m unittest tests.test_syllabify.TestSyllabify.test_lincoln  # one test
```

There is no linter, formatter, or build step configured.

## Architecture

The pipeline is **syllable-first**, and the layers are deliberately stratified by
how much they know about rhyme. When adding code, place it in the layer that
matches its knowledge level rather than reaching across:

1. **`phonetics.py`** — raw ARPAbet facts only; knows *nothing* about rhyme. The
   ARPAbet vowel inventory, stress encoding (`Stress` IntEnum from CMUdict's
   trailing digit), and English onset phonotactics (hand-listed legal onset
   clusters, intentionally non-exhaustive — extend as real lyrics expose gaps).
2. **`models.py`** — the data structures. `Syllable(onset, nucleus, coda, stress)`
   and `Pronunciation` (an ordered tuple of syllables). Both are frozen
   dataclasses. **Key design invariant:** a single word and a multi-word span are
   *both* just `Pronunciation`s, so nothing downstream cares which it started as.
   `Pronunciation.vowel_skeleton` (the nuclei in order) is the spine of rhyme.
3. **`syllabify.py`** — CMUdict lookup + the Maximal Onset Principle syllabifier
   (`syllabify`). Splits a flat phoneme list into syllables: one nucleus per
   vowel; intervocalic consonant runs are pushed into the *following* onset as
   far as `phonetics.is_legal_onset` allows, the rest is coda. Lookup comes in
   four flavors on two axes — single word vs. multi-word **span** (`_for_span`,
   which concatenates via `Pronunciation.concat`), and first-variant vs. **all
   CMUdict variants** (`pronunciations_*`, plural): `pronunciation_for`,
   `pronunciation_for_span`, `pronunciations_for`, `pronunciations_for_span`.
   OOV is "skip-and-flag": the singular forms return `None`, the plural forms
   return `[]` (and one OOV word empties a whole span). Span variants are the
   cartesian product of the words' variants.
4. **`features.py`** — articulatory feature spaces giving *graded* phoneme
   similarity (this is what enables slant rhyme). Vowels live on the IPA
   quadrilateral (backness × height) plus roundedness + a rhotic flag, with
   diphthongs modeled as a glide between two `VowelPoint`s. Consonants get a
   parallel place × manner plane (manner ordered by sonority) plus voicing.
   `vowel_distance` / `consonant_distance` return `[0,1]` (0 = identical);
   coordinates are hand-placed approximations, swappable for a library like
   panphon later.

5. **`rhyme.py`** — the rhyme kernel, built on the tail from the last stress:
   `rhyme_tail` slices it; `align_tails` runs Needleman–Wunsch over the two tails'
   vowel skeletons (substitution cost = `vowel_distance`, gap = `DEFAULT_GAP_PENALTY`,
   backtrace recovers the pairing) so unequal-length (multisyllabic) tails can be
   compared; `rhyme_score` averages a per-column blend of nucleus + coda similarity
   (gaps score 0); `is_rhyme` thresholds it. The vowel-vs-coda weighting lives
   *here* (`DEFAULT_NUCLEUS_WEIGHT`/`DEFAULT_CODA_WEIGHT`), **not** in `features.py`;
   perfect rhyme is the threshold-1.0 special case, and equal-length tails stay on
   the alignment's no-gap diagonal, reproducing simple position-by-position scoring.
   `best_rhyme_score`/`best_is_rhyme` are variant-aware wrappers: given two
   *lists* of pronunciations they take the `max` over all pairings (a rapper
   picks whichever reading rhymes) — a thin layer *around* the kernel, which
   itself still only ever sees one `Pronunciation` vs. one `Pronunciation`.
   `group_rhymes` (Unit 10) sits one level up again: given *many* items (each a
   variant list), it makes `best_is_rhyme` the edge test of a graph and returns
   its **connected components** (via a small private `_UnionFind`, exposed as
   `connected_components(count, edges)` for reuse) as rhyme classes — lists of
   item indices. Components impose transitivity on a slant-rhyme relation that
   lacks it (A–B and B–C rhyme, A–C need not); that is the deliberate modeling
   choice the unit is about, not an accident.

6. **`scan.py`** — the internal-rhyme scanner (Unit 11): `scan_verse(text)`
   turns a raw verse into a `VerseScan` (selected matches, rhyme classes, OOV
   words). Candidates are **(word span, anchor)** pairs; the anchor is a claim
   about *performed* stress, minted as data by `coerce_performed_stress`
   (promote the anchor, demote everything after it) — the scanner is a second
   `Pronunciation` factory, so the kernel needed no changes. Precision comes
   from layers, each with a documented rationale: a nucleus-only **seed gate**
   (anchor syllables must rhyme on their own, and identical anchors are
   rime riche, not rhyme), a **coercion cost** on unlikely stress promotions
   (function words pay; articles/conjunctions in `NEVER_ANCHOR` never anchor),
   and score-first **selection** (with averaged scores an extension must raise
   the average to earn its seat — this also auto-splits glued rhyme chains into
   one-beat matches; Hirjee & Brown's longest/nearest survive as tiebreakers).
   Grouping feeds the *selected matches themselves* as edges to
   `connected_components` — not recomputed `best_is_rhyme` calls, which would
   readmit the gated rejections. The full design dialogue, stage-by-stage
   walkthrough, and **open tuning ledger** live in
   `learning/interactive/lessons/unit-11-scanner-walkthrough.md`; consult the
   ledger before tuning any of this.

7. **`g2p.py`** — the Unit 13 grapheme-to-phoneme fallback chain:
   `pronounce(word) -> Guess`. Chain order is dictionary → slang lexicon →
   normalization rules (g-drop / stem+-in' / -a-for-er) → letter-to-sound;
   the lexicon outranks rules because it is curated truth ("shoulda"
   pattern-matches -a-for-er via "shoulder" but contracts "should have").
   Design principle: **dialect spellings are performance transcriptions** —
   rules recover the dictionary stem then keep the *spelled* surface
   phonology (N-for-NG, non-rhotic final AH), the Unit 11 move one layer
   down. Confidence is priced, not modeled: `Guess.cost` (0 except
   letter-to-sound's `DEFAULT_LTS_COST`) folds into `Reading.cost` in
   `scan.py`, so kernel and `models.py` stay provenance-free. `VerseScan`
   gains `guessed` ((word, source) pairs); `oov` now means "even guessing
   failed" (no vowel: "brrr"). Renderers mark guesses — dashed underline,
   provenance tooltip line, legend note — distinct from OOV's dotted.

8. **`render.py`** — the Unit 12 renderer: `plan_verse` resolves a verse +
   `VerseScan` into a medium-agnostic `RenderPlan` (every policy decision as
   data), and `render_html` / `render_terminal` are deliberately dumb emitters
   over it. Color = **rhyme class** (Pudding/Vox school, chosen over Brath's
   color-by-vowel and Hirjee & Brown's five stacked channels — render the
   scanner's judgments, not the input phonetics). Multi-class words (common:
   up to 5 classes/word in real data, extents both nest *and* cross) get
   fill-by-best-score + tick bars + tooltip receipts; multi-beat `Compound`s
   (via `chain_matches`) get a neutral spanning rule; OOV words a dotted
   underline. Palette: 8 fixed-order categorical slots as text-safe tints
   (CVD-validated per mode), largest classes first, overflow folds to a
   neutral wash — never cycle hues.

9. **`evaluate.py`** — the Unit 14 harness. `parse_gold` reads a
   hand-editable annotation format (`tests/gold/`), and `score_pairs` /
   `evaluate_verse` count precision, recall and F1 over **word pairs**:
   gold groups and scanner output are both exploded into the pairs they
   imply. Two levels are scored against the same gold (`edge_pairs`, the
   selected matches; `class_pairs`, everything a component implies) under
   two extent rulers (`anchor`, `exact`). Precision counts predicted pairs
   and recall counts gold pairs, which are different denominators on
   purpose (`Evaluation.gold_matched`). Not re-exported from `__init__.py`.

**`tools/`** holds corpus scripts that are not part of the package: the
MCFlow converter (`mcflow_to_gold.py`), the corpus driver
(`run_corpus_eval.py`), two audits, and `mcflow_performed_eval.py`, which
reruns the kernel on MCFlow's performed pronunciations by building
`Candidate`s itself and handing them to the unchanged `find_matches` /
`select_matches`. They need a local MCFlow clone kept **outside** the
repository; never commit corpus lyric text, gold files derived from it, or
a report that quotes it.

**Test fixtures must be content-safe**: never embed multi-line commercial
lyrics (content-filter + copyright); use the original engineered verse and
public-domain poetry (Poe, Gilbert & Sullivan) in `tests/test_render.py`.
Single iconic mild lines ("His palms are sweaty…") are fine.

**Where the project stands** (see `README.md`, Status): the scanner has been
measured against MCFlow, and the numbers are in the walkthrough section "The
first measurement", in front of the tuning ledger. At default settings its
edges score precision 0.136 and recall 0.374. The measurement puts the
largest errors outside the knobs the ledger was saving for one tuning sweep
(the scanner has no chance model and no term for line position), so whether
to run that sweep or rebuild the scoring model is **undecided**. Ask before
starting either. The standing rule is unchanged: no default is tuned
piecemeal; new observations go in the ledger. MCFlow is the only usable
gold found so far (Haider & Kuhn's hip-hop set is German and end-rhyme
only; Hirjee & Brown's is five songs), and the class-level clustering
scores (B-cubed, adjusted Rand) are not implemented.

**Prior art and `REVIEW.md`.** `REVIEW.md` is an external review from July
2026, preserved as written and never corrected. Do not treat it as an
authority. The README's "Where this sits in the field" section lists the
claims in it that are known to be wrong. Check any prior-art claim against
the paper itself before repeating it.

The public API is re-exported from `rhyme_schemer/__init__.py`; update `__all__`
when you add user-facing surface.

## Conventions

- Phoneme convention: ARPAbet tokens are uppercase; **vowels carry a trailing
  stress digit** (`IH1`), consonants never do. Use `strip_stress` /`is_vowel`
  from `phonetics.py` rather than parsing digits inline.
- Tests are named `test_*.py` and use `unittest`. Syllabifier tests assert against
  the human-readable `str(Syllable)` form (CMUdict-per-syllable) drawn from the
  running "Hypnotize" examples.
- `from __future__ import annotations` is used throughout; prefer the lowercase
  builtin generics (`tuple[str, ...]`) in annotations.

## The `learning/` directory

`learning/` is a self-contained, project-driven course (curriculum, lesson
guides, browser widgets, quizzes, and exercise stubs) for learning NLP and
computational phonology *by finishing this repo*. It was added via `git subtree`.
The course is **delivered as a static browser site**: `learning/site/` is
generated from the Markdown sources by `learning/build_site.py` (dev-only dep:
`pip install markdown`). Markdown is the source of truth — after editing any
lesson or `curriculum.md`, rerun the build script and commit the regenerated
site alongside the source change.
It is documentation/teaching material, not part of the package — don't import from
it or wire it into the build. The browser widgets render the repo's own numbers
(e.g. `vowel-explorer.html` calls the same `vowel_distance` math), so if you change
the feature spaces, those widgets may need matching updates.

**Design.** The stylesheet is generated too: `learning/style_source.py` is the
design system (and documents its own reasoning) and emits `site/style.css`.
Its palette is transcribed from `rhyme_schemer/render.py` — the warm paper
ground and the eight categorical hue slots, in the renderer's fixed order —
so **if you retune that palette, retune `style_source.py` to match**. The
eleven hand-authored pages under `interactive/` link the same stylesheet and
express their own colors as `--hue-N` / `--fill-N`, following render.py's
split: full-strength hue for thin marks, washed fill wherever text sits on
the color. Typefaces are SIL-OFL, committed subset under `site/fonts/`, and
rebuilt only by `learning/build_fonts.py` when coverage changes. Note that
`--mono` is the monospace *family* token; widgets must not reuse that name.
