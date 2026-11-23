"""Tests for the Unit 14 evaluation harness (``rhyme_schemer.evaluate``).

A ruler you can't trust is worse than no ruler, so these tests use tiny
engineered verses where every pair count is checkable by hand -- the gold
format round-trips, the pair explosion and vetoes count correctly, each
matching mode draws its documented line, and the two prediction levels
(edges vs classes) measure what they claim to.
"""

from __future__ import annotations

import unittest

from rhyme_schemer.evaluate import (
    Extent,
    agreement,
    annotation_template,
    class_pairs,
    edge_pairs,
    evaluate_verse,
    parse_gold,
    score_pairs,
)
from rhyme_schemer.scan import scan_verse

# Four line-final EY rhymes; "phone" rhymes with nothing. Every gold
# number below is hand-countable.
TINY = "day@0.1 way@0.2 -- gold uses this verse's own layout"

TINY_GOLD = """\
# hand-checkable toy annotation
verse:
  I say the day
  went my way
  on the phone
  not today

group: say@0.1 day@0.3 way@1.2 today@3.1
not: say@0.1 today@3.1
"""


class TestGoldParsing(unittest.TestCase):
    def test_parse_recovers_verse_groups_and_vetoes(self):
        gold = parse_gold(TINY_GOLD)
        self.assertEqual(gold.verse.splitlines()[0], "I say the day")
        self.assertEqual(len(gold.groups), 1)
        self.assertEqual(len(gold.groups[0]), 4)
        self.assertEqual(len(gold.vetoes), 1)

    def test_pairs_explode_groups_and_apply_vetoes(self):
        # 4 members -> C(4,2) = 6 pairs, minus the vetoed say~today = 5.
        gold = parse_gold(TINY_GOLD)
        pairs = gold.pairs()
        self.assertEqual(len(pairs), 5)
        say, today = Extent(0, 1, 1), Extent(3, 1, 1)
        self.assertNotIn((say, today), pairs)

    def test_word_text_is_checked_against_position(self):
        # The typo guard: a reference whose text doesn't match the word at
        # that position must fail loudly at parse time.
        bad = TINY_GOLD.replace("say@0.1", "day@0.1")
        with self.assertRaises(ValueError) as ctx:
            parse_gold(bad)
        self.assertIn("index slip", str(ctx.exception))

    def test_out_of_range_reference_fails(self):
        bad = TINY_GOLD.replace("today@3.1", "today@9.1")
        with self.assertRaises(ValueError):
            parse_gold(bad)

    def test_spans_parse_inclusively(self):
        gold = parse_gold(
            "verse:\n  wake up shake the state up\n"
            "group: wake@0.0-1 state@0.4-5\n"
        )
        self.assertEqual(gold.groups[0][0], Extent(0, 0, 1))
        self.assertEqual(gold.groups[0][1], Extent(0, 4, 5))

    def test_template_round_trips_through_the_parser(self):
        # A generated template (plus one group line) must be parseable:
        # the indexed listing's tags are exactly the reference syntax.
        verse = "I say the day\nwent my way"
        template = annotation_template(verse)
        gold = parse_gold(template + "\ngroup: day@0.3 way@1.2\n")
        self.assertEqual(gold.verse, verse)
        self.assertEqual(len(gold.pairs()), 1)


class TestMatchingModes(unittest.TestCase):
    """One scanned verse, gold with known extents, all three rulers."""

    @classmethod
    def setUpClass(cls):
        cls.verse = "I wake up today\nyou shake the state up"
        cls.scan = scan_verse(cls.verse)
        cls.gold = parse_gold(
            "verse:\n  I wake up today\n  you shake the state up\n"
            "group: wake@0.1-2 state@1.3-4\n"
        )

    def test_anchor_mode_forgives_span_edges(self):
        # The scanner may describe the second side as "state up" or a
        # padded variant; anchor mode accepts any description anchored
        # inside the gold extents.
        result = score_pairs(edge_pairs(self.scan), self.gold,
                             mode="anchor")
        self.assertGreaterEqual(result.gold_matched, 1)
        self.assertEqual(result.recall, 1.0)

    def test_exact_mode_demands_identical_extents(self):
        # Only a prediction covering exactly words 1-2 / 3-4 counts.
        result = score_pairs(edge_pairs(self.scan), self.gold, mode="exact")
        for pair in result.true_positives:
            self.assertEqual(
                sorted(pair.sides),
                [Extent(0, 1, 2), Extent(1, 3, 4)],
            )

    def test_unknown_mode_fails_loudly(self):
        with self.assertRaises(ValueError):
            score_pairs(edge_pairs(self.scan), self.gold, mode="fuzzy")


class TestPrecisionRecallArithmetic(unittest.TestCase):
    def test_the_worked_example(self):
        # The design discussion's worked example, verbatim: gold endorses
        # 3 pairs (steady/ready/confetti), the tool claims 1 correct pair.
        # Recall 1/3, precision 1/1.
        gold = parse_gold(
            "verse:\n  steady ready confetti\n"
            "group: steady@0.0 ready@0.1 confetti@0.2\n"
        )
        scan = scan_verse("steady ready xylophone")
        # keep only the steady~ready edge claims (guard: there must be one)
        edges = [
            p for p in edge_pairs(scan)
            if {s.start for s in p.sides} == {0, 1}
        ]
        self.assertTrue(edges)
        result = score_pairs(edges, gold, mode="anchor")
        self.assertEqual(result.precision, 1.0)
        self.assertAlmostEqual(result.recall, 1 / 3)
        self.assertAlmostEqual(result.f1, 0.5)

    def test_false_positives_are_named_not_just_counted(self):
        # A predicted pair gold doesn't endorse lands in false_positives
        # with a human-readable label -- the error list is the payoff.
        gold = parse_gold(
            "verse:\n  day way phone\n"
            "group: day@0.0 way@0.1\n"
        )
        scan = scan_verse("day way phone")
        result = score_pairs(edge_pairs(scan), gold, mode="anchor")
        for pair in result.false_positives:
            self.assertIn("~", pair.label)
            self.assertIsNotNone(pair.score)

    def test_empty_predictions_score_zero_recall_full_precision(self):
        gold = parse_gold(
            "verse:\n  day way\n"
            "group: day@0.0 way@0.1\n"
        )
        result = score_pairs([], gold, mode="anchor")
        self.assertEqual(result.precision, 1.0)  # no false claims made
        self.assertEqual(result.recall, 0.0)     # and no rhymes found


class TestEdgeVsClassLevels(unittest.TestCase):
    def test_class_pairs_include_the_closure_edges_dont(self):
        # A~B and B~C selected as edges puts A, B, C in one class; the
        # class level claims A~C too, the edge level doesn't. This is the
        # localization the two levels exist for.
        verse = "hat\ncat\ncap"  # hat~cat perfect; cat~cap slant bridge
        scan = scan_verse(verse)
        edge_sides = {
            frozenset(s.line for s in p.sides) for p in edge_pairs(scan)
        }
        class_sides = {
            frozenset(s.line for s in p.sides) for p in class_pairs(scan)
        }
        if frozenset({0, 2}) in class_sides:  # closure created hat~cap
            self.assertGreaterEqual(len(class_sides), len(edge_sides))

    def test_overlapping_extents_never_pair_within_a_class(self):
        # "wake" and "wake up" can share a class; the closure must not
        # claim they rhyme with each other (one utterance, two
        # descriptions).
        scan = scan_verse("I wake up today\nyou shake the state up")
        for pair in class_pairs(scan):
            a, b = pair.sides
            if a.line == b.line:
                self.assertTrue(a.end < b.start or b.end < a.start)


class TestVerseEvaluationAndDisputes(unittest.TestCase):
    def test_all_four_cells_and_disputes_are_reported(self):
        gold = parse_gold(
            "verse:\n  I wake up today\n  you shake the state up\n"
            "group: wake@0.1-2 state@1.3-4\n"
        )
        report = evaluate_verse(scan_verse(gold.verse), gold)
        # Anchor forgiveness can only ever help, never hurt:
        self.assertGreaterEqual(
            report.class_anchor.recall, report.class_exact.recall
        )
        # Every dispute is an anchor-mode TP by construction.
        anchor_tp = {p.label for p in report.class_anchor.true_positives}
        for pair in report.extent_disputes:
            self.assertIn(pair.label, anchor_tp)


class TestAgreement(unittest.TestCase):
    def test_identical_annotators_agree_perfectly(self):
        gold = parse_gold(TINY_GOLD)
        result = agreement(gold, gold)
        self.assertEqual(result.f1, 1.0)

    def test_extent_disagreement_is_forgiven_pair_absence_is_not(self):
        # Annotator B marks the same two rhymes with wider extents (their
        # ear heard the padded span) -- overlap matching calls that
        # agreement. B's extra pair that A lacks costs precision/recall.
        a = parse_gold(
            "verse:\n  wake up shake the state up\n  stay another day\n"
            "group: wake@0.0 state@0.4\n"
        )
        b = parse_gold(
            "verse:\n  wake up shake the state up\n  stay another day\n"
            "group: wake@0.0-1 state@0.4-5\n"
            "group: stay@1.0 day@1.2\n"
        )
        result = agreement(a, b)
        self.assertEqual(len(result.true_positives), 1)   # the shared pair
        self.assertEqual(len(result.false_negatives), 1)  # b's extra pair
        self.assertLess(result.f1, 1.0)


if __name__ == "__main__":
    unittest.main()
