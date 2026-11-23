# Feature-space audits

Corpus-derived evidence checks on the hand-placed feature spaces in
`rhyme_schemer/features.py`. **Audit, not tuning**: per the standing freeze
(tuning-ledger, Unit 11 walkthrough), nothing in `features.py` moves because
of anything found here — findings are recorded as ledger items 11–13 and
become *conditions* in Unit 14's evaluation sweep.

## Contents

- `hirjee_brown_2009.py` — Hirjee & Brown's learned rhyme scoring matrices
  (vowels and coda consonants), transcribed from Tables 1–2 of their ISMIR
  2009 paper, with a validating parser. These are BLOSUM-style log-odds
  estimated from observed rap rhyme pairs: the empirical record of which
  sound pairs rappers actually treat as rhymable.
- `audit_feature_space.py` — the rank comparison (`python
  learning/audits/audit_feature_space.py`). Rank, because log-odds entangle
  similarity with frequency correction: absolute values aren't on our [0, 1]
  scale, but if the corpus calls a pair unrhymable and our space calls it
  closest-of-all, the *orderings* disagree, and that is scale-free evidence.
- `audit_bark.py` — the same rank comparison for a competing vowel space:
  Bark-scaled formant space from Hillenbrand et al. (1995), next to the
  hand-placed one, on the 12 vowels both sources cover (`python
  learning/audits/audit_bark.py`).
- `derive_hillenbrand_bark.py` — dev-only. Downloads the Hillenbrand data
  into the gitignored `.cache/`, checks its hash, converts formants to Bark
  and averages them per vowel and condition. Its docstring walks through
  each step.
- `hillenbrand_1995_bark.py` — the output of the script above: per-vowel
  Bark means for each audit condition. Generated; don't edit it by hand.

## Findings (2026-08-07)

Full statements live in tuning-ledger items 11–12; headline:

- **Vowels** (ρ = +0.51): two systematic biases. *Front-glide generosity* —
  EY~IH is our closest pair of all 105 but corpus-negative; AY~EY is our
  9th vs the corpus's 102nd. *Rhoticity overpriced* — the corpus treats
  ER-pairs (AA~ER, ER~UH...) as far more rhymable than we do, plausibly
  because non-rhotic AAE performance vocalizes coda /r/; decided
  variant-first (mint non-rhotic readings as priced data), `_W_RHOTIC` as
  the sweep's comparison condition. Exonerated: EH~IH (corpus +0.2) and
  AA~AO (+1.6) are corpus-endorsed — fixes must be surgical.
- **Consonants** (ρ = +0.41): coda stop-place mismatches overpriced (B~G,
  K~P corpus-positive); DH row overly generous on our side; Katz 2015's
  nasal-place discount is unrepresentable in our parallel-plane geometry
  (though pooled H&B log-odds don't show it either — a genuine tension in
  the literature); Kawahara 2007's qualitative ordering we pass.

## Findings: the Bark arm (2026-11-22)

Full statements live in tuning-ledger item 13. Spearman ρ against H&B's
vowel log-odds, all on the same 66 pairs of 12 vowels:

| Space | ρ |
|---|---|
| Hand-placed quadrilateral (`features.py`) | +0.561 |
| Bark F1/F2, steady state, men | +0.681 |
| Bark F1/F2 at 20% and 80%, men | +0.693 |
| Bark F1/F2/F3 at 20% and 80%, men | +0.625 |
| Lobanov-Bark F1/F2 at 20% and 80%, men and women | +0.553 |
| Lobanov-Bark F1/F2/F3 at 20% and 80%, men and women | +0.360 |

- **Bark orders pairs better than the hand space, but the gap isn't
  established.** A bootstrap over pairs puts the ρ difference (best Bark
  condition minus hand) at +0.128, 95% CI [−0.017, +0.307], and that
  interval is optimistic because pairs share vowels.
- **Bark doesn't fix EY~IH.** Rank 3 of 66 in Bark (1 in the hand space,
  38 in the corpus). The pair really is acoustically close; why rappers
  avoid it is open.
- **F3 hurts, mostly through ER.** F3 is the main acoustic cue for
  r-coloring. Adding it pushes ER away from the other vowels (AH~ER rank
  10 → 32; 55 once Lobanov normalization is added too) and lowers ρ. That
  fits ledger item 11b's reading that the corpus's ER rhymes were
  performed without the r.
- **The reference data carries a dialect.** AE~EH is Bark's closest pair
  (corpus rank 22), consistent with the raised /æ/ of the talkers'
  southern Michigan dialect.
- **Lobanov normalization hurt.** Cause unknown.

## Provenance notes

- A July 2026 review claim that Katz 2015 / Kawahara 2007 could audit the
  *vowel* space was checked and found wrong (both datasets are consonantal;
  Katz keys rhyme detection on matched vowel quality by construction). See
  the corrected note in `learning/learning-resources.md`.
- H&B's consonant matrix covers **coda** position only (their "*" columns,
  unmatched coda edges, are dropped in transcription) — convenient, since
  our kernel ignores onsets too.
- The matrices are estimated from 1980s–2000s rap albums; genre and era are
  baked into the counts. That is a feature for this project (it's our
  target register), but it is not "English rhyme" in general.
- Hillenbrand, Getty, Clark & Wheeler (1995), *JASA* 97(5):3099–3111,
  doi:10.1121/1.411872. Fetched from Santiago Barreda's MIT-licensed mirror
  (https://github.com/santiagobarreda/hillenbrand_et_al_1995, hosted with
  Hillenbrand's permission), pinned to one commit and checked by SHA-256.
  Only derived per-vowel means are committed, never the raw measurements or
  the recordings.
- **Talker dialect.** 87% of Hillenbrand's talkers were raised in southern
  Michigan and nearly all the rest elsewhere in the inland northeast
  (Hillenbrand 2003, p. 121): Northern Cities Shift territory.
  Whatever dialect the reference data has gets built into the metric, and
  hip-hop's main dialect is African American English, not Inland North.
  This is the CMUdict dialect caveat in acoustic form.
- **No AY, AW or OY.** The 1995 study recorded 12 /hVd/ vowels (EY and OW
  among them) and no other diphthongs, so the Bark arm covers 66 of H&B's
  105 vowel pairs. A search for a source to fill the gap (2026-11-22)
  found no published onset/offset table. Jacewicz, Fox & Salmons (2011),
  *JSLHR* 54(2):448–470, doi:10.1044/1092-4388(2010/10-0161), is the
  nearest fit (hide/howed/hoyd, southeastern-Wisconsin men, 20–80% of
  the vowel) but gives values only in a figure, under unclear terms;
  Hillenbrand (2003) draws the three diphthongs impressionistically, with
  no numbers. Building them from monophthong endpoints was declined.
- The F3 conditions drop tokens with an unmeasurable F3, and ER loses the
  most (38 of 45 men's tokens survive). F3 is hardest to track exactly
  where it matters most, so the F3 rows rest on less ER data than the
  others.
