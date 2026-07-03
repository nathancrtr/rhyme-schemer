"""Tests for rhyme grouping (Unit 10, Phase 3).

``group_rhymes`` turns pairwise scores into rhyme classes: build a graph whose
edges are rhyming pairs (``best_is_rhyme`` at a threshold) and read off the
**connected components**. Components glue items together transitively -- which
slant rhyme is *not* -- so the interesting cases here are the ones that expose
that choice. Items are variant lists (a word's or span's pronunciations), and
grouping returns component indices back into the input.
"""

import unittest

from rhyme_schemer import (
    group_rhymes,
    pronunciations_for,
    pronunciations_for_span,
)


def _variants(*words):
    """Look up each word's variant list -- the per-item input group_rhymes eats."""
    return [pronunciations_for(w) for w in words]


class TestConnectedComponents(unittest.TestCase):
    def test_perfect_rhymes_group_and_non_rhyme_stands_alone(self):
        # cat/hat/bat are one perfect-rhyme class; orange joins nobody.
        items = _variants("cat", "hat", "bat", "orange")
        self.assertEqual(group_rhymes(items), [[0, 1, 2], [3]])

    def test_slant_rhyme_groups_below_perfect(self):
        # The north-star pair: "lincoln"/"reason" score ~0.83, above the default
        # 0.75 threshold, so grouping must place them together.
        items = _variants("lincoln", "reason")
        self.assertEqual(group_rhymes(items), [[0, 1]])

    def test_components_are_deterministic_and_ordered(self):
        # Members ascending, components ordered by their first member -- the
        # property that lets a caller map classes straight back onto verse order.
        items = _variants("orange", "cat", "purple", "hat")
        # orange(0) and purple(2) rhyme with nobody; cat(1)/hat(3) pair up.
        self.assertEqual(group_rhymes(items), [[0], [1, 3], [2]])


class TestNonTransitivity(unittest.TestCase):
    """The deliberate, debatable choice at the heart of Unit 10.

    "feel"-"fill"-"fell" is a real non-transitive triple: at threshold 0.85 the
    adjacent pairs rhyme (0.916, 0.878) but the ends do not (0.829). Connected
    components merge all three *through* "fill" anyway -- we encode that decision
    here so it can't drift silently.
    """

    WORDS = ("feel", "fill", "fell")

    def test_chain_merges_the_non_rhyming_ends(self):
        items = _variants(*self.WORDS)
        # feel(0) and fell(2) do NOT rhyme at 0.85 on their own...
        self.assertEqual(group_rhymes([items[0], items[2]], threshold=0.85), [[0], [1]])
        # ...yet through fill(1) the whole chain is one class.
        self.assertEqual(group_rhymes(items, threshold=0.85), [[0, 1, 2]])

    def test_raising_the_threshold_breaks_the_chain(self):
        # The threshold is the looseness dial: past 0.916 even feel-fill drops,
        # and the class shatters into singletons. Same items, different modeling.
        items = _variants(*self.WORDS)
        self.assertEqual(group_rhymes(items, threshold=0.92), [[0], [1], [2]])


class TestEdgeCases(unittest.TestCase):
    def test_repeated_word_stays_two_nodes_in_one_class(self):
        # Identity is position, not string: a word repeated at two line ends is
        # two nodes that (perfectly) rhyme, so one class of two indices.
        items = _variants("back", "back")
        self.assertEqual(group_rhymes(items), [[0, 1]])

    def test_oov_item_is_a_surfaced_singleton(self):
        # An out-of-vocabulary word (empty variant list) scores 0 against all,
        # so it is its own component -- present in the output, never dropped.
        items = _variants("cat", "asdfqwer", "hat")
        self.assertEqual(group_rhymes(items), [[0, 2], [1]])

    def test_empty_input_yields_no_components(self):
        self.assertEqual(group_rhymes([]), [])

    def test_threshold_one_groups_only_perfect_rhymes(self):
        # At 1.0 slant rhyme is excluded: cat/hat still merge (identical tails),
        # but lincoln/reason no longer do.
        items = _variants("cat", "hat", "lincoln", "reason")
        self.assertEqual(group_rhymes(items, threshold=1.0), [[0, 1], [2], [3]])


class TestSpanItems(unittest.TestCase):
    def test_a_span_groups_with_a_word(self):
        # Items need not be single words: the multi-word span "for real" is one
        # node, and it rhymes into a class with the word "surreal".
        items = [
            pronunciations_for_span(["for", "real"]),
            pronunciations_for("surreal"),
            pronunciations_for("orange"),
        ]
        self.assertEqual(group_rhymes(items), [[0, 1], [2]])


if __name__ == "__main__":
    unittest.main()
