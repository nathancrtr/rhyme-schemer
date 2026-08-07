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

Both rules are *decision procedures*, not discovered truths, and MOP in
particular forces a clean answer where English is genuinely torn. Since Kahn
(1976), phonologists have observed that a consonant between a stressed lax
vowel and an unstressed one -- the /t/ in "sweaty" -- behaves as if it belongs
to **both** syllables at once ("ambisyllabic"): it flaps, which a true
syllable-initial /t/ (as in "attack") never does, yet ``SW EH1`` cannot stand
alone either, because a stressed lax vowel cannot end an English syllable.
We resolve the tie wholly in the onset's favor because the pipeline needs one
boundary, but the choice is lossy: whatever MOP hands to the onset disappears
from the preceding syllable's coda, and the rhyme kernel downstream ignores
onsets -- so a shared medial consonant vanishes from scoring entirely
(sweaty~heavy scores a perfect 1.0; see tuning-ledger item 7 in the Unit 11
walkthrough for the diagnosis and candidate fixes).
"""

from __future__ import annotations

import itertools
from typing import Optional, Sequence

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


def pronunciations_for(word: str) -> list[Pronunciation]:
    """Look up *all* of ``word``'s CMUdict pronunciations and syllabify each.

    CMUdict often lists several pronunciations for one spelling -- "read" is
    ``R EH1 D`` or ``R IY1 D``, "either" is ``IY1 DH ER0`` or ``AY1 DH ER0`` --
    and a rapper picks whichever *variant* makes the line rhyme (pronunciation
    coercion). Returning the whole list is what lets scoring later take the best
    variant instead of guessing one.

    Returns an empty list for out-of-vocabulary words (the "skip-and-flag"
    contract: callers test truthiness). Order follows CMUdict, so the first
    entry is the one ``pronunciation_for`` returns.
    """
    variants = pronouncing.phones_for_word(word.lower())
    return [
        Pronunciation(syllables=syllabify(v.split()), text=word)
        for v in variants
    ]


def pronunciation_for(word: str) -> Optional[Pronunciation]:
    """Look up ``word`` and return its *first* CMUdict pronunciation.

    A convenience over ``pronunciations_for`` for the common case where one
    pronunciation is enough; returns ``None`` for out-of-vocabulary words. When
    a rhyme might hinge on a less-common pronunciation, reach for
    ``pronunciations_for`` (and variant-aware scoring) instead.
    """
    variants = pronunciations_for(word)
    return variants[0] if variants else None


def pronunciation_for_span(words: Sequence[str]) -> Optional[Pronunciation]:
    """Look up a multi-word span and return it as a single ``Pronunciation``.

    A span like ``["get", "up"]`` is just the two words' syllables laid end to
    end (see ``Pronunciation.concat``) -- the payoff of the model's core
    invariant that a word and a span are the same downstream object. This lets
    a multi-word phrase be scored against a single word ("get up" vs "setup")
    with the unchanged rhyme kernel.

    If *any* word is out of vocabulary, the whole span is OOV and we return
    ``None`` -- the same "skip-and-flag" contract as ``pronunciation_for``. Like
    it, this uses only the first CMUdict variant of each word; scoring over all
    variant combinations arrives in Unit 9's later phases.
    """
    prons = []
    for word in words:
        pron = pronunciation_for(word)
        if pron is None:
            return None
        prons.append(pron)
    return Pronunciation.concat(prons)


def pronunciations_for_span(words: Sequence[str]) -> list[Pronunciation]:
    """Enumerate *every* pronunciation of a multi-word span.

    A span's variants are the cartesian product of its words' variants: if
    "read"(2) precedes "it"(1) then "read it" has 2x1 = 2 spans, and each is one
    combination concatenated end to end (Phase 1). This is what lets scoring
    later pick the best-rhyming reading of a whole phrase, not just word by word.

    Returns an empty list if *any* word is out of vocabulary (its variant list
    is empty, so the product is empty) -- the span-level "skip-and-flag".
    """
    per_word = [pronunciations_for(word) for word in words]
    if any(not variants for variants in per_word):
        return []
    return [
        Pronunciation.concat(combo)
        for combo in itertools.product(*per_word)
    ]
