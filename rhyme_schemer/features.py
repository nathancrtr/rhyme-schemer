"""Articulatory feature space for vowels, and a distance over it.

This is the heart of slant-rhyme detection. Hip-hop rhyme is driven by matching
vowel *sounds*, so we need a graded notion of "how close are two vowels?" rather
than equality.

We borrow the IPA vowel quadrilateral directly: every vowel is placed by tongue
**height** (open->close) and **backness** (front->back). Those two axes form a
coordinate plane, so vowel similarity becomes distance on that plane. We add two
smaller dimensions -- **roundedness** and a **rhotic** flag (for ER) -- and model
diphthongs as a glide between two points (start -> end); monophthongs have
start == end.

All coordinates are hand-placed approximations of cardinal IPA positions,
normalized to [0, 1]. They encode the standard lax-vowel centralization (e.g. ɪ
sits lower and more central than i), so the tense/lax contrast falls out of
position without a separate feature. This is the deliberately-small DIY table; a
library like panphon can replace it later.

A note on weights, prompted by ALINE (Kondrak 2000), which names a salience
weight for every feature it consults: two of ours are explicit (``_W_ROUND``,
``_W_RHOTIC``) but a third is not -- choosing the Euclidean metric on the plane
fixes the backness:height ratio at 1:1, silently. That 1:1 is a deliberate
default, not a finding; if evidence ever favors weighing height differently
from backness, the knob must first be made to exist before the Unit 14 sweep
can move it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .phonetics import strip_stress


@dataclass(frozen=True)
class VowelPoint:
    """A single position on the vowel chart, plus roundedness."""

    backness: float  # 0.0 = front, 0.5 = central, 1.0 = back
    height: float    # 0.0 = open/low, 1.0 = close/high
    rounded: float   # 0.0 = unrounded, 1.0 = rounded


@dataclass(frozen=True)
class VowelFeatures:
    """A vowel as a glide from ``start`` to ``end`` (equal for monophthongs)."""

    start: VowelPoint
    end: VowelPoint
    rhotic: bool = False

    @property
    def is_diphthong(self) -> bool:
        return self.start != self.end


def _mono(backness: float, height: float, rounded: float) -> VowelFeatures:
    point = VowelPoint(backness, height, rounded)
    return VowelFeatures(start=point, end=point)


def _diph(
    s_back: float, s_high: float, s_round: float,
    e_back: float, e_high: float, e_round: float,
) -> VowelFeatures:
    return VowelFeatures(
        start=VowelPoint(s_back, s_high, s_round),
        end=VowelPoint(e_back, e_high, e_round),
    )


# ARPAbet vowel -> articulatory features. Coordinates are approximate IPA
# positions (front=0/back=1, open=0/close=1), eyeballed from the vowel chart.
VOWEL_FEATURES: dict[str, VowelFeatures] = {
    # --- front unrounded, top to bottom ---
    "IY": _mono(0.00, 1.00, 0.0),   # i  (beat)
    "IH": _mono(0.20, 0.85, 0.0),   # ɪ  (bit)  -- lower & more central than IY
    "EH": _mono(0.10, 0.50, 0.0),   # ɛ  (bet)
    "AE": _mono(0.10, 0.20, 0.0),   # æ  (bat)
    # --- central ---
    "AH": _mono(0.50, 0.50, 0.0),   # ʌ/ə (but / about)
    "ER": VowelFeatures(            # ɝ  (bird) -- r-colored, central-mid
        start=VowelPoint(0.50, 0.55, 0.0),
        end=VowelPoint(0.50, 0.55, 0.0),
        rhotic=True,
    ),
    # --- back, bottom to top ---
    "AA": _mono(0.90, 0.00, 0.0),   # ɑ  (father / cot)
    "AO": _mono(0.90, 0.35, 1.0),   # ɔ  (thought)  -- rounded
    "UH": _mono(0.75, 0.85, 1.0),   # ʊ  (book)
    "UW": _mono(1.00, 1.00, 1.0),   # u  (boot)
    # --- diphthongs (start -> end) ---
    "EY": _diph(0.10, 0.65, 0.0,  0.20, 0.85, 0.0),  # eɪ (bait)
    "AY": _diph(0.50, 0.05, 0.0,  0.20, 0.85, 0.0),  # aɪ (bite)  -> ɪ offglide
    "OY": _diph(0.90, 0.35, 1.0,  0.20, 0.85, 0.0),  # ɔɪ (boy)   -> ɪ offglide
    "AW": _diph(0.50, 0.05, 0.0,  0.75, 0.85, 1.0),  # aʊ (bout)  -> ʊ offglide
    "OW": _diph(0.90, 0.60, 1.0,  0.80, 0.85, 1.0),  # oʊ (boat)  -> ʊ offglide
}

# Relative importance of the non-positional dimensions. Position (height x
# backness) is the dominant signal; rounding and rhoticity are nudges.
_W_ROUND = 0.3
_W_RHOTIC = 0.5

# Largest possible raw distance, used to normalize into [0, 1]. The position term
# maxes out at the plane diagonal sqrt(2); the others at their weights.
_MAX_RAW = math.sqrt(2) + _W_ROUND + _W_RHOTIC


def _plane_distance(p: VowelPoint, q: VowelPoint) -> float:
    """Euclidean distance on the height x backness plane."""
    return math.hypot(p.backness - q.backness, p.height - q.height)


def vowel_distance(a: str, b: str) -> float:
    """Distance in [0, 1] between two ARPAbet vowels (stress digits ignored).

    0.0 = identical vowel; larger = more dissimilar.
    """
    fa = VOWEL_FEATURES[strip_stress(a)[0]]
    fb = VOWEL_FEATURES[strip_stress(b)[0]]

    position = (_plane_distance(fa.start, fb.start) + _plane_distance(fa.end, fb.end)) / 2
    rounding = (abs(fa.start.rounded - fb.start.rounded) + abs(fa.end.rounded - fb.end.rounded)) / 2
    rhotic = 1.0 if fa.rhotic != fb.rhotic else 0.0

    raw = position + _W_ROUND * rounding + _W_RHOTIC * rhotic
    return raw / _MAX_RAW


def vowel_similarity(a: str, b: str) -> float:
    """Similarity in [0, 1]; 1.0 = identical vowel. Inverse of ``vowel_distance``."""
    return 1.0 - vowel_distance(a, b)


# ---------------------------------------------------------------------------
# Consonants
# ---------------------------------------------------------------------------
#
# Consonants get a parallel treatment to vowels: a 2-D plane plus a binary
# nudge. The two plane axes are PLACE (front -> back constriction) and MANNER
# (ordered by sonority: stop -> affricate -> fricative -> nasal -> liquid ->
# glide). Voicing plays the role rounding did for vowels. Consonants matter to
# rhyme mainly in the coda, and less than vowels overall -- that relative weight
# is applied later, in the rhyme scorer, not here.

# Place of articulation, front (0.0) to back (1.0).
_PLACE = {
    "bilabial": 0.00,
    "labiovelar": 0.10,   # W -- double articulation; we lean on its labiality
    "labiodental": 0.15,
    "dental": 0.25,
    "alveolar": 0.40,
    "postalveolar": 0.55,
    "palatal": 0.70,
    "velar": 0.85,
    "glottal": 1.00,
}

# Manner of articulation, ordered by sonority, obstruent (0.0) to glide (1.0).
_MANNER = {
    "stop": 0.00,
    "affricate": 0.15,
    "fricative": 0.30,
    "nasal": 0.55,
    "liquid": 0.75,
    "glide": 0.90,
}


@dataclass(frozen=True)
class ConsonantFeatures:
    place: float
    manner: float
    voiced: float  # 0.0 = voiceless, 1.0 = voiced


def _cons(place: str, manner: str, voiced: bool) -> ConsonantFeatures:
    return ConsonantFeatures(_PLACE[place], _MANNER[manner], 1.0 if voiced else 0.0)


# ARPAbet consonant -> articulatory features.
CONSONANT_FEATURES: dict[str, ConsonantFeatures] = {
    # stops
    "P": _cons("bilabial", "stop", False),
    "B": _cons("bilabial", "stop", True),
    "T": _cons("alveolar", "stop", False),
    "D": _cons("alveolar", "stop", True),
    "K": _cons("velar", "stop", False),
    "G": _cons("velar", "stop", True),
    # affricates
    "CH": _cons("postalveolar", "affricate", False),
    "JH": _cons("postalveolar", "affricate", True),
    # fricatives
    "F": _cons("labiodental", "fricative", False),
    "V": _cons("labiodental", "fricative", True),
    "TH": _cons("dental", "fricative", False),
    "DH": _cons("dental", "fricative", True),
    "S": _cons("alveolar", "fricative", False),
    "Z": _cons("alveolar", "fricative", True),
    "SH": _cons("postalveolar", "fricative", False),
    "ZH": _cons("postalveolar", "fricative", True),
    "HH": _cons("glottal", "fricative", False),
    # nasals
    "M": _cons("bilabial", "nasal", True),
    "N": _cons("alveolar", "nasal", True),
    "NG": _cons("velar", "nasal", True),
    # liquids
    "L": _cons("alveolar", "liquid", True),
    "R": _cons("postalveolar", "liquid", True),
    # glides
    "W": _cons("labiovelar", "glide", True),
    "Y": _cons("palatal", "glide", True),
}

# Voicing is a smaller perceptual cue than place/manner for rhyme.
_W_VOICE = 0.2
_MAX_RAW_C = math.sqrt(2) + _W_VOICE


def consonant_distance(a: str, b: str) -> float:
    """Distance in [0, 1] between two ARPAbet consonants. 0.0 = identical."""
    fa = CONSONANT_FEATURES[a]
    fb = CONSONANT_FEATURES[b]

    plane = math.hypot(fa.place - fb.place, fa.manner - fb.manner)
    voice = 1.0 if fa.voiced != fb.voiced else 0.0

    raw = plane + _W_VOICE * voice
    return raw / _MAX_RAW_C


def consonant_similarity(a: str, b: str) -> float:
    """Similarity in [0, 1]; 1.0 = identical consonant."""
    return 1.0 - consonant_distance(a, b)
