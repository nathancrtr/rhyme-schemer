"""Per-vowel Bark means for AAE, from CORAAL's DC read passage. GENERATED.

License: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/),
inherited from the sources below, whose license requires derived versions
to carry it. Do not edit by hand. Regenerate with
``python learning/audits/derive_coraal_stella_bark.py``, whose docstring
explains every filtering step.

Sources: Farrington, Quartey, Tacata & Kendall (2023), CORAAL:DCB Stella
Passage (Washington DC 2016), version 2023.03,
https://oraal.github.io/dcb-stella; Kendall, Quartey, Farrington, McLarty,
Arnson & Josler (2018), CORAAL:DCB (Washington DC 2016), version
2018.10.06 (speaker metadata); Kendall & Farrington (2023), The Corpus of
Regional African American Language, version 2023.06,
https://doi.org/10.7264/1ad5-6t35.

16 adult men reading "Please Call Stella"; primary-stressed vowels,
proclitics and pre-R vowels excluded. A proof of concept, not reference
values: several vowels rest on one word per speaker (see WORDS).

``MEANS[vowel]`` is ((F1, F2) at 20%, (F1, F2) at 80%), in Bark, averaged
per speaker and then across speakers. ``SPEAKERS`` and ``TOKENS`` count
what is behind each mean; ``DROPPED`` lists vowels with too few speakers.
"""

MEANS = {
    'AA': ((5.8488, 9.0292), (5.8476, 8.9906)),
    'AE': ((5.9448, 11.9353), (5.6081, 11.9719)),
    'AH': ((5.4159, 9.9989), (5.3982, 9.7764)),
    'AO': ((5.4847, 9.1485), (5.6358, 8.3517)),
    'AY': ((6.361, 10.6467), (6.2748, 11.1164)),
    'EH': ((4.9927, 11.0827), (5.2709, 11.4967)),
    'ER': ((5.0997, 10.7596), (5.2176, 10.6214)),
    'EY': ((5.116, 12.1308), (4.5347, 12.5278)),
    'IH': ((4.5356, 12.1423), (4.4611, 12.6067)),
    'IY': ((3.954, 13.1648), (3.9971, 13.1575)),
    'OW': ((4.9044, 9.5228), (4.3859, 7.9088)),
    'OY': ((4.5934, 7.9149), (4.1845, 10.9946)),
    'UW': ((4.2223, 9.8692), (4.301, 10.0102)),
}

SPEAKERS = {
    'AA': 16,
    'AE': 16,
    'AH': 13,
    'AO': 16,
    'AY': 16,
    'EH': 16,
    'ER': 12,
    'EY': 16,
    'IH': 16,
    'IY': 16,
    'OW': 16,
    'OY': 16,
    'UW': 16,
}

TOKENS = {
    'AA': 36,
    'AE': 97,
    'AH': 23,
    'AO': 51,
    'AY': 17,
    'EH': 66,
    'ER': 24,
    'EY': 64,
    'IH': 116,
    'IY': 157,
    'OW': 33,
    'OY': 16,
    'UW': 60,
}

WORDS = {
    'AA': {'bob': 16, 'frog': 16, 'bother': 1, 'stop': 1, 'sa': 1, 'ah': 1},
    'AE': {'plastic': 17, 'snack': 16, 'bags': 16, 'ask': 15, 'slabs': 15, 'at': 12, 'can': 3, 'that': 1, 'bla': 1, 'plast': 1},
    'AH': {'brother': 9, 'of': 8, 'from': 4, 'up': 1, 'uh': 1},
    'AO': {'call': 17, 'also': 17, 'small': 15, 'on': 1, 'tall': 1},
    'AY': {'five': 16, 'i': 1},
    'EH': {'stella': 18, 'fresh': 16, 'red': 16, 'wednesday': 15, 'get': 1},
    'ER': {'her': 24},
    'EY': {'maybe': 16, 'snake': 16, 'station': 16, 'train': 14, 'rain': 1, 'okays': 1},
    'IH': {'things': 30, 'thick': 16, 'big': 16, 'kids': 16, 'six': 15, 'bring': 12, 'into': 3, 'will': 3, 'this': 2, 'with': 2, 'skip': 1},
    'IY': {'we': 32, 'these': 29, 'please': 17, 'cheese': 16, 'meet': 16, 'peas': 14, 'she': 14, 'need': 9, 'three': 7, 't': 1, 'mean': 1, 'pe': 1},
    'OW': {'go': 16, 'snow': 15, 'oh': 1, 'so': 1},
    'OY': {'toy': 16},
    'UW': {'spoons': 17, 'blue': 16, 'scoop': 14, 'into': 10, 'to': 1, 'you': 1, 'spoon': 1},
}

# vowel -> (speakers, tokens), below the minimum of 8 speakers
DROPPED = {
    'UH': (1, 1),
}
