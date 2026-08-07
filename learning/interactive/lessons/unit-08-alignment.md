# Unit 8: Alignment for Unequal Tails

**Objective:** you can implement Needleman–Wunsch over vowel skeletons with a
feature-distance substitution cost, and you see it as the same
dynamic-programming alignment behind spell-check and DNA — generalized to
vowels. **Prerequisites:** Units 5–7; the Minimum Edit Distance section of
SLP3 Ch. 2 is the companion reading. **Pairs with:** `rhyme_schemer/rhyme.py`;
`interactive/exercises/unit-08-alignment/`.

This is the hardest unit in the course. Go slow, and build the DP table by
hand on a tiny example before touching code — the exercise's `task.md` walks
one. If a wall appears, it usually falls to a smaller table.

## The problem your Unit 7 kernel can't see

Your kernel so far averages similarity position by position — position 1
against position 1, position 2 against position 2. That silently assumes the
two tails have the *same number* of syllables.

> PAUSE. What should happen when one tail has three nuclei and the other has
> two? Walk it concretely before reading on: which positions pair up, and
> what happens to the leftover syllable?

There is no correct answer *within* position-by-position scoring — either the
code crashes, or it mis-pairs everything after the length mismatch. And
multisyllabic slant rhyme mismatches lengths all the time: a rapper rhymes a
three-syllable phrase against a two-syllable word and your scorer needs to
decide *which* syllables correspond and what the spare one costs. Deciding
correspondence under insertions and deletions is a named, solved problem:
**sequence alignment**.

## The intuition: three moves, priced

If you've ever read a `git diff` or taken a spell-checker's suggestion,
you've watched this algorithm work. Any transformation of one sequence into
another decomposes into three moves: **match/substitute** (pair two
elements), **insert**, and **delete** (leave an element unpaired — a *gap*).

Aligning two vowel skeletons is exactly that, with one upgrade: the cost of
a substitution isn't the 0-or-1 of spell-check but `vowel_distance` — pairing
EH with IH is cheap, pairing IY with AA is expensive. The whole feature-space
apparatus of Unit 2 becomes the alignment's cost model.

> PAUSE. What should a *gap* cost, relative to a cheap substitution and an
> expensive one? Reason it out from failure cases: what goes wrong if gaps
> are cheaper than every substitution? If they're dearer than all of them?

Bound it from both sides. If a gap is cheaper than a near-vowel
substitution, the aligner shreds real matches into gap pairs — everything
aligns against nothing. If it's dearer than even a far substitution, a
genuinely spare syllable gets force-matched onto whatever is adjacent rather
than skipped. So the gap penalty must sit *above* near-vowel substitutions
(~0.1–0.2) and *below* far ones (~0.6–0.7). The repo's calibrated value is
`DEFAULT_GAP_PENALTY = 0.6`; the `nw-alignment.html` widget lets you feel
what moves as you slide it.

## Formalizing: Needleman–Wunsch

- Fill a table `D[i][j]` = the best cost of aligning the first `i` nuclei of
  one skeleton with the first `j` of the other, taking the minimum of the
  three moves (substitute from the diagonal, gap from above, gap from the
  left). A second table records *which* move won, so the actual pairing can
  be recovered by walking backwards from the corner — the **backtrace**.
- Substitution cost = `vowel_distance(a, b)`; gap = the constant penalty.
  The finished cost converts to a similarity by inversion/normalization.
- The equal-length case from Unit 6 is the special path straight down the
  diagonal with no gaps — alignment *generalizes* your old scorer, and the
  parity test in the exercise proves your old scores still come out when
  lengths match.
- panphon's `Distance` class implements this same idea (feature-weighted
  edit distance) in a mature library — worth reading its source after yours
  works.
- **This has a name in the literature: ALINE** (Kondrak 2000, https://webdocs.cs.ualberta.ca/~kondrak/papers/chum.pdf) — DP alignment of phone sequences with feature-decomposed similarity, the standard phonetic-alignment algorithm for 25 years. Reimplementing it from first principles was the point of this unit; read it *after* your implementation works, both for credit and because its design answers questions we currently settle ad hoc — the next section maps them.

This is the workhorse algorithm of sequence comparison — diff, spell-check,
bioinformatics — applied to phonology, where it has been the standard tool
since 2000. The structure is identical; only the cost model knows about
vowels.

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

> PAUSE. Find one more weight in the pipeline that exists only as a
> structural choice, not as a number. (Candidates: gaps scoring exactly 0
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

## Common confusions

- **Gap penalty too low** → everything aligns to gaps, scores collapse. Too
  high → real extra syllables can't be skipped.
- **Skipping the backtrace** → you get a score but can't show *which*
  syllables rhymed — and the pairing is needed for coda scoring and for
  Unit 12's visualization. Build the backtrace now, not later.
- **Distance vs. similarity bookkeeping** → pick one convention and hold it;
  alignment naturally minimizes a cost, so convert to similarity once, at
  the end.

## Exit check

> Check yourself: hand-fill the DP table for a small pair (the exercise's
> 2×3 example is ideal), then read the alignment off your own backtrace.
> Where did a gap get chosen, and what did it cost? If you can't fill the
> table without peeking, shrink to 2×2 and rebuild the recurrence cell by
> cell — then implement it and make the exercise's tests pass, including
> the equal-length parity cases.

**Where this is heading:** with alignment, any two spans can be scored.
Phase 3 turns these pairwise scores into *groups* — the rhyme scheme itself.
