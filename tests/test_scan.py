"""Unit 11, piece 1: candidate generation for the internal-rhyme scanner.

These tests encode the design decisions from the Unit 11 dialogue:

- Performed stress is *data*, minted by the scanner as a second Pronunciation
  factory (``coerce_performed_stress``), so the anchored reading of "wake up"
  travels through the untouched kernel -- resolving the stress-anchoring
  limitation ``test_spans.TestStressAnchoringLimitation`` documents for
  citation stress (which still holds there, unchanged).
- Anchors are enumerated, not predicted -- but only on syllables that can
  phonologically bear stress (no schwa: "the" never anchors).
- A candidate's identity includes its anchor, so distinct rhyme structures
  over the same text stay distinct.
"""

from __future__ import annotations

import unittest

from rhyme_schemer import (
    Pronunciation,
    Stress,
    is_rhyme,
    pronunciations_for,
    rhyme_tail,
)
from rhyme_schemer.scan import (
    DEFAULT_COERCION_COST,
    Candidate,
    coerce_performed_stress,
    enumerate_candidates,
    find_matches,
    scan_verse,
    select_matches,
    tokenize_verse,
)

RUNNING_LINE = "Every day I wake up, take a cake and shake the state up"


def _first_reading(words: list[str], anchor: int) -> Pronunciation:
    """First-variant performed-stress reading of a span, for test brevity."""
    combo = [pronunciations_for(w)[0] for w in words]
    return coerce_performed_stress(Pronunciation.concat(combo), anchor)


class TestTokenizeVerse(unittest.TestCase):
    def test_strips_punctuation_keeps_apostrophes(self):
        [words] = tokenize_verse("Every day I wake up, I'm feelin' blessed.")
        self.assertEqual(
            words,
            ["Every", "day", "I", "wake", "up", "I'm", "feelin'", "blessed"],
        )

    def test_blank_lines_preserve_line_numbers(self):
        # A blank line stays an (empty) entry so indices are true line
        # numbers -- Unit 12 must map candidates back onto the typed verse.
        lines = tokenize_verse("wake up\n\nstate up")
        self.assertEqual(lines, [["wake", "up"], [], ["state", "up"]])


class TestCoercePerformedStress(unittest.TestCase):
    """The transport trick: an anchored reading survives ``rhyme_tail``."""

    def test_demotes_stresses_after_the_anchor(self):
        # Citation stress: "state" S T EY1 T, "up" AH1 P -- two primaries.
        # The performed reading anchored at "state" must demote "up", or
        # rhyme_tail's last-primary-wins scan would hand the tail right back.
        reading = _first_reading(["state", "up"], anchor=0)
        self.assertEqual(reading.stresses, (Stress.PRIMARY, Stress.UNSTRESSED))

    def test_rhyme_tail_now_returns_the_whole_slice(self):
        reading = _first_reading(["wake", "up"], anchor=0)
        self.assertEqual(
            [str(s) for s in rhyme_tail(reading)], ["W EY1 K", "AH0 P"]
        )

    def test_promotes_an_unstressed_anchor(self):
        # "spaghetti" S P AH0 G EH1 T IY0: coercing the beat onto final -TI
        # promotes IY0 to primary. Pre-anchor syllables keep their *citation*
        # stress -- -GHET- stays primary -- because the claim is minimal and
        # rhyme_tail anchors on the LAST primary, which is still ours.
        [spaghetti] = pronunciations_for("spaghetti")
        reading = coerce_performed_stress(spaghetti, anchor=2)
        self.assertEqual(
            reading.stresses,
            (Stress.UNSTRESSED, Stress.PRIMARY, Stress.PRIMARY),
        )
        self.assertEqual([str(s) for s in rhyme_tail(reading)], ["T IY1"])

    def test_the_wake_up_state_up_rhyme_is_now_visible(self):
        # The Unit 11 motivating bug: under citation stress these score 1.0
        # for the wrong reason (identity on "up"/"up") while the EY rhyme is
        # invisible. Anchored readings surface the real multisyllabic rhyme
        # through the unchanged public kernel.
        wake_up = _first_reading(["wake", "up"], anchor=0)
        state_up = _first_reading(["state", "up"], anchor=0)
        self.assertTrue(is_rhyme(wake_up, state_up))


class TestAnchorEligibility(unittest.TestCase):
    def test_schwa_syllables_never_anchor(self):
        # "sofa" S OW1 F AH0: the final schwa is phonologically unstressable,
        # so only SO- (index 0) may anchor.
        anchors = {c.anchor for c in enumerate_candidates("sofa")}
        self.assertEqual(anchors, {0})

    def test_articles_and_conjunctions_never_anchor(self):
        # The schwa gate alone was not enough here: CMUdict lists *emphatic*
        # variants for these words ("the" -> DH AH1 and DH IY0 "thee", "a" ->
        # the letter-name EY1), which are full vowels and would resurrect
        # every article as a rhyme partner for "free" and "day". Emphasis is
        # citation behavior, not a beat: articles and conjunctions are
        # proclitics, so NEVER_ANCHOR bars them outright -- unlike particles
        # and pronouns ("up", "I", "me"), which are coercible for a price.
        for word in ["the", "a", "and"]:
            self.assertEqual(enumerate_candidates(word), [], word)

    def test_full_vowel_monosyllable_anchors_despite_citation_stress(self):
        # "up" is AH1: a *full* STRUT vowel, eligible -- the dictionary's
        # citation stress neither grants nor blocks anchorhood.
        [candidate] = enumerate_candidates("up")
        self.assertEqual(candidate.anchor, 0)

    def test_spaghetti_anchors_on_full_vowels_only(self):
        anchors = {
            c.anchor for c in enumerate_candidates("spaghetti")
        }
        # spuh(AH0, reduced) is out; -GHET-(EH1) and -TI(IY0, full) are in.
        self.assertEqual(anchors, {1, 2})


class TestEnumerateCandidates(unittest.TestCase):
    def test_positions_spans_and_anchors(self):
        candidates = enumerate_candidates("wake up")
        described = {str(c) for c in candidates}
        self.assertEqual(
            described,
            {"wake @L0:W0+0", "wake up @L0:W0+0", "up @L0:W1+0"},
        )

    def test_spans_do_not_cross_line_breaks(self):
        for candidate in enumerate_candidates("wake up\nstate up"):
            self.assertEqual(candidate.end - candidate.start + 1,
                             len(candidate.words))
            self.assertIn(candidate.line, {0, 1})
            # No candidate mixes words from both lines.
            self.assertLessEqual(len(candidate.words), 2)

    def test_oov_word_poisons_only_the_spans_containing_it(self):
        candidates = enumerate_candidates("blorptastic flow")
        self.assertEqual({str(c) for c in candidates}, {"flow @L0:W1+0"})

    def test_readings_cover_variant_combinations(self):
        # "either" has two CMUdict variants (IY1- and AY1-initial); both
        # survive coercion as readings of the same candidate.
        [candidate] = [
            c for c in enumerate_candidates("either") if c.anchor == 0
        ]
        nuclei = {
            r.pronunciation.syllables[0].nucleus for r in candidate.readings
        }
        self.assertEqual(nuclei, {"IY", "AY"})


def _matches_between(verse: str, span_a: str, span_b: str, **kwargs):
    """Matches whose two candidates carry exactly these span texts."""
    matches = find_matches(enumerate_candidates(verse), **kwargs)
    return [
        m
        for m in matches
        if " ".join(m.a.words) == span_a and " ".join(m.b.words) == span_b
    ]


class TestFindMatches(unittest.TestCase):
    def test_finds_the_multisyllabic_internal_rhyme(self):
        [match] = _matches_between("wake up\nstate up", "wake up", "state up")
        self.assertGreater(match.score, 0.9)
        self.assertEqual(match.length, 2)

    def test_identity_anchors_cannot_open_a_rhyme(self):
        # Rime riche: "up"/"up" is repetition, not rhyme. Under citation
        # stress this pair scored a perfect 1.0; the seed gate removes the
        # identity-anchored readings from the running entirely.
        self.assertEqual(_matches_between("wake up\ngive up", "up", "up"), [])
        scores = [
            m.score
            for m in find_matches(enumerate_candidates("wake up\ngive up"))
        ]
        self.assertTrue(all(score < 1.0 for score in scores))
        # Known residue, pinned deliberately (cf. test_spans' stress-anchoring
        # precedent): wake/give anchors still pass the gate because our vowel
        # space rates EY/IH at 0.95 -- the feature-space generosity parked for
        # Unit 14's evaluation to adjudicate. The match survives today.
        self.assertTrue(scores)

    def test_repeating_a_word_is_not_a_rhyme(self):
        self.assertEqual(_matches_between("state\nstate", "state", "state"), [])

    def test_mosaic_rhymes_may_share_word_types(self):
        # "plane, man" / "sane, man": the repeated word TYPE "man" occupies
        # two different positions, so the pair is fully pairable -- identity
        # is welcome in the *extension* (man/man is a perfect column) so long
        # as the anchors (plane/sane, onsets PL/S) open the rhyme.
        [match] = _matches_between(
            "ride on a plane man\nnot feeling sane man", "plane man", "sane man"
        )
        self.assertEqual(match.score, 1.0)
        self.assertEqual(match.length, 2)

    def test_overlapping_positions_never_pair(self):
        # "state" at word 2 sits inside "state up" at words 2-3: one stretch
        # of audio, two descriptions -- not partners. (Each may still rhyme
        # with OTHER candidates; that is how overlapping classes coexist.)
        self.assertEqual(
            _matches_between("shake the state up", "state", "state up"), []
        )

    def test_proximity_window_limits_pairing(self):
        far_apart = "cake\nyo\nyo\nlake"
        self.assertEqual(_matches_between(far_apart, "cake", "lake"), [])
        [match] = _matches_between(
            far_apart, "cake", "lake", max_line_gap=3
        )
        self.assertEqual(match.score, 1.0)


class TestCoercionCost(unittest.TestCase):
    def test_default_beat_placements_are_free(self):
        # "wake up" anchored at wake: the anchor is citation-stressed content
        # and the demotion of "up" (a function word) is business as usual.
        [candidate] = [
            c
            for c in enumerate_candidates("wake up")
            if c.words == ("wake", "up")
        ]
        self.assertEqual({r.cost for r in candidate.readings}, {0.0})

    def test_promoting_an_unstressed_syllable_costs(self):
        # spaghetti@-TI promotes citation-unstressed IY0; spaghetti@-GHET-
        # anchors on the citation primary for free.
        by_anchor = {c.anchor: c for c in enumerate_candidates("spaghetti")}
        self.assertTrue(
            all(r.cost == DEFAULT_COERCION_COST
                for r in by_anchor[2].readings)
        )
        self.assertEqual({r.cost for r in by_anchor[1].readings}, {0.0})

    def test_anchoring_on_a_function_word_costs(self):
        # Even citation-stressed readings of coercible function words ("up"
        # AH1, "you" Y UW1) pay: their isolation-form stress is an artifact,
        # and claiming a beat on one is always a coercion.
        for word in ["up", "you"]:
            [candidate] = enumerate_candidates(word)
            self.assertTrue(
                all(r.cost == DEFAULT_COERCION_COST
                    for r in candidate.readings),
                word,
            )

    def test_cost_kills_function_word_junk_matches(self):
        # you~to share a perfect UW rime, but two function-word promotions
        # cost 0.30. PROVISIONAL: this is the right call mid-line, but
        # line-*final* "you"/"to" take nuclear stress for free and do rhyme
        # (walkthrough ledger item 5); a position-sensitive cost would flip
        # this case, and this assertion must change with it.
        self.assertEqual(_matches_between("you\nto", "you", "to"), [])
        # see~me survives its single discount (1.0 - 0.15): "me" really can
        # take the beat, and the ear agrees this one rhymes.
        [match] = _matches_between("see\nme", "see", "me")
        self.assertAlmostEqual(match.score, 1.0 - DEFAULT_COERCION_COST)

    def test_a_strong_rhyme_survives_the_discount(self):
        # "get UP!" / "cup": rime AH-P vs AH-P is perfect, onsets differ;
        # 1.0 gross - one function-word promotion = 0.85, still a rhyme.
        [match] = _matches_between("get up\ncup", "up", "cup")
        self.assertAlmostEqual(match.score, 1.0 - DEFAULT_COERCION_COST)


class TestSelectMatches(unittest.TestCase):
    def _selected_texts(self, verse: str) -> set[tuple[str, str]]:
        selected = select_matches(find_matches(enumerate_candidates(verse)))
        return {
            (" ".join(m.a.words), " ".join(m.b.words)) for m in selected
        }

    def test_an_extension_that_earns_its_seat_wins(self):
        # up/up pulls the average UP (0.964 > core wake~state's 0.928), so
        # the longer description of the event is the one reported.
        texts = self._selected_texts("wake up\nstate up")
        self.assertIn(("wake up", "state up"), texts)
        self.assertNotIn(("wake", "state"), texts)

    def test_dead_weight_extensions_lose_to_the_core(self):
        # and/up drags the average DOWN ("cake and"~"state up" 0.83 < core
        # cake~state 0.88): the average is the extension criterion.
        texts = self._selected_texts("cake and\nstate up")
        self.assertIn(("cake", "state"), texts)
        self.assertNotIn(("cake and", "state up"), texts)

    def test_mega_spans_lose_to_their_internal_hits(self):
        # Score-first selection auto-splits glued rhyme events: the 4-syllable
        # "wake up take a"~"cake and shake the" (0.950) averages below its
        # internal hits (take~shake at 1.0), so the hits win the events.
        texts = self._selected_texts(RUNNING_LINE)
        self.assertIn(("take", "shake"), texts)
        self.assertNotIn(("wake up take a", "cake and shake the"), texts)
        self.assertNotIn(("take a cake and", "shake the state up"), texts)
        # Nor may vacuous schwa padding steal the event on the length
        # tiebreak: "take a ~ shake the" ties take~shake at 1.0 only because
        # a/the is free schwa filler, and informative length breaks the tie.
        self.assertNotIn(("take a", "shake the"), texts)

    def test_distinct_overlapping_structures_both_survive(self):
        # The Unit 11 dialogue's requirement: "wake" partners with "take"
        # (monosyllabic EY class) while the overlapping "wake up" partners
        # with "state up" (multisyllabic pair). Same text, two structures.
        texts = self._selected_texts(RUNNING_LINE)
        self.assertIn(("wake", "take"), texts)
        self.assertIn(("wake up", "state up"), texts)

    def test_mosaic_subsumes_its_seed_on_tie(self):
        # plane man~sane man and plane~sane both score 1.0; the tie breaks
        # longer-first and the seed is the same event, so only the mosaic
        # survives.
        texts = self._selected_texts(
            "ride on a plane man\nnot feeling sane man"
        )
        self.assertIn(("plane man", "sane man"), texts)
        self.assertNotIn(("plane", "sane"), texts)


class TestScanVerse(unittest.TestCase):
    """The verse-level wiring: matches become graph edges, components become
    the scheme. The edges are the scanner's own selected matches -- NOT
    recomputed best_is_rhyme calls, which would readmit every seed-gated and
    coercion-priced rejection (the letter of the old 'feed group_rhymes
    unchanged' milestone would undo the unit; the spirit survives via the
    shared connected_components engine)."""

    @staticmethod
    def _group_texts(scan) -> list[set[str]]:
        return [
            {" ".join(c.words) for c in group} for group in scan.groups
        ]

    def test_overlapping_classes_coexist_in_the_scheme(self):
        # The unit's founding observation, realized end to end: one verse,
        # two rhyme classes whose text extents overlap on "wake"/"state".
        groups = self._group_texts(scan_verse(RUNNING_LINE))
        self.assertIn({"wake", "take", "cake", "shake", "state"}, groups)
        self.assertIn({"wake up", "state up"}, groups)

    def test_rhymes_group_across_lines(self):
        scan = scan_verse("ride on a plane man\nnot feeling sane man")
        self.assertIn({"plane man", "sane man"}, self._group_texts(scan))

    def test_oov_words_are_surfaced_not_silently_dropped(self):
        scan = scan_verse("blorptastic flow\nglow")
        self.assertEqual(scan.oov, ("blorptastic",))
        self.assertIn({"flow", "glow"}, self._group_texts(scan))


if __name__ == "__main__":
    unittest.main()
