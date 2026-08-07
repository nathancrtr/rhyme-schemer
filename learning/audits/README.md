# Feature-space audits

Corpus-derived evidence checks on the hand-placed feature spaces in
`rhyme_schemer/features.py`. **Audit, not tuning**: per the standing freeze
(tuning-ledger, Unit 11 walkthrough), nothing in `features.py` moves because
of anything found here — findings are recorded as ledger items 11–12 and
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
