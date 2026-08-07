# Unit 1: Phonemes, Not Spelling

**Objective:** you internalize that rhyme is a relation between *sounds*, that
English spelling hides those sounds, and that a pronunciation lexicon —
CMUdict, in ARPAbet — is therefore the foundation everything else stands on.
**Prerequisites:** the Phase 0 orientation. **Pairs with:** `phonetics.py`;
the `pronunciation_for` lookup in `syllabify.py`.

## Start with your ear

> PAUSE. Do "Lincoln" and "reason" rhyme? Say both out loud — actually out
> loud — before you answer.

If you said yes, notice what you had to do to get there: you had to *say*
them. On the page they share almost no letters. If you hesitated, that
hesitation is itself the finding — the eye says no, the ear says yes. Either
way, you've just run the experiment this whole unit generalizes.

Here's the mismatch made explicit. The spellings look unrelated, but the
pronunciations —

```
lincoln  →  L IH1 NG K AH0 N
reason   →  R IY1 Z AH0 N
```

— share the entire `AH0 N` tail and closely related stressed vowels. The
rhyme was in the sounds all along; the spelling was hiding it.

> PAUSE. Suppose you had to write `do_these_rhyme(word1, word2)` using only
> the *letters*. Where does it break first? List three failure cases before
> reading on.

The list writes itself once you start: silent letters ("comb"/"tomb"/"bomb"
— three spellings of "-omb", three different sounds); the "ough" fiasco
("through"/"though"/"tough"/"cough" — one spelling, four rhyme classes);
homophones spelled apart ("their"/"there"); rhymes spelled apart
("Lincoln"/"reason"). And the classic: "love"/"move"/"prove" — same four
final letters, three different vowels, no two of them perfect rhymes.
English spelling is a lossy, irregular encoding of sound. Any rhyme engine
must therefore first *recover the sound*, and that recovery is what a
pronunciation lexicon provides.

## The formal pieces

- A **phoneme** is a contrastive sound unit — the difference between "bat"
  and "pat" is one phoneme. **Graphemes** (letters) map to phonemes
  many-to-many, and in English, irregularly.
- **ARPAbet** is an ASCII alphabet for English phonemes — friendlier to code
  than IPA, and what CMUdict uses. Vowels carry a trailing **stress digit**:
  `1` primary, `2` secondary, `0` unstressed. So `IH1` is a stressed KIT
  vowel. (`phonetics.py`'s `strip_stress` and `is_vowel` exist so no other
  code ever parses those digits by hand.)
- **CMUdict** maps ~134k words to ARPAbet pronunciations.
  `pronouncing.phones_for_word("lincoln")` → `['L IH1 NG K AH0 N']`. That
  string is the real input to rhyme-schemer; the spelling was only ever a
  lookup key.

Two engineering consequences follow, and both become whole units later. The
lexicon is a **hard dependency with gaps**: try
`phones_for_word("coogi")` and watch it return `[]` — the out-of-vocabulary
problem, Unit 13's territory. And the lexicon returns a **list**: "read" has
two pronunciations, "either" has two, and which one a rapper *performs* is
not the dictionary's call — variants become Unit 9's territory.

## Common confusions

- **Phonemes are not syllables.** `IH1` is one phoneme; a syllable is a
  *structure* (onset + nucleus + coda) that we will have to reconstruct,
  because CMUdict doesn't mark syllable boundaries at all — that's Unit 4.
- **CMUdict is not complete, and not neutral.** It's North American citation
  pronunciation, informally maintained. The README names it as a threat to
  validity; keep that in your peripheral vision from day one.
- **"Why not just use a rhyming dictionary?"** Because lookup tables encode
  *perfect* rhyme, and the entire point of this project is **graded slant
  rhyme** — Lincoln/reason must count, and no table says how much.

## Check yourself

> Check yourself: produce a pair of words that *look* like they should rhyme
> but don't, and a pair that don't look like they rhyme but do — then say
> how CMUdict reveals each. ("Lessen"/"strengthen" vs "Lincoln"/"reason" is
> the canonical answer; find your own pair too.)

## Exercise

From the syllabus: in a REPL, collect five words CMUdict gets interestingly
wrong or lacks entirely (slang, names — "Coogi" starts the list). Save them:
they become your Unit 13 test set. Then write the property tests for the
phonetics primitives — `strip_stress("IH1") == ("IH", PRIMARY)` and friends,
and that every ARPAbet vowel round-trips.

**Where this is heading:** "recover the sound" sets up Unit 2's question —
*how similar* are two recovered sounds? That graded question is what makes
slant rhyme computable.
