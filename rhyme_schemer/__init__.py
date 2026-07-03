"""rhyme-schemer: detect and group rhymes in hip-hop lyrics."""

from .models import Pronunciation, Syllable
from .phonetics import Stress
from .rhyme import (
    align_tails,
    best_is_rhyme,
    best_rhyme_score,
    group_rhymes,
    is_rhyme,
    rhyme_score,
    rhyme_tail,
)
from .syllabify import (
    pronunciation_for,
    pronunciation_for_span,
    pronunciations_for,
    pronunciations_for_span,
    syllabify,
)

__all__ = [
    "Pronunciation",
    "Syllable",
    "Stress",
    "pronunciation_for",
    "pronunciation_for_span",
    "pronunciations_for",
    "pronunciations_for_span",
    "syllabify",
    "rhyme_tail",
    "align_tails",
    "rhyme_score",
    "is_rhyme",
    "best_rhyme_score",
    "best_is_rhyme",
    "group_rhymes",
]
