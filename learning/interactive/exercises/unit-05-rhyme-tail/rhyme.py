"""The rhyme kernel — Unit 5 starts it with the rhyme-bearing tail.

>>> COPY THIS FILE INTO THE PACKAGE AS  rhyme_schemer/rhyme.py  <<<
then implement rhyme_tail (replace the NotImplementedError) until
tests/test_rhyme_tail.py is green.

Rhyme is anchored at the last *stressed* syllable, not merely the final one:
"lessen" and "strengthen" share a final syllable but do not rhyme. So the tail
runs from the last PRIMARY-stressed syllable through the end of the word.
"""

from __future__ import annotations

from .models import Pronunciation, Syllable
from .phonetics import Stress


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
    raise NotImplementedError("Implement rhyme_tail (Unit 5).")
