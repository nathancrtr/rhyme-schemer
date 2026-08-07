"""Compare predicted rhyme-class sizes against gold class sizes.

Pairwise P/R/F says *how much* the scanner is wrong; it doesn't say what the
wrongness looks like. The tuning ledger's items 1 and 9 both predict one
specific shape -- connected components gluing distinct rhyme families into a
single mega-class, because slant rhyme isn't transitive and every bridge
edge merges two families for good.

That shape is visible in the size distribution. If the scanner's classes are
mostly the size of gold's, precision is being lost on edges; if the scanner
has a handful of enormous classes where gold has many small ones, the glue
is the problem and no amount of threshold tuning fixes it.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from rhyme_schemer.evaluate import parse_gold
from rhyme_schemer.scan import scan_verse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold_dir", type=Path)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    files = sorted(args.gold_dir.glob("*.gold"))
    if args.limit:
        files = files[:args.limit]

    gold_sizes: Counter = Counter()
    pred_sizes: Counter = Counter()
    gold_total = pred_total = verses = 0
    biggest: list[tuple[int, str]] = []

    for path in files:
        try:
            gold = parse_gold(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        scan = scan_verse(gold.verse)
        verses += 1
        for group in gold.groups:
            gold_sizes[len(group)] += 1
            gold_total += 1
        for group in scan.groups:
            pred_sizes[len(group)] += 1
            pred_total += 1
            biggest.append((len(group), path.stem))

    def bucket(n: int) -> str:
        if n <= 3:
            return f"{n}"
        if n <= 5:
            return "4-5"
        if n <= 9:
            return "6-9"
        if n <= 19:
            return "10-19"
        return "20+"

    gold_buckets: Counter = Counter()
    pred_buckets: Counter = Counter()
    for size, n in gold_sizes.items():
        gold_buckets[bucket(size)] += n
    for size, n in pred_sizes.items():
        pred_buckets[bucket(size)] += n

    order = ["2", "3", "4-5", "6-9", "10-19", "20+"]
    print("=" * 58)
    print("RHYME CLASS SIZE DISTRIBUTION")
    print("=" * 58)
    print(f"{verses} verses    gold classes: {gold_total}    "
          f"predicted classes: {pred_total}")
    print()
    print(f"{'size':<10}{'gold':>10}{'gold %':>10}"
          f"{'pred':>10}{'pred %':>10}")
    print("-" * 58)
    for key in order:
        g, p = gold_buckets.get(key, 0), pred_buckets.get(key, 0)
        gp = 100.0 * g / gold_total if gold_total else 0.0
        pp = 100.0 * p / pred_total if pred_total else 0.0
        print(f"{key:<10}{g:>10}{gp:>9.1f}%{p:>10}{pp:>9.1f}%")

    biggest.sort(reverse=True)
    print("\nlargest predicted classes:")
    for size, stem in biggest[:10]:
        print(f"  {size:>4} members   {stem}")


if __name__ == "__main__":
    main()
