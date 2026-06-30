# rhyme-schemer Question Bank

A pool to draw from when the learner says *"quiz me on Phase N"* or *"test me on Unit N."* Each question carries an answer **and** a one-line teaching note, so a wrong answer gets a real explanation, not just "no." Mix recall, application, and "explain why" — the last reveals understanding best.

---

## Phase 1 — Phonetic foundation

**Q (recall):** What are the three parts of a syllable in the repo's `Syllable` model, and which one is the rhyme-bearing "rime"?
**A:** onset, nucleus, coda; the **rime** is nucleus + coda.
*Teaching note:* onsets are ignored by rhyme — that's why "cat"/"hat" rhyme.

**Q (why):** Why do consonants never carry a stress digit in ARPAbet, but vowels do?
**A:** Stress is a property of syllable nuclei (vowels); consonants don't bear lexical stress.
*Teaching note:* this is why `strip_stress` returns `None` for the stress of a consonant.

**Q (application):** `pronouncing.phones_for_word("read")` returns two pronunciations. Why, and what does the repo currently do about it?
**A:** "read" is a heteronym (present/past, REED/RED); the repo takes the *first* variant only.
*Teaching note:* variant handling is deferred to Unit 9.

**Q (why):** Why is `NG` excluded from legal single-consonant onsets?
**A:** English has no syllables beginning with /ŋ/; it only occurs in codas (and intervocalically).
*Teaching note:* this is the one hard-coded exception in `_ILLEGAL_SINGLE_ONSETS`.

**Q (application):** Syllabify `S IH1 K S` ("six"). Where do the trailing consonants go?
**A:** One syllable: onset `S`, nucleus `IH`, coda `K S` — all finals stay in the single coda.
*Teaching note:* with no following vowel to compete, word-final consonants are all coda.

**Q (why):** Diphthongs are stored as a glide from a start point to an end point. Why not a single point?
**A:** A diphthong's vowel quality moves during articulation (e.g. `AY` in "bite"); one point can't represent the movement.
*Teaching note:* monophthongs have start == end.

---

## Phase 2 — The rhyme kernel

**Q (why):** Why is the rhyming tail defined from the **last stressed** syllable to the end, rather than just the last syllable?
**A:** Because "lessen"/"strengthen" share a final syllable but don't rhyme; rhyme is anchored at the last stress.
*Teaching note:* this is Parrish's `rhyming_part` idea.

**Q (application):** Your perfect-rhyme scorer gives 1.0 to "cat"/"hat". What roughly should it give "cat"/"cot", and why isn't it 1.0?
**A:** Below 1.0 — same coda, but `AE`≠`AA`, so the graded vowel similarity is < 1.
*Teaching note:* this is the gap the Unit 7 graded kernel exists to handle.

**Q (why):** Why are onsets ignored and codas down-weighted in `rhyme_score`?
**A:** Rhyme is vowel-led; onsets differ even in perfect rhymes, and codas contribute less than nuclei perceptually.
*Teaching note:* over-weighting codas lets a matched consonant rescue a bad vowel pair — wrong.

**Q (application):** Two tails have lengths 3 and 2. Why can't the Unit 6 scorer handle this, and what algorithm fixes it?
**A:** Position-by-position averaging has no pairing for the extra nucleus; **sequence alignment** (Needleman–Wunsch) fixes it.
*Teaching note:* the equal-length case is the gap-free diagonal of the alignment.

**Q (why):** In alignment, what goes wrong if the gap penalty is too low?
**A:** Everything aligns to gaps, collapsing the score; gaps must cost more than a good substitution.
*Teaching note:* too high and genuine extra syllables can't be skipped — it's a tuning balance.

---

## Phase 3 — From scores to a scheme

**Q (why):** Slant-rhyme similarity isn't transitive. What concrete problem does that create for grouping by connected components?
**A:** A and C can land in one group *through* B even though A and C don't rhyme.
*Teaching note:* the alternative (cliques / all-pairs) avoids this but groups less.

**Q (application):** Rappers "coerce" pronunciations to force rhymes. How does variant-aware scoring help?
**A:** Taking the best score over CMUdict variants lets the rhyme-friendly pronunciation win.
*Teaching note:* it's why "business"/"witness" can be made to rhyme under one variant.

**Q (why):** Why isn't line-final-only rhyme detection enough for hip-hop?
**A:** Hip-hop is dense with **internal** and **multisyllabic** rhyme within and across lines.
*Teaching note:* Unit 11 slides a window over the syllable stream to catch these.

---

## Phase 4 — Visualization, OOV, evaluation

**Q (why):** Why does a single word sometimes need to belong to more than one rhyme color?
**A:** It can participate in both an internal rhyme and a line-final rhyme simultaneously.
*Teaching note:* Hirjee & Brown's UI used five overlapping formatting styles for this.

**Q (application):** A word isn't in CMUdict. Name a rule-based and a neural way to get its pronunciation.
**A:** Rule-based G2P (e.g. Epitran); neural seq2seq G2P (e.g. `g2p_en`).
*Teaching note:* the neural approach is a transformer/seq2seq model — your ML track shows up here.

**Q (why):** Rhyme has no perfect ground truth. Why build an evaluation harness anyway?
**A:** To measure precision/recall and do error analysis — you can't improve what you can't measure, even if agreement is partial.
*Teaching note:* inter-annotator disagreement is itself a finding about slant rhyme.

**Q (application):** Your detector misses a rhyme a human catches. What are the three places the failure could live?
**A:** Threshold too strict; feature coordinates off; or the word was OOV/mis-pronounced.
*Teaching note:* error analysis routes each miss back to the unit that owns it.
