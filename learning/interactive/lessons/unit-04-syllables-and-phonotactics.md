# Unit 4: Syllables & phonotactics — the Maximal Onset Principle

**Objective:** you can explain how a flat phoneme string becomes structured
syllables — onset, nucleus, coda — and why the boundary the code draws is a
*decision*, not a discovery. **Prerequisites:** Units 1–3. **Pairs with:**
`rhyme_schemer/syllabify.py`, `rhyme_schemer/models.py`, the onset tables in
`rhyme_schemer/phonetics.py`; the Syllabifier widget.

## The problem: CMUdict hands us a string, rhyme needs a structure

Look up "lincoln" and the dictionary gives you a flat sequence:

```
lincoln  →  L IH1 NG K AH0 N
```

No boundaries. But everything this project does downstream — the rhyme tail,
nucleus-versus-coda weighting, "onsets are ignored" — talks about *parts of
syllables*. Before any of that vocabulary means anything, six phonemes have
to become two structured syllables:

```
L IH1 NG . K AH0 N
```

Who decided the NG belongs to the *first* syllable and the K to the
*second*? That decision is this unit.

## Syllable anatomy: a sonority mountain

A syllable has three slots. The **nucleus** is its vowel — the peak. The
**onset** is the consonants that climb up to it; the **coda** is the
consonants that fall away after it. Nucleus + coda together form the
**rime** — the part that sounds alike in words that rhyme, which is why the
data model (`models.py`) gives `Syllable` a `.rime` property while no code
anywhere asks for "onset + nucleus."

"Climb" and "fall" are not metaphors here. Phonemes differ in **sonority** —
roughly, how loud and vowel-like they are: stops are the least sonorous,
then affricates, fricatives, nasals, liquids, glides, and vowels at the top.
A well-formed syllable rises in sonority to its nucleus and falls after it —
a mountain with the vowel at the summit. Say "plant" slowly: p (stop) →
l (liquid) → a (vowel) → n (nasal) → t (stop). Up, peak, down.

You have already met this hierarchy in the code: `features.py` orders its
consonant MANNER axis by sonority. That ordering does double duty — it makes
sonority-adjacent consonants *near* in the similarity space (Unit 3), and it
is the organizing principle behind which onsets English permits at all.

## Phonotactics: not every consonant string is a legal onset

**Phonotactics** is a language's rulebook for sound sequences. English
happily begins a syllable with "pl" (rising sonority: stop → liquid) but
never with "lp" (falling). The Sonority Sequencing Principle predicts most
of the rulebook for free.

Most — not all. English keeps a famous family of exceptions: /s/ + stop
clusters. "St", "sp", "sk", "str", "spl" all *fall* or plateau in sonority
on the way in (fricative → stop), and are all perfectly legal. Every
phonology textbook flags this; the /s/-clusters simply have to be listed.

> PAUSE. Before reading on: which of these should be legal English onsets?
> **"str"** (as in *street*), **"ngk"**, **"pn"** (as in... anything?),
> **"sw"** (as in *sweaty*). Commit to answers.

"Str" — legal, an /s/-exception. "Sw" — legal, rising (fricative → glide).
"Ngk" — illegal; NG can't even *start* an English syllable alone. "Pn" —
illegal in English (though fine in Greek, whence "pneumatic"; the p falls
silent in borrowing precisely because English phonotactics won't seat it).
Phonotactics is language-specific knowledge, which is why
`phonetics.is_legal_onset` is a hand-curated table and not a formula — the
table encodes SSP *plus* the exceptions, and it is deliberately
non-exhaustive: it grows when real lyrics expose a missing cluster (that's
this unit's exercise).

## The Maximal Onset Principle: the tiebreaker

Now back to "lincoln." Between the two vowels sits the cluster `NG K`.
Logically it could split three ways: both consonants left (`L IH NG K . AH N`),
both right (`L IH . NG K AH N`), or one each. Every option puts one nucleus
in each syllable; phonotactics alone doesn't force a unique answer. The
field's standard tiebreaker is the **Maximal Onset Principle**: give the
*following* syllable the longest onset that is still legal.

Try it: is `NG K` a legal onset? No. Is `K`? Yes. So K goes right, NG stays
left as coda: `L IH1 NG . K AH0 N`. That's the whole algorithm, and
`syllabify._split_consonants` is exactly this loop — try the longest suffix
of the cluster as an onset, shrink until `is_legal_onset` says yes, the
remainder is coda.

> PAUSE. Syllabify **"hypnotize"** (`HH IH1 P N AH0 T AY2 Z`) by hand
> before checking below. Two clusters to split: `P N` and `T`.

`P N`: is "pn" a legal onset? No (see above). Is "n"? Yes. So: `HH IH1 P .
N AH0 . T AY2 Z` — the p stays back as coda, exactly mirroring why English
speakers can't say "pneumatic" the Greek way. Single consonants like the `T`
always go right (a one-consonant onset is always at least as legal as a
one-consonant coda is mandatory — and MOP says prefer the onset).

Word edges are the degenerate case: word-initial consonants have no left
neighbor to compete with, so they are all onset ("sweaty" opens with the
legal cluster `SW`); word-final consonants are all coda.

Open the **Syllabifier widget** and watch the split happen on these words —
it runs the same table and the same loop.

## The fine print: MOP is a decision procedure, not a discovered truth

Here the course's running honesty policy kicks in. MOP gives a clean,
deterministic answer everywhere. English itself is not so tidy — and the gap
matters to this project in a documented, load-bearing way.

Consider the /t/ in "sweaty" (`SW EH1 . T IY0` by MOP). Since Kahn (1976),
phonologists have observed that a consonant in this position — between a
stressed lax vowel and an unstressed one — behaves as if it belongs to
**both** syllables at once ("ambisyllabic"). Two facts pull in opposite
directions:

- That /t/ **flaps** in American English (it comes out as the quick tap in
  "water"), which a true syllable-initial /t/ never does — compare the
  crisply aspirated /t/ in "attack." So it isn't purely an onset.
- But `SW EH1` can't stand alone either: a stressed lax vowel cannot end an
  English syllable. There is no possible English word "sweh." So the /t/
  isn't purely the next syllable's property.

English is genuinely torn; MOP resolves the tie by fiat, wholly in the
onset's favor. The choice is *lossy*, and the loss surfaces three units
later as a measured problem: the rhyme kernel ignores onsets, so a medial
consonant that MOP hands rightward **vanishes from rhyme scoring
entirely**. sweaty~heavy scores a perfect 1.0 — indistinguishable from true
perfect rhyme — even though the learner's ear, when probed, ranked
sweaty~Betty (matching medial t~t) audibly above sweaty~heavy (t~v). The
kernel ties them. That gap between the ear and the score is recorded as
open **tuning-ledger item 7** (Unit 11's walkthrough), with two candidate
fixes waiting on Unit 14's evaluation harness: copy ambisyllabic consonants
into the preceding coda so the ordinary coda term prices them, or teach the
kernel to peek at non-initial onsets.

The unit-sized lesson inside that story: when a clean algorithm meets a
messy phenomenon, the algorithm's simplification is a *claim*, and the
honest move is to write the claim down where the evidence can eventually
judge it — a docstring that says "decision procedure," a ledger item with
probe pairs, an eval that will settle it. Compare `syllabify.py`'s module
docstring, which says exactly this in the code's own voice.

## Check yourself

> Check yourself: (1) Why does one nucleus per syllable make counting
> syllables trivial? (2) Syllabify "hypnotize" from memory. (3) Why is
> "st" on the legal-onset list even though its sonority falls? (4) What is
> ambisyllabicity, and which ledger item does it explain?

## Exercise

From the syllabus: find a word the syllabifier currently gets wrong or
can't handle because its onset cluster is missing from
`phonetics.is_legal_onset`'s tables, add the cluster, and pin the fix with
a new case in `tests/test_syllabify.py`. The tests assert against the
human-readable `str(Syllable)` form — follow the existing examples.

## Where this is heading

The syllable structure you can now build is the *input type* of everything
that follows: Unit 5 slices a `Pronunciation` down to its rhyme-bearing
tail (a run of syllables), Unit 6 scores tails nucleus-against-nucleus and
coda-against-coda, and the "onsets are ignored" design — which this unit
just showed is entangled with a real open problem — becomes the kernel's
signature move.
