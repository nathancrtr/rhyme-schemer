# Unit 8 Lesson Guide: Alignment for Unequal Tails

**Objective:** The learner can implement Needleman–Wunsch over vowel skeletons with a feature-distance substitution cost, and sees it as the same dynamic-programming alignment behind spell-check and DNA — generalized to vowels.
**Prerequisites:** Units 5–7; willingness to read the Minimum Edit Distance section of SLP3 Ch. 2.
**Pairs with:** `rhyme_schemer/rhyme.py`; `interactive/exercises/unit-08-alignment/`.

## How to run this lesson
Dialogue, one question per turn. This is the hardest unit — go slow, build the DP table by hand on a tiny example before any code.

## 1. Diagnostic opener
Ask: **"Your Unit 7 kernel averages similarity position-by-position. What does it do when one tail has three nuclei and the other has two — and why is that a problem for multisyllabic rhyme?"**
- Toward "position 3 has nothing to pair with / it crashes or mis-pairs" → step 2.
- Unsure → walk a concrete pair ("national" 3 syllables vs "rational" 3 — then deliberately pick a 3-vs-2 case) and let the mismatch surface.

## 2. Build the intuition
We need to decide *which* nuclei correspond — and allow gaps when one side has an extra syllable. That's an alignment problem.

> PAUSE. Ask: **"If you've ever looked at a `git diff` or a spell-checker's suggestion, you've seen this. What are the three moves that turn one sequence into another?"**

Wait. Elicit **match/substitute, insert, delete**. Then: aligning two vowel skeletons is exactly that, where the *cost* of a substitution isn't 0/1 but `vowel_distance` — a near-vowel substitution is cheap, a far one is expensive.

> PAUSE. Ask: **"So what should the cost of a gap (insert/delete) be, relative to a cheap vs. expensive substitution?"**

Lead them to: a gap must cost *more* than a good substitution (or everything aligns to gaps) but be reachable when there's genuinely an extra syllable. It's a tunable penalty.

## 3. Formalize
- **Needleman–Wunsch**: fill a DP table `D[i][j]` = best alignment cost of the first `i` of one skeleton and `j` of the other, from `min(` substitute, insert, delete `)`. Backtrace recovers the alignment.
- Substitution cost = `vowel_distance(a, b)`; gap = a constant penalty. The total cost → a similarity by inversion/normalization.
- The equal-length case from Unit 6 is the special path down the diagonal with no gaps — alignment *generalizes* it; verify your old scores still come out when lengths match.
- panphon's `Distance` class does exactly this (feature-weighted edit distance) — read its source to see the same idea in a mature library.
- **This has a name in the literature: ALINE** (Kondrak 2000, https://webdocs.cs.ualberta.ca/~kondrak/papers/chum.pdf) — DP alignment of phone sequences with feature-decomposed similarity, the standard phonetic-alignment algorithm for 25 years. Reimplementing it from first principles was the point of this unit; read it *after* your implementation works, both for credit and because its design answers questions we currently settle ad hoc — the next section maps them.

Connect back: **"This is the workhorse algorithm of sequence comparison — diff, spell-check, bioinformatics. You're applying it to phonology; the structure is identical — and in phonology specifically, it's been the standard tool since 2000."**

## 3b. What ALINE knows that we settle ad hoc

Each of ALINE's three design elements maps onto a question our kernel answers
*implicitly*. Reading the mapping is the fastest way to see your own design
decisions as decisions.

- **Per-feature salience weights.** ALINE scores phone similarity as a
  weighted sum over features, every weight named and hand-set (place 40,
  manner 50, voice 10...). We have salience weights too, but scattered:
  `DEFAULT_NUCLEUS_WEIGHT`/`DEFAULT_CODA_WEIGHT` are explicit, and so are
  `features.py`'s `_W_ROUND`/`_W_RHOTIC` — but the Euclidean metric on the
  vowel plane silently fixes the backness:height ratio at 1:1. That ratio is
  a third salience weight that currently doesn't exist as a parameter, so no
  sweep can sweep it.

> PAUSE. Ask: **"Find one more weight in the pipeline that exists only as a
> structural choice, not as a number."** (Candidates: gaps scoring exactly 0
> in `rhyme_score`; the seed gate's nucleus-only-ness in Unit 11.)

- **Separate vowel/consonant treatment.** ALINE *discourages* vowel–consonant
  alignment via its features; we make it impossible — NW sees only the vowel
  skeleton, and each coda is welded to its column. Mostly a feature (no
  pathological alignments can exist), but the weld means a consonant can
  never shift columns to find its counterpart: one representational
  commitment behind three ledger symptoms (item 4's missing-coda zero, item
  7's invisible medial consonants, item 10's flat-gap smoothing).

- **Expansions/compressions.** ALINE lets one phone align against *two*,
  priced by similarity — a diphthong can match a two-vowel sequence. Our only
  tool for a syllable-count mismatch is the flat gap penalty. The probe
  triangle **sky / fire / higher** (a rapper smoothing "-ire" toward one long
  vowel treats all three as classmates) exposes the cost: fire~higher scores
  1.000, sky~fire 0.741 (rescued by CMUdict's monosyllabic `F AY1 R`
  variant), sky~higher 0.500 ("higher" has no such variant, so the gap burns
  the column) — three numbers for one perceptual relation, steered by
  accidents of dictionary variant coverage. Ledger item 10 holds the ear
  data and the candidate fixes (variants first; a compression op as the
  metric-side alternative).

## 4. Common confusions
- **Gap penalty too low** → everything aligns to gaps, scores collapse. Too high → real extra syllables can't be skipped.
- **Forgetting the backtrace** → you get a score but can't show *which* syllables rhymed (needed for visualization, Unit 12). Build the backtrace now.
- **Distance vs. similarity bookkeeping** → keep one convention; alignment naturally minimizes a cost, so convert to similarity at the end.

## 5. Exit check
Ask: **"Hand-fill the 3×3 DP table for a tiny pair I give you, then read off the alignment. Where did a gap get chosen, and what did it cost you?"**
- Correct table + sensible gap → implement it; make the multisyllabic tests pass; confirm equal-length parity with Unit 6.
- Stuck → shrink to a 2×2 and rebuild the recurrence cell by cell.

**Where this is heading:** with alignment, any two spans can be scored. Phase 3 turns these pairwise scores into *groups* — the rhyme scheme itself.
