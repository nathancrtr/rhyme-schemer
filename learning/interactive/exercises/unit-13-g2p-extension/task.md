# Unit 13 Exercise — Extend the Chain as Lyrics Expose Gaps

**What you're doing:** the real maintenance workflow the G2P module was
designed for. Three words the current chain gets wrong or can't voice;
your job is to fix each one *in the right link of the chain* — and the
choice of link is the exercise.

## The three words, and what the chain does today

Run them yourself first:

```python
from rhyme_schemer.g2p import pronounce
for w in ("skrrt", "deadass", "boutta"):
    g = pronounce(w)
    print(w, g.source, [str(p) for p in g.pronunciations])
```

- **skrrt** → `oov`, nothing. The letter-run collapse ("rrr" → "r") strips
  the word to `skrt`, which has no vowel, so letter-to-sound correctly
  refuses. But the performance has a clear nucleus — a syllabic R, which
  ARPAbet writes as the vowel `ER`.
- **deadass** → letter-to-sound guesses `D IY1 D AE0 S` — *dee-dass*. The
  "ea"→IY pattern is right for "beat" and wrong here; the word is
  `D EH1 D AE2 S`.
- **boutta** → letter-to-sound guesses `B AW1 T AE0`. Close-ish, but this
  word contracts "(a)bout to" — the final vowel is a schwa, `B AW1 T AH0`
  (rhymes the way "gotta" does).

## Your job

For each word, decide **which chain link should own the fix**, make the
fix, and get the tests green:

```bash
cd learning/interactive/exercises/unit-13-g2p-extension
python -m unittest test_g2p_extension -v
```

The tests check outcomes (source and pronunciation shape), not your
route — but the routes are not equally defensible, and task review means
being able to say why you chose yours. Things worth weighing:

- Could a **letter-to-sound pattern** fix "skrrt"? Trace `_letter_to_sound`
  by hand: the collapse regex runs *before* pattern matching, so an "rr"
  pattern would never see its input. A fix there means reordering the
  function's phases — is that worth it for one word, when the module's
  philosophy prices LTS as a crude last resort?
- Could a **rule** fix "deadass"? It's a compound ("dead" + "ass"), and
  both halves are in CMUdict. A compound-splitting rule would be a *new
  chain link* — a real design (many G2P systems have one), but a big
  hammer. What does the module's "closed class → lexicon" reasoning say?
- "boutta" is the "imma" case almost exactly. Which precedent does the
  module set for contractions that no spelling pattern can derive?

(If you concluded "lexicon, three times" — with the LTS and rule routes
*considered and rejected for stated reasons* — you've reasoned like the
module. The `_LEXICON` dict in `rhyme_schemer/g2p.py` is deliberately
small and marked "extend as real lyrics expose gaps." This is that.)

## Afterward

- Your entries are real contributions: the repo's own tests
  (`python -m unittest discover tests` from the root) must still pass —
  lexicon additions are additive, so they will. Consider committing them.
- Feed the chain a word it should *still* refuse ("brrr", "psst") and
  confirm OOV survives your changes — the flag half of skip-and-flag is
  load-bearing (renderers mark it).
- Then the loop closes: your three words now participate in rhyme
  detection, flagged with their source, priced at 0 (the lexicon
  testifies). Check `skrrt` against "hurt" in the sandbox widget — does
  the syllabic-R reading rhyme the way the performance does?
