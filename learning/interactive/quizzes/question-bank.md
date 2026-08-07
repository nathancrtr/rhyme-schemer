# rhyme-schemer Question Bank

A pool to draw from for self-testing (or for asking Claude to "quiz me on
Phase N"). Each question carries an answer **and** a one-line teaching note,
so a wrong answer gets a real explanation, not just "no." Mix recall,
application, and "explain why" — the last reveals understanding best.

*Refreshed August 2026: scanner-era questions added (units 9–13), stale
answers corrected, and the review-pass material (ambisyllabicity, ALINE,
the feature-space audit, the AAE grounding) folded in.*

---

## Phase 1 — Phonetic foundation

**Q (recall):** What are the three parts of a syllable in the repo's `Syllable` model, and which one is the rhyme-bearing "rime"?
**A:** onset, nucleus, coda; the **rime** is nucleus + coda.
*Teaching note:* onsets are ignored by rhyme — that's why "cat"/"hat" rhyme.

**Q (why):** Why do consonants never carry a stress digit in ARPAbet, but vowels do?
**A:** Stress is a property of syllable nuclei (vowels); consonants don't bear lexical stress.
*Teaching note:* this is why `strip_stress` returns `None` for the stress of a consonant.

**Q (application):** `pronouncing.phones_for_word("read")` returns two pronunciations. Why, and what does the repo do about it?
**A:** "read" is a heteronym (REED/RED); `pronunciations_for` returns all variants, and `best_rhyme_score` takes the max over pairings.
*Teaching note:* "the rapper picks whichever reading rhymes" — Unit 9's principle.

**Q (why):** Why is `NG` excluded from legal single-consonant onsets?
**A:** English has no syllables beginning with /ŋ/; it only occurs in codas (and intervocalically).
*Teaching note:* phonotactics is language-specific list-keeping, not a formula.

**Q (application):** Syllabify `S IH1 K S` ("six"). Where do the trailing consonants go?
**A:** One syllable: onset `S`, nucleus `IH`, coda `K S` — all finals stay in the single coda.
*Teaching note:* with no following vowel to compete, word-final consonants are all coda.

**Q (why):** Diphthongs are stored as a glide from a start point to an end point. Why not a single point?
**A:** A diphthong's vowel quality moves during articulation (e.g. `AY` in "bite"); one point can't represent the movement.
*Teaching note:* monophthongs have start == end — and the shared *offglides* are why EY/AY park near the front vowels, the audit's front-glide bias.

**Q (why):** The /t/ in "sweaty" is called *ambisyllabic*. What two facts pull the syllable boundary in opposite directions?
**A:** It flaps (so it isn't a true onset), but a stressed lax vowel can't end an English syllable (so it can't be pure coda either — "sweh" is impossible).
*Teaching note:* MOP resolves the tie by fiat; ledger item 7 records what that costs the kernel.

**Q (why):** The sonority hierarchy does two different jobs in this project. Name both.
**A:** It orders the consonant MANNER axis (similarity), and it predicts which onsets are legal (syllables rise to the nucleus, fall after).
*Teaching note:* one concept, two load-bearing uses — Unit 3 and Unit 4.

**Q (application):** Why can't English speakers say "pneumatic" the Greek way, and what does the syllabifier do with the same cluster in "hypnotize"?
**A:** "pn" is not a legal English onset; in "hypnotize" MOP keeps the p as coda and gives only n to the next onset (`HH IH1 P . N AH0 . T AY2 Z`).
*Teaching note:* borrowings obey the borrower's phonotactics.

---

## Phase 2 — The rhyme kernel

**Q (why):** Why is the rhyming tail defined from the **last stressed** syllable to the end, rather than just the last syllable?
**A:** Because "lessen"/"strengthen" share a final syllable but don't rhyme; rhyme is anchored at the last stress.
*Teaching note:* this is Parrish's `rhyming_part` idea — and "last" (not "first") primary is what makes multi-word spans work for free.

**Q (application):** Your perfect-rhyme scorer gives 1.0 to "cat"/"hat". What roughly should it give "cat"/"cot", and why isn't it 1.0?
**A:** Below 1.0 — same coda, but `AE`≠`AA`, so the graded vowel similarity is < 1.
*Teaching note:* this is the gap the Unit 7 graded kernel exists to handle.

**Q (why):** Why is the nucleus/coda blend divided by the total weight?
**A:** So identical syllables score exactly 1.0 for *any* weights — perfect rhyme stays the top of the scale while you tune.
*Teaching note:* the normalization is what makes the weights safely sweepable.

**Q (why):** Why are onsets ignored and codas down-weighted in `rhyme_score`?
**A:** Rhyme is vowel-led; onsets differ even in perfect rhymes, and codas contribute less than nuclei perceptually.
*Teaching note:* over-weighting codas lets a matched consonant rescue a bad vowel pair — a recorded false-positive risk (read/seed).

**Q (application):** Two tails have lengths 3 and 2. Why can't the Unit 6 scorer handle this, and what algorithm fixes it?
**A:** Position-by-position averaging has no pairing for the extra nucleus; **sequence alignment** (Needleman–Wunsch) fixes it.
*Teaching note:* the equal-length case is the gap-free diagonal — tie-breaking toward the diagonal preserves Unit 6's scores exactly.

**Q (why):** In alignment, what goes wrong if the gap penalty is too low? Too high?
**A:** Too low: everything aligns to gaps and scores collapse. Too high: genuinely spare syllables get force-matched.
*Teaching note:* the penalty must sit above near-vowel substitutions and below far ones — 0.6 in the repo.

**Q (why):** Why does `align_tails` return columns rather than just a score?
**A:** The backtrace's actual pairing is needed downstream — coda scoring uses it, and the renderer will need to show *which* syllables rhymed.
*Teaching note:* a DP without a backtrace answers "how good" but never "which."

**Q (application):** ALINE names a salience weight for every feature. Find the weight in our vowel space that exists only as a structural choice.
**A:** The backness:height ratio — Euclidean distance fixes it at 1:1 silently; it isn't a parameter, so no sweep can move it.
*Teaching note:* every implicit equal-weighting is a hidden decision (Unit 8, §3b).

**Q (why):** The audit found EY~IH is our closest vowel pair but corpus-negative in rap practice. What's the mechanism on our side?
**A:** Diphthong offglides: EY (and AY) end near ɪ, parking the front glides on top of the front vowels — but rappers rhyme the whole vowel, not its endpoint.
*Teaching note:* ledger item 11(a); the fix must be surgical because EH~IH is corpus-*endorsed*.

---

## Phase 3 — From scores to a scheme

**Q (why):** Slant-rhyme similarity isn't transitive. What concrete problem does that create for grouping by connected components?
**A:** A and C can land in one group *through* B even though A and C don't rhyme — one generous edge glues two good clusters (chaining/percolation).
*Teaching note:* components = single-link clustering; the pathology has a name and a literature (Unit 10).

**Q (application):** Rappers "coerce" pronunciations to force rhymes. How does variant-aware scoring model that — and what does it cost?
**A:** `best_rhyme_score` takes the max over all variant pairings; the cost is optimism by construction — more variants, more chances to clear threshold spuriously.
*Teaching note:* right model for "did the rapper find a rhyme," wrong for "do these naturally rhyme" — the debt is on the books for Unit 14.

**Q (why):** The kernel ranked lincoln/listen above lincoln/reason and the learner's ear disagreed. Why was raising the nucleus weight the wrong fix?
**A:** The mismatch was in the *reading*, not the metric: the learner's idiolect has IY in "Lincoln"; rewarding exact vowel matches harder widened the wrong gap.
*Teaching note:* variants, not metric generosity — the principle has now won three times (lincoln, smoothing, rhoticity).

**Q (why):** Why isn't line-final-only rhyme detection enough for hip-hop?
**A:** Hip-hop is dense with **internal** and **multisyllabic** rhyme within and across lines.
*Teaching note:* Unit 11 enumerates (span, anchor) candidates rather than sliding a fixed window — the anchor is part of a candidate's identity.

**Q (application):** "Get up ~ setup" scores 0.5 in the bare kernel. What's wrong, and which unit fixes it?
**A:** Citation stress puts a primary on "up," shrinking the span's tail; performed "GET-up" demotes it. Unit 11 makes performed stress an enumerated, *priced* reading.
*Teaching note:* the scanner is a second Pronunciation factory; the kernel never changed.

**Q (why):** In the scanner, why must the anchor pair rhyme *on its own* (the seed gate), instead of letting the full-tail average decide?
**A:** An average lets a perfect trailing column subsidize a failing anchor; the ear treats the anchor as a gate, not a term.
*Teaching note:* mean-vs-gate — and identical anchors are rime riche, which opens nothing.

**Q (why):** Selection ranks by score, not length ("an extension must raise the average"). What desirable behavior falls out for free?
**A:** Glued rhyme chains auto-split into one-beat matches: a mega-span always averages below its best internal hit.
*Teaching note:* one of the review's three "genuinely fresh" ideas.

**Q (application):** Grouping feeds the scanner's *selected matches* as edges — why not just recompute `best_is_rhyme` between all selected spans?
**A:** Recomputing would readmit pairs the gates already rejected; the selected matches *are* the judgments.
*Teaching note:* layers must not silently overrule each other.

---

## Phase 4 — Visualization, G2P, evaluation

**Q (why):** Why does a single word sometimes need to belong to more than one rhyme color?
**A:** It can participate in several rhyme events at once — up to five classes per word in real data, with extents that nest *and* cross.
*Teaching note:* policy: fill by best-scoring class, tick bars for the rest, receipts in the tooltip.

**Q (why):** The renderer colors by *rhyme class*, not by vowel. What's the argument?
**A:** The scanner spent eleven units judging; color-by-vowel would discard those judgments and show raw input phonetics instead.
*Teaching note:* render the conclusions — which honestly includes rendering the mistakes.

**Q (recall):** A verse has ten rhyme classes and the palette has eight slots. What happens to classes nine and ten, and why?
**A:** They fold into a neutral wash — never cycle hues, because a reused hue is a false claim that two classes match.
*Teaching note:* largest classes claim slots first.

**Q (why):** In the G2P chain, why does the hand lexicon outrank the spelling rules?
**A:** "Shoulda" *pattern-matches* -a-for-er (via "shoulder") but actually contracts "should have" — only curated truth knows that.
*Teaching note:* dictionary → lexicon → rules → letter-to-sound; each link outranks the next for a stated reason.

**Q (application):** Why does "chokin'" get its dictionary stem's pronunciation *with N for NG*, rather than being normalized to "choking"?
**A:** The apostrophe is the lyricist transcribing performance — coda N is what's said, and N-vs-NG is a coda difference the kernel scores.
*Teaching note:* dialect spellings are performance transcriptions; the rules recover the stem and keep the spelled surface phonology.

**Q (why):** Only letter-to-sound guesses carry a cost in the G2P chain. Why?
**A:** The lexicon and the spelling *testify*; an LTS guess is an unlikely claim that must buy its way into a rhyme (same mechanism as coercion cost).
*Teaching note:* confidence is priced, not modeled — the kernel stays provenance-free.

**Q (recall):** Which sociolinguistic features do the two dialect rules encode, and roughly who documented them?
**A:** g-drop = the (ING) variable (Fischer 1958; Green 2002 for AAE); -a-for-er = AAE non-rhoticity (Thomas 2007 — most common in unstressed syllables, exactly the rule's environment).
*Teaching note:* the citations answer "why does your tool rewrite Black speech?" with receipts — it doesn't; the performed form is the one that scores.

**Q (why):** G2P's pronunciations were *correct*, yet coverage made grouping worse. How?
**A:** Every new word is a new node; -in'~-ing bridge edges glued three separate families into one OW mega-class.
*Teaching note:* new coverage inherits old debt — recall gains arrive married to precision losses (ledger item 9).

**Q (why):** Gold annotators mark *groups*, but the harness scores *pairs*. Why explode?
**A:** Groups impose transitivity gold shouldn't (annotating A B C implies A~C); scoring pairs makes one bad bridge cost exactly the bad pairs it creates.
*Teaching note:* the format's `not:` directive is an ear-veto on one induced pair.

**Q (application):** Why report both pairwise link P/R/F *and* class-level clustering metrics (B-cubed/ARI)?
**A:** They answer different questions — the mega-class pathologies only show up in the class-level numbers.
*Teaching note:* high edge precision + low class precision = the glue is the problem, not the kernel.

**Q (why):** A word isn't in CMUdict. Name the modern rule-based and neural options — and what the repo actually does.
**A:** Rule-based: Epitran-style rules; neural: byte-level transformers (ByT5 G2P, CharsiuG2P). The repo uses a hand chain (lexicon + two cited dialect rules + crude LTS) behind a priced `Guess` interface a neural model could slot into.
*Teaching note:* `g2p_en` is a stale 2019 mention; SIGMORPHON shared tasks are the benchmark line.

**Q (why):** Rhyme annotators genuinely disagree. Why is that a *finding* rather than a nuisance, and what does the harness do about it?
**A:** Perception of slant rhyme differs (Katz's result); the harness reports inter-annotator agreement as the *ceiling* any scanner score is read against.
*Teaching note:* single-annotator gold optimizes toward one person's ear.
