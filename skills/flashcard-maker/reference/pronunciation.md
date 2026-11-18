# Pronunciation guides

Every word gets an easy-read guide with the stressed syllable in capitals: `aw-TOT-uh-mee`, `mad-ruh-POR-ite`. The page shows it next to the word, and the browser’s voice reads it aloud for words it can’t pronounce from their spelling.

## Where guides come from

1. **Dictionary.** `words.py` looks each word up on Wiktionary and converts the phonetic spelling (IPA) into a guide. It prefers the British pronunciation, or the American one when `book.json` `spelling` is `american`. Plurals and spelling variants borrow from a related entry (“ossicles” from “ossicle”). Results are cached in `pron/ipa_cache.json`, so each word is looked up once.
2. **By hand.** Words with no dictionary entry (most genus, species and group names, many technical words) are listed in `pron/missing.json`. Write a guide for each into `pron/manual.json` as `{"term": "guide"}`, by the rules below. The Words tab marks these “no dictionary entry”, so the reader knows they are less certain.

## Writing a guide by hand

Use the same spelling system the converter uses:

| Sound | Write | Example |
|---|---|---|
| short a, e, i, o, u | a, e, ih (open) / i (closed), o, u | `KAT`, `MET`, `pih-LAJ-ik`, `OS-ih-kul`, `MUS-ul` |
| long vowels | ay, ee, eye / y, oh, oo, yoo | `GAY`, `SEE-lum`, `my-OH-sis`, `TOH-tul`, `KYOO-pyoo-luh` |
| unstressed “uh” | uh (open) / u (closed) | `uh-NAL-ih-sis`, `kum-PRES-iv` |
| r-vowels | ar, or, er, air, eer | `KAR-tih-lij`, `FOR-mul`, `TER-mih-nul`, `LAIR-ee-uh` |
| other | aw, ow, oy, th, sh, ch, j, zh, ng | `AW-tum`, `OWT`, `KRY-noydz` |

- Split syllables with hyphens. Capitalise the stressed syllable only.
- Put a consonant with a short vowel’s syllable so it reads right: `OS-ih-kul`, not `O-sih-kul`.
- Two-word terms get two guides separated by a space: `as-TEER-ee-us ROO-benz`.

## Scientific names (traditional English pronunciation of Latin)

There is no single correct pronunciation, so aim for the one most English-speaking biologists use:

- Stress the second-to-last syllable when its vowel is long or followed by two consonants; otherwise the third-to-last: `as-TEER-ee-us`, `pak-sih-LOSS-ih-duh`.
- Family names (-idae) end `-ih-dee`, with stress before it: `loo-ih-DY-ih-dee`, `as-troh-pek-TIN-ih-dee`. Orders (-ida) end `-ih-duh`: `val-VAT-ih-duh`.
- -ae at the end of a word is `-ee`: `ped-ih-suh-LAIR-ee-ee`.
- c and g are soft before e, i, y (`sih`, `jih`) and hard elsewhere.
- ch is k (`brak-ee-oh-LAIR-ee-uh`); ph is f; initial pt-, ps-, cn- drop the first letter (`ter-uh-STER-ih-dee`).
- A species name keeps its own stress: `oh-KRAY-shus`, `glay-see-AY-lis`.
