"""Guess pronunciations for words CMUdict doesn't know (Unit 13).

Every layer below this one starts from a dictionary pronunciation;
out-of-vocabulary words have been skip-and-flagged since Unit 3. This module
replaces the skip with a guess -- but "grapheme-to-phoneme" for hip-hop
lyrics is not one problem, it is a **fallback chain**, because OOV words
come in kinds (measured on the fixture corpus and CMUdict itself):

1. **Dialect spellings of known words** ("chokin'", "flossin'", "holla") --
   recoverable by *rules* that lean on the dictionary.
2. **A closed class of slang contractions** ("imma", "finna") -- not
   rule-derivable ("imma" is "I'm gonna"); a small hand **lexicon** is the
   honest answer.
3. **Genuinely unknown strings** (brands like "Coogi", onomatopoeia like
   "blaow", coinages like "bling") -- only **letter-to-sound** rules can
   say anything, and what they say is a guess.

The chain tries each in order: dictionary, lexicon, normalization rules,
letter-to-sound (see ``pronounce`` for why the lexicon outranks the rules). This dictionary-first-with-fallback shape is the same
architecture the field converged on -- ``g2p_en`` is a CMUdict lookup with a
seq2seq model behind it, and Epitran, rule-based for most languages, leans
on a lexicon for English precisely because English spelling is too irregular
for rules alone (Unit 1's founding lesson, now load-bearing). A neural
fallback could slot in behind the same ``Guess`` interface later; Unit 13
deliberately stops at hand rules.

**The design principle for the rules: dialect spellings are performance
transcriptions.** The obvious normalization -- "chokin'" *is* "choking", so
look it up and stop -- is subtly wrong: the apostrophe is the lyricist
transcribing what they actually say, coda N rather than NG, and N-vs-NG is
exactly the kind of coda difference the rhyme kernel scores. Likewise the
final -a of "holla"/"gangsta" testifies to a non-rhotic AH0 that rhymes
with "follow", where dictionary "holler"'s ER0 does not. So every rule
recovers the dictionary *stem* and then **keeps the spelled surface
phonology** -- look up "choking", then rewrite NG to N *because the spelling
says so*. This is Unit 11's move one layer down: the dictionary records
citation facts, the performance overrides them, and we mint the performed
form as data.

The rules encode *documented* vernacular and AAE phonology, not invented
respellings -- each rule's docstring cites the sociolinguistics of its
feature, and the README's dialect note states the position outright:
performed AAE phonology is ground truth here, not noise to normalize away.

**Confidence is priced, not modeled.** A letter-to-sound guess is an
unlikely claim of the same species as a coerced stress, and it travels the
same road: ``Guess.cost`` is folded into ``Reading.cost`` at candidate
minting (scan.py), so a guessed pronunciation must buy its way into a rhyme
while the kernel and ``models.py`` stay provenance-free -- a dictionary
pronunciation and a guessed one are both just ``Pronunciation``s. Rule- and
lexicon-derived forms cost nothing (the spelling or the lexicon testifies);
letter-to-sound pays ``DEFAULT_LTS_COST``. Words the whole chain fails
(no vowel to guess: "brrr") remain OOV, and ``source`` lets the scanner and
renderer say *how* a pronunciation was obtained without peeking inside it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pronouncing

from .models import Pronunciation
from .phonetics import VOWELS
from .syllabify import syllabify

# The prior on a letter-to-sound guess, subtracted from any match built on
# one (same mechanism as scan.DEFAULT_COERCION_COST -- an explicit thumb on
# the scale, not a probability). Hand-written English letter-to-sound is
# wrong often enough that a marginal rhyme should not survive being built on
# it, while a strong one ("Coogi"~"groovy" at 1.0) shrugs it off. Tune at
# Unit 14 with everything else.
DEFAULT_LTS_COST = 0.1

# Guess.source values, in chain order. Renderers and receipts key off these;
# only LETTER_TO_SOUND carries a cost.
DICTIONARY = "dictionary"
G_DROP = "g-drop"
STEM_SUFFIX = "stem+-in'"
A_FOR_ER = "-a-for-er"
LEXICON = "lexicon"
LETTER_TO_SOUND = "letter-to-sound"
OOV = "oov"


@dataclass(frozen=True)
class Guess:
    """One word's pronunciations plus the receipt for how they were got.

    ``pronunciations`` empty means the whole chain failed (the word stays
    OOV). ``cost`` is the per-word price scoring must pay to use these
    pronunciations; ``source`` names the chain link that produced them.
    """

    pronunciations: tuple[Pronunciation, ...]
    cost: float
    source: str


# Slang contractions the dictionary lacks and no spelling rule can derive
# ("imma" is "I'm gonna"; nothing about the letters says so). A closed
# class, so a hand lexicon is the honest tool. Flat ARPAbet, dictionary
# convention. Deliberately small; extend as real lyrics expose gaps.
_LEXICON: dict[str, tuple[str, ...]] = {
    "imma": ("AY1 M AH0",),
    "finna": ("F IH1 N AH0",),
    "gonna": ("G AH1 N AH0",),
    "gon": ("G AA1 N",),
    "gon'": ("G AA1 N",),
    "shoulda": ("SH UH1 D AH0",),
    "woulda": ("W UH1 D AH0",),
    "coulda": ("K UH1 D AH0",),
    "tryna": ("T R AY1 N AH0",),
    "yall": ("Y AO1 L",),
    "gimme": ("G IH1 M IY0",),
    "lemme": ("L EH1 M IY0",),
}


def _variants(word: str) -> list[list[str]]:
    """Raw CMUdict variants for ``word`` as token lists ([] if OOV)."""
    return [v.split() for v in pronouncing.phones_for_word(word.lower())]


def _mint(word: str, variants: list[list[str]]) -> tuple[Pronunciation, ...]:
    """Syllabify token-list variants into ``Pronunciation``s for ``word``.

    Variants that syllabify to nothing (no vowel anywhere) are dropped: a
    pronunciation with no nucleus can't carry a rhyme, or even a syllable.
    """
    minted = []
    for tokens in variants:
        syllables = syllabify(tokens)
        if syllables:
            minted.append(Pronunciation(syllables=syllables, text=word))
    return tuple(minted)


# --- Normalization rules: dictionary-stem + spelled surface phonology -------

_G_DROP_RE = re.compile(r"[a-z]+in'?$")


def _g_drop(word: str) -> tuple[str, list[list[str]]] | None:
    """Recover "-in'" spellings from their dictionary "-ing" relatives.

    Two lookups, most faithful first: the full "-ing" form ("chokin'" via
    "choking"), then the bare stem with common orthography undone -- as
    written ("flossin'" via "floss"), restoring a dropped silent e
    ("stylin'" via "style"), and undoing consonant doubling ("runnin'" via
    "run"). Either way the spelled ending wins: the final NG the dictionary
    would supply is rewritten to the N the lyricist wrote, or IH0 N is
    appended to the stem and the whole thing re-syllabified (the Maximal
    Onset Principle moves the stem's final consonant into the new
    syllable's onset, exactly as in speech).

    The feature this encodes is the classic sociolinguistic **(ING)
    variable** -- coronal [n] for velar [ng] in unstressed -ing -- the
    founding variable of variationist sociolinguistics (Fischer 1958,
    *Word* 14:47-56) and part of AAE's documented phonology (Green 2002,
    *African American English*, CUP). It is pan-vernacular English, not
    AAE-exclusive; "-in'" is simply its standard written transcription.
    """
    if not _G_DROP_RE.fullmatch(word):
        return None
    bare = word.rstrip("'")

    ing_variants = _variants(bare + "g")
    if ing_variants:
        rewritten = [
            tokens[:-1] + ["N"] if tokens[-1] == "NG" else tokens
            for tokens in ing_variants
        ]
        return G_DROP, rewritten

    stem = bare[:-2]
    candidates = [stem, stem + "e"]
    if len(stem) >= 2 and stem[-1] == stem[-2]:
        candidates.append(stem[:-1])
    for candidate in candidates:
        stem_variants = _variants(candidate)
        if stem_variants:
            return STEM_SUFFIX, [
                tokens + ["IH0", "N"] for tokens in stem_variants
            ]
    return None


def _a_for_er(word: str) -> tuple[str, list[list[str]]] | None:
    """Recover non-rhotic "-a" spellings from dictionary "-er" relatives.

    "holla"/"gangsta" spell out a performed non-rhotic vowel: final AH0,
    which rhymes with "follow", not dictionary "holler"'s ER0. Look up the
    "-er" form, then keep the spelled phonology by rewriting its final ER
    to AH -- the stress digit carries over, since dropping the r doesn't
    move the beat.

    The feature is AAE **non-rhoticity**: coda /r/ vocalizes, and Thomas
    (2007, *Language and Linguistics Compass* 1:450-475) records that
    r-lessness "is most common in unstressed syllables, as in over,
    brother" -- precisely this rule's final unstressed -er environment.
    Tuning-ledger item 11 generalizes the same feature beyond spelled
    testimony (non-rhotic readings for standard spellings, priced).
    """
    if len(word) < 3 or not word.endswith("a"):
        return None
    variants = _variants(word[:-1] + "er")
    rewritten = [
        tokens[:-1] + ["AH" + tokens[-1][2:]]
        for tokens in variants
        if tokens[-1].startswith("ER")
    ]
    return (A_FOR_ER, rewritten) if rewritten else None


# --- Letter-to-sound: the guessing end of the chain -------------------------

# Longest-match-first grapheme patterns. Deliberately crude: no magic-e
# lengthening, no soft-g, one guess per pattern -- expressive hip-hop
# spellings ("blaow") mostly bypass literary orthography anyway, and
# DEFAULT_LTS_COST prices the crudeness. Extend as real lyrics expose gaps;
# replace wholesale with a neural model behind the same Guess interface if
# Unit 14 shows these rules are the bottleneck.
_LTS_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("aow", ("AW",)),  # expressive: "blaow"
    ("igh", ("AY",)),
    ("tch", ("CH",)),
    ("ch", ("CH",)), ("sh", ("SH",)), ("th", ("TH",)), ("ph", ("F",)),
    ("wh", ("W",)), ("ck", ("K",)), ("ng", ("NG",)), ("qu", ("K", "W")),
    ("ee", ("IY",)), ("ea", ("IY",)), ("oo", ("UW",)),
    ("ou", ("AW",)), ("ow", ("AW",)), ("oa", ("OW",)),
    ("ai", ("EY",)), ("ay", ("EY",)), ("oi", ("OY",)), ("oy", ("OY",)),
    ("au", ("AO",)), ("aw", ("AO",)),
    ("ar", ("AA", "R")), ("or", ("AO", "R")),
    ("er", ("ER",)), ("ir", ("ER",)), ("ur", ("ER",)),
)

_LTS_SINGLE: dict[str, tuple[str, ...]] = {
    "a": ("AE",), "b": ("B",), "d": ("D",), "e": ("EH",), "f": ("F",),
    "g": ("G",), "h": ("HH",), "i": ("IH",), "j": ("JH",), "k": ("K",),
    "l": ("L",), "m": ("M",), "n": ("N",), "o": ("AA",), "p": ("P",),
    "r": ("R",), "s": ("S",), "t": ("T",), "u": ("AH",), "v": ("V",),
    "w": ("W",), "x": ("K", "S"), "z": ("Z",),
}


def _letter_to_sound(word: str) -> list[str] | None:
    """Map a spelling to ARPAbet tokens by greedy longest-match rules.

    The handful of context rules earn their keep on real OOV data: soft c
    ("Coogi" needs K, "ice"-likes need S), y as consonant/vowel by
    position, silent final e, doubled letters collapsed ("brrr" collapses
    to B R -- and having no vowel, correctly fails). Stress is assigned
    crudely: first vowel PRIMARY, the rest UNSTRESSED -- wrong for many
    words, but anchor enumeration (Unit 11) re-stresses candidates anyway,
    so inside the scanner only the *number* of syllables and their vowel
    qualities survive; the citation-stress guess matters only to direct
    kernel calls.
    """
    spelling = word.lower().replace("'", "")
    if not spelling.isalpha():
        return None
    # Collapse letter runs, but not to the point of destroying digraphs:
    # runs of 3+ go to one ("brrr" -> "br"), then doubled *consonants* to
    # one ("holla" -> "hola") -- doubled vowels stay, because "oo"/"ee" are
    # patterns with their own sound ("Coogi" needs its UW).
    spelling = re.sub(r"(.)\1{2,}", r"\1", spelling)
    spelling = re.sub(r"([^aeiou])\1", r"\1", spelling)
    if len(spelling) > 2 and spelling.endswith("ie"):
        spelling = spelling[:-1]  # "homie" -> "homi"; final i says IY below
    elif len(spelling) > 2 and spelling.endswith("e"):
        if spelling[-2] not in "aeiouy":  # silent final e
            spelling = spelling[:-1]

    tokens: list[str] = []
    i = 0
    while i < len(spelling):
        for pattern, phones in _LTS_PATTERNS:
            if spelling.startswith(pattern, i):
                tokens.extend(phones)
                i += len(pattern)
                break
        else:
            letter = spelling[i]
            if letter == "c":
                tokens.append("S" if spelling[i + 1: i + 2] in
                              ("e", "i", "y") else "K")
            elif letter == "y":
                if i == 0:
                    tokens.append("Y")
                elif i == len(spelling) - 1:
                    tokens.append("IY")
                else:
                    tokens.append("IH")
            elif letter == "i" and i == len(spelling) - 1:
                tokens.append("IY")  # final -i reads as -y: "Coogi"
            else:
                tokens.extend(_LTS_SINGLE.get(letter, ()))
            i += 1

    stressed, seen_vowel = [], False
    for token in tokens:
        if token in VOWELS:
            stressed.append(token + ("0" if seen_vowel else "1"))
            seen_vowel = True
        else:
            stressed.append(token)
    return stressed if seen_vowel else None


# --- The chain ---------------------------------------------------------------


def pronounce(word: str) -> Guess:
    """Pronounce ``word`` via the full fallback chain.

    Dictionary first (cost 0 -- this is a superset of
    ``syllabify.pronunciations_for``), then the slang lexicon, then the
    normalization rules (all cost 0: the lexicon or the spelling
    testifies), then letter-to-sound (cost ``DEFAULT_LTS_COST``: a guess
    must buy its way in). The lexicon outranks the rules because it is
    curated truth and the rules are pattern-matching: "shoulda" *matches*
    -a-for-er via "shoulder", but it contracts "should have", and only the
    lexicon knows that. A word the whole chain cannot voice comes back
    with no pronunciations and ``source=OOV`` -- the flag half of
    skip-and-flag, now meaning "even guessing failed" rather than "not in
    the dictionary".
    """
    key = word.lower()

    dictionary = _variants(key)
    if dictionary:
        return Guess(_mint(word, dictionary), 0.0, DICTIONARY)

    if key in _LEXICON:
        variants = [phones.split() for phones in _LEXICON[key]]
        return Guess(_mint(word, variants), 0.0, LEXICON)

    for rule in (_g_drop, _a_for_er):
        result = rule(key)
        if result:
            source, variants = result
            minted = _mint(word, variants)
            if minted:
                return Guess(minted, 0.0, source)

    tokens = _letter_to_sound(key)
    if tokens:
        minted = _mint(word, [tokens])
        if minted:
            return Guess(minted, DEFAULT_LTS_COST, LETTER_TO_SOUND)

    return Guess((), 0.0, OOV)
