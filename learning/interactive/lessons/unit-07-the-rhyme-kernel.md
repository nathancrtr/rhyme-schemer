# Unit 7: The Rhyme Kernel

**Objective:** you can explain and implement `rhyme_score` as a *graded*
function — perfect rhyme as the special case at the top of a continuum, slant
rhyme as everything tunable below it — and you understand the weights as
approximations of perceptual similarity. **Prerequisites:** Units 5 (rhyme
tail) and 6 (perfect-rhyme scoring); `vowel_similarity` /
`consonant_similarity` understood. **Pairs with:** `rhyme_schemer/rhyme.py`;
the Rhyme-Score Sandbox widget; the perceptual-similarity reading.

## The problem your Unit 6 scorer has

Your scorer returns 1.0 for cat/hat and something suitably low for cat/dog.

> PAUSE. What does it return for Lincoln/reason — and is that what you want?
> Run it before reading on.

If you've run it, you've seen the gap: the codas match but `IH` and `IY`
aren't *identical*, so an equal-or-not treatment of vowels scores the pair
far below where your ear puts it. That gap between the number and your ear
is this unit. Unit 2 built graded vowel similarity precisely so that
near-vowels can earn near-full credit — the kernel's job is to let them.

## Deriving the shape

> PAUSE. In the rhyming tail, which carries more rhyme weight — the nucleus
> (the vowel) or the coda (the consonants after it)? And should the onset
> count at all?

Work from cases. Cat/hat rhyme *despite* different onsets — that's not an
exception to rhyme, it's practically the definition: what comes before the
stressed vowel is free. So the onset contributes nothing. Between nucleus
and coda: say "read"/"seed" (nuclei differ, codas match) against
"read"/"red" (nucleus matches... in one pronunciation — more on that in
Unit 9). Hip-hop practice settles it emphatically: the north star is
vowel-led rhyme, consonants as flexible texture. So: **nuclei dominate,
codas matter less, onsets are ignored.**

> PAUSE. If you're averaging similarities over the tail, how do you express
> "codas count, but less" in arithmetic?

A weighted average per syllable position: a full weight on nucleus
similarity, a smaller weight on coda similarity, onset absent — then
normalize by the total weight so that an identical syllable scores exactly
1.0 *whatever* the weights are. That normalization is what keeps "perfect
rhyme = 1.0" true while you tune.

## The formal pieces

- `rhyme_score` over the tail = per-position weighted blends of
  `vowel_similarity` (nuclei) and `consonant_similarity` (codas), averaged.
  In the repo: `DEFAULT_NUCLEUS_WEIGHT = 1.0`, `DEFAULT_CODA_WEIGHT = 0.35`.
- A **threshold** turns the continuous score into a yes/no when a decision
  is needed (`is_rhyme`, default 0.75); threshold 1.0 recovers perfect
  rhyme exactly. Weights shape the *ranking*; the threshold only decides
  where to cut. Keep those two knobs separate in your head — most
  "looseness" questions are threshold questions.
- The weights are not arbitrary: they approximate **perceptual similarity**
  — the empirical finding (Steriade's P-map; Hirjee & Brown; the Katz and
  Kawahara line of work) that the imperfect rhymes people actually accept
  track how confusable the sounds are. Your weighted feature combination is
  ordinary scoring-model machinery; only the features are articulatory.

Now open the **Rhyme-Score Sandbox** and type pairs at it: it shows the
tails, every per-column nucleus/coda receipt, and the final score — the
exact numbers your `rhyme_score` produces. Try cat/hat, Lincoln/reason,
Lincoln/listen, read/seed. The receipts are the fastest way to see *which
term* is responsible for any score that surprises you.

## Common confusions

- **Overfitting to one pair.** If you tune weights until Lincoln/reason is
  perfect, check what happened to cat/cot. One pair is one datapoint;
  calibrate on a *battery*, and encode **orderings** (perfect > slant >
  none) as tests rather than exact magnitudes — the house test style
  exists for exactly this reason.
- **Fixing threshold problems with weights** (or vice versa). If the
  ranking is right but the yes/no is wrong, it's the threshold. If the
  ranking itself is wrong, no threshold can save it — that's weights, or
  the feature space underneath them (see the audit trail from Unit 2).
- **Codas overpowering.** If a matched coda rescues a bad vowel pair, the
  coda weight is too high — rhyme is vowel-led. (The repo's history has a
  recorded instance: read/seed scoring above threshold traces to generous
  vowel similarity *plus* the matched D, and it's logged as a known
  precision risk, not tuned away — the tuning freeze says knobs move only
  under Unit 14's evaluation.)

## Check yourself

> Check yourself: predict the *ordering* your score gives these, then run
> them — time/rhyme, time/tone, Lincoln/reason, Lincoln/orange. If your
> ranking disagrees with the code's, diagnose before fixing: weight
> problem, threshold problem, or feature-space problem?

## Exercise

From the syllabus: make Lincoln/reason score as a slant rhyme above your
chosen threshold while Lincoln/orange stays below — and encode the ordering
(perfect > slant > none) as tests, not magnitudes.

**Where this is heading:** the kernel silently assumes the two tails have
the same number of syllables. Unit 8 breaks that assumption — multisyllabic
rhyme needs alignment.
