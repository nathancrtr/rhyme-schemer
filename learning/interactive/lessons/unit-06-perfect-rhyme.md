# Unit 6: Perfect Rhyme First

**Objective:** you can score equal-length rhyme tails with a weighted
nucleus/coda blend calibrated so identical tails score exactly 1.0 — and you
know why building the easy case first is a strategy, not a stall.
**Prerequisites:** Unit 5. **Pairs with:** `rhyme_schemer/rhyme.py`
(`rhyme_score`'s equal-length core, `_coda_similarity`,
`_syllable_similarity`).

## Model the easy case before the hard one

The full problem — graded, multisyllabic, unequal-length slant rhyme — has
too many moving parts to debug at once. So this unit deliberately shrinks
it: **equal-length tails only**, scored position by position. Every later
generalization (graded weighting in Unit 7, alignment in Unit 8) must
*reduce to* today's behavior on today's inputs — Unit 8's tests literally
assert that parity. Build the floor, then build on it.

## The shape of the score

Two tails of the same length pair up syllable by syllable. Per pair:

- **Nucleus similarity** — `vowel_similarity` on the two vowels.
- **Coda similarity** — compare the consonant tuples. The repo's
  `_coda_similarity` is deliberately crude: position-by-position over the
  *longer* coda, a consonant with no counterpart contributes 0, two empty
  codas agree perfectly. (Real consonant alignment would be Unit 8
  machinery; crude is *enough* while tails are equal length, and the
  crudeness correctly prices a missing or extra coda consonant.)
- **Onset — not consulted.** Cat/hat is the definition of rhyme, not an
  edge case.

Blend nucleus and coda with weights (nucleus dominant), then average the
per-position blends across the tail.

> PAUSE. Whatever weights you pick, identical tails must score exactly
> 1.0 — perfect rhyme is the top of the scale. What single arithmetic
> choice guarantees that for *any* weights?

Divide by the total weight: `(w_n·nucleus + w_c·coda) / (w_n + w_c)`. Both
similarities are 1.0 for identical material, so the blend is 1.0 no matter
how the weights are set. That normalization is load-bearing — it means
Unit 7 can tune weights freely without ever breaking the top of the scale.

## House test style, from day one

Encode the properties, not the magnitudes: the score is **symmetric**;
it lives in **[0, 1]**; identical tails hit exactly 1.0; perfect rhymes
(cat/hat, time/rhyme) beat clear non-rhymes by a wide margin. Ordering
assertions survive re-tuning; magic-number assertions die at the first
calibration pass. The repo's `tests/` model this style throughout.

## Check yourself

> Check yourself: (1) Why does cat/hat score exactly 1.0 despite different
> onsets? (2) What does `_coda_similarity` return for "day"~"wake" tails
> (`EY` vs `EY K` — one coda empty)? Why is that a *feature* here — and
> can you guess which tuning-ledger item it eventually becomes? (3) Which
> property test would catch an accidental `nucleus/coda` swap?

(That day/wake question is a genuine thread: the missing-coda zero puts
day~wake at 0.741, one hair under the eventual threshold — ledger item 4.
You just built the mechanism; Unit 14 decides whether it's calibrated
right.)

## Exercise

From the syllabus: failing tests for perfect rhymes and clear non-rhymes;
make them pass; assert symmetry and range. Then try to *break* your scorer
with a weird-but-legal input (empty coda, monosyllable, identical words)
before the tests do.

**Where this is heading:** Unit 7 exposes the weights and threshold and
loosens this scorer into a slant-rhyme detector; Unit 8 removes the
equal-length assumption. The 1.0 you calibrated today stays the top of the
scale forever.
