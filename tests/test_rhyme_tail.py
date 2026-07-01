"""Tests for rhyme_tail — the rhyme-bearing tail (Unit 5).

Following the repo's house style, we assert *structural* properties (the tail is
a suffix of the syllables; its nuclei are a suffix of the vowel skeleton) and a
few *example* relationships we're confident about, rather than leaning on exact
ARPAbet strings everywhere. The fallback cases build pronunciations by hand,
because no real English word lacks a primary stress.
"""

import unittest

from rhyme_schemer import Pronunciation, Syllable, Stress, pronunciation_for
from rhyme_schemer.rhyme import rhyme_tail


def syl(onset, nucleus, coda, stress):
    """Small helper to hand-build a Syllable."""
    return Syllable(onset=tuple(onset), nucleus=nucleus, coda=tuple(coda), stress=stress)


class TestRhymeTailStructure(unittest.TestCase):
    def test_tail_is_a_suffix_of_the_syllables(self):
        for word in ("reason", "around", "hypnotize", "six", "lincoln"):
            pron = pronunciation_for(word)
            assert pron is not None, f"{word!r} unexpectedly OOV"
            tail = rhyme_tail(pron)
            self.assertGreater(len(tail), 0, f"{word}: tail should be non-empty")
            self.assertLessEqual(len(tail), len(pron.syllables))
            # the tail must be exactly the final len(tail) syllables, in order
            self.assertEqual(tail, pron.syllables[len(pron.syllables) - len(tail):])

    def test_tail_nuclei_are_a_suffix_of_the_vowel_skeleton(self):
        for word in ("reason", "around", "hypnotize"):
            pron = pronunciation_for(word)
            tail = rhyme_tail(pron)
            tail_nuclei = tuple(s.nucleus for s in tail)
            skeleton = pron.vowel_skeleton
            self.assertEqual(tail_nuclei, skeleton[len(skeleton) - len(tail_nuclei):])

    def test_tail_begins_at_a_stressed_syllable_when_one_exists(self):
        # When the word has a primary stress, the first tail syllable carries it.
        for word in ("reason", "around", "lincoln", "six"):
            pron = pronunciation_for(word)
            tail = rhyme_tail(pron)
            self.assertEqual(tail[0].stress, Stress.PRIMARY,
                             f"{word}: tail should start at the primary-stressed syllable")


class TestRhymeTailExamples(unittest.TestCase):
    def test_reason_primary_first_returns_whole_word(self):
        # R IY1 . Z AH0 N -> primary on syllable 0, so the tail is the whole word.
        pron = pronunciation_for("reason")
        self.assertEqual(rhyme_tail(pron), pron.syllables)

    def test_around_slices_to_the_stressed_tail(self):
        # AH0 . R AW1 N D -> primary on syllable 1, so the tail is just that syllable.
        pron = pronunciation_for("around")
        tail = rhyme_tail(pron)
        self.assertEqual(len(tail), 1)
        self.assertEqual(tail[0].nucleus, "AW")
        self.assertLess(len(tail), len(pron.syllables))  # genuine slicing happened

    def test_monosyllable_is_its_own_tail(self):
        # S IH1 K S -> one syllable, which is the whole tail.
        pron = pronunciation_for("six")
        self.assertEqual(rhyme_tail(pron), pron.syllables)


class TestRhymeTailFallbacks(unittest.TestCase):
    def test_secondary_stress_fallback(self):
        # No primary anywhere; tail should start at the last SECONDARY syllable.
        pron = Pronunciation(syllables=(
            syl(("B",), "AH", (), Stress.UNSTRESSED),
            syl(("T",), "EH", (), Stress.SECONDARY),
            syl(("N",), "AH", (), Stress.UNSTRESSED),
        ))
        tail = rhyme_tail(pron)
        self.assertEqual(len(tail), 2)               # from the SECONDARY syllable on
        self.assertEqual(tail[0].stress, Stress.SECONDARY)

    def test_no_stress_falls_back_to_final_syllable(self):
        # All unstressed: fall back to the final syllable alone.
        pron = Pronunciation(syllables=(
            syl((), "AH", (), Stress.UNSTRESSED),
            syl(("N",), "AH", (), Stress.UNSTRESSED),
        ))
        tail = rhyme_tail(pron)
        self.assertEqual(len(tail), 1)
        self.assertEqual(tail, pron.syllables[-1:])

    def test_last_primary_wins_when_several(self):
        # A multi-word span can carry two primaries; the LAST anchors the tail.
        pron = Pronunciation(syllables=(
            syl(("G",), "EH", (), Stress.PRIMARY),
            syl(("M",), "AH", (), Stress.UNSTRESSED),
            syl(("N",), "IY", (), Stress.PRIMARY),
        ))
        tail = rhyme_tail(pron)
        self.assertEqual(len(tail), 1)
        self.assertEqual(tail[0].stress, Stress.PRIMARY)
        self.assertEqual(tail[0].nucleus, "IY")

    def test_empty_pronunciation_has_empty_tail(self):
        self.assertEqual(rhyme_tail(Pronunciation(syllables=())), ())


if __name__ == "__main__":
    unittest.main()
