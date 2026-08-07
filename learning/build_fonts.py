"""Fetch and subset the course's web fonts into learning/site/fonts/.

The site is delivered as static files that must open from ``file://`` with no
network, so the typefaces have to ship *with* the repo. Full variable fonts are
~1MB each; subsetting to the character ranges the course actually uses cuts
that by roughly 90%. The subset ``.woff2`` files are committed, so a fresh
clone renders correctly without running anything -- this script exists to make
that generation reproducible and auditable, not because the build needs it.

    pip install "fonttools[woff]" brotli     # dev-only, like `markdown`
    python learning/build_fonts.py

Why these four faces:

- **Source Serif 4** (roman + italic) carries the body and display text. It is
  a screen-first text serif with genuine italics, and the course is ~24,000
  words of argumentative prose -- a reading experience before it is a
  reference.
- **Inter** carries the *graphic* layer only: eyebrows, badges, nav, table
  headers, anything set in caps and tracked out. Keeping the UI voice separate
  from the reading voice is what stops the two from muddling each other.
- **JetBrains Mono** carries code, ARPAbet, and -- checked, not assumed -- the
  full box-drawing range the lesson diagrams use (U+2500-257F).
- **Charis SIL** is a *fallback face only*, subset to about a dozen glyphs.
  Source Serif 4 has no IPA extensions, and the lessons set IPA inline in
  running prose (``/ɪ/``, ``[tʰ]``, the tap ``[ɾ]``). Without this, those
  characters drop to whatever system serif the reader happens to have --
  precisely the mismatched look the design pass exists to remove. Charis is
  SIL International's own linguistics face, so the coverage is guaranteed and
  the color sits close enough to Source Serif to pass unnoticed at inline size.
  It is last in every ``font-family`` stack; browsers fall back per *glyph*, so
  it only ever paints the handful of characters the primary face lacks.

Licensing: all four are SIL Open Font License. The OFL text for each is
copied next to the fonts, which is what the license requires for redistribution.
"""

from __future__ import annotations

import io
import pathlib
import sys
import urllib.request

try:
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
except ImportError:  # pragma: no cover - dev-only tool
    sys.exit('build_fonts.py needs fonttools: pip install "fonttools[woff]" brotli')

LEARNING = pathlib.Path(__file__).resolve().parent
FONTS = LEARNING / "site" / "fonts"
UPSTREAM = "https://raw.githubusercontent.com/google/fonts/main/ofl"

# ---------------------------------------------------------------------------
# Character coverage
# ---------------------------------------------------------------------------
# Ranges, not the exact characters in today's Markdown: the course is still
# being written, and a subset tight enough to break when someone types "café"
# is a trap. latin + latin-ext is the standard Google Fonts split and costs
# only a few KB more than an exact subset.

LATIN = (
    "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,"
    "U+2000-206F,U+2074,U+20AC,U+2122,U+2212,U+2215,U+FEFF,U+FFFD"
)
# Deliberately *not* the full Google "latin-ext": U+1E00-1EFF (Latin Extended
# Additional, mostly Vietnamese) and U+A720-A7FF together cost ~25 KB per face
# and cover nothing this course can plausibly need. Extended-A plus a handful
# of strays is the honest range.
LATIN_EXT = "U+0100-017F,U+0192,U+01FA-01FF,U+0218-021B,U+0259,U+2020"
ARROWS = "U+2190-21FF"          # → ← ↔ ⇒, used in prose and diagrams
MATH = "U+2200-22FF"            # ≈ ≤ ≥ ∅
BOX = "U+2500-257F"             # the lesson diagrams' box-drawing frames
SHAPES = "U+25A0-25FF,U+2713"   # ● ◄ ▸ ▾ ✓ -- code blocks only
IPA = "U+0250-02AF,U+02B0,U+02C8,U+02CC"  # IPA extensions + the used modifiers

# Axis limits. `opsz` (optical size) is the single biggest cost in both Source
# Serif 4 and Inter -- keeping it more than doubles each file. Pinning it near
# text size and controlling display sizing explicitly in CSS (weight, tracking,
# and line-height) costs about 240 KB less and gives more predictable results
# than letting the browser interpolate. `wght` stays a range: one file has to
# serve the whole type ramp, from 300 captions to 800 display.
TEXT_AXES = {"opsz": 18, "wght": (300, 900)}
ITALIC_AXES = {"opsz": 18, "wght": (400, 700)}
UI_AXES = {"opsz": 20, "wght": (400, 800)}
MONO_AXES = {"wght": (400, 700)}

# (upstream path, output stem, unicode ranges, axis limits)
FACES = [
    ("sourceserif4/SourceSerif4%5Bopsz,wght%5D.ttf", "source-serif-4",
     f"{LATIN},{LATIN_EXT},{ARROWS},{MATH}", TEXT_AXES),
    ("sourceserif4/SourceSerif4-Italic%5Bopsz,wght%5D.ttf", "source-serif-4-italic",
     f"{LATIN},{LATIN_EXT},{ARROWS},{MATH}", ITALIC_AXES),
    ("inter/Inter%5Bopsz,wght%5D.ttf", "inter",
     f"{LATIN},{LATIN_EXT},{ARROWS}", UI_AXES),
    ("jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf", "jetbrains-mono",
     f"{LATIN},{LATIN_EXT},{ARROWS},{MATH},{BOX},{SHAPES}", MONO_AXES),
    # Fallback face: the IPA block, plus the three symbols Source Serif lacks.
    # Nothing else -- it must never win a glyph the primary face can paint
    # itself, and it is last in every font-family stack for that reason.
    ("charissil/CharisSIL-Regular.ttf", "charis-sil-ipa",
     f"{IPA},U+2194,U+21D2,U+2205", None),
]

LICENSES = [
    ("sourceserif4/OFL.txt", "OFL-SourceSerif4.txt"),
    ("inter/OFL.txt", "OFL-Inter.txt"),
    ("jetbrainsmono/OFL.txt", "OFL-JetBrainsMono.txt"),
    ("charissil/OFL.txt", "OFL-CharisSIL.txt"),
]


def fetch(path: str) -> bytes:
    with urllib.request.urlopen(f"{UPSTREAM}/{path}", timeout=120) as response:
        return response.read()


def subset_to_woff2(raw: bytes, stem: str, unicodes: str, axes: dict | None) -> int:
    """Subset `raw` to `unicodes`, clamp its axes, write site/fonts/<stem>.woff2.

    Order matters: subset first, then instance. Running the instancer over the
    full font and subsetting after raises KeyError on glyphs the subsetter has
    already dropped from the variation tables.
    """
    font = TTFont(io.BytesIO(raw))
    options = subset.Options()
    options.flavor = "woff2"
    options.retain_gids = False
    options.desubroutinize = False
    options.layout_features = ["*"]        # keep kerning, ligatures, tnum
    options.name_IDs = ["*"]
    options.notdef_outline = True
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=subset.parse_unicodes(unicodes))
    subsetter.subset(font)
    if axes and "fvar" in font:
        font = instancer.instantiateVariableFont(font, axes, updateFontNames=False)
    out = FONTS / f"{stem}.woff2"
    font.flavor = "woff2"
    font.save(out)
    return out.stat().st_size


def main() -> None:
    FONTS.mkdir(parents=True, exist_ok=True)
    total = 0
    for path, stem, unicodes, axes in FACES:
        raw = fetch(path)
        size = subset_to_woff2(raw, stem, unicodes, axes)
        total += size
        print(f"  {stem + '.woff2':<32} {size / 1024:>7.1f} KB"
              f"   (from {len(raw) / 1024:.0f} KB upstream)")
    for path, name in LICENSES:
        (FONTS / name).write_bytes(fetch(path))
    print(f"\n  {len(FACES)} faces, {total / 1024:.1f} KB total -> {FONTS}")


if __name__ == "__main__":
    main()
