"""Build the course site: learning/site/ from the Markdown sources.

The course is delivered as a static, file://-friendly site -- every page
opens by double-click, no server, no network. This script is the whole
build system: it renders the lesson guides and course documents
(python-markdown), wraps them in a shared shell (sticky header, unit
switcher, theme toggle, section rail, prev/next footer), assembles per-unit
pages that combine the unit's syllabus entry with its lesson and hands-on
material, and writes the stylesheet. Markdown stays the source of truth; the
generated site is committed so a fresh clone is browsable without running
anything.

Regenerate after editing any lesson or curriculum.md:

    pip install markdown           # dev-only dependency (not in requirements.txt)
    python learning/build_site.py

The typefaces are a separate, rarely-run step -- the subset .woff2 files are
committed, so you only need this if you change the character coverage:

    pip install "fonttools[woff]" brotli
    python learning/build_fonts.py

Conventions the build enforces:
- "> PAUSE. ..." blockquotes in lessons render as think-first boxes -- the
  reader is asked to commit to an answer before scrolling on (the browser
  descendant of the old Socratic pause).
- Links to lesson .md files are rewritten to their unit pages.
- Widgets/quizzes/exercises stay where they live (interactive/); unit pages
  link to them relatively, so the site works from any checkout location.
- Prose gets typographic punctuation (curly quotes, proper dashes and
  ellipses) via python-markdown's `smarty`. The sources are written with
  straight quotes; making the *renderer* responsible for typography means
  nobody has to type a curly quote to get one, and code spans are left
  alone because smarty never touches them.
- Every h2/h3 in body prose gets a stable id and a hover anchor, which is
  also what feeds the sticky section rail.

Design lives in learning/style_source.py -- including why it looks like this.
"""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

import markdown

import style_source
from style_source import KIND_HUE, PHASE_HUE

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
         quiz=("Phase 2 checkpoint", "interactive/quizzes/phase-2-checkpoint.html"),
         companion=("The sequence-alignment family", "sequence-alignment-family.md")),
    dict(num=9, phase=3, title="Multi-word spans & pronunciation variants",
         lesson="unit-09-variants-and-spans.md",
         widgets=[("Rhyme-Score Sandbox", "interactive/widgets/rhyme-score-sandbox.html")]),
    dict(num=10, phase=3, title="Grouping rhymes: similarity graphs & components",
         lesson="unit-10-non-transitivity.md",
         widgets=[("Grouping Explorer", "interactive/widgets/grouping-explorer.html")],
         quiz=("Phase 3 checkpoint", "interactive/quizzes/phase-3-checkpoint.html"),
         exercise=("unit-10-grouping", "interactive/exercises/unit-10-grouping"),
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
         lesson="unit-13-g2p.md",
         quiz=("Phase 4 checkpoint", "interactive/quizzes/phase-4-checkpoint.html"),
         exercise=("unit-13-g2p-extension", "interactive/exercises/unit-13-g2p-extension")),
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

# Companion pages, so the unit switcher can offer them too.
COMPANIONS = [
    ("phonetics-primer.html", "How speech works: a phonetics refresher"),
    ("sequence-alignment-family.html", "The sequence-alignment family"),
    ("graphs-and-union-find.html", "Graphs, components, and union-find"),
]

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

# `smarty` gives the prose real typography; the sources are written with
# straight quotes on purpose, so that nobody has to type a curly one.
MD_EXTENSIONS = ["fenced_code", "tables", "smarty"]


def md_to_html(text: str) -> str:
    text = _LIST_AFTER_PARAGRAPH.sub(r"\1\n\n", text)
    html = markdown.markdown(text, extensions=MD_EXTENSIONS)
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


# ---------------------------------------------------------------------------
# Headings: ids, hover anchors, and the section rail they feed
# ---------------------------------------------------------------------------

_HEADING = re.compile(r"<(h[23])>(.*?)</\1>", re.DOTALL)


def slugify(label: str) -> str:
    slug = re.sub(r"<[^>]+>", "", label)
    slug = html_mod.unescape(slug).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug or "section"


def anchor_headings(html: str) -> tuple[str, list[tuple[str, str, str]]]:
    """Give body h2/h3 stable ids + hover anchors; return the TOC alongside.

    Ids are slugs of the heading text, de-duplicated with a numeric suffix so
    that two "Common confusions" sections on one page still get distinct
    targets (unit 11 has repeats).
    """
    toc: list[tuple[str, str, str]] = []
    seen: dict[str, int] = {}

    def replace(match: re.Match[str]) -> str:
        tag, inner = match.group(1), match.group(2)
        base = slugify(inner)
        seen[base] = seen.get(base, 0) + 1
        ident = base if seen[base] == 1 else f"{base}-{seen[base]}"
        label = html_mod.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        toc.append((tag, ident, label))
        anchor = (f'<a class="anchor" href="#{ident}" aria-hidden="true" '
                  f'tabindex="-1">#</a>')
        return f'<{tag} id="{ident}">{anchor}{inner}</{tag}>'

    return _HEADING.sub(replace, html), toc


# ---------------------------------------------------------------------------
# Purpose-built layouts for the two reference documents
# ---------------------------------------------------------------------------
# The syllabus and the resources list are not prose -- they are records, and
# almost every line of both is a "**Label:** value" bullet. Rendered as
# bullets they are a wall: fifteen units whose Build/Read/Concepts/Exercise
# fields all look alike, and nothing to scan by. Nobody reads a syllabus; they
# look things up in one. So the labels get a column of their own, units become
# numbered entries that link to their pages (the old syllabus said every unit
# had a page but linked to none of them), and resource type tags stop being
# inline code and become badges.

_INNER_UL = re.compile(r"<ul>((?:(?!</?ul>).)*?)</ul>", re.S)
_FIELD_LI = re.compile(r"<li>\s*<strong>([^<:]{2,30}):</strong>\s*(.*?)</li>", re.S)


def field_lists(html: str) -> str:
    """A bullet list whose every item opens '**Label:**' is a definition list."""
    def convert(match: re.Match[str]) -> str:
        block = match.group(1)
        fields = _FIELD_LI.findall(block)
        # Only convert when *every* item fits the shape; a mixed list stays a list.
        if len(fields) < 2 or len(fields) != block.count("<li>"):
            return match.group(0)
        rows = "".join(f"<dt>{html_mod.escape(key)}</dt><dd>{value.strip()}</dd>"
                       for key, value in fields)
        return f'<dl class="fields">{rows}</dl>'
    return _INNER_UL.sub(convert, html)


UNIT_PHASE = {unit["num"]: unit["phase"] for unit in UNITS}

_SYL_UNIT = re.compile(
    r"<h3>Unit (\d+) &mdash; (.*?)</h3>\s*(<dl class=\"fields\">.*?</dl>)"
    r"|<h3>Unit (\d+) — (.*?)</h3>\s*(<dl class=\"fields\">.*?</dl>)", re.S)
_SYL_CHECKPOINT = re.compile(r"<h3>—\s*(Phase \d+ Checkpoint)\s*—</h3>")


def syllabus_layout(html: str) -> str:
    html = field_lists(html)

    def unit(match: re.Match[str]) -> str:
        groups = [g for g in match.groups() if g is not None]
        num, title, fields = int(groups[0]), groups[1], groups[2]
        hue = PHASE_HUE[UNIT_PHASE.get(num, 1)]
        return (f'<section class="uentry" style="--accent:var(--hue-{hue})">'
                f'<div class="ue-num">{num}</div><div class="ue-body">'
                f"<h3>{title}</h3>{fields}"
                f'<a class="ue-go" href="unit-{num:02d}.html">Open Unit {num}</a>'
                f"</div></section>")

    html = _SYL_UNIT.sub(unit, html)
    return _SYL_CHECKPOINT.sub(r'<p class="checkpoint">\1</p>', html)


# Resource type -> hue slot, so the badges stay categorical rather than decorative.
RESOURCE_HUE = {"TEXT": 0, "PAPER": 4, "CODE": 1, "TOOL": 2,
                "INTERACTIVE": 7, "VIDEO": 5}
_RES_TAGS = re.compile(r"\s*<code>((?:\[[A-Z]+\])+)</code>")
# Everything from an h3 up to the next heading is that resource's entry.
# Matching the *body* rather than a specific list shape matters: only about a
# third of the entries are pure "**Label:** value" lists. The rest mix those
# with citation lines ("**Kondrak (2000),** *A New Algorithm...*"), which are
# genuinely a list and should stay one. Every entry still becomes a card.
_RES_ENTRY = re.compile(r"<h3>(.*?)</h3>(.*?)(?=<h[123]|\Z)", re.S)


_RES_LEGEND = re.compile(r"<p>Tags:\s*<code>((?:\[[A-Z]+\]\s*)+)</code>\.?</p>")


def resources_layout(html: str) -> str:
    html = field_lists(html)

    # The "Tags: [TEXT] [CODE] ..." legend is the key to the badges, so it
    # should be made of badges rather than of inline code.
    def legend(match: re.Match[str]) -> str:
        badges = "".join(
            f'<span class="rtag" style="--accent:var(--hue-'
            f'{RESOURCE_HUE.get(tag, 3)})">{tag}</span>'
            for tag in re.findall(r"[A-Z]+", match.group(1)))
        return f'<p class="legend-row">Tags <span class="rtags">{badges}</span></p>'

    html = _RES_LEGEND.sub(legend, html)

    def entry(match: re.Match[str]) -> str:
        title, body = match.group(1), match.group(2)
        found: list[str] = []
        title = _RES_TAGS.sub(
            lambda m: found.extend(re.findall(r"[A-Z]+", m.group(1))) or "", title)
        hue = RESOURCE_HUE.get(found[0], 3) if found else 3
        badges = "".join(
            f'<span class="rtag" style="--accent:var(--hue-'
            f'{RESOURCE_HUE.get(tag, 3)})">{tag}</span>' for tag in found)
        head = f'<div class="rtags">{badges}</div>' if badges else ""
        return (f'<section class="res" style="--accent:var(--hue-{hue})">'
                f"{head}<h3>{title.strip()}</h3>{body.strip()}</section>")

    return _RES_ENTRY.sub(entry, html)


def rail_html(toc: list[tuple[str, str, str]]) -> str:
    """The sticky "on this page" rail. Omitted when there is nothing to steer by."""
    if len([t for t in toc if t[0] == "h2"]) < 2:
        return ""
    items = []
    for tag, ident, label in toc:
        cls = ' class="sub"' if tag == "h3" else ""
        items.append(f'<li{cls}><a href="#{ident}">{html_mod.escape(label)}</a></li>')
    return ('<aside class="rail" aria-label="On this page"><h2>On this page</h2>'
            f'<ol>{"".join(items)}</ol></aside>')


# ---------------------------------------------------------------------------
# Chrome
# ---------------------------------------------------------------------------

def unit_switcher(current: str | None) -> str:
    """A native <details> menu of the whole course. Works from file:// with no JS."""
    groups = []
    for phase_num, (title, _blurb) in PHASES.items():
        hue = PHASE_HUE[phase_num]
        rows = []
        for unit in UNITS:
            if unit["phase"] != phase_num:
                continue
            page = f'unit-{unit["num"]:02d}.html'
            mark = ' aria-current="page"' if page == current else ""
            rows.append(f'<a href="{page}"{mark}><span class="n">{unit["num"]}</span>'
                        f'<span>{html_mod.escape(unit["title"])}</span></a>')
        groups.append(f'<h4 style="--accent:var(--hue-{hue})">Phase {phase_num} &middot; '
                      f'{html_mod.escape(title)}</h4>{"".join(rows)}')
    extras = "".join(
        f'<a href="{page}"{" aria-current=\"page\"" if page == current else ""}>'
        f'<span class="n">&middot;</span><span>{html_mod.escape(label)}</span></a>'
        for page, label in COMPANIONS)
    groups.append(f'<h4>Companion reading</h4>{extras}')
    label = "Course contents"
    if current and current.startswith("unit-"):
        label = f"Unit {int(current[5:7])}"
    return ('<details class="switch"><summary>' + label + '</summary>'
            f'<div class="switch-menu">{"".join(groups)}</div></details>')


THEME_TOGGLE = """<button class="theme" type="button" id="theme-toggle"
  aria-label="Switch between light and dark">
<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
  stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.2v2M12 19.8v2
  M2.2 12h2M19.8 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/></svg>
<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
  stroke-linecap="round" stroke-linejoin="round"><path d="M20 14.5A8.2 8.2 0 0 1 9.5 4
  a8.2 8.2 0 1 0 10.5 10.5z"/></svg></button>"""

# Runs before first paint, so an explicit choice never flashes the other mode.
THEME_BOOT = ('<script>(function(){try{var t=localStorage.getItem("rs-theme");'
              'if(t==="light"||t==="dark")document.documentElement.dataset.theme=t;}'
              'catch(e){}})();</script>')

# Toggle + rail scrollspy, written out as site/course.js so the eleven
# hand-authored widget and quiz pages can link the same file instead of each
# carrying its own copy. Both features degrade to nothing if JS is off: the
# theme still follows the OS, and the rail still works as plain anchor links.
COURSE_JS = """(function(){
  var root=document.documentElement, btn=document.getElementById("theme-toggle");
  if(btn) btn.addEventListener("click",function(){
    var dark=root.dataset.theme
      ? root.dataset.theme==="dark"
      : matchMedia("(prefers-color-scheme:dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try{localStorage.setItem("rs-theme",root.dataset.theme);}catch(e){}
  });
  var links=[].slice.call(document.querySelectorAll(".rail a"));
  if(!links.length||!window.IntersectionObserver) return;
  var byId={};
  links.forEach(function(a){ byId[a.getAttribute("href").slice(1)]=a; });
  var visible={};
  var obs=new IntersectionObserver(function(entries){
    entries.forEach(function(e){ visible[e.target.id]=e.isIntersecting; });
    var current=null;
    Object.keys(byId).forEach(function(id){ if(visible[id]&&!current) current=id; });
    links.forEach(function(a){ a.classList.remove("on"); });
    if(current&&byId[current]) byId[current].classList.add("on");
  },{rootMargin:"-88px 0px -70% 0px"});
  Object.keys(byId).forEach(function(id){
    var el=document.getElementById(id); if(el) obs.observe(el);
  });
})();
"""

SITE_JS = '<script src="course.js"></script>'


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@TITLE@</title>
<link rel="stylesheet" href="style.css">
@BOOT@
</head>
<body@BODYATTR@>
<header class="top">
  <div class="top-in">
    <a class="brand" href="index.html">rhyme-schemer <span>&middot; the course</span></a>
    @SWITCHER@
    <nav>
      <a href="index.html"@NAV_INDEX@>Units</a>
      <a href="syllabus.html"@NAV_SYLL@>Syllabus</a>
      <a href="resources.html"@NAV_RES@>Resources</a>
      <a href="about.html"@NAV_ABOUT@>About</a>
      @THEME@
    </nav>
  </div>
</header>
<div class="shell">
<main>
@CONTENT@
</main>
@RAIL@
</div>
<footer class="pager">
@PAGER@
</footer>
<div class="foot">Generated from Markdown by <code>learning/build_site.py</code>.
Type: Source Serif&nbsp;4, Inter, JetBrains&nbsp;Mono, Charis&nbsp;SIL &mdash; all
<a href="https://openfontlicense.org">SIL&nbsp;OFL</a>.</div>
@JS@
</body>
</html>
"""


def write_page(name: str, title: str, content: str, pager: str = "",
               rail: str = "", accent: int | None = None) -> None:
    body_attr = f' style="--accent:var(--hue-{accent})"' if accent is not None else ""
    html = (PAGE.replace("@TITLE@", title)
                .replace("@BOOT@", THEME_BOOT)
                .replace("@BODYATTR@", body_attr)
                .replace("@SWITCHER@", unit_switcher(name))
                .replace("@THEME@", THEME_TOGGLE)
                .replace("@CONTENT@", content)
                .replace("@RAIL@", rail)
                .replace("@PAGER@", pager)
                .replace("@JS@", SITE_JS))
    for token, page in (("@NAV_INDEX@", "index.html"), ("@NAV_SYLL@", "syllabus.html"),
                        ("@NAV_RES@", "resources.html"), ("@NAV_ABOUT@", "about.html")):
        html = html.replace(token, ' aria-current="page"' if name == page else "")
    (SITE / name).write_text(html)


def pager_link(direction: str, href: str, label: str) -> str:
    word = "Previous" if direction == "prev" else "Next"
    return (f'<a class="{direction}" href="{href}"><span class="dir">{word}</span>'
            f'<span class="ttl">{html_mod.escape(label)}</span></a>')


def curriculum_extract(curriculum: str, num: int) -> str:
    """The '### Unit N' section of curriculum.md, minus its heading."""
    match = re.search(
        rf"^### Unit {num} — .*?$\n(.*?)(?=^### |^## |^---)",
        curriculum, re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def chip(kind: str, label: str, href: str) -> str:
    """One hands-on link. The dot carries the type; no emoji.

    Full-colour emoji (the old prefixes) read as clip-art beside a palette
    this restrained, and they are the first thing that makes a page look
    unconsidered. A hue dot plus a tracked micro-label says the same thing
    in the design system's own voice.
    """
    hue = KIND_HUE[kind]
    return (f'<a class="chip" href="{href}" style="--accent:var(--hue-{hue})">'
            f'<span>{html_mod.escape(label)}</span>'
            f'<span class="kind">{kind}</span></a>')


def hands_on_card(unit: dict) -> str:
    rows = []
    for label, path in unit.get("widgets", []):
        rows.append(chip("widget", label, f"../{path}"))
    if unit.get("quiz"):
        label, path = unit["quiz"]
        rows.append(chip("quiz", label, f"../{path}"))
    if unit.get("exercise"):
        label, path = unit["exercise"]
        rows.append(chip("exercise", label, f"../{path}/task.md"))
    if unit.get("companion"):
        label, md_name = unit["companion"]
        page = LINK_MAP.get(md_name, md_name)
        rows.append(chip("companion", label, page))
    if not rows:
        return ""
    return ('<div class="hands-on"><h2>Hands-on</h2>'
            f'<div class="chips">{"".join(rows)}</div></div>')


def build_unit_pages(curriculum: str) -> None:
    for i, unit in enumerate(UNITS):
        num = unit["num"]
        phase_title = PHASES[unit["phase"]][0]
        hue = PHASE_HUE[unit["phase"]]
        # The unit number rides in the eyebrow, not the h1: "Unit 4 -- " in
        # front of a real title pushed several headings to three display-size
        # lines and buried the words that name the unit.
        parts = [
            '<div class="masthead">',
            f'<p class="crumb"><b>Unit {num}</b><span class="sep">/</span>'
            f'Phase {unit["phase"]} &middot; {html_mod.escape(phase_title)}</p>',
            f'<h1>{html_mod.escape(unit["title"])}</h1>',
            '</div>',
        ]
        extract = curriculum_extract(curriculum, num)
        if extract:
            parts.append('<details class="glance" open><summary>The unit at a glance '
                         '<span class="muted">from the syllabus</span></summary>'
                         + md_to_html(extract) + "</details>")
        parts.append(hands_on_card(unit))

        toc: list[tuple[str, str, str]] = []
        if unit.get("lesson"):
            lesson_md = (LESSONS / unit["lesson"]).read_text()
            # The lesson file's own H1 duplicates the page title; drop it.
            lesson_md = re.sub(r"^# .*\n", "", lesson_md, count=1)
            note = unit.get("lesson_note")
            if note:
                parts.append('<div class="note">' + md_to_html(note)[3:-4] + "</div>")
            lesson_html, toc = anchor_headings(md_to_html(lesson_md))
            parts.append('<article class="lesson">' + lesson_html + "</article>")
        else:
            parts.append(
                '<div class="pending">The full guide for this unit is still being '
                "written; the syllabus entry above is the map in the meantime. "
                "Guides land unit by unit as the course build-out continues.</div>")

        pager = ""
        if i > 0:
            p = UNITS[i - 1]
            pager += pager_link("prev", f'unit-{p["num"]:02d}.html',
                                f'Unit {p["num"]}: {p["title"]}')
        if i < len(UNITS) - 1:
            n = UNITS[i + 1]
            pager += pager_link("next", f'unit-{n["num"]:02d}.html',
                                f'Unit {n["num"]}: {n["title"]}')
        write_page(f"unit-{num:02d}.html", f"Unit {num} — {unit['title']}",
                   "\n".join(p for p in parts if p), pager,
                   rail_html(toc), accent=hue)


def build_index() -> None:
    cards = []
    for phase_num, (title, blurb) in PHASES.items():
        hue = PHASE_HUE[phase_num]
        rows = []
        for unit in UNITS:
            if unit["phase"] != phase_num:
                continue
            badges = []
            for kind, present in (("guide", unit.get("lesson")),
                                  ("widget", unit.get("widgets")),
                                  ("quiz", unit.get("quiz")),
                                  ("exercise", unit.get("exercise"))):
                if present:
                    badges.append(
                        f'<span class="badge" style="--accent:var(--hue-{KIND_HUE[kind]})"'
                        f' title="{kind}"><span>{kind}</span></span>')
            rows.append(
                f'<li><a href="unit-{unit["num"]:02d}.html">'
                f'<span class="unum">{unit["num"]}</span>'
                f'<span class="utitle">{html_mod.escape(unit["title"])}</span>'
                f'<span class="badges">{"".join(badges)}</span></a></li>')
        cards.append(
            f'<section class="phase" style="--accent:var(--hue-{hue})">'
            f'<div class="phase-hd"><p class="phase-n">Phase {phase_num}</p>'
            f'<h2>{html_mod.escape(title)}</h2>'
            f'<p>{html_mod.escape(blurb)}</p></div>'
            f'<ul class="units">{"".join(rows)}</ul></section>')

    content = (
        '<div class="masthead">'
        "<h1>Computational phonetics, one rhyme detector at a time</h1>"
        '<p class="lede">A self-contained course on NLP and computational phonology, taught '
        "through a single worked project: <b>rhyme-schemer</b>, a tool that reads hip-hop "
        "lyrics and surfaces their rhyme scheme &mdash; slant rhyme, assonance, and all. You read "
        "real modules, build the missing ones, and every concept arrives already attached to "
        "code that uses it.</p>"
        '<p class="lede muted">For the linguistics-curious programmer: the phonology is taught '
        "from the ground up; the algorithms assume fluency in code but not a background in "
        'algorithm design. Start with <a href="about.html">how this course works</a> &mdash; and if '
        'your phonetics is cold (or was never warm), <a href="phonetics-primer.html">the sounds '
        "refresher</a> rebuilds it in twenty minutes, mostly by making you make sounds at your "
        "desk.</p></div>"
        + SPECIMEN
        + "".join(cards))
    write_page("index.html", "rhyme-schemer: the course", content)


# The hero specimen: a stretch of the project's own engineered test verse with
# its rhyme classes painted in the renderer's hue slots. It is hand-marked
# rather than generated, so the site build never depends on the package
# importing cleanly -- but the classes and colours are the real ones.
SPECIMEN = """
<div class="specimen">
<p class="cap">What you are building</p>
<p><span class="rw" style="--accent:var(--hue-0)">My palms</span> are <span
class="rw" style="--accent:var(--hue-1)">steady</span>, my <span
class="rw" style="--accent:var(--hue-0)">arms</span> are <span
class="rw" style="--accent:var(--hue-1)">ready</span><br>I <span
class="rw" style="--accent:var(--hue-2)">wake up</span>, <span
class="rw" style="--accent:var(--hue-2)">shake the whole state up</span><br>I&rsquo;m <span
class="rw" style="--accent:var(--hue-4)">nervous</span>, but my <span
class="rw" style="--accent:var(--hue-4)">verses</span> stay <span
class="rw" style="--accent:var(--hue-1)">steady</span></p>
</div>
"""


def build_document_pages(curriculum: str) -> None:
    resources = (LEARNING / "learning-resources.md").read_text()
    body, toc = anchor_headings(resources_layout(md_to_html(resources)))
    write_page("resources.html", "Resources",
               '<div class="masthead"><p class="crumb">Course reference</p></div>'
               + body, rail=rail_html(toc))

    body, toc = anchor_headings(syllabus_layout(md_to_html(curriculum)))
    write_page("syllabus.html", "Syllabus",
               '<div class="masthead"><p class="crumb">Course reference</p></div>'
               '<p class="note">The complete syllabus, one page &mdash; every unit here '
               'links to its own page, with the lesson and hands-on material.</p>' + body,
               rail=rail_html(toc))

    seq = (LESSONS / "sequence-alignment-family.md").read_text()
    body, toc = anchor_headings(md_to_html(seq))
    write_page("sequence-alignment-family.html", "The sequence-alignment family",
               '<div class="masthead"><p class="crumb">Companion reading &middot; Unit 8</p>'
               '</div>' + body,
               pager_link("next", "unit-08.html", "Unit 8: Unequal lengths: sequence alignment"),
               rail_html(toc), accent=PHASE_HUE[2])

    primer = (LESSONS / "phonetics-primer.md").read_text()
    body, toc = anchor_headings(md_to_html(primer))
    write_page("phonetics-primer.html", "How speech works: a phonetics refresher",
               '<div class="masthead"><p class="crumb">On-ramp &middot; before Unit 1</p>'
               '</div>' + body,
               pager_link("next", "unit-01.html", "Unit 1: Phonemes, ARPAbet & the lexicon"),
               rail_html(toc), accent=PHASE_HUE[1])

    dsu = (LESSONS / "graphs-and-union-find.md").read_text()
    body, toc = anchor_headings(md_to_html(dsu))
    write_page("graphs-and-union-find.html", "Graphs, components, and union-find from zero",
               '<div class="masthead"><p class="crumb">Companion reading &middot; Unit 10</p>'
               '</div>' + body,
               pager_link("next", "unit-10.html", "Unit 10: Grouping rhymes"),
               rail_html(toc), accent=PHASE_HUE[3])

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
`learning/build_site.py`; edit the source, not the HTML. The design system
lives in `learning/style_source.py` and the subset webfonts are built by
`learning/build_fonts.py`.
"""
    body, toc = anchor_headings(md_to_html(about))
    write_page("about.html", "About this course",
               '<div class="masthead"><p class="crumb">Orientation</p></div>' + body,
               pager_link("next", "index.html", "Browse the units"),
               rail_html(toc))


def main() -> None:
    SITE.mkdir(exist_ok=True)
    curriculum = (LEARNING / "curriculum.md").read_text()
    (SITE / "style.css").write_text(style_source.stylesheet())
    (SITE / "course.js").write_text(COURSE_JS)
    build_index()
    build_unit_pages(curriculum)
    build_document_pages(curriculum)
    pages = sorted(p.name for p in SITE.glob("*.html"))
    print(f"built {len(pages)} pages -> {SITE}")
    print(" ".join(pages))


if __name__ == "__main__":
    main()
