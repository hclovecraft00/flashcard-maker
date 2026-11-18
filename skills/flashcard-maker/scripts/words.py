"""Merge the sub-agents' word lists into the final list, apply the keep rules, order the words,
and look up pronunciations. Writes words.json and pron/missing.json.

    python3 words.py DIR

Keep rules (see reference/word-rules.md):
  - a concept stays if its chapter uses it 3+ times, or the book explains it ("defined_in_book")
  - a name (genus, species, group) stays if used 4+ times, or the book features it ("featured")
  - "force": true keeps a word regardless (words the reader asked for)
  - words listed in book.json "removed" are dropped
  - a word belongs to the first chapter it appears in; within a chapter, most used first
"""
import argparse
import re

from _lib import Project, need, norm
from pron import guide_for, lookup

TOPIC_FALLBACK = "other"


def uses(entry, text):
    forms = {entry["term"], *entry.get("alt", [])}
    for f in list(forms):
        parts = f.split()
        if len(parts) == 2 and parts[0][:1].isupper():  # species: also count "A. rubens"
            forms.add(f"{parts[0][0]}. {parts[1]}")
    n = 0
    for f in forms:
        pat = r"(?<![A-Za-z])" + re.escape(f).replace(r"\ ", r"[\s-]+") + r"(?![a-z])"
        n += len(re.findall(pat, text, flags=0 if f[:1].isupper() and " " in f else re.I))
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--no-lookup", action="store_true", help="skip Wiktionary (offline)")
    a = ap.parse_args()
    zf = need("wordfreq").zipf_frequency
    p = Project(a.project)
    book = p.book
    topics = set(book.get("topics", {})) or None
    removed = {norm(r) for r in book.get("removed", [])}

    words, seen, dropped = [], set(), {"duplicate": 0, "rare in chapter": 0, "removed by reader": 0}
    for n in p.chapters():
        entries = p.read_json("entries", f"ch{n}.json")
        if entries is None:
            print(f"chapter {n}: no entries/ch{n}.json yet, skipped")
            continue
        text_file = p.dir / "text" / f"ch{n}.nocite.txt"
        text = (text_file if text_file.exists() else p.dir / "text" / f"ch{n}.txt").read_text(encoding="utf-8")
        for e in entries:
            keys = {norm(e["term"])} | {norm(x) for x in e.get("alt", [])}
            if keys & seen:
                dropped["duplicate"] += 1
                continue
            if keys & removed:
                dropped["removed by reader"] += 1
                continue
            e["ch"], e["uses"] = n, uses(e, text)
            is_name = e.get("kind") == "name"
            keep = e.get("force") or (e.get("featured") or e["uses"] >= 4 if is_name else e.get("defined_in_book") or e["uses"] >= 3)
            if not keep:
                dropped["rare in chapter"] += 1
                continue
            if topics and e.get("topic") not in topics:
                e["topic"] = TOPIC_FALLBACK
            seen |= keys
            words.append(e)
    words.sort(key=lambda w: (w["ch"], -w["uses"]))

    cache = p.read_json("pron", "ipa_cache.json", default={})
    if not a.no_lookup:
        forms = [f for w in words for f in [w["term"], *w["term"].split(), *w.get("alt", [])]]
        prefer = "US" if book.get("spelling") == "american" else "UK"
        lookup(forms, cache, prefer, save=lambda c: p.write_json(c, "pron", "ipa_cache.json"))
        p.write_json(cache, "pron", "ipa_cache.json")
    manual = p.read_json("pron", "manual.json", default={})
    missing = []
    for w in words:
        g = guide_for(w["term"], w.get("alt", []), cache)
        if w["term"] in manual:
            w["pron"], w["pron_src"] = manual[w["term"]], "rules"
        elif g:
            w["pron"], w["pron_src"] = g, "dictionary"
        else:
            w["pron"], w["pron_src"] = "", "missing"
            missing.append(w["term"])
        w["say_word"] = min(zf(x.lower(), "en") for x in re.findall(r"[A-Za-z]+", w["term"]) or ["x"]) >= 3.0
    p.write_json(words, "words.json")
    p.write_json(missing, "pron", "missing.json")

    per = {}
    for w in words:
        per[w["ch"]] = per.get(w["ch"], 0) + 1
    print(f"kept {len(words)} words {per}; dropped {dropped}")
    print(f"pronunciations: {sum(w['pron_src'] == 'dictionary' for w in words)} from the dictionary, "
          f"{sum(w['pron_src'] == 'rules' for w in words)} written by hand, {len(missing)} still needed"
          + (" (listed in pron/missing.json)" if missing else ""))


if __name__ == "__main__":
    main()
