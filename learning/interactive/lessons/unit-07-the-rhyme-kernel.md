# Unit 7 Lesson Guide: The Rhyme Kernel

**Objective:** The learner can explain and implement `rhyme_score` as a *graded* function — perfect rhyme as the special case at the top of a continuum, slant rhyme as everything tunable below it — and understands the weights as approximations of perceptual similarity.
**Prerequisites to check:** Units 5 (rhyme tail) and 6 (perfect-rhyme scoring) done; `vowel_similarity`/`consonant_similarity` understood.
**Pairs with:** `rhyme_schemer/rhyme.py`; widget `rhyme-score-sandbox.html`; the perceptual-similarity reading.

## How to run this lesson
Dialogue, one question per turn. The learner has built perfect-rhyme scoring already; this lesson is about *loosening* it without breaking it. Resist handing them the weights — make them derive the shape.

## 1. Diagnostic opener
Ask: **"Your Unit 6 scorer returns 1.0 for 'cat'/'hat' and something low for 'cat'/'dog'. What does it currently return for 'Lincoln'/'reason', and is that what you want?"**
- If they've noticed it scores too low (the codas match but the vowels `IH`/`IY` aren't identical): good, the problem is live. → step 2.
- If unsure: have them run it. The gap between the number and their ear is the lesson.

## 2. Build the intuition
The perfect-rhyme scorer treats vowels as equal-or-not. But Unit 2 gave us *graded* vowel similarity. The kernel's job is to let near-vowels contribute near-full credit.

> PAUSE. Ask: **"In the rhyming tail, which carries more rhyme weight — the nucleus (vowel) or the coda (consonants after it)? And should the onset count at all?"**

Wait for their reasoning. Steer toward the README's design: nuclei dominate, codas matter less, onsets are ignored. Ask *why* onsets are ignored (because "cat"/"hat" rhyme despite different onsets — that's the definition of rhyme).

> PAUSE. Ask: **"So if you're averaging similarities over the tail, how would you express 'codas count, but less'?"**

Lead them to a weighted average: weight on nucleus similarity, smaller weight on coda similarity, onset excluded.

## 3. Formalize
- `rhyme_score` over the tail = a weighted combination of per-position `vowel_similarity` (nuclei) and `consonant_similarity` (codas), nuclei weighted above codas, onsets dropped.
- A **threshold** turns the continuous score into a yes/no when needed; **1.0** recovers perfect rhyme exactly.
- The weights are not arbitrary: they approximate **perceptual similarity** — the empirical finding (Steriade's P-map; Hirjee & Brown) that the imperfect rhymes people actually accept track how confusable the sounds are.

Connect back: "This is the same move as a weighted feature combination in any scoring model you've built — the novelty is only that the features are articulatory."

## 4. Common confusions
- **Overfitting to one pair.** If they tune weights until "Lincoln/reason" is perfect, ask what that did to "cat/cot." Insist on a *battery* of pairs and on testing *orderings*, not magnitudes.
- **Threshold vs. weights.** Tease these apart: weights shape the ranking; the threshold only decides where to cut. Slant-rhyme looseness is mostly the threshold.
- **Codas overpowering.** If a matched coda rescues a bad vowel pair, the coda weight is too high — rhyme is vowel-led.

## 5. Exit check
Ask: **"Predict the ordering of these by your score, then run them: 'time'/'rhyme', 'time'/'tone', 'Lincoln'/'reason', 'Lincoln'/'orange'. If the ranking is wrong, is it a weight problem or a threshold problem?"**
- Correct ranking + correct diagnosis → send them to encode that ordering as tests and to the sandbox widget to feel the weight knobs.
- Wrong → return to step 2 and separate the two knobs again on their actual numbers.

**Where this is heading:** the kernel assumes the two tails are the *same length*. Unit 8 breaks that assumption — multisyllabic rhyme needs alignment.
