# rhyme-schemer: Learning Resources

*A curated shelf for learning NLP and computational phonology **by building rhyme-schemer**. For a senior software engineer who learns by implementing, with a linguistics background to lean on, working ~3–5 hrs/week. Math depth: moderate (follow the formulas, skip the proofs). Formats: text + code.*

This is a reference shelf, not a syllabus — `curriculum.md` says *when* to read what. Resources are grouped by **role**. Every link was checked live in June 2026.

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
- **Companion (deeper):** *Using Automated Rhyme Detection to Characterize Rhyming Style in Rap Music* (Empirical Musicology Review 5(4):121–145, 2010) and Hirjee's full thesis *Rhyme, Rhythm, and Rhubarb* (https://uwspace.uwaterloo.ca/items — search the title) expand the method and the evaluation.

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
- **Role:** For Unit 13 (out-of-vocabulary words). When CMUdict doesn't have a word, you need grapheme-to-phoneme (G2P). Epitran is a solid rule-based G2P; `g2p_en` (https://github.com/Kyubyong/g2p) is a neural alternative whose seq2seq model connects directly to what you know about transformers.

### The phonology of imperfect rhyme — perceptual similarity `[PAPER]`
- *Hip-hop Rhymes Reiterate Phonological Typology* / perceptual-similarity studies of rap rhyme: https://researchrepository.wvu.edu/cgi/viewcontent.cgi?article=2149&context=faculty_publications
- **Role:** The deep "why" behind the whole feature-distance bet. These studies find that the imperfect rhymes rappers actually use track **perceptual similarity** between sounds — which is the empirical justification for modeling rhyme as distance in an articulatory space rather than as exact match. Read when you start tuning weights (Unit 7) and want to know what "correct" even means. (Background: Steriade's P-map.)

### Wikipedia, used well `[TEXT]`
- **Sonority Sequencing Principle:** https://en.wikipedia.org/wiki/Sonority_Sequencing_Principle
- **Phonotactics:** https://en.wikipedia.org/wiki/Phonotactics · **Syllable:** https://en.wikipedia.org/wiki/Syllable
- **ARPABET:** https://en.wikipedia.org/wiki/ARPABET
- **Role:** Fast, accurate orientation for the phonology concepts the repo leans on (MOP, legal onsets, onset/nucleus/coda). Good enough for an engineer who needs the working idea, not a linguistics degree.

---

## Tier 3 — Reference & practice

| Resource | URL | Use it for |
|---|---|---|
| CMU Pronouncing Dictionary | http://www.speech.cs.cmu.edu/cgi-bin/cmudict | The pronunciation data under everything; look up entries, see variants |
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

*Resources verified available and current, June 2026.*
