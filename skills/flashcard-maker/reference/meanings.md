# Writing meanings

A meaning appears on the back of a flip card and, in Type it, as the clue the reader spells the word from. It has to be accurate to the book, easy to read, and must not give the word away.

## Follow the book

- When the chapter defines or explains the term, base the meaning on that definition, in plainer words with the same sense.
- When the chapter only uses the term, write a meaning that matches how the chapter uses it.
- Never add a fact, number, name or date the book doesn’t give. If a meaning needs one, leave it out.
- For a genus, species or group, say what the animal or group is and why the book mentions it: “A genus of sand stars that burrow in soft sediment; the chapter uses it to compare modern and ancient mouth skeletons.”

## Write for the reader

- `book.json` `level` is `beginner` or `some background`. For a beginner, use no other jargon in the meaning; if one technical word is unavoidable, explain it in the same sentence. With some background, basic terms of the subject are fine.
- 8 to 30 words. One or two short sentences.
- Use the book’s spelling setting (`british` or `american`) throughout.
- Curly apostrophes and quotes (’ “ ”). No em dashes.

## Don’t give the word away

The meaning must not contain the term or an obvious form of it (“autotomy” must not appear in the meaning of autotomy, nor “autotomise”). The page also hides any leftover 5+ letter part of the word, but a meaning that reads “____ is the act of ____” is a bad clue, so write around it.

## Plain sentences

Meanings are short, so the habits below show up fast. Write the plain version.

| Avoid | Write instead |
|---|---|
| A clause tacked on with *-ing*: “…two plates, alternating with the central pair and often bearing spines.” | Make it its own sentence: “…two plates. They alternate with the central pair and often carry spines.” |
| “X, not Y” or a closing “Not X.”: “Interlocking ridges… Not real teeth.” | State it once: “The ridges are not teeth.” |
| *serves as*, *acts as*, *functions as*: “It acts as a tough tether.” | *is*: “It is a tough tether.” |
| Saying the same thing twice: “The yearly round… which repeats each year.” | “The yearly round in which starfish make, ripen and release eggs and sperm.” |
| A stack of nouns: “arm groove skeletal articulation surfaces” | Unpack it: “the surfaces where the arm-groove plates meet” |
| Dropping *that* in a long clause: “the plates the muscles pull on when the arm bends” | “the plates that the muscles pull on when the arm bends” |
| Adverbs that stand in for evidence: *plainly*, *simply*, *crucially*, *notably* | Cut them, or give the evidence. |
| Significance words: *key*, *crucial*, *vital*, *plays a role in* | Say what it does: “It stores food reserves.” |

Before writing the file, reread each meaning once against this table.

## Roots

Add Greek or Latin roots only where they help the reader remember the word. Format: `part = meaning; part = meaning`, for example `autos = self; tomē = cut`. Leave `roots` empty when the parts don’t help (most names, most everyday-looking words).
