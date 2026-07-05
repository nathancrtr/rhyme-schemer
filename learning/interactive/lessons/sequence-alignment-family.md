# The Sequence-Alignment Family: Alignment, Seed-and-Extend, and Chaining

*A companion essay for rhyme-schemer. Prerequisite: you've implemented (or
read) `align_tails` in `rhyme.py` and `scan.py`. No biology assumed or
required — these are general-purpose algorithms over sequences of symbols; the
symbols are vowels for us, and we lean on the same three ideas that turn up
whenever anyone compares long strings.*

---

## 0. Why these algorithms keep showing up in one project

Three times now, a problem in this repo has had a matching solution in the
theory of comparing sequences:

| rhyme-schemer problem | the algorithm | the "canonical" home |
|---|---|---|
| Score two whole rhyme tails of unequal length (Unit 8) | **global alignment** (Needleman–Wunsch) | comparing two whole strings |
| *Find* rhymes anywhere in a verse without checking all O(n²) spans (Unit 11) | **seed-and-extend** (the BLAST heuristic) | fast approximate search |
| Fuse per-beat matches into the multisyllabic unit the ear hears (Unit 12) | **co-linear chaining** | stitching local hits into one |

That isn't a coincidence, and it isn't because rhyme is secretly biological.
It's because **all three problems are the same shape**: you have two (or many)
sequences of symbols drawn from a small alphabet, symbols can match
*imperfectly* (a slant vowel; a mutated DNA base; a typo), and you want to
line them up in a way that maximizes total similarity while respecting
*order*. Any field with that shape — computational biology, plagiarism
detection, `diff`, spell-check, music similarity, speech recognition —
reinvents or imports the same toolkit. Biology got there early and with the
most funding, so the vocabulary ("gap penalty", "local alignment", "BLAST")
comes from there. The math is alphabet-agnostic.

The unifying idea underneath all three: **an alignment is a path, and the best
alignment is a shortest/cheapest path.** Once you see that, the three
algorithms are just three different graphs and three different path problems.

---

## 1. Global alignment (Needleman–Wunsch) — the one you already built

### The problem
You have two sequences and you want a single score for *"how similar are these,
end to end?"* — where they may differ in length, so you can't just compare
position 1 to position 1. For us: two rhyme tails, `[EY, AH]` (wake up) versus
`[EY, AH, P?]`… where a multisyllabic rhyme has more syllables on one side than
the other. Comparing "position by position" breaks the moment the lengths
differ or a syllable is inserted.

### The idea: alignment as a grid path
Lay sequence A down the left edge of a grid and sequence B across the top. Any
way of aligning them corresponds to a monotone path from the top-left corner
to the bottom-right, where at each step you either:

- move **diagonally** — pair `A[i]` with `B[j]` (a *substitution*, cheap if
  they're similar, dear if not),
- move **down** — consume `A[i]` against nothing (a *gap* in B),
- move **right** — consume `B[j]` against nothing (a *gap* in A).

```
        B:  E   Y   A   H
     ┌───┬───┬───┬───┬───┐
     │ 0 │→  │→  │→  │→  │
   E ├───┼───┼───┼───┼───┤
     │↓  │ ↘ │   │   │   │      ↘ diagonal = pair the two symbols
   Y ├───┼───┼───┼───┼───┤      ↓  down     = gap (skip a symbol of A)
     │↓  │   │ ↘ │   │   │      →  right    = gap (skip a symbol of B)
   A ├───┼───┼───┼───┼───┤
     │↓  │   │   │ ↘ │   │
   H ├───┼───┼───┼───┼───┤
     │↓  │   │   │   │ ↘ │  ← bottom-right corner = fully aligned
     └───┴───┴───┴───┴───┘
```

Every path is a valid alignment; the score of a path is the sum of its step
costs. So *"find the best alignment"* becomes *"find the cheapest corner-to-corner
path"* — and because the path only ever moves toward the bottom-right, the
cheapest way to reach any cell depends only on three neighbors already
computed. That's the **dynamic programming recurrence** you wrote:

```
D[i][j] = min(
    D[i-1][j-1] + substitution_cost(A[i], B[j]),   # diagonal: pair them
    D[i-1][j]   + gap_penalty,                       # down: skip A[i]
    D[i][j-1]   + gap_penalty,                        # right: skip B[j]
)
```

Fill the grid row by row (each cell O(1) given its neighbors), and the
bottom-right cell holds the best total cost. Then **backtrace** — walk from the
corner back to the origin, at each cell asking "which of the three neighbors
did I come from?" — to recover the actual pairing, not just its score. That
backtrace is why `align_tails` returns *columns* and not just a number: the
downstream coda scoring and (soon) the visualization need to know *which*
syllable paired with which.

### The name and the knobs
This is **Needleman–Wunsch** (1970), the first application of dynamic
programming to sequence comparison. Two knobs define its behavior, and both
live in `rhyme.py`:

- **substitution cost** — how much a mismatch hurts. For us this is
  `vowel_distance`: near-vowels cost little, far ones cost a lot. In the
  textbook version it's a fixed "match = 0, mismatch = 1"; our graded cost is
  what makes it a *slant*-rhyme scorer instead of an equality check.
- **gap penalty** (`DEFAULT_GAP_PENALTY`) — the price of an unpaired symbol.
  Set it too low and the algorithm skips freely, matching anything to anything;
  too high and it force-pairs symbols that shouldn't be. Our value sits
  *above* a near-vowel substitution but *below* a far one, exactly so genuine
  slant pairs are kept while spare syllables are dropped.

### Cost
`O(m·n)` time and space for sequences of length m and n. For rhyme tails
(2–6 syllables) that's nothing. For two whole genomes (billions of symbols)
it's `10¹⁸` — hopelessly slow, and **the reason the next algorithm exists.**

### The "global" in global alignment
Needleman–Wunsch pins *both* ends: the path must start at the top-left corner
and finish at the bottom-right, so every symbol of both sequences is accounted
for. That's the right model when you already know the two things are
counterparts and want to score them whole — which is exactly the rhyme-tail
situation (you've already decided these two tails are the rhyme; now grade
them). It's the *wrong* model when you want to find a good-matching *region*
buried inside two much longer sequences, where forcing the ends to align just
drags in noise. That distinction is the seam between Unit 8 and Unit 11.

---

## 2. Local alignment and seed-and-extend — the scanner's engine

### The problem shift
In Unit 11 the question changed from *"score these two tails"* to *"somewhere
in this verse, are there two stretches that rhyme?"* Now you don't know the
endpoints — that's the *output*, not the input. And you can't afford to run a
full alignment between every pair of candidate spans: that's the O(n²)-spans ×
O(n²)-pairs blowup we counted early in Unit 11.

### Local alignment (Smith–Waterman), briefly
There's a cousin of Needleman–Wunsch called **Smith–Waterman** (1981) that
finds the single best-matching *sub-region* of two sequences rather than
aligning them end to end. The trick is a one-line change to the recurrence:
add a fourth option, `0`, to the `min`/`max` —

```
D[i][j] = max(0, diagonal, up, left)   # a 0 lets the alignment "restart"
```

— so an alignment that's going badly resets to nothing instead of accumulating
penalty, and you read the answer off the *best cell anywhere in the grid*
rather than the corner. That finds the best local region between *two given*
sequences. But it's still `O(m·n)` per pair, so on its own it doesn't solve the
"search a whole verse / database" problem. For that you need to avoid looking at
most pairs at all.

### The BLAST heuristic: seed, then extend
**BLAST** (Basic Local Alignment Search Tool, 1990) is the most-cited method in
its field, and its idea is one every programmer can appreciate: *don't run the
expensive algorithm everywhere — run a cheap filter first, and only pay for the
expensive part where the filter says it might be worth it.* Three steps:

1. **Seed.** Find short, high-quality exact-or-near-exact matches ("seeds" or
   "words"). These are cheap to find (hash lookups) and most of the sequence
   produces none — so you've thrown away the vast boring majority for almost no
   cost. *A rhyme cannot exist without its anchor syllables matching, so only
   stressed-syllable pairs are worth seeding from.*
2. **Extend.** From each seed, grow outward in both directions, accumulating
   score, and **stop when the score starts dropping** — the extension is only
   worth continuing while it improves. This recovers a good local alignment
   around each promising seed without ever aligning the non-seeded regions.
3. **Threshold / rank.** Keep extended hits above a significance cut; rank the
   survivors.

The payoff is enormous: instead of aligning everything to everything, you do
cheap seeding first and expensive alignment only in the neighborhoods seeds
point at. You trade a *guarantee* (Smith–Waterman finds the provably best local
alignment) for *speed* (BLAST finds the good ones fast and rarely misses a real
one). That is the classic **heuristic bargain**: give up "provably optimal" for
"fast and almost always right," and know exactly which you're giving up.

### How this maps onto `scan.py`, precisely
Our scanner is BLAST's skeleton with rhyme-flavored steps:

- **Seed** = the seed gate (`_seed_ok`). A pair of candidates is only worth
  scoring if their *anchor syllables* rhyme on their own — the anchor is our
  seed, and "anchors must match" is our "seed must be a near-exact word." The
  phonological restriction that only stressed, full-vowel syllables can anchor
  is what makes seeds sparse (most positions never seed), which is the whole
  point of seeding.
- **Extend** = the rhyme kernel scoring the tail from the anchor outward, plus
  selection's rule that a trailing syllable only stays if it pulls the *average*
  up — that is literally "extend while the score improves, stop when it drops."
- **Threshold / rank** = `find_matches`' threshold and `select_matches`'
  score-first ranking.

So Unit 11 wasn't "inspired by" BLAST loosely; it's the same three-phase
structure, with each phase's generic requirement ("seeds must be
high-quality", "extend while improving") instantiated by a fact about rhyme.

### The knobs, and the bargain they encode
- **seed sensitivity** — shorter/looser seeds find more real matches but waste
  time on more false leads; longer/stricter seeds are faster but miss faint
  ones. Our `DEFAULT_SEED_THRESHOLD` is exactly this dial: lower it and more
  anchor pairs qualify as seeds.
- Every knob here trades **sensitivity** (don't miss real rhymes — recall)
  against **specificity** (don't chase fake ones — precision). You'll meet that
  tradeoff by its proper names in Unit 14, when you finally *measure* it
  instead of guessing.

---

## 3. Co-linear chaining — Unit 12's compound-builder

### The problem
Seed-and-extend gives you a *set* of local hits. But one real feature often
shows up as *several* nearby hits that ought to be read as a single longer
alignment — interrupted by a gap too big for extension to have crossed, yet
clearly part of one story. In our terms: "PALMS-are-SWEATY ~ ARMS-are-HEAVY" is
one 4-syllable rhyme the ear hears as a unit, but the scanner (correctly, per
its per-beat model) emits it as two separate matches, `palms are ~ arms are`
and `sweaty ~ heavy`. We need to recognize that these two hits *line up* and
fuse them.

### The idea: hits as points, a compound as a monotone path
Put every local hit on a 2-D plane: the x-axis is position in sequence A, the
y-axis is position in sequence B. A hit is a little segment (it occupies a
range on each axis). Two hits are **co-linear / chainable** if one lies *down
and to the right* of the other — i.e. it comes strictly later in *both*
sequences. Chain a set of hits that are pairwise compatible in that sense and
you've got one long alignment threading through them.

```
   position in B ↑
                 │
     "heavy"     │              ● (sweaty~heavy)      both coordinates
                 │             ╱                       increase → chainable
     "arms are"  │        ● (palms are~arms are)
                 │       ╱
                 └───────────────────────────→ position in A
                    both hits go down-and-right together = one compound

   A crossing pair (down-LEFT) would be a reversal, not a compound — reject it.
```

The rule "later in both sequences, same order" is exactly your **sandwich
observation** made precise. Your "SWEATY is the meat between PALMS and ARMS"
is what interleaving looks like from the middle; "both hits step down-and-right
together" is what it looks like from the extents. The extent view is the one
that generalizes cleanly to **three or more** beats (a chain, not just a pair)
and to hits that are far apart or on different lines (where nothing is
literally sandwiched but the compound is just as real).

### Why it's a classic (and where it lives in the wild)
After BLAST-style tools produce many local hits, a **chaining** step stitches
compatible ones into larger alignments — it's standard post-processing in
genome-scale aligners, and the general problem ("given weighted intervals/hits,
find the best-scoring chain of mutually compatible ones") is a well-studied
piece of computational geometry. The clean version sorts hits by one coordinate
and runs a dynamic program (or an interval structure) to find the maximum-weight
increasing chain — a close relative of **longest-increasing-subsequence**, which
you may have met in coding interviews. Same skeleton as the two algorithms
above: *the best chain is the best-scoring monotone path through a set of
points.* Alignment was a path through a grid; chaining is a path through a
scatter of hits.

### What we actually need (and don't)
Our version is deliberately tiny, because our hits are already few and clean:

- **Adjacency, not just order.** In genomics, chained hits can have large gaps
  between them (introns, etc.). For a rhyme *compound* the ear only fuses beats
  that are contiguous — `palms are` then *immediately* `sweaty` — so our
  chaining requires the extents to **abut** (share a boundary), a stricter
  condition than mere down-and-right. We tried and *rejected* tolerating a
  one-word gap: on the Lose Yourself verse it fused unrelated beats from
  different rhyme classes (`palms sweaty ~ calm ready`) five times for every
  real compound. A blind gap can't tell a throwaway (`so`) from a word already
  claimed by another beat (`palms [are] sweaty`, where `are` belongs to the
  `palms are ~ arms are` beat) — that distinction needs the gap's *content*,
  which a match-level post-pass can't see. And the one thing a gap would buy —
  fusing across *differing* fillers (`palms are so sweaty ~ arms are really
  heavy`) — isn't clearly a real perceived rhyme. Parallel fillers that are
  *identical* on both sides need no gap help anyway: span enumeration absorbs
  them into a beat (as an identity column) before chaining runs. So: strict
  abutment, full stop.
- **Same order, no crossing.** Enforced exactly as above: reject a pair whose
  sequences disagree on order (that's chiasmus, a different device).
- **No scoring contest.** Genome chainers maximize a weighted chain because
  hits compete and overlap messily. Ours simply grows maximal runs of
  abutting, same-order matches — closer to a union-find / transitive closure
  over a "these two abut" relation than to a weighted-path optimization. If
  real verses ever produce competing overlapping chains, the full
  maximum-weight-chain DP is the principled upgrade, and it's the same shape as
  everything else here.

So `chain_matches` will be a pure post-pass over `VerseScan.matches`: no
scanner or kernel changes, each beat keeps its own rhyme class (the compound
*spans* classes — that's the whole point), and the renderer gets a uniform
picture whether a given compound happened to survive selection whole or in
pieces.

---

## 4. The through-line

Read the three together and one picture keeps redrawing itself:

- **An alignment is a monotone path**, and the best one is a cheapest/best path
  found by dynamic programming.
  - *Global* (Needleman–Wunsch): path across a full grid, both ends pinned —
    score two known counterparts whole. **(Unit 8: `align_tails`.)**
  - *Local + seeded* (Smith–Waterman idea, BLAST heuristic): find good
    *regions* without pinning ends, and skip most of the work with a cheap seed
    filter first. **(Unit 11: the scanner.)**
  - *Chaining*: a path not through a grid but through a scatter of local hits,
    fusing compatible ones into one longer structure. **(Unit 12:
    `chain_matches`.)**
- Every one exposes the same **two-sided knob**: how freely to match (gap
  penalty / seed looseness / gap tolerance) trades finding-real-things
  (sensitivity, recall) against not-inventing-things (specificity, precision).
  Unit 14 is where you stop turning those knobs by feel and start measuring.
- And each step up the ladder *reuses* the one below: chaining chains the hits
  that seed-and-extend produced, and each hit was scored by an alignment. The
  scanner is alignment wrapped in a search; the compound-builder is a search
  wrapped around the scanner.

None of this is biology. It's what falls out whenever you compare sequences of
imperfectly-matching symbols and care about order — which is precisely the
structure of rhyme over a stream of vowels. The life sciences are simply where
these particular tools were sharpened first; we're borrowing the whetstone, not
the knife.

### If you want to go deeper (all alphabet-agnostic algorithm reading)
- Needleman–Wunsch and Smith–Waterman: any algorithms text's dynamic-programming
  chapter, or the "edit distance / sequence alignment" section (it's the same
  DP as Levenshtein distance, which powers spell-checkers and `diff`).
- The seed-and-extend / heuristic-search idea generalizes as "filter cheaply,
  verify expensively" — the same pattern behind database query planning and
  approximate nearest-neighbor search.
- Chaining ↔ longest-increasing-subsequence and maximum-weight interval
  scheduling: classic DP/greedy problems you may know from interview prep.
