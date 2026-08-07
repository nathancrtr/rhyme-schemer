"""Unit 10 exercise -- connected components via union-find.

You are building the grouping step: pairwise rhyme verdicts (edges) in,
rhyme classes (components) out. Two functions to complete, marked
# YOUR CODE HERE. The graphs-and-union-find companion essay walks the whole
data structure by hand; task.md has the worked trace.

Contract (matching rhyme.py's `connected_components`): nodes are the
integers 0..count-1, edges are (a, b) index pairs, and the result is a list
of components, each a list of node indices -- every node appears in exactly
one component, singletons included.
"""

from __future__ import annotations


def connected_components(count: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    """Group 0..count-1 into components under the given edges."""
    # The union-find forest: parent[x] points at some node in x's component;
    # a node that points at itself is its component's representative.
    parent = list(range(count))

    def find(x: int) -> int:
        # YOUR CODE HERE: follow parent pointers until you reach a node that
        # is its own parent, and return it. (Optional but classic: path
        # compression -- repoint nodes you pass directly at the root.)
        raise NotImplementedError

    def union(a: int, b: int) -> None:
        # YOUR CODE HERE: find both representatives; if they differ, make
        # one point at the other. One line of consequence, total merge.
        raise NotImplementedError

    for a, b in edges:
        union(a, b)

    # Collect: nodes sharing a representative share a component.
    groups: dict[int, list[int]] = {}
    for node in range(count):
        groups.setdefault(find(node), []).append(node)
    return list(groups.values())


def group_rhymes_by_threshold(
    words: list[str],
    scores: dict[tuple[int, int], float],
    threshold: float,
) -> list[list[str]]:
    """Rhyme classes for `words`, given pairwise scores and a threshold.

    `scores` maps (i, j) index pairs (i < j) to a similarity in [0, 1].
    An edge exists wherever the score clears the threshold; classes are the
    connected components, returned as word lists (all words appear;
    singletons included).
    """
    # YOUR CODE HERE: build the edge list from `scores` and `threshold`,
    # call connected_components, and map index-components to word lists.
    raise NotImplementedError
