"""Tests for multi-word spans (Unit 9, Phase 1).

A *span* is several words scored as one unit. The whole point of the model's
core invariant -- a word and a span are the same downstream object -- is that a
span is just a longer ``Pronunciation`` and flows through the unchanged rhyme
kernel. These tests pin down that plumbing, plus one honest limitation the
canonical "get up"/"setup" example exposes.
"""

import unittest

from rhyme_schemer import (
    Pronunciation,
    pronunciation_for,
    pronunciation_for_span,
)
from rhyme_schemer.rhyme import is_rhyme, rhyme_score


class TestSpanAssembly(unittest.TestCase):
    def test_span_is_the_words_syllables_end_to_end(self):
        # "get up" is get's syllables followed by up's -- no boundary marker.
        span = pronunciation_for_span(["get", "up"])
        assert span is not None
        self.assertEqual(
            [str(s) for s in span.syllables], ["G EH1 T", "AH1 P"]
        )
        # And its source text prints as the joined phrase.
        self.assertEqual(span.text, "get up")

    def test_single_word_span_equals_the_bare_word(self):
        # A one-word span must be indistinguishable from looking the word up.
        span = pronunciation_for_span(["cat"])
        word = pronunciation_for("cat")
        assert span is not None and word is not None
        self.assertEqual(span.syllables, word.syllables)

    def test_oov_anywhere_makes_the_whole_span_oov(self):
        # Same skip-and-flag contract as pronunciation_for: one miss -> None.
        self.assertIsNone(pronunciation_for_span(["get", "asdfqwer"]))
        self.assertIsNone(pronunciation_for_span(["asdfqwer", "up"]))

    def test_concat_of_pronunciations_is_a_pronunciation(self):
        # The composition itself lives on the model and yields the same type.
        parts = [pronunciation_for("get"), pronunciation_for("up")]
        assert all(p is not None for p in parts)
        joined = Pronunciation.concat(parts)
        self.assertIsInstance(joined, Pronunciation)
        self.assertEqual(pronunciation_for_span(["get", "up"]), joined)


class TestSpanScoresThroughTheKernel(unittest.TestCase):
    def test_span_vs_word_rhyme_clears_threshold(self):
        # The milestone: a multi-word span scored against a single word by the
        # unchanged kernel. "for real" / "surreal" is a clean perfect rhyme.
        span = pronunciation_for_span(["for", "real"])
        word = pronunciation_for("surreal")
        assert span is not None and word is not None
        self.assertTrue(is_rhyme(span, word))


class TestKnownLimitation(unittest.TestCase):
    """"get up"/"setup" -- the curriculum's own example -- exposes, not a span
    bug, but the *stress-coercion* limitation already flagged for future work:
    the kernel anchors the rhyme tail on the last PRIMARY-stressed syllable
    using CMUdict's citation stress, which it cannot yet coerce to match how a
    rapper actually performs the line.
    """

    def test_the_vowels_really_do_rhyme(self):
        # As bare vowel sequences the rhyme is perfect: EH-AH vs EH-AH. The
        # rhyme is genuinely present in the phonology.
        span = pronunciation_for_span(["get", "up"])
        setup = pronunciation_for("setup")
        assert span is not None and setup is not None
        self.assertEqual(span.vowel_skeleton, setup.vowel_skeleton)

    def test_but_stress_anchoring_hides_it(self):
        # "get UP" carries primary on *both* syllables, so the tail collapses to
        # just (AH1 P); "setup" keeps SET-up (primary first). Mismatched tails
        # -> a gap -> the kernel under-credits a rhyme the ear hears clearly.
        # This assertion documents current behavior; a future prosody unit that
        # coerces stress is expected to flip it.
        span = pronunciation_for_span(["get", "up"])
        setup = pronunciation_for("setup")
        self.assertFalse(is_rhyme(span, setup))
        self.assertLess(rhyme_score(span, setup), 1.0)


if __name__ == "__main__":
    unittest.main()
