"""rhyme-schemer: detect and group rhymes in hip-hop lyrics."""

from .models import Pronunciation, Syllable
from .phonetics import Stress
from .rhyme import (
    align_tails,
    best_is_rhyme,
    best_rhyme_score,
    connected_components,
    group_rhymes,
    is_rhyme,
    rhyme_score,
    rhyme_tail,
)
from .scan import (
    Candidate,
    Compound,
    Match,
    Reading,
    VerseScan,
    chain_matches,
    coerce_performed_stress,
    enumerate_candidates,
    find_matches,
    scan_verse,
    select_matches,
    tokenize_verse,
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
    "connected_components",
    "tokenize_verse",
    "coerce_performed_stress",
    "Reading",
    "Candidate",
    "Match",
    "Compound",
    "VerseScan",
    "enumerate_candidates",
    "find_matches",
    "select_matches",
    "chain_matches",
    "scan_verse",
]
