"""Tests for the vowel and consonant feature spaces.

We assert *structural* properties (identity, symmetry, range) and *ordering*
relationships we are confident about, rather than exact distances -- the
coordinates are hand-placed approximations, so the rankings are what we trust.
"""

import unittest

from rhyme_schemer.features import (
    CONSONANT_FEATURES,
    VOWEL_FEATURES,
    consonant_distance,
    consonant_similarity,
    vowel_distance,
    vowel_similarity,
)


class TestVowelDistance(unittest.TestCase):
    def test_identity_is_zero(self):
        for v in VOWEL_FEATURES:
            self.assertEqual(vowel_distance(v, v), 0.0)
            self.assertEqual(vowel_similarity(v, v), 1.0)

    def test_symmetry(self):
        for a in VOWEL_FEATURES:
            for b in VOWEL_FEATURES:
                self.assertAlmostEqual(vowel_distance(a, b), vowel_distance(b, a))

    def test_range(self):
        for a in VOWEL_FEATURES:
            for b in VOWEL_FEATURES:
                self.assertGreaterEqual(vowel_distance(a, b), 0.0)
                self.assertLessEqual(vowel_distance(a, b), 1.0)

    def test_stress_digits_ignored(self):
        self.assertEqual(vowel_distance("IH1", "IH0"), 0.0)
        self.assertEqual(vowel_distance("AY2", "AY"), 0.0)

    def test_neighbors_closer_than_opposites(self):
        # IH/IY are tense-lax neighbors; IH/UW are front vs back+round.
        self.assertGreater(vowel_similarity("IH", "IY"), vowel_similarity("IH", "UW"))
        # EH/AE are vertical neighbors on the front edge.
        self.assertGreater(vowel_similarity("EH", "AE"), vowel_similarity("EH", "UW"))

    def test_shared_offglide_helps_diphthongs(self):
        # AY and OY share the ɪ offglide; AY/UW share nothing relevant.
        self.assertGreater(vowel_similarity("AY", "OY"), vowel_similarity("AY", "UW"))

    def test_rhotic_penalty(self):
        # ER is positionally near AH but the rhotic mismatch separates them.
        self.assertLess(vowel_similarity("ER", "AH"), 1.0)


class TestConsonantDistance(unittest.TestCase):
    def test_identity_is_zero(self):
        for c in CONSONANT_FEATURES:
            self.assertEqual(consonant_distance(c, c), 0.0)
            self.assertEqual(consonant_similarity(c, c), 1.0)

    def test_symmetry(self):
        for a in CONSONANT_FEATURES:
            for b in CONSONANT_FEATURES:
                self.assertAlmostEqual(consonant_distance(a, b), consonant_distance(b, a))

    def test_range(self):
        for a in CONSONANT_FEATURES:
            for b in CONSONANT_FEATURES:
                self.assertGreaterEqual(consonant_distance(a, b), 0.0)
                self.assertLessEqual(consonant_distance(a, b), 1.0)

    def test_voicing_pairs_are_close(self):
        # Same place & manner, differ only in voicing -> strong near-rhyme.
        self.assertGreater(consonant_similarity("S", "Z"), 0.8)
        self.assertGreater(consonant_similarity("T", "D"), 0.8)

    def test_same_manner_closer_than_different(self):
        # Two nasals (N/M) should beat a nasal vs a stop (N/D).
        self.assertGreater(consonant_similarity("N", "M"), consonant_similarity("N", "D"))

    def test_sibilants_cluster(self):
        # S/SH share manner and sit adjacent in place -> closer than S vs far stop.
        self.assertGreater(consonant_similarity("S", "SH"), consonant_similarity("S", "P"))


if __name__ == "__main__":
    unittest.main()
