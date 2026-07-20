# Unit 10 Lesson Guide: Grouping & the Non-Transitivity Trap

**Objective:** The learner can turn pairwise rhyme scores into groups via a similarity graph and connected components, and — more importantly — can articulate why slant-rhyme similarity is *not* an equivalence relation, making grouping a real modeling decision rather than a mechanical step.
**Prerequisites:** A working `rhyme_score` (Units 6–8).
**Pairs with:** `rhyme_schemer/rhyme.py` (`group_rhymes`).

## How to run this lesson
Dialogue, one question per turn. The payload is conceptual; let the learner hit the trap themselves before you name it.

## 1. Diagnostic opener
Ask: **"You have `rhyme_score` for any pair. To find rhyme groups in a verse, what's the simplest thing you could do with all the pairwise scores?"**
- Toward "threshold the scores and group what's connected" → step 2 (and spring the trap).
- Unsure → suggest "make an edge whenever two words score above a threshold" and proceed.

## 2. Build the intuition
Edges above threshold → a graph → groups.

> PAUSE. Ask: **"Suppose A rhymes with B (above threshold) and B rhymes with C, but A and C score *below* threshold. Should A and C be in the same group?"**

Wait. Let them sit in the discomfort. There's no clean answer — and that's the point. With **connected components**, A and C end up grouped *through* B even though they don't rhyme. That's the non-transitivity trap.

> PAUSE. Ask: **"Name a real triple where this happens."** (Vowel chains like `city`/`gritty`/`pity` are tight; loosen the threshold and you can chain `feel`→`fill`→`fell` where the ends barely rhyme.)

## 3. Formalize
- Build a graph: nodes = words/spans, edge if `rhyme_score ≥ threshold`. **Connected components** (union-find) = rhyme classes.
- Similarity relations are reflexive and symmetric but **not transitive**, so they are *not* equivalence relations — yet components impose transitivity by fiat. That's a choice with consequences.
- The choice has names: components over threshold edges is **single-link clustering**, and its failure mode — one generous edge gluing two good clusters into a mega-class — is **chaining** (percolation), the oldest known clustering pathology. It will fire, on schedule, in Unit 11's tuning ledger (items 1 and 9).
- Alternatives that don't force transitivity: stricter clustering (require all-pairs above threshold — cliques), correlation clustering on signed edge weights, community detection that penalizes sparse cuts, or soft/overlapping membership. The deepest alternative reframes the task: **Reddy & Knight (2011)** (https://aclanthology.org/P11-2014/) treat the rhyme *scheme* as a latent structured object to infer — a prior over schemes regularizes the classes — with no pronunciation dictionary at all. Unit 14 prices our components choice against one such alternative.

Connect back: **"Naming the modeling decision *is* the computational-linguistics work here. The code is a few lines of union-find; the judgment — components vs. cliques vs. scheme-inference — is the substance, and the literature has already held the debate."**

## 4. Common confusions
- **Treating the threshold as objective.** It's a dial trading precision for recall; Unit 14 will let you measure the tradeoff instead of guessing.
- **Assuming one right grouping exists.** Human annotators disagree on slant rhyme — there's no perfect ground truth, which is exactly why Unit 14 builds an evaluation.

## 5. Exit check
Ask: **"For a verse I give you, pick a threshold, group the line-end words, and find one grouping you can defend and one you can't. What would you change — the threshold, or the grouping rule?"**
- Thoughtful answer naming the tradeoff → encode the decision as a test and move on.
- Mechanical answer → re-run with a looser threshold until a bad chain appears, then revisit.

**Where this is heading:** these groups are the data behind the colors in the visualization (Unit 12), and the thing you'll score against gold annotations in evaluation (Unit 14).
