"""Tests for the Unit 13 G2P fallback chain (``rhyme_schemer.g2p``).

Organized by chain link -- dictionary, normalization rules, lexicon,
letter-to-sound, failure -- plus the integration tests that state the
unit's milestone: a previously-skipped word participating in a detected
rhyme, discounted and flagged as guessed.
"""

from __future__ import annotations

import unittest

from rhyme_schemer.g2p import (
    A_FOR_ER,
    DEFAULT_LTS_COST,
    DICTIONARY,
    G_DROP,
    LETTER_TO_SOUND,
    LEXICON,
    OOV,
    STEM_SUFFIX,
    pronounce,
)
from rhyme_schemer.rhyme import best_rhyme_score
from rhyme_schemer.scan import scan_verse
from rhyme_schemer.syllabify import pronunciations_for


def _syllables(guess):
    """Human-readable syllables of a guess's first pronunciation."""
    return " . ".join(str(s) for s in guess.pronunciations[0].syllables)


class TestDictionaryLink(unittest.TestCase):
    def test_dictionary_words_pass_through_at_no_cost(self):
        guess = pronounce("steady")
        self.assertEqual(guess.source, DICTIONARY)
        self.assertEqual(guess.cost, 0.0)
        self.assertEqual(
            guess.pronunciations,
            tuple(pronunciations_for("steady")),
        )

    def test_all_variants_survive(self):
        # "either" has IY- and AY-initial variants; the chain must not
        # collapse them (variant-aware scoring depends on the full list).
        guess = pronounce("either")
        self.assertEqual(len(guess.pronunciations), 2)


class TestGDropRule(unittest.TestCase):
    def test_apostrophe_form_keeps_the_spelled_coda(self):
        # The design principle: "chokin'" is a performance transcription.
        # The stem lookup goes through "choking", but the spelled coda N
        # replaces the dictionary's NG -- N-vs-NG is a coda difference the
        # kernel scores, so faithfulness here is not pedantry.
        guess = pronounce("chokin'")
        self.assertEqual(guess.source, G_DROP)
        self.assertEqual(guess.cost, 0.0)
        self.assertEqual(_syllables(guess), "CH OW1 . K IH0 N")

    def test_bare_form_works_too(self):
        self.assertEqual(_syllables(pronounce("chokin")),
                         "CH OW1 . K IH0 N")

    def test_stem_fallback_when_ing_form_is_oov(self):
        # CMUdict lacks "flossing", so the rule falls back to "floss" and
        # appends the spelled suffix, re-syllabified by MOP (the S moves
        # into the new syllable's onset).
        guess = pronounce("flossin'")
        self.assertEqual(guess.source, STEM_SUFFIX)
        self.assertEqual(_syllables(guess), "F L AA1 . S IH0 N")

    def test_stem_orthography_restored(self):
        # Dropped silent e ("stylin" via "style") and consonant doubling
        # ("runnin" via "run") are undone before stem lookup.
        self.assertEqual(_syllables(pronounce("stylin'")),
                         "S T AY1 . L IH0 N")
        self.assertEqual(_syllables(pronounce("runnin'")),
                         "R AH1 . N IH0 N")


class TestAForErRule(unittest.TestCase):
    def test_final_a_reads_as_non_rhotic_schwa(self):
        # "holla" spells a performed non-rhotic vowel: final AH0 (rhymes
        # "follow"), not dictionary "holler"'s ER0.
        guess = pronounce("holla")
        self.assertEqual(guess.source, A_FOR_ER)
        self.assertEqual(_syllables(guess), "HH AA1 . L AH0")

    def test_non_er_stems_do_not_match(self):
        # "pasta" - "paster" isn't a word; the rule must not fire. (It
        # falls through to letter-to-sound instead of minting nonsense
        # from a dictionary miss.)
        self.assertNotEqual(pronounce("pasta").source, A_FOR_ER)


class TestLexicon(unittest.TestCase):
    def test_contractions_no_rule_can_derive(self):
        # "imma" contracts "I'm gonna"; nothing about the letters says so.
        guess = pronounce("imma")
        self.assertEqual(guess.source, LEXICON)
        self.assertEqual(guess.cost, 0.0)
        self.assertEqual(_syllables(guess), "AY1 . M AH0")

    def test_lexicon_outranks_the_rules(self):
        # "shoulda" *matches* -a-for-er via "shoulder" (which would mint a
        # wrong OW vowel), but it contracts "should have" -- the curated
        # entry must win over the pattern-match.
        guess = pronounce("shoulda")
        self.assertEqual(guess.source, LEXICON)
        self.assertEqual(_syllables(guess), "SH UH1 . D AH0")


class TestLetterToSound(unittest.TestCase):
    def test_guesses_carry_the_lts_cost(self):
        guess = pronounce("Coogi")
        self.assertEqual(guess.source, LETTER_TO_SOUND)
        self.assertEqual(guess.cost, DEFAULT_LTS_COST)
        self.assertEqual(_syllables(guess), "K UW1 . G IY0")

    def test_expressive_spelling(self):
        # Onomatopoeia bypasses literary orthography; the "aow" pattern
        # exists because expressive spellings are core OOV data here.
        self.assertEqual(_syllables(pronounce("blaow")), "B L AW1")

    def test_digraphs_survive_doubled_letter_collapse(self):
        # "oo" is a digraph with its own sound, not a doubled letter to
        # collapse; "bling"'s "ng" maps as a unit.
        self.assertEqual(_syllables(pronounce("bling")), "B L IH1 NG")

    def test_final_ie_and_i_read_as_y(self):
        self.assertEqual(_syllables(pronounce("homie")),
                         "HH AA1 . M IY0")


class TestChainFailure(unittest.TestCase):
    def test_vowelless_strings_stay_oov(self):
        # "brrr" collapses to "br": no vowel, no nucleus, no syllable.
        # The chain reports failure rather than inventing a vowel.
        guess = pronounce("brrr")
        self.assertEqual(guess.source, OOV)
        self.assertEqual(guess.pronunciations, ())


class TestMilestone(unittest.TestCase):
    """The unit's milestone: previously-skipped words participate in
    detected rhymes, discounted and flagged as G2P-derived."""

    def test_coogi_rhymes_groovy_through_the_kernel(self):
        coogi = pronounce("Coogi").pronunciations
        groovy = pronunciations_for("groovy")
        self.assertEqual(
            best_rhyme_score(list(coogi), groovy), 1.0
        )

    def test_guessed_word_participates_in_a_scanned_rhyme(self):
        # End to end: "Coogi" (letter-to-sound) lands in a rhyme class
        # with "groovy", and the scan says how its pronunciation was got.
        scan = scan_verse("rocking that Coogi\nfeeling so groovy")
        groups = [
            {" ".join(c.words) for c in group} for group in scan.groups
        ]
        self.assertIn({"Coogi", "groovy"}, groups)
        self.assertIn(("Coogi", "letter-to-sound"), scan.guessed)

    def test_lts_matches_pay_the_discount(self):
        # The same rhyme found via a guess scores below its kernel score:
        # both sides' Guess.costs came off the match. (Coogi~groovy is
        # 1.0 at the kernel; one LTS side pays 0.1.)
        scan = scan_verse("rocking that Coogi\nfeeling so groovy")
        [match] = [
            m for m in scan.matches
            if {" ".join(m.a.words), " ".join(m.b.words)}
            == {"Coogi", "groovy"}
        ]
        self.assertAlmostEqual(match.score, 1.0 - DEFAULT_LTS_COST)

    def test_dialect_spelling_rhyme_is_free(self):
        # Rule-derived pronunciations cost nothing: chokin'~jokin' scores
        # its full kernel value.
        scan = scan_verse("I was chokin'\nnow I'm jokin'")
        [match] = [
            m for m in scan.matches
            if {" ".join(m.a.words), " ".join(m.b.words)}
            == {"chokin'", "jokin'"}
        ]
        self.assertEqual(match.score, 1.0)


if __name__ == "__main__":
    unittest.main()
