"""Evaluate the scanner against hand-annotated ground truth (Unit 14).

You can't improve what you can't measure, and rhyme has no perfect ground
truth -- the annotator's ear *is* the instrument. This module is the ruler:
gold annotations in a hand-editable format, precision/recall/F1 over them,
and -- the real payoff -- named error lists, because "P=0.61" doesn't tell
you what to fix and "these eleven pairs are false positives, nine share a
vowel-space edge" does.

**The unit of measurement is the pair.** Humans naturally annotate rhyme in
*groups* ("steady/ready/confetti -- one family"), so the gold format takes
groups; but groups impose transitivity, and Unit 10's lesson was that slant
rhyme doesn't have it. Scoring group-against-group would let one bad bridge
edge condemn an entire merged class. So both gold and predictions are
exploded into the **word pairs they imply**, and pairs are what precision
and recall count: one bad bridge then costs exactly the bad pairs it
creates. Because gold *groups* over-generate pairs the same way components
do (annotating A,B,C as a family implies A~C even if the ear only endorses
A~B and B~C), the format has a ``not:`` directive -- an explicit ear-veto
on one induced pair.

**Two prediction levels are scored against the same gold.** The scanner
makes two claims of different strengths: its *edges* (``matches`` -- pairs
``select_matches`` chose) and its *classes* (``groups`` -- the transitive
closure the renderer actually paints). Scoring both localizes failure:
high edge precision with low class precision means the pairwise judgments
are sound and the component *glue* is the problem (tuning-ledger items 1
and 9); low edge precision means the kernel or its thresholds (items 2-4).

**Extent matching is a parameter, deliberately.** The scanner predicts
spans; gold names word extents; when do they agree? ``anchor`` mode counts
a predicted side as matching a gold side when the predicted *anchor word*
falls inside the gold extent -- forgiving about span edges (ledger item 6
says exact extents are flow-dependent), strict about what the rhyme is
anchored to. ``exact`` mode demands identical extents. The corpus problem
is false positives, so forgiveness is under suspicion: reports carry both
modes side by side, and the pairs on which they *disagree* are themselves
a diagnostic -- each one is an extent-sloppiness case to inspect.

The harness is also its own inter-annotator agreement tool: agreement is
just one annotator's gold evaluated as if it were the other's predictions
(``overlap`` matching, since two honest ears may pick different extents
for the same percept). Rhyme is subjective; partial agreement is a fact
about the task, and the agreement number is the ceiling any scanner score
should be read against.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations

from .scan import Candidate, Match, VerseScan, tokenize_verse

# --- Gold annotations: the format and its parser -----------------------------

# One side of a gold rhyme: word(s) at line L, words W1..W2, written
# "word@L.W" or "word@L.W1-W2" (the leading word text is optional but
# checked against the verse -- a cheap typo guard for hand-edited files).
_REF_RE = re.compile(
    r"^(?:(?P<text>[A-Za-z'’-]+)@)?"
    r"(?P<line>\d+)\.(?P<start>\d+)(?:-(?P<end>\d+))?$"
)


@dataclass(frozen=True, order=True)
class Extent:
    """A gold-side location: words ``start``..``end`` (inclusive) on ``line``.

    Deliberately *positional*, not textual: the same word can appear many
    times in a verse ("steady" twice, "rapping" four times in Poe), and a
    rhyme annotation is a claim about one specific utterance of it.
    """

    line: int
    start: int
    end: int

    def __str__(self) -> str:
        span = f"{self.start}" if self.start == self.end \
            else f"{self.start}-{self.end}"
        return f"@{self.line}.{span}"


# A pair is an unordered set of two extents; sorting gives a canonical form
# so the same pair written in either order compares equal.
Pair = tuple[Extent, Extent]


def _pair(a: Extent, b: Extent) -> Pair:
    return (a, b) if a <= b else (b, a)


@dataclass(frozen=True)
class Gold:
    """A verse plus one annotator's ear: rhyme groups and pair vetoes."""

    verse: str
    groups: tuple[tuple[Extent, ...], ...]
    vetoes: tuple[Pair, ...]

    def pairs(self) -> set[Pair]:
        """The pairs this annotation endorses: groups exploded, vetoes cut.

        This is where "annotate groups, score pairs" becomes mechanical:
        every unordered pair within a group is an endorsed rhyme unless a
        ``not:`` line vetoed it.
        """
        endorsed = {
            _pair(a, b)
            for group in self.groups
            for a, b in combinations(group, 2)
        }
        return endorsed - set(self.vetoes)


def _parse_ref(token: str, words: list[list[str]], where: str) -> Extent:
    """Parse one ``word@L.W`` reference, sanity-checking against the verse."""
    m = _REF_RE.match(token)
    if not m:
        raise ValueError(f"{where}: can't parse reference {token!r}")
    line = int(m.group("line"))
    start = int(m.group("start"))
    end = int(m.group("end") or start)
    if line >= len(words) or end >= len(words[line]) or start > end:
        raise ValueError(f"{where}: {token!r} is outside the verse")
    text = m.group("text")
    if text is not None:
        actual = words[line][start]
        if text.lower() != actual.lower():
            raise ValueError(
                f"{where}: {token!r} says {text!r} but word "
                f"{line}.{start} is {actual!r} -- index slip?"
            )
    return Extent(line=line, start=start, end=end)


def parse_gold(text: str) -> Gold:
    """Parse a gold annotation file.

    Format, line by line: ``#`` comments and blanks are skipped; a
    ``verse:`` line starts the verse block (each following *indented* line
    is one verse line, common indentation stripped); ``group:`` lists two
    or more word references that rhyme as a family; ``not:`` names exactly
    two references whose induced pair the annotator's ear rejects. Word
    references are ``word@L.W`` or spans ``word@L.W1-W2`` -- the text
    before ``@`` is optional, but when present must match the word at that
    position, so a mis-typed index fails loudly at parse time instead of
    silently scoring the wrong word.
    """
    verse_lines: list[str] = []
    directives: list[tuple[str, str]] = []
    in_verse = False
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("verse:"):
            in_verse = True
            continue
        if raw[:1].isspace() and in_verse:
            verse_lines.append(raw)
            continue
        in_verse = False
        key, _, rest = raw.partition(":")
        if key not in ("group", "not"):
            raise ValueError(f"unrecognized line: {raw!r}")
        directives.append((key, rest.strip()))

    if not verse_lines:
        raise ValueError("no verse: block found")
    indent = min(len(line) - len(line.lstrip()) for line in verse_lines)
    verse = "\n".join(line[indent:] for line in verse_lines)
    words = tokenize_verse(verse)

    groups: list[tuple[Extent, ...]] = []
    vetoes: list[Pair] = []
    for key, rest in directives:
        where = f"{key}: {rest}"
        refs = [_parse_ref(token, words, where) for token in rest.split()]
        if key == "group":
            if len(refs) < 2:
                raise ValueError(f"{where}: a group needs >= 2 members")
            groups.append(tuple(refs))
        else:
            if len(refs) != 2:
                raise ValueError(f"{where}: 'not' takes exactly 2 members")
            vetoes.append(_pair(*refs))
    return Gold(verse=verse, groups=tuple(groups), vetoes=tuple(vetoes))


def annotation_template(verse: str) -> str:
    """A blank gold file for ``verse``, with every word indexed.

    The indexed listing makes hand-annotation mechanical: find the word,
    copy its ``word@L.W`` tag into a ``group:`` line. The template contains
    *no* scanner output on purpose -- gold seeded from the tool under test
    inherits the tool's blind spots, and the whole point of the ruler is
    independence from the thing it measures.
    """
    lines = [
        "# Gold rhyme annotation. Fill in group:/not: lines below.",
        "# group: two or more word@L.W refs that rhyme as one family",
        "#        (spans allowed: word@L.W1-W2 covers words W1..W2)",
        "# not:   veto one pair implied by a group (A B C endorses A~C;",
        "#        if your ear rejects exactly that pair, veto it here)",
        "# Same-word repetition is not rhyme (rime riche): don't annotate",
        "# door~door; do annotate door~lore.",
        "#",
        "# Indexed words:",
    ]
    for line_no, words in enumerate(tokenize_verse(verse)):
        tags = "  ".join(
            f"{word}@{line_no}.{w}" for w, word in enumerate(words)
        )
        lines.append(f"#   {tags}")
    lines.append("")
    lines.append("verse:")
    lines.extend(f"  {line}" for line in verse.splitlines())
    lines.append("")
    lines.append("# group: ...")
    lines.append("")
    return "\n".join(lines)


# --- Matching: when does a predicted pair hit a gold pair? --------------------


def _side_matches(pred: Extent, anchor: int | None, gold: Extent,
                  mode: str) -> bool:
    """Does one predicted side count as the same rhyme-side as a gold side?

    - ``anchor``: the predicted anchor word must fall inside the gold
      extent. Span-edge disagreement is forgiven (a padded "shake the"
      still matches gold "shake"); anchoring the rhyme to a different beat
      is not ("the whole state" does not match gold "shake").
    - ``exact``: the extents must be identical, edge for edge.
    - ``overlap``: any shared word position. Symmetric and anchor-free,
      which is what inter-annotator agreement needs (a gold extent has no
      anchor to test).
    """
    if pred.line != gold.line:
        return False
    if mode == "exact":
        return pred.start == gold.start and pred.end == gold.end
    if mode == "anchor":
        return gold.start <= anchor <= gold.end
    if mode == "overlap":
        return pred.start <= gold.end and gold.start <= pred.end
    raise ValueError(f"unknown matching mode {mode!r}")


def _pair_matches(pred: tuple[Extent, Extent],
                  anchors: tuple[int | None, int | None],
                  gold: Pair, mode: str) -> bool:
    """A predicted pair hits a gold pair if its sides match both gold
    sides, one-to-one, in either order."""
    (p1, p2), (a1, a2) = pred, anchors
    g1, g2 = gold
    return (
        (_side_matches(p1, a1, g1, mode) and _side_matches(p2, a2, g2, mode))
        or
        (_side_matches(p1, a1, g2, mode) and _side_matches(p2, a2, g1, mode))
    )


# --- Scoring ------------------------------------------------------------------


@dataclass(frozen=True)
class PredictedPair:
    """One pair the scanner claims, in a form the matcher can test.

    ``score`` is the match score for edge-level pairs and ``None`` for
    class-level pairs (the closure doesn't score the pairs it implies --
    that asymmetry is worth keeping visible in error reports). ``label``
    renders the pair for humans.
    """

    sides: tuple[Extent, Extent]
    anchors: tuple[int | None, int | None]  # None when a human is the
    label: str                              # predictor (agreement mode)
    score: float | None = None


def _extent(candidate: Candidate) -> Extent:
    return Extent(candidate.line, candidate.start, candidate.end)


def _predicted(a: Candidate, b: Candidate,
               score: float | None) -> PredictedPair:
    return PredictedPair(
        sides=(_extent(a), _extent(b)),
        # The anchor always lives in a candidate's first word.
        anchors=(a.start, b.start),
        label=f"{' '.join(a.words)}{_extent(a)} ~ "
              f"{' '.join(b.words)}{_extent(b)}",
        score=score,
    )


def edge_pairs(scan: VerseScan) -> list[PredictedPair]:
    """The scanner's direct claims: one pair per selected match."""
    return [_predicted(m.a, m.b, m.score) for m in scan.matches]


def class_pairs(scan: VerseScan) -> list[PredictedPair]:
    """The claims the *picture* makes: every pair implied by a rhyme class.

    This is the transitive closure the renderer paints, exploded the same
    way gold groups are. Pairs of overlapping same-line extents ("wake"
    and "wake up" sharing a class) are skipped: those are two descriptions
    of one utterance, not a claim that a sound rhymes with itself.
    """
    pairs = []
    for group in scan.groups:
        for a, b in combinations(group, 2):
            if (a.line == b.line
                    and a.start <= b.end and b.start <= a.end):
                continue
            pairs.append(_predicted(a, b, None))
    return pairs


@dataclass(frozen=True)
class Evaluation:
    """Precision/recall/F1 plus the lists that make them actionable.

    ``true_positives`` and ``false_positives`` partition the predicted
    pairs; ``false_negatives`` are the gold pairs nothing matched;
    ``gold_matched`` counts the gold pairs something *did* match. The two
    directions count different things on purpose -- precision counts
    predicted pairs (two predictions hitting one gold pair are two correct
    claims), recall counts gold pairs (that same gold pair is still just
    one rhyme found). The lists are the point: error analysis reads them,
    the numbers only summarize them.
    """

    true_positives: tuple[PredictedPair, ...]
    false_positives: tuple[PredictedPair, ...]
    false_negatives: tuple[Pair, ...]
    gold_matched: int

    @property
    def precision(self) -> float:
        claimed = len(self.true_positives) + len(self.false_positives)
        return len(self.true_positives) / claimed if claimed else 1.0

    @property
    def recall(self) -> float:
        gold = self.gold_matched + len(self.false_negatives)
        return self.gold_matched / gold if gold else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclass(frozen=True)
class VerseEvaluation:
    """The full measurement for one verse: two levels under two rulers.

    - ``edge_*``: the scanner's direct pair claims (``matches``) --
      evaluates the kernel + selection.
    - ``class_*``: the pairs implied by the painted classes (transitive
      closure) -- evaluates what the user actually sees. The gap between
      edge and class precision is the price of the component glue.
    - ``*_anchor`` vs ``*_exact``: the forgiving and strict extent rulers.
      ``extent_disputes`` lists the pairs the rulers disagree on -- each
      one is a predicted pair that matched gold only because anchor mode
      forgave its span edges. If this list fills with junk, the forgiving
      ruler is lying and ``exact`` should become the headline.
    """

    edge_anchor: Evaluation
    edge_exact: Evaluation
    class_anchor: Evaluation
    class_exact: Evaluation
    extent_disputes: tuple[PredictedPair, ...]


def evaluate_verse(scan: VerseScan, gold: Gold) -> VerseEvaluation:
    """Score one scanned verse against one gold annotation, every way."""
    edges, classes = edge_pairs(scan), class_pairs(scan)
    edge_anchor = score_pairs(edges, gold, mode="anchor")
    edge_exact = score_pairs(edges, gold, mode="exact")
    class_anchor = score_pairs(classes, gold, mode="anchor")
    class_exact = score_pairs(classes, gold, mode="exact")
    exact_tp = {pair.label for pair in class_exact.true_positives}
    disputes = tuple(
        pair for pair in class_anchor.true_positives
        if pair.label not in exact_tp
    )
    return VerseEvaluation(
        edge_anchor=edge_anchor,
        edge_exact=edge_exact,
        class_anchor=class_anchor,
        class_exact=class_exact,
        extent_disputes=disputes,
    )


def agreement(a: Gold, b: Gold) -> Evaluation:
    """Inter-annotator agreement: annotator ``a`` scored against ``b``.

    Agreement is just evaluation with a human in the prediction seat:
    ``a``'s endorsed pairs are matched against ``b``'s under ``overlap``
    (two honest ears can pick different extents for one percept, and
    neither annotation carries an anchor to be strict about). The F1 is
    symmetric even though precision/recall swap when the arguments do.
    Rhyme is subjective; this number is the *ceiling* any scanner score
    should be read against -- a tool cannot agree with an ear more than
    two ears agree with each other.
    """
    predicted = [
        PredictedPair(sides=pair, anchors=(None, None),
                      label=f"{pair[0]} ~ {pair[1]}")
        for pair in sorted(a.pairs())
    ]
    return score_pairs(predicted, b, mode="overlap")


def score_pairs(predicted: list[PredictedPair], gold: Gold,
                mode: str = "anchor") -> Evaluation:
    """Score predicted pairs against gold, under one matching mode."""
    gold_pairs = sorted(gold.pairs())
    tp, fp = [], []
    matched_gold: set[Pair] = set()
    for pair in predicted:
        hits = [
            g for g in gold_pairs
            if _pair_matches(pair.sides, pair.anchors, g, mode)
        ]
        if hits:
            tp.append(pair)
            matched_gold.update(hits)
        else:
            fp.append(pair)
    fn = tuple(g for g in gold_pairs if g not in matched_gold)
    return Evaluation(
        true_positives=tuple(tp),
        false_positives=tuple(fp),
        false_negatives=fn,
        gold_matched=len(matched_gold),
    )
