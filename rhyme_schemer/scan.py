"""Scan a verse for the *candidates* internal rhymes could live in.

Everything below this module answers "do these two things rhyme?"; nothing
before it answers "which things should we even ask about?". For line-final
rhyme a human picked the items. Internal rhyme (Unit 11) needs enumeration:
this module turns raw verse text into positioned, scoreable rhyme candidates.

A candidate is a **(word span, anchor)** pair: a run of adjacent words within
one line, plus a claim about *which syllable carries the performed stress*.
The anchor has to be part of the candidate's identity because CMUdict records
citation stress -- how a word sounds alone -- and that provably underdetermines
the rhyme: "up" is AH1 in citation form, so the citation tail of "wake up" is
just "up", hiding the EY rhyme of "wake up" / "state up" while awarding every
"...up" span a perfect score against every other. Which syllable the beat
lands on is a fact about the *performance*, absent from the dictionary, so the
scanner does what this project always does when the text underdetermines the
reading: it enumerates the readings and lets scoring take the best (the same
move as pronunciation variants in Unit 9 and dialects later).

The transport trick that keeps the kernel untouched: a ``Pronunciation`` is
just data, and the kernel trusts whatever stress digits it is handed --
nothing checks *provenance*. ``syllabify`` is the factory that transcribes
CMUdict's citation claims; this module is a second factory that asserts
**performed** stress instead (``coerce_performed_stress``). The founding
invariant "a word and a span are both just Pronunciations" extends to "a
citation reading and a performed reading are both just Pronunciations", and
``rhyme_tail``/``rhyme_score``/``group_rhymes`` flow on unchanged.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, replace
from typing import Sequence

from .features import vowel_similarity
from .g2p import DICTIONARY, OOV, pronounce
from .models import Pronunciation, Syllable
from .phonetics import REDUCED_NUCLEI, Stress
from .rhyme import (
    DEFAULT_RHYME_THRESHOLD,
    align_tails,
    connected_components,
    rhyme_score,
    rhyme_tail,
)
# Longest candidate span, in words. Rhyme units longer than a few words stop
# being heard as one rhyme event; every extra word also multiplies candidates.
# "shake the state up" (4 words) is about the ceiling of the running examples.
DEFAULT_MAX_SPAN_WORDS = 4

# A word is a run of letters and apostrophes ("I'm", "feelin'"); everything
# else -- punctuation, digits, whitespace -- separates words. Case is kept for
# display; CMUdict lookup lowercases on its own.
_WORD_RE = re.compile(r"[a-zA-Z']+")

# How far apart (in lines) two candidates may sit and still be paired. Rhyme
# is perceptual: a listener's echoic memory spans a couple of seconds, so a
# partner four lines away is not *heard* as a rhyme. 2 is the smallest value
# that still reaches ABAB schemes (A's partner is two lines down); chains of
# nearer pairs let ``group_rhymes``'s connected components extend a class
# further than any single pair could reach.
DEFAULT_MAX_LINE_GAP = 2

# Minimum *nucleus* similarity between two anchor syllables for the pair to
# open a rhyme at all (the seed gate's graded clause). Nucleus-only on
# purpose: gating on the blended nucleus+coda column would demand consonant
# agreement exactly where slant rhyme licenses disagreement -- it would score
# lincoln/reason's seed at 0.657 and kill the project's flagship pair, while
# nucleus-only keeps it at 0.887. Vowels are the rhyme; codas are texture.
DEFAULT_SEED_THRESHOLD = 0.8

# Score deducted from a match for each side whose reading *promotes* its
# anchor -- claims a beat on a syllable that doesn't carry one by default:
# either citation-unstressed ("thee", spaghetti's -TI) or any reading of a
# function word (see FUNCTION_WORDS). Enumerating performed-stress readings
# and maxing over them treats all readings as equally likely; they are not,
# and this cost is the thumb on the scale -- a prior made explicit. A strong
# rhyme survives the discount ("get UP!" still rhymes with "cup" at 0.85); a
# marginal one built on an unlikely reading ("day"/"thee" at 0.897) dies.
# Demotions are deliberately free: performers swallow beats constantly
# ("plane, MAN", the "-up" of "setup"), and pricing demotion killed both of
# those flagships when tried.
DEFAULT_COERCION_COST = 0.15

# Closed-class (function) words: prosodically weak by default -- articles,
# pronouns, particles, auxiliaries don't carry the beat unless a performer
# forces it, and CMUdict's citation stress on their monosyllables ("up" AH1,
# "and" AE1 emphatic) is an artifact of words being listed in isolation.
# Anchoring on one is therefore always a coercion claim and pays
# DEFAULT_COERCION_COST; *demoting* one is business as usual and free.
# Deliberately moderate; extend as real lyrics expose gaps.
FUNCTION_WORDS = frozenset({
    "a", "an", "the",
    "and", "but", "or", "nor", "so", "if", "as", "than", "then",
    "of", "to", "in", "on", "at", "by", "for", "with", "from",
    "up", "down", "out", "off", "over",
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those",
    "is", "am", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had",
    "will", "would", "can", "could", "shall", "should", "may", "might",
    "must", "not", "no",
})

# The subset of function words that can never anchor a rhyme at all.
# Function words split prosodically: particles and pronouns are *coercible*
# ("get UP!" takes a beat; "me, myself and I" rhymes "I" and "me" all day) --
# they pay DEFAULT_COERCION_COST and may win. But articles and conjunctions
# are proclitics: they lean on the following word and never carry the beat,
# and CMUdict's emphatic variants for them ("thee", the letter-name "ay" for
# "a", "AE1 N D") describe citation emphasis, not rhyme anchors. Without this
# list every "the" rhymes with "free" and every "a" with "day".
NEVER_ANCHOR = frozenset({"a", "an", "the", "and", "but", "or", "nor"})


def _is_function_word(word: str) -> bool:
    return word.lower() in FUNCTION_WORDS


def tokenize_verse(text: str) -> list[list[str]]:
    """Split verse text into lines of words, preserving line positions.

    Every input line yields an entry -- a blank or word-less line is just an
    empty list -- so indices into the result are *real* line numbers in the
    original text. That fidelity matters downstream: candidates carry (line,
    word) positions, and Unit 12's visualization must map them back onto the
    verse exactly as the user typed it.
    """
    return [_WORD_RE.findall(line) for line in text.splitlines()]


def _is_schwa(syllable: Syllable) -> bool:
    """True if this syllable's nucleus is reduced (schwa) as it stands.

    Reduction is a joint fact about the vowel and its stress: unstressed AH
    is [ə], stressed AH is the full STRUT vowel (see
    ``phonetics.REDUCED_NUCLEI``). Schwa is rhyme-inert in two ways this
    module cares about: it cannot receive a beat (``_can_anchor``), and a
    schwa-against-schwa column carries no rhyme information (every schwa
    "matches" every other -- see ``_informative_length``).
    """
    return (
        syllable.stress is Stress.UNSTRESSED
        and syllable.nucleus in REDUCED_NUCLEI
    )


def _can_anchor(syllable: Syllable) -> bool:
    """True if performed stress could plausibly land on this syllable.

    The phonological gate on anchor enumeration: English stressed syllables
    need a full vowel, so a reduced syllable cannot be coerced into carrying
    the beat. Any *full*-vowel syllable is fair game regardless of its
    citation stress -- the whole point of anchor enumeration is that the
    performer, not the dictionary, decides where the beat falls.
    """
    return not _is_schwa(syllable)


def coerce_performed_stress(pron: Pronunciation, anchor: int) -> Pronunciation:
    """Re-stress ``pron`` to assert: the rhyme anchor is syllable ``anchor``.

    This is the scanner's factory step, and the resolution of the stress
    problem Unit 9 deferred: performed stress becomes explicit *data* rather
    than a kernel feature. The anchor syllable is promoted to PRIMARY, and --
    the load-bearing move -- every syllable *after* it is demoted to
    UNSTRESSED, because ``rhyme_tail`` anchors on the **last** primary: any
    primary surviving after ours ("up" in "wake up") would steal the tail
    right back. Syllables *before* the anchor keep their citation stress: they
    are outside the claimed rhyme domain, ``rhyme_tail`` slices them away
    regardless, and we prefer to assert no more than we know.

    The result flows through the untouched kernel:
    ``rhyme_tail(coerce_performed_stress(wake_up, 0))`` is the full
    ``W EY K . AH P``, not citation stress's lonely ``AH P``.
    """
    syllables = list(pron.syllables)
    for i, syllable in enumerate(syllables):
        if i == anchor and syllable.stress is not Stress.PRIMARY:
            syllables[i] = replace(syllable, stress=Stress.PRIMARY)
        elif i > anchor and syllable.stress is not Stress.UNSTRESSED:
            syllables[i] = replace(syllable, stress=Stress.UNSTRESSED)
    return Pronunciation(syllables=tuple(syllables), text=pron.text)


@dataclass(frozen=True)
class Reading:
    """One performed-stress reading of a candidate, priced.

    ``cost`` is the reading's coercion cost: ``DEFAULT_COERCION_COST`` if the
    anchor had to be *promoted* (a citation-unstressed syllable, or any
    syllable of a function word), else 0. It is computed here, at minting
    time, because it needs facts the finished ``Pronunciation`` no longer
    carries: the anchor's citation stress (coercion overwrites it) and which
    word the anchor belongs to (``Pronunciation.concat`` erases boundaries --
    the one place the "nothing downstream cares" invariant needed help).
    Scoring subtracts the cost from the match score: readings are enumerated
    because the text underdetermines the performance, but they are not
    equally *likely*, and the cost is that prior made explicit.
    """

    pronunciation: Pronunciation
    cost: float


@dataclass(frozen=True)
class Candidate:
    """One place a rhyme could live: a word span read with a chosen anchor.

    - ``line`` / ``start``: the span's position -- line index in the verse,
      index of its first word within that line.
    - ``words``: the span's words. The *first* word always contains the
      anchor: a span whose anchor sat deeper inside would present the kernel
      with exactly the same rhyme tail as the shorter span starting at the
      anchor word, so only that shorter span is enumerated (pre-anchor words
      add nothing to score and would only bloat the highlighted extent).
    - ``anchor``: syllable index *within the first word* where performed
      stress is claimed to fall. Part of the candidate's identity on purpose:
      "spaghetti" anchored at -GHET- and at -TI are different rhyme
      structures, and keeping them distinct is what lets text-overlapping
      rhyme classes coexist (the wake / "wake up" observation).
    - ``readings``: the priced performed-stress ``Reading``s, one per CMUdict
      variant combination that supports this anchor. Their pronunciations are
      the variant list that downstream scoring and grouping consume.
    """

    line: int
    start: int
    words: tuple[str, ...]
    anchor: int
    readings: tuple[Reading, ...]

    @property
    def end(self) -> int:
        """Index (within the line) of the span's last word, inclusive."""
        return self.start + len(self.words) - 1

    def __str__(self) -> str:
        return f"{' '.join(self.words)} @L{self.line}:W{self.start}+{self.anchor}"


def _anchored_readings(
    words: tuple[str, ...],
) -> list[tuple[int, tuple[Reading, ...]]]:
    """All (anchor, readings) pairs for one word span.

    Variant combinations are the cartesian product of the words' variants
    (the ``pronunciations_for_span`` pattern), and anchors are the
    stress-bearing syllables of the *first* word. The two axes interact --
    variants of the first word can differ in syllable count or vowel quality,
    so each anchor index collects readings only from the combinations whose
    first word actually offers an eligible syllable there.

    Pronunciations come from the Unit 13 G2P chain (``g2p.pronounce``), not
    bare dictionary lookup, so "chokin'" and "Coogi" now yield candidates.
    Guessing is priced like coercion: each word's ``Guess.cost`` is summed
    into the span's base cost, so every reading of a span containing a
    letter-to-sound guess pays for it -- a marginal rhyme cannot be built
    on a made-up pronunciation, while a strong one survives the discount
    (the same logic, and the same knob-tuning deferral to Unit 14, as
    ``DEFAULT_COERCION_COST``).

    A span containing any word the whole chain fails to voice ("brrr")
    yields nothing: skip-and-flag, with the flag now meaning "even guessing
    failed". (Word-level reporting belongs to the verse-level wiring.)
    """
    if words[0].lower() in NEVER_ANCHOR:
        return []
    guesses = [pronounce(word) for word in words]
    if any(not guess.pronunciations for guess in guesses):
        return []
    g2p_cost = sum(guess.cost for guess in guesses)

    by_anchor: dict[int, list[Reading]] = {}
    for combo in itertools.product(
        *(guess.pronunciations for guess in guesses)
    ):
        first = combo[0]
        span = Pronunciation.concat(combo)
        for index, syllable in enumerate(first.syllables):
            if not _can_anchor(syllable):
                continue
            promoted = (
                syllable.stress is Stress.UNSTRESSED
                or _is_function_word(words[0])
            )
            coercion = DEFAULT_COERCION_COST if promoted else 0.0
            by_anchor.setdefault(index, []).append(
                Reading(
                    pronunciation=coerce_performed_stress(span, index),
                    cost=coercion + g2p_cost,
                )
            )
    return sorted(
        (anchor, tuple(readings)) for anchor, readings in by_anchor.items()
    )


def enumerate_candidates(
    verse: str, *, max_span_words: int = DEFAULT_MAX_SPAN_WORDS
) -> list[Candidate]:
    """Enumerate every rhyme candidate in a verse.

    The candidate space is deliberately generous -- every span of 1 to
    ``max_span_words`` adjacent words within a line, crossed with every
    eligible anchor syllable in its first word. Overlapping and nested
    candidates ("state", "state up", "the state up") all coexist here;
    deciding which of them constitute *the* rhyme is the selection stage's
    job (ranking by score and length), not enumeration's. Spans do not cross
    line breaks: a line ending is a prosodic boundary, and a rhyme unit
    straddling one stops being heard as a unit.

    Candidates whose span is out-of-vocabulary do not appear. Two anchor
    filters apply, at different grains: the schwa gate (``_can_anchor``)
    drops unstressable *readings* per variant, and ``NEVER_ANCHOR`` drops
    article/conjunction-initial spans outright -- necessary because CMUdict
    lists emphatic variants for function words ("the" is DH AH0 but also
    DH AH1 and DH IY0, "thee") that would otherwise resurrect every article
    as a full-vowel rhyme partner. Coercible function words ("up", "I") do
    anchor; their readings just carry a coercion cost.
    """
    candidates: list[Candidate] = []
    for line_index, line in enumerate(tokenize_verse(verse)):
        for start in range(len(line)):
            for length in range(1, max_span_words + 1):
                if start + length > len(line):
                    break
                words = tuple(line[start : start + length])
                for anchor, readings in _anchored_readings(words):
                    candidates.append(
                        Candidate(
                            line=line_index,
                            start=start,
                            words=words,
                            anchor=anchor,
                            readings=readings,
                        )
                    )
    return candidates


# --- Pairing: which candidates rhyme with which -----------------------------


@dataclass(frozen=True)
class Match:
    """A scored rhyme between two candidates (``a`` strictly before ``b``).

    ``score`` is the best gated ``rhyme_score`` over the two candidates'
    reading pairs, *net of both readings' coercion costs* -- an unlikely
    performed-stress claim has to buy its way in. ``length`` is the syllable
    width (alignment columns) of the winning pair, and
    ``informative_length`` counts only the columns that carry actual rhyme
    information -- a schwa-against-schwa column with no codas ("a"/"the")
    scores a vacuous 1.0 (every schwa matches every schwa) and must not let
    a padded match out-length its own core during selection.
    """

    a: Candidate
    b: Candidate
    score: float
    length: int
    informative_length: int

    def __str__(self) -> str:
        return f"{self.a} ~ {self.b} ({self.score:.3f}, {self.length} syl)"


def _seed_ok(a: Syllable, b: Syllable, seed_threshold: float) -> bool:
    """The seed gate: may this pair of anchor syllables *open* a rhyme?

    Rhyme is judged at the stressed anchor first; trailing material can
    extend a rhyme but never rescue one. ``rhyme_score``'s average cannot
    express that -- a perfect trailing column ("up"/"up") subsidizes a failing
    anchor -- so the gate is applied *before* scoring, per reading pair. Two
    clauses:

    - **No rime riche.** An identical anchor syllable (same onset, nucleus,
      and coda -- "up"/"up", or any word against itself) is repetition, not
      rhyme: English ears demand the onset differ. Identity is still welcome
      *after* the anchor ("plane, man" / "sane, man" -- the shared "man"
      extends a rhyme that plane/sane opened).
    - **Anchor nuclei must be close** (``vowel_similarity`` at
      ``seed_threshold``), nucleus-only -- see ``DEFAULT_SEED_THRESHOLD`` for
      why the coda is deliberately excluded here.
    """
    if a == b:
        return False
    return vowel_similarity(a.nucleus, b.nucleus) >= seed_threshold


def _best_gated_score(
    a: Candidate, b: Candidate, seed_threshold: float
) -> tuple[float, int]:
    """Best (score, winning alignment columns) over gated reading pairs.

    The variant-aware ``max`` of ``best_rhyme_score``, with the seed gate
    applied inside the loop: a reading pair whose anchors cannot open a rhyme
    contributes nothing, no matter how well its trailing syllables agree.
    This is what stops max-over-readings from grabbing degenerate anchors --
    under citation stress "wake up"/"give up" scored a perfect 1.0 via the
    "up"/"up" reading; gated, that reading is simply not in the running.
    """
    best_score, best_columns = 0.0, ()
    for reading_a in a.readings:
        for reading_b in b.readings:
            pron_a = reading_a.pronunciation
            pron_b = reading_b.pronunciation
            tail_a, tail_b = rhyme_tail(pron_a), rhyme_tail(pron_b)
            if not tail_a or not tail_b:
                continue
            if not _seed_ok(tail_a[0], tail_b[0], seed_threshold):
                continue
            score = (
                rhyme_score(pron_a, pron_b) - reading_a.cost - reading_b.cost
            )
            if score > best_score:
                best_score = score
                best_columns = align_tails(tail_a, tail_b)
    return best_score, best_columns


def _informative_length(columns) -> int:
    """Count the alignment columns that carry actual rhyme information.

    Excluded: gaps (no pairing at all) and vacuous schwa columns -- both
    nuclei reduced and both codas empty. Schwa matches schwa perfectly by
    definition, so such a column is free filler: it says nothing about
    whether these two stretches rhyme. (A schwa column *with* codas is
    informative -- lincoln/reason's "-coln"/"-son" agree on a real N.)
    """
    count = 0
    for syllable_a, syllable_b in columns:
        if syllable_a is None or syllable_b is None:
            continue
        if (
            _is_schwa(syllable_a)
            and _is_schwa(syllable_b)
            and not syllable_a.coda
            and not syllable_b.coda
        ):
            continue
        count += 1
    return count


def _are_pairable(a: Candidate, b: Candidate, max_line_gap: int) -> bool:
    """May these two candidates be partners in a rhyme?

    Two conditions, both structural rather than phonetic:

    - **Proximity**: within ``max_line_gap`` lines of each other -- past
      that, a listener no longer binds the two into one percept.
    - **Disjoint extents**: candidates occupying overlapping word *positions*
      ("state" at word 11 inside "the state up" at words 10-12) are competing
      descriptions of the same stretch of performed audio, not partners -- a
      sound cannot rhyme with itself, and any shared syllables would score as
      free identity columns (the "up"/"up" pathology in span form). This is
      strictly positional: candidates may freely share word *types* -- the
      repeated "man" in "plane, man" / "sane, man" occupies two different
      moments in time and extends a real rhyme. And a candidate excluded here
      still joins the scheme through *other* partners: "wake" pairs with
      "take" while the overlapping "wake up" pairs with "state up", which is
      how text-overlapping rhyme classes coexist.
    """
    if abs(a.line - b.line) > max_line_gap:
        return False
    if a.line != b.line:
        return True
    return a.end < b.start or b.end < a.start


def find_matches(
    candidates: Sequence[Candidate],
    *,
    threshold: float = DEFAULT_RHYME_THRESHOLD,
    seed_threshold: float = DEFAULT_SEED_THRESHOLD,
    max_line_gap: int = DEFAULT_MAX_LINE_GAP,
) -> list[Match]:
    """Score every pairable candidate pair; keep those that clear ``threshold``.

    The quadratic heart of the scanner -- deliberately plain: proximity and
    disjointness prune the pair set, the seed gate prunes the reading pairs
    inside each, and the surviving scores are thresholded exactly like
    ``is_rhyme``. The output is still *redundant* by design ("wake up" ~
    "state up" appears alongside "wake up" ~ "the state up" and so on);
    boiling redundancy down to the rhymes a listener would report is the
    selection stage's job, not this one's.
    """
    matches: list[Match] = []
    for i, a in enumerate(candidates):
        for b in candidates[i + 1 :]:
            if not _are_pairable(a, b, max_line_gap):
                continue
            score, columns = _best_gated_score(a, b, seed_threshold)
            if score >= threshold:
                matches.append(
                    Match(
                        a=a,
                        b=b,
                        score=score,
                        length=len(columns),
                        informative_length=_informative_length(columns),
                    )
                )
    return matches


# --- Selection: from redundant matches to the rhymes a listener reports -----


def _extents_overlap(c: Candidate, d: Candidate) -> bool:
    """True if the two candidates occupy overlapping word positions."""
    return c.line == d.line and not (c.end < d.start or d.end < c.start)


def _same_event(x: Match, y: Match) -> bool:
    """True if two matches are descriptions of the same rhyme event.

    Two matches describe one event when their sides overlap pairwise -- both
    left sides share text, and both right sides share text ("wake ~ state"
    inside "wake up ~ state up"). Matches touching at only *one* side are
    different events: "wake ~ take" and "wake up ~ state up" share the wake
    material, but they connect it to different partners -- that is the
    overlapping-rhyme-structures case, and both must survive selection.
    """
    return _extents_overlap(x.a, y.a) and _extents_overlap(x.b, y.b)


def select_matches(matches: Sequence[Match]) -> list[Match]:
    """Boil redundant matches down to one description per rhyme event.

    Greedy best-first: sort by score (then length, then nearness) and accept
    a match unless an already-accepted one describes the same event. Score
    comes first -- a deliberate inversion of Hirjee & Brown's longest-first
    ranking, and the reason is the shape of our scores. Theirs are *sums* of
    per-syllable log-odds, where longer matches accumulate evidence; ours are
    *averages*, which makes the average itself the arbiter of extension: a
    trailing column joins a rhyme only if it pulls the average up. "wake up ~
    state up" (0.964) beats its core "wake ~ state" (0.928) because up/up
    earns its seat; "cake and ~ state up" (0.83) loses to its core "cake ~
    state" (0.88) because and/up is dead weight. The same arithmetic
    auto-splits chains: a mega-span gluing two rhyme events ("wake up take a"
    ~ "cake and shake the") always averages below its best internal hit, so
    the hits win and the glue never surfaces. One mechanism, three jobs.

    Ties break on *informative* length, descending (a mosaic "plane man ~
    sane man" at 1.0 subsumes its seed "plane ~ sane" at 1.0 -- man/man is a
    full-vowel column that earns credit), then *total* length ascending (the
    tightest description wins: "take ~ shake" beats "take a ~ shake the",
    whose extra column is vacuous schwa filler), then nearer-first. Hirjee &
    Brown's longest/nearest preferences survive only as these tiebreakers.
    """
    ordered = sorted(
        matches,
        key=lambda m: (
            -m.score,
            -m.informative_length,
            m.length,
            m.b.line - m.a.line,
            m.b.start,
            m.a.line,
            m.a.start,
        ),
    )
    accepted: list[Match] = []
    for match in ordered:
        if not any(_same_event(match, kept) for kept in accepted):
            accepted.append(match)
    return accepted


# --- Chaining: fuse per-beat matches into the compounds the ear hears --------


@dataclass(frozen=True)
class Compound:
    """A multi-beat rhyme read as one unit: a chain of abutting matches.

    The scanner reports one match per *beat* -- "PALMS-are-SWEATY ~
    ARMS-are-HEAVY" arrives as two matches (``palms are ~ arms are`` and
    ``sweaty ~ heavy``) because ``select_matches`` scores each beat on its own
    and the internal hits outbid the glued span. But the ear hears one
    4-syllable rhyme, so chaining fuses beats whose text extents abut on both
    sides back into a single object.

    A compound still describes *one pairwise rhyme*: its member matches all
    share the same two sides. ``a_span`` is the left run of candidates (in
    verse order), ``b_span`` the right run; a lone match that never chained is
    a one-member compound, so the renderer sees a uniform stream whether a
    compound survived selection whole or in pieces.
    """

    matches: tuple[Match, ...]

    @property
    def a_span(self) -> tuple[Candidate, ...]:
        return tuple(m.a for m in self.matches)

    @property
    def b_span(self) -> tuple[Candidate, ...]:
        return tuple(m.b for m in self.matches)

    def __str__(self) -> str:
        left = " ".join(w for m in self.matches for w in m.a.words)
        right = " ".join(w for m in self.matches for w in m.b.words)
        return f"[{left}] ~ [{right}] ({len(self.matches)} beat)"


def _abuts(x: Match, y: Match) -> bool:
    """True if match ``y`` continues match ``x`` -- the immediately next beat
    on *both* sides, contiguously and in the same order.

    The chaining relation, and the precise form of the learner's "sandwich"
    intuition: ``x``'s left extent ends exactly where ``y``'s begins, and the
    same holds on the right. Both sides stepping forward together is what
    "later in both sequences" (co-linear chaining) looks like in the word
    stream; requiring *immediate* succession (``end + 1 == start``) rather than
    mere order is the rhyme-specific tightening -- the ear fuses contiguous
    beats, not ones with a word between them. Same-line on each side falls out
    of comparing ``line`` before position; a pair going forward on one side and
    back on the other fails outright (that is chiasmus, not a compound).

    We deliberately do *not* tolerate a gap between beats. A bounded gap was
    tried and rejected: on the Lose Yourself verse it fused unrelated beats
    ("palms sweaty ~ calm ready", from two different rhyme classes) five times
    for every real compound, because a blind gap cannot tell a throwaway
    ("so") from a word claimed by another beat ("palms [are] sweaty", where
    "are" belongs to the palms-are~arms-are beat). The one pattern it would
    have recovered -- *differing* filler on the two sides -- is not clearly a
    real perceived rhyme. Contiguous filler that is parallel (identical on both
    sides) needs no help here: span enumeration already absorbs it into a beat
    (it scores as an identity column) before chaining runs.
    """
    return (
        x.a.line == y.a.line
        and x.a.end + 1 == y.a.start
        and x.b.line == y.b.line
        and x.b.end + 1 == y.b.start
    )


def chain_matches(matches: Sequence[Match]) -> list[Compound]:
    """Fuse abutting matches into ``Compound``s (co-linear chaining post-pass).

    Every match becomes a node; an ``_abuts`` relation between two matches is
    an edge; each **connected component** (the same ``rhyme.connected_components``
    engine behind grouping) is one compound, its members ordered by left
    position. A match that abuts nothing is its own singleton compound, so the
    output partitions *all* the input matches -- nothing is dropped, and the
    renderer can walk compounds instead of raw matches uniformly.

    This is a pure post-pass over already-selected matches: no scanner, kernel,
    or grouping change, and each beat keeps whatever rhyme class it landed in
    (a compound deliberately *spans* classes -- that is the whole point of
    representing it separately from the grouping). Chaining assumes selection
    has already deduplicated per-beat, so the abut relation is effectively a
    linked list and components are simple chains; if competing overlapping
    chains ever arise, the principled upgrade is a maximum-weight-chain DP,
    the same shape as everything else in the alignment family.
    """
    ordered = sorted(matches, key=lambda m: (m.a.line, m.a.start))
    edges = [
        (i, j)
        for i in range(len(ordered))
        for j in range(len(ordered))
        if i != j and _abuts(ordered[i], ordered[j])
    ]
    components = connected_components(len(ordered), edges)
    return [
        Compound(
            matches=tuple(
                sorted(
                    (ordered[i] for i in component),
                    key=lambda m: (m.a.line, m.a.start),
                )
            )
        )
        for component in components
    ]


# --- The verse-level entry point ---------------------------------------------


@dataclass(frozen=True)
class VerseScan:
    """Everything the scanner found in one verse.

    - ``matches``: the selected matches -- the pairwise evidence, kept
      because each carries the score and syllable width behind its edge
      (Unit 12's renderer and Unit 14's evaluation both want the receipts).
    - ``groups``: the rhyme classes -- connected components over the match
      graph -- each a tuple of ``Candidate``s in verse order, classes ordered
      by first member. Classes may overlap in *text* while being disjoint in
      candidates ("wake" in the EY class, "wake up" in the "-ake up" pair).
    - ``oov``: words the whole G2P chain failed to voice ("brrr"), in
      first-appearance order. The "flag" half of skip-and-flag, surfaced at
      verse level: spans containing these words silently produced no
      candidates, and a renderer should say "unknown word" rather than let
      it read as "doesn't rhyme". Since Unit 13 this is much rarer than
      "not in CMUdict" -- most dictionary misses become guesses instead.
    - ``guessed``: (word, source) pairs for words whose pronunciation came
      from the G2P chain rather than the dictionary, first-appearance
      order. These *did* participate in scanning, and honesty requires
      saying so: a rhyme built on a letter-to-sound guess is a claim about
      a pronunciation no dictionary attests, and the renderer should mark
      it as such rather than let it read as dictionary fact.
    """

    matches: tuple[Match, ...]
    groups: tuple[tuple[Candidate, ...], ...]
    oov: tuple[str, ...]
    guessed: tuple[tuple[str, str], ...] = ()


def _word_provenance(
    lines: list[list[str]],
) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    """(chain-failed words, (word, source) guesses), first-appearance order."""
    seen: set[str] = set()
    oov: list[str] = []
    guessed: list[tuple[str, str]] = []
    for line in lines:
        for word in line:
            key = word.lower()
            if key in seen:
                continue
            seen.add(key)
            source = pronounce(word).source
            if source == OOV:
                oov.append(word)
            elif source != DICTIONARY:
                guessed.append((word, source))
    return tuple(oov), tuple(guessed)


def scan_verse(
    verse: str,
    *,
    max_span_words: int = DEFAULT_MAX_SPAN_WORDS,
    threshold: float = DEFAULT_RHYME_THRESHOLD,
    seed_threshold: float = DEFAULT_SEED_THRESHOLD,
    max_line_gap: int = DEFAULT_MAX_LINE_GAP,
) -> VerseScan:
    """Scan a verse end to end: text in, rhyme scheme out.

    The whole Unit 11 pipeline in one call: enumerate (span, anchor)
    candidates, pair and score them through the gated kernel, select one
    description per rhyme event, then read the scheme off the match graph as
    connected components (``rhyme.connected_components`` -- the same engine
    behind ``group_rhymes``).

    Note what the edges are: the **selected matches themselves**, not
    recomputed ``best_is_rhyme`` calls. The scanner's edge test is stricter
    than the bare kernel's -- seed-gated, coercion-priced, event-deduplicated
    -- and rescoring pairs with the plain kernel here would readmit
    everything those layers rejected (every "...up"/"...up" pair, for a
    start). The grouping *machinery* is Unit 10's, unchanged; the edge
    *judgment* is Unit 11's, and keeping them separable is exactly why
    ``connected_components`` takes edges as data.

    Only candidates that appear in a selected match become nodes: a
    candidate was never an observation, just an enumerated possibility, so
    an unmatched one is not a "singleton rhyme class" -- but a *word* no
    part of the G2P chain could voice is real information (``oov``), and so
    is a pronunciation the chain guessed rather than looked up
    (``guessed``).
    """
    candidates = enumerate_candidates(verse, max_span_words=max_span_words)
    matches = find_matches(
        candidates,
        threshold=threshold,
        seed_threshold=seed_threshold,
        max_line_gap=max_line_gap,
    )
    selected = select_matches(matches)

    node_set = {c for match in selected for c in (match.a, match.b)}
    nodes = sorted(node_set, key=lambda c: (c.line, c.start, c.end, c.anchor))
    index = {candidate: i for i, candidate in enumerate(nodes)}
    edges = [(index[match.a], index[match.b]) for match in selected]
    groups = tuple(
        tuple(nodes[i] for i in component)
        for component in connected_components(len(nodes), edges)
    )
    oov, guessed = _word_provenance(tokenize_verse(verse))
    return VerseScan(
        matches=tuple(selected),
        groups=groups,
        oov=oov,
        guessed=guessed,
    )
