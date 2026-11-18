"""Count candidate words in each chapter: words that are rare in everyday English, and repeated
two-word phrases. Writes candidates/chN.json for every chapter that doesn't have one yet.

    python3 candidates.py DIR            (add --force to redo every chapter)
"""
import argparse
import collections
import re

from _lib import Project, need, strip_citations

STOP = set("""the a an of and or in on to for with by from as at is are was were be been being that this these those which
its it their than into not but also may can has have had such other most more some any each both all only very""".split())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    zf = need("wordfreq").zipf_frequency
    p = Project(a.project)
    for n in p.chapters():
        out = p.dir / "candidates" / f"ch{n}.json"
        if out.exists() and not a.force:
            continue
        text, names = strip_citations((p.dir / "text" / f"ch{n}.txt").read_text(encoding="utf-8"))
        p.path("text", f"ch{n}.nocite.txt").write_text(text, encoding="utf-8")
        toks = re.findall(r"[A-Za-z][A-Za-z\-]*[A-Za-z]", text)
        groups = collections.defaultdict(collections.Counter)
        for w in toks:
            key = w.lower()
            if len(key) > 4:
                key = re.sub(r"(ae|es|s)$", "", key)
            groups[key][w] += 1
        words = []
        for ctr in groups.values():
            shown = ctr.most_common(1)[0][0]
            rarity = min(zf(w.lower(), "en") for w in ctr)
            if rarity >= 3.6 or shown in names or shown.lower() in STOP:
                continue
            words.append({"term": shown, "forms": sorted(ctr), "count": sum(ctr.values()), "zipf": round(rarity, 2)})
        low = [w.lower() for w in toks]
        pairs = collections.Counter(zip(low, low[1:]))
        phrases = [{"term": f"{x} {y}", "count": c} for (x, y), c in pairs.items()
                   if c >= 3 and x not in STOP and y not in STOP and (zf(x, "en") < 4.5 or zf(y, "en") < 4.5)]
        words.sort(key=lambda w: -w["count"])
        phrases.sort(key=lambda w: -w["count"])
        p.write_json({"words": words, "phrases": phrases, "author_names_removed": sorted(names)}, "candidates", f"ch{n}.json")
        print(f"chapter {n}: {len(words)} rare words ({sum(w['count'] >= 2 for w in words)} used 2+ times), "
              f"{len(phrases)} repeated phrases, {len(names)} author names removed")


if __name__ == "__main__":
    main()
