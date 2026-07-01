"""Tests for graded slant rhyme and the yes/no threshold (Unit 7).

These run on CMUdict's General American pronunciations, so "Lincoln" carries the
KIT vowel /IH/ and "reason" the FLEECE vowel /IY/ -- a near-match, which is
exactly what makes the pair the canonical *slant* rhyme here.

Per the Unit 7 lesson's warning against over-fitting weights to one pair, we
assert *orderings* (perfect > slant > none) and which side of the threshold a
pair lands on -- never exact magnitudes.
"""

import unittest

from rhyme_schemer import pronunciation_for
from rhyme_schemer.rhyme import (
    DEFAULT_RHYME_THRESHOLD,
    is_rhyme,
    rhyme_score,
)


def score(w1: str, w2: str) -> float:
    return rhyme_score(pronunciation_for(w1), pronunciation_for(w2))


def rhymes(w1: str, w2: str, **kw) -> bool:
    return is_rhyme(pronunciation_for(w1), pronunciation_for(w2), **kw)


class TestGradedContinuum(unittest.TestCase):
    def test_perfect_beats_slant_beats_none(self):
        # The whole point of the graded kernel: three distinct tiers.
        perfect = score("cold", "gold")     # identical tails -> 1.0
        slant = score("lincoln", "reason")  # near vowel, shared -on ending
        none = score("lincoln", "orange")   # unrelated tail
        self.assertGreater(perfect, slant)
        self.assertGreater(slant, none)


class TestThresholdDecision(unittest.TestCase):
    def test_slant_rhyme_clears_default_threshold(self):
        self.assertTrue(rhymes("lincoln", "reason"))

    def test_non_rhyme_fails_default_threshold(self):
        self.assertFalse(rhymes("lincoln", "orange"))

    def test_perfect_rhyme_clears_even_a_strict_threshold(self):
        # threshold=1.0 recovers perfect-rhyme-only detection exactly.
        self.assertTrue(rhymes("cold", "gold", threshold=1.0))
        self.assertFalse(rhymes("lincoln", "reason", threshold=1.0))

    def test_threshold_is_a_looseness_knob(self):
        # A pair below the default can be admitted by loosening the threshold
        # alone -- weights (ranking) and threshold (cutoff) are separate knobs.
        self.assertFalse(rhymes("time", "tone"))                    # ~0.62 < 0.75
        self.assertTrue(rhymes("time", "tone", threshold=0.5))

    def test_default_threshold_sits_between_the_clusters(self):
        # Documents the calibration: slant pairs above it, non-rhymes below.
        self.assertLess(score("lincoln", "orange"), DEFAULT_RHYME_THRESHOLD)
        self.assertLess(DEFAULT_RHYME_THRESHOLD, score("lincoln", "reason"))


if __name__ == "__main__":
    unittest.main()
