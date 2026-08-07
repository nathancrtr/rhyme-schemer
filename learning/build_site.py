"""Build the course site: learning/site/ from the Markdown sources.

The course is delivered as a static, file://-friendly site -- every page
opens by double-click, no server, no network. This script is the whole
build system: it renders the lesson guides and course documents
(python-markdown), wraps them in a shared shell (header nav, unit
breadcrumbs, prev/next footer), assembles per-unit pages that combine the
unit's syllabus entry with its lesson and hands-on material, and writes the
stylesheet. Markdown stays the source of truth; the generated site is
committed so a fresh clone is browsable without running anything.

Regenerate after editing any lesson or curriculum.md:

    pip install markdown          # dev-only dependency (not in requirements.txt)
    python learning/build_site.py

Conventions the build enforces:
- "> PAUSE. ..." blockquotes in lessons render as think-first boxes -- the
  reader is asked to commit to an answer before scrolling on (the browser
  descendant of the old Socratic pause).
- Links to lesson .md files are rewritten to their unit pages.
- Widgets/quizzes/exercises stay where they live (interactive/); unit pages
  link to them relatively, so the site works from any checkout location.
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown

LEARNING = Path(__file__).resolve().parent
SITE = LEARNING / "site"
LESSONS = LEARNING / "interactive" / "lessons"

# ---------------------------------------------------------------------------
# Course structure
# ---------------------------------------------------------------------------

PHASES = {
    1: ("The phonetic foundation", "read the existing modules as worked examples"),
    2: ("The rhyme kernel", "build rhyme_score, from perfect rhyme to alignment"),
    3: ("From pairs to a scheme", "spans, variants, grouping, and the verse scanner"),
    4: ("Seeing, guessing, measuring", "visualization, G2P, and evaluation"),
    5: ("Capstone & frontiers", "the finished tool and where it points next"),
}

# One entry per unit: page content is the unit's curriculum extract plus its
# lesson (if written) plus hands-on links. Paths are relative to learning/.
UNITS = [
    dict(num=1, phase=1, title="Phonemes, ARPAbet & the lexicon",
         lesson="unit-01-phonemes-not-spelling.md",
         companion=("How speech works: a phonetics refresher", "phonetics-primer.md")),
    dict(num=2, phase=1, title="The IPA vowel space & articulatory features",
         lesson="unit-02-feature-distance.md",
         widgets=[("Vowel-Space Explorer", "interactive/widgets/vowel-explorer.html")]),
    dict(num=3, phase=1, title="Consonants: place, manner, voicing, sonority",
         lesson="unit-03-consonants.md",
         widgets=[("Consonant-Space Explorer", "interactive/widgets/consonant-explorer.html")]),
    dict(num=4, phase=1, title="Syllables & phonotactics: the Maximal Onset Principle",
         lesson="unit-04-syllables-and-phonotactics.md",
         widgets=[("Syllabifier", "interactive/widgets/syllabifier.html")],
         quiz=("Phase 1 checkpoint", "interactive/quizzes/phase-1-checkpoint.html")),
    dict(num=5, phase=2, title="The vowel skeleton & the rhyme-bearing tail",
         lesson="unit-05-rhyme-tail.md",
         exercise=("unit-05-rhyme-tail", "interactive/exercises/unit-05-rhyme-tail")),
    dict(num=6, phase=2, title="Perfect rhyme first",
         lesson="unit-06-perfect-rhyme.md"),
    dict(num=7, phase=2, title="Graded slant rhyme & weighting",
         lesson="unit-07-the-rhyme-kernel.md",
         widgets=[("Rhyme-Score Sandbox", "interactive/widgets/rhyme-score-sandbox.html")]),
    dict(num=8, phase=2, title="Unequal lengths: sequence alignment",
         lesson="unit-08-alignment.md",
         widgets=[("NW Alignment Explorer", "interactive/widgets/nw-alignment.html")],
         exercise=("unit-08-alignment", "interactive/exercises/unit-08-alignment"),
         companion=("The sequence-alignment family", "sequence-alignment-family.md")),
    dict(num=9, phase=3, title="Multi-word spans & pronunciation variants",
         lesson="unit-09-variants-and-spans.md",
         widgets=[("Rhyme-Score Sandbox", "interactive/widgets/rhyme-score-sandbox.html")]),
    dict(num=10, phase=3, title="Grouping rhymes: similarity graphs & components",
         lesson="unit-10-non-transitivity.md",
         widgets=[("Grouping Explorer", "interactive/widgets/grouping-explorer.html")],
         quiz=("Phase 3 checkpoint", "interactive/quizzes/phase-3-checkpoint.html"),
         companion=("Graphs, components, and union-find from zero", "graphs-and-union-find.md")),
    dict(num=11, phase=3, title="Internal & multisyllabic rhyme: scanning a verse",
         lesson="unit-11-scanner-walkthrough.md",
         lesson_note=(
             "This unit's guide is the scanner walkthrough — written **during** the "
             "collaborative build, warts and wrong turns included, and it contains the "
             "project's living <em>open tuning ledger</em>. The Markdown file in "
             "<code>interactive/lessons/</code> remains the engineering-canonical copy "
             "that code comments cite; this page is its rendering.")),
    dict(num=12, phase=4, title="Visualizing the scheme",
         lesson="unit-12-rendering.md"),
    dict(num=13, phase=4, title="Out-of-vocabulary words & grapheme-to-phoneme",
         lesson="unit-13-g2p.md"),
    dict(num=14, phase=4, title="Evaluation: is it any good?",
         widgets=[("Gold Annotator", "interactive/widgets/gold-annotator.html")]),
    dict(num=15, phase=5, title="Capstone: the finished tool + the written understanding"),
]

# .md links appearing in prose, rewritten to their site pages.
LINK_MAP = {
    "unit-01-phonemes-not-spelling.md": "unit-01.html",
    "unit-03-consonants.md": "unit-03.html",
    "unit-04-syllables-and-phonotactics.md": "unit-04.html",
    "unit-05-rhyme-tail.md": "unit-05.html",
    "unit-06-perfect-rhyme.md": "unit-06.html",
    "unit-09-variants-and-spans.md": "unit-09.html",
    "unit-12-rendering.md": "unit-12.html",
    "unit-13-g2p.md": "unit-13.html",
    "unit-02-feature-distance.md": "unit-02.html",
    "unit-07-the-rhyme-kernel.md": "unit-07.html",
    "unit-08-alignment.md": "unit-08.html",
    "unit-10-non-transitivity.md": "unit-10.html",
    "unit-11-scanner-walkthrough.md": "unit-11.html",
    "sequence-alignment-family.md": "sequence-alignment-family.html",
    "phonetics-primer.md": "phonetics-primer.html",
    "graphs-and-union-find.md": "graphs-and-union-find.html",
    "learning-resources.md": "resources.html",
    "curriculum.md": "syllabus.html",
}

# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

# GitHub-flavored Markdown lets a list open directly under a paragraph line;
# python-markdown needs a blank line first, else the bullets are swallowed
# into the paragraph. Insert the blank line: before a column-0 list item,
# when the previous line is ordinary paragraph text (not blank, not itself a
# list item or continuation, not a blockquote/heading/table row).
_LIST_AFTER_PARAGRAPH = re.compile(
    r"(^(?![ \t>#|]|[-*+] |\d+\. ).+)\n(?=(?:[-*+]|\d+\.) )",
    re.MULTILINE,
)


def md_to_html(text: str) -> str:
    text = _LIST_AFTER_PARAGRAPH.sub(r"\1\n\n", text)
    html = markdown.markdown(text, extensions=["fenced_code", "tables"])
    # Socratic pauses become think-first boxes.
    html = re.sub(
        r"<blockquote>\s*<p>(?:<strong>)?PAUSE\.?(?:</strong>)?\s*(?:Ask:)?\s*",
        '<blockquote class="think"><p><span class="think-label">Think first</span> ',
        html,
    )
    # "Check yourself" prompts get the same treatment.
    html = re.sub(
        r"<blockquote>\s*<p>(?:<strong>)?Check yourself:?(?:</strong>)?\s*",
        '<blockquote class="think"><p><span class="think-label">Check yourself</span> ',
        html,
    )
    for md_name, page in LINK_MAP.items():
        html = re.sub(rf'href="[^"]*{re.escape(md_name)}"', f'href="{page}"', html)
    return html


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@TITLE@</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top">
  <a class="brand" href="index.html">rhyme-schemer <span>· the course</span></a>
  <nav>
    <a href="index.html">Units</a>
    <a href="syllabus.html">Syllabus</a>
    <a href="resources.html">Resources</a>
    <a href="about.html">About</a>
  </nav>
</header>
<main>
@CONTENT@
</main>
<footer class="pager">
@PAGER@
</footer>
</body>
</html>
"""


def write_page(name: str, title: str, content: str, pager: str = "") -> None:
    html = (PAGE.replace("@TITLE@", title)
                .replace("@CONTENT@", content)
                .replace("@PAGER@", pager))
    (SITE / name).write_text(html)


def curriculum_extract(curriculum: str, num: int) -> str:
    """The '### Unit N' section of curriculum.md, minus its heading."""
    match = re.search(
        rf"^### Unit {num} — .*?$\n(.*?)(?=^### |^## |^---)",
        curriculum, re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def hands_on_card(unit: dict) -> str:
    rows = []
    for label, path in unit.get("widgets", []):
        rows.append(f'<a class="chip widget" href="../{path}">🧪 {label}</a>')
    if unit.get("quiz"):
        label, path = unit["quiz"]
        rows.append(f'<a class="chip quiz" href="../{path}">✅ {label}</a>')
    if unit.get("exercise"):
        label, path = unit["exercise"]
        rows.append(f'<a class="chip exercise" href="../{path}/task.md">⌨️ Exercise: {label}</a>')
    if unit.get("companion"):
        label, md_name = unit["companion"]
        page = LINK_MAP.get(md_name, md_name)
        rows.append(f'<a class="chip companion" href="{page}">📖 {label}</a>')
    if not rows:
        return ""
    return '<div class="hands-on"><h2>Hands-on</h2>' + " ".join(rows) + "</div>"


def build_unit_pages(curriculum: str) -> None:
    for i, unit in enumerate(UNITS):
        num = unit["num"]
        phase_title = PHASES[unit["phase"]][0]
        parts = [
            f'<p class="crumb">Phase {unit["phase"]} · {phase_title}</p>',
            f'<h1>Unit {num} — {unit["title"]}</h1>',
        ]
        extract = curriculum_extract(curriculum, num)
        if extract:
            parts.append('<details class="glance" open><summary>The unit at a glance '
                         '<span class="muted">(from the syllabus)</span></summary>'
                         + md_to_html(extract) + "</details>")
        parts.append(hands_on_card(unit))
        if unit.get("lesson"):
            lesson_md = (LESSONS / unit["lesson"]).read_text()
            # The lesson file's own H1 duplicates the page title; drop it.
            lesson_md = re.sub(r"^# .*\n", "", lesson_md, count=1)
            note = unit.get("lesson_note")
            if note:
                parts.append('<div class="note">' + md_to_html(note)[3:-4] + "</div>")
            parts.append('<article class="lesson">' + md_to_html(lesson_md) + "</article>")
        else:
            parts.append(
                '<div class="pending">The full guide for this unit is still being '
                "written; the syllabus entry above is the map in the meantime. "
                "Guides land unit by unit as the course build-out continues.</div>")

        prev_html = next_html = ""
        if i > 0:
            p = UNITS[i - 1]
            prev_html = f'<a class="prev" href="unit-{p["num"]:02d}.html">← Unit {p["num"]}: {p["title"]}</a>'
        if i < len(UNITS) - 1:
            n = UNITS[i + 1]
            next_html = f'<a class="next" href="unit-{n["num"]:02d}.html">Unit {n["num"]}: {n["title"]} →</a>'
        write_page(f"unit-{num:02d}.html", f"Unit {num} — {unit['title']}",
                   "\n".join(p for p in parts if p), prev_html + next_html)


def build_index() -> None:
    cards = []
    for phase_num, (title, blurb) in PHASES.items():
        rows = []
        for unit in UNITS:
            if unit["phase"] != phase_num:
                continue
            badges = []
            if unit.get("lesson"):
                badges.append('<span class="badge lesson">guide</span>')
            if unit.get("widgets"):
                badges.append('<span class="badge widget">widget</span>')
            if unit.get("quiz"):
                badges.append('<span class="badge quiz">quiz</span>')
            if unit.get("exercise"):
                badges.append('<span class="badge exercise">exercise</span>')
            rows.append(
                f'<li><a href="unit-{unit["num"]:02d}.html">'
                f'<span class="unum">{unit["num"]}</span> {unit["title"]}</a>'
                f'<span class="badges">{"".join(badges)}</span></li>')
        cards.append(
            f'<section class="phase"><h2>Phase {phase_num} — {title}</h2>'
            f'<p class="muted">{blurb}</p><ul class="units">{"".join(rows)}</ul></section>')

    content = (
        "<h1>Computational phonetics, one rhyme detector at a time</h1>"
        '<p class="lede">A self-contained course on NLP and computational phonology, taught '
        "through a single worked project: <b>rhyme-schemer</b>, a tool that reads hip-hop "
        "lyrics and surfaces their rhyme scheme — slant rhyme, assonance, and all. You read "
        "real modules, build the missing ones, and every concept arrives already attached to "
        "code that uses it.</p>"
        '<p class="lede muted">For the linguistics-curious programmer: the phonology is taught '
        "from the ground up; the algorithms assume fluency in code but not a background in "
        'algorithm design. Start with <a href="about.html">how this course works</a> — and if '
        'your phonetics is cold (or was never warm), <a href="phonetics-primer.html">the sounds '
        "refresher</a> rebuilds it in twenty minutes, mostly by making you make sounds at your "
        "desk.</p>"
        + "".join(cards))
    write_page("index.html", "rhyme-schemer: the course", content)


def build_document_pages(curriculum: str) -> None:
    resources = (LEARNING / "learning-resources.md").read_text()
    write_page("resources.html", "Resources", md_to_html(resources))
    write_page("syllabus.html", "Syllabus",
               '<p class="note">The complete syllabus, one page. Each unit heading here has a '
               'matching <a href="index.html">unit page</a> with the lesson and hands-on material.</p>'
               + md_to_html(curriculum))
    seq = (LESSONS / "sequence-alignment-family.md").read_text()
    write_page("sequence-alignment-family.html", "The sequence-alignment family",
               '<p class="crumb">Companion reading · Unit 8</p>' + md_to_html(seq),
               '<a class="next" href="unit-08.html">Unit 8: Unequal lengths: sequence alignment →</a>')
    primer = (LESSONS / "phonetics-primer.md").read_text()
    write_page("phonetics-primer.html", "How speech works: a phonetics refresher",
               '<p class="crumb">On-ramp · before Unit 1</p>' + md_to_html(primer),
               '<a class="next" href="unit-01.html">Unit 1: Phonemes, ARPAbet & the lexicon →</a>')
    dsu = (LESSONS / "graphs-and-union-find.md").read_text()
    write_page("graphs-and-union-find.html", "Graphs, components, and union-find from zero",
               '<p class="crumb">Companion reading · Unit 10</p>' + md_to_html(dsu),
               '<a class="next" href="unit-10.html">Unit 10: Grouping rhymes →</a>')

    about = """
# How this course works

**The repo is the spine.** Each unit takes rhyme-schemer from one working
state to the next. Theory is just-in-time: you read the chapter or paper that
unblocks *this* step, never a survey. Where the code already exists, you read
it as a worked example and prove your understanding by extending it; where it
doesn't, you build it, usually by making a failing test pass.

**A word about the voice.** These materials were produced *during* the actual
collaborative construction of the project, and they keep that character on
purpose. You will find recorded design arguments, wrong turns that stayed
wrong for three units before the evidence arrived, and judgments that rest
explicitly on one listener's ear (marked as such — in rhyme detection, the
annotator's ear *is* the instrument). That history is not noise around the
course; it is the course. Watching a design decision get made — including the
options that lost — teaches more than being handed the winner.

**Think-first boxes.** Where a guide pauses on a question, commit to your own
answer before reading past the box. The friction is the point: the questions
mark exactly the spots where a plausible wrong answer teaches something.

**The hands-on layer.** Widgets are self-contained pages that render the
repo's *own numbers* — the vowel explorer computes the very
`vowel_distance()` the kernel uses, and the sandbox is a verified port of the
scoring pipeline. Exercises ship as failing tests: green bar = done. Quizzes
are per-phase checkpoints.

**Working the repo.** You'll want a clone and a working Python environment
(`pip install -r requirements.txt`; `python -m unittest discover tests`
should be green before Unit 1). The tests are the course's grader.

**Regenerating this site.** Pages are generated from Markdown sources by
`learning/build_site.py`; edit the source, not the HTML.
"""
    write_page("about.html", "About this course", md_to_html(about))


STYLE = """
:root{--bg:#0f1115;--card:#1a1e26;--ink:#e8eaed;--muted:#9aa3af;--line:#2a2f3a;
      --accent:#6ea8fe;--good:#2ecc71;--warn:#f0a868;--think:#c678dd;}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);
     font:16px/1.65 ui-sans-serif,system-ui,-apple-system,sans-serif;}
a{color:var(--accent);text-decoration:none;}
a:hover{text-decoration:underline;}
header.top{display:flex;justify-content:space-between;align-items:center;gap:16px;
  flex-wrap:wrap;padding:14px 22px;border-bottom:1px solid var(--line);}
.brand{font-weight:700;color:var(--ink);font-size:1.02rem;}
.brand span{color:var(--muted);font-weight:400;}
header.top nav{display:flex;gap:18px;font-size:.92rem;}
main{max-width:780px;margin:0 auto;padding:30px 20px 60px;}
h1{font-size:1.7rem;line-height:1.25;margin:.2em 0 .5em;}
h2{font-size:1.25rem;margin-top:1.6em;}
h3{font-size:1.05rem;margin-top:1.4em;}
.crumb{color:var(--muted);font-size:.85rem;letter-spacing:.4px;text-transform:uppercase;margin:0;}
.lede{font-size:1.08rem;}
.muted{color:var(--muted);}
code{background:#222833;border-radius:5px;padding:1px 5px;font-size:.86em;
     font-family:ui-monospace,Menlo,monospace;}
pre{background:var(--card);border:1px solid var(--line);border-radius:12px;
    padding:14px 16px;overflow-x:auto;line-height:1.45;}
pre code{background:none;padding:0;font-size:.84rem;}
blockquote{margin:1.2em 0;padding:2px 18px;border-left:3px solid var(--line);color:var(--muted);}
blockquote.think{border-left:3px solid var(--think);background:rgba(198,120,221,.07);
  border-radius:0 10px 10px 0;color:var(--ink);padding:10px 18px;}
.think-label{display:inline-block;font-size:.72rem;font-weight:700;letter-spacing:.8px;
  text-transform:uppercase;color:var(--think);margin-right:8px;}
table{border-collapse:collapse;margin:1.1em 0;font-size:.92rem;display:block;overflow-x:auto;}
th,td{border:1px solid var(--line);padding:6px 11px;text-align:left;}
th{background:var(--card);}
.glance{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:6px 18px 12px;margin:1.2em 0;}
.glance summary{cursor:pointer;font-weight:600;padding:8px 0;}
.hands-on{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:14px 18px;margin:1.2em 0;}
.hands-on h2{margin:0 0 10px;font-size:1rem;}
.chip{display:inline-block;background:#222833;border:1px solid var(--line);
  border-radius:999px;padding:6px 14px;margin:3px 6px 3px 0;font-size:.9rem;color:var(--ink);}
.chip:hover{border-color:var(--accent);text-decoration:none;}
.note{background:rgba(110,168,254,.08);border:1px solid rgba(110,168,254,.3);
  border-radius:12px;padding:10px 16px;margin:1.2em 0;font-size:.93rem;}
.pending{background:var(--card);border:1px dashed var(--line);border-radius:12px;
  padding:14px 18px;margin:1.4em 0;color:var(--muted);}
.phase{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:16px 20px;margin:18px 0;}
.phase h2{margin:0 0 2px;font-size:1.1rem;}
.phase p{margin:.2em 0 .7em;font-size:.9rem;}
ul.units{list-style:none;margin:0;padding:0;}
ul.units li{display:flex;justify-content:space-between;gap:10px;align-items:baseline;
  padding:7px 0;border-top:1px solid var(--line);flex-wrap:wrap;}
ul.units a{color:var(--ink);}
.unum{display:inline-block;min-width:1.6em;color:var(--muted);font-variant-numeric:tabular-nums;}
.badges{display:flex;gap:6px;}
.badge{font-size:.68rem;letter-spacing:.5px;text-transform:uppercase;border-radius:999px;
  padding:2px 9px;border:1px solid var(--line);color:var(--muted);}
.badge.lesson{color:var(--good);border-color:rgba(46,204,113,.4);}
.badge.widget{color:var(--accent);border-color:rgba(110,168,254,.4);}
.badge.quiz{color:var(--warn);border-color:rgba(240,168,104,.4);}
.badge.exercise{color:var(--think);border-color:rgba(198,120,221,.4);}
footer.pager{max-width:780px;margin:0 auto;padding:0 20px 50px;display:flex;
  justify-content:space-between;gap:14px;flex-wrap:wrap;}
footer.pager a{font-size:.92rem;}
footer.pager .next{margin-left:auto;}
article.lesson{margin-top:1.6em;border-top:1px solid var(--line);padding-top:.4em;}
"""


def main() -> None:
    SITE.mkdir(exist_ok=True)
    curriculum = (LEARNING / "curriculum.md").read_text()
    (SITE / "style.css").write_text(STYLE)
    build_index()
    build_unit_pages(curriculum)
    build_document_pages(curriculum)
    pages = sorted(p.name for p in SITE.glob("*.html"))
    print(f"built {len(pages)} pages -> {SITE}")
    print(" ".join(pages))


if __name__ == "__main__":
    main()
