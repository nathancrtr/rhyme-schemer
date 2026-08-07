"""Rank-compare the hand-placed feature spaces against corpus evidence.

Run from the repo root (or anywhere):

    python learning/audits/audit_feature_space.py

This is an **audit, not a tuning pass** (the distinction the tuning ledger
insists on): it reports where our hand-placed geometry *disagrees in
ordering* with Hirjee & Brown's rap-corpus log-odds matrices, and checks a
handful of published qualitative claims (Katz 2015, Kawahara 2007). No
number in ``features.py`` moves because of anything printed here; the
findings feed the Unit 14 sweep's conditions instead.

Why *rank* comparison: a log-odds score entangles similarity with frequency
correction (see ``hirjee_brown_2009.py``), so its absolute values are not on
our [0, 1] scale -- but if rappers treat EY/IH as unrhymable and our space
calls the pair 2nd-closest, the *orderings* disagree, and that is
scale-free evidence.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rhyme_schemer.features import consonant_similarity, vowel_similarity  # noqa: E402

from hirjee_brown_2009 import (  # noqa: E402
    CONSONANT_LOGODDS,
    CONSONANTS,
    VOWEL_LOGODDS,
    VOWELS,
)


def _ranks(values: list[float]) -> list[float]:
    """Ranks (1 = largest), averaging ties -- Spearman's preprocessing."""
    order = sorted(range(len(values)), key=lambda i: -values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(a: list[float], b: list[float]) -> float:
    """Spearman rank correlation: Pearson's r over the two rank vectors."""
    ra, rb = _ranks(a), _ranks(b)
    n = len(ra)
    mean_a, mean_b = sum(ra) / n, sum(rb) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(ra, rb))
    var_a = sum((x - mean_a) ** 2 for x in ra)
    var_b = sum((y - mean_b) ** 2 for y in rb)
    return cov / (var_a * var_b) ** 0.5


def rank_report(
    title: str,
    pairs: list[tuple[str, str]],
    ours: list[float],
    corpus: list[float],
    top: int = 10,
) -> None:
    """Print overall agreement plus the biggest per-pair rank disagreements."""
    print(f"\n== {title} ==")
    print(f"pairs compared: {len(pairs)}   Spearman rho = {spearman(ours, corpus):+.3f}")

    our_ranks, corpus_ranks = _ranks(ours), _ranks(corpus)
    gaps = sorted(
        range(len(pairs)), key=lambda i: -abs(our_ranks[i] - corpus_ranks[i])
    )
    print(f"largest ordering disagreements (of {len(pairs)}; rank 1 = most similar):")
    print(f"  {'pair':<8} {'ours':>6} {'rank':>5} {'corpus':>7} {'rank':>5}")
    for i in gaps[:top]:
        a, b = pairs[i]
        print(
            f"  {a + '~' + b:<8} {ours[i]:>6.3f} {our_ranks[i]:>5.0f} "
            f"{corpus[i]:>+7.1f} {corpus_ranks[i]:>5.0f}"
        )


def audit_vowels() -> None:
    pairs = list(combinations(VOWELS, 2))
    ours = [vowel_similarity(a, b) for a, b in pairs]
    corpus = [VOWEL_LOGODDS[a, b] for a, b in pairs]
    rank_report("VOWELS: ours vs Hirjee & Brown 2009 (rap rhyme log-odds)", pairs, ours, corpus)

    # The ledger's named suspects, called out individually.
    print("\nledger suspects (corpus log-odds > 0 means 'rhymable more than chance'):")
    for a, b in [("EY", "IH"), ("EH", "AH"), ("EY", "EH"), ("AA", "OW"),
                 ("AH", "EH"), ("EH", "IY"), ("IY", "AY"), ("EH", "IH"), ("AA", "AO")]:
        print(f"  {a}~{b}:  ours {vowel_similarity(a, b):.3f}   corpus {VOWEL_LOGODDS[a, b]:+.1f}")


def audit_consonants() -> None:
    pairs = list(combinations(CONSONANTS, 2))
    ours = [consonant_similarity(a, b) for a, b in pairs]
    corpus = [CONSONANT_LOGODDS[a, b] for a, b in pairs]
    rank_report(
        "CONSONANTS (coda position): ours vs Hirjee & Brown 2009", pairs, ours, corpus
    )

    # Katz (2015), table 7: place mismatches among *nasals* carry far less
    # perceived rhyme distance than among oral stops (b = -2.51, sig.).
    nasal = vowel_pairs_mean([("M", "N"), ("M", "NG"), ("N", "NG")])
    oral = vowel_pairs_mean([("P", "T"), ("P", "K"), ("T", "K")])
    print("\nKatz 2015 check -- nasal place mismatch should be much cheaper than oral-stop:")
    print(f"  ours:   mean sim nasals {nasal:.3f}  vs oral stops {oral:.3f}"
          f"   ({'captures' if nasal > oral + 0.05 else 'MISSES'} the nasal discount)")
    hb_nasal = sum(CONSONANT_LOGODDS[p] for p in [("M", "N"), ("M", "NG"), ("N", "NG")]) / 3
    hb_oral = sum(CONSONANT_LOGODDS[p] for p in [("P", "T"), ("P", "K"), ("T", "K")]) / 3
    print(f"  corpus: mean log-odds nasals {hb_nasal:+.1f}  vs oral stops {hb_oral:+.1f}")

    # Kawahara (2007): similar pairs rhyme often, dissimilar rarely (Japanese
    # coda-less context; W is absent from both H&B's matrix and our codas, so
    # the {w-k} pair is skipped).
    print("\nKawahara 2007 check -- his 'often rhyme' pairs should outrank 'rarely':")
    for label, pair_list in [("often ", [("M", "N"), ("T", "S"), ("R", "N")]),
                             ("rarely", [("M", "SH"), ("N", "P")])]:
        sims = ", ".join(f"{a}~{b} {consonant_similarity(a, b):.3f}" for a, b in pair_list)
        print(f"  {label}: {sims}")


def vowel_pairs_mean(pair_list: list[tuple[str, str]]) -> float:
    return sum(consonant_similarity(a, b) for a, b in pair_list) / len(pair_list)


if __name__ == "__main__":
    audit_vowels()
    audit_consonants()
