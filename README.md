# rhyme-schemer

Take hip-hop lyrics as plain text and surface their rhyme scheme — highlighting
and grouping the words that rhyme, in the spirit of the Vox / Matt Daniels
*"Hypnotize"* rhyme visualizations.

The north star is **slant rhyme and assonance, not just perfect rhyme.** Hip-hop
rhyme is built on matching *vowel sounds*; consonants are flexible texture. A tool
that only finds perfect rhymes ("cat" / "hat") misses almost everything that makes
rap rhyme interesting — so "Lincoln" / "reason" needs to count.

This is first and foremost a learning project for working through NLP and
phonetics from the ground up. The code is written to be read.

## Approach

The pipeline is **syllable-first**. Pronunciations come from the
[CMU Pronouncing Dictionary](http://www.speech.cs.cmu.edu/cgi-bin/cmudict)
(ARPAbet symbols) via the [`pronouncing`](https://pypi.org/project/pronouncing/)
library.

1. **Look up & syllabify.** A flat CMUdict phoneme list (`lincoln → L IH1 NG K AH0
   N`) is split into structured syllables using the **Maximal Onset Principle**,
   constrained by a hand-listed inventory of legal English onset clusters.
2. **Model.** The universal unit is a `Pronunciation`: an ordered tuple of
   `Syllable(onset, nucleus, coda, stress)`. A single word and a multi-word span
   (e.g. *"ménage à trois"*) are both just pronunciations, so nothing downstream
   cares which it started as.
3. **Score similarity.** Rhyme is graded, not binary, so vowels and
   consonants live in small **articulatory feature spaces** and similarity is
   distance in those spaces:
   - **Vowels** are placed on the IPA vowel quadrilateral (tongue height ×
     backness), plus roundedness and a rhotic flag; diphthongs are modeled as a
     glide between two points.
   - **Consonants** get a parallel treatment: place × manner (manner ordered by
     sonority), plus voicing.
4. **Rhyme kernel.** `rhyme_score(a, b) -> float` scores the **rhyme tail** —
   the syllables from the last stressed syllable to the end — blending graded
   vowel similarity on nuclei with lower-weighted consonant similarity on codas,
   onsets ignored. Perfect rhyme is just the special case at threshold `1.0`;
   loosening toward slant rhyme is turning the threshold and weights, not
   rewriting the engine. Tails of unequal length (multisyllabic rhyme) are
   aligned with Needleman–Wunsch over their vowel skeletons before scoring.

Out-of-vocabulary words go through a **grapheme-to-phoneme fallback chain**
(`g2p.py`): dialect spellings recovered by rules that keep the spelled surface
phonology (*"chokin'"* gets choking's syllables but the spelled N coda), a
small slang lexicon (*"imma"*), and hand-written letter-to-sound rules for
genuinely unknown strings (*"Coogi"*) — with letter-to-sound guesses priced
so a marginal rhyme can't be built on a made-up pronunciation. Only words
even guessing can't voice (*"brrr"*) are still skipped and flagged.

## Status

Foundation built:

- `rhyme_schemer/phonetics.py` — ARPAbet inventory and English onset phonotactics
- `rhyme_schemer/models.py` — `Syllable` and `Pronunciation` data structures
- `rhyme_schemer/syllabify.py` — CMUdict lookup + Maximal Onset Principle syllabifier
- `rhyme_schemer/features.py` — vowel and consonant feature spaces with distance metrics

Rhyme kernel built:

- `rhyme_schemer/rhyme.py` — `rhyme_tail` (the rhyme-bearing tail), `align_tails`
  (Needleman–Wunsch over vowel skeletons), `rhyme_score` (graded perfect/slant
  scoring), and `is_rhyme` (thresholded yes/no)

Spans and pronunciation variants built:

- `rhyme_schemer/syllabify.py` — multi-word **spans** (`pronunciation_for_span`)
  and **all** CMUdict variants (`pronunciations_for`, `pronunciations_for_span`),
  a span being just a concatenated `Pronunciation`
- `rhyme_schemer/rhyme.py` — `best_rhyme_score` / `best_is_rhyme`, variant-aware
  scoring that takes the `max` over pronunciation variants around the unchanged
  kernel

Grouping into a scheme built:

- `rhyme_schemer/rhyme.py` — `group_rhymes`, which makes `best_is_rhyme` the edge
  test of a similarity graph and returns its **connected components** (union-find,
  exposed as `connected_components`) as rhyme classes. Because slant rhyme isn't
  transitive (A–B and B–C can rhyme while A–C doesn't), components are a
  deliberate, debatable modeling choice.

Internal & multisyllabic rhyme scanning built:

- `rhyme_schemer/scan.py` — `scan_verse(text)`: verse in, rhyme scheme out.
  Enumerates **(word span, anchor)** candidates — the anchor is a claim about
  *performed* stress, minted as data by `coerce_performed_stress` so the kernel
  needs no changes — then pairs candidates within a proximity window behind a
  **seed gate** (anchor nuclei must rhyme on their own; identical anchors are
  repetition, not rhyme), prices unlikely stress claims (**coercion cost**),
  selects one description per rhyme event (score-first: with averaged scores,
  an extension must *raise* the average to earn its seat, which also auto-splits
  glued rhyme chains), and reads the scheme off the match graph as connected
  components. Run on the *Lose Yourself* opening, it finds the full -etty chain
  (including "forgetting"), *nervous ~ surface*, *palms are ~ arms are*, and the
  `AW` family unprompted. See
  `learning/interactive/lessons/unit-11-scanner-walkthrough.md` for the full
  design walkthrough and open tuning ledger.

Visualization built:

- `rhyme_schemer/scan.py` — `chain_matches`, fusing abutting per-beat matches
  into the multisyllabic `Compound`s the ear hears ("palms are steady" ~
  "arms are ready" as one four-beat rhyme), a pure post-pass over selected
  matches.
- `rhyme_schemer/render.py` — `render_html` / `render_terminal` over a
  medium-agnostic `plan_verse` policy layer. Color marks the **rhyme class**
  (Pudding/Vox school — the picture shows what the scanner decided); a word
  in several classes gets its background from the best-scoring match, thin
  **tick** bars for the others, and full receipts in its tooltip; multi-beat
  compounds get a neutral spanning rule; OOV words are dotted-underlined so
  "unknown" never reads as "doesn't rhyme". Fills are CVD-validated tints in
  both light and dark mode.

Grapheme-to-phoneme fallback built:

- `rhyme_schemer/g2p.py` — `pronounce(word) -> Guess`: the fallback chain
  (dictionary → slang lexicon → normalization rules → letter-to-sound).
  Dialect spellings are treated as *performance transcriptions*: rules
  recover the dictionary stem, then keep the spelled surface phonology
  (g-drop's N-for-NG, *"holla"*'s non-rhotic final AH). Guess confidence is
  priced like stress coercion — `Guess.cost` folds into `Reading.cost`, so
  the kernel stays provenance-free — and renderers mark guessed words
  (dashed underline + provenance tooltip) so a guess never reads as
  dictionary fact.

Next up: **evaluation** against annotated ground truth — precision/recall
over hand-labeled verses, then one tuning sweep across every deferred knob
(thresholds, weights, vowel space, chaining gate).

## Development

```bash
pip install -r requirements.txt
python -m unittest discover tests
```
