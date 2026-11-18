"""Build the flashcard page from words.json and the template, then check it.

    python3 build.py DIR                  writes DIR/<book id>-flashcards.html, a full page that opens in any browser
    python3 build.py DIR --artifact       also writes DIR/<book id>-flashcards.artifact.html, the body-only version
                                          for publishing as a Claude artifact (artifacts supply their own <head>)

Checks run every time: every word has a meaning; every word has a pronunciation guide (or the build
says which don't); no Type it clue gives away its answer; the page script parses (when Node is installed).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from _lib import Project

TEMPLATE = Path(__file__).resolve().parent.parent / "template.html"
FULL_HEAD = ('<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
             '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
             '<style>[hidden] {{ display: none !important; }} body {{ margin: 0; }}</style>\n</head>\n<body>\n')


def mask(meaning, term, alts):
    """Same rule as the page: hide any 5+ letter part of the word (and its endings) inside its own meaning."""
    out = meaning
    for form in [term, *alts]:
        for part in re.findall(r"[A-Za-z]{5,}", form):
            out = re.sub(r"(?i)\b" + re.escape(part[:-1]) + r"\w*", "____", out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--artifact", action="store_true")
    a = ap.parse_args()
    p = Project(a.project)
    book = p.book
    words = p.read_json("words.json")
    if not words:
        sys.exit("No words.json yet. Run words.py first.")

    problems = []
    no_meaning = [w["term"] for w in words if not w.get("meaning", "").strip()]
    if no_meaning:
        problems.append(f"{len(no_meaning)} words have no meaning: {', '.join(no_meaning[:10])}")
    no_pron = [w["term"] for w in words if not w.get("pron")]
    leaks = []
    for w in words:
        clue = re.sub(r"<[^>]+>", "", mask(w["meaning"], re.sub(r"<[^>]+>", "", w["term"]), w.get("alt", [])))
        for part in re.findall(r"[A-Za-z]{5,}", re.sub(r"<[^>]+>", "", w["term"])):
            if part.lower() in clue.lower():
                leaks.append(w["term"])
                break

    data = {
        "id": book["id"], "title": book.get("title", ""), "short": book.get("short", ""),
        "spelling": book.get("spelling", "british"),
        "chapters": [{"n": c["n"], "title": c["title"]} for c in book["chapters"] if any(w["ch"] == c["n"] for w in words)],
        "topics": book.get("topics", {}),
        "words": [[w["ch"], w.get("topic", "other"), w["term"], w.get("roots", ""), w["meaning"], w.get("pron", ""),
                   w.get("pron_src", ""), w.get("alt", []), bool(w.get("say_word"))] for w in words],
    }
    tpl = TEMPLATE.read_text(encoding="utf-8")
    title = f"{book.get('short') or book.get('title') or 'My'} Flashcards"
    body = re.sub(r"/\*BOOK\*/.*?/\*END\*/", lambda m: json.dumps(data, ensure_ascii=False).replace("</", "<\\/"), tpl, count=1, flags=re.S)
    body = body.replace("{{TITLE}}", title.replace("&", "&amp;").replace("<", "&lt;"))
    lang = "en-US" if data["spelling"] == "american" else "en-GB"
    full = FULL_HEAD.format(lang=lang) + body + "\n</body>\n</html>\n"

    out = p.dir / f"{book['id']}-flashcards.html"
    out.write_text(full, encoding="utf-8")
    if a.artifact:
        (p.dir / f"{book['id']}-flashcards.artifact.html").write_text(body, encoding="utf-8")

    node = shutil.which("node")
    if node:
        script = re.findall(r"<script>(.*?)</script>", body, re.S)[-1]
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(script)
        r = subprocess.run([node, "--check", f.name], capture_output=True, text=True)
        if r.returncode:
            problems.append("the page script has a syntax error:\n" + r.stderr[-800:])

    per = {}
    for w in words:
        per[w["ch"]] = per.get(w["ch"], 0) + 1
    print(f"built {out} ({len(words)} words: " + ", ".join(f"ch {k}: {v}" for k, v in sorted(per.items())) + ")")
    print(f"pronunciation guides: {len(words) - len(no_pron)} of {len(words)}"
          + (f"; missing for {', '.join(no_pron[:12])}{' …' if len(no_pron) > 12 else ''}" if no_pron else ""))
    if leaks:
        problems.append(f"{len(leaks)} clues still contain their word; reword these meanings: {', '.join(leaks[:12])}")
    if not node:
        print("Node isn't installed, so the script syntax check was skipped.")
    for x in problems:
        print("PROBLEM:", x)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
