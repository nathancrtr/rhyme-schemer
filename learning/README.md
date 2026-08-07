# rhyme-schemer: the course

**Open [`site/index.html`](site/index.html) in a browser — that's the course.**
Every page is static and self-contained (no server needed); the site is
generated from the Markdown sources here by `build_site.py`, so edit the
Markdown, not the HTML, and rebuild with
`pip install markdown && python learning/build_site.py`.

A complete, interactive course for learning **NLP and computational phonology by finishing this repo**. You'll work from the phonetic foundation already in `rhyme_schemer/` — phonemes, articulatory features, syllabification — forward through the rhyme-scoring kernel, sequence alignment, rhyme-scheme grouping, visualization, grapheme-to-phoneme, and evaluation, until the tool described in the top-level README actually exists.

It's built for an implementation-first learner at ~3–5 hrs/week, about six months. The repo is the spine: every concept is in service of code you'll read or write, and most exercises are "make the failing test pass."

## What's here

```
learning/
├── README.md                 ← you are here
├── learning-resources.md      tiered, verified resources ("why this one")
├── curriculum.md              the 15-unit, project-driven syllabus + dependency map
├── audits/                    corpus-evidence checks on the feature spaces
│   ├── hirjee_brown_2009.py     H&B's learned rhyme matrices, as data
│   └── audit_feature_space.py   rank-compare them against features.py
└── interactive/
    ├── lessons/               Socratic lesson guides (run with Claude)
    │   ├── unit-01-phonemes-not-spelling.md
    │   ├── unit-02-feature-distance.md
    │   ├── unit-07-the-rhyme-kernel.md
    │   ├── unit-08-alignment.md
    │   ├── unit-10-non-transitivity.md
    │   ├── unit-11-scanner-walkthrough.md   + the open tuning ledger
    │   └── sequence-alignment-family.md     diff/DNA/rhyme, one algorithm
    ├── widgets/               open these in a browser
    │   ├── vowel-explorer.html    click two vowels → the exact vowel_distance()
    │   ├── syllabifier.html       watch the Maximal Onset Principle split a word
    │   ├── nw-alignment.html      feel the gap penalty in the DP table
    │   ├── rhyme-score-sandbox.html   two words → tails, alignment, score receipts
    │   └── generate_sandbox_lexicon.py  regenerates the sandbox's embedded words
    ├── quizzes/
    │   ├── phase-1-checkpoint.html  self-checking, explanatory feedback
    │   ├── phase-3-checkpoint.html
    │   └── question-bank.md         pool for "quiz me on Phase N"
    └── exercises/
        ├── unit-05-rhyme-tail/      stub + failing tests → make them green
        └── unit-08-alignment/       guided NW skeleton + hand-worked table
```

## How to start

1. Get the repo running: `pip install -r requirements.txt`, then `python -m unittest discover tests` (all green).
2. Read `learning-resources.md`, then skim the Hirjee & Brown (2009) intro and one Pudding piece so you know the target.
3. Open `curriculum.md` and begin **Phase 0 → Phase 1**. Phase 1 reads the existing modules as worked examples; the build begins at Unit 5.
4. Open `interactive/widgets/vowel-explorer.html` and `syllabifier.html` while you read Units 2 and 4 — they render the repo's own numbers.

## Working with Claude

The interactive layer is meant to be driven in conversation:

- *"Teach me Unit 1 interactively."* → Claude runs that unit's Socratic lesson guide.
- *"Quiz me on Phase 1."* → Claude pulls from `interactive/quizzes/question-bank.md`.
- *"I wrote my `rhyme_tail` for Unit 5 — review it against the spec."* → paste your code.
- *"Unit 8's alignment isn't clicking — walk me through it on our actual vowel skeletons."*
- *"Give me a harder exercise for Unit 7."*

Open a fresh chat per unit if you like; these files hold the structure between sessions. The widgets and quizzes are self-contained HTML — just open them in a browser, no server needed.

## A note on placement

This directory is designed to live **inside the rhyme-schemer repo** as `learning/`, so the exercises can reference and extend the real code (the Unit 5 stub is copied into `rhyme_schemer/rhyme.py`, its tests into `tests/`). Commit it alongside the source and the course grows with the project.

*Course v1.0 — June 2026; v1.1 — July 2026, revised against the external research review in the top-level `REVIEW.md` (corpora-first Unit 14, post-2010 detection literature, ALINE credit, workshop-paper frontier).*
