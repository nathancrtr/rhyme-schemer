"""Derive per-vowel Bark formant means from Hillenbrand et al. (1995).

Dev-only. Run from anywhere:

    python learning/audits/derive_hillenbrand_bark.py

It downloads the upstream data (once, into a gitignored cache), averages it,
and rewrites ``hillenbrand_1995_bark.py`` next to this file. That generated
module is the only Hillenbrand-derived artifact the repo commits. The raw
measurements and the recordings stay upstream.

**The data.** Hillenbrand, Getty, Clark & Wheeler (1995), "Acoustic
characteristics of American English vowels", JASA 97(5):3099-3111,
doi:10.1121/1.411872. Talkers (45 men, 48 women, 46 children) read 12
vowels in /hVd/ words ("heed", "hid", "hayed" ...). For each token the file
``vowdata.dat`` gives F1-F3 in Hz at the vowel's steady state and at 20%,
50% and 80% of its duration. We fetch it from Santiago Barreda's MIT-licensed
mirror, hosted with Hillenbrand's permission, pinned to one commit and
checked against a SHA-256 so the derived numbers can't drift silently:
https://github.com/santiagobarreda/hillenbrand_et_al_1995

**What "derive" means here**, step by step:

1. Keep the talker groups a condition asks for (``m`` men, ``w`` women).
2. Drop any token where a formant the condition uses is 0. In this file 0
   means "not measurable", not 0 Hz.
3. Convert Hz to Bark with Traunmüller's (1990) formula
   ``z = 26.81 f / (1960 + f) - 0.53``. Bark is an auditory frequency
   scale that follows the ear's critical bands: roughly linear below about
   500 Hz, roughly logarithmic above. Distance in Bark is closer to how far
   apart two vowels *sound* than distance in Hz.
4. For Lobanov conditions only, z-score each formant within each talker
   (subtract that talker's mean, divide by their standard deviation). This
   is a standard way to remove talker differences such as vocal-tract
   length before pooling men with women.
5. Average per vowel.

Each condition below is one row of the Bark audit (``audit_bark.py``). The
two-time-point conditions keep the 20% and 80% samples separate, because the
audit's distance compares a vowel's start with the other vowel's start and
end with end, the same way ``features.vowel_distance`` treats a diphthong.

Hillenbrand's codes map to ARPAbet as below. Two look odd but are right:
``ah`` is "hod" (the vowel of "cot", ARPAbet AA) and ``aw`` is "hawed"
(AO). The mirror's README spells "hayed" ``ey``; the data file itself uses
``ei``, and that is what we match.
"""

from __future__ import annotations

import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path
from statistics import mean, pstdev

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
OUTPUT = HERE / "hillenbrand_1995_bark.py"

UPSTREAM_COMMIT = "7fee5b548ad3898b1d0be3755253f1cb33ad083d"
UPSTREAM_URL = (
    "https://raw.githubusercontent.com/santiagobarreda/hillenbrand_et_al_1995/"
    f"{UPSTREAM_COMMIT}/h95-alldata.zip"
)
UPSTREAM_SHA256 = "2560548591e3a726c88549b6dc9d226995616c26874d601c69fee8b9eee9d730"

HILLENBRAND_TO_ARPABET = {
    "ae": "AE", "ah": "AA", "aw": "AO", "eh": "EH", "er": "ER", "ei": "EY",
    "ih": "IH", "iy": "IY", "oa": "OW", "oo": "UH", "uh": "AH", "uw": "UW",
}

# vowdata.dat column numbers (1-indexed, as its header lists them).
STEADY = {"F1": 4, "F2": 5, "F3": 6}
AT_20 = {"F1": 8, "F2": 9, "F3": 10}
AT_80 = {"F1": 14, "F2": 15, "F3": 16}

# name -> (talker groups, time points as column dicts, formants, Lobanov?)
CONDITIONS = {
    "steady_f1f2_men": (("m",), (STEADY,), ("F1", "F2"), False),
    "t20_80_f1f2_men": (("m",), (AT_20, AT_80), ("F1", "F2"), False),
    "t20_80_f1f2f3_men": (("m",), (AT_20, AT_80), ("F1", "F2", "F3"), False),
    "lobanov_t20_80_f1f2_men_women": (("m", "w"), (AT_20, AT_80), ("F1", "F2"), True),
    "lobanov_t20_80_f1f2f3_men_women": (
        ("m", "w"), (AT_20, AT_80), ("F1", "F2", "F3"), True,
    ),
}

# Four decimals is far finer than any formant tracker's accuracy (0.0001
# Bark is a few hundredths of a Hz), and enough that rounding never changes
# a rank in the audit.
DECIMALS = 4


def bark(hz: float) -> float:
    """Traunmüller (1990): Hz to Bark."""
    return 26.81 * hz / (1960 + hz) - 0.53


def fetch_vowdata() -> str:
    """Return the text of ``vowdata.dat``, downloading the zip on first use."""
    CACHE.mkdir(exist_ok=True)
    archive = CACHE / "h95-alldata.zip"
    if not archive.exists():
        print(f"downloading {UPSTREAM_URL}")
        with urllib.request.urlopen(UPSTREAM_URL) as response:
            archive.write_bytes(response.read())
    data = archive.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != UPSTREAM_SHA256:
        raise SystemExit(
            f"{archive} has SHA-256 {digest}, expected {UPSTREAM_SHA256}. "
            "Delete it to re-download, or investigate the upstream change."
        )
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        return bundle.read("vowdata.dat").decode("ascii")


def parse(text: str) -> list[tuple[str, str, str, list[int]]]:
    """(group, talker, ARPAbet vowel, the 16 columns as ints) per token.

    Only data rows have exactly 16 fields and a filename like ``m01ae``; the
    header's prose lines and column-number row are skipped by that test.
    Column 1 (the filename) is kept as 0 so list index = column number - 1.
    """
    tokens = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 16 or fields[0][3:5] not in HILLENBRAND_TO_ARPABET:
            continue
        name = fields[0]
        columns = [0] + [int(x) for x in fields[1:]]
        tokens.append((name[0], name[:3], HILLENBRAND_TO_ARPABET[name[3:5]], columns))
    return tokens


def derive(tokens, groups, time_points, formants, lobanov):
    """Per-vowel mean Bark vectors, plus the token count behind each mean.

    A token's vector is its formants at each time point, flattened in order
    (F1@20, F2@20, F1@80, F2@80 for a two-point F1/F2 condition).
    """
    columns = [point[f] for point in time_points for f in formants]
    by_talker: dict[str, list[tuple[str, list[float]]]] = {}
    for group, talker, vowel, values in tokens:
        if group not in groups:
            continue
        hz = [values[c - 1] for c in columns]
        if 0 in hz:
            continue
        by_talker.setdefault(talker, []).append((vowel, [bark(f) for f in hz]))

    pooled: dict[str, list[list[float]]] = {}
    for talker_tokens in by_talker.values():
        if lobanov:
            k = len(columns)
            mu = [mean(t[1][i] for t in talker_tokens) for i in range(k)]
            sd = [pstdev([t[1][i] for t in talker_tokens]) or 1.0 for i in range(k)]
            talker_tokens = [
                (v, [(x[i] - mu[i]) / sd[i] for i in range(k)]) for v, x in talker_tokens
            ]
        for vowel, vector in talker_tokens:
            pooled.setdefault(vowel, []).append(vector)

    width = len(formants)
    result = {}
    for vowel in sorted(pooled):
        flat = [round(mean(c), DECIMALS) for c in zip(*pooled[vowel])]
        points = tuple(tuple(flat[i : i + width]) for i in range(0, len(flat), width))
        result[vowel] = (points, len(pooled[vowel]))
    return result


def render_module(derived: dict) -> str:
    lines = [
        '"""Per-vowel Bark formant means from Hillenbrand et al. (1995). GENERATED.',
        "",
        "Do not edit by hand. Regenerate with",
        "``python learning/audits/derive_hillenbrand_bark.py``, whose docstring",
        "explains every step (token filtering, Hz to Bark, optional Lobanov",
        "normalization, averaging) and the data's provenance.",
        "",
        "Source: Hillenbrand, Getty, Clark & Wheeler (1995), JASA 97(5):3099-3111,",
        "doi:10.1121/1.411872, via the MIT-licensed mirror at",
        "https://github.com/santiagobarreda/hillenbrand_et_al_1995",
        f"(commit {UPSTREAM_COMMIT[:12]}), hosted with Hillenbrand's permission.",
        "",
        "Talker dialect: mostly raised in southern Michigan (Hillenbrand 2003),",
        "i.e. Northern Cities Shift territory. No AY, AW or OY: the 1995 study",
        "recorded 12 /hVd/ vowels only.",
        "",
        "``CONDITIONS[name][vowel]`` is a tuple of time points (one for steady",
        "state, two for 20% and 80%); each time point is a tuple of formants in",
        "Bark (or Lobanov z-units), F1 first. ``TOKENS`` holds the token count",
        "behind each mean, after dropping unmeasurable formants.",
        '"""',
        "",
        "CONDITIONS = {",
    ]
    for name, by_vowel in derived.items():
        lines.append(f"    {name!r}: {{")
        for vowel, (points, _) in by_vowel.items():
            lines.append(f"        {vowel!r}: {points!r},")
        lines.append("    },")
    lines += ["}", "", "TOKENS = {"]
    for name, by_vowel in derived.items():
        counts = ", ".join(f"{v!r}: {n}" for v, (_, n) in by_vowel.items())
        lines.append(f"    {name!r}: {{{counts}}},")
    lines += ["}", ""]
    return "\n".join(lines)


def main() -> None:
    tokens = parse(fetch_vowdata())
    derived = {
        name: derive(tokens, *spec) for name, spec in CONDITIONS.items()
    }
    OUTPUT.write_text(render_module(derived))
    print(f"wrote {OUTPUT.relative_to(HERE.parents[1])} ({len(tokens)} tokens parsed)")


if __name__ == "__main__":
    main()
