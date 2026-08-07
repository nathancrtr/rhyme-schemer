# Unit 8 Exercise — Alignment for Unequal Tails

**What you're building:** the generalization of `rhyme_score` to tails of
different lengths — the thing that makes *multisyllabic* slant rhyme scorable.
You'll fill in the two holes in `alignment.py`: the Needleman–Wunsch recurrence
+ backtrace, and the gap-aware scorer.

**Why it matters now:** Unit 6's scorer walks two equal tails position by
position. Give it a 3-syllable tail against a 2-syllable one and there's no
"position by position" to walk — you first have to decide *which syllables
correspond*, and whether one of them corresponds to nothing at all (a **gap**).
That decision problem is sequence alignment, the same algorithm behind `diff`,
spell-check, and DNA comparison. (The `sequence-alignment-family` lesson tells
that story; the `nw-alignment.html` widget lets you feel the DP table.)

## Work one example by hand first

Align tail_a = `[EH, IY]` against tail_b = `[EH, AH, IY]` with gap penalty 0.6.
Useful distances: `EH~EH = 0`, `IY~IY = 0`, `EH~AH ≈ 0.18`, `AH~IY ≈ 0.32`,
`EH~IY ≈ 0.23`.

Build the table — rows are prefixes of tail_a, columns prefixes of tail_b,
cell (i, j) is the cheapest alignment of the first i vs the first j:

|       | ∅    | EH   | EH,AH | EH,AH,IY |
|-------|------|------|-------|----------|
| ∅     | 0    | 0.6  | 1.2   | 1.8      |
| EH    | 0.6  | **0**| 0.6   | 1.2      |
| EH,IY | 1.2  | 0.6  | **0.32** | **0.60** |

Fill each cell as `min(diagonal + vowel_distance, above + 0.6, left + 0.6)`.
Check your bottom-right corner: the cheapest full alignment costs 0.60. Now
trace it backwards — which moves produced it? You should recover:

```
EH ~ EH      (substitute, cost 0)
gap ~ AH     (insert, cost 0.6)      ← the extra syllable, priced
IY ~ IY      (substitute, cost 0)
```

That's the whole algorithm. The code is the same table with the same three
moves, plus a `back[][]` matrix so the trace doesn't have to be re-derived.

## The spec

1. **`align_tails`** — fill the recurrence and the backtrace (the table
   allocation and edge initialization are provided). On ties prefer the
   diagonal, then "up": this keeps equal-length tails on the no-gap diagonal,
   so Unit 6's scoring falls out as the special case.
2. **`score_alignment`** — average the per-column scores: matched columns get
   `_syllable_similarity` (provided), gap columns get **0.0**.

## Run the tests

```bash
cd learning/interactive/exercises/unit-08-alignment
python -m unittest test_alignment -v
```

The cases are chosen to localize failures: diagonal tests catch recurrence
tie-breaking, the forced-gap tests catch the backtrace, parity tests catch
scoring. Green bar = done.

## Afterward: two things worth doing

- **Diff against the real thing.** The repo's `rhyme_schemer/rhyme.py` contains
  the production `align_tails`. Compare choices — did you tie-break the same
  way? Handle the backtrace the same way? (Don't peek until you're green;
  the struggle is the unit.)
- **Meet your algorithm's pedigree.** What you just wrote is, almost exactly,
  ALINE (Kondrak 2000) — see lesson §3b for the three design ideas ALINE has
  that this version doesn't, one of which is now tuning-ledger item 10.

## When you're stuck

The classic failure modes, in order of likelihood: comparing `tail_a[i]`
instead of `tail_a[i-1]` (the table has a phantom row 0); forgetting to
reverse the backtraced columns; scoring gaps as if they were matches (your
hypnotize~eyes number will be too high). The hand-worked table above is small
enough to step through in a debugger against your own code.
