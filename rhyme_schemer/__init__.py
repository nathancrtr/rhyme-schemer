"""rhyme-schemer: detect and group rhymes in hip-hop lyrics."""

from .models import Pronunciation, Syllable
from .phonetics import Stress
from .rhyme import align_tails, is_rhyme, rhyme_score, rhyme_tail
from .syllabify import pronunciation_for, syllabify

__all__ = [
    "Pronunciation",
    "Syllable",
    "Stress",
    "pronunciation_for",
    "syllabify",
    "rhyme_tail",
    "align_tails",
    "rhyme_score",
    "is_rhyme",
]
