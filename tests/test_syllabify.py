"""Tests for the syllabifier.

Each case records the expected syllable break for a word from our running
"Hypnotize" examples, written as the human-readable CMUdict-per-syllable form
(what ``str(Syllable)`` produces). If the Maximal Onset Principle drifts, these
will catch it.
"""

import unittest

from rhyme_schemer import pronunciation_for, syllabify
from rhyme_schemer.phonetics import Stress, is_legal_onset, is_vowel, strip_stress


def syllable_strings(word: str) -> list[str]:
    pron = pronunciation_for(word)
    assert pron is not None, f"{word!r} unexpectedly OOV"
    return [str(s) for s in pron.syllables]


class TestPhonetics(unittest.TestCase):
    def test_strip_stress(self):
        self.assertEqual(strip_stress("IH1"), ("IH", Stress.PRIMARY))
        self.assertEqual(strip_stress("AH0"), ("AH", Stress.UNSTRESSED))
        self.assertEqual(strip_stress("NG"), ("NG", None))

    def test_is_vowel(self):
        self.assertTrue(is_vowel("IH1"))
        self.assertTrue(is_vowel("ER0"))
        self.assertFalse(is_vowel("NG"))
        self.assertFalse(is_vowel("S"))

    def test_onset_legality(self):
        self.assertTrue(is_legal_onset(()))           # vowel-initial syllable
        self.assertTrue(is_legal_onset(("K",)))
        self.assertFalse(is_legal_onset(("NG",)))     # NG can't begin a syllable
        self.assertTrue(is_legal_onset(("S", "T", "R")))
        self.assertFalse(is_legal_onset(("K", "S")))  # not an English onset


class TestSyllabify(unittest.TestCase):
    def test_lincoln(self):
        # L IH1 NG K AH0 N -> ling . kun  (coda NG; onset K via MOP)
        self.assertEqual(syllable_strings("lincoln"), ["L IH1 NG", "K AH0 N"])

    def test_reason(self):
        # R IY1 Z AH0 N -> ree . zun  (open first syllable; Z is next onset)
        self.assertEqual(syllable_strings("reason"), ["R IY1", "Z AH0 N"])

    def test_lexus(self):
        # L EH1 K S AH0 S -> lek . sus  (KS not a legal onset, so K is coda)
        self.assertEqual(syllable_strings("lexus"), ["L EH1 K", "S AH0 S"])

    def test_cutie(self):
        # K Y UW1 T IY0 -> kyoo . tee  (KY is a legal onset cluster)
        self.assertEqual(syllable_strings("cutie"), ["K Y UW1", "T IY0"])

    def test_hypnotize(self):
        # HH IH1 P N AH0 T AY2 Z -> hip . nuh . tize
        self.assertEqual(
            syllable_strings("hypnotize"), ["HH IH1 P", "N AH0", "T AY2 Z"]
        )

    def test_monosyllable_coda_keeps_all_finals(self):
        # S IH1 K S -> all trailing consonants stay in the single coda.
        self.assertEqual(syllable_strings("six"), ["S IH1 K S"])

    def test_oov_returns_none(self):
        self.assertIsNone(pronunciation_for("coogi"))   # not in CMUdict

    def test_empty_phones(self):
        self.assertEqual(syllabify([]), ())


if __name__ == "__main__":
    unittest.main()
