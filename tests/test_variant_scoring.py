"""Tests for variant-aware scoring (Unit 9, Phase 3).

Scoring over pronunciation variants is "take the best": a rapper picks whichever
reading makes the line rhyme, so the score is the ``max`` over every variant
pairing -- a thin wrapper around the unchanged kernel. Spans multiply the same
way, via the cartesian product of their words' variants.
"""

import unittest

from rhyme_schemer import (
    best_is_rhyme,
    best_rhyme_score,
    pronunciation_for,
    pronunciations_for,
    pronunciations_for_span,
)
from rhyme_schemer.rhyme import DEFAULT_RHYME_THRESHOLD, rhyme_score


class TestBestOverVariants(unittest.TestCase):
    def test_rhyme_only_under_the_second_pronunciation(self):
        # "route" is R UW1 T ("root") | R AW1 T ("rout"). Against "shout" the
        # first reading does NOT rhyme; the second is a perfect match. Best-over-
        # variants must find it where first-variant-only scoring would miss it.
        route = pronunciations_for("route")
        shout = pronunciations_for("shout")
        first_only = rhyme_score(route[0], shout[0])
        self.assertLess(first_only, DEFAULT_RHYME_THRESHOLD)  # missed
        self.assertTrue(best_is_rhyme(route, shout))          # found

    def test_best_is_the_maximum_over_pairings(self):
        route = pronunciations_for("route")
        shout = pronunciations_for("shout")
        expected = max(rhyme_score(a, b) for a in route for b in shout)
        self.assertAlmostEqual(best_rhyme_score(route, shout), expected)

    def test_best_never_below_the_first_variant_pairing(self):
        # The max can only help: it is >= any single pairing, first included.
        for w1, w2 in (("read", "seed"), ("either", "fire"), ("cat", "hat")):
            a, b = pronunciations_for(w1), pronunciations_for(w2)
            self.assertGreaterEqual(
                best_rhyme_score(a, b) + 1e-12, rhyme_score(a[0], b[0])
            )

    def test_single_variant_words_match_the_plain_kernel(self):
        # When neither word has options, best-over-variants is just rhyme_score.
        a, b = pronunciations_for("cat"), pronunciations_for("hat")
        self.assertAlmostEqual(
            best_rhyme_score(a, b),
            rhyme_score(pronunciation_for("cat"), pronunciation_for("hat")),
        )

    def test_oov_scores_zero(self):
        self.assertEqual(best_rhyme_score(pronunciations_for("asdfqwer"),
                                          pronunciations_for("cat")), 0.0)


class TestSpanVariants(unittest.TestCase):
    def test_span_variants_are_the_cartesian_product(self):
        # A span's variant count is the product of its words' variant counts.
        n_read = len(pronunciations_for("read"))
        n_it = len(pronunciations_for("it"))
        spans = pronunciations_for_span(["read", "it"])
        self.assertEqual(len(spans), n_read * n_it)
        # Both readings of "read" survive into the assembled spans.
        first_nuclei = {s.vowel_skeleton[0] for s in spans}
        self.assertEqual(first_nuclei, {"EH", "IY"})

    def test_oov_word_empties_the_span_product(self):
        self.assertEqual(pronunciations_for_span(["read", "asdfqwer"]), [])

    def test_variant_span_scored_against_a_word(self):
        # Spans and variants compose: score a whole phrase's best reading.
        spans = pronunciations_for_span(["for", "real"])
        target = pronunciations_for("surreal")
        self.assertTrue(best_is_rhyme(spans, target))


if __name__ == "__main__":
    unittest.main()
