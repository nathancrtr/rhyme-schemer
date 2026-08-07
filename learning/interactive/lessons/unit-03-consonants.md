# Unit 3: Consonants — place, manner, voicing, sonority

**Objective:** you can read the consonant half of `features.py` as a
deliberate parallel to the vowel space — a 2-D plane plus a binary nudge —
and explain why its axes are place and sonority-ordered manner.
**Prerequisites:** Unit 2. **Pairs with:** `features.py` (consonant half).

## The same move, different anatomy

Unit 2 put vowels on a plane (height × backness) and made similarity a
distance. Consonants get the parallel treatment, but their anatomy offers
different axes:

- **Place of articulation** — *where* the airflow is constricted, front to
  back: bilabial (p, b, m) → labiodental (f, v) → dental (th) → alveolar
  (t, d, s, n, l) → postalveolar (sh, ch, r) → palatal (y) → velar
  (k, g, ng) → glottal (h). Run "p, t, k" and feel the constriction walk
  backwards through your mouth.
- **Manner of articulation** — *how* the constriction shapes the air: a
  full stop and release (stops), a stop released into friction
  (affricates), turbulent narrowing (fricatives), airflow through the nose
  (nasals), vowel-like partial closures (liquids), and nearly-vowels
  (glides).
- **Voicing** — whether the vocal folds vibrate. Put a finger on your
  throat and alternate "sss"/"zzz": same place, same manner, voicing is
  the entire difference.

`features.py` maps place and manner to the plane's two axes and treats
voicing the way roundedness was treated for vowels: a small weighted nudge
(`_W_VOICE = 0.2`), because voicing is a real but *minor* perceptual cue
for rhyme.

## Why manner is ordered by sonority

The manner axis isn't in arbitrary order — it runs stop → affricate →
fricative → nasal → liquid → glide, which is the **sonority hierarchy**
from least to most vowel-like.

> PAUSE. Why is that the right *ordering* for a similarity axis? What pair
> of manners should be nearest neighbors, and does the sonority order
> agree?

Two payoffs. First, similarity: sonority-adjacent manners genuinely
confuse — a liquid and a glide are both "almost a vowel," a stop and an
affricate share the closure. Distance along a sonority-ordered axis tracks
that. Second, foreshadowing: Unit 4 builds syllables on the principle that
sonority *rises* to the nucleus and *falls* after it — the same hierarchy
does double duty as a similarity scale here and a well-formedness principle
there. One concept, two load-bearing jobs.

## Predict, then check

> PAUSE. Using the axes, predict which pair is closer in each case, then
> verify with `consonant_similarity` in a REPL: (a) M~N vs M~SH;
> (b) S~Z vs T~K; (c) S~Z vs S~SH.

The real numbers: M~N is 0.752 (a pure place move, same manner) while M~SH
is 0.502 (place *and* manner *and* voicing all differ). S~Z is 0.876 (only
the 0.2 voicing nudge) while T~K is 0.721 (a long place move,
alveolar → velar). And the third case is the instructive one: S~SH comes
out at 0.907 — *closer than the voicing pair* — because one step along the
place axis (alveolar → postalveolar, 0.15) costs less than the voicing
nudge (0.2). Small place steps are cheap; voicing is mid-priced; big place
moves and manner jumps are dear. Whether that pricing is *right* is an
empirical question — which is the next section.

## The audit: what corpus evidence says about this space

The course ran the check (Unit 2 told this story for vowels;
`learning/audits/` holds the machinery). Rank-compared against Hirjee &
Brown's rhyme-derived consonant matrix, this space agrees moderately
(Spearman ρ ≈ +0.41) with three instructive disagreements, recorded as
tuning-ledger item 12:

- **Coda stop-place is overpriced.** Rap practice freely rhymes K against
  P and B against G in codas (both corpus-positive; Hirjee & Brown note
  those very pairs "validate Holtman's hierarchy") — but our long place
  moves rank them among the most distant pairs. The ear evidently forgives
  coda place more than a tongue-position map suggests.
- **The nasal discount is unrepresentable.** Katz (2015) found place
  mismatches among *nasals* (m~n) perceptually far cheaper than among oral
  stops (t~k) — but our parallel geometry prices both as the same place
  move, *by construction*. A hand-built space can't express an asymmetry
  its axes don't encode. (Honest complication: pooled corpus counts don't
  show the asymmetry either — a live tension between the two best
  sources.)
- **Kawahara's ordering: we pass.** His often-rhyming Japanese pairs
  (m~n, t~s, r~n) all outrank his rarely-rhyming ones (m~ʃ, n~p) in our
  space. The space isn't wrong — it's an approximation with mapped edges.

## Why consonants matter less here (and where the weight lives)

Consonants matter to rhyme mostly in the **coda** — and less than vowels
overall. Notice what the code does with that fact: `features.py` does *not*
bake a discount into `consonant_distance`. The relative weighting lives one
layer up, in the rhyme scorer (Unit 7's `DEFAULT_CODA_WEIGHT`). Each layer
knows only its own business: the feature space answers "how similar are
these two sounds?", the kernel answers "how much does that matter for
rhyme?" — the stratification discipline the whole repo runs on.

## Check yourself

> Check yourself: (1) Why is HH (glottal) the loneliest consonant on the
> plane? (2) Which does our space treat as more similar, CH~JH or CH~SH —
> and what feature drives each comparison? (3) State the nasal-discount
> problem from memory, and why the current geometry cannot express it.

## Exercise

From the syllabus: add an ordering assertion of your own — the classic is
that voicing pairs (S~Z, P~B) beat big place moves (T~K) — and write one
sentence explaining the weight that makes it true. House style: orderings,
not magnitudes.

**Where this is heading:** Unit 4 assembles phonemes into syllables using
the sonority hierarchy you just met; the coda similarities priced here
become the kernel's texture term in Units 6–7.
