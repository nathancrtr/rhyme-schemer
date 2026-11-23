"""Tests for the pure parts of ``tools/mcflow_performed_eval.py``.

The tool itself needs a local MCFlow clone, which cannot live in this
repository. What can be tested here is everything that does not touch the
corpus: the transcription-to-ARPAbet mapping, and the claim the tool's
results rest on -- that its candidate factory, given dictionary
pronunciations and the scanner's own stress policy, builds exactly the
candidates ``scan.enumerate_candidates`` builds.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from mcflow_performed_eval import (  # noqa: E402
    build_candidates,
    ipa_syllable_to_phones,
    make_token,
    performed_pronunciation,
)
from mcflow_to_gold import Word  # noqa: E402

from rhyme_schemer.scan import enumerate_candidates, tokenize_verse  # noqa: E402

VERSE = (
    "My palms are steady my arms are ready\n"
    "I wake up shake the whole state up\n"
    "I face the day and make my way"
)


def _word(text, ipa, stresses, line=0, index=0):
    return Word(text=text, line=line, index=index, ipa=ipa, stresses=stresses)


class TestTranscriptionMapping(unittest.TestCase):
    def test_diphthong_is_one_vowel(self):
        self.assertEqual(ipa_syllable_to_phones("taIm", True),
                         ["T", "AY1", "M"])

    def test_stress_becomes_the_vowel_digit(self):
        self.assertEqual(ipa_syllable_to_phones("ðə", False), ["DH", "AH0"])
        self.assertEqual(ipa_syllable_to_phones("kət", True),
                         ["K", "AH1", "T"])

    def test_affricates_and_rhotic_vowel(self):
        self.assertEqual(ipa_syllable_to_phones("tʃɜ˞tʃ", True),
                         ["CH", "ER1", "CH"])

    def test_syllabic_consonant_gets_a_schwa(self):
        # "didn't" is transcribed "dI" + "dnt": the second syllable has no
        # vowel symbol, and CMUdict writes it D AH0 N T.
        self.assertEqual(ipa_syllable_to_phones("dnt", False),
                         ["D", "AH0", "N", "T"])

    def test_unknown_symbol_is_refused(self):
        self.assertIsNone(ipa_syllable_to_phones("t|a", True))

    def test_word_keeps_one_syllable_per_transcribed_syllable(self):
        pron = performed_pronunciation(
            _word("running", ["rə", "nIn"], [1, 0]))
        self.assertEqual([str(s) for s in pron.syllables],
                         ["R AH1", "N IH0 N"])

    def test_misaligned_stress_marks_are_refused(self):
        self.assertIsNone(
            performed_pronunciation(_word("running", ["rə", "nIn"], [1])))


class TestCandidateFactory(unittest.TestCase):
    def _lines(self, segments, stress):
        return [
            [make_token(_word(text, [], [], line=i, index=j), segments, stress)
             for j, text in enumerate(line)]
            for i, line in enumerate(tokenize_verse(VERSE))
        ]

    def test_dictionary_cell_reproduces_the_scanner(self):
        built = build_candidates(self._lines("dictionary", "inferred"), 4)
        self.assertEqual(built, enumerate_candidates(VERSE))

    def test_performed_beats_are_the_only_anchors(self):
        # "ready" performed with the beat on its second syllable: the
        # scanner's own policy would anchor on either, the performed policy
        # only where the beat was heard, and at no cost.
        word = _word("ready", ["rɜ", "di"], [0, 1])
        token = make_token(word, "performed", "performed")
        candidates = build_candidates([[token]], 4)
        self.assertEqual([c.anchor for c in candidates], [1])
        self.assertEqual([r.cost for r in candidates[0].readings], [0.0])

    def test_unusable_transcription_falls_back_to_the_dictionary(self):
        token = make_token(_word("ready", ["r|"], [1]),
                           "performed", "performed")
        self.assertTrue(token.fallback)
        self.assertTrue(token.variants)


if __name__ == "__main__":
    unittest.main()
