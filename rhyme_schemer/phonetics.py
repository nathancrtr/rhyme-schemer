"""Low-level ARPAbet facts.

This module knows nothing about rhyme. It only encodes the raw phonetic
inventory we get from the CMU Pronouncing Dictionary (ARPAbet symbols) plus a
couple of facts about English phonotactics that the syllabifier needs.

ARPAbet primer:
  - Phonemes are 1-2 letter uppercase symbols, e.g. ``L``, ``IH``, ``NG``.
  - *Vowel* symbols carry a trailing stress digit: 0 (unstressed),
    1 (primary), 2 (secondary). e.g. ``IH1``, ``AH0``.
  - *Consonant* symbols never carry a digit.

So "lincoln" arrives as the token list: ``L IH1 NG K AH0 N``.
"""

from __future__ import annotations

from enum import IntEnum


class Stress(IntEnum):
    """Lexical stress on a vowel, as encoded by CMUdict's trailing digit."""

    UNSTRESSED = 0
    PRIMARY = 1
    SECONDARY = 2


# The 15 ARPAbet vowel nuclei (ER, the r-colored vowel, counts as a vowel).
VOWELS = frozenset({
    "AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER",
    "EY", "IH", "IY", "OW", "OY", "UH", "UW",
})


def strip_stress(phoneme: str) -> tuple[str, Stress | None]:
    """Split a CMUdict token into (base phoneme, stress).

    Consonants have no stress, so the second element is ``None`` for them.

        >>> strip_stress("IH1")
        ('IH', <Stress.PRIMARY: 1>)
        >>> strip_stress("NG")
        ('NG', None)
    """
    if phoneme and phoneme[-1].isdigit():
        return phoneme[:-1], Stress(int(phoneme[-1]))
    return phoneme, None


def is_vowel(phoneme: str) -> bool:
    """True if the token (with or without a stress digit) is a vowel nucleus."""
    base, _ = strip_stress(phoneme)
    return base in VOWELS


# --- English onset phonotactics -------------------------------------------
#
# The Maximal Onset Principle lets a syllable boundary push consonants into the
# *following* onset only as far as English actually permits. The set of legal
# onset clusters is governed by the Sonority Sequencing Principle (sonority must
# rise toward the nucleus), with the well-known /s/-clusters as the systematic
# exceptions. Rather than implement sonority math, we list the inventory
# directly -- it's transparent and trivially extensible. This list is
# deliberately not exhaustive; add clusters as real lyrics expose gaps.

# A bare consonant is a legal onset, *except* /NG/ which never begins a syllable.
_ILLEGAL_SINGLE_ONSETS = frozenset({"NG"})

_TWO_CONSONANT_ONSETS = frozenset({
    # /s/ + voiceless stop / nasal / approximant / fricative
    ("S", "P"), ("S", "T"), ("S", "K"),
    ("S", "M"), ("S", "N"),
    ("S", "L"), ("S", "W"),
    ("S", "F"),
    # voiceless stop + liquid / glide
    ("P", "L"), ("P", "R"), ("P", "Y"),
    ("T", "R"), ("T", "W"), ("T", "Y"),
    ("K", "L"), ("K", "R"), ("K", "W"), ("K", "Y"),
    # voiced stop + liquid / glide
    ("B", "L"), ("B", "R"), ("B", "Y"),
    ("D", "R"), ("D", "W"), ("D", "Y"),
    ("G", "L"), ("G", "R"), ("G", "W"),
    # fricative + liquid / glide
    ("F", "L"), ("F", "R"), ("F", "Y"),
    ("TH", "R"), ("TH", "W"),
    ("SH", "R"),
    ("HH", "Y"), ("HH", "W"),
    ("V", "Y"),
    # nasal + glide
    ("M", "Y"), ("N", "Y"),
})

# Three-consonant onsets in English all begin with /s/ + voiceless stop + liquid/glide.
_THREE_CONSONANT_ONSETS = frozenset({
    ("S", "P", "L"), ("S", "P", "R"), ("S", "P", "Y"),
    ("S", "T", "R"), ("S", "T", "Y"),
    ("S", "K", "R"), ("S", "K", "W"), ("S", "K", "Y"), ("S", "K", "L"),
})


def is_legal_onset(cluster: tuple[str, ...]) -> bool:
    """True if ``cluster`` (consonant phonemes, no stress) can begin a syllable.

    An empty cluster is legal (a vowel-initial syllable).
    """
    n = len(cluster)
    if n == 0:
        return True
    if n == 1:
        return cluster[0] not in _ILLEGAL_SINGLE_ONSETS
    if n == 2:
        return cluster in _TWO_CONSONANT_ONSETS
    if n == 3:
        return cluster in _THREE_CONSONANT_ONSETS
    return False
