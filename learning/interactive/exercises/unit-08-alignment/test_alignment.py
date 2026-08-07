"""Tests for the Unit 8 alignment exercise.

Run from this directory:  python -m unittest test_alignment -v

House style: structural properties (range, symmetry, the no-gap diagonal)
plus pinned examples whose failure localizes the bug -- diagonal tests catch
recurrence tie-breaking, forced-gap tests catch the backtrace, parity tests
catch scoring.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from alignment import GAP_PENALTY, _syllable_similarity, align_tails, score_alignment
from rhyme_schemer import Stress, Syllable, pronunciation_for
from rhyme_schemer.rhyme import rhyme_tail


def syl(onset, nucleus, coda, stress=Stress.PRIMARY):
    return Syllable(onset=tuple(onset), nucleus=nucleus, coda=tuple(coda), stress=stress)


# The task.md hand-worked example: [EH, IY] vs [EH, AH, IY].
TAIL_2 = (syl(("S",), "EH", ()), syl(("T",), "IY", (), Stress.UNSTRESSED))
TAIL_3 = (syl(("B",), "EH", ()), syl(("D",), "AH", (), Stress.UNSTRESSED),
          syl(("T",), "IY", (), Stress.UNSTRESSED))


class TestAlignmentStructure(unittest.TestCase):
    def test_equal_length_tails_stay_on_the_diagonal(self):
        # No gaps when lengths match: every column has both sides. This is
        # the tie-breaking rule doing its job (diagonal preferred).
        for word_a, word_b in (("reason", "season"), ("cat", "hat"), ("national", "rational")):
            ta = rhyme_tail(pronunciation_for(word_a))
            tb = rhyme_tail(pronunciation_for(word_b))
            self.assertEqual(len(ta), len(tb), "precondition: equal tails")
            columns = align_tails(ta, tb)
            self.assertEqual(len(columns), len(ta))
            for sa, sb in columns:
                self.assertIsNotNone(sa)
                self.assertIsNotNone(sb)

    def test_column_count_is_bounded(self):
        columns = align_tails(TAIL_2, TAIL_3)
        self.assertGreaterEqual(len(columns), 3)   # at least max(m, n)
        self.assertLessEqual(len(columns), 5)      # at most m + n

    def test_columns_preserve_tail_order(self):
        # Reading only A's side of the columns gives tail_a back, in order
        # (and likewise for B) -- the backtrace must not scramble or drop.
        columns = align_tails(TAIL_2, TAIL_3)
        self.assertEqual(tuple(sa for sa, _ in columns if sa is not None), TAIL_2)
        self.assertEqual(tuple(sb for _, sb in columns if sb is not None), TAIL_3)

    def test_score_is_symmetric_and_in_range(self):
        pairs = [(TAIL_2, TAIL_3), (TAIL_2, TAIL_2), (TAIL_3, TAIL_3)]
        for ta, tb in pairs:
            s_ab = score_alignment(align_tails(ta, tb))
            s_ba = score_alignment(align_tails(tb, ta))
            self.assertAlmostEqual(s_ab, s_ba, places=9)
            self.assertGreaterEqual(s_ab, 0.0)
            self.assertLessEqual(s_ab, 1.0)


class TestHandWorkedExample(unittest.TestCase):
    def test_the_extra_syllable_gets_the_gap(self):
        # task.md's table: EH~EH, gap~AH, IY~IY.
        columns = align_tails(TAIL_2, TAIL_3)
        self.assertEqual(len(columns), 3)
        self.assertEqual((columns[0][0].nucleus, columns[0][1].nucleus), ("EH", "EH"))
        self.assertIsNone(columns[1][0])           # the gap is on A's side...
        self.assertEqual(columns[1][1].nucleus, "AH")  # ...opposite the extra AH
        self.assertEqual((columns[2][0].nucleus, columns[2][1].nucleus), ("IY", "IY"))

    def test_gap_columns_score_zero(self):
        columns = align_tails(TAIL_2, TAIL_3)
        matched = [c for c in columns if c[0] is not None and c[1] is not None]
        expected = sum(_syllable_similarity(sa, sb) for sa, sb in matched) / len(columns)
        self.assertAlmostEqual(score_alignment(columns), expected, places=9)


class TestParityWithUnit6(unittest.TestCase):
    def test_equal_length_scores_match_position_by_position(self):
        # Alignment must GENERALIZE Unit 6, not change it: on equal-length
        # tails the score equals the plain positional average.
        for word_a, word_b in (("reason", "season"), ("lincoln", "reason"), ("cat", "hat")):
            ta = rhyme_tail(pronunciation_for(word_a))
            tb = rhyme_tail(pronunciation_for(word_b))
            positional = sum(
                _syllable_similarity(sa, sb) for sa, sb in zip(ta, tb)
            ) / len(ta)
            self.assertAlmostEqual(score_alignment(align_tails(ta, tb)), positional, places=9)

    def test_identical_tails_score_one(self):
        ta = rhyme_tail(pronunciation_for("spaghetti"))
        self.assertAlmostEqual(score_alignment(align_tails(ta, ta)), 1.0, places=9)


class TestPinnedExamples(unittest.TestCase):
    def test_hypnotize_eyes_gaps_kill_the_rhyme(self):
        # 3-syllable tail vs 1: the final columns match perfectly (AY-Z), but
        # two gap columns score 0, and the average lands at exactly 1/3 of
        # the final column's score. Gaps are a real rhyme cost.
        ta = rhyme_tail(pronunciation_for("hypnotize"))
        tb = rhyme_tail(pronunciation_for("eyes"))
        columns = align_tails(ta, tb)
        gaps = [c for c in columns if c[0] is None or c[1] is None]
        self.assertEqual(len(gaps), 2)
        self.assertAlmostEqual(score_alignment(columns), 1.0 / 3.0, places=9)

    def test_gap_penalty_is_in_the_working_band(self):
        # The band the module docstring promises: above a near-vowel
        # substitution, below a far one.
        from rhyme_schemer.features import vowel_distance
        self.assertGreater(GAP_PENALTY, vowel_distance("EH", "IH"))   # near
        self.assertLess(GAP_PENALTY, vowel_distance("IY", "AA"))      # far


if __name__ == "__main__":
    unittest.main()
