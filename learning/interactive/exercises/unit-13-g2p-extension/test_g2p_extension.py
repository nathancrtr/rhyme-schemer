"""Tests for the Unit 13 G2P-extension exercise.

Run from this directory:  python -m unittest test_g2p_extension -v

These fail against the unmodified repo -- that's the exercise. They check
*outcomes* (the chain now voices each word, plausibly), not which link you
fixed; task.md is where the route gets argued.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from rhyme_schemer.g2p import LETTER_TO_SOUND, OOV, pronounce


def nuclei(pron):
    return [s.nucleus for s in pron.syllables]


class TestSkrrt(unittest.TestCase):
    def test_skrrt_is_no_longer_oov(self):
        guess = pronounce("skrrt")
        self.assertNotEqual(guess.source, OOV, "the chain should now voice 'skrrt'")
        self.assertTrue(guess.pronunciations)

    def test_skrrt_has_a_syllabic_r_nucleus(self):
        guess = pronounce("skrrt")
        pron = guess.pronunciations[0]
        self.assertEqual(len(pron.syllables), 1)
        self.assertEqual(nuclei(pron), ["ER"], "the performed nucleus is a syllabic R (ER)")

    def test_skrrt_costs_nothing(self):
        # A curated entry testifies; only letter-to-sound guesses pay.
        self.assertEqual(pronounce("skrrt").cost, 0.0)


class TestDeadass(unittest.TestCase):
    def test_deadass_first_nucleus_is_EH_not_IY(self):
        # The stock LTS "ea"->IY pattern says dee-dass; the word says dead.
        guess = pronounce("deadass")
        pron = guess.pronunciations[0]
        self.assertEqual(pron.syllables[0].nucleus, "EH")

    def test_deadass_is_not_a_letter_to_sound_guess(self):
        # However you fixed it, the crude guesser should no longer own this
        # word -- its answer was wrong.
        self.assertNotEqual(pronounce("deadass").source, LETTER_TO_SOUND)


class TestBoutta(unittest.TestCase):
    def test_boutta_ends_in_schwa(self):
        # Contracts "(a)bout to": B AW1 T AH0 -- final AH, like "gotta".
        guess = pronounce("boutta")
        pron = guess.pronunciations[0]
        self.assertEqual(pron.syllables[-1].nucleus, "AH")
        self.assertEqual(pron.syllables[0].nucleus, "AW")
        self.assertNotEqual(guess.source, LETTER_TO_SOUND)


class TestTheFlagStillWorks(unittest.TestCase):
    def test_vowelless_noise_stays_oov(self):
        # Extending coverage must not break the refusal path: skip-and-flag's
        # flag half is load-bearing (renderers mark OOV words).
        for word in ("brrr", "psst", "tsk"):
            self.assertEqual(pronounce(word).source, OOV, word)


if __name__ == "__main__":
    unittest.main()
