"""Tests for sequence alignment and multisyllabic rhyme (Unit 8).

`align_tails` runs Needleman-Wunsch over two tails' vowel skeletons; `rhyme_score`
scores the resulting columns. House style: structural properties (no gaps when
lengths match, exactly one gap where one syllable is spare) and orderings, over
exact magnitudes. One test codifies the by-hand DP fill from the Unit 8 lesson.
"""

import unittest

from rhyme_schemer import (
    Pronunciation,
    Stress,
    Syllable,
    align_tails,
    pronunciation_for,
    rhyme_score,
    rhyme_tail,
)


def syl(nucleus: str, stress: Stress = Stress.PRIMARY) -> Syllable:
    return Syllable(onset=(), nucleus=nucleus, coda=(), stress=stress)


def nuclei(columns):
    """Render an alignment as a list of (nucleus_a|None, nucleus_b|None)."""
    return [
        (a.nucleus if a else None, b.nucleus if b else None) for a, b in columns
    ]


def score(w1: str, w2: str) -> float:
    return rhyme_score(pronunciation_for(w1), pronunciation_for(w2))


class TestEqualLengthParity(unittest.TestCase):
    def test_equal_length_tails_align_with_no_gaps(self):
        # When lengths match, the optimal path is the no-gap diagonal, so the
        # alignment reduces to position-by-position (the Unit 6 behavior).
        for w1, w2 in (("cat", "hat"), ("lincoln", "reason"), ("national", "rational")):
            cols = align_tails(rhyme_tail(pronunciation_for(w1)),
                               rhyme_tail(pronunciation_for(w2)))
            self.assertTrue(all(a is not None and b is not None for a, b in cols),
                            f"{w1}/{w2}: equal-length tails should not gap")

    def test_multisyllabic_perfect_rhymes_score_one(self):
        for w1, w2 in (("national", "rational"), ("reason", "season"),
                       ("city", "pity")):
            self.assertAlmostEqual(score(w1, w2), 1.0,
                                   msg=f"{w1}/{w2} should be a perfect rhyme")


class TestHandFilledExample(unittest.TestCase):
    def test_hypnotize_against_ah_ay_gaps_the_leading_vowel(self):
        # The Unit 8 lesson's by-hand table: hypnotize's tail [IH, AH, AY] aligned
        # against a bare [AH, AY]. The IH has no partner -> a single gap; AH~AH and
        # AY~AY pair perfectly. (gap penalty 0.6.)
        hyp_tail = rhyme_tail(pronunciation_for("hypnotize"))
        other = (syl("AH", Stress.UNSTRESSED), syl("AY"))
        cols = align_tails(hyp_tail, other)
        self.assertEqual(nuclei(cols), [("IH", None), ("AH", "AH"), ("AY", "AY")])
        gaps = [c for c in cols if c[0] is None or c[1] is None]
        self.assertEqual(len(gaps), 1)


class TestUnequalLengthScoring(unittest.TestCase):
    def test_spare_syllable_drags_score_down(self):
        # A whole unmatched syllable (scored 0) should keep the pair below the
        # rhyme range even when the matched part is a perfect vowel hit.
        for w1, w2 in (("cat", "reason"), ("emcee", "empty")):
            s = score(w1, w2)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0)
            self.assertLess(s, 0.75)


class TestGapPenaltyKnob(unittest.TestCase):
    def test_low_penalty_collapses_the_alignment_into_gaps(self):
        # The widget's lesson: when a gap is cheaper than a good substitution, the
        # optimal path avoids matching. lincoln/reason aligns cleanly at the
        # default penalty but sprouts gaps when the penalty is tiny.
        a, b = rhyme_tail(pronunciation_for("lincoln")), rhyme_tail(pronunciation_for("reason"))
        clean = align_tails(a, b)  # default 0.6
        collapsed = align_tails(a, b, gap_penalty=0.05)
        self.assertTrue(all(x is not None and y is not None for x, y in clean))
        self.assertTrue(any(x is None or y is None for x, y in collapsed))


if __name__ == "__main__":
    unittest.main()
