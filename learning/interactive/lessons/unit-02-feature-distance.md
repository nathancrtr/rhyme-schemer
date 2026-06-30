# Unit 2 Lesson Guide: Feature Distance (a baby embedding)

**Objective:** The learner sees `vowel_distance` not as ad-hoc arithmetic but as "distance in a feature space," and recognizes it as the same idea behind word embeddings — scaled down to 15 vowels.
**Prerequisites:** Unit 1; comfort reading `features.py`.
**Pairs with:** widget `vowel-explorer.html`; `features.py` (vowel half).

## How to run this lesson
Dialogue, one question per turn. Use the widget live — have the learner click pairs as you go.

## 1. Diagnostic opener
Ask: **"`vowel_distance('IH','IY')` is small and `vowel_distance('IH','UW')` is large. Before looking at the code — what real difference between those vowels is the number measuring?"**
- Toward "IH and IY are both front/high, UW is back" → step 2.
- Unsure → have them open the widget and click the three vowels; the geometry answers it.

## 2. Build the intuition
Each vowel is a point on the height × backness plane; distance on that plane *is* dissimilarity.

> PAUSE. Ask: **"`AY` ('bite') is stored as a glide from one point to another, not a single point. Why would a single (height, backness) point fail to capture it?"**

Wait. Land it: a diphthong's quality *moves* during the vowel; modeling it as start→end is the smallest honest representation. Have them click `AY` and `OY` in the widget and notice the shared offglide pulls them together.

## 3. Formalize
- `vowel_distance` = mean plane-distance of the start points and the end points, plus small nudges for rounding and rhoticity, normalized to [0,1].
- Identity ⇒ 0; symmetry holds; range is bounded — exactly the structural tests in `test_features.py`.

Connect back: **"You've just built a 4-dimensional embedding by hand. word2vec does the same thing — 'similar = close in a learned vector space' — only with 300 dimensions learned from data instead of 4 placed by ear. When you meet embeddings on your ML track, you'll have already implemented the core idea."**

## 4. Common confusions
- **Tense/lax as a separate feature.** It isn't here — `IH` sits lower/more central than `IY`, so the contrast falls out of *position*. Show them the coordinates.
- **Why a square, not the IPA trapezoid.** The code uses Euclidean distance on raw coordinates, so the honest picture is a square; the trapezoid is a presentation choice. The widget notes this.

## 5. Exit check
Ask: **"Pick two vowels you'd expect to be middling-close, predict the similarity to one decimal, then check in the widget. If you're off, is it the height axis or the backness axis fooling you?"**
- Good calibration → on to the exercise (justify/adjust a coordinate, keep ordering tests green).
- Off → re-run with a clearer pair and re-examine which axis dominates.

**Where this is heading:** this graded vowel similarity is the raw material the rhyme kernel (Unit 7) will weight and combine.
