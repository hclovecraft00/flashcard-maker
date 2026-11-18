# Picking the words

One sub-agent picks the words for one chapter. Give it this file, `meanings.md`, and the paths below. Its output goes to `entries/chN.json` in the project folder.

## What the sub-agent reads

- `text/chN.txt`: the chapter’s clean text. This is the source of truth; read all of it.
- `candidates/chN.json`: every word in the chapter that is rare in everyday English, with how often the chapter uses it (`words`), repeated two-word phrases (`phrases`), and author names already removed from citations (`author_names_removed`). The list is a starting point, not the answer: it misses everyday-looking words with a technical meaning, and it includes rare words nobody needs.
- `book.json`: the reader’s level (`level`), spelling (`spelling`), the topic labels to choose from (`topics`), and `contents`, the titles of every chapter in the whole book.

## Which words to keep

Keep a term when the reader needs it to follow the book, and at least one of these is true:

1. The chapter uses it 3 or more times (count every form: singular, plural, abbreviated species names such as “A. rubens”).
2. The chapter explains or defines it.
3. The chapter relies on it as a core idea, even if it appears once.

Count these as technical even though they look ordinary:
- words for positions and directions (*radial*, *distal*, *oral*)
- everyday words the book uses in a special sense (*disc*, *ray*, *order*, *Recent* with a capital R)
- fixed two-word terms made of common words (*tube feet*, *fossil record*)

Names follow their own rule. Genus names, full species names (two words, both halves, such as “Asterias rubens”) and named groups (families, orders, classes) stay when the chapter uses them 4 or more times, or when the book features them. A name is featured when a title in `book.json` `contents` names it (a later chapter called “Astropecten” makes *Astropecten* featured in every chapter), or when the chapter treats it as a main example.

Leave out:
- people’s names, places and journal titles
- everyday words an adult already knows, judged by you rather than by the frequency list. The list treats some technical phrases as everyday (“tube feet” is made of two common words), so check the chapter’s usage.
- words used once in passing, such as one species in a list of examples
- lab techniques and units used once
- broken fragments left over from the PDF

When in doubt about a technical term the chapter uses more than once, include it. The build step drops anything below the thresholds automatically, so you don’t need to count exactly.

## One term per card

- Never combine two terms (“oral / actinal” becomes two entries).
- Use the form the book uses most, singular or plural, as `term`. Put other forms the reader might type in `alt`: the other number, British and American spellings (“caeca”, “ceca”), the abbreviation if the book uses one.
- A two-word term is one entry when the pair is the term (“tube feet”, “connective tissue”, “broadcast spawning”).
- Don’t worry about words earlier chapters already picked; duplicates are removed later, and the earliest chapter keeps the word.

## Output

Write a JSON array to `entries/chN.json`, ordered roughly by how much the chapter uses each term:

```json
[
  {
    "term": "autotomy",
    "alt": [],
    "topic": "eco",
    "kind": "concept",
    "featured": false,
    "defined_in_book": true,
    "meaning": "Dropping a body part on purpose, here an arm, usually at a set breaking point, to escape a predator or damage.",
    "roots": "autos = self; tomē = cut"
  }
]
```

- `topic`: one of the keys in `book.json` `topics`.
- `kind`: `"name"` for genus, species and group names; `"concept"` for everything else.
- `featured`: `true` for a name that a chapter title in `contents` names, or that this chapter treats as a main example.
- `defined_in_book`: `true` when the chapter defines or explains the term.
- `meaning` and `roots`: follow `meanings.md`.

Check the file parses (`python3 -c "import json; json.load(open('entries/chN.json'))"`). Then reply with only: how many entries, how many are names, and up to 10 borderline terms you left out and why. Don’t paste the entries.

## Words the reader adds or removes

- To add a word, append an entry to the right `entries/chN.json` with `"force": true`, so the thresholds don’t drop it. Write the meaning from the book as usual.
- To remove a word, add its term to `removed` in `book.json`.
- Then run `words.py` and `build.py` again. Practice progress is kept, because a word’s progress is stored under its chapter and spelling.
