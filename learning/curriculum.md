# rhyme-schemer: Curriculum

Learn NLP and computational phonology **by building rhyme-schemer** — from the phonetic foundation already in the repo, through the rhyme-scoring kernel, to a working visualizer of rhyme schemes in hip-hop lyrics. For a senior software engineer at ~3–5 hrs/week; roughly 6 months.

---

## How this curriculum works

**The repo is the spine.** This is a project-driven course: each unit takes rhyme-schemer from one working state to the next. The theory is just-in-time — you read the chapter or paper that unblocks *this* step, not a survey. Where the code already exists (the whole phonetic foundation), you read it as a worked example and prove your understanding by extending it; where it doesn't (everything from `rhyme_score` onward), you build it, usually by making a failing test pass.

**Two tracks, interleaved.** Every unit pairs an **implementation** step with the **concept** it embodies. You'll never wire up a function without understanding the phonology or algorithm behind it, and never meet a concept without immediately coding it.

**Each unit has:** Build (the implementation step) · Read (precise sources) · Concepts · Exercise · Milestone, and sometimes a Key Insight or an interactive piece in `interactive/`.

**Pacing.** One unit ≈ one week at 3–5 hrs. Phase 1 moves fast because you're reading existing code; the build phases are slower. Some units run long — Unit 8 (alignment) especially. That's expected.

**The repo's own tests are your grader.** rhyme-schemer's `tests/` already model the house style: structural property tests (identity, symmetry, range) and ordering assertions you trust over exact numbers. New exercises follow that style, and many ship as failing tests in `interactive/exercises/`.

**Working with Claude.** This course is built to be worked through with Claude. Triggers like *"teach me Unit 5 interactively"* run a Socratic lesson guide; *"quiz me on Phase 1"* draws from the question bank. See the end of this file.

---

## Phase 0 — Orientation (Week 0)

**Goal:** Know what you're building and why, and get the foundation running.

- **Build:** Nothing yet. `pip install -r requirements.txt`; `python -m unittest discover tests` — all green.
- **Read:** the repo `README.md`; the introduction of Hirjee & Brown (2009); one Pudding piece. Play in a REPL: `pronouncing.phones_for_word("lincoln")`, `pronouncing.rhymes("cheese")`.
- **Concepts:** the syllable-first pipeline (look up → syllabify → feature-score → rhyme-kernel → group → visualize); slant rhyme vs perfect rhyme; why "Lincoln/reason" must count.
- **Milestone:** Tests pass locally, and you can describe the pipeline and the north star in your own words.

> **Check yourself:** Why does the README insist the tool target *vowel sounds* rather than spelling? If you're not sure, that's exactly what Unit 1's lesson guide opens with.

---

## Phase 1 — The phonetic foundation already in the repo (Weeks 1–5)

**Goal:** Master the concepts the existing modules encode, by reading and extending them. By the end you understand every line of `phonetics.py`, `models.py`, `syllabify.py`, and `features.py`, and you've made each one yours by extending it.

### Unit 1 — Phonemes, ARPAbet & the lexicon
- **Build:** Read `phonetics.py` (`Stress`, `VOWELS`, `strip_stress`, `is_vowel`) and the `pronouncing`/CMUdict layer in `syllabify.py` (`pronunciation_for`). Add property-based tests for `strip_stress`/`is_vowel`.
- **Read:** SLP3 **Phonetics** chapter (phonemes, IPA, ARPAbet); Parrish's CMUdict notes; ARPABET (Wikipedia).
- **Concepts:** phoneme vs grapheme; transcription systems (IPA vs ARPAbet); the pronunciation lexicon; lexical stress (0/1/2); the out-of-vocabulary (OOV) problem; why CMUdict returns *variants*.
- **Exercise:** In a REPL, collect five words CMUdict gets interestingly wrong or lacks (slang, names — *"Coogi"*). Write tests asserting `strip_stress("IH1") == ("IH", PRIMARY)` and friends, and that every ARPAbet vowel round-trips.
- **Milestone:** New passing tests for the phonetics primitives, and a short note listing five OOV words (your future Unit-13 test set).
- **Interactive:** `interactive/lessons/unit-01-phonemes-not-spelling.md`.

### Unit 2 — The IPA vowel space & articulatory features (vowels)
- **Build:** Read the vowel half of `features.py` (`VowelPoint`, `VowelFeatures`, `VOWEL_FEATURES`, `vowel_distance`). Adjust or justify two coordinate choices without breaking the ordering tests.
- **Read:** SLP3 Phonetics (vowels); the interactive IPA chart (make the sounds!); the vowel-quadrilateral references.
- **Concepts:** the IPA vowel quadrilateral (height × backness); roundedness; the rhotic `ER`; tense/lax falling out of position (centralization); **diphthongs as a glide** between two points; distance on a plane as similarity.
- **Exercise:** Open `interactive/widgets/vowel-explorer.html`, click pairs, and confirm by hand that the widget's numbers match `vowel_distance`. Then change one vowel's coordinates in `features.py`, predict which ordering tests shift, and check.
- **Milestone:** You can explain why `IH` sits lower and more central than `IY`, and why a single point can't model `AY`.
- **Key insight:** This table is a tiny, hand-built **embedding**. "Similarity = distance in a feature space" is the same move word2vec makes — you're meeting it in 15 vowels instead of 50,000 words.
- **Interactive:** widget `vowel-explorer.html`; lesson `unit-02-feature-distance.md`.

### Unit 3 — Consonants: place, manner, voicing, sonority
- **Build:** Read the consonant half of `features.py` (`CONSONANT_FEATURES`, `consonant_distance`). Add a near-pair ordering assertion of your own.
- **Read:** SLP3 Phonetics (consonants); Sonority Sequencing Principle (Wikipedia).
- **Concepts:** place × manner as the consonant plane; the **sonority hierarchy** (stop → … → glide) and why manner is ordered by it; voicing as a small perceptual cue (hence the low `_W_VOICE`); why consonants matter to rhyme mostly in the coda.
- **Exercise:** Add an assertion that voicing pairs (e.g. `S`/`Z`, `P`/`B`) are closer than same-manner different-place pairs, and explain the weight that makes it true.
- **Milestone:** A passing consonant test you wrote, plus a one-paragraph rationale for the sonority ordering.

### Unit 4 — Syllables & phonotactics: the Maximal Onset Principle
- **Build:** Read `models.py` (`Syllable`, `Pronunciation`, `rime`, `vowel_skeleton`), the onset tables in `phonetics.py` (`is_legal_onset`), and `syllabify.py` (`_split_consonants`, `syllabify`). Add an onset cluster a new word needs.
- **Read:** SLP3 Phonetics (syllable structure); Phonotactics & Syllable (Wikipedia).
- **Concepts:** onset / nucleus / coda / **rime**; phonotactics; the Sonority Sequencing Principle as the rule behind legal onsets (and the /s/-cluster exceptions); the **Maximal Onset Principle**; one nucleus per syllable; word-edge handling.
- **Exercise:** Open `interactive/widgets/syllabifier.html`, run the test words, and trace the MOP split by hand for one. Then pick a word whose syllabification is currently wrong or unsupported, add the needed onset cluster to `phonetics.py`, and add a `test_syllabify` case for it.
- **Milestone:** A new word correctly syllabified, gated by a test you wrote.
- **Interactive:** widget `syllabifier.html`; quiz `interactive/quizzes/phase-1-checkpoint.html`.

### — Phase 1 Checkpoint —
You can read every module in the repo, explain the phonology each encodes, and you've extended all four with tests of your own. You understand that the whole foundation exists to produce one thing: a `Pronunciation` whose `vowel_skeleton` you can now reason about. You're ready to build forward.

---

## Phase 2 — The rhyme kernel (Weeks 6–10)

**Goal:** Build `rhyme_score(a, b) -> float`, the piece the README calls "next up." Start from the perceptual definition of rhyme, ship the perfect-rhyme special case first, then loosen to graded slant rhyme, then handle unequal lengths with sequence alignment.

### Unit 5 — The vowel skeleton & the rhyme-bearing tail
- **Build:** A new `rhyme_schemer/rhyme.py`. Implement `rhyme_tail(pron) -> tuple[Syllable, ...]` — the syllables from the **last primary-stressed** syllable to the end (the perceptual rhyming part).
- **Read:** Parrish's `rhyming_part()` notes; Hirjee & Brown §2 (what counts as a rhyme).
- **Concepts:** why rhyme lives in the tail from the last stress (not the last syllable — "lessen"/"strengthen" share a final syllable but don't rhyme); the rime; stress as the anchor; reusing `Pronunciation.vowel_skeleton`.
- **Exercise:** `interactive/exercises/unit-05-rhyme-tail/` ships failing tests; make them pass. Edge cases: no primary stress (fall back to last secondary, then last vowel); monosyllables.
- **Milestone:** `rhyme_tail` passes its suite, including the "lessen/strengthen don't rhyme" case.

### Unit 6 — Perfect rhyme first
- **Build:** `rhyme_score(a, b)` for the **equal-length** case: average `vowel_similarity` over aligned nuclei in the tail, with `consonant_similarity` on codas weighted lower and onsets ignored. Calibrate so identical tails score `1.0`.
- **Read:** re-skim Hirjee & Brown's scoring section.
- **Concepts:** model the easy case before the hard one; the threshold-`1.0` special case; weighting nuclei over codas; ignoring onsets (the README's design).
- **Exercise:** Failing tests for perfect rhymes (`cat`/`hat`, `time`/`rhyme`) and clear non-rhymes; make them pass. Assert the score is symmetric and in `[0, 1]` (the repo's house style).
- **Milestone:** Perfect rhyme detected at threshold `1.0`; non-rhymes well below.

### Unit 7 — Graded slant rhyme & weighting
- **Build:** Turn `rhyme_score` into the graded kernel: expose weights (coda weight, nucleus weight) and a threshold; tune so slant rhymes land between perfect and non-rhyme.
- **Read:** the perceptual-similarity phonology paper (why imperfect rhyme tracks perceptual closeness); Hirjee & Brown's imperfect-rhyme results.
- **Concepts:** rhyme as graded, not binary; the threshold as a tunable knob; **perceptual similarity** as the target your weights approximate; the danger of over-fitting weights to a few examples.
- **Exercise:** Make "Lincoln"/"reason" score as a slant rhyme above your chosen threshold while "Lincoln"/"orange" stays below. Encode the *ordering* (perfect > slant > none) as tests, not exact magnitudes.
- **Milestone:** A graded `rhyme_score` that ranks a small battery of pairs the way your ear does.
- **Interactive:** widget `interactive/widgets/rhyme-score-sandbox.html` (planned — build it here as the unit's artifact); lesson `unit-07-the-rhyme-kernel.md`.

### Unit 8 — Unequal lengths: sequence alignment
- **Build:** Generalize `rhyme_score` to tails of **different lengths** (multisyllabic rhyme) via alignment: implement Needleman–Wunsch over vowel skeletons using `vowel_distance` as substitution cost and a tuned gap penalty.
- **Read:** SLP3 Ch. 2 **Minimum Edit Distance** (the algorithm, the backtrace); panphon's `Distance` source (feature-weighted edit distance in the wild).
- **Concepts:** edit distance / Needleman–Wunsch / DTW; substitution cost from a feature metric; gap penalties; alignment as the general case of which equal-length scoring was a special case.
- **Exercise:** `interactive/exercises/unit-08-alignment/` — implement the DP table and backtrace; make multisyllabic tests pass (e.g. "national"/"rational"; a 3-syllable vs 2-syllable near-rhyme). Verify equal-length inputs still match Unit 6's scores.
- **Milestone:** Multisyllabic slant rhymes scored sensibly; the alignment visualized in the lesson.
- **Key insight:** This is the same dynamic-programming alignment used for spell-check and DNA — you're applying a workhorse NLP algorithm to vowels.
- **Interactive:** lesson `unit-08-alignment.md`.

### — Phase 2 Checkpoint —
`rhyme_score` exists and works: it detects perfect rhyme exactly, grades slant rhyme by feature distance, and aligns tails of unequal length. You've implemented a feature-weighted alignment from scratch and understand it as classic NLP. The engine is built; the rest is putting it to work.

---

## Phase 3 — From pair-scores to a rhyme scheme (Weeks 11–15)

**Goal:** Move from "do these two rhyme?" to "find and group all the rhymes in a verse."

### Unit 9 — Multi-word spans & pronunciation variants
- **Build:** `pronunciation_for_span(words)` (a span is just a `Pronunciation`); make scoring **variant-aware** (best score over CMUdict variants), replacing the current first-variant-only behavior.
- **Read:** `pronouncing` API (`phones_for_word` returns a list); the README note on multi-word spans.
- **Concepts:** a multi-word span and a single word are the same downstream object; pronunciation **variants** and why rappers exploit them (coercion); taking the max over variants.
- **Exercise:** Score a multisyllabic *multi-word* rhyme (e.g. "get up"/"setup"). Add a variant case where the rhyme only works under the second pronunciation.
- **Milestone:** Spans and variants flow through `rhyme_score` unchanged downstream.

### Unit 10 — Grouping rhymes: similarity graphs & components
- **Build:** `group_rhymes(words, threshold)` — build a graph where an edge means "score ≥ threshold," then return connected components as rhyme classes.
- **Read:** SLP3 on clustering basics; any union-find reference.
- **Concepts:** pairwise scores → groups; thresholding; the **non-transitivity of slant rhyme** (A rhymes with B, B with C, but not A with C) and why connected components is a deliberate (debatable) choice; union-find.
- **Exercise:** Group the line-end words of a real verse. Find a real non-transitive triple and decide how your grouping should treat it; encode the decision as a test.
- **Milestone:** Line-end words of a verse grouped into colored rhyme classes (data, not yet pixels).
- **Interactive:** lesson `unit-10-non-transitivity.md`; quiz `interactive/quizzes/phase-3-checkpoint.html` (build here).
- **Key insight:** Slant-rhyme grouping isn't an equivalence relation — similarity rarely is. Choosing components vs. stricter clustering *is* a modeling decision, and naming it is half of computational linguistics.

### Unit 11 — Internal & multisyllabic rhyme: scanning a verse
- **Build:** A scanner that slides over syllables (not just line ends) to surface internal and multisyllabic rhymes within and across lines.
- **Read:** Hirjee & Brown on internal-rhyme detection; the Vox "Rapping, deconstructed" breakdown.
- **Concepts:** rhyme is not only line-final; windowing over the syllable stream; ranking candidate matches by score and length (longest/nearest, as Hirjee & Brown do).
- **Exercise:** On a verse with known internal rhymes, surface them; tune to suppress spurious low-score matches.
- **Milestone:** Internal rhymes in a real verse detected and scored.

### — Phase 3 Checkpoint —
Given a verse, rhyme-schemer finds the rhymes — line-final, internal, and multisyllabic — and groups them. Everything needed to *show* the scheme now exists as data.

---

## Phase 4 — Visualization, OOV/G2P, and evaluation (Weeks 16–22)

**Goal:** Make it visible, make it robust to unknown words, and find out whether it's any good.

### Unit 12 — Visualizing the scheme
- **Build:** A renderer that takes grouped rhymes and emits highlighted output — an HTML page coloring each rhyme class (Pudding/Vox style), plus a terminal fallback.
- **Read:** the Pudding pieces; Hirjee & Brown's "Rhyme Analyzer" UI (five formatting styles for overlapping rhymes).
- **Concepts:** mapping rhyme classes to colors; handling a word in multiple classes (internal + line-final); designing for the non-specialist reader.
- **Exercise:** Render a full verse to a standalone HTML file; handle the overlapping-membership case.
- **Milestone:** A shareable HTML visualization of a verse's rhyme scheme — the README's original goal, realized.

### Unit 13 — Out-of-vocabulary words & grapheme-to-phoneme
- **Build:** A G2P fallback for words CMUdict lacks (your Unit-1 list): rule-based first; optionally wire in a neural G2P.
- **Read:** Epitran; `g2p_en` (seq2seq); SLP3 on G2P if present in your draft.
- **Concepts:** the OOV problem; **grapheme-to-phoneme** as rule-based vs **sequence-to-sequence neural** (a direct bridge to your transformer knowledge); confidence/flagging of guessed pronunciations.
- **Exercise:** Replace skip-and-flag with a G2P guess for three of your OOV words; mark guesses as lower-confidence so scoring can discount them.
- **Milestone:** A previously-skipped word participates in a detected rhyme, flagged as G2P-derived.

### Unit 14 — Evaluation: is it any good?
- **Build:** An eval harness: a small hand-annotated verse (gold rhyme groups) and metrics over your detector's output.
- **Read:** SLP3 Ch. 2 on **precision / recall / F-score**; Hirjee & Brown's evaluation methodology.
- **Concepts:** gold annotations; precision/recall/F1 for rhyme detection; inter-annotator agreement (rhyme is subjective!); error analysis as the real payoff.
- **Exercise:** Annotate ~8 lines yourself, run the harness, and do an error analysis: are misses threshold problems, feature-coordinate problems, or OOV problems? Feed three concrete fixes back into earlier units.
- **Milestone:** A precision/recall number for your tool and a prioritized list of what to fix — measured, not guessed.
- **Key insight:** You can't improve what you can't measure, and rhyme has no perfect ground truth — agreement is partial. Building the ruler is as much the work as building the tool.

### — Phase 4 Checkpoint —
rhyme-schemer is end-to-end: text in, highlighted rhyme scheme out, unknown words handled, with a number that says how well it works and a roadmap for improving it.

---

## Phase 5 — Capstone & frontiers (Weeks 23+)

### Unit 15 — Capstone: the finished tool + the written understanding
- **Build:** Polish the pipeline into one entry point: paste a verse → an HTML visualization of its rhyme scheme, OOV handled, score reported. Then write a 2–3 page articulation of the phonology and NLP you now understand — phonemes and features, syllabification, the rhyme kernel, alignment, grouping, G2P, evaluation — and where each lives in the code.
- **Milestone:** A demo you'd show someone, plus the writeup that proves the learning, not just the code.

**Frontiers (pick your own path):**
- **Swap in panphon** for the hand-built feature tables; compare detections and re-run your eval.
- **Phonetic word embeddings** (Parrish 2017): represent whole lines as vectors for fast candidate retrieval before exact scoring.
- **Unsupervised rhyme-scheme identification** with HMMs (Addanki & Wu 2013).
- **Prosody & flow:** bring stress/meter into scoring, not just segments.
- **Variant disambiguation:** pick the pronunciation that maximizes *whole-verse* rhyme, not per-pair.

---

## Concept dependency map

Arrows mean "understand before." The left column is phonetics/phonology; the right is algorithms.

```
ARPAbet & the lexicon (U1)
        │
        ▼
Articulatory features ── vowels (U2) ── consonants (U3)
        │                     │
        ▼                     │
Syllables & MOP (U4)          │
        │                     ▼
        │            Feature distance = a baby embedding
        ▼                     │
Vowel skeleton / rhyme tail (U5)
        │
        ▼
Perfect rhyme score (U6)
        │
        ▼
Graded slant rhyme + weights (U7) ◄── perceptual similarity (phonology)
        │
        ▼
Sequence alignment (U8) ◄────────────── Minimum Edit Distance (SLP3 Ch.2)
        │
        ├───────────────┐
        ▼               ▼
Spans & variants (U9)  Grouping = graph components (U10) ◄── non-transitivity
        │               │
        └──────┬────────┘
               ▼
   Internal/multisyllabic scanning (U11)
               │
               ▼
   Visualization (U12) ── OOV / G2P (U13) ── Evaluation (U14)
               │
               ▼
           Capstone (U15)
```

**Load-bearing (do not skip):** U1 → U2 → U4 → U5 → U6 → U7 → U8 → U10. **Safe to skim if it clicks:** U3 (read), U9, U11. **Can defer:** U13, parts of U11.

---

## How to use this curriculum with Claude

- *"Teach me Unit N interactively."* → runs the unit's Socratic lesson guide in `interactive/lessons/`.
- *"Quiz me on Phase N."* → draws from `interactive/quizzes/question-bank.md`.
- *"I wrote my `rhyme_tail` for Unit 5 — review it."* → paste the code for feedback against the unit's intent.
- *"The alignment in Unit 8 isn't clicking — explain it on our actual vowel skeletons."* → a different angle on your own data.
- *"Give me a harder exercise for Unit 7."* → an extra problem scoped to the unit.
- *"Connect Unit 8 to something I already know."* → bridges to spell-check, diff, DNA alignment.

The curriculum is a guide, not a cage. The dependency map shows what's load-bearing and what you can skim if it clicks. If a unit runs long, let it — Unit 8 usually does.

*Curriculum v1.0 — June 2026. Project-driven; revise as the repo and your understanding evolve.*
