# rhyme-schemer: Learning Resources

*A curated shelf for learning NLP and computational phonology **by building rhyme-schemer**. For a senior software engineer who learns by implementing, with a linguistics background to lean on, working ~3–5 hrs/week. Math depth: moderate (follow the formulas, skip the proofs). Formats: text + code.*

This is a reference shelf, not a syllabus — `curriculum.md` says *when* to read what. Resources are grouped by **role**. Every link was checked live in June 2026; the entries marked *(added July 2026)* come from the external research review in the top-level `REVIEW.md`, which is itself worth reading as a map of where this project sits in the field.

---

## How this is organized

- **Tier 1 — The core path.** Read substantially. These four carry the course.
- **Tier 2 — Deepening & alternatives.** Consult as a unit demands.
- **Tier 3 — Reference & practice.** Look things up; read source.
- **Tier 4 — Culture & motivation.** The "why this is worth building" tier.

Tags: `[TEXT] [CODE] [PAPER] [TOOL] [INTERACTIVE]`.

---

## Tier 1 — The core path

### Speech and Language Processing (3rd ed.) — Jurafsky & Martin `[TEXT]`
- **URL:** https://web.stanford.edu/~jurafsky/slp3 (free draft; Jan 2025 release)
- **Why this one:** *The* computational-linguistics textbook, written by a computational linguist, and the single best map of the whole field. You already know it from your ML/AI shelf — here you'll mine specific chapters rather than read cover-to-cover. It supplies the formal backbone for three pillars of rhyme-schemer: the **Phonetics** chapter (articulatory phonetics, the IPA, ARPAbet — exactly what `phonetics.py` and `features.py` encode), the **Minimum Edit Distance** section of Ch. 2 (the alignment algorithm you'll need to compare vowel skeletons of unequal length), and **Vector Semantics & Embeddings** (Ch. 6), which reframes your feature-distance metric as a baby embedding — the conceptual bridge to your ML interests.
- **Note:** Chapter numbers drift between drafts; navigate by title from the index page.

### Automatic Detection of Internal and Imperfect Rhymes in Rap Lyrics — Hirjee & Brown (2009) `[PAPER]`
- **URL:** https://ismir2009.ismir.net/proceedings/OS8-1.pdf (ISMIR 2009)
- **Why this one:** This is rhyme-schemer's prior art — the paper that did this exact task and did it well. They score *imperfect* (slant) rhymes with a phoneme-similarity matrix learned from real rap lyrics, then detect internal and line-final rhymes. Reading it tells you which design decisions in the repo are standard practice (phoneme features, scoring over the rhyming tail) and which are your own simplifications (hand-placed coordinates instead of a learned matrix). It is the benchmark your finished tool should be measured against.
- **Companion (deeper):** *Using Automated Rhyme Detection to Characterize Rhyming Style in Rap Music* (Empirical Musicology Review 5(4):121–145, 2010) and Hirjee's full thesis *Rhyme, Rhythm, and Rhubarb* (https://uwspace.uwaterloo.ca/items — search the title) expand the method and the evaluation. The thesis's annotated lyrics were the field's benchmark — an evaluation resource for Unit 14, and using them makes results directly comparable to the named prior art.
- **Field note** *(added July 2026)*: their work was never displaced for this task, but it also wasn't extended — today it is cited mostly as the source of the **rhyme density** metric used to evaluate rap *generation* (e.g. DopeLearning, Malmi et al. KDD 2016: https://arxiv.org/abs/1505.04771). rhyme-schemer is one of very few active successors to their actual detection program.

### Allison Parrish — `pronouncing` + phonetic-similarity work `[CODE][PAPER]`
- **Library docs:** https://pronouncing.readthedocs.io/ — the CMUdict interface the repo already depends on.
- **CMUdict teaching notes:** https://github.com/aparrish/gen-text-workshop/blob/master/cmu_pronouncing_dictionary_notes.md — her `rhyming_part()` ("everything from the stressed syllable nearest the end") is *precisely* the vowel-skeleton idea in rhyme-schemer's roadmap, in a few lines of Python.
- **Paper:** *Poetic Sound Similarity Vectors Using Phonetic Features* (AAAI 2017): https://chuck.stanford.edu/chai/data/aparrish/parrish-2017-aaai.pdf
- **Why this one:** Parrish is the ideal bridge figure for your profile — a programmer-poet who turns phonemes into feature vectors for creative tools, exactly the spirit of this project. Her library is your data layer; her teaching notes are the gentlest possible on-ramp to the rhyming-tail concept; her paper shows where the feature-distance approach goes next (full phonetic word embeddings that handle out-of-vocabulary words). Read the docs and notes early, the paper around Phase 2–3.

### A first look at articulatory phonetics — the IPA, hands-on `[INTERACTIVE]`
- **Interactive IPA chart with audio:** https://www.ipachart.com/ — click a vowel/consonant, hear it.
- **IPA vowel chart (reference):** https://en.wikipedia.org/wiki/Vowel#Vowel_chart and https://en.wikipedia.org/wiki/IPA_vowel_chart_with_audio
- **Why this one:** `features.py` places every vowel on the IPA vowel quadrilateral (height × backness) and every consonant by place × manner. To trust — and tune — those coordinates, you need the articulatory picture in your ear and your mouth, not just on a grid. Spend an hour *making the sounds* while watching where your tongue goes. This is the one place where audio beats text. (The course also ships an interactive vowel-quadrilateral widget built from the repo's own numbers — see `interactive/widgets/`.)

---

## Tier 2 — Deepening & alternatives

### panphon — IPA → articulatory feature vectors — Mortensen et al. `[CODE][PAPER]`
- **GitHub:** https://github.com/dmort27/panphon · **Paper (COLING 2016):** https://aclanthology.org/C16-1328/
- **Role:** The library `features.py` explicitly names as its future replacement. It maps 5,000+ IPA segments to 21 articulatory features and — crucially — its `Distance` class computes *feature-weighted edit distance*, which is your alignment unit (Unit 8) and your feature unit (Units 2–3) fused into one tool. Read its `Distance` source when you build alignment; consider swapping it in during the capstone.

### Epitran — precision grapheme-to-phoneme — Mortensen et al. (2018) `[TOOL]`
- **GitHub:** https://github.com/dmort27/epitran
- **Role:** For Unit 13 (out-of-vocabulary words). When CMUdict doesn't have a word, you need grapheme-to-phoneme (G2P). Epitran is a solid rule-based G2P.
- **Currency note** *(added July 2026)*: `g2p_en` (https://github.com/Kyubyong/g2p), previously listed here as "the neural alternative," is a 2019 artifact and effectively unmaintained. The current neural G2P baseline is byte-level transformers — ByT5 G2P (https://www.isca-archive.org/interspeech_2022/zhu22_interspeech.pdf) and CharsiuG2P (https://github.com/lingjzhu/CharsiuG2P) — with the SIGMORPHON 2020–22 shared tasks (https://aclanthology.org/2020.sigmorphon-1.13.pdf) as the benchmark line. And for the *dialect-variant* gap CMUdict leaves (tuning-ledger item 2), the field's answer is Wiktionary-scraped lexicons: **WikiPron** (Lee et al., LREC 2020: https://aclanthology.org/2020.lrec-1.521/).

### The phonology of imperfect rhyme — perceptual similarity `[PAPER]`
- **Katz (2015),** *Hip-hop rhymes reiterate phonological typology*. **Lingua** 160:54–73: https://www.sciencedirect.com/science/article/abs/pii/S0024384115000492 (open repository copy: https://researchrepository.wvu.edu/cgi/viewcontent.cgi?article=2149&context=faculty_publications — cite the *Lingua* venue).
- **Kawahara (2007),** *Half rhymes in Japanese rap lyrics and knowledge of similarity*. *Journal of East Asian Linguistics* 16: https://link.springer.com/article/10.1007/s10831-007-9009-1
- **Role:** The deep "why" behind the whole feature-distance bet. These studies find that the imperfect rhymes rappers actually use track **perceptual similarity** between sounds — which is the empirical justification for modeling rhyme as distance in an articulatory space rather than as exact match. Read when you start tuning weights (Unit 7) and want to know what "correct" even means. (Background: Steriade's P-map.)
- **Use them as data, not just motivation** *(added July 2026)*: Katz's correspondence counts and Kawahara's half-rhyme statistics tell you *empirically* which vowel pairs rappers treat as rhymable — they can sanity-check the hand-placed vowel space (the ledger's EY/IH generosity!) today, before any Unit 14 sweep runs. Also worth knowing: articulatory adjacency is not perceptual confusability — the IPA chart is a tongue-position diagram, and the standard perceptual embedding is Bark-scaled formant (F1/F2) space. The line of work is alive: McPherson & Ryan (2019) survey musical adaptation as phonological evidence (https://compass.onlinelibrary.wiley.com/doi/10.1111/lnc3.12359), and a 2024 study extends imperfect-rhyme analysis to Chinese hip hop (https://www.degruyterbrill.com/document/doi/10.1515/lingvan-2024-0093/html).

### The detection literature after 2010 — what moved on around Hirjee & Brown `[PAPER]` *(added July 2026)*
- **Reddy & Knight (2011),** *Unsupervised Discovery of Rhyme Schemes* (ACL): https://aclanthology.org/P11-2014/ — the standard-cited paper for the task this repo calls "grouping." The scheme is a **latent variable** learned by EM from the corpus itself, with *no pronunciation dictionary at all*; its framing (a stanza's scheme as a structured object to infer, not a graph to component-ize) is the principled alternative to connected components. Read alongside Unit 10.
- **Plecháč (2018),** *A Collocation-Driven Method of Discovering Rhymes*: https://www.researchgate.net/publication/328847558 · `rhymetagger`: https://github.com/versotym/rhymetagger — bootstraps rhyme pairs from end-of-line co-occurrence statistics, then trains on its own output; F ≈ 0.90–0.95 across seven languages, still an active line (2026 training-size study: https://arxiv.org/abs/2604.08156).
- **Haider & Kuhn (2018),** *Supervised Rhyme Detection with Siamese Recurrent Networks*: https://aclanthology.org/W18-4509/ — ~97% pair-classification accuracy from raw *character* sequences, no phonetic features at all, evaluated partly on **hip-hop lyrics annotated for rhyme and assonance**. Doubly relevant: the neural baseline a symbolic pipeline should beat or match, and an existing annotation effort for Unit 14.
- **Role:** None of these invalidates the feature-based symbolic approach — they are mostly line-final-only, and Hirjee & Brown remain the only true task-peer for internal rap rhyme — but a research artifact must position itself against the field as it is. These three are the field.

### Kondrak's ALINE — the phonetic-alignment prior art `[PAPER]` *(added July 2026)*
- **Kondrak (2000),** *A New Algorithm for the Alignment of Phonetic Sequences* (NAACL): https://webdocs.cs.ualberta.ca/~kondrak/papers/chum.pdf
- **Role:** Unit 8's Needleman–Wunsch over vowel skeletons with feature-decomposed substitution costs is, almost exactly, ALINE — the standard phonetic-alignment algorithm for 25 years. Reinventing it was the right pedagogical call; read it afterward for credit and for the design answers it already worked out: per-feature **salience weights**, separate vowel/consonant treatment, and expansions/compressions for diphthongs — several questions the repo currently answers ad hoc.

### Evaluation corpora & the beat grid `[PAPER]` *(added July 2026)*
- **MCFlow** — Condit-Schultz (2016), *MCFlow: A Digital Corpus of Rap Transcriptions*, *Empirical Musicology Review* 11(2): https://emusicology.org/article/id/4737/ — 124 rap songs, 374 verses, ~6k measures, freely available, with rhythmic, prosodic, phonetic **and rhyme** annotations *including metric placement*. One dataset addresses both the Unit 14 evaluation gap and the prosody frontier (ledger items 5–6); its observed stress placements could even validate the scanner's inferred anchors directly.
- **Haider & Kuhn's rhyme gold standard** (above) — includes a hip-hop set annotated for rhyme *and assonance*, directly matching the project's north star.
- **Hirjee & Brown's annotated lyrics** (thesis, Tier 1 entry) — the field's benchmark; using them makes results comparable to the named prior art.
- **Adams (2009),** *On the Metrical Techniques of Flow in Rap Music*, *Music Theory Online* 15(5): https://mtosmt.org/issues/mto.09.15.5/mto.09.15.5.adams.html — the music-theory side of the "performance context carries information a segment-only scanner cannot see" diagnosis.
- **Ohriner (2019),** *Flow: The Rhythmic Voice in Rap Music* (Oxford UP): https://global.oup.com/academic/product/flow-9780190670412 — the book-length computational treatment of rap prosody, including rhyme's interaction with meter. The prosody & flow frontier, anchored to names.
- **Content-safety caveat:** the repo's fixture rule (no multi-line commercial lyrics) is in tension with evaluating on corpora of commercial rap. Evaluate locally against downloaded corpora; the harness should store **song IDs + offsets, never lyric text**.

### LLMs and phonology — why a symbolic scanner matters in 2026 `[PAPER]` *(added July 2026)*
- **PhonologyBench** — Suvarna et al. (2024): https://arxiv.org/html/2404.02456v2 — LLMs working from orthographic tokens are *weak* at exactly the phoneme-level skills this pipeline implements symbolically.
- **Hybrid systems** — e.g. the 2026 Greek rhyme-detection/generation hybrid: https://arxiv.org/pdf/2601.09631 — the emerging pattern is LLM fluency filtered through phonological machinery like this repo's.
- **Role:** The positioning claim in the README's "Where this sits in the field" section, with receipts.

### Wikipedia, used well `[TEXT]`
- **Sonority Sequencing Principle:** https://en.wikipedia.org/wiki/Sonority_Sequencing_Principle
- **Phonotactics:** https://en.wikipedia.org/wiki/Phonotactics · **Syllable:** https://en.wikipedia.org/wiki/Syllable
- **ARPABET:** https://en.wikipedia.org/wiki/ARPABET
- **Role:** Fast, accurate orientation for the phonology concepts the repo leans on (MOP, legal onsets, onset/nucleus/coda). Good enough for an engineer who needs the working idea, not a linguistics degree.

---

## Tier 3 — Reference & practice

| Resource | URL | Use it for |
|---|---|---|
| CMU Pronouncing Dictionary | http://www.speech.cs.cmu.edu/cgi-bin/cmudict | The pronunciation data under everything; look up entries, see variants. *Know its limits:* North American citation pronunciation, informally maintained, no dialect coverage, inconsistent variants — the README names it as a threat to validity |
| WikiPron | https://aclanthology.org/2020.lrec-1.521/ | Wiktionary-scraped pronunciation lexicons — the candidate source for the dialect variants ledger item 2 needs |
| MCFlow corpus | https://emusicology.org/article/id/4737/ | Annotated rap transcriptions — Unit 14 ground truth + beat-grid data |
| `pronouncing` API reference | https://pronouncing.readthedocs.io/en/latest/pronouncing.html | `phones_for_word`, `rhymes`, `rhyming_part`, `stresses` |
| panphon API | https://github.com/dmort27/panphon#api | `Distance`, feature tables, feature-edit-distance |
| Hirjee & Brown "Rhyme Analyzer" | https://www.semanticscholar.org/paper/edd32747cc8ac12fa3bf82f3aa19cae19933a88b | A reference UI for visualizing detected rhymes (Unit 12) |
| Prior-art repos to read | https://github.com/alexmarozick/RapAnalysis | How others structured the same pipeline (read critically) |

---

## Tier 4 — Culture & motivation

### The Pudding — Matt Daniels `[INTERACTIVE]`
- *The Largest Vocabulary in Hip-Hop:* https://pudding.cool/projects/vocabulary/
- *The Language of Hip Hop:* https://pudding.cool/2017/09/hip-hop-words/
- **Role:** The visual-journalism north star the README points at — the standard for turning lyric data into something a non-specialist *feels*. Keep these open when you design the visualization (Unit 12); the bar for "highlight the rhymes" is set here.

### Vox / Estelle Caswell — *Rapping, deconstructed: The best rhymers of all time* `[VIDEO]`
- Search the title on YouTube (Vox, Earworm series). The breakdown of multisyllabic and internal rhyme in rap is the clearest motivation for why perfect-rhyme matching is not enough — and previews internal rhyme (Unit 11).

---

## Suggested first moves (formalized in `curriculum.md`)

1. Get the repo running: `pip install -r requirements.txt`, `python -m unittest discover tests` (all green).
2. Skim the Hirjee & Brown 2009 intro and one Pudding piece — know what you're building toward.
3. Play with `pronouncing` in a REPL and the interactive IPA chart — get the data and the sounds under your fingers.
4. Read `phonetics.py` and `features.py` alongside the SLP3 Phonetics chapter.

Then open `curriculum.md` and start Phase 1.

---

## Notes for course design

- **The repo is the spine.** Every concept here is in service of a component you will build or have built. Theory is just-in-time.
- **The learner's linguistics background is an asset** — lean into it for phonetics and phonology; it's the rare subject where you start ahead. Don't re-teach what a phoneme is; do make the *computational* treatment precise.
- **Feature distance is a baby embedding.** Foreground this bridge: it connects this project to the learner's ML/AI track and makes the eventual panphon/Parrish "phonetic vectors" step feel inevitable rather than novel.

*Resources verified available and current, June 2026; entries marked (added July 2026) folded in from the external research review (`REVIEW.md`), links as cited there.*
