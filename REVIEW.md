# A research review of rhyme-schemer

*Reviewer's note: this is an evaluation of the project as a unit of research —
the currency of its cited literature, its blind spots, and its novelty — not a
code review. It was written July 2026, with the repo at the end of Unit 13
(G2P) and Unit 14 (evaluation) next on the roadmap. I've tried to be candid
the way I'd want a senior colleague to be with me: the praise below is meant,
and so are the criticisms.*

---

## Summary verdict

This is an unusually well-reasoned implementation built on a **correct but
narrow** slice of the literature. The two foundational bets — that rap rhyme
is graded perceptual similarity anchored at the last stressed vowel, and that
imperfect rhyme therefore needs a distance metric rather than an equality test
— are exactly right and remain the consensus position of the phonological
literature ([Katz 2015](https://www.sciencedirect.com/science/article/abs/pii/S0024384115000492),
[Kawahara 2007](https://link.springer.com/article/10.1007/s10831-007-9009-1)).
The choice of [Hirjee & Brown](https://ismir2009.ismir.net/proceedings/OS8-1.pdf)
as the named prior art is the right choice: sixteen years on, it is *still*
the reference point for internal + imperfect rhyme detection in rap
specifically, and nothing has displaced it for that exact task.

But the citation shelf reads as if computational rhyme detection stopped in
2010. It didn't. There is a fifteen-year literature on rhyme detection in
verse generally — unsupervised, collocation-driven, and supervised-neural —
that the project never engages, and, more materially, **annotated evaluation
corpora for this task already exist** while Unit 14 currently plans to build
ground truth from scratch. That is the one omission that would materially
change the project as implemented; the rest are matters of positioning and of
knowing which of your problems already have names.

On novelty: most of the pipeline is a clean, pedagogically excellent
reimplementation of known practice — which is fine, because that is the
project's stated purpose. But two or three ideas in the scanner are, to my
knowledge, genuinely fresh articulations, and with the right evaluation they
would clear the bar for a workshop paper. Details in §5.

---

## 1. Currency check: the cited foundations

**Hirjee & Brown (2009, 2010) — still the right prior art, correctly read.**
The [ISMIR 2009 paper](https://ismir2009.ismir.net/proceedings/OS8-1.pdf) and
the [EMR 2010 expansion](https://kb.osu.edu/handle/1811/48548) remain the
canonical work on scoring imperfect internal rhyme in rap with a
phoneme-similarity matrix. The repo's self-description of its own deviation —
"hand-placed coordinates instead of a learned matrix" — is accurate and
honest. Nothing since has redone their task better *for rap*; what has
happened instead is that the general rhyme-detection problem moved on around
them (see §3.1). Their work has not been superseded so much as orphaned: it
gets cited today mostly as the source of the **rhyme density** metric used to
evaluate rap *generation* systems
([DopeLearning, Malmi et al. 2016](https://arxiv.org/abs/1505.04771);
[GhostWriter evaluation, Potash et al.](https://arxiv.org/pdf/1612.03205)),
not extended as a detection method. That makes this project one of very few
active successors to their actual program — worth saying out loud in the
README.

**Katz (2015) and Kawahara (2007) — current, and the strongest thing on the
shelf.** One correction: [Katz 2015](https://www.sciencedirect.com/science/article/abs/pii/S0024384115000492)
appeared in *Lingua* 160:54–73 (the learning-resources entry links only the
WVU repository copy; cite the venue). The finding — imperfect rhyme
correspondences in AAE hip-hop track perceptual similarity and recapitulate
typological markedness — is precisely the empirical license for the
feature-distance bet, and this line of work is *alive*: see e.g.
[McPherson & Ryan's overview of musical adaptation as phonological evidence
(2019)](https://compass.onlinelibrary.wiley.com/doi/10.1111/lnc3.12359) and a
[2024 study of imperfect rhyming in Chinese hip hop](https://www.degruyterbrill.com/document/doi/10.1515/lingvan-2024-0093/html).
The project cites Katz as motivation but does not yet *use* him as data —
that's the missed trick (§3.2).

**panphon, Parrish, MOP, Needleman–Wunsch — all fine.**
[panphon](https://github.com/dmort27/panphon) remains maintained and standard;
Parrish's `pronouncing` is stable (if frozen); the Maximal Onset Principle is
the standard engineering syllabification (with the standard caveat that
phonologists since Kahn 1976 note English intervocalic consonants are often
*ambisyllabic* — "sweaty" arguably shares its /t/ — which is quietly relevant
to ledger item 7, where MOP's clean handoff of medial consonants to onsets is
what makes them invisible to the kernel). NW is unimpeachable as an alignment
algorithm; see §3.3 for the prior art it reinvents.

**CMUdict — the aging foundation nobody mentions.** CMUdict is North American
citation pronunciation with informal maintenance, no dialect coverage, and
famously inconsistent variant entries. Two of the project's own recorded pain
points — the lincoln/reason "listen > reason" issue being a *dialect variant*
problem, and G2P having to reconstruct AAE surface forms by rule — are
downstream of this single dependency. The field has been moving toward
Wiktionary-scraped lexicons ([WikiPron, Lee et al. LREC 2020](https://aclanthology.org/2020.lrec-1.521/))
for coverage and variant handling. The project doesn't need to switch, but it
should *name* CMUdict as a threat to validity: the plan to protect
lincoln/reason "with dialect variants, not metric generosity" (ledger item 2)
currently has no identified source for those variants.

---

## 2. The strongest features of the work

Before the criticisms, three things a reviewer should not take for granted:

1. **The tuning ledger is real science hygiene.** Nine numbered, dated,
   example-grounded open problems, each with candidate fixes and an explicit
   commitment to decide by evaluation rather than intuition, is better
   epistemic practice than most published systems papers manage. Several of my
   "blind spots" below are already half-diagnosed in that ledger; my
   contribution is mostly to tell the author that their problems have names
   and literatures.

2. **The stratified architecture is a theory claim, and a defensible one.**
   "A word and a span are both just `Pronunciation`s; a citation reading and a
   performed reading are both just `Pronunciation`s" is a genuinely elegant
   invariant, and the decision to keep provenance (coercion cost, G2P cost)
   *priced at the boundary* rather than modeled in the kernel is the kind of
   separation working phonologists would recognize as
   underlying-vs-surface-form discipline.

3. **The honesty about transitivity.** Flagging connected components as "a
   deliberate, debatable modeling choice" that imposes transitivity on a
   non-transitive relation is exactly right — see §4.3 for why the debate has
   already been held elsewhere.

---

## 3. Superseded or aging elements

### 3.1 The detection literature moved on around Hirjee & Brown

Three lines of work postdate 2010 and are absent from the repo's framing:

- **Unsupervised rhyme-scheme discovery.**
  [Reddy & Knight (ACL 2011)](https://aclanthology.org/P11-2014/) learn rhyme
  schemes generatively — the scheme is a latent variable, rhyme "strength"
  between word pairs is learned by EM from the corpus itself, with **no
  pronunciation dictionary at all**. This is the standard-cited paper for the
  task this repo calls "grouping," and its framing (a stanza's scheme as a
  structured object to infer, not a graph to component-ize) is the principled
  alternative to connected components (§4.3).
- **Collocation-driven detection.**
  [Plecháč (2018)](https://www.researchgate.net/publication/328847558) /
  [rhymetagger](https://github.com/versotym/rhymetagger) bootstraps rhyme
  pairs from end-of-line co-occurrence statistics, then trains on its own
  output; F ≈ 0.90–0.95 across seven languages, and the line of work is still
  active ([2026 training-size study](https://arxiv.org/abs/2604.08156)).
- **Supervised neural detection.**
  [Haider & Kuhn (2018)](https://aclanthology.org/W18-4509/) train a Siamese
  recurrent network on *character* sequences — no phonetic features at all —
  and hit ~97% pair-classification accuracy in three languages, **evaluated
  in part on hip-hop lyrics annotated for rhyme and assonance**. This paper is
  doubly relevant: as the neural baseline the symbolic pipeline should beat or
  match, and as an existing annotation effort (§4.1).

None of this invalidates the repo's approach — a feature-based symbolic
pipeline is more interpretable, more tunable, and pedagogically superior, and
the line-final-only scope of most of these systems means Hirjee & Brown remain
the only true task-peers. But a research artifact must position itself against
the field as it is, and right now the README implies the field is Vox videos
and one 2009 paper.

### 3.2 Hand-placed geometry where learned similarity exists

The vowel quadrilateral with Euclidean distance is a fine *pedagogical* stand-
in, and the module says so. But two stronger options are sitting in the
project's own bibliography, and the ledger's recurring complaint — "vowel-space
generosity" (items 2, 3, 8: EY~IH at 0.95, EH~AH and EY~EH passengers) — is
the predictable symptom of the weaker choice:

- **Articulatory adjacency is not perceptual confusability.** The IPA chart is
  a tongue-position diagram, not a psychoacoustic space. The standard
  perceptual embedding is Bark-scaled formant (F1/F2) space, and the standard
  rhyme-specific evidence is *corpus-derived*: Katz 2015's correspondence
  counts and Kawahara 2007's half-rhyme statistics tell you empirically which
  vowel pairs rappers actually treat as rhymable. The EY/IH problem is a
  question those tables can answer today, without waiting for Unit 14.
- **Hirjee & Brown's central move — learn the matrix.** Their BLOSUM-style
  log-odds matrix, estimated from observed rhyme pairs, *is* the fix for
  hand-placed coordinates, and it is the very thing the repo's own resource
  notes identify as "your own simplification." Unit 14's sweep should include
  "replace/refit the vowel space from rhyme-pair data" as a condition, not
  just "tune the weights of the hand space."

### 3.3 The alignment reinvents ALINE (uncredited, not incorrectly)

NW over vowel skeletons with `vowel_distance` substitution costs is, almost
exactly, [Kondrak's ALINE (2000)](https://webdocs.cs.ualberta.ca/~kondrak/papers/chum.pdf):
dynamic-programming alignment of phone sequences with feature-decomposed
multivalued similarity — the standard phonetic-alignment algorithm for 25
years, still in use. panphon's `Distance` class (already cited for other
reasons) ships feature-weighted edit distance out of the box. Reinventing this
was the right pedagogical call; the lesson materials should still cite it,
both for credit and because ALINE's design (salience weights per feature,
separate vowel/consonant treatment, expansions/compressions for diphthongs)
answers several questions the repo is currently answering ad hoc.

### 3.4 G2P: the deliberate stop is fine; the cited alternatives are stale

Hand-written LTS as a priced last resort is defensible and the
`Guess.cost` design is nice. Two notes: `g2p_en`, cited as "the neural
alternative," is a 2019 artifact and effectively unmaintained; the current
neural G2P baseline is byte-level transformer models
([ByT5 G2P](https://www.isca-archive.org/interspeech_2022/zhu22_interspeech.pdf),
[CharsiuG2P](https://github.com/lingjzhu/CharsiuG2P)) with the
[SIGMORPHON 2020–22 shared tasks](https://aclanthology.org/2020.sigmorphon-1.13.pdf)
as the benchmark line. And the dialect-respelling rules (g-drop, -a-for-er)
are quietly doing **AAE phonology by intuition**; the features they encode
(velar nasal fronting, non-rhoticity) are extensively documented in the
sociolinguistics literature, and grounding each rule in a documented feature
rather than an observed fixture case would both harden the rules and make the
inevitable "why does your tool rewrite Black speech?" question answerable
with citations. This is also a place to tread respectfully: the NLP
literature on AAE is substantially a literature about systems *failing* AAE
speakers; a tool that takes performed AAE phonology as ground truth rather
than as noise is on the right side of that, and should say so deliberately.

---

## 4. Material omissions

### 4.1 Evaluation corpora already exist — the single most consequential gap

Unit 14 is framed as "evaluation against annotated ground truth," with the
implication that the ground truth will be produced in-house. Three existing
resources change that calculus:

- **[MCFlow](https://emusicology.org/article/id/4737/)** (Condit-Schultz,
  *Empirical Musicology Review* 2016): 124 rap songs, 374 verses, ~6k measures,
  transcribed with rhythmic, prosodic, phonetic, **and rhyme annotations**,
  freely available. This is, to my knowledge, the only public corpus that
  annotates rap rhyme *including its metric placement* — which is exactly the
  beat-grid information ledger items 5 and 6 say the scanner cannot see.
  One dataset addresses the evaluation gap *and* the prosody frontier.
- **Haider & Kuhn's rhyme gold standard** (§3.1) includes a hip-hop set
  annotated for rhyme *and assonance* — directly matching the project's
  north star of assonance-inclusive detection.
- **Hirjee & Brown's own annotated lyrics** (from the
  [thesis](https://www.uwspace.uwaterloo.ca/bitstreams/5e80ea84-582e-4fde-afda-4465810740a2/download))
  were the field's benchmark; using them makes results directly comparable to
  the named prior art.

Two methodological cautions the plan should absorb now: (a) rhyme annotation
has genuinely contested ground truth — annotators disagree about slant rhyme
because perception differs (this is Katz's *finding*, not just an annoyance) —
so any in-house annotation needs a second annotator and an agreement number,
or the tuning sweep optimizes toward one person's ear; (b) pairwise P/R/F on
rhyme links and class-level clustering metrics (B-cubed, adjusted Rand) answer
different questions, and the mega-class pathologies (ledger items 1, 9) will
only show up in the latter. Report both.

*(One genuine caveat: the repo's content-safety rule — no multi-line
commercial lyrics in fixtures — is in tension with evaluating on corpora of
commercial rap. Evaluation can still run locally against downloaded corpora
without committing lyric text; the harness should store song IDs + offsets,
not verses.)*

### 4.2 The beat grid has a literature

Ledger items 5–6 correctly diagnose that "performance context carries
information a segment-only scanner cannot see." The music-theory side has
been building exactly that apparatus for fifteen years:
[Adams (2009)](https://mtosmt.org/issues/mto.09.15.5/mto.09.15.5.adams.html)
on the metrical techniques of flow, Condit-Schultz's MCFlow encoding, and
[Ohriner's *Flow: The Rhythmic Voice in Rap Music* (OUP 2019)](https://global.oup.com/academic/product/flow-9780190670412),
which is the book-length computational treatment of rap prosody, including
rhyme's interaction with meter. The "performed stress" problem the scanner
solves segmentally (coercion + pricing) is, in that literature, solved
observationally (transcribe where the beat falls). The two are complementary
— the repo's approach works on bare text, theirs needs audio/transcription —
but the roadmap's "prosody & flow frontier" should be anchored to these names
rather than left as a blank spot on the map.

### 4.3 The transitivity debate has already been held

Connected components over noisy similarity edges is single-link clustering,
and its failure mode — one generous edge glues two good clusters into a
mega-class — is the oldest known pathology in clustering (chaining /
percolation). Ledger items 1 and 9 *observed* this empirically ("mush twin,"
"OW mega-class via connected components"); it was predictable a priori, and
the standard remedies are known: correlation clustering on signed edge
weights, community detection that penalizes sparse cuts, or — most relevantly
— Reddy & Knight's move of making the *scheme* the object of inference so
that class structure is regularized by a prior over schemes. The unit's
framing ("components impose transitivity knowingly; that is the modeling
choice the unit is about") is pedagogically sound, but the research posture
should be: this choice has a literature, the literature predicts our two
worst warts, and Unit 14 should include one edge-weight-aware clustering
condition to measure what the components choice actually costs.

### 4.4 Positioning against the LLM era

Not an omission in the implementation — an omission in the framing. The
current benchmark literature
([PhonologyBench, 2024](https://arxiv.org/html/2404.02456v2); the
[2026 Greek rhyme-detection hybrid](https://arxiv.org/pdf/2601.09631)) has
established that LLMs, working from orthographic tokens, are *weak* at
precisely the phoneme-level skills this pipeline implements symbolically, and
the emerging pattern is hybrid systems: LLM fluency filtered through exactly
this kind of phonological machinery. A symbolic, interpretable,
feature-grounded rhyme scanner is not a retro exercise in 2026; it is the
component the generation side of the field currently imports or badly
approximates. The README could claim this position in two sentences, and
should.

---

## 5. Novelty assessment

Being direct, because an honest novelty ledger is more useful than a kind one:

**Not novel (nor claimed to be):** the rhyme tail (Parrish's `rhyming_part`,
and centuries of prosody before that); graded phoneme similarity for slant
rhyme (Hirjee & Brown 2009; panphon); DP alignment of phone strings (Kondrak
2000); connected components as rhyme classes (standard practice, with known
problems); dictionary-first G2P with fallbacks (the field's consensus
architecture, as the module itself notes). The syllable-first decomposition
is *less* standard than the repo implies — Hirjee & Brown work from stressed
vowels without full syllabification — but "we syllabified first" is an
engineering choice, not a contribution.

**Genuinely fresh, to my knowledge, and worth developing:**

1. **Performed stress as an enumerable, priced reading.** Treating the
   stress-placement of a candidate as part of its *identity* — enumerating
   (span, anchor) pairs, minting coerced-stress `Pronunciation`s as data, and
   charging a context-free coercion prior that scoring must overcome — is a
   move I have not seen in the detection literature. Hirjee & Brown take
   dictionary stress as given; the musicology corpora observe performed
   stress rather than infer it. "Infer the performance from text by making
   stress a latent, priced variable" is a real idea, and it is the repo's
   most publishable one — *if* Unit 14 shows it buys precision/recall on an
   external corpus (MCFlow's stress placements could even validate the
   inferred anchors directly, a lovely experiment).
2. **The average-raising extension rule.** Replacing longest-first match
   ranking with "an extension must raise the average to earn its seat," and
   getting auto-splitting of glued rhyme chains as a corollary, is a small
   but elegant selection principle with a clean justification. It is the
   kind of thing that makes a good workshop-paper section.
3. **"Dialect spellings are performance transcriptions."** The G2P principle
   of recovering the dictionary stem but *keeping the spelled surface
   phonology* — because the apostrophe is testimony, not noise — is a
   genuinely nice articulation of something lyric-normalization pipelines
   get wrong by design. It is closer to a position statement than a
   technique, but it is a good position, and I'd like to see it argued
   against the normalization literature explicitly.

None of these alone is a conference paper. Together — a segmental scanner
with priced performed-stress inference, evaluated on MCFlow against Hirjee &
Brown and a Haider & Kuhn-style neural baseline — they plausibly are, at a
venue like the NLP4MusA / Computational Humanities / ML4Audio workshop tier.

## 6. Recommendations, in priority order

1. **Redefine Unit 14 around existing corpora.** MCFlow + Haider & Kuhn's
   hip-hop annotations + Hirjee & Brown's data as ground truth; in-house
   annotation only to fill gaps, with a second annotator and a reported
   agreement figure. Report pairwise link P/R/F *and* class-level B-cubed/ARI.
2. **Make "learn the similarity matrix" a Unit 14 condition,** not just
   weight-tuning of the hand-placed space. Katz 2015's and Kawahara 2007's
   correspondence data can sanity-check the vowel space (EY/IH!) immediately,
   before any sweep runs.
3. **Add one edge-weight-aware clustering condition** to the sweep to price
   the connected-components choice (§4.3), rather than adding more gates
   upstream of a percolation-prone grouping step.
4. **Write the positioning section**: two paragraphs in the README situating
   the project against Reddy & Knight, Plecháč, Haider & Kuhn, and the
   LLM-phonology benchmarks, and claiming the hybrid-era relevance of a
   symbolic phonological scanner. Cite Kondrak in the alignment lesson.
5. **Name the CMUdict threat to validity** and identify a dialect-variant
   source (WikiPron/Wiktionary scraping, or explicit AAE-feature rules with
   sociolinguistic citations) before ledger item 2's "protect lincoln/reason
   with variants" plan can be executed.
6. **Ground the G2P dialect rules in the documented AAE-phonology literature**
   — one citation per rule — both for correctness and for the ethics
   paragraph this tool will eventually need.

## References

- Hirjee & Brown (2009). [Automatic Detection of Internal and Imperfect Rhymes in Rap Lyrics](https://ismir2009.ismir.net/proceedings/OS8-1.pdf). ISMIR.
- Hirjee & Brown (2010). [Using Automated Rhyme Detection to Characterize Rhyming Style in Rap Music](https://kb.osu.edu/handle/1811/48548). *Empirical Musicology Review* 5(4).
- Katz (2015). [Hip-hop rhymes reiterate phonological typology](https://www.sciencedirect.com/science/article/abs/pii/S0024384115000492). *Lingua* 160:54–73.
- Kawahara (2007). Half rhymes in Japanese rap lyrics and knowledge of similarity. *Journal of East Asian Linguistics* 16.
- Reddy & Knight (2011). [Unsupervised Discovery of Rhyme Schemes](https://aclanthology.org/P11-2014/). ACL.
- Plecháč (2018). [A Collocation-Driven Method of Discovering Rhymes](https://www.researchgate.net/publication/328847558) / [rhymetagger](https://github.com/versotym/rhymetagger); see also [training-size sensitivity (2026)](https://arxiv.org/abs/2604.08156).
- Haider & Kuhn (2018). [Supervised Rhyme Detection with Siamese Recurrent Networks](https://aclanthology.org/W18-4509/). SIGHUM/LaTeCH-CLfL.
- Condit-Schultz (2016). [MCFlow: A Digital Corpus of Rap Transcriptions](https://emusicology.org/article/id/4737/). *Empirical Musicology Review* 11(2).
- Ohriner (2019). [*Flow: The Rhythmic Voice in Rap Music*](https://global.oup.com/academic/product/flow-9780190670412). Oxford University Press.
- Adams (2009). [On the Metrical Techniques of Flow in Rap Music](https://mtosmt.org/issues/mto.09.15.5/mto.09.15.5.adams.html). *Music Theory Online* 15(5).
- Kondrak (2000). [A New Algorithm for the Alignment of Phonetic Sequences](https://webdocs.cs.ualberta.ca/~kondrak/papers/chum.pdf). NAACL; ALINE.
- Mortensen et al. (2016). [PanPhon](https://aclanthology.org/C16-1328/). COLING.
- Lee et al. (2020). [Massively Multilingual Pronunciation Modeling with WikiPron](https://aclanthology.org/2020.lrec-1.521/). LREC.
- Zhu et al. (2022). [ByT5 model for massively multilingual grapheme-to-phoneme conversion](https://www.isca-archive.org/interspeech_2022/zhu22_interspeech.pdf). Interspeech; [CharsiuG2P](https://github.com/lingjzhu/CharsiuG2P).
- Suvarna et al. (2024). [PhonologyBench: Evaluating Phonological Skills of Large Language Models](https://arxiv.org/html/2404.02456v2).
- Malmi et al. (2016). [DopeLearning: A Computational Approach to Rap Lyrics Generation](https://arxiv.org/abs/1505.04771). KDD.
- (2026). [LLMs Got Rhythm? Hybrid Phonological Filtering for Greek Poetry Rhyme Detection and Generation](https://arxiv.org/pdf/2601.09631).
- (2024). [Variation is the way to perfection: imperfect rhyming in Chinese hip hop](https://www.degruyterbrill.com/document/doi/10.1515/lingvan-2024-0093/html). *Linguistics Vanguard*.
- McPherson & Ryan (2019). [Musical adaptation as phonological evidence](https://compass.onlinelibrary.wiley.com/doi/10.1111/lnc3.12359). *Language and Linguistics Compass*.
