# How Speech Works: a Phonetics Refresher

*A pre-Unit-1 primer for rhyme-schemer. If your linguistics is fresh, skim
the ARPAbet table at the end and skip ahead; if it's fifteen years cold — or
you never took the course — this rebuilds everything the project assumes, in
about twenty minutes, mostly by having you make sounds at your desk. Nobody
is watching. Make the sounds.*

---

## 1. The instrument

Every speech sound is shaped breath. Air leaves the lungs, passes through
the **larynx** (the voice box), and exits through the **vocal tract** — the
throat, mouth, and sometimes nose. Two decisions along the way define almost
everything:

- **At the larynx: do the vocal folds vibrate?** Rest a finger on your
  throat and sustain "ssssss," then "zzzzzz." Same mouth shape, same
  hiss — but the buzz under your finger switches on for the z. That buzz is
  **voicing**, and s/z, f/v, t/d, p/b, k/g are all the *same gesture* with
  voicing off vs on.
- **In the mouth: is the airflow obstructed?** Obstruct it somewhere and
  you get a **consonant**; let it flow freely and shape it with the tongue
  body and you get a **vowel**. That single distinction organizes the whole
  inventory.

## 2. Consonants: where and how you block the air

Two coordinates locate every consonant:

**Place** — *where* the blockage happens. Say "p… t… k" slowly and feel the
closure walk backwards: lips (bilabial), tongue-tip at the ridge behind
your teeth (alveolar), tongue-back at the soft palate (velar). English uses
about eight stations front-to-back; "f" (lip against teeth), "th" (tongue
between teeth), "sh" (just behind the ridge), and "h" (all the way back at
the glottis) fill in the map.

**Manner** — *how* the blockage shapes the air. A complete stop-and-release
("p," "t"): a **stop**. A tight channel that makes turbulence ("s," "f"): a
**fricative**. A stop released into a fricative ("ch"): an **affricate**.
Air rerouted through the nose ("m," "n," "ng"): a **nasal**. Nearly-open,
vowel-ish obstructions: **liquids** ("l," "r") and **glides** ("w," "y").

That ordering — stop, affricate, fricative, nasal, liquid, glide — runs from
least to most vowel-like, and it has a name you'll meet repeatedly:
**sonority**. Add voicing as a third coordinate and you can uniquely
describe every English consonant: "z" is a voiced alveolar fricative; "ng"
is a velar nasal. The project's `features.py` is literally this
three-coordinate description turned into numbers.

## 3. Vowels: shaping an open tube

> PAUSE. Sustain "eeee" and slide slowly to "aaaah" (as in *father*).
> Then sustain "eeee" and slide to "oooo." What is physically moving in
> each slide?

In the first slide your tongue body *drops* — that's the **height** axis
(close/high for "ee," open/low for "ah"). In the second it pulls *back*,
and your lips **round** — the **backness** axis plus **roundedness**. Those
three parameters are nearly the whole story of vowels, and the classic IPA
**vowel quadrilateral** is just a map of the first two: height on the
vertical, backness on the horizontal. The project places its fifteen vowels
on exactly this map.

Two English specialties to have back on the shelf:

- **Diphthongs.** Some vowels *move while you say them*: "bite" starts low
  and central, ends high and front. Say it in slow motion and feel the
  glide. A diphthong is honestly modeled as a start point and an end point
  — which is precisely how `features.py` stores AY, EY, OY, AW, OW.
- **The r-colored vowel.** "Bird" has no separate r-consonant in most
  American speech — the vowel itself is **rhotic**, said with a curled or
  bunched tongue. ARPAbet calls it `ER`, and its r-ness is a feature flag,
  not a following consonant. (Whether that r-color survives in *performed*
  hip-hop is a live question in this project — you'll meet non-rhotic AAE
  in Unit 13 and in the tuning ledger.)

## 4. Phonemes, phones, and why "the same sound" is subtle

Say "water" naturally. That middle consonant — the quick tap most
Americans produce — is physically nothing like the crisp, puffed "t" of
"top." (Hold your palm before your mouth: "top" puffs, "water" doesn't.)
Yet every English speaker files both under "t."

The mental category is a **phoneme** (written /t/); its physical
realizations — aspirated [tʰ], the tap [ɾ] — are **phones**, and
context-dependent variants of one phoneme are **allophones**. The test for
phoneme-hood is **contrast**: "bat" vs "pat" differ in exactly one sound
and mean different things, so /b/ and /p/ are different phonemes. No pair
of English words is distinguished by puffed-vs-tapped t, so those are one
phoneme wearing two costumes.

Why this matters here: CMUdict transcribes *phonemes* — the categories, not
the costumes. That's usually what rhyme wants. But the costumes sometimes
carry information the categories erase (that tapped t is part of why the
syllable boundary in "sweaty" is genuinely ambiguous — a story Unit 4 tells
properly), and performance can override citation categories entirely. The
project's recurring theme of *dictionary form vs performed form* is this
distinction, industrialized.

## 5. Stress, and the vowel that isn't there

> PAUSE. Say "PHOtograph," then "phoTOgraphy." Beyond the beat moving,
> what happens to the *vowels* in the unstressed syllables?

They collapse — toward the featureless mid-central vowel called **schwa**
(the "uh" in "about," IPA ə). English does this systematically: unstressed
syllables reduce, stressed ones keep full vowel quality. This is why stress
is not decoration for a rhyme engine but *structure*: the stressed syllable
is where vowel identity is reliable, which is why rhyme anchors there
(Unit 5's whole argument). CMUdict marks three levels on every vowel:
primary (1), secondary (2), unstressed (0).

## 6. Writing sound down: IPA and ARPAbet

The **IPA** gives every sound one unambiguous symbol (/ɪ/, /ŋ/, /ə/). It's
the field's standard and worth recognizing on sight — the
[interactive IPA chart](https://www.ipachart.com/) plays every symbol
aloud and is worth ten minutes of clicking.

For code, the project uses **ARPAbet**: ASCII names, vowels carrying a
stress digit. The fifteen vowels, with a keyword each — this table is worth
bookmarking for the whole course:

| ARPAbet | as in | | ARPAbet | as in |
|---|---|---|---|---|
| IY | b**ea**t | | AA | f**a**ther |
| IH | b**i**t | | AO | th**ough**t |
| EY | b**ai**t | | OW | b**oa**t |
| EH | b**e**t | | UH | b**oo**k |
| AE | b**a**t | | UW | b**oo**t |
| AH | b**u**t | | AY | b**i**te |
| ER | b**ir**d | | AW | b**ou**t |
| | | | OY | b**oy** |

Consonants are mostly what they look like (P B T D K G, F V S Z, M N L R
W), plus: **CH**/**JH** ("church"/"judge"), **SH**/**ZH** ("shoe"/
"measure"), **TH**/**DH** ("thin"/"then" — voiceless and voiced), **NG**
("sing"), **HH** ("hat"), **Y** ("yes"). So `S W EH1 T IY0` is "sweaty":
s + w + stressed EH + t + unstressed IY.

## 7. Where each idea lands in the course

Phonemes, ARPAbet, and the dictionary → **Unit 1**. The vowel map as a
similarity space → **Unit 2**. Place/manner/voicing as consonant
coordinates, and sonority → **Unit 3**. Syllables, and what sonority has to
do with their shape → **Unit 4**. Stress as the anchor of rhyme →
**Unit 5**. The dictionary-vs-performance gap → Units 9, 11, and 13,
repeatedly, because it turns out to be the project's most productive
tension.

> Check yourself: describe "z" and "ng" in three coordinates each; explain
> to an imaginary colleague why "water"'s middle consonant is /t/ at all;
> and transcribe "reason" into ARPAbet with stress digits before looking
> it up.
