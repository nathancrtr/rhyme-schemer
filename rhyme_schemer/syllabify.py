"""Turn a flat CMUdict phoneme list into structured syllables.

CMUdict gives us pronunciations as a flat sequence of phonemes with no syllable
boundaries:

    lincoln -> L IH1 NG K AH0 N

This module reconstructs the boundaries using two classic rules:

1. **One nucleus per syllable.** Every vowel is the nucleus of exactly one
   syllable, so the number of vowels is the number of syllables.

2. **Maximal Onset Principle (MOP).** A run of consonants sitting *between* two
   vowels is split so that the *following* syllable's onset is as long as
   English phonotactics allow (see ``phonetics.is_legal_onset``); whatever is
   left over becomes the *preceding* syllable's coda.

Word-initial consonants are entirely the first onset; word-final consonants are
entirely the last coda (there is no neighbor to compete for them).
"""

from __future__ import annotations

from typing import Optional

import pronouncing

from .models import Pronunciation, Syllable
from .phonetics import Stress, is_legal_onset, is_vowel, strip_stress


def _split_consonants(cluster: list[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Split an intervocalic consonant run into (coda, next_onset) via MOP.

    We try to hand as many consonants as possible to the onset (largest first),
    keeping only what forms a legal English onset; the rest is the coda.
    """
    n = len(cluster)
    for onset_len in range(n, -1, -1):
        onset = tuple(cluster[n - onset_len:])
        if is_legal_onset(onset):
            coda = tuple(cluster[: n - onset_len])
            return coda, onset
    # Unreachable: the empty onset is always legal, so the loop always returns.
    return tuple(cluster), ()


def syllabify(phones: list[str]) -> tuple[Syllable, ...]:
    """Convert a list of ARPAbet tokens (with stress digits) into syllables."""
    vowel_positions = [i for i, p in enumerate(phones) if is_vowel(p)]
    if not vowel_positions:
        # No vowel => no nucleus => nothing we can syllabify (e.g. stray "HH").
        return ()

    syllables: list[Syllable] = []
    for n, vpos in enumerate(vowel_positions):
        base, stress = strip_stress(phones[vpos])

        # Onset: consonants between the previous vowel and this one. For the
        # first syllable that's everything before the first vowel.
        if n == 0:
            onset = tuple(phones[:vpos])
        else:
            onset = _pending_onset  # computed when we processed the gap below

        # Coda + the *next* syllable's onset come from the consonants between
        # this vowel and the next one.
        if n + 1 < len(vowel_positions):
            gap = phones[vpos + 1 : vowel_positions[n + 1]]
            coda, _pending_onset = _split_consonants(gap)
        else:
            # Last syllable: everything after the final vowel is coda.
            coda = tuple(phones[vpos + 1 :])

        syllables.append(
            Syllable(onset=onset, nucleus=base, coda=coda, stress=stress or Stress.UNSTRESSED)
        )

    return tuple(syllables)


def pronunciation_for(word: str) -> Optional[Pronunciation]:
    """Look up ``word`` in CMUdict and syllabify it.

    Returns ``None`` for out-of-vocabulary words (our agreed "skip-and-flag"
    behavior). For now we take the *first* pronunciation variant; handling
    multiple variants is deferred.
    """
    variants = pronouncing.phones_for_word(word.lower())
    if not variants:
        return None
    phones = variants[0].split()
    return Pronunciation(syllables=syllabify(phones), text=word)
