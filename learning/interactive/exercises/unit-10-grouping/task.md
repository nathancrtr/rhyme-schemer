# Unit 10 Exercise — Components & the Grouping Decision

**What you're building:** the grouping step itself — union-find connected
components, plus the thin wrapper that turns pairwise scores and a threshold
into rhyme classes. Then one test makes you *sign* the modeling decision the
unit is about.

**Before starting:** read the `graphs-and-union-find` companion if you
haven't — the exercise assumes its §4 hand-trace.

## Work the trace by hand first

Five nodes, edges `(0,1), (3,4), (1,2)`:

```
start:      parent = [0, 1, 2, 3, 4]
union(0,1): parent = [0, 0, 2, 3, 4]     1's rep is now 0
union(3,4): parent = [0, 0, 2, 3, 3]
union(1,2): find(1) walks 1 → 0; 2 joins:  parent = [0, 0, 0, 3, 3]
result:     {0,1,2} and {3,4}
```

Now add edge `(2,4)` and trace again — you should end with one component of
five. That single edge merging two whole clusters is the mechanism behind
everything Unit 10 warns about.

## The spec

1. **`connected_components(count, edges)`** — fill `find` (walk to the
   representative) and `union` (merge representatives). The collection loop
   is provided. Path compression is optional; correctness doesn't need it
   at this scale.
2. **`group_rhymes_by_threshold(words, scores, threshold)`** — threshold
   the scores into edges, group, and return word lists.

## Run the tests

```bash
cd learning/interactive/exercises/unit-10-grouping
python -m unittest test_components -v
```

The suite includes the hand-trace above, singletons, order-independence of
edges — and two tests worth reading before you make them pass:

- **`test_the_bridge_glues_two_good_clusters`** pins percolation: a single
  borderline edge merges two clean classes. Your implementation *should*
  do this — that's the point. The test documents the failure mode as
  chosen behavior.
- **`test_non_transitive_triple_is_grouped_anyway`** is the unit's
  decision made executable: A~B and B~C above threshold, A~C below —
  components put all three together. The test's docstring says why the
  project accepts this (and where the alternatives live). Passing it
  means you've implemented the choice; understanding it means you could
  argue for a different one.

## Afterward

Diff against `rhyme_schemer/rhyme.py`'s `_UnionFind` /
`connected_components` — did you compress paths? Did the repo? Then open
the Grouping Explorer widget and find the threshold where the bridge test's
situation happens on real verse data.
