"""Convert MCFlow Humdrum transcriptions into this project's gold format.

MCFlow (Condit-Schultz, *Empirical Musicology Review* 2016) transcribes 124
rap songs with, among other spines, ``**lyrics`` (syllable-by-syllable, with
hyphens marking word continuation), ``**break`` (phrase-onset markers),
``**stress`` (**performed** stress, 0/1 -- the very thing CMUdict cannot
tell us), and ``**rhyme`` (rhyme-class labels). That last spine is the
ground truth Unit 14 was going to build by hand.

**This script emits data; it must never be run into the repo.** MCFlow is
commercial lyric text, and the project's content-safety rule forbids
committing it. The script is the artifact worth keeping -- point it at a
local clone and write the gold files somewhere untracked.

The ``**rhyme`` encoding, decoded from the corpus itself:

- a bare capital (``A``) is a one-syllable member of rhyme class A;
- ``(B`` ... ``b)`` brackets a *multisyllabic* rhyme, capital opening it and
  lowercase closing it, both belonging to class B;
- ``(E`` ... ``F)`` is the compound case -- one multisyllabic rhyme whose
  syllables belong to *different* classes, which is exactly the tension
  ``render.chain_matches`` handles by drawing a spanning rule under beats
  that keep their own colors;
- ``]`` appears as an alternate closer.

Class letters are scoped to the section (``*>Verse1``), so groups are built
per section and the sections are emitted as separate gold files.

Syllable-to-word folding follows the hyphens: a syllable starting with "-"
continues the previous word, one ending with "-" continues into the next.
Because a rhyme is annotated on a *syllable* but the gold format names
*words*, a multisyllabic rhyme inside one word collapses to that one word;
across words it becomes a word span.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# Humdrum interpretation tokens we route by name rather than by column index:
# spine order is stable across MCFlow today, but naming the spines makes a
# reordered file fail loudly instead of silently scoring the wrong column.
WANTED_SPINES = ("**lyrics", "**break", "**rhyme", "**stress")

# A rhyme token is an optional opener, a letter, an optional closer.
_RHYME_RE = re.compile(r"^(?P<open>\()?(?P<letter>[A-Za-z])(?P<close>[)\]])?$")

# The emitted verse must tokenize *identically* under ``scan.tokenize_verse``
# (``[a-zA-Z']+``), or every gold word index after the first odd token points
# at the wrong word. So rather than blacklisting the punctuation MCFlow
# happens to use -- parentheses, underscores, digits, "#" censoring -- keep
# only what the project counts as a word character and drop what's left.
_KEEP = re.compile(r"[^A-Za-z']")

# MCFlow uses typographic apostrophes; the tokenizer wants the straight one.
_APOSTROPHES = str.maketrans("’‘`", "'''")


@dataclass
class Word:
    """One reconstructed word: its text, its line, and its index on that line."""

    text: str
    line: int
    index: int
    # Rhyme class letters annotated on any syllable of this word.
    classes: set[str] = field(default_factory=set)
    # Raw ``**rhyme`` tokens, one per syllable, in order. Kept raw because
    # the brackets -- not just the letters -- carry the structure: a
    # multisyllabic rhyme is a *run* from "(X" to "x)", and collapsing it to
    # a set of letters loses the fact that its syllables are one side of a
    # rhyme rather than rhyme partners of each other.
    rhyme_tokens: list[str] = field(default_factory=list)
    # Performed stress: 1 if any syllable of the word was performed stressed.
    performed_stress: bool = False
    # Per-syllable performed stress, in order -- MCFlow's observation of
    # where the beat actually landed, which is what CMUdict cannot say.
    stresses: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class Instance:
    """One occurrence of a rhyme: a word extent on one line, plus its class."""

    letter: str
    line: int
    start: int
    end: int
    text: str

    def ref(self) -> str:
        """This occurrence as a gold reference, ``word@line.start[-end]``.

        The leading word text is the format's typo guard, checked against the
        word at ``start`` -- so spans carry it too, naming their first word.
        """
        span = (f"{self.start}" if self.start == self.end
                else f"{self.start}-{self.end}")
        return f"{self.text}@{self.line}.{span}"


def _instance(letter: str, start: Word, last: Word) -> Instance:
    """Build an Instance from the words a rhyme run opened and closed on."""
    if last.line != start.line or last.index < start.index:
        last = start  # clipped: Extent cannot straddle a line
    return Instance(letter=letter, line=start.line, start=start.index,
                    end=last.index, text=start.text)


@dataclass
class Section:
    """One song section (a verse), reconstructed into lines and words."""

    name: str
    song: str
    lines: list[list[Word]] = field(default_factory=list)

    def verse_text(self) -> str:
        return "\n".join(" ".join(w.text for w in line) for line in self.lines)

    def instances(self) -> list[Instance]:
        """Every rhyme *occurrence*, as a word extent plus its class.

        This is the distinction that decides whether the gold is honest. A
        bare capital marks a one-syllable occurrence. ``(C`` ... ``c)``
        brackets a *multisyllabic* one: in "hemp be" / "empty" / "pimps be",
        class C has three occurrences of two syllables each -- and the claim
        is that those three units rhyme *with each other*, not that "hemp"
        rhymes with "be". Exploding class membership word-by-word would
        manufacture that second, false claim.

        Compounds (``(E`` opening, ``F)`` closing) are keyed by the
        *opening* letter, which is what makes "rap tunes" and "sassoon"
        land in one group rather than two half-groups.

        An occurrence that runs across a line break is clipped to the line
        it started on, because the gold format's ``Extent`` is single-line.
        """
        found: list[Instance] = []
        open_letter: str | None = None
        start: Word | None = None
        last: Word | None = None

        for line in self.lines:
            for word in line:
                for token in word.rhyme_tokens:
                    m = _RHYME_RE.match(token)
                    if not m:
                        continue
                    letter = m.group("letter").upper()
                    if m.group("open"):
                        open_letter, start, last = letter, word, word
                    elif open_letter is not None:
                        last = word
                        if m.group("close"):
                            found.append(_instance(open_letter, start, last))
                            open_letter = start = last = None
                    else:
                        found.append(_instance(letter, word, word))
            # A run left open at the end of a line still describes the words
            # it covered; close it there rather than losing it.
            if open_letter is not None and start is not None:
                found.append(_instance(open_letter, start, last or start))
                open_letter = start = last = None
        return found

    def groups(self) -> dict[str, list[Instance]]:
        """Occurrences grouped by class letter, classes with >= 2 members."""
        by_class: dict[str, list[Instance]] = defaultdict(list)
        for instance in self.instances():
            by_class[instance.letter].append(instance)
        return {k: v for k, v in sorted(by_class.items()) if len(v) >= 2}


def _spine_columns(header: str) -> dict[str, int]:
    """Map spine name -> column index from the exclusive interpretation line."""
    columns = {}
    for i, name in enumerate(header.rstrip("\n").split("\t")):
        if name in WANTED_SPINES and name not in columns:
            columns[name] = i
    missing = set(WANTED_SPINES) - set(columns)
    if missing:
        raise ValueError(f"missing spines: {sorted(missing)}")
    return columns


def parse_file(path: Path) -> list[Section]:
    """Parse one .rap file into its sections."""
    song = path.stem
    sections: list[Section] = []
    current: Section | None = None
    columns: dict[str, int] | None = None

    # Word assembly state: syllables accumulate until a word is complete.
    pending_text: list[str] = []
    pending_classes: set[str] = set()
    pending_stress = False
    pending_stresses: list[int] = []
    pending_rhymes: list[str] = []
    open_word = False  # previous syllable ended with "-", so the word continues

    def flush() -> None:
        """Emit the accumulated syllables as one word on the current line."""
        nonlocal pending_text, pending_classes, pending_stress, open_word
        nonlocal pending_stresses, pending_rhymes
        if pending_text and current and current.lines:
            # Each syllable carries its own continuation hyphens ("wel-",
            # "-come"); strip them per syllable before joining, or the seam
            # keeps both ("wel--come").
            text = "".join(s.strip("-") for s in pending_text)
            text = _KEEP.sub("", text.translate(_APOSTROPHES))
            # A syllable that was purely a digit or a censoring mark leaves
            # nothing behind; dropping the word entirely keeps the emitted
            # verse and the emitted indices consistent with each other.
            if text:
                line = current.lines[-1]
                line.append(Word(text=text, line=len(current.lines) - 1,
                                 index=len(line), classes=set(pending_classes),
                                 performed_stress=pending_stress,
                                 stresses=list(pending_stresses),
                                 rhyme_tokens=list(pending_rhymes)))
        pending_text, pending_classes, pending_stress = [], set(), False
        pending_stresses = []
        pending_rhymes = []
        open_word = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("**"):
            columns = _spine_columns(raw)
            continue
        if raw.startswith("*>"):
            flush()
            name = raw.split("\t")[0][2:]
            # Only lyric-bearing sections interest us; MCFlow also marks
            # instrumental spans, which simply end up empty and get dropped.
            current = Section(name=name, song=song)
            sections.append(current)
            continue
        if raw.startswith(("!", "*", "=")) or not raw.strip():
            continue
        if columns is None or current is None:
            continue

        cells = raw.split("\t")
        if len(cells) <= max(columns.values()):
            continue

        syllable = cells[columns["**lyrics"]].strip()
        if syllable in (".", ""):
            continue

        brk = cells[columns["**break"]].strip()
        rhyme = cells[columns["**rhyme"]].strip()
        stress = cells[columns["**stress"]].strip()

        # A break marker starts a new line -- but only between words, never
        # mid-word, so a hyphenated word straddling a break stays intact.
        if brk not in (".", "") and not open_word:
            flush()
            current.lines.append([])

        if not current.lines:
            current.lines.append([])

        continues_previous = syllable.startswith("-")
        if not continues_previous:
            flush()

        pending_text.append(syllable)
        open_word = syllable.endswith("-")
        if stress in ("0", "1"):
            pending_stresses.append(int(stress))
        if stress == "1":
            pending_stress = True
        pending_rhymes.append(rhyme)
        m = _RHYME_RE.match(rhyme)
        if m:
            pending_classes.add(m.group("letter").upper())

        if not open_word:
            flush()

    flush()
    return [s for s in sections if any(line for line in s.lines)]


def to_gold(section: Section) -> str:
    """Render one section as a gold annotation file."""
    lines = [
        f"# Gold rhyme annotation from MCFlow — {section.song}, {section.name}.",
        "# Annotator: MCFlow (Condit-Schultz 2016), **rhyme spine.",
        "# Rhyme classes are the corpus's own; extents are word-level.",
        "",
        "verse:",
    ]
    for line in section.lines:
        lines.append("  " + " ".join(w.text for w in line))
    lines.append("")
    for letter, occurrences in section.groups().items():
        refs = " ".join(o.ref() for o in occurrences)
        lines.append(f"group: {refs}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("humdrum", type=Path,
                        help="MCFlow Humdrum directory (a local clone)")
    parser.add_argument("out", type=Path, help="output directory (untracked!)")
    parser.add_argument("--limit", type=int, default=0,
                        help="stop after N songs (0 = all)")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    files = sorted(args.humdrum.glob("*.rap"))
    if args.limit:
        files = files[:args.limit]

    written = skipped = 0
    for path in files:
        try:
            sections = parse_file(path)
        except (ValueError, OSError) as exc:
            print(f"skip {path.name}: {exc}")
            skipped += 1
            continue
        for section in sections:
            if not section.groups():
                continue
            target = args.out / f"{section.song}.{section.name}.gold"
            target.write_text(to_gold(section), encoding="utf-8")
            written += 1
    print(f"wrote {written} gold files from {len(files)} songs "
          f"({skipped} skipped)")


if __name__ == "__main__":
    main()
