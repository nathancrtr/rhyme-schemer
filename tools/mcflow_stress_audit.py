"""Measure how far *performed* stress departs from CMUdict citation stress.

This is the empirical test of the scanner's central bet. ``scan.py`` argues
that CMUdict records how a word sounds *alone*, that rap re-places the beat,
and that the gap is big enough to be worth enumerating and pricing readings
over. That has been an argument from examples ("wake up") since Unit 11.

MCFlow's ``**stress`` spine settles it with data: Condit-Schultz transcribed
where the beat actually landed, syllable by syllable, across 124 songs. Line
that up against ``syllabify``'s citation stress and the disagreement rate is
just a number.

Two counts matter separately, because ``scan.py`` prices them differently:

- **promotions** -- performed stress on a syllable CMUdict leaves unstressed.
  These are what ``DEFAULT_COERCION_COST`` charges for.
- **demotions** -- a citation-stressed syllable performed without stress.
  These the scanner lets through free, on the theory that performers swallow
  beats constantly. The demotion rate says whether "constantly" is fair.

Also reported: how often ``scan.FUNCTION_WORDS`` are performed *stressed*,
which is the assumption behind pricing them, and how often ``NEVER_ANCHOR``
words are -- because if those carry real beats, that hard veto is wrong.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pronouncing

from rhyme_schemer.phonetics import Stress
from rhyme_schemer.scan import FUNCTION_WORDS, NEVER_ANCHOR
from rhyme_schemer.syllabify import syllabify

from mcflow_to_gold import parse_file


def citation_stresses(word: str) -> list[int] | None:
    """CMUdict's citation stress per syllable: 1 for primary, else 0.

    Secondary stress counts as unstressed here to match MCFlow's binary
    spine -- the corpus records "did the beat land here", not a three-way
    prominence judgment.
    """
    variants = pronouncing.phones_for_word(word.lower())
    if not variants:
        return None
    syllables = syllabify(variants[0].split())
    if not syllables:
        return None
    return [1 if s.stress == Stress.PRIMARY else 0 for s in syllables]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("humdrum", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    files = sorted(args.humdrum.glob("*.rap"))
    if args.limit:
        files = files[:args.limit]

    counts = Counter()
    function_word_beats = Counter()
    never_anchor_beats = Counter()
    promoted_examples = Counter()

    for path in files:
        for section in parse_file(path):
            for line in section.lines:
                for word in line:
                    counts["words_seen"] += 1
                    citation = citation_stresses(word.text)
                    if citation is None:
                        counts["oov"] += 1
                        continue
                    performed = word.stresses
                    if len(performed) != len(citation):
                        # Syllable-count disagreement is its own finding
                        # (elision, or the transcriber hearing a different
                        # number of beats) but can't be compared position-
                        # wise, so it is counted and set aside.
                        counts["syllable_count_mismatch"] += 1
                        continue

                    counts["words_compared"] += 1
                    counts["syllables_compared"] += len(performed)
                    identical = True
                    for perf, cite in zip(performed, citation):
                        if perf == cite:
                            continue
                        identical = False
                        if perf == 1 and cite == 0:
                            counts["promotions"] += 1
                        elif perf == 0 and cite == 1:
                            counts["demotions"] += 1
                    if identical:
                        counts["words_identical"] += 1
                    else:
                        counts["words_differing"] += 1
                        if len(performed) == 1 and performed[0] == 1 \
                                and citation[0] == 0:
                            promoted_examples[word.text.lower()] += 1

                    key = word.text.lower()
                    if key in FUNCTION_WORDS:
                        function_word_beats["total"] += 1
                        if any(performed):
                            function_word_beats["stressed"] += 1
                    if key in NEVER_ANCHOR:
                        never_anchor_beats["total"] += 1
                        if any(performed):
                            never_anchor_beats["stressed"] += 1

    def pct(n: int, d: int) -> str:
        return f"{100.0 * n / d:.1f}%" if d else "n/a"

    print("=" * 62)
    print("PERFORMED vs CITATION STRESS  (MCFlow **stress vs CMUdict)")
    print("=" * 62)
    print(f"words seen              {counts['words_seen']:>8}")
    print(f"  out of vocabulary     {counts['oov']:>8}  "
          f"{pct(counts['oov'], counts['words_seen'])}")
    print(f"  syllable-count clash  {counts['syllable_count_mismatch']:>8}  "
          f"{pct(counts['syllable_count_mismatch'], counts['words_seen'])}")
    print(f"  compared              {counts['words_compared']:>8}")
    print()
    print(f"words matching citation {counts['words_identical']:>8}  "
          f"{pct(counts['words_identical'], counts['words_compared'])}")
    print(f"words differing         {counts['words_differing']:>8}  "
          f"{pct(counts['words_differing'], counts['words_compared'])}")
    print()
    print(f"syllables compared      {counts['syllables_compared']:>8}")
    print(f"  promotions (0 -> 1)   {counts['promotions']:>8}  "
          f"{pct(counts['promotions'], counts['syllables_compared'])}")
    print(f"  demotions  (1 -> 0)   {counts['demotions']:>8}  "
          f"{pct(counts['demotions'], counts['syllables_compared'])}")
    print()
    print(f"FUNCTION_WORDS performed with a beat: "
          f"{function_word_beats['stressed']}/{function_word_beats['total']}  "
          f"{pct(function_word_beats['stressed'], function_word_beats['total'])}")
    print(f"NEVER_ANCHOR  performed with a beat: "
          f"{never_anchor_beats['stressed']}/{never_anchor_beats['total']}  "
          f"{pct(never_anchor_beats['stressed'], never_anchor_beats['total'])}")
    print()
    print("most-promoted monosyllables (citation-unstressed, performed on the beat):")
    for word, n in promoted_examples.most_common(15):
        print(f"  {word:<12} {n}")


if __name__ == "__main__":
    main()
