"""The rhyme kernel.

Rhyme is anchored at the last *stressed* syllable, not merely the final one:
"lessen" and "strengthen" share a final syllable but do not rhyme. So the
rhyme-bearing tail runs from the last PRIMARY-stressed syllable through the end
of the word, and everything the kernel scores operates on that tail.
"""

from __future__ import annotations

from typing import Sequence

from .features import consonant_similarity, vowel_distance, vowel_similarity
from .models import Pronunciation, Syllable
from .phonetics import Stress

# Rhyme is vowel-led: the nucleus dominates, the coda is a smaller texture cue,
# and the onset is ignored entirely (that's what makes "cat"/"hat" rhyme). These
# are the graded-kernel's knobs; Unit 7 tunes them, but they already have to lean
# vowel-heavy for perfect rhyme to calibrate to 1.0 the way the ear expects.
DEFAULT_NUCLEUS_WEIGHT = 1.0
DEFAULT_CODA_WEIGHT = 0.35

# Cost of aligning a syllable against nothing (an extra syllable on one side)
# when the two rhyme tails differ in length. In vowel_distance units, it has to
# sit *above* a near-vowel substitution (~0.1-0.2, so genuine matches are kept)
# but *below* a far one (~0.6-0.7, so a truly spare syllable is skipped rather
# than force-matched). See interactive/widgets/nw-alignment.html to feel it.
DEFAULT_GAP_PENALTY = 0.6

# The cut that turns the graded score into a yes/no. Chosen from evidence, not
# taste: perfect rhymes score 1.0, clear slant rhymes (e.g. "Lincoln"/"reason")
# land around 0.83-0.87, and non-rhymes ("Lincoln"/"orange") around 0.6 -- so
# 0.75 falls in the empty band between the two clusters with margin on each side.
# It's the looseness knob: lower to admit more distant slant rhymes.
DEFAULT_RHYME_THRESHOLD = 0.75


def rhyme_tail(pron: Pronunciation) -> tuple[Syllable, ...]:
    """Return the rhyme-bearing tail of ``pron``.

    The tail is the run of syllables from the last PRIMARY-stressed syllable to
    the end of the pronunciation. This is the material every rhyme comparison
    downstream operates on (its ``vowel_skeleton`` is the spine the kernel
    scores).

    Fallbacks when there is no PRIMARY stress:
      1. from the last SECONDARY-stressed syllable to the end, else
      2. the final syllable alone.

    An empty pronunciation yields an empty tail.

        >>> # reason -> [R IY1, Z AH0 N], primary on syllable 0
        >>> # rhyme_tail(pronunciation_for("reason"))  ->  both syllables
        >>> # around -> [AH0, R AW1 N D], primary on syllable 1
        >>> # rhyme_tail(pronunciation_for("around"))  ->  just (R AW1 N D,)
    """
    syllables = pron.syllables
    if not syllables:
        return ()

    # Scan once, remembering the *last* index at each stress level. We can't
    # break on the first primary: a multi-word span may carry several, and the
    # last one anchors the tail ("...GEM . uh . NI!" rhymes on the final stress).
    last_primary: int | None = None
    last_secondary: int | None = None
    for i, syllable in enumerate(syllables):
        if syllable.stress == Stress.PRIMARY:
            last_primary = i
        elif syllable.stress == Stress.SECONDARY:
            last_secondary = i

    # Fallback cascade: primary, else secondary, else the final syllable alone.
    if last_primary is not None:
        start = last_primary
    elif last_secondary is not None:
        start = last_secondary
    else:
        start = len(syllables) - 1

    return syllables[start:]


def _coda_similarity(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    """Graded similarity in [0, 1] between two codas (consonant tuples).

    Two empty codas agree perfectly (nothing vs. nothing). Otherwise we compare
    position-by-position over the *longer* coda; a consonant present in only one
    coda is an unmatched sound and scores 0. This is deliberately crude -- true
    consonant alignment is Unit 8's job -- but it's enough while tails are equal
    length, and it correctly costs a missing/extra coda consonant.
    """
    if not a and not b:
        return 1.0
    n = max(len(a), len(b))
    total = 0.0
    for i in range(n):
        if i < len(a) and i < len(b):
            total += consonant_similarity(a[i], b[i])
        # else: a consonant in only one coda is unmatched -> contributes 0.
    return total / n


def _syllable_similarity(
    a: Syllable, b: Syllable, nucleus_weight: float, coda_weight: float
) -> float:
    """Weighted blend of nucleus (vowel) and coda (consonant) similarity.

    The onset is not consulted at all -- rhyme ignores what comes before the
    vowel. Dividing by the total weight keeps the result in [0, 1] and makes an
    identical syllable score exactly 1.0 for any weights.
    """
    nucleus = vowel_similarity(a.nucleus, b.nucleus)
    coda = _coda_similarity(a.coda, b.coda)
    return (nucleus_weight * nucleus + coda_weight * coda) / (
        nucleus_weight + coda_weight
    )


Alignment = tuple[tuple[Syllable | None, Syllable | None], ...]


def align_tails(
    tail_a: tuple[Syllable, ...],
    tail_b: tuple[Syllable, ...],
    *,
    gap_penalty: float = DEFAULT_GAP_PENALTY,
) -> Alignment:
    """Needleman-Wunsch alignment of two rhyme tails over their vowel skeletons.

    Returns the alignment as an ordered tuple of columns; each column is a pair
    ``(syllable_a, syllable_b)`` where exactly one side may be ``None`` -- a gap,
    i.e. a syllable on one tail with no counterpart on the other.

    We align on the *nuclei* only (the rhyme spine): a substitution costs
    ``vowel_distance`` between the two nuclei -- cheap for near-vowels, dear for
    far ones -- and a gap costs ``gap_penalty``. Codas are not consulted here;
    they fold back in when the chosen alignment is *scored*. The classic DP:
    ``D[i][j]`` is the least cost to align the first ``i`` nuclei of ``tail_a``
    with the first ``j`` of ``tail_b``, and ``back`` records the winning move so
    we can retrace the actual pairing (needed for coda scoring and, later,
    visualization). See interactive/widgets/nw-alignment.html.
    """
    m, n = len(tail_a), len(tail_b)
    dist = [[0.0] * (n + 1) for _ in range(m + 1)]
    back = [[""] * (n + 1) for _ in range(m + 1)]

    # Edges: aligning a prefix against nothing is a run of pure gaps.
    for i in range(1, m + 1):
        dist[i][0] = i * gap_penalty
        back[i][0] = "up"
    for j in range(1, n + 1):
        dist[0][j] = j * gap_penalty
        back[0][j] = "left"

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            substitute = dist[i - 1][j - 1] + vowel_distance(
                tail_a[i - 1].nucleus, tail_b[j - 1].nucleus
            )
            delete = dist[i - 1][j] + gap_penalty  # skip tail_a[i-1]
            insert = dist[i][j - 1] + gap_penalty  # skip tail_b[j-1]
            # Prefer substitution on ties (the diagonal), then delete: keeps
            # equal-length tails on the no-gap diagonal, matching Unit 6.
            best, move = substitute, "diag"
            if delete < best - 1e-12:
                best, move = delete, "up"
            if insert < best - 1e-12:
                best, move = insert, "left"
            dist[i][j] = best
            back[i][j] = move

    # Backtrace from the corner to the origin, collecting columns in reverse.
    columns: list[tuple[Syllable | None, Syllable | None]] = []
    i, j = m, n
    while i > 0 or j > 0:
        move = back[i][j]
        if move == "diag":
            columns.append((tail_a[i - 1], tail_b[j - 1]))
            i, j = i - 1, j - 1
        elif move == "up":
            columns.append((tail_a[i - 1], None))
            i -= 1
        else:
            columns.append((None, tail_b[j - 1]))
            j -= 1
    columns.reverse()
    return tuple(columns)


def rhyme_score(
    a: Pronunciation,
    b: Pronunciation,
    *,
    nucleus_weight: float = DEFAULT_NUCLEUS_WEIGHT,
    coda_weight: float = DEFAULT_CODA_WEIGHT,
    gap_penalty: float = DEFAULT_GAP_PENALTY,
) -> float:
    """Graded rhyme similarity in [0, 1] between two pronunciations.

    Scoring runs over each pronunciation's ``rhyme_tail`` (from the last stress
    to the end). The tails are aligned with ``align_tails`` (so unequal lengths
    -- multisyllabic rhyme -- are handled), then each aligned column is scored:
    a matched pair by its blended nucleus/coda similarity, a gap by 0.0 (a
    syllable with no counterpart is a real rhyme cost). The column scores are
    averaged.

    Identical tails score 1.0 -- perfect rhyme is just the top of the continuum
    -- and near-vowels earn graded, near-full credit, which is what turns this
    into a slant-rhyme detector rather than an equality check. Equal-length
    tails stay on the alignment's no-gap diagonal, recovering the simpler
    position-by-position scoring exactly.
    """
    tail_a = rhyme_tail(a)
    tail_b = rhyme_tail(b)
    if not tail_a or not tail_b:
        return 0.0

    columns = align_tails(tail_a, tail_b, gap_penalty=gap_penalty)
    per_column = [
        _syllable_similarity(sa, sb, nucleus_weight, coda_weight)
        if sa is not None and sb is not None
        else 0.0
        for sa, sb in columns
    ]
    return sum(per_column) / len(per_column)


def is_rhyme(
    a: Pronunciation,
    b: Pronunciation,
    *,
    threshold: float = DEFAULT_RHYME_THRESHOLD,
    nucleus_weight: float = DEFAULT_NUCLEUS_WEIGHT,
    coda_weight: float = DEFAULT_CODA_WEIGHT,
    gap_penalty: float = DEFAULT_GAP_PENALTY,
) -> bool:
    """Yes/no rhyme decision: does the graded score clear the threshold?

    This is where "rhyme" becomes binary. Perfect rhyme is the ``threshold=1.0``
    special case; the default admits slant rhyme. The threshold is the looseness
    knob, kept separate from the weights (which shape the *ranking*) on purpose:
    lowering it lets in more distant rhymes without changing their order.
    """
    return rhyme_score(
        a,
        b,
        nucleus_weight=nucleus_weight,
        coda_weight=coda_weight,
        gap_penalty=gap_penalty,
    ) >= threshold


def best_rhyme_score(
    a_variants: Sequence[Pronunciation],
    b_variants: Sequence[Pronunciation],
    *,
    nucleus_weight: float = DEFAULT_NUCLEUS_WEIGHT,
    coda_weight: float = DEFAULT_CODA_WEIGHT,
    gap_penalty: float = DEFAULT_GAP_PENALTY,
) -> float:
    """The best ``rhyme_score`` over all pronunciation-variant combinations.

    A word (or span) rarely has one pronunciation; a rapper picks whichever
    *variant* lands the rhyme (coercion). So the honest score for two candidates
    is the maximum over every pairing of their variants -- not a guess at variant
    zero. "route" (R UW1 T | R AW1 T) rhymes with "shout" only under its second
    reading, and this ``max`` is what finds it.

    Crucially the kernel is untouched: this is a thin ``max`` *around*
    ``rhyme_score``. Empty input (an out-of-vocabulary word or span, whose
    variant list is empty) yields ``0.0``, matching ``rhyme_score``'s treatment
    of empty tails. Pair with ``pronunciations_for`` / ``pronunciations_for_span``
    to get the variant lists.
    """
    scores = [
        rhyme_score(
            a,
            b,
            nucleus_weight=nucleus_weight,
            coda_weight=coda_weight,
            gap_penalty=gap_penalty,
        )
        for a in a_variants
        for b in b_variants
    ]
    return max(scores) if scores else 0.0


def best_is_rhyme(
    a_variants: Sequence[Pronunciation],
    b_variants: Sequence[Pronunciation],
    *,
    threshold: float = DEFAULT_RHYME_THRESHOLD,
    nucleus_weight: float = DEFAULT_NUCLEUS_WEIGHT,
    coda_weight: float = DEFAULT_CODA_WEIGHT,
    gap_penalty: float = DEFAULT_GAP_PENALTY,
) -> bool:
    """Yes/no rhyme decision over variants: does the *best* variant clear it?

    The variant-aware sibling of ``is_rhyme``: two words rhyme if *some* pair of
    their pronunciations does. Thresholds ``best_rhyme_score``.
    """
    return best_rhyme_score(
        a_variants,
        b_variants,
        nucleus_weight=nucleus_weight,
        coda_weight=coda_weight,
        gap_penalty=gap_penalty,
    ) >= threshold
