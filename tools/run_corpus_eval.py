"""Run the scanner over a directory of gold files and report the damage.

Unit 14's harness scores one verse at a time; this is the corpus driver on
top of it -- micro-averaged precision/recall/F1 across every verse, at both
levels (edges, classes) under both extent rulers (anchor, exact), plus the
error lists that say what to fix.

Micro-averaging (pool all pairs, then score) rather than macro-averaging
(score each verse, then mean) is deliberate: a four-line verse and a
thirty-line verse make very different numbers of claims, and the pooled
count is the one that answers "how wrong is the scanner per rhyme".

Point it at gold files produced by ``mcflow_to_gold.py``. Those contain
commercial lyric text, so keep both the gold and any report out of the repo.
"""

from __future__ import annotations

import argparse
import time
from collections import Counter
from pathlib import Path

from rhyme_schemer.evaluate import (
    Gold,
    class_pairs,
    edge_pairs,
    parse_gold,
    score_pairs,
)
from rhyme_schemer.scan import scan_verse


def _say(gold: Gold, pair) -> str:
    """Render a gold pair as its words, so error lists are readable.

    ``Extent`` is positional by design (see evaluate.py), which makes it
    unreadable in a report; look the words back up out of the verse.
    """
    lines = [line.split() for line in gold.verse.splitlines()]

    def words(extent) -> str:
        row = lines[extent.line] if extent.line < len(lines) else []
        return " ".join(row[extent.start:extent.end + 1]) or "?"

    a, b = pair
    return f"{words(a)}{a} ~ {words(b)}{b}"


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall else 0.0)
    return precision, recall, f1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold_dir", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--max-lines", type=int, default=0,
                        help="skip verses longer than this (0 = no limit)")
    parser.add_argument("--errors", type=int, default=15,
                        help="how many example errors to print")
    args = parser.parse_args()

    files = sorted(args.gold_dir.glob("*.gold"))
    if args.limit:
        files = files[:args.limit]

    # Pooled counts, keyed by (level, ruler).
    pools: dict[tuple[str, str], Counter] = {
        (level, ruler): Counter()
        for level in ("edge", "class") for ruler in ("anchor", "exact")
    }
    false_positives: list[str] = []
    false_negatives: list[str] = []
    verses = words = guessed = oov = 0
    gold_pairs_total = 0
    started = time.time()

    for path in files:
        try:
            gold: Gold = parse_gold(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            print(f"skip {path.name}: {exc}")
            continue
        line_count = len(gold.verse.splitlines())
        if args.max_lines and line_count > args.max_lines:
            continue

        scan = scan_verse(gold.verse)
        verses += 1
        words += sum(len(line.split()) for line in gold.verse.splitlines())
        guessed += len(scan.guessed)
        oov += len(scan.oov)
        gold_pairs_total += len(gold.pairs())

        for level, predicted in (("edge", edge_pairs(scan)),
                                 ("class", class_pairs(scan))):
            for ruler in ("anchor", "exact"):
                ev = score_pairs(predicted, gold, mode=ruler)
                pools[(level, ruler)]["tp"] += len(ev.true_positives)
                pools[(level, ruler)]["fp"] += len(ev.false_positives)
                pools[(level, ruler)]["fn"] += len(ev.false_negatives)
                if level == "class" and ruler == "anchor":
                    for pair in ev.false_positives[:3]:
                        false_positives.append(f"{path.stem}: {pair.label}")
                    for pair in ev.false_negatives[:3]:
                        false_negatives.append(
                            f"{path.stem}: {_say(gold, pair)}")

    elapsed = time.time() - started
    print(f"\n{'='*66}")
    print(f"CORPUS: {verses} verses, {words} words, "
          f"{gold_pairs_total} gold pairs   ({elapsed:.1f}s)")
    print(f"g2p guesses: {guessed}   still OOV: {oov}")
    print("="*66)
    print(f"{'level':<8}{'ruler':<9}{'TP':>7}{'FP':>7}{'FN':>7}"
          f"{'P':>8}{'R':>8}{'F1':>8}")
    print("-"*66)
    for (level, ruler), c in pools.items():
        p, r, f1 = _prf(c["tp"], c["fp"], c["fn"])
        print(f"{level:<8}{ruler:<9}{c['tp']:>7}{c['fp']:>7}{c['fn']:>7}"
              f"{p:>8.3f}{r:>8.3f}{f1:>8.3f}")

    print(f"\n--- sample FALSE POSITIVES (class/anchor) ---")
    for line in false_positives[:args.errors]:
        print(f"  {line}")
    print(f"\n--- sample FALSE NEGATIVES (class/anchor) ---")
    for line in false_negatives[:args.errors]:
        print(f"  {line}")


if __name__ == "__main__":
    main()
