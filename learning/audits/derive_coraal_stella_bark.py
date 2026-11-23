"""Derive per-vowel Bark means for African American English from CORAAL.

Dev-only. Run from anywhere:

    python learning/audits/derive_coraal_stella_bark.py

It downloads two small upstream files (once, into the gitignored cache),
averages them, and rewrites ``coraal_dcb_stella_bark.py`` next to this
file. That generated module is the only CORAAL-derived artifact the repo
commits.

**Why this data.** The Bark audit's reference data, Hillenbrand et al.
(1995), comes from talkers raised in southern Michigan, and that dialect
shows up in the metric (tuning-ledger item 13d). Hip-hop's main dialect is
African American English (AAE). CORAAL, the Corpus of Regional African
American Language (Kendall & Farrington), is the openly licensed AAE
corpus. This script is a **proof of concept** built on its smallest
measured component: the "Please Call Stella" read passage recorded by the
Washington DC speakers of CORAAL:DCB (2015-2017), which the CORAAL team
released with per-vowel formant measurements already made (FAVE-extract,
on Montreal Forced Aligner boundaries) at 20%, 35%, 50%, 65% and 80% of
each vowel. No alignment or formant tracking happens here.

**Sources and license**, cited as the CORAAL user guide recommends:

- Farrington, Quartey, Tacata & Kendall (2023), *CORAAL:DCB Stella Passage
  (Washington DC 2016)*, version 2023.03, https://oraal.github.io/dcb-stella
  (the formant measurements);
- Kendall, Quartey, Farrington, McLarty, Arnson & Josler (2018), *The
  Corpus of Regional African American Language: DCB (Washington DC 2016)*,
  version 2018.10.06 (the speaker metadata);
- Kendall & Farrington (2023), *The Corpus of Regional African American
  Language*, version 2023.06, https://doi.org/10.7264/1ad5-6t35.

All are licensed CC BY-NC-SA 4.0, which requires derived versions to carry
the same license, so the generated module is CC BY-NC-SA 4.0 too.

**What "derive" means here**, step by step:

1. Keep adult men: ``Gender`` Male and ``Age`` 18 or over in the DCB
   speaker metadata (16 of the 22 men who read the passage). Men only, to
   match the audit's best Hillenbrand condition.
2. Keep primary-stressed vowels (FAVE's ``stress`` column is 1).
3. Drop the proclitics in ``scan.NEVER_ANCHOR`` ("a", "and", "the" ...).
   CMUdict lists stressed readings for them (the article "a" as EY1,
   "and" as AE1), and the aligner takes those labels, but in a read
   passage they are almost always said as schwa. They would drag EY and
   AE toward AH. The same list the scanner uses, for the same reason.
4. Drop vowels followed by R ("store", "for", "pears"): the R colors the
   vowel's formants, and Hillenbrand's /hVd/ frame has no such context.
5. Convert F1 and F2 at 20% and 80% to Bark (Traunmüller 1990, the same
   formula as ``derive_hillenbrand_bark.py``), average each speaker's
   tokens, then average across speakers, so a speaker who read a word
   twice doesn't count double.
6. Keep a vowel only if at least ``MIN_SPEAKERS`` of the 16 men produced
   it. UH falls out here: the passage's only UH word is one "could".
   AW never occurs in the passage at all.

The passage is short, so several vowels rest on one word per speaker
(AY is "five", OY is "toy", ER is "her", AO is mostly "call", "also" and
"small", all before L). The generated module records the words behind
each mean, so a reader can see that.
"""

from __future__ import annotations

import csv
import hashlib
import io
import sys
import tarfile
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from derive_hillenbrand_bark import CACHE, DECIMALS, bark  # noqa: E402

from rhyme_schemer.scan import NEVER_ANCHOR  # noqa: E402

OUTPUT = HERE / "coraal_dcb_stella_bark.py"

STELLA_URL = (
    "https://lingtools.uoregon.edu/coraal/supplements/DCB-stella_annotations.tar.gz"
)
STELLA_SHA256 = "9e461636417651253f34afc550ac0c56f27e605cc46e1e69b3b3d57b28254d8d"
METADATA_URL = (
    "https://lingtools.uoregon.edu/coraal/dcb/2018.10.06/DCB_metadata_2018.10.06.txt"
)
METADATA_SHA256 = "f705126709b364e915877108028f9eaf831f6f7c857dcdb93dfe26a3a193d913"

MIN_AGE = 18
MIN_SPEAKERS = 8
TIME_POINTS = (("F1@20%", "F2@20%"), ("F1@80%", "F2@80%"))


def fetch(url: str, expected_sha256: str) -> bytes:
    """Return a cached upstream file, downloading it on first use."""
    CACHE.mkdir(exist_ok=True)
    path = CACHE / url.rsplit("/", 1)[1]
    if not path.exists():
        print(f"downloading {url}")
        with urllib.request.urlopen(url) as response:
            path.write_bytes(response.read())
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise SystemExit(
            f"{path} has SHA-256 {digest}, expected {expected_sha256}. "
            "Delete it to re-download, or investigate the upstream change."
        )
    return data


def adult_men(metadata: bytes) -> set[str]:
    """Speaker ids of adult men. The file has one row per interview file,
    so a speaker can appear more than once; their age is the same each time."""
    rows = csv.DictReader(io.StringIO(metadata.decode("utf-8")), delimiter="\t")
    return {
        row["CORAAL.Spkr"]
        for row in rows
        if row["Gender"] == "Male" and int(row["Age"]) >= MIN_AGE
    }


def stella_tables(archive: bytes):
    """Yield (speaker id, rows) for each speaker's FAVE measurement table."""
    # "r:*" lets tarfile detect compression: despite its .tar.gz name, the
    # upstream archive is (as of version 2023.03) an uncompressed tar.
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as bundle:
        for member in bundle.getmembers():
            name = Path(member.name).name
            # Skip the _norm tables, FAVE's log files, and the "._" metadata
            # files macOS's tar adds beside every real file.
            if not name.endswith("_stella-out.txt") or name.startswith("._"):
                continue
            text = bundle.extractfile(member).read().decode("utf-8")
            yield name.split("_stella")[0], csv.DictReader(io.StringIO(text), delimiter="\t")


def derive(archive: bytes, speakers: set[str]):
    per_speaker = defaultdict(lambda: defaultdict(list))  # vowel -> speaker -> vectors
    words = defaultdict(Counter)
    for speaker, rows in stella_tables(archive):
        if speaker not in speakers:
            continue
        for row in rows:
            if row["stress"] != "1":
                continue
            if row["word"].lower() in NEVER_ANCHOR or row["fol_seg"] == "R":
                continue
            hz = [float(row[col]) for point in TIME_POINTS for col in point]
            if 0 in hz:
                continue
            per_speaker[row["vowel"]][speaker].append([bark(f) for f in hz])
            words[row["vowel"]][row["word"].lower()] += 1

    means, counts, dropped = {}, {}, {}
    for vowel in sorted(per_speaker):
        by_speaker = per_speaker[vowel]
        tokens = sum(len(v) for v in by_speaker.values())
        if len(by_speaker) < MIN_SPEAKERS:
            dropped[vowel] = (len(by_speaker), tokens)
            continue
        speaker_means = [[mean(c) for c in zip(*vectors)] for vectors in by_speaker.values()]
        flat = [round(mean(c), DECIMALS) for c in zip(*speaker_means)]
        means[vowel] = (tuple(flat[0:2]), tuple(flat[2:4]))
        counts[vowel] = (len(by_speaker), tokens, dict(words[vowel].most_common()))
    return means, counts, dropped


def render_module(means, counts, dropped, n_speakers) -> str:
    lines = [
        '"""Per-vowel Bark means for AAE, from CORAAL\'s DC read passage. GENERATED.',
        "",
        "License: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/),",
        "inherited from the sources below, whose license requires derived versions",
        "to carry it. Do not edit by hand. Regenerate with",
        "``python learning/audits/derive_coraal_stella_bark.py``, whose docstring",
        "explains every filtering step.",
        "",
        "Sources: Farrington, Quartey, Tacata & Kendall (2023), CORAAL:DCB Stella",
        "Passage (Washington DC 2016), version 2023.03,",
        "https://oraal.github.io/dcb-stella; Kendall, Quartey, Farrington, McLarty,",
        "Arnson & Josler (2018), CORAAL:DCB (Washington DC 2016), version",
        "2018.10.06 (speaker metadata); Kendall & Farrington (2023), The Corpus of",
        "Regional African American Language, version 2023.06,",
        "https://doi.org/10.7264/1ad5-6t35.",
        "",
        f"{n_speakers} adult men reading \"Please Call Stella\"; primary-stressed vowels,",
        "proclitics and pre-R vowels excluded. A proof of concept, not reference",
        "values: several vowels rest on one word per speaker (see WORDS).",
        "",
        "``MEANS[vowel]`` is ((F1, F2) at 20%, (F1, F2) at 80%), in Bark, averaged",
        "per speaker and then across speakers. ``SPEAKERS`` and ``TOKENS`` count",
        "what is behind each mean; ``DROPPED`` lists vowels with too few speakers.",
        '"""',
        "",
        "MEANS = {",
    ]
    lines += [f"    {v!r}: {points!r}," for v, points in means.items()]
    lines += ["}", "", "SPEAKERS = {"]
    lines += [f"    {v!r}: {c[0]}," for v, c in counts.items()]
    lines += ["}", "", "TOKENS = {"]
    lines += [f"    {v!r}: {c[1]}," for v, c in counts.items()]
    lines += ["}", "", "WORDS = {"]
    lines += [f"    {v!r}: {c[2]!r}," for v, c in counts.items()]
    lines += ["}", "", "# vowel -> (speakers, tokens), below the minimum of "
              f"{MIN_SPEAKERS} speakers", "DROPPED = {"]
    lines += [f"    {v!r}: {d!r}," for v, d in dropped.items()]
    lines += ["}", ""]
    return "\n".join(lines)


def main() -> None:
    speakers = adult_men(fetch(METADATA_URL, METADATA_SHA256))
    archive = fetch(STELLA_URL, STELLA_SHA256)
    readers = {speaker for speaker, _ in stella_tables(archive)} & speakers
    means, counts, dropped = derive(archive, speakers)
    OUTPUT.write_text(render_module(means, counts, dropped, len(readers)))
    print(
        f"wrote {OUTPUT.relative_to(HERE.parents[1])}: {len(means)} vowels "
        f"from {len(readers)} adult men; dropped {sorted(dropped)}"
    )


if __name__ == "__main__":
    main()
