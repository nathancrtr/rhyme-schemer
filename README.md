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

Out-of-vocabulary words (not in CMUdict, e.g. *"Coogi"*) are skipped and flagged
for now; grapheme-to-phoneme handling comes later.

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

Next up: from pairwise scores to a whole verse — multi-word spans and
pronunciation variants, then grouping rhymes into a scheme.

## Development

```bash
pip install -r requirements.txt
python -m unittest discover tests
```
