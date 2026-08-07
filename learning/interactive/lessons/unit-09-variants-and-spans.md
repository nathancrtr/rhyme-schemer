# Unit 9: Multi-Word Spans & Pronunciation Variants

**Objective:** you can make the kernel score phrases against words and take
the best score over dictionary variants — and you can articulate what each
convenience *costs*, because both bills arrive in later units.
**Prerequisites:** Unit 8. **Pairs with:** `syllabify.py` (the `*_for_span`
and plural `pronunciations_*` lookups); `rhyme.py` (`best_rhyme_score`,
`best_is_rhyme`).

## Spans: the invariant pays out

Rappers rhyme *phrases*: "get up" against "setup," "palms are" against
"arms are." The kernel scores `Pronunciation`s — so the design question is
whether a phrase needs a new type.

It doesn't, and that's the payoff of the model's core invariant: **a word
and a multi-word span are both just `Pronunciation`s.** "Get up" is the two
words' syllables laid end to end (`Pronunciation.concat`); nothing
downstream can even tell which it started as. `pronunciation_for_span`
builds it; the unchanged kernel scores it. Remember Unit 5's decision to
anchor the tail on the *last* primary stress? Spans carry several primaries
— that decision was quietly waiting for this unit.

## Variants: the rapper picks the reading

CMUdict returns a *list*: "read" is `R IY1 D` or `R EH1 D`, "either" opens
with `IY` or `AY`. Which one is performed is not the dictionary's call —
it's the rapper's, and a rapper picks **whichever reading rhymes**.

> PAUSE. Given variant lists for both words, how should a scorer decide
> which pronunciations to compare?

Score all pairings and take the **max** — that is the entire content of
`best_rhyme_score` / `best_is_rhyme`. Span variants are the cartesian
product of the words' variants ("read"×2 · "it"×1 = 2 readings of "read
it"), and the max runs over all of it. Note the layering: the kernel still
only ever sees one `Pronunciation` against one; best-over-variants is a
thin wrapper *around* the kernel, not a change *inside* it.

## What the max really models — a recorded idiolect story

This project learned what variants are for the honest way. Early on, the
kernel ranked lincoln/listen (0.870) *above* lincoln/reason (0.829), which
struck the learner as backwards. The first instinct was to reach for the
weights — push nucleus similarity harder. Measured, that made it *worse*:
rewarding exact vowel matches widens listen's lead, because in CMUdict's
General American, "lincoln" and "listen" share `IH` exactly while "reason"
has `IY`.

The actual finding: the learner *pronounces* Lincoln's first vowel as `IY`
("bean," not "bin"). In their idiolect, lincoln/reason is a perfect
stressed-vowel match — their ear was right, and it disagreed with the
dictionary, not with the math. The fix therefore lives in the
**pronunciation input** (a dialect variant supplying the `IY` reading),
never in the weights. That principle — *variants, not metric generosity* —
has since won the same argument two more times in this project (smoothed
readings, ledger item 10; non-rhotic readings, ledger item 11). When a
score offends your ear, ask "is this a distance problem or a *reading*
problem?" before touching any knob.

## The bill: optimism by construction

> PAUSE. Best-over-variants means "two words rhyme if *some* pairing of
> their readings rhymes." What does that do to precision as variant lists
> grow?

It inflates recall and erodes precision, mechanically: more variants, more
chances to clear the threshold spuriously — and it compounds with any
generosity in the feature space underneath. This is the right model for
"did the rapper *find* a rhyme here?" and the wrong model for "do these
words *naturally* rhyme?" — the project wants the first question, accepts
the cost, and has the cost on the books (it feeds the false-positive
pressure that Unit 10's grouping then amplifies; Unit 14 measures the
damage).

## A cliffhanger you can reproduce

Open the Rhyme-Score Sandbox and score **get up ~ setup**. You'll get 0.5 —
embarrassingly low for the flagship span example. Read the tails to see
why: citation stress puts a primary on "up," the tail anchors on the *last*
primary, and the span's tail shrinks to one syllable while "setup" keeps
two. The span machinery is fine; the *stress* is wrong — performed "GET-up"
demotes the particle. Making performed stress a first-class, priced reading
is exactly Unit 11's scanner, and this pair is its motivating example.

## Check yourself

> Check yourself: (1) Why does `pronunciation_for_span(["get","up"])`
> return one object rather than two? (2) How many readings does a
> three-word span have if its words carry 2, 1, and 3 variants? (3) State
> the lincoln/reason principle in one sentence. (4) Why is
> best-over-variants "optimistic by construction," and when is that the
> right model?

## Exercise

From the syllabus: score a multisyllabic multi-word rhyme; then construct a
pair where the rhyme only works under a *second* CMUdict variant and assert
that `best_rhyme_score` finds it while first-variant-only scoring misses
it.

**Where this is heading:** Unit 10 turns pairwise verdicts into groups;
Unit 11 turns "the rapper picks the reading" from pronunciation variants
into *performed-stress* variants — same move, one level deeper.
