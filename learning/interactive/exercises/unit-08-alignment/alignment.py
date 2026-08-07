"""Unit 8 exercise -- Needleman-Wunsch alignment over vowel skeletons.

You are generalizing the rhyme kernel to tails of unequal length. The two
functions to complete are marked  # YOUR CODE HERE ; everything else is
working material from earlier units (the blend weights and syllable scoring
you built in Units 6-7), provided so you can focus on the alignment itself.

The shape of the algorithm (see task.md for a hand-worked table):

    dist[i][j] = the cheapest way to align the first i syllables of tail_a
                 with the first j of tail_b
    back[i][j] = which move won ("diag" | "up" | "left"), so the actual
                 pairing can be recovered afterward

Work through task.md first -- it walks a 2x3 example by hand, and the test
file's cases are chosen so each failure tells you which part is wrong.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from rhyme_schemer.features import consonant_similarity, vowel_distance, vowel_similarity
from rhyme_schemer.models import Syllable

# From Unit 7: the nucleus dominates, the coda is texture.
NUCLEUS_WEIGHT = 1.0
CODA_WEIGHT = 0.35

# The cost of aligning a syllable against nothing. It must sit ABOVE a
# near-vowel substitution (else real matches get skipped) and BELOW a far
# one (else a genuinely spare syllable gets force-matched). 0.6 is the
# repo's calibrated value; the tests only assume it is in that band.
GAP_PENALTY = 0.6

# One aligned column: a syllable from each tail, where exactly one side may
# be None -- a gap (a syllable with no counterpart on the other tail).
Alignment = tuple[tuple[Syllable | None, Syllable | None], ...]


def _coda_similarity(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    """Graded [0, 1] similarity between two codas (from Unit 6, complete)."""
    if not a and not b:
        return 1.0
    n = max(len(a), len(b))
    total = 0.0
    for i in range(n):
        if i < len(a) and i < len(b):
            total += consonant_similarity(a[i], b[i])
    return total / n


def _syllable_similarity(a: Syllable, b: Syllable) -> float:
    """Weighted nucleus/coda blend (from Unit 7, complete). Onsets ignored."""
    nucleus = vowel_similarity(a.nucleus, b.nucleus)
    coda = _coda_similarity(a.coda, b.coda)
    return (NUCLEUS_WEIGHT * nucleus + CODA_WEIGHT * coda) / (NUCLEUS_WEIGHT + CODA_WEIGHT)


def align_tails(
    tail_a: tuple[Syllable, ...],
    tail_b: tuple[Syllable, ...],
    *,
    gap_penalty: float = GAP_PENALTY,
) -> Alignment:
    """Align two tails over their nuclei; return the columns of the pairing.

    A substitution (pairing two syllables) costs ``vowel_distance`` between
    their nuclei -- cheap for near-vowels, dear for far ones. A gap costs
    ``gap_penalty``. Codas are NOT consulted here; they come back when the
    chosen alignment is *scored*.
    """
    m, n = len(tail_a), len(tail_b)
    dist = [[0.0] * (n + 1) for _ in range(m + 1)]
    back = [[""] * (n + 1) for _ in range(m + 1)]

    # Edges (provided): aligning a prefix against nothing is pure gaps.
    for i in range(1, m + 1):
        dist[i][0] = i * gap_penalty
        back[i][0] = "up"
    for j in range(1, n + 1):
        dist[0][j] = j * gap_penalty
        back[0][j] = "left"

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # YOUR CODE HERE (the recurrence).
            # Three candidate moves reach cell (i, j):
            #   substitute: dist[i-1][j-1] + vowel_distance between the two
            #               nuclei tail_a[i-1].nucleus / tail_b[j-1].nucleus
            #   delete:     dist[i-1][j]   + gap_penalty   (skip tail_a[i-1])
            #   insert:     dist[i][j-1]   + gap_penalty   (skip tail_b[j-1])
            # Take the cheapest; on a TIE prefer substitute ("diag"), then
            # delete ("up") -- the diagonal preference is what keeps
            # equal-length tails gap-free, matching Unit 6's scoring.
            # Record the winner in dist[i][j] and its move in back[i][j].
            raise NotImplementedError("fill in the recurrence")

    # YOUR CODE HERE (the backtrace).
    # Start at (m, n) and follow back[][] to (0, 0), collecting one column
    # per step: "diag" pairs (tail_a[i-1], tail_b[j-1]); "up" is a gap on
    # b's side (tail_a[i-1], None); "left" is a gap on a's side
    # (None, tail_b[j-1]). You collect them corner-first, so reverse before
    # returning.
    raise NotImplementedError("fill in the backtrace")


def score_alignment(columns: Alignment) -> float:
    """Score an alignment: the average of its per-column scores, in [0, 1].

    A matched column scores ``_syllable_similarity``; a gap column scores
    0.0 -- a syllable with no counterpart is a real rhyme cost, not a free
    pass. (This choice is why hypnotize~eyes is not a rhyme even though its
    final columns match perfectly -- see the test.)
    """
    # YOUR CODE HERE.
    raise NotImplementedError("fill in the scoring")
