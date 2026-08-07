# Unit 13: Out-of-Vocabulary Words & Grapheme-to-Phoneme

**Objective:** you can explain the G2P fallback chain — what each link
knows, why they run in that order, and why a guess carries a price — and
you can state the design principle that makes the dialect rules *respectful
recovery* rather than normalization. **Prerequisites:** Units 11–12.
**Pairs with:** `rhyme_schemer/g2p.py`.

## The problem, sized honestly

Since Unit 1 you've been collecting words CMUdict lacks; since Unit 3 the
pipeline has skip-and-flagged them. On real lyrics the skips cluster into
*kinds*, and the kinds want different tools:

1. **Dialect spellings of known words** — "chokin'," "flossin'," "holla."
   The dictionary *knows* these words; the spelling encodes how they're
   performed. Recoverable by rules that lean on the dictionary.
2. **A closed class of slang contractions** — "imma," "finna," "tryna."
   Not rule-derivable ("imma" is "I'm gonna"; no letter pattern says so).
   A small hand lexicon is the honest tool.
3. **Genuinely unknown strings** — brands ("Coogi"), onomatopoeia
   ("blaow"), coinages. Only letter-to-sound rules can say anything, and
   what they say is a guess.

## The chain, and why the order matters

`pronounce(word)` tries: **dictionary → lexicon → rules → letter-to-sound**.

> PAUSE. Why must the hand lexicon outrank the spelling rules? Find a word
> that would go wrong the other way around.

The recorded example is "shoulda": it *pattern-matches* the -a-for-er rule
(via "shoulder") but actually contracts "should have" — only the lexicon
knows that. Curated truth outranks pattern-matching wherever both claim a
word. Dictionary-first-with-fallbacks is also the field's consensus
architecture (Epitran leans on a lexicon for English; neural G2P slots in
behind the same interface) — Unit 1's founding lesson about English
spelling, now load-bearing.

## The design principle: dialect spellings are performance transcriptions

The obvious normalization — "chokin'" *is* "choking," so look it up, done —
is subtly wrong. The apostrophe is the lyricist **transcribing what they
say**: coda N rather than NG. And N-vs-NG is precisely the kind of coda
difference the kernel scores. So every rule recovers the dictionary *stem*,
then **keeps the spelled surface phonology**: look up "choking," rewrite
the final NG to the N the lyricist wrote. Likewise "holla"/"gangsta" spell
a performed non-rhotic final vowel — `AH0`, which rhymes with "follow" —
where dictionary "holler" ends in `ER0`, which doesn't.

This is Unit 11's move one layer down: the dictionary records citation
facts, the performance overrides them, and the performed form is minted as
data.

## The rules are documented phonology, cited

Neither rule is an invented respelling; each encodes a feature the
sociolinguistics literature has documented for decades, and each carries
its citation in the code:

- **g-drop** encodes the classic **(ING) variable** — coronal [n] for
  velar [ŋ] in unstressed -ing — the founding variable of variationist
  sociolinguistics (Fischer 1958) and part of AAE's documented phonology
  (Green 2002). Pan-vernacular English, not AAE-exclusive; "-in'" is
  simply its standard written transcription.
- **-a-for-er** encodes **AAE non-rhoticity** — coda /r/ vocalizes — and
  Thomas (2007) records that r-lessness "is most common in unstressed
  syllables, as in *over, brother*": exactly this rule's final
  unstressed-ER environment.

The citations do double duty: they harden the rules, and they answer "why
does your tool rewrite Black speech?" with receipts — it doesn't. Much of
the NLP literature on AAE is a literature about systems *failing* AAE
speakers by normalizing the performance away. This project's stated
position (see the README's dialect paragraph) is the opposite: performed
AAE phonology is ground truth here, and the performed form is the one that
scores.

## Confidence is priced, not modeled

A letter-to-sound guess is an unlikely claim of the same species as a
coerced stress, and it travels the same road: `Guess.cost` (0 for
dictionary, lexicon, and rules — the spelling or the lexicon *testifies* —
and `DEFAULT_LTS_COST = 0.1` for letter-to-sound) folds into the reading's
cost at candidate minting. A marginal rhyme built on a guess dies; a strong
one ("Coogi"~"groovy" at 1.0) shrugs the price off. The kernel and
`models.py` stay provenance-free — a guessed `Pronunciation` is just a
`Pronunciation` — while `source` lets the scanner and renderer *say* how
each pronunciation was obtained: guessed words get a dashed underline and a
provenance tooltip line, distinct from OOV's dotted. And "OOV" now means
something stronger than before: *even guessing failed* (no vowel to build
on — "brrr").

## The bill arrives, on schedule

Recall Unit 9: every convenience has a cost, and the cost lands downstream.
G2P's recall gain arrived married to a precision loss, observed at this
unit's own end-to-end check: the chain's pronunciations were *correct*, yet
"-in'"~"-ing" bridge edges glued chokin'/jokin', Coogi/groovy, and
flowing/going into one OW mega-class — every G2P word is a new *node*
feeding Unit 10's percolation-prone grouping. Nothing to fix in `g2p.py`
itself; ledger item 9 routes it to Unit 14 alongside its siblings. Say it
as a slogan: **new coverage inherits old debt.**

## Check yourself

> Check yourself: (1) Order the chain and give the one-word reason each
> link outranks the next. (2) Why does "chokin'" get N-for-NG *rather
> than* being normalized to "choking"? (3) Which features do the two
> dialect rules encode, and roughly who documented them? (4) Why does only
> letter-to-sound carry a cost?

## Exercise

From the syllabus: replace skip-and-flag with a G2P guess for three of
your Unit-1 OOV words; confirm a previously-skipped word now participates
in a detected rhyme, flagged as guessed. Then feed the chain a word it
*should* refuse ("brrr") and confirm it stays OOV.

**Where this is heading:** coverage is as wide as it's getting; Unit 14
finally builds the ruler — and ledger item 11 already sketches this
module's next job (minting non-rhotic readings for *standard* spellings,
priced, as performed-phonology variants).
