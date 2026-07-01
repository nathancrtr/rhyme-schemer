"""Core data structures: the syllable and the pronunciation.

A `Pronunciation` is the universal unit the rhyme engine will reason about. A
single word and a multi-word span (e.g. "ménage à trois") are *both* just
pronunciations -- ordered sequences of syllables -- so nothing downstream needs
to care which it started as.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .phonetics import Stress


@dataclass(frozen=True)
class Syllable:
    """One syllable, split into the classic onset / nucleus / coda anatomy.

    - ``onset``: consonant phonemes before the vowel (possibly empty)
    - ``nucleus``: the single vowel phoneme, *without* its stress digit
    - ``coda``: consonant phonemes after the vowel (possibly empty)
    - ``stress``: the stress carried by the nucleus
    """

    onset: tuple[str, ...]
    nucleus: str
    coda: tuple[str, ...]
    stress: Stress

    @property
    def rime(self) -> tuple[str, ...]:
        """Nucleus + coda -- the rhyme-bearing part of a syllable."""
        return (self.nucleus, *self.coda)

    def __str__(self) -> str:
        # Re-attach the stress digit to the nucleus for a CMUdict-style readout.
        parts = [*self.onset, f"{self.nucleus}{self.stress.value}", *self.coda]
        return " ".join(parts)


@dataclass(frozen=True)
class Pronunciation:
    """An ordered sequence of syllables, optionally tagged with its source text."""

    syllables: tuple[Syllable, ...]
    text: str | None = None

    @property
    def vowel_skeleton(self) -> tuple[str, ...]:
        """The bare nucleus of each syllable, in order.

        This is the spine of hip-hop rhyme: matching vowel sequences is the
        thing we ultimately care about most.
        """
        return tuple(s.nucleus for s in self.syllables)

    @property
    def stresses(self) -> tuple[Stress, ...]:
        return tuple(s.stress for s in self.syllables)

    @classmethod
    def concat(
        cls, prons: Iterable[Pronunciation], *, text: str | None = None
    ) -> Pronunciation:
        """Glue several pronunciations end to end into one.

        This is how a multi-word *span* ("get up") is built: it is simply the
        first word's syllables followed by the second's, with no boundary marker
        -- because downstream nothing cares where one word ended and the next
        began. The result is an ordinary ``Pronunciation``, so it flows through
        ``rhyme_tail`` and the whole kernel unchanged; a span carrying two
        primary stresses just anchors on the *last* one, exactly as a
        long single word would.

        ``text`` defaults to the source texts joined by spaces (skipping any
        that are ``None``), so a span prints as "get up".
        """
        prons = list(prons)
        syllables = tuple(s for p in prons for s in p.syllables)
        if text is None:
            texts = [p.text for p in prons if p.text]
            text = " ".join(texts) if texts else None
        return cls(syllables=syllables, text=text)

    def __str__(self) -> str:
        body = " . ".join(str(s) for s in self.syllables)
        return f"{self.text}: {body}" if self.text else body
