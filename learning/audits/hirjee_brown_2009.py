"""Hirjee & Brown (2009)'s learned rhyme scoring matrices, as data.

Transcribed 2026-08-07 from Tables 1 and 2 of:

    Hirjee & Brown (2009). Automatic Detection of Internal and Imperfect
    Rhymes in Rap Lyrics. ISMIR 2009.
    https://ismir2009.ismir.net/proceedings/OS8-1.pdf

These are BLOSUM-style **log-odds scores** estimated from observed rhyme
pairs in rap lyrics: positive = this pair co-occurs in rhyme position more
often than chance (rappers treat the sounds as rhymable), negative = less
often than chance. They are *corpus-derived evidence* about which sound
pairs actually function as rhymes in this genre -- the empirical check our
hand-placed feature space never had.

Two caveats to keep in mind when comparing against ``features.py``:

1. A log-odds score is similarity *entangled with frequency correction*:
   the diagonal itself varies (rare sounds score higher for self-match,
   e.g. OY 4.9 vs AA 2.3), so only the relative *ordering* of pairs is
   comparable to our distances -- hence the audit's rank comparison.
2. The consonant matrix is estimated over **coda** consonants (their "*"
   columns are unmatched-coda-edge scores; we drop them here), so it says
   nothing about onsets -- convenient, since neither does our kernel.

The row strings below are verbatim from the PDF text layer; ``_parse``
validates the upper-triangular row lengths so a transcription slip fails
loudly rather than silently skewing the audit.
"""

from __future__ import annotations

VOWELS = ["AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER",
          "EY", "IH", "IY", "OW", "OY", "UH", "UW"]

# Table 1, upper triangle: row i holds columns i..14.
_VOWEL_ROWS = """\
2.3 -3.3 -0.8 1.6 -1.7 -2.7 -7.2 -0.6 -3.9 -4.8 -3.9 -1.0 -1.7 -3.3 -3.9
2.1 -1.5 -6.6 -1.9 -3.3 -1.5 -3.4 -1.8 -2.0 -4.3 -4.6 -4.5 -3.7 -6.7
2.2 -1.2 -1.4 -1.4 -0.6 -0.2 -1.7 -0.3 -3.0 -1.0 -0.6 -0.9 -1.5
3.1 -1.0 -3.8 -6.5 -1.1 -3.9 -4.2 -6.3 -0.3 -0.4 1.1 -3.3
3.8 -0.3 -6.0 -4.2 -5.7 -6.0 -5.7 -2.0 -2.9 -4.5 -1.4
2.5 -4.2 -1.1 -7.0 -1.8 -3.2 -4.3 -1.1 -5.7 -6.4
1.9 -1.2 -1.5 0.2 -2.1 -7.0 -4.5 -6.1 -4.3
3.9 -5.6 -1.5 -5.5 -1.6 -2.7 -1.3 -2.6
2.5 -3.4 -2.7 -4.4 -4.3 -5.8 -6.5
2.0 -0.9 -7.1 0.2 -2.2 -3.7
2.4 -4.4 -4.2 -5.8 -6.4
2.8 -4.0 -2.5 -1.5
4.9 0.1 -3.7
2.6 -0.5
3.1
"""

# Table 2 column order (the trailing two "*" columns are dropped by _parse).
CONSONANTS = ["B", "CH", "D", "DH", "F", "G", "JH", "K", "L", "M", "N",
              "NG", "P", "R", "S", "SH", "T", "TH", "V", "Z", "ZH"]

_CONSONANT_ROWS = """\
4.3 -4.8 1.1 0.4 -5.5 1.9 1.9 -6.9 -0.3 -0.5 -1.6 -5.5 0.1 -0.9 -1.6 -4.6 -1.0 -4.3 2.3 0.3 -2.5 -0.6 -1.5
4.2 -1.6 -4.9 -0.3 0.3 0.4 1.5 -6.8 -6.6 -2.8 -5.5 1.1 -6.7 0.3 0.6 0.9 1.4 -6.1 -2.0 -2.5 -6.0 -2.6
2.3 -7.0 -7.6 0.1 0.2 -3.1 -1.7 -2.2 -2.2 -3.0 -1.8 -0.9 -9.0 -2.1 0.2 0.0 -0.2 0.0 -4.6 -0.2 1.2
3.5 -5.6 -5.1 -4.2 -0.4 -0.2 -2.0 -7.5 -5.6 -6.2 -1.4 -7.0 -4.8 -0.3 1.3 2.8 1.1 -2.6 -6.0 -3.4
3.4 -1.2 -4.9 -0.3 -1.5 -1.3 -3.5 -1.6 1.1 -2.7 1.1 1.2 -0.9 4.0 0.6 -7.3 -3.2 -1.4 -2.9
4.2 1.9 0.0 -0.2 -1.0 -1.9 -5.7 -0.6 -0.8 -2.5 -4.9 -1.1 -4.5 0.3 -0.3 -2.7 -0.9 -2.8
5.2 -6.3 -1.5 0.1 -0.5 -4.8 -0.2 -0.3 -0.6 0.6 -1.1 -3.6 1.4 1.0 4.1 -5.3 0.5
2.6 -2.9 -2.1 -2.6 -1.3 1.7 -2.1 -0.7 -0.6 0.9 0.5 -1.8 -3.1 -4.7 -1.0 -1.8
2.8 -1.8 -1.8 -2.8 -8.1 -0.5 -2.9 -6.6 -2.9 -6.3 -1.3 -1.6 -4.5 0.4 -1.0
2.7 1.8 0.7 -3.2 -1.2 -2.9 -1.1 -2.5 0.4 -0.6 -3.7 -4.2 -0.8 -1.7
2.2 1.2 -2.5 -1.0 -2.3 -0.7 -1.5 -0.6 -1.5 -2.1 -5.1 -0.4 -2.3
4.1 -6.8 -2.7 -2.3 -5.3 -3.5 -5.0 -2.1 -2.0 -3.2 0.2 -3.9
3.3 -2.0 -1.1 -0.7 1.1 0.9 -0.6 -7.9 -3.8 -0.7 -0.8
2.8 -2.3 -0.8 -1.2 -6.1 -2.1 -2.2 -4.3 1.7 -0.7
2.6 2.4 -1.0 1.0 -2.4 0.5 0.0 0.6 0.6
5.2 -0.6 -4.1 -1.3 -0.2 3.6 -5.8 -7.7
1.7 1.6 -0.9 -9.2 -5.2 0.0 0.7
4.4 0.5 -6.1 -2.0 -5.4 -0.6
2.9 -0.4 1.6 -1.2 -1.7
2.6 3.0 -1.3 1.1
6.8 -3.7 -5.6
"""


def _parse(symbols: list[str], rows: str, n_extra_cols: int = 0) -> dict[tuple[str, str], float]:
    """Expand verbatim upper-triangle rows into a symmetric pair -> score dict.

    Row i must hold exactly ``(len(symbols) + n_extra_cols) - i`` values
    (its own diagonal through the final column); anything else is a
    transcription error and raises. Extra trailing columns (the consonant
    table's two "*" columns) are validated for count but not stored.
    """
    n = len(symbols)
    lines = rows.strip().splitlines()
    if len(lines) != n:
        raise ValueError(f"expected {n} rows, got {len(lines)}")

    scores: dict[tuple[str, str], float] = {}
    for i, line in enumerate(lines):
        values = [float(v) for v in line.split()]
        expected = (n + n_extra_cols) - i
        if len(values) != expected:
            raise ValueError(f"row {symbols[i]}: expected {expected} values, got {len(values)}")
        for j, value in enumerate(values[: n - i]):
            a, b = symbols[i], symbols[i + j]
            scores[(a, b)] = scores[(b, a)] = value
    return scores


VOWEL_LOGODDS: dict[tuple[str, str], float] = _parse(VOWELS, _VOWEL_ROWS)
CONSONANT_LOGODDS: dict[tuple[str, str], float] = _parse(
    CONSONANTS, _CONSONANT_ROWS, n_extra_cols=2
)
