# Unit 12: Visualizing the Scheme

**Objective:** you can turn a `VerseScan` into the colored verse view the
README promised on day one — and you can defend every rendering decision as
a *policy*, separated from the pixels that execute it. **Prerequisites:**
Unit 11. **Pairs with:** `rhyme_schemer/render.py`; `tests/test_render.py`.

## What color means: render the judgments, not the phonetics

The field offers three schools for coloring rhyme. Color-by-vowel (Martin
Brath's lyric visualizations): every EY is one hue, every IY another — the
*input phonetics* made visible. Multi-channel formatting (Hirjee & Brown's
Rhyme Analyzer): five stacked typographic channels for different rhyme
types. And color-by-**rhyme-class** (the Pudding/Vox school): words that
the analysis groups together share a color, whatever their vowels are.

This project renders **classes**. The reasoning: the scanner already spent
eleven units *judging* — gating, pricing, selecting, grouping. Coloring by
vowel would throw those judgments away and show raw phonetics; stacking
five channels shows everything and communicates little to a non-specialist.
The renderer's job is to display the scanner's *conclusions* — and, less
comfortably, that means its mistakes too. That discomfort is a feature;
hold the thought.

## Policy as data: `RenderPlan`

`render.py` splits in two. `plan_verse` resolves a verse plus its
`VerseScan` into a **`RenderPlan`** — a data structure in which every
policy decision is already made: which class each word span belongs to,
what fills it, what marks it. Then `render_html` and `render_terminal` are
deliberately **dumb emitters** that walk the plan and paint.

> PAUSE. Why insist the emitters be dumb? What goes wrong when rendering
> policy lives inside the HTML generator?

Two renderers is the forcing function: any judgment made inside
`render_html` has to be re-made — identically, forever — inside
`render_terminal`, and inside every future emitter. Hoisting every decision
into the plan means one place decides and N places paint. It also makes
policy *testable as data*: `test_render.py` asserts against plans, not
against HTML strings.

## The hard cases are the normal cases

Real verses are not tidy:

- **Words in multiple classes.** Common — up to five classes on one word in
  real data, with extents that both nest *and* cross. Policy: the word's
  fill goes to its **best-scoring** class; the others appear as small tick
  bars; the tooltip carries the full receipts (each class, each partner,
  each score). Show the winner, keep the evidence.
- **Compounds.** Unit 11's selector splits glued chains into one-beat
  matches by design ("palms are SWEATY ~ arms are HEAVY" is two matches in
  two classes); `chain_matches` reassembles adjacent same-line runs so the
  ear-sized unit renders as one — under a *neutral* spanning rule, since a
  compound's beats belong to different classes.
- **OOV words** get a dotted underline; **G2P-guessed** words (Unit 13) a
  dashed one plus a provenance line in the tooltip — the reader can always
  tell attested from inferred from absent.

## Palette discipline

Eight fixed-order categorical slots, chosen as text-safe tints and
validated for color-vision deficiency in both light and dark modes.
Largest classes claim slots first; classes beyond eight fold into a neutral
wash rather than cycling hues — **never cycle**: the eleventh hue is
indistinguishable from the third, and a false color match is a false claim
about the analysis.

> PAUSE. A verse has ten rhyme classes. Defend "two of them go gray" over
> "reuse colors" to a designer who finds gray boring.

## What rendering taught the project — the recorded moment

Unit 12 was where the precision debt stopped being abstract. The ledger had
suspected generous edges for two units; *rendering the fixture verses made
it visible* — mega junk classes in the Poe stanza, function-word glue,
passenger beats riding real compounds ("kind of a mess," in the learner's
recorded verdict). The response is the project's whole epistemics in
miniature: no knob was turned. Every observation went into the tuning
ledger, and **all** tuning was deferred to Unit 14's evaluation sweep,
because fixing what you can suddenly *see* — before you can *measure* — is
how a system gets tuned to one demo verse. The renderer's job was to make
the debt visible; the harness's job is to price it.

## A test-fixture rule with teeth

Never embed multi-line commercial lyrics in fixtures — copyright, plus
content-filter breakage in tooling. The repo's fixtures are an original
engineered verse and public-domain poetry (Poe, Gilbert & Sullivan);
single iconic mild lines are acceptable. This rule shaped Unit 14 too:
evaluation corpora are referenced by song ID + offsets, never by committed
lyric text.

## Check yourself

> Check yourself: (1) Why does a word's fill color follow its
> *best-scoring* class rather than its first or largest? (2) What would be
> lost — concretely — if classes beyond eight cycled hues? (3) Why does
> the plan/emitter split make the multi-class policy testable?

## Exercise

From the syllabus: render a full verse to a standalone HTML file, and make
sure a word with overlapping class memberships displays fill, ticks, and
tooltip receipts correctly in both HTML and terminal output.

**Where this is heading:** the renderer shows the scanner's judgments,
mistakes included. Unit 13 widens coverage (OOV words join the scan);
Unit 14 finally measures what you've been looking at.
