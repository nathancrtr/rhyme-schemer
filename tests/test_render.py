"""Tests for the Unit 12 renderer (``rhyme_schemer.render``).

The fixtures are the project's *safe corpus*: an original verse engineered to
contain every phenomenon the renderer must draw (a multisyllabic chain, an
abutting compound, nested mono/multi class membership, an OOV word), plus
public-domain poetry with dense internal rhyme. Commercial lyrics are
deliberately absent -- single iconic lines aside, they don't belong in
fixtures.

Most assertions target ``plan_verse``: the plan is where every rendering
*policy* lives (fill ownership, ticks, compound rules, tooltips, slots), so
that is where behavior is pinned. The HTML and ANSI emitters get structural
smoke tests -- the plan decided what to draw; the emitters only owe us
faithful text and well-formed markup.
"""

from __future__ import annotations

import re
import unittest

from rhyme_schemer.render import plan_verse, render_html, render_terminal
from rhyme_schemer.scan import scan_verse

# Original verse, written for this repo (see the engineered phenomena listed
# in the module docstring).
ORIGINAL = """\
My palms are steady, my arms are ready
I wake up, shake the whole state up
I face the day and make my way
I'm nervous, but my verses stay steady
My Coogi sweater keeps me warm and clever
The plan spins round like fresh confetti
Whatever the weather, I hold it together
Already ready, sharp as a machete"""

# Public domain: Poe, "The Raven" (1845), stanza 1 -- dense same-line
# internal rhyme, and the corpus's deepest compound: a three-beat chain
# whose beats are one perfect match (tapping ~ rapping, 1.000) plus two
# threshold-huggers (there ~ one 0.826, came a ~ gently 0.825). It renders
# fine, and it also documents a real property of chaining: ``_abuts`` is
# purely positional, so marginal selected matches fuse as readily as strong
# ones -- chaining amplifies whatever precision debt selection lets through.
POE = """\
Once upon a midnight dreary, while I pondered, weak and weary,
Over many a quaint and curious volume of forgotten lore,
While I nodded, nearly napping, suddenly there came a tapping,
As of some one gently rapping, rapping at my chamber door.
'Tis some visitor, I muttered, tapping at my chamber door,
Only this and nothing more."""


def _word_paints(plan):
    """(line, word text) -> WordPaint for every word cell in the plan."""
    paints = {}
    for line_index, cells in enumerate(plan.lines):
        word_index = 0
        for cell in cells:
            if cell.paint is not None:
                paints[(line_index, word_index)] = (cell.text, cell.paint)
                word_index += 1
    return paints


class TestPlanVerse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scan = scan_verse(ORIGINAL)
        cls.plan = plan_verse(ORIGINAL, cls.scan)
        cls.paints = _word_paints(cls.plan)

    def test_cells_reproduce_the_verse_exactly(self):
        # The renderer's core contract: punctuation, case, and spacing all
        # survive the round trip through tokenization.
        for raw, cells in zip(ORIGINAL.splitlines(), self.plan.lines):
            self.assertEqual("".join(cell.text for cell in cells), raw)

    def test_compound_rule_spans_both_fused_sides(self):
        # Line 0: [palms are steady] ~ [arms are ready] is the engineered
        # compound. Both three-word extents carry the same rule id, and the
        # unfused words around them carry none.
        line0 = {
            w: paint for (line, w), (_, paint) in self.paints.items()
            if line == 0
        }
        left = {line0[w].compound for w in (1, 2, 3)}
        right = {line0[w].compound for w in (5, 6, 7)}
        self.assertEqual(len(left), 1)
        self.assertEqual(left, right)
        self.assertIsNotNone(left.pop())
        self.assertIsNone(line0[0].compound)  # "My"
        self.assertIsNone(line0[4].compound)  # "my"

    def test_nested_membership_becomes_fill_plus_ticks(self):
        # "wake" sits in the EY class and inside the "wake up ~ state up"
        # class: one membership owns the fill, the other must survive as a
        # tick rather than vanish.
        text, paint = self.paints[(1, 1)]
        self.assertEqual(text, "wake")
        self.assertIsNotNone(paint.fill)
        self.assertTrue(paint.ticks)
        self.assertNotIn(paint.fill, paint.ticks)

    def test_fill_goes_to_the_best_scoring_match(self):
        # Fill ownership is by score: for every painted word, its fill class
        # must be the class of the top-scoring covering candidate, which by
        # construction is first in its tooltip.
        for (line, w), (text, paint) in self.paints.items():
            if paint.fill is None or paint.oov:
                continue
            first_line = paint.tooltip.splitlines()[0]
            self.assertIn(f"class {paint.fill},", first_line)

    def test_guessed_word_is_marked_with_provenance(self):
        # Unit 13's milestone word: "Coogi" was skip-and-flagged until the
        # G2P chain gave it a letter-to-sound guess. It now scans like any
        # word but must carry its provenance -- the guess marker and a
        # tooltip line saying the pronunciation is not dictionary fact.
        text, paint = self.paints[(4, 1)]
        self.assertEqual(text, "Coogi")
        self.assertFalse(paint.oov)
        self.assertEqual(paint.guessed, "letter-to-sound")
        self.assertIn("guessed", paint.tooltip)
        self.assertIn(("Coogi", "letter-to-sound"), self.plan.guessed)
        self.assertNotIn("Coogi", self.plan.oov)

    def test_unvoiceable_word_is_flagged_not_classed(self):
        # "brrr" fails the whole chain: still the old skip-and-flag path.
        plan = plan_verse("brrr it's cold\nmy story told")
        paints = _word_paints(plan)
        text, paint = paints[(0, 0)]
        self.assertEqual(text, "brrr")
        self.assertTrue(paint.oov)
        self.assertIsNone(paint.fill)
        self.assertIn("brrr", plan.oov)
        self.assertIn("unknown", paint.tooltip)

    def test_slots_go_to_the_largest_classes(self):
        # The eight palette slots belong to the eight largest classes;
        # overflow classes fold to the neutral wash (slot None). Slots are
        # never duplicated or generated.
        slotted = [e for e in self.plan.classes if e.slot is not None]
        overflow = [e for e in self.plan.classes if e.slot is None]
        self.assertEqual(len(slotted), min(8, len(self.plan.classes)))
        self.assertEqual(
            len({e.slot for e in slotted}), len(slotted)
        )
        if overflow:
            smallest_slotted = min(len(e.members) for e in slotted)
            largest_folded = max(len(e.members) for e in overflow)
            self.assertGreaterEqual(smallest_slotted, largest_folded)

    def test_tooltip_carries_the_receipts(self):
        # Every covering match appears: span, partner, class, and score.
        _, paint = self.paints[(1, 1)]  # "wake"
        self.assertRegex(paint.tooltip, r"'wake' ~ '\w+'")
        self.assertRegex(paint.tooltip, r"class \d+, \d\.\d\d")


class TestPoeCompounds(unittest.TestCase):
    def test_three_beat_compound_is_ruled_end_to_end(self):
        # "there came a tapping" ~ "one gently rapping": the corpus's
        # deepest chain. Every word of both extents shares one rule id.
        # Pins current behavior: the two passenger beats survive because
        # chaining has no score gate (tuning ledger item 8); if a per-beat
        # floor lands, this compound should shrink to tapping ~ rapping
        # and this test must change with it.
        plan = plan_verse(POE)
        paints = _word_paints(plan)
        left = [paints[(2, w)] for w in (6, 7, 8, 9)]
        right = [paints[(3, w)] for w in (3, 4, 5)]
        self.assertEqual([t for t, _ in left], ["there", "came", "a",
                                                "tapping"])
        self.assertEqual([t for t, _ in right], ["one", "gently", "rapping"])
        ids = {p.compound for _, p in left} | {p.compound for _, p in right}
        self.assertEqual(len(ids), 1)
        self.assertIsNotNone(ids.pop())

    def test_conflicting_compound_draws_no_fragment(self):
        # [many a quaint] ~ [suddenly there] loses "there" to the stronger
        # three-beat chain. Rules are all-or-nothing: rather than a dangling
        # fragment under "suddenly" alone (asserting a fusion the picture
        # can't show), the losing compound draws no rule at all -- on
        # either side.
        plan = plan_verse(POE)
        paints = _word_paints(plan)
        text, paint = paints[(2, 5)]
        self.assertEqual(text, "suddenly")
        self.assertIsNone(paint.compound)
        for w in (1, 2, 3):  # "many a quaint" on line 1
            self.assertIsNone(paints[(1, w)][1].compound)


class TestHtmlEmitter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = render_html(ORIGINAL)

    def test_words_and_style_are_present(self):
        self.assertIn("<style>", self.html)
        self.assertIn("rhyme-scheme", self.html)
        self.assertIn("steady", self.html)
        self.assertIn('class="cmp"', self.html)   # a compound rule
        self.assertIn('class="ticks"', self.html)  # a secondary membership
        self.assertIn("title=", self.html)         # receipts survive

    def test_guessed_marked_and_legend_lists_it(self):
        # "Coogi" gets the dashed guess marker and a provenance legend line.
        self.assertIn('class="w gsd"', self.html)
        self.assertIn("pronunciation guessed", self.html)
        self.assertIn("Coogi (letter-to-sound)", self.html)

    def test_unvoiceable_marked_and_legend_lists_it(self):
        html = render_html("brrr it's cold\nmy story told")
        self.assertIn('class="w oov"', html)
        self.assertIn("unknown words", html)

    def test_legend_has_one_row_per_class(self):
        plan = plan_verse(ORIGINAL)
        self.assertEqual(
            self.html.count('<span class="sw'), len(plan.classes)
        )

    def test_html_is_escaped(self):
        html = render_html('Q&A day\nsay "hey"')
        self.assertIn("Q&amp;A", html)
        self.assertNotIn('say "hey"', html)  # quotes fine, & must escape


class TestTerminalEmitter(unittest.TestCase):
    def test_stripped_output_reproduces_the_verse(self):
        out = render_terminal(ORIGINAL)
        stripped = re.sub(r"\x1b\[[0-9;]*m", "", out)
        for raw in ORIGINAL.splitlines():
            self.assertIn(raw, stripped)

    def test_ansi_fills_and_legend_present(self):
        out = render_terminal(ORIGINAL)
        self.assertIn("\x1b[48;2;", out)   # truecolor fill
        self.assertIn("\x1b[4m", out)      # compound underline
        self.assertIn("class 0:", out)
        self.assertIn("Coogi", out)


if __name__ == "__main__":
    unittest.main()
