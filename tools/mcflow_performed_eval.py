"""Run the scanner's kernel on MCFlow's *performed* pronunciations.

``run_corpus_eval.py`` says how wrong the scanner is on real lyrics. It
cannot say why, because three suspects are tangled together in one number:

- the **segments** are the dictionary's. CMUdict records how a word sounds
  read alone in General American; the performance may be r-less, may merge
  vowels the dictionary keeps apart, may drop a final consonant;
- the **stress** is inferred. ``scan.py`` enumerates where the beat might
  fall and prices the unlikely readings, because the text does not say;
- the **model** -- kernel, seed gate, selection, components -- judges
  whatever it is handed.

MCFlow lets the first two be taken out of the picture. Next to its
``**rhyme`` spine it carries ``**ipa``, a syllable-by-syllable transcription
of what was actually said, and ``**stress``, where the beat actually landed.
So the same kernel can be run four ways -- dictionary or performed segments,
crossed with inferred or performed stress -- against the same gold, with
every threshold left alone. Whatever error survives the cell where both are
performed cannot be blamed on the dictionary or on stress inference. It
belongs to the model.

**One caution about that cell.** The person who transcribed the
pronunciations also marked the rhymes, by ear, from the same recordings.
A transcriber who hears two syllables as rhyming may write their vowels the
same way. So the performed cells are an optimistic bound on what better
pronunciations could buy, not an estimate of it.

How the four cells are built
----------------------------

The scanner is not modified. ``scan.find_matches`` and
``scan.select_matches`` take ``Candidate``s as data, so this tool is one
more candidate factory: it builds the same ``Candidate``/``Reading`` objects
``scan.enumerate_candidates`` builds, from a different source of truth, and
hands them to the unchanged pairing and selection code. In the dictionary /
inferred cell the factory must reproduce ``enumerate_candidates`` exactly,
and the tool checks that on every verse and stops if it does not.

- *Performed segments.* Each ``**ipa`` syllable is mapped to ARPAbet (the
  table below) and the word's phonemes are re-syllabified with the
  project's own ``syllabify``, so medial consonants are divided between
  syllables by the same rule in every cell.
- *Performed stress.* A span may anchor only on a syllable MCFlow marks as
  stressed, and pays no coercion cost and no function-word cost for it:
  the stress was observed, not guessed. ``NEVER_ANCHOR`` is not applied
  either, for the same reason.
- *Performed segments with inferred stress* needs a stress pattern that
  does not come from the performance. It borrows the citation stress of
  the first dictionary variant with the same number of syllables.
- *Dictionary segments with performed stress* keeps the dictionary variants
  whose syllable count matches the performance, so that "syllable 2 was
  stressed" points at a definite syllable.

A token that cannot be built the requested way (an unmappable symbol, a
syllable-count clash, a missing stress mark) falls back to the next plainer
treatment, and the report counts how often that happened.

MCFlow's transcription conventions
----------------------------------

Read off the corpus by tabulating its symbols against CMUdict for
one-syllable, one-variant words. It is a broad, nearly phonemic scheme, and
two of its choices matter when reading the results:

- ``a`` covers both AA and AO ("rock" and "talk" are written alike): the
  corpus transcribes the cot-caught pair as merged. Before /r/ the
  dictionary's AO is written ``o`` + ``ʊ`` + ``r`` instead.
- ``ə`` covers both schwa and the stressed STRUT vowel, which is CMUdict's
  own convention (AH0 and AH1), so stress tells them apart here too.

Consonant choices made for this tool, not by the corpus: the flap ``ɾ`` is
read as D and the glottal stop ``ʔ`` as T, their nearest neighbors in
``features.py``'s consonant inventory. A syllable transcribed with no vowel
at all (syllabic "n" in "didn't", "l" in "little") gets an AH inserted
before its first sonorant, which is how CMUdict writes the same syllables.

The reference rows
------------------

Below the kernel's four cells the report prints a rule with no kernel in
it: two words rhyme if their stressed vowels are *identical*, within the
scanner's two-line window. It is there as a floor. A scoring model that
compares vowels by graded similarity, weighs codas, aligns tails and
selects among overlapping spans ought to beat it, and the comparison says
whether it does. Each version of the rule uses the stress knowledge its
representation has: the dictionary version takes the vowel of each word's
citation rhyme tail and skips ``scan.FUNCTION_WORDS``; the performed
version takes the last syllable MCFlow marks as stressed and skips nothing.

Point this at a local MCFlow clone. Nothing it prints contains lyric text.
"""

from __future__ import annotations

import argparse
import itertools
import multiprocessing
import os
from collections import Counter
from dataclasses import dataclass, replace
from itertools import combinations
from pathlib import Path

from rhyme_schemer.evaluate import (
    Extent,
    Gold,
    PredictedPair,
    class_pairs,
    edge_pairs,
    parse_gold,
    score_pairs,
)
from rhyme_schemer.g2p import pronounce
from rhyme_schemer.models import Pronunciation
from rhyme_schemer.phonetics import Stress
from rhyme_schemer.rhyme import (
    DEFAULT_RHYME_THRESHOLD,
    connected_components,
    rhyme_tail,
)
from rhyme_schemer.scan import (
    DEFAULT_COERCION_COST,
    DEFAULT_MAX_LINE_GAP,
    DEFAULT_MAX_SPAN_WORDS,
    DEFAULT_SEED_THRESHOLD,
    FUNCTION_WORDS,
    NEVER_ANCHOR,
    Candidate,
    Reading,
    VerseScan,
    _can_anchor,
    coerce_performed_stress,
    enumerate_candidates,
    find_matches,
    select_matches,
)
from rhyme_schemer.syllabify import syllabify

from mcflow_to_gold import Section, Word, parse_file, to_gold

# --- MCFlow **ipa -> ARPAbet -------------------------------------------------

# Two-character symbols are tried before one-character ones, so "aI" is the
# PRICE diphthong and never AA followed by a stray IH.
_VOWELS = {
    "aI": "AY", "aʊ": "AW", "oʊ": "OW", "eI": "EY", "ɔI": "OY", "ɜ˞": "ER",
    "ə": "AH", "ʌ": "AH", "I": "IH", "i": "IY", "a": "AA", "æ": "AE",
    "ɜ": "EH", "u": "UW", "ʊ": "UH", "o": "OW", "ɔ": "AO",
}
_CONSONANTS = {
    "tʃ": "CH", "dʒ": "JH",
    "p": "P", "b": "B", "t": "T", "d": "D", "k": "K", "g": "G",
    "f": "F", "v": "V", "θ": "TH", "ð": "DH", "s": "S", "z": "Z",
    "ʃ": "SH", "ʒ": "ZH", "h": "HH", "m": "M", "n": "N", "ŋ": "NG",
    "l": "L", "r": "R", "w": "W", "j": "Y", "y": "Y",
    "ɾ": "D",  # flap: the nearest consonant features.py has a place for
    "ʔ": "T",  # glottal stop: in this corpus almost always a realized /t/
}
_SONORANTS = frozenset({"M", "N", "NG", "L", "R"})


def ipa_syllable_to_phones(ipa: str, stressed: bool) -> list[str] | None:
    """One MCFlow ``**ipa`` syllable as ARPAbet tokens, or None if unmappable.

    The vowel carries the performed stress as its digit (1 or 0). A syllable
    must come out with exactly one vowel: none means a syllabic consonant,
    which gets an AH before its first sonorant; two means a symbol sequence
    this table does not understand, and the caller falls back.
    """
    digit = "1" if stressed else "0"
    phones: list[str] = []
    vowels = 0
    i = 0
    while i < len(ipa):
        for width in (2, 1):
            chunk = ipa[i:i + width]
            if chunk in _VOWELS:
                phones.append(_VOWELS[chunk] + digit)
                vowels += 1
                break
            if chunk in _CONSONANTS:
                phones.append(_CONSONANTS[chunk])
                break
        else:
            return None
        i += width
    if vowels == 1:
        return phones
    if vowels == 0:
        for at, phone in enumerate(phones):
            if phone in _SONORANTS:
                return phones[:at] + ["AH" + digit] + phones[at:]
    return None


def performed_pronunciation(word: Word) -> Pronunciation | None:
    """The word as MCFlow heard it, stress marks included; None if unusable."""
    if not word.ipa or len(word.ipa) != len(word.stresses):
        return None
    phones: list[str] = []
    for ipa, stress in zip(word.ipa, word.stresses):
        syllable = ipa_syllable_to_phones(ipa, stressed=stress == 1)
        if syllable is None:
            return None
        phones.extend(syllable)
    syllables = syllabify(phones)
    if len(syllables) != len(word.ipa):
        return None
    return Pronunciation(syllables=syllables, text=word.text)


# --- Tokens: one word, read one of four ways ----------------------------------

SEGMENTS = ("dictionary", "performed")
STRESS = ("inferred", "performed")
CELLS = tuple(itertools.product(SEGMENTS, STRESS))


@dataclass(frozen=True)
class Token:
    """One word of the verse as one cell of the experiment reads it.

    ``beats`` is the set of syllable indices MCFlow marks as stressed, or
    None when stress is to be inferred the scanner's way. It decides the
    anchor policy for spans that *start* at this token.
    """

    text: str
    variants: tuple[Pronunciation, ...]
    cost: float
    beats: frozenset[int] | None
    fallback: bool = False


def _dictionary_token(word: Word) -> Token:
    guess = pronounce(word.text)
    return Token(word.text, guess.pronunciations, guess.cost, None)


def _with_stress_of(pron: Pronunciation, model: Pronunciation) -> Pronunciation:
    return Pronunciation(
        syllables=tuple(
            replace(syllable, stress=source.stress)
            for syllable, source in zip(pron.syllables, model.syllables)
        ),
        text=pron.text,
    )


def make_token(word: Word, segments: str, stress: str) -> Token:
    """Read ``word`` the way one cell asks, falling back when it cannot be."""
    plain = _dictionary_token(word)
    if (segments, stress) == ("dictionary", "inferred"):
        return plain

    aligned = bool(word.stresses) and len(word.stresses) == len(word.ipa)
    beats = frozenset(i for i, s in enumerate(word.stresses) if s == 1)

    if segments == "dictionary":
        matching = tuple(
            p for p in plain.variants
            if len(p.syllables) == len(word.stresses)
        )
        if not aligned or not matching:
            return replace(plain, fallback=True)
        return Token(word.text, matching, plain.cost, beats)

    performed = performed_pronunciation(word)
    if performed is None:
        # No usable transcription: read the word the dictionary way, with
        # whatever stress treatment this cell would otherwise have had.
        token = make_token(word, "dictionary", stress)
        return replace(token, fallback=True)
    if stress == "performed":
        return Token(word.text, (performed,), 0.0, beats)
    for variant in plain.variants:
        if len(variant.syllables) == len(performed.syllables):
            cited = _with_stress_of(performed, variant)
            return Token(word.text, (cited,), 0.0, None)
    # No dictionary variant of the right length to borrow citation stress
    # from; the performed marks stand in.
    return Token(word.text, (performed,), 0.0, None, fallback=True)


# --- The candidate factory ----------------------------------------------------


def _anchored_readings(span: tuple[Token, ...]):
    """(anchor, readings) pairs for one span, under its first token's policy.

    With ``beats`` None this is ``scan._anchored_readings`` restated over
    tokens: any full-vowel syllable of the first word may anchor, and a
    promoted syllable or a function word pays ``DEFAULT_COERCION_COST``.
    With ``beats`` given, only the observed beats anchor and nothing is
    charged for them.
    """
    first = span[0]
    inferred = first.beats is None
    if inferred and first.text.lower() in NEVER_ANCHOR:
        return []
    if any(not token.variants for token in span):
        return []
    g2p_cost = sum(token.cost for token in span)

    by_anchor: dict[int, list[Reading]] = {}
    for combo in itertools.product(*(token.variants for token in span)):
        whole = Pronunciation.concat(combo)
        for index, syllable in enumerate(combo[0].syllables):
            if inferred:
                if not _can_anchor(syllable):
                    continue
                promoted = (
                    syllable.stress is Stress.UNSTRESSED
                    or first.text.lower() in FUNCTION_WORDS
                )
                cost = DEFAULT_COERCION_COST if promoted else 0.0
            else:
                if index not in first.beats:
                    continue
                cost = 0.0
            by_anchor.setdefault(index, []).append(
                Reading(
                    pronunciation=coerce_performed_stress(whole, index),
                    cost=cost + g2p_cost,
                )
            )
    return sorted(
        (anchor, tuple(readings)) for anchor, readings in by_anchor.items()
    )


def build_candidates(
    lines: list[list[Token]], max_span_words: int
) -> list[Candidate]:
    """``scan.enumerate_candidates``, over tokens instead of a verse string."""
    candidates: list[Candidate] = []
    for line_index, line in enumerate(lines):
        for start in range(len(line)):
            for length in range(1, max_span_words + 1):
                if start + length > len(line):
                    break
                span = tuple(line[start:start + length])
                for anchor, readings in _anchored_readings(span):
                    candidates.append(
                        Candidate(
                            line=line_index,
                            start=start,
                            words=tuple(token.text for token in span),
                            anchor=anchor,
                            readings=readings,
                        )
                    )
    return candidates


def scan_candidates(
    candidates: list[Candidate], threshold: float, seed_threshold: float
) -> VerseScan:
    """Everything ``scan.scan_verse`` does after enumeration, unchanged."""
    matches = find_matches(
        candidates,
        threshold=threshold,
        seed_threshold=seed_threshold,
        max_line_gap=DEFAULT_MAX_LINE_GAP,
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
    return VerseScan(matches=tuple(selected), groups=groups, oov=())


# --- The reference rule: identical stressed vowels ----------------------------


def _stressed_vowel(word: Word, segments: str) -> str | None:
    if segments == "dictionary":
        if word.text.lower() in FUNCTION_WORDS:
            return None
        variants = pronounce(word.text).pronunciations
        if not variants:
            return None
        tail = rhyme_tail(variants[0])
        return tail[0].nucleus if tail else None
    performed = performed_pronunciation(word)
    if performed is None:
        return None
    beats = [i for i, s in enumerate(word.stresses) if s == 1]
    return performed.syllables[beats[-1]].nucleus if beats else None


def same_vowel_pairs(
    section: Section, segments: str, line_final_only: bool
) -> tuple[list[PredictedPair], list[PredictedPair]]:
    """(edges, class pairs) under the identical-stressed-vowel rule."""
    nodes: list[tuple[Word, str]] = []
    for line in section.lines:
        for word in line:
            if line_final_only and word.index != len(line) - 1:
                continue
            vowel = _stressed_vowel(word, segments)
            if vowel is not None:
                nodes.append((word, vowel))

    def predicted(i: int, j: int) -> PredictedPair:
        a, b = nodes[i][0], nodes[j][0]
        return PredictedPair(
            sides=(Extent(a.line, a.index, a.index),
                   Extent(b.line, b.index, b.index)),
            anchors=(a.index, b.index),
            label="",
        )

    edges = [
        (i, j) for i, j in combinations(range(len(nodes)), 2)
        if nodes[i][1] == nodes[j][1]
        and abs(nodes[i][0].line - nodes[j][0].line) <= DEFAULT_MAX_LINE_GAP
        and nodes[i][0].text.lower() != nodes[j][0].text.lower()
    ]
    closure = [
        (i, j)
        for component in connected_components(len(nodes), edges)
        for i, j in combinations(component, 2)
    ]
    return ([predicted(i, j) for i, j in edges],
            [predicted(i, j) for i, j in closure])


# --- Scoring one song ---------------------------------------------------------

_OPTIONS: dict = {}


def _tally(counts: Counter, row: str, level: str,
           predicted: list[PredictedPair], gold: Gold) -> None:
    for ruler in ("anchor", "exact"):
        result = score_pairs(predicted, gold, mode=ruler)
        key = (row, level, ruler)
        counts[key + ("tp",)] += len(result.true_positives)
        counts[key + ("fp",)] += len(result.false_positives)
        counts[key + ("fn",)] += len(result.false_negatives)
        counts[key + ("found",)] += result.gold_matched


def _kernel_row(segments: str, stress: str) -> str:
    return f"kernel: {segments} segments, {stress} stress"


def _rule_row(segments: str, line_final_only: bool) -> str:
    where = "line-final words only" if line_final_only else "any position"
    return f"same vowel: {segments} segments, {where}"


def score_song(path: Path) -> Counter:
    """Every row of the report for one ``.rap`` file, as pooled counts."""
    counts: Counter = Counter()
    for section in parse_file(path):
        if not section.groups():
            continue
        gold = parse_gold(to_gold(section))
        words = [word for line in section.lines for word in line]
        counts["verses"] += 1
        counts["words"] += len(words)
        counts["gold pairs"] += len(gold.pairs())
        counts["words with a usable transcription"] += sum(
            performed_pronunciation(word) is not None for word in words
        )
        last = {i: len(line) - 1 for i, line in enumerate(section.lines)}

        for segments, stress in CELLS:
            row = _kernel_row(segments, stress)
            lines = [
                [make_token(word, segments, stress) for word in line]
                for line in section.lines
            ]
            counts[(row, "fallbacks")] += sum(
                token.fallback for line in lines for token in line
            )
            candidates = build_candidates(lines, _OPTIONS["max_span_words"])
            if (segments, stress) == ("dictionary", "inferred"):
                expected = enumerate_candidates(
                    gold.verse, max_span_words=_OPTIONS["max_span_words"]
                )
                if candidates != expected:
                    raise AssertionError(
                        f"{path.stem} {section.name}: the candidate factory "
                        "does not reproduce scan.enumerate_candidates"
                    )
            scan = scan_candidates(
                candidates, _OPTIONS["threshold"], _OPTIONS["seed_threshold"]
            )
            _tally(counts, row, "edge", edge_pairs(scan), gold)
            _tally(counts, row, "class", class_pairs(scan), gold)

            # Where in the line do the right and wrong edges sit?
            result = score_pairs(edge_pairs(scan), gold, mode="anchor")
            for outcome, pairs in (("tp", result.true_positives),
                                   ("fp", result.false_positives)):
                for pair in pairs:
                    finals = sum(
                        side.end == last[side.line] for side in pair.sides
                    )
                    counts[(row, "position", finals, outcome)] += 1

        for segments in SEGMENTS:
            for line_final_only in (False, True):
                row = _rule_row(segments, line_final_only)
                edges, closure = same_vowel_pairs(
                    section, segments, line_final_only
                )
                _tally(counts, row, "edge", edges, gold)
                _tally(counts, row, "class", closure, gold)
    return counts


def _init(options: dict) -> None:
    _OPTIONS.update(options)


# --- Report -------------------------------------------------------------------


def _prf(counts: Counter, row: str, level: str, ruler: str):
    """Precision over predicted pairs, recall over gold pairs.

    The two count different things, as ``evaluate.Evaluation`` explains:
    several predictions may land on one gold pair, and that is several
    correct claims but still one rhyme found.
    """
    key = (row, level, ruler)
    tp, fp = counts[key + ("tp",)], counts[key + ("fp",)]
    found, missed = counts[key + ("found",)], counts[key + ("fn",)]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = found / (found + missed) if found + missed else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall else 0.0)
    return precision, recall, f1, tp + fp


def report(counts: Counter, options: dict) -> None:
    kernel_rows = [_kernel_row(*cell) for cell in CELLS]
    rule_rows = [
        _rule_row(segments, line_final_only)
        for segments in SEGMENTS
        for line_final_only in (False, True)
    ]
    usable = counts["words with a usable transcription"]
    print("=" * 100)
    print(f"MCFlow: {counts['verses']} verses, {counts['words']} words, "
          f"{counts['gold pairs']} gold pairs")
    print(f"threshold {options['threshold']}, seed threshold "
          f"{options['seed_threshold']}, spans up to "
          f"{options['max_span_words']} words")
    print(f"words with a usable performed transcription: {usable} "
          f"({usable / counts['words']:.1%})")
    for row in kernel_rows[1:]:
        print(f"  fallbacks in '{row}': {counts[(row, 'fallbacks')]}")
    for ruler in ("anchor", "exact"):
        print("=" * 100)
        print(f"{'extent ruler: ' + ruler:<54}{'':>7}{'asserted pairs':>21}"
              f"  |{'pairs implied by classes':>24}")
        print(f"{'':<54}{'edges':>7}{'P':>7}{'R':>7}{'F1':>7}"
              f"  |{'P':>8}{'R':>8}{'F1':>8}")
        print("-" * 100)
        for row in kernel_rows + rule_rows:
            p, r, f1, n = _prf(counts, row, "edge", ruler)
            cp, cr, cf1, _ = _prf(counts, row, "class", ruler)
            print(f"{row:<54}{n:>7}{p:>7.3f}{r:>7.3f}{f1:>7.3f}"
                  f"  |{cp:>8.3f}{cr:>8.3f}{cf1:>8.3f}")
    print("=" * 100)
    print("edge precision by line position (anchor ruler): how many of the "
          "edge's two sides end their line")
    print(f"{'':<54}{'both':>15}{'one':>15}{'neither':>15}")
    for row in kernel_rows:
        cells = []
        for finals in (2, 1, 0):
            tp = counts[(row, "position", finals, "tp")]
            fp = counts[(row, "position", finals, "fp")]
            share = tp / (tp + fp) if tp + fp else 0.0
            cells.append(f"{share:.3f} ({tp + fp})")
        print(f"{row:<54}{cells[0]:>15}{cells[1]:>15}{cells[2]:>15}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score the kernel on MCFlow under dictionary and "
                    "performed segments and stress."
    )
    parser.add_argument("humdrum", type=Path,
                        help="MCFlow Humdrum directory (a local clone)")
    parser.add_argument("--limit", type=int, default=0,
                        help="stop after N songs (0 = all)")
    parser.add_argument("--threshold", type=float,
                        default=DEFAULT_RHYME_THRESHOLD)
    parser.add_argument("--seed-threshold", type=float,
                        default=DEFAULT_SEED_THRESHOLD)
    parser.add_argument("--max-span-words", type=int,
                        default=DEFAULT_MAX_SPAN_WORDS)
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1,
                        help="worker processes (1 = run in this process)")
    args = parser.parse_args()

    options = {
        "threshold": args.threshold,
        "seed_threshold": args.seed_threshold,
        "max_span_words": args.max_span_words,
    }
    files = sorted(args.humdrum.glob("*.rap"))
    if args.limit:
        files = files[:args.limit]

    totals: Counter = Counter()
    if args.jobs > 1 and "fork" in multiprocessing.get_all_start_methods():
        context = multiprocessing.get_context("fork")
        with context.Pool(args.jobs, initializer=_init,
                          initargs=(options,)) as pool:
            for counts in pool.imap_unordered(score_song, files):
                totals.update(counts)
    else:
        _init(options)
        for path in files:
            totals.update(score_song(path))
    report(totals, options)


if __name__ == "__main__":
    main()
