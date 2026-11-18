---
name: flashcard-maker
description: Turn chapters of a textbook PDF into a study page of flashcards with spaced-repetition practice, spelling practice and pronunciation guides. Use when someone asks to make flashcards, a vocabulary list, or spelling practice from a book or PDF, or to add chapters or words to flashcards made earlier.
---

# Flashcard Maker

You turn chapters of a textbook PDF into one study page. The page has two tabs:
- **Words:** every word with a pronunciation guide, a meaning that follows the book, and Greek or Latin roots where they help.
- **Practice:** flip cards and Type it (spell the word from its meaning), both scheduled by spaced repetition.

The page is a single HTML file. It works offline on a computer or a phone and saves progress in the reader’s browser. Your job is to pick the right words, write good meanings and get the pronunciations right. The scripts do the counting, the dictionary lookups and the page building.

Scripts are in `${CLAUDE_SKILL_DIR}/scripts/`. Run them with `python3`, from the folder they’re in or with their full path. The reference files are in `${CLAUDE_SKILL_DIR}/reference/`.

## 0. One-time setup

The scripts need two Python libraries. If a script says one is missing, install both once:

```
python3 -m pip install --target ~/.cache/flashcard-maker/lib pypdf wordfreq
```

## 1. Ask, one question at a time

1. Which PDF, and which chapters? (Skip whatever they already said.)
2. How much do they already know about the subject: total beginner, or some background? This sets how plain the meanings are.
3. British or American spelling?

Then pick a short name for the book (2–3 words, used in the page title) and tell them what you chose.

## 2. Find the chapters and extract their text

```
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_text.py BOOK.pdf --list
```

This prints the PDF’s table of contents with each entry’s page range. Choose the ranges for the chapters asked for. If the PDF has no table of contents, or the ranges look wrong, ask the reader which pages each chapter covers. Then save them into a new project folder next to the PDF, named `flashcards-<short-name>`:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/extract_text.py BOOK.pdf --project DIR --title "Full book title" \
    --chapter 1 "Chapter title" 16 27 --chapter 2 "Chapter title" 28 36
```

If it warns that a chapter has almost no text, the PDF is probably scanned images. Tell the reader this version can’t read those.

## 3. Fill in book.json

Open `DIR/book.json` and set:
- `short`: the short name
- `id`: the short name in lowercase with hyphens (`starfish`, `cell-biology`). It names the page file and keeps this book’s progress separate from other books in the same browser. Don’t change it after the reader starts practising.
- `level`: `"beginner"` or `"some background"`
- `spelling`: `"british"` or `"american"`
- `removed`: leave it empty. It lists words the reader later asks to drop.
- `topics`: 5 to 9 topic labels for this book, as `{"key": "Label"}`. Skim the chapters first. For a biology book they might be `{"body": "Body & skeleton", "cells": "Cells & tissues", "repro": "Reproduction", "eco": "Ecology", "tree": "Evolution & family trees", "names": "Names & groups"}`. The label shows on each card.

## 4. Count candidate words

```
python3 ${CLAUDE_SKILL_DIR}/scripts/candidates.py DIR
```

## 5. Pick the words with one sub-agent per chapter

Start one sub-agent per chapter in a single message, so they run in parallel. Give each this brief, with N and DIR filled in:

> Build the flashcard word list for chapter N of the book in DIR. Read `${CLAUDE_SKILL_DIR}/reference/word-rules.md` and `${CLAUDE_SKILL_DIR}/reference/meanings.md` first and follow them exactly. Your sources are `DIR/text/chN.txt`, `DIR/candidates/chN.json` and `DIR/book.json`. Write your list to `DIR/entries/chN.json`.

Wait for all of them, then go on.

## 6. Merge, trim and get pronunciations

```
python3 ${CLAUDE_SKILL_DIR}/scripts/words.py DIR
```

This merges the chapters, removes duplicates, applies the keep rules from `word-rules.md`, orders each chapter by how often it uses each word, and looks up pronunciations on Wiktionary (only the words are sent). The lookup goes slowly on purpose, so Wiktionary doesn’t block it; a few hundred words take a few minutes.

It lists the words with no dictionary entry in `DIR/pron/missing.json`. Write a guide for each into `DIR/pron/manual.json`, following `${CLAUDE_SKILL_DIR}/reference/pronunciation.md`, then run `words.py DIR --no-lookup` to apply them.

## 7. Check the meanings

Read `DIR/words.json`. For every meaning, check it against the “Plain sentences” table in `meanings.md` (habits such as tacked-on “-ing” clauses and “X, not Y”) and fix any you find, in `DIR/entries/chN.json` (so rebuilds keep the fix). Spot-check at least ten meanings against the chapter text for accuracy. If you changed anything, run `words.py DIR --no-lookup` again.

## 8. Build and open the page

```
python3 ${CLAUDE_SKILL_DIR}/scripts/build.py DIR --artifact
```

It writes `DIR/<id>-flashcards.html` and prints any problems: missing meanings or guides, a clue (the meaning Type it shows) that gives away its word, a script error. Fix every problem and build again.

- If you can publish Claude artifacts, publish `DIR/<id>-flashcards.artifact.html` and give the reader the link.
- Otherwise open `DIR/<id>-flashcards.html` in their browser and tell them where the file is. It works offline, and they can copy it to their phone.

Tell the reader how many words each chapter has, and that guides marked “no dictionary entry” were written from pronunciation rules and are less certain. Mention that they can add or hide words on the Words tab.

## Later requests

- **Add a chapter:** run `extract_text.py` again with the new `--chapter`, then `candidates.py`, one sub-agent for the new chapter only, `words.py`, the missing guides, and `build.py`. Earlier chapters and the reader’s progress stay as they are.
- **Add a word:** append it to the right `entries/chN.json` with `"force": true` and a meaning written from the book, then run `words.py` and `build.py`.
- **Remove a word:** add it to `removed` in `book.json`, then run `words.py --no-lookup` and `build.py`.
- **The reader pastes “Please add these words to my flashcards: …”:** that is the page’s “copy my added words” text. Add each word as above. Use the reader’s meaning only if the book doesn’t explain the word.

Progress is stored in the reader’s browser under each word’s chapter and the word itself, so a rebuilt page picks it up again.

## Keep in mind

- The page never contains the book’s text, only the words, their meanings and guides.
- Meanings must follow the book. Don’t add facts the book doesn’t give.
- Don’t change the page design or add features to it. `${CLAUDE_SKILL_DIR}/template.html` is the design.
