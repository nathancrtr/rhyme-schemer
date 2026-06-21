# Unit 1 Lesson Guide: Phonemes, Not Spelling

**Objective:** The learner internalizes that rhyme is a relation between *sounds*, that English spelling hides those sounds, and that a pronunciation lexicon (CMUdict, in ARPAbet) is therefore the foundation everything else stands on.
**Prerequisites to check:** none beyond the Phase 0 orientation.
**Pairs with:** `phonetics.py`; the `pronunciation_for` lookup in `syllabify.py`.

## How to run this lesson
Dialogue, one question per turn, then stop and wait. The learner has a linguistics background — don't lecture them on what a phoneme is; use that knowledge, and aim the lesson at the *computational* consequences.

## 1. Diagnostic opener
Ask: **"Do 'Lincoln' and 'reason' rhyme? Say both out loud before you answer."**
- If they say yes (correct): "Right — and notice you had to *say* them. On the page they share almost no letters. Hold onto that." → go to step 2.
- If they hesitate on the spelling: that hesitation *is* the point — the eye says no, the ear says yes. → go to step 2.

## 2. Build the intuition
Point out the mismatch: `lincoln` and `reason` share no obvious spelled ending, yet `L IH1 NG K AH0 N` and `R IY1 Z AH0 N` share the `AH0 N` tail and a closely-related stressed vowel.

> PAUSE. Ask: **"If you had to write a function `do_these_rhyme(word1, word2)` using only the *letters*, where would it break first?"**

Wait. Let them enumerate failures (silent letters, "ough", homophones like "their/there", "Lincoln/reason"). Then land it: spelling is a lossy, irregular encoding of sound, so any rhyme engine must first *recover the sound*. That recovery is what CMUdict gives us.

## 3. Formalize
Now make it precise:
- A **phoneme** is a contrastive sound unit; **graphemes** (letters) map to phonemes many-to-many and irregularly in English.
- **ARPAbet** is an ASCII phoneme alphabet; **CMUdict** maps ~134k words to ARPAbet pronunciations, with **stress digits** on vowels (0/1/2).
- `pronouncing.phones_for_word("lincoln")` → `['L IH1 NG K AH0 N']`. That string is the real input to rhyme-schemer; the spelling was only ever a key for lookup.

Connect back: "You already know this as a linguist. The engineering consequence is that the lexicon is a hard dependency, and its gaps — words it doesn't contain — become a whole problem of their own."

## 4. Common confusions
- If they conflate **syllables** with **phonemes**: clarify that `IH1` is one phoneme; a syllable is a *group* (onset+nucleus+coda) we reconstruct in Unit 4.
- If they assume CMUdict is complete: it isn't — preview OOV. Ask them to try a slang word or a name and watch it return empty.
- If they ask why not just use a rhyming dictionary: because we want *graded slant* rhyme, which no lookup table encodes — that's the whole project.

## 5. Exit check
Ask: **"Give me a pair of words that look like they should rhyme but don't, and a pair that don't look like they rhyme but do — and say how CMUdict would reveal each."**
- A good answer (e.g. "lessen/strengthen look close but don't; Lincoln/reason look far but do") → send them to the exercise: collect five OOV words and write the `strip_stress`/`is_vowel` property tests.
- A shaky answer → return to step 2 with a fresh pair (try "love/move/prove" — same spelling, three different vowels).

**Where this is heading:** today's "recover the sound" sets up Unit 2, where we ask *how similar* two recovered sounds are — the graded question that makes slant rhyme possible.
