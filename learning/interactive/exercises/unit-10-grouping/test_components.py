"""Tests for the Unit 10 grouping exercise.

Run from this directory:  python -m unittest test_components -v
"""

import unittest

from components import connected_components, group_rhymes_by_threshold


def as_sets(components):
    return {frozenset(c) for c in components}


class TestConnectedComponents(unittest.TestCase):
    def test_no_edges_means_all_singletons(self):
        self.assertEqual(as_sets(connected_components(4, [])),
                         {frozenset({0}), frozenset({1}), frozenset({2}), frozenset({3})})

    def test_the_hand_trace(self):
        # task.md's worked example.
        comps = connected_components(5, [(0, 1), (3, 4), (1, 2)])
        self.assertEqual(as_sets(comps), {frozenset({0, 1, 2}), frozenset({3, 4})})

    def test_every_node_appears_exactly_once(self):
        comps = connected_components(6, [(0, 5), (2, 3)])
        flat = sorted(n for c in comps for n in c)
        self.assertEqual(flat, list(range(6)))

    def test_edge_order_is_irrelevant(self):
        edges = [(0, 1), (1, 2), (2, 3), (4, 5)]
        expected = as_sets(connected_components(6, edges))
        self.assertEqual(as_sets(connected_components(6, list(reversed(edges)))), expected)

    def test_duplicate_and_self_edges_are_harmless(self):
        comps = connected_components(3, [(0, 1), (0, 1), (2, 2)])
        self.assertEqual(as_sets(comps), {frozenset({0, 1}), frozenset({2})})

    def test_the_bridge_glues_two_good_clusters(self):
        # Percolation, pinned as *chosen* behavior: two clean clusters plus
        # one borderline bridge edge -> one mega-component. This is
        # single-link clustering doing what it always does; ledger items 1
        # and 9 are this test firing on real data.
        clean = [(0, 1), (1, 2), (3, 4), (4, 5)]
        self.assertEqual(len(as_sets(connected_components(6, clean))), 2)
        bridged = clean + [(2, 3)]
        self.assertEqual(as_sets(connected_components(6, bridged)),
                         {frozenset(range(6))})


class TestGroupRhymesByThreshold(unittest.TestCase):
    WORDS = ["cake", "shake", "state", "one", "feeling"]
    SCORES = {
        (0, 1): 1.0,    # cake~shake
        (0, 2): 0.93,   # cake~state
        (1, 2): 0.93,   # shake~state
        (0, 3): 0.55, (1, 3): 0.55, (2, 3): 0.60,
        (0, 4): 0.20, (1, 4): 0.20, (2, 4): 0.20, (3, 4): 0.15,
    }

    def test_grouping_at_a_sensible_threshold(self):
        classes = group_rhymes_by_threshold(self.WORDS, self.SCORES, 0.75)
        self.assertEqual({frozenset(c) for c in classes},
                         {frozenset({"cake", "shake", "state"}),
                          frozenset({"one"}), frozenset({"feeling"})})

    def test_threshold_one_keeps_only_perfect_edges(self):
        classes = group_rhymes_by_threshold(self.WORDS, self.SCORES, 1.0)
        self.assertIn(frozenset({"cake", "shake"}),
                      {frozenset(c) for c in classes})
        self.assertIn(frozenset({"state"}), {frozenset(c) for c in classes})

    def test_non_transitive_triple_is_grouped_anyway(self):
        # THE unit's decision, executable. A~B (0.80) and B~C (0.80) clear
        # the threshold; A~C (0.40) does not. Components still put A, B, C
        # in ONE class: connectivity, not all-pairs agreement, defines
        # membership. The project accepts this knowingly -- the relation
        # isn't transitive but components impose transitivity -- because
        # the alternatives (cliques, correlation clustering, scheme
        # inference) trade different errors, and Unit 14 prices the choice.
        words = ["A", "B", "C"]
        scores = {(0, 1): 0.80, (1, 2): 0.80, (0, 2): 0.40}
        classes = group_rhymes_by_threshold(words, scores, 0.75)
        self.assertEqual({frozenset(c) for c in classes},
                         {frozenset({"A", "B", "C"})})


if __name__ == "__main__":
    unittest.main()
