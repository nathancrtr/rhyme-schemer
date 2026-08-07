# Graphs, Components, and Union-Find from Zero

*A companion essay for Unit 10. No graph theory or algorithms background
assumed — by the end you can read `connected_components(count, edges)` in
`rhyme.py` line by line and explain why grouping rhymes was secretly a
graph problem all along. If you already know union-find from interview
prep, skim §4 for the repo specifics and go back to Unit 10.*

---

## 1. A graph is a set of claims

Strip away the textbook formality and a **graph** is just: some things
(**nodes**), and some pairwise claims about them (**edges**). Nothing more.
The things here are the words of a verse; the claim is *"these two rhyme"*
— an edge appears between two words exactly when `best_is_rhyme` says yes.

```
  cake ─── shake        debate ─── great        one
    │       │
    └─ state┘                                   feeling
```

Six words, four claims. Drawing it makes the structure jump out: cake,
shake, and state form one cluster; debate and great another; "one" and
"feeling" sit alone. Those clusters are what Unit 10 calls **rhyme
classes**, and the graph vocabulary for them is **connected components**: a
component is a maximal set of nodes where every node can reach every other
by walking edges. "Maximal" carries weight — you can't extend the
cake-cluster by even one node without breaking reachability, and a node
with no edges is a component of size one, all by itself.

Notice what reachability quietly permits: cake and state are in one
component *even if the cake~state edge were missing*, as long as both
connect to shake. The walk is allowed to go **through** intermediate nodes.
Hold that thought; it is the entire drama of Unit 10.

## 2. Finding components the obvious way: spreading paint

Here's an algorithm you already believe in. Pour paint on any node. Paint
flows along edges. When it stops spreading, everything wet is one
component; pour a fresh color on any dry node and repeat.

That's **flood fill** (as breadth-first or depth-first search), and it's a
perfectly good way to compute components: visit a node, visit its
neighbors, their neighbors, until nothing new appears. Linear time,
easy to write. If the project only ever needed "given this finished graph,
list the components once," flood fill would be the end of the story.

## 3. The other way: answer without walking

**Union-find** (also "disjoint-set union," DSU) attacks the same problem
from a different angle. Instead of exploring a finished graph, it
*maintains* the component structure while edges arrive one at a time,
answering two questions at any moment:

- `find(x)` — which component is x in? (Answered by a representative
  member — an arbitrary "captain" of the component.)
- `union(x, y)` — an edge arrived; merge x's and y's components if they
  differ.

The data structure is almost embarrassingly small: one array, `parent`,
where each node points at some node in its own component, and captains
point at themselves. `find` follows parent pointers up to the captain;
`union` makes one captain point at the other. That's it — component
membership stored as a forest of pointer-trails.

## 4. Walk it by hand, on the repo's own function

`rhyme.py` exposes exactly this as `connected_components(count, edges)`:
nodes are the integers `0..count-1` (indices into whatever list you're
grouping — words, matches), and each edge is a pair of indices. Take five
nodes and three edges — `(0,1)`, `(3,4)`, `(1,2)`:

```
start:      parent = [0, 1, 2, 3, 4]     five captains, five solo components
union(0,1): parent = [0, 0, 2, 3, 4]     1's captain is now 0
union(3,4): parent = [0, 0, 2, 3, 3]     4's captain is now 3
union(1,2): find(1) walks 1 → 0.         2 joins 0's component:
            parent = [0, 0, 0, 3, 3]
result:     components {0,1,2} and {3,4}
```

> PAUSE. Before reading on: add `union(2, 4)` to the trace yourself.
> Which captain wins, and what does `parent` look like after? Then predict
> what `connected_components(5, [(0,1),(3,4),(1,2),(2,4)])` returns.

(One component containing everything — 4's trail leads to captain 3, 2's
to captain 0, and one of the two captains bows to the other. Five nodes,
four edges, one class.)

Real implementations add two easy accelerations you'll see in the repo's
`_UnionFind`: **path compression** (while walking to the captain, repoint
everything you passed directly at the captain, flattening the trail for
next time) and merging small-into-large. With both, each operation is
*effectively constant time* — the true bound involves a function (inverse
Ackermann) that grows so slowly it never exceeds 4 for any input that fits
in the universe. For verse-sized inputs none of this matters for speed; it
matters that you recognize the names.

## 5. Why union-find here, when flood fill would do?

Three honest reasons, in descending weight:

1. **Shape fit.** The scanner produces matches as a *list of pairs* — the
   edges arrive already in union-find's native format, and the nodes are
   just indices. `connected_components(count, edges)` is ten lines.
2. **Reuse.** The same helper groups words (Unit 10) and, later, selected
   matches (Unit 11) and abutting compound beats (Unit 12's chaining is
   "union-find over an abuts relation"). One tiny structure, three
   callers.
3. **The incremental frame is the *conceptually* right one.** Each edge is
   an independent claim ("these two rhyme"), and the component structure
   is the *accumulated consequence* of all claims so far. Union-find makes
   that reading literal: classes are what you get by merging one claim at
   a time — which sets up the unit's real question.

## 6. The setup for the trap

Look again at what `union` does: it merges whole components on the
strength of a *single* edge. No second opinion, no vote, no undo. One
claim, and two entire clusters become one forever.

For truly transitive relations ("same birthday," "same connected circuit")
that's just correct. But Unit 10's punchline is that slant rhyme is **not
transitive** — A~B and B~C can both be true while A~C is false — and
union-find *imposes* transitivity structurally, by construction, with no
way to express dissent. The clustering literature calls components over
threshold edges **single-link clustering**, and its signature failure —
one generous edge gluing two good clusters into a mega-class — is
**chaining**. When the tuning ledger's items 1 and 9 report "mush twin"
classes and an OW mega-class, the mechanism is exactly the pointer-merge
you traced in §4: some single borderline edge fired, and union did what
union does.

None of that makes union-find the wrong tool — it makes it an *honest*
implementation of a debatable modeling choice. The choice, its rivals
(cliques, correlation clustering, scheme inference), and the plan to
price it are Unit 10's subject. Go back there carrying this: **the
algorithm is innocent; the modeling decision is load-bearing.**

### If you want to go deeper

- Union-find is a staple of interview prep and competitive programming
  (Kruskal's minimum-spanning-tree algorithm is its most famous client) —
  any algorithms text covers it under "disjoint sets."
- Flood fill / BFS / DFS: the same texts, one chapter earlier; also the
  algorithm behind the paint bucket in every image editor.
- The inverse-Ackermann analysis (Tarjan 1975) is a celebrated result —
  not needed here, delightful if you like that sort of thing.
