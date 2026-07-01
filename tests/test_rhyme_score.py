"""Tests for rhyme_score — the equal-length rhyme kernel (Unit 6).

House style: assert structural properties (identity, symmetry, range) and
*orderings* we trust (perfect > slant > none) rather than exact magnitudes, so
the weights stay free to be tuned in Unit 7 without rewriting the suite. All
pairs here have equal-length tails; unequal lengths are Unit 8's problem.
"""

import unittest

from rhyme_schemer import pronunciation_for
from rhyme_schemer.rhyme import rhyme_score


def score(w1: str, w2: str) -> float:
    a, b = pronunciation_for(w1), pronunciation_for(w2)
    assert a is not None and b is not None, f"OOV in {w1!r}/{w2!r}"
    return rhyme_score(a, b)


class TestRhymeScoreStructure(unittest.TestCase):
    def test_identity_is_one(self):
        # A pronunciation rhymes perfectly with itself, for any weights.
        for word in ("cat", "time", "reason", "hypnotize"):
            self.assertAlmostEqual(score(word, word), 1.0)

    def test_symmetry(self):
        for w1, w2 in (("cat", "hat"), ("cat", "dog"), ("time", "tone")):
            self.assertAlmostEqual(score(w1, w2), score(w2, w1))

    def test_range(self):
        for w1, w2 in (("cat", "hat"), ("cat", "dog"), ("cat", "key"),
                       ("cat", "cab"), ("time", "rhyme")):
            s = score(w1, w2)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 1.0)

    def test_empty_pronunciation_scores_zero(self):
        from rhyme_schemer import Pronunciation
        empty = Pronunciation(syllables=())
        self.assertEqual(rhyme_score(empty, pronunciation_for("cat")), 0.0)


class TestPerfectRhyme(unittest.TestCase):
    def test_perfect_rhymes_score_one(self):
        # Same nucleus and same coda, different onset -> textbook perfect rhyme.
        for w1, w2 in (("cat", "hat"), ("time", "rhyme"), ("cat", "bat")):
            self.assertAlmostEqual(score(w1, w2), 1.0,
                                   msg=f"{w1}/{w2} should be a perfect rhyme")


class TestNonRhyme(unittest.TestCase):
    def test_non_rhymes_score_well_below_one(self):
        for w1, w2 in (("cat", "dog"), ("time", "tone"), ("cat", "key")):
            self.assertLess(score(w1, w2), 0.8,
                            msg=f"{w1}/{w2} should not read as a rhyme")


class TestGradedOrdering(unittest.TestCase):
    def test_assonance_sits_between_perfect_and_none(self):
        # cat/cab shares the nucleus (AE) but not the coda (T vs B): it should
        # rank below a perfect rhyme yet clearly above a true non-rhyme. This is
        # the graded behavior Unit 7 will lean on.
        perfect = score("cat", "hat")
        assonance = score("cat", "cab")
        none = score("cat", "dog")
        self.assertGreater(perfect, assonance)
        self.assertGreater(assonance, none)

    def test_shared_nucleus_beats_shared_coda(self):
        # Rhyme is vowel-led: matching the vowel (cat/cab) should beat matching
        # only the coda while missing the vowel (cat/cot -> AE vs AA, coda T=T).
        self.assertGreater(score("cat", "cab"), score("cat", "cot"))


class TestUnequalLengths(unittest.TestCase):
    def test_unequal_tail_lengths_score_without_error(self):
        # cat has a 1-syllable tail; reason has a 2-syllable tail. Unit 8's
        # alignment handles the mismatch, and an extra unmatched syllable drags
        # the score down rather than raising.
        s = rhyme_score(pronunciation_for("cat"), pronunciation_for("reason"))
        self.assertGreaterEqual(s, 0.0)
        self.assertLessEqual(s, 1.0)
        self.assertLess(s, 0.8)  # not a rhyme: a whole spare syllable


if __name__ == "__main__":
    unittest.main()
