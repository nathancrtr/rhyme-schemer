# Unit 5: The Vowel Skeleton & the Rhyme-Bearing Tail

**Objective:** you can implement `rhyme_tail` — the slice of a pronunciation
that actually carries rhyme — and defend its anchor: the *last
primary-stressed* syllable, not the last syllable. **Prerequisites:** Units
1–4 (this is the first *build* unit: the phonetic foundation is now yours to
stand on). **Pairs with:** `rhyme_schemer/rhyme.py` (`rhyme_tail`);
`interactive/exercises/unit-05-rhyme-tail/`.

## Where rhyme lives

"Lessen" and "strengthen" share a final syllable — both end in the same
unstressed `-en` — and do not rhyme at all. "Reason" and "season" rhyme
across *two* syllables. The difference is stress:

```
lessen      L EH1 . S AH0 N        strengthen  S T R EH1 NG . TH AH0 N
reason      R IY1 . Z AH0 N        season      S IY1 . Z AH0 N
```

Rhyme is anchored at the **last stressed syllable** and runs from there to
the end of the word. For reason/season that's `IY1 …` onward — two matching
syllables. For lessen/strengthen the anchored material is `EH1 . S AH0 N` vs
`EH1 NG . TH AH0 N` — the shared `-en` was never the rhyme-bearing part,
just trailing coincidence after two very different stressed syllables.

That anchored slice is the **rhyme tail**, and every scoring step for the
rest of the course operates on tails, never on whole words. Its sequence of
nuclei is the **vowel skeleton** — the spine that Unit 8's alignment will
walk.

## The spec, with its edge cases

`rhyme_tail(pron) -> tuple[Syllable, ...]`:

- The syllables from the **last PRIMARY-stressed** syllable to the end.
- No primary anywhere? Fall back to the last SECONDARY-stressed syllable.
- No stress at all? The final syllable alone.
- Empty pronunciation → empty tail.

> PAUSE. Why "last" primary rather than "first"? Invent a case where they
> differ before reading on.

Single words rarely carry two primaries — but Unit 9 makes multi-word
*spans* into ordinary `Pronunciation`s, and a span like "GEM-in-I" carries
a primary per word. The rhyme anchors on the final beat ("…-I!"), so the
*last* primary wins. Writing `rhyme_tail` to scan for the last one costs
nothing today and makes spans work for free later — a small example of
designing the invariant before the feature that needs it.

And the fallbacks aren't decoration: CMUdict contains stress-less
pronunciations (reduced function words), and a scorer that crashes on "a"
is not a scorer. The final-syllable fallback says: with no stress evidence,
the most rhyme-like thing left is the word's end.

## One honest caveat, recorded now

The tail trusts *dictionary* stress. Hip-hop performance routinely
overrides it — a rapper lands the beat on "em-CEE" where the dictionary
says "EM-cee," and suddenly the performed tail differs from the citation
tail. That gap is not this unit's problem, but it is real, it is recorded
(the performed-vs-lexical-stress thread), and Unit 11 eventually solves it
properly: performed stress becomes an enumerated, *priced* reading rather
than a dictionary fact. For now: citation stress, deliberately.

## Check yourself

> Check yourself: (1) `rhyme_tail` of "around" (`AH0 . R AW1 N D`) — how
> many syllables and why? (2) Why must lessen/strengthen come out as
> non-rhyming from any correct tail implementation? (3) What does the tail
> of a stress-less pronunciation contain?

## Exercise

`interactive/exercises/unit-05-rhyme-tail/` ships the stub and failing
tests — the tests assert structure (the tail is a suffix; its nuclei are a
suffix of the vowel skeleton) plus the examples above, including the
hand-built fallback cases. Green bar = the rhyme engine has its first
working part, written by you.

**Where this is heading:** Unit 6 scores two tails of equal length; Unit 7
grades the scoring; Unit 8 aligns unequal tails. Everything runs on the
slice you just built.
