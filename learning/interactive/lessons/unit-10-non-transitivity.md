# Unit 10: Grouping & the Non-Transitivity Trap

**Objective:** you can turn pairwise rhyme scores into groups via a
similarity graph and connected components, and — more importantly — you can
articulate why slant-rhyme similarity is *not* an equivalence relation,
which makes grouping a real modeling decision rather than a mechanical step.
**Prerequisites:** a working `rhyme_score` (Units 6–8). **Pairs with:**
`rhyme_schemer/rhyme.py` (`group_rhymes`, `connected_components`).

## From pairs to groups

You can score any pair. A verse needs *groups* — the rhyme classes that
become colors in Unit 12.

> PAUSE. Given all pairwise scores, what's the simplest thing you could do
> to get groups? Sketch it before reading on.

The simplest thing: draw an edge whenever two words score above a
threshold, then call each connected clump a group. That is exactly what
`group_rhymes` does — nodes, threshold edges, **connected components** (via
a small union-find, exposed as `connected_components(count, edges)` for
reuse). A few lines of code. The unit is about what those lines *commit
you to*.

## The trap

> PAUSE. Suppose A rhymes with B (above threshold) and B rhymes with C —
> but A and C score *below* threshold. Should A and C be in the same
> group? Sit with it; there is no clean answer.

That discomfort is the payload of the unit. With connected components, A
and C end up grouped *through* B even though they don't rhyme. Slant-rhyme
similarity is reflexive and symmetric but **not transitive** — it is not an
equivalence relation — yet "connected components" imposes transitivity by
fiat. Real triples are easy to build: tight vowel chains like
city/gritty/pity hold up, but loosen the threshold and you can chain
feel → fill → fell, where the ends barely rhyme at all.

## The trap has a name, and a literature

- Components over threshold edges is **single-link clustering**, and its
  failure mode — one generous edge gluing two good clusters into a
  mega-class — is **chaining** (percolation), the oldest known clustering
  pathology. This is not a hypothetical: it fires, on schedule, in Unit
  11's tuning ledger (items 1 and 9 — the "mush twin" and the OW
  mega-class), and the ledger's naming note credits this exact analysis.
- Alternatives that refuse forced transitivity: require *all* pairs above
  threshold (cliques — strict, brittle); **correlation clustering** on
  signed edge weights; community detection that penalizes sparse cuts; or
  soft/overlapping membership.
- The deepest alternative reframes the task entirely: **Reddy & Knight
  (2011)** (https://aclanthology.org/P11-2014/) treat the rhyme *scheme* as
  a latent structured object to infer — a prior over schemes regularizes
  the class structure — with no pronunciation dictionary at all. Unit 14's
  sweep includes one edge-weight-aware clustering condition precisely to
  *price* what the components choice costs, rather than guessing.

Naming the modeling decision **is** the computational-linguistics work
here. The code is a few lines of union-find; the judgment — components vs.
cliques vs. scheme-inference — is the substance, and the field has already
held the debate. What the project adds is the discipline of writing its
choice down as a choice and scheduling the measurement.

## Common confusions

- **Treating the threshold as objective.** It's a dial trading precision
  for recall. Unit 14 measures the tradeoff; until then it's a recorded
  guess (0.75, chosen from the empty band between observed clusters —
  see `rhyme.py`'s comment).
- **Assuming one right grouping exists.** Human annotators genuinely
  disagree about slant rhyme — perception differs, and that's a *finding*
  in the literature (Katz), not an annoyance. It's why Unit 14 reports
  inter-annotator agreement as the ceiling any scanner score is read
  against.

## Check yourself

> Check yourself: group the line-end words of a verse you like at some
> threshold. Find one grouping you can defend and one you can't. For the
> indefensible one — is the fix the threshold, or the grouping rule
> itself? (If lowering the threshold un-glues one bad class but breaks a
> good one elsewhere, you've just rediscovered why item 2's ledger entry
> says the fix must come from the feature space.)

## Exercise

From the syllabus: find a real non-transitive triple in a real verse,
decide how your grouping should treat it, and encode the decision as a
test.

**Where this is heading:** these groups are the data behind Unit 12's
colors, the scanner (Unit 11) feeds its *selected matches* — not recomputed
scores — into this same grouping, and Unit 14 finally prices the whole
arrangement against gold annotations.
