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
   its **connected components** (via a small private `_UnionFind`) as rhyme
   classes — lists of item indices. Components impose transitivity on a slant-
   rhyme relation that lacks it (A–B and B–C rhyme, A–C need not); that is the
   deliberate modeling choice the unit is about, not an accident.

**Next milestone** (see top-level `README.md`): grouping into a scheme is now in
place (Unit 10). Next is **internal & multisyllabic rhyme** (Unit 11) — a scanner
that slides over the whole syllable stream (not just line ends) to surface
rhymes within and across lines, feeding the *same* `group_rhymes` unchanged.

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

`learning/` is a self-contained, project-driven course (curriculum, Socratic
lesson guides, browser widgets, quizzes, and exercise stubs) for learning NLP and
computational phonology *by finishing this repo*. It was added via `git subtree`.
It is documentation/teaching material, not part of the package — don't import from
it or wire it into the build. The browser widgets render the repo's own numbers
(e.g. `vowel-explorer.html` calls the same `vowel_distance` math), so if you change
the feature spaces, those widgets may need matching updates.
