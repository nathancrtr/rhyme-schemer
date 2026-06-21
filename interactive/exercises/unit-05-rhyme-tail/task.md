# Unit 5 Exercise — `rhyme_tail`

**What you're building:** the first piece of the rhyme engine — the function that extracts the *rhyme-bearing tail* of a pronunciation. This is the spine every later scoring step works on, so it's the right place to start the build phase.

**Why it matters now:** rhyme is anchored at the **last stressed syllable**, not merely the final one. "Lessen" and "strengthen" share a final syllable yet don't rhyme; the difference is where the stress falls. Getting this slice right is what makes everything downstream (perfect rhyme, slant rhyme, alignment) operate on the correct material.

## The spec

Implement `rhyme_tail(pron) -> tuple[Syllable, ...]`:

- Return the syllables from the **last PRIMARY-stressed** syllable through the end of the word.
- Fallbacks when there is no primary stress:
  1. from the **last SECONDARY-stressed** syllable to the end, else
  2. the **final syllable** alone.
- An empty pronunciation returns an empty tuple.

## How to do it

1. Copy `rhyme.py` into the package as `rhyme_schemer/rhyme.py` and implement the function (replace the `NotImplementedError`).
2. Copy `test_rhyme_tail.py` into `tests/`.
3. Run the suite from the repo root:
   ```bash
   python -m unittest discover tests
   ```
4. Green bar = done. The tests assert the spec structurally (the tail is a suffix of the syllables; its nuclei are a suffix of `vowel_skeleton`) and by example (`around` starts the tail at the stressed syllable; `reason` returns the whole word; a stress-less pronunciation falls back to the final syllable).

## When you're stuck

Run `interactive/lessons/` has no guide for this one by design — but ask Claude *"teach me Unit 5 interactively"* or *"I wrote `rhyme_tail`, review it against the spec."* A good first move: iterate the syllables once, record the index of the last `Stress.PRIMARY`, and slice. Handle the fallbacks as a small cascade.
