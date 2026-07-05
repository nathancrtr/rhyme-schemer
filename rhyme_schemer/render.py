"""Render a scanned verse as a highlighted rhyme scheme (Unit 12).

The scanner (``scan.py``) ends with data: matches, classes, compounds. This
module turns that data back into the *verse the user typed*, painted so the
scheme is visible at a glance -- the Pudding/Vox picture this project has
chased since the README's first paragraph.

**What color means here -- a deliberate choice among three schools.** The
prior art splits on what the visual encoding should carry:

- *Hirjee & Brown's Rhyme Analyzer* (ISMIR 2010) formats every detected rhyme
  with one of five overlapping typographic channels (bold, italic, red,
  underline, strike-through). Complete, but five simultaneous channels read
  as receipts, not as a scheme.
- *Richard Brath's lyric tiles* color every syllable by its **vowel** (and
  texture by coda), so rhyme *emerges* from lookalike runs. Beautiful, and
  literally our ``features.py`` vowel space reused as a colormap -- but it
  renders the input phonetics, not the scanner's judgments: unmatched words
  glow exactly like matched ones.
- *Vox/Pudding* color the **rhyme class**. That is what we render: the
  picture shows what the scanner decided, nothing it didn't. (The Brath
  option would make Unit 11's precision work invisible.)

**The two problems class-coloring must then solve**, both measured on the
safe fixture corpus (an original engineered verse, Poe's "The Raven" st. 1,
Gilbert & Sullivan's Major-General song) rather than assumed:

1. **Words belong to several classes at once.** Selection dedups *events*,
   but one word still joins many: 17 multi-class word positions in 8
   original-verse lines, 27 in six lines of Poe, up to five classes on a
   single word ("quaint"), including *crossing* extents ("many a quaint" /
   "quaint and curious" share only their edge word) that no nested-boxes
   scheme can draw. G&S even rhymes three different syllables of
   "information" with three different partners. The policy: the
   **best-scoring** covering match owns the word's background fill; every
   other covering class appears as a thin **tick** bar under the word; the
   full receipts (every span, partner, and score) live in the word's
   tooltip. One dominant reading visible, nothing hidden from inspection.
2. **Compounds span classes.** ``chain_matches`` fuses per-beat matches
   ("palms are ~ arms are" + "steady ~ ready") into the multisyllabic unit
   the ear hears, but each beat keeps its own class and therefore its own
   color. A compound is drawn as a neutral **rule** under the whole fused
   extent -- adjacency plus the rule says "one rhyme", while the fills keep
   saying which family each beat belongs to. This is where the
   compound-vs-class tension the scanner deliberately left unresolved
   finally gets an answer, and it is a *rendering* answer: no scanner or
   kernel change.

**Palette.** Rhyme classes are categorical, so classes get fixed-order hues
-- never generated or cycled; classes beyond the eight slots fold into a
neutral wash (they are mostly two-member pairs, so prominence follows size).
Because text sits *on* the color, fills are tints of the categorical hues
(mixed toward the surface; CVD-validated as a set in both modes), while the
full-strength hues carry the thin marks: ticks and legend swatches. Identity
never rides on fill alone -- the word itself labels every mark, and the
legend and tooltips carry the ground truth.

**Layering.** ``plan_verse`` is the *policy* layer: it resolves fills,
ticks, compound rules, tooltips, and slot assignments into a medium-agnostic
``RenderPlan``. ``render_html`` and ``render_terminal`` are deliberately dumb
emitters over that plan -- what to draw is decided once, in one place, and
tested there; how to draw it is per-medium plumbing. OOV words are the flag
half of skip-and-flag: dotted-underlined in HTML, listed in both media, so
"unknown word" never reads as "doesn't rhyme".
"""

from __future__ import annotations

import html
from dataclasses import dataclass

from .scan import (
    VerseScan,
    chain_matches,
    scan_verse,
    tokenize_verse,
    _WORD_RE,
)

# The categorical hue slots (light mode / dark mode), in the fixed order the
# reference palette validated for adjacent-pair CVD separation. Slot hues are
# full-strength: they paint the *thin* marks (ticks, legend swatches).
_ACCENT_LIGHT = (
    "#2a78d6", "#1baf7a", "#eda100", "#008300",
    "#4a3aa7", "#e34948", "#e87ba4", "#eb6834",
)
_ACCENT_DARK = (
    "#3987e5", "#199e70", "#c98500", "#2ec02e",
    "#9085e9", "#e66767", "#d55181", "#d95926",
)

# Highlight fills: the same hues washed toward each mode's surface so primary
# ink stays readable on top (light: 40% hue on #fcfcfb; dark: 62% on #1a1a19,
# with a lighter green source so the green/yellow pair survives protanopia).
# Validated as sets: light worst adjacent CVD deltaE 12.4 (pass), dark 9.3
# (floor band -- legal because every fill is labeled by its own word and
# doubled by full-strength ticks/legend/tooltips).
_FILL_LIGHT = (
    "#a8c7ec", "#a2ddc7", "#f6d897", "#97cc97",
    "#b5aed9", "#f2b4b3", "#f4c8d8", "#f5c1ab",
)
_FILL_DARK = (
    "#2d5e97", "#196c4f", "#865c0a", "#268126",
    "#635c9a", "#984a49", "#8e3c59", "#904121",
)

# The neutral wash for overflow classes (a 9th class is never a new hue) and
# the ink/surface roles the emitters share.
_NEUTRAL_FILL = ("#e7e6e1", "#383835")  # (light, dark)
_NEUTRAL_ACCENT = ("#898781", "#898781")

N_SLOTS = len(_ACCENT_LIGHT)


# --- The plan: policy resolved into data --------------------------------------


@dataclass(frozen=True)
class WordPaint:
    """Everything the emitters need to know about one word.

    - ``fill``: rhyme-class index owning the background, or ``None`` (word is
      in no selected match). Ownership goes to the best-scoring match
      covering the word -- ties broken toward wider spans (compound-friendly)
      then earlier ones, so the choice is deterministic.
    - ``ticks``: the word's *other* class memberships, ascending -- drawn as
      thin bars so a secondary reading stays legible without competing.
    - ``compound``: id of the multi-beat compound whose rule spans this word,
      or ``None``. Single-beat compounds get no rule: underlining every
      match would say nothing.
    - ``oov``: the word has no CMUdict entry (render as "unknown", never as
      "doesn't rhyme").
    - ``tooltip``: the receipts -- one line per covering match, best first.
    """

    fill: int | None = None
    ticks: tuple[int, ...] = ()
    compound: int | None = None
    oov: bool = False
    tooltip: str = ""


@dataclass(frozen=True)
class Cell:
    """One run of verse text: a word (with paint) or the stuff between words.

    Cells partition each raw line exactly -- concatenating their ``text``
    reproduces the line character for character, punctuation, case, and
    spacing included. That fidelity is the whole contract: the reader must
    see the verse *they typed*, painted, not a tokenized shadow of it.
    """

    text: str
    paint: WordPaint | None = None


@dataclass(frozen=True)
class ClassEntry:
    """A legend row: one rhyme class and its assigned color slot.

    ``slot`` is an index into the categorical palette, or ``None`` for
    overflow classes folded into the neutral wash. Slots go to the largest
    classes first (ties by first appearance): with more classes than
    distinguishable hues, prominence should follow evidence, and the folded
    classes are mostly two-member pairs.
    """

    index: int
    slot: int | None
    members: tuple[str, ...]


@dataclass(frozen=True)
class RenderPlan:
    """A fully-resolved rendering: lines of cells, a legend, and OOV flags."""

    lines: tuple[tuple[Cell, ...], ...]
    classes: tuple[ClassEntry, ...]
    oov: tuple[str, ...]


def _slot_assignment(scan: VerseScan) -> dict[int, int | None]:
    """Class index -> palette slot (or None for the neutral overflow wash)."""
    by_size = sorted(
        range(len(scan.groups)), key=lambda k: (-len(scan.groups[k]), k)
    )
    return {
        k: (i if i < N_SLOTS else None) for i, k in enumerate(by_size)
    }


def _compound_rules(scan: VerseScan) -> dict[tuple[int, int], int]:
    """Word position -> id of the compound rule drawn under it.

    A compound's beats are contiguous on both sides (that is what ``_abuts``
    chained), so each side collapses to one word extent. Compounds claim
    their words **all-or-nothing**, strongest fusion first (more beats, then
    earlier): if any word of a compound is already claimed, the whole
    compound draws no rule. A partial rule would be worse than none -- a
    dangling fragment under half an extent asserts a fusion the picture
    cannot actually show (Poe's ``[many a quaint] ~ [suddenly there]`` loses
    "there" to the three-beat chain; a lone underlined "suddenly" is a
    falsehood, and silence is not).
    """
    compounds = [
        c for c in chain_matches(scan.matches) if len(c.matches) > 1
    ]
    compounds.sort(
        key=lambda c: (-len(c.matches), c.matches[0].a.line,
                       c.matches[0].a.start)
    )
    rules: dict[tuple[int, int], int] = {}
    for cid, compound in enumerate(compounds):
        words = [
            (span[0].line, w)
            for span in (compound.a_span, compound.b_span)
            for w in range(span[0].start, span[-1].end + 1)
        ]
        if any(position in rules for position in words):
            continue
        for position in words:
            rules[position] = cid
    return rules


def plan_verse(verse: str, scan: VerseScan | None = None) -> RenderPlan:
    """Resolve a verse (and its scan) into a medium-agnostic ``RenderPlan``.

    This is the policy layer: every judgment call in the module docstring --
    best-scoring match owns the fill, other memberships become ticks,
    multi-beat compounds become rules, receipts become tooltips -- happens
    here, once, as data. Pass ``scan`` to reuse an existing ``scan_verse``
    result; otherwise one is computed at defaults.
    """
    if scan is None:
        scan = scan_verse(verse)

    class_of = {
        c: k for k, group in enumerate(scan.groups) for c in group
    }

    # Each candidate's best match: the score that competes for fill
    # ownership, and the partner named in the receipts.
    best = {}
    for match in scan.matches:
        for side, other in ((match.a, match.b), (match.b, match.a)):
            if side not in best or match.score > best[side][0]:
                best[side] = (match.score, other)

    # Word position -> covering candidates, best first. The sort key is the
    # fill-ownership rule: score, then width, then earlier start.
    covering: dict[tuple[int, int], list] = {}
    for candidate in class_of:
        score = best[candidate][0]
        for w in range(candidate.start, candidate.end + 1):
            covering.setdefault((candidate.line, w), []).append(candidate)
    for cands in covering.values():
        cands.sort(
            key=lambda c: (-best[c][0], -(c.end - c.start), c.start)
        )

    rules = _compound_rules(scan)

    oov_set = {word.lower() for word in scan.oov}

    lines = []
    for line_index, raw_line in enumerate(verse.splitlines()):
        cells: list[Cell] = []
        cursor = 0
        for word_index, m in enumerate(_WORD_RE.finditer(raw_line)):
            if m.start() > cursor:
                cells.append(Cell(text=raw_line[cursor:m.start()]))
            position = (line_index, word_index)
            cands = covering.get(position, [])
            fill = class_of[cands[0]] if cands else None
            ticks = tuple(sorted(
                {class_of[c] for c in cands[1:]} - {fill}
            ))
            tooltip = "\n".join(
                "'{}' ~ '{}' — class {}, {:.2f}".format(
                    " ".join(c.words),
                    " ".join(best[c][1].words),
                    class_of[c],
                    best[c][0],
                )
                for c in cands
            )
            is_oov = m.group().lower() in oov_set
            if is_oov:
                tooltip = "no CMUdict entry — not scanned"
            paint = WordPaint(
                fill=fill,
                ticks=ticks,
                compound=rules.get(position),
                oov=is_oov,
                tooltip=tooltip,
            )
            cells.append(Cell(text=m.group(), paint=paint))
            cursor = m.end()
        if cursor < len(raw_line):
            cells.append(Cell(text=raw_line[cursor:]))
        lines.append(tuple(cells))

    slots = _slot_assignment(scan)
    classes = tuple(
        ClassEntry(
            index=k,
            slot=slots[k],
            members=tuple(" ".join(c.words) for c in group),
        )
        for k, group in enumerate(scan.groups)
    )
    return RenderPlan(lines=tuple(lines), classes=classes, oov=scan.oov)


# --- HTML emitter -------------------------------------------------------------

_CSS = """
.rhyme-scheme {{
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  line-height: 2.1; color: {ink_l}; background: {surface_l};
  padding: 1.5em; border-radius: 8px;
}}
.rhyme-scheme p.vline {{ margin: 0; white-space: pre-wrap; }}
.rhyme-scheme .w {{ display: inline-block; vertical-align: top;
  line-height: 1.4; }}
.rhyme-scheme .t {{ display: block; padding: 0 3px; border-radius: 3px; }}
.rhyme-scheme .ticks i {{ display: block; height: 3px; margin-top: 2px;
  border-radius: 1.5px; }}
.rhyme-scheme .cmp {{ border-bottom: 2px solid {ink2_l};
  padding-bottom: 2px; }}
.rhyme-scheme .oov {{ text-decoration: underline dotted {ink2_l} 2px;
  text-underline-offset: 3px; }}
.rhyme-scheme .legend {{ margin-top: 1.2em; font-size: 0.85em;
  line-height: 1.7; color: {ink2_l}; }}
.rhyme-scheme .legend .sw {{ display: inline-block; width: 0.9em;
  height: 0.9em; border-radius: 3px; vertical-align: -0.1em;
  margin-right: 0.4em; }}
{fills_l}
{accents_l}
@media (prefers-color-scheme: dark) {{
  .rhyme-scheme {{ color: {ink_d}; background: {surface_d}; }}
  .rhyme-scheme .cmp {{ border-bottom-color: {ink2_d}; }}
  .rhyme-scheme .oov {{ text-decoration-color: {ink2_d}; }}
  .rhyme-scheme .legend {{ color: {ink2_d}; }}
  {fills_d}
  {accents_d}
}}
"""


def _css() -> str:
    """The scoped stylesheet, fills and accents generated from the palette.

    Both modes are *selected*, not auto-flipped: the dark fills are their own
    validated set against the dark surface (see the palette comment above).
    """
    def rules(prefix, prop, values, neutral):
        lines = [
            f".rhyme-scheme .{prefix}{i} {{ {prop}: {v}; }}"
            for i, v in enumerate(values)
        ]
        lines.append(f".rhyme-scheme .{prefix}x {{ {prop}: {neutral}; }}")
        return "\n".join(lines)

    return _CSS.format(
        surface_l="#fcfcfb", surface_d="#1a1a19",
        ink_l="#0b0b0b", ink_d="#ffffff",
        ink2_l="#898781", ink2_d="#898781",
        fills_l=rules("f", "background", _FILL_LIGHT, _NEUTRAL_FILL[0]),
        accents_l=rules("a", "background", _ACCENT_LIGHT,
                        _NEUTRAL_ACCENT[0]),
        fills_d=rules("f", "background", _FILL_DARK, _NEUTRAL_FILL[1]),
        accents_d=rules("a", "background", _ACCENT_DARK,
                        _NEUTRAL_ACCENT[1]),
    )


def _slot_class(prefix: str, slot: int | None) -> str:
    return f"{prefix}{slot}" if slot is not None else f"{prefix}x"


def _html_word(cell: Cell, slots: dict[int, int | None]) -> str:
    paint = cell.paint
    text = html.escape(cell.text)
    if paint.oov:
        return (
            f'<span class="w oov" title="{html.escape(paint.tooltip)}">'
            f"{text}</span>"
        )
    if paint.fill is None:
        return text
    title = html.escape(paint.tooltip).replace("\n", "&#10;")
    fill = _slot_class("f", slots[paint.fill])
    ticks = "".join(
        f'<i class="{_slot_class("a", slots[k])}"></i>'
        for k in paint.ticks
    )
    tick_block = f'<span class="ticks">{ticks}</span>' if ticks else ""
    return (
        f'<span class="w" title="{title}">'
        f'<span class="t {fill}">{text}</span>{tick_block}</span>'
    )


def render_html(verse: str, scan: VerseScan | None = None) -> str:
    """Render a verse as a self-contained HTML fragment.

    A ``<div class="rhyme-scheme">`` with its own scoped ``<style>`` -- no
    external assets, light and dark mode both styled -- suitable for writing
    to a file, embedding in a page, or publishing as an artifact. Fills mark
    classes, tick bars mark secondary memberships, a neutral rule marks each
    multi-beat compound, dotted underlines mark OOV words, and every painted
    word carries its receipts in a plain ``title`` tooltip. A legend maps
    swatches to class members, so identity never rides on fill alone.
    """
    plan = plan_verse(verse, scan)
    slots = {entry.index: entry.slot for entry in plan.classes}

    body = []
    for cells in plan.lines:
        parts, open_rule = [], None
        for index, cell in enumerate(cells):
            rule = _cell_rule(cells, index, open_rule)
            if rule != open_rule:
                if open_rule is not None:
                    parts.append("</span>")
                if rule is not None:
                    parts.append('<span class="cmp">')
                open_rule = rule
            if cell.paint is None:
                parts.append(html.escape(cell.text))
            else:
                parts.append(_html_word(cell, slots))
        if open_rule is not None:
            parts.append("</span>")
        body.append(f'<p class="vline">{"".join(parts) or "&nbsp;"}</p>')

    legend = ['<div class="legend">']
    for entry in plan.classes:
        members = html.escape(" · ".join(_preview(entry.members)))
        swatch = _slot_class("f", entry.slot)
        legend.append(
            f'<div><span class="sw {swatch}"></span>'
            f"class {entry.index}: {members}</div>"
        )
    if plan.oov:
        oov = html.escape(", ".join(plan.oov))
        legend.append(
            f"<div>unknown to CMUdict (not scanned): {oov}</div>"
        )
    legend.append("</div>")

    return (
        f"<style>{_css()}</style>\n"
        f'<div class="rhyme-scheme">\n'
        + "\n".join(body)
        + "\n"
        + "\n".join(legend)
        + "\n</div>"
    )


def _cell_rule(
    cells: tuple[Cell, ...], index: int, open_rule: int | None
) -> int | None:
    """Which compound rule (if any) should run under cell ``index``.

    Word cells answer from their paint. A between-words cell (punctuation,
    spaces) continues an open rule only if the *next* word cell carries the
    same one -- so "up, shake" stays one unbroken rule but the rule never
    dangles past its last word.
    """
    cell = cells[index]
    if cell.paint is not None:
        return cell.paint.compound
    if open_rule is None:
        return None
    for nxt in cells[index + 1:]:
        if nxt.paint is not None:
            return open_rule if nxt.paint.compound == open_rule else None
    return None


def _preview(members: tuple[str, ...], limit: int = 6) -> list[str]:
    """The legend's member list, deduplicated and truncated with a count."""
    unique = list(dict.fromkeys(members))
    if len(unique) <= limit:
        return unique
    return unique[:limit] + [f"… +{len(unique) - limit}"]


# --- Terminal emitter ---------------------------------------------------------


def _ansi_bg(hex_color: str) -> str:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"\x1b[48;2;{r};{g};{b}m"


def render_terminal(verse: str, scan: VerseScan | None = None) -> str:
    """Render a verse with ANSI colors -- the deliberately lossy fallback.

    Truecolor backgrounds mark class fills (the dark-mode fill set, readable
    under white text on light and dark terminals alike), underlines mark
    compound rules, and the legend lists every class with a swatch. What the
    terminal cannot carry -- tick bars and hover receipts -- lives only in
    the HTML view; the legend and OOV note keep the fallback honest.
    """
    plan = plan_verse(verse, scan)
    slots = {entry.index: entry.slot for entry in plan.classes}

    def fill_code(class_index):
        slot = slots[class_index]
        color = _FILL_DARK[slot] if slot is not None else _NEUTRAL_FILL[1]
        return _ansi_bg(color) + "\x1b[97m"

    out = []
    for cells in plan.lines:
        parts = []
        for cell in cells:
            paint = cell.paint
            if paint is None or (paint.fill is None
                                 and paint.compound is None
                                 and not paint.oov):
                parts.append(cell.text)
                continue
            codes = ""
            if paint.fill is not None:
                codes += fill_code(paint.fill)
            if paint.compound is not None:
                codes += "\x1b[4m"
            if paint.oov:
                codes += "\x1b[3m"
            parts.append(f"{codes}{cell.text}\x1b[0m")
        out.append("".join(parts))

    out.append("")
    for entry in plan.classes:
        slot = entry.slot
        color = _FILL_DARK[slot] if slot is not None else _NEUTRAL_FILL[1]
        swatch = f"{_ansi_bg(color)}  \x1b[0m"
        out.append(
            f"{swatch} class {entry.index}: "
            + " · ".join(_preview(entry.members))
        )
    if plan.oov:
        out.append(
            "unknown to CMUdict (not scanned): " + ", ".join(plan.oov)
        )
    return "\n".join(out)
