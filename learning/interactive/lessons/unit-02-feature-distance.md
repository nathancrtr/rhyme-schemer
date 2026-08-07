# Unit 2: Feature Distance (a baby embedding)

**Objective:** you see `vowel_distance` not as ad-hoc arithmetic but as
"distance in a feature space," and recognize it as the same idea behind word
embeddings — scaled down to 15 vowels. **Prerequisites:** Unit 1. **Pairs
with:** the Vowel-Space Explorer widget; `features.py` (vowel half).

Have the widget open in another tab as you read — every claim below is
clickable there, and the numbers it shows are the exact values
`vowel_distance()` computes.

## The question a number has to answer

`vowel_distance('IH','IY')` is small; `vowel_distance('IH','UW')` is large.

> PAUSE. Before looking at any code: what real, physical difference between
> those vowels is the number measuring?

Say the three vowels — "bit," "beat," "boot" — and pay attention to your
tongue. For the first two it sits high and forward; for "boot" it pulls high
and *back* (and your lips round). The number is measuring articulation:
where in the mouth the vowel lives. `features.py` places every vowel on a
plane — tongue **height** on one axis, **backness** on the other — and
similarity is simply distance on that plane. IH and IY are neighbors; UW is
across the map.

## Diphthongs: a vowel that moves

> PAUSE. `AY` ("bite") is stored as a *glide* from one point to another,
> not as a single point. Why would one (height, backness) point fail?

Because the vowel's quality *changes while you say it*: "bite" starts low
and central and ends high and front. A single point would have to average
away the very motion that makes it AY. Modeling a diphthong as start → end
is the smallest honest representation. Click `AY` and `OY` in the widget:
their *start* points are far apart, but the shared offglide (both end near
ɪ) pulls the pair's distance in. Hold that observation — it returns below
with consequences.

## The formal pieces

- `vowel_distance` = the mean of the plane-distances between the two
  start points and the two end points, plus small weighted nudges for
  **roundedness** and **rhoticity**, normalized into [0, 1].
- Identity ⇒ 0; symmetry holds; the range is bounded. Those three facts are
  exactly the *structural* tests in `test_features.py` — the house style is
  to pin properties and orderings, not magic numbers.
- You have just met a **4-dimensional embedding built by hand**. word2vec
  makes the same move — "similar = close in a vector space" — with 300
  dimensions learned from data instead of 4 placed by ear. When you meet
  embeddings elsewhere, you'll have already implemented the core idea at a
  size you can see all of.

## Common confusions

- **"Where's the tense/lax feature?"** There isn't one — deliberately. `IH`
  is *placed* lower and more central than `IY` (the standard lax
  centralization), so the tense/lax contrast falls out of position without
  a separate dimension. Look at the coordinates in `features.py`.
- **Why the widget draws a square, not the IPA trapezoid.** The code runs
  Euclidean distance on raw coordinates, so the honest picture of the space
  the code measures in is a square. The trapezoid is the traditional
  presentation of the same axes. The gap between them is worth noticing:
  every diagram encodes a choice.
- **Articulatory adjacency is not perceptual confusability — or rhyme
  practice.** The quadrilateral is a tongue-position diagram, not a
  psychoacoustic space (that would be Bark-scaled formant space), and not a
  record of what rappers actually rhyme. This project *checked*: the
  hand-placed space was rank-compared against Hirjee & Brown's rhyme-derived
  log-odds matrix (`learning/audits/`), and the audit found two systematic
  biases — the diphthong offglides you just clicked park EY and AY on top of
  the front vowels (EY~IH is our closest pair of all 105; the corpus says
  rappers treat it as unrhymable), and rhoticity is overpriced (non-rhotic
  performance rhymes ER against AH-like vowels far more freely than our
  binary flag allows). Tuning-ledger item 11 holds the full findings; Unit
  14 makes "refit this space from data" a first-class experiment. The space
  you're learning is a good pedagogical instrument *and* a measured
  approximation — both true at once.

## Check yourself

> Check yourself: pick two vowels you expect to be middling-close, predict
> the similarity to one decimal, then check in the widget. If you're off,
> which axis fooled you — height or backness? (And for a diphthong pair:
> was it the start or the end doing the work?)

## Exercise

From the syllabus: adjust or justify two coordinate choices in `features.py`
without breaking the ordering tests — predict which tests *would* shift
before you touch anything, then verify.

**Where this is heading:** this graded vowel similarity is the raw material
the rhyme kernel (Unit 7) weights and combines — and the audit above is your
first taste of Unit 14, where the whole space goes on trial.
