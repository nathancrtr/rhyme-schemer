"""Tests for pronunciation-variant lookup (Unit 9, Phase 2).

CMUdict lists several pronunciations for many words; ``pronunciations_for``
exposes the whole list so scoring can later pick the best one. Here we only
check the lookup layer: that the list is complete, that OOV yields an empty
list, and that the singular convenience stays consistent with it.
"""

import unittest

from rhyme_schemer import pronunciation_for, pronunciations_for


class TestVariantLookup(unittest.TestCase):
    def test_returns_all_variants(self):
        # "read" is R EH1 D (past) or R IY1 D (present) -- two real variants.
        skeletons = {p.vowel_skeleton for p in pronunciations_for("read")}
        self.assertIn(("EH",), skeletons)
        self.assertIn(("IY",), skeletons)

    def test_single_variant_word_gives_one(self):
        self.assertEqual(len(pronunciations_for("cat")), 1)

    def test_oov_gives_empty_list(self):
        # Empty list, not None: the plural's skip-and-flag is "nothing here".
        self.assertEqual(pronunciations_for("asdfqwer"), [])

    def test_singular_is_the_first_variant(self):
        # pronunciation_for must stay the head of pronunciations_for so the two
        # never drift apart.
        variants = pronunciations_for("read")
        self.assertEqual(pronunciation_for("read"), variants[0])

    def test_singular_oov_is_none(self):
        self.assertIsNone(pronunciation_for("asdfqwer"))


if __name__ == "__main__":
    unittest.main()
