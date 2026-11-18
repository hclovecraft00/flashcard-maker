"""Shared helpers for the Flashcard Maker scripts: the project folder, the extra Python libraries, and text cleaning."""
import json
import os
import re
import sys
from pathlib import Path

# pypdf and wordfreq are installed here once (see SKILL.md), so nothing touches the system Python.
LIB = Path(os.environ.get("FLASHCARD_MAKER_LIB", Path.home() / ".cache" / "flashcard-maker" / "lib"))
if LIB.exists():
    sys.path.insert(0, str(LIB))


def need(module):
    """Import a library, or stop with the command that installs it."""
    try:
        return __import__(module)
    except ImportError:
        sys.exit(f"Missing the Python library '{module}'. Install it with:\n"
                 f"  python3 -m pip install --target {LIB} pypdf wordfreq")


class Project:
    """One book's working folder. Layout:
    book.json            title, id, spelling, reader level, topics, chapters
    text/chN.txt         clean chapter text
    candidates/chN.json  rare words and repeated phrases with counts
    entries/chN.json     the words a sub-agent picked for chapter N
    pron/ipa_cache.json  Wiktionary lookups (word -> phonetic spelling or null)
    pron/manual.json     guides written by Claude for words with no dictionary entry
    words.json           the final list, built by words.py
    """

    def __init__(self, folder):
        self.dir = Path(folder).expanduser().resolve()
        self.book_path = self.dir / "book.json"

    @property
    def book(self):
        if not self.book_path.exists():
            sys.exit(f"No book.json in {self.dir}. Run extract_text.py first.")
        return json.loads(self.book_path.read_text(encoding="utf-8"))

    def save_book(self, book):
        self.dir.mkdir(parents=True, exist_ok=True)
        self.book_path.write_text(json.dumps(book, indent=1, ensure_ascii=False), encoding="utf-8")

    def path(self, *parts):
        p = self.dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def read_json(self, *parts, default=None):
        p = self.dir.joinpath(*parts)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

    def write_json(self, data, *parts):
        self.path(*parts).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")

    def chapters(self):
        return [c["n"] for c in self.book["chapters"]]


# ---------- cleaning text extracted from a PDF ----------

def repeated_lines(pages, min_pages=3):
    """Short lines that recur on many pages: running headers, footers, page furniture."""
    seen = {}
    for page in pages:
        for ln in {re.sub(r"\d+", "#", l.strip()) for l in page.split("\n") if 0 < len(l.strip()) < 70}:
            seen[ln] = seen.get(ln, 0) + 1
    return {ln for ln, n in seen.items() if n >= min_pages}


def clean_text(pages):
    """Join a chapter's pages into one clean string."""
    rep = repeated_lines(pages)
    kept = []
    for page in pages:
        for ln in page.split("\n"):
            if re.sub(r"\d+", "#", ln.strip()) in rep:
                continue
            if re.search(r"(?:\b\w ){5,}", ln):  # letter-spaced lines: "t h a t  i n"
                ln = " ".join(seg.replace(" ", "") for seg in re.split(r" {2,}", ln))
            kept.append(ln)
    t = "\n".join(kept)
    t = t.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff").replace("ﬃ", "ffi").replace("ﬄ", "ffl")
    t = re.sub(r"(\w)-\n([a-z])", r"\1\2", t)       # word split across a line break
    t = re.sub(r"\b(fi|fl|ff)\s+(?=[a-z])", r"\1", t)  # "fi rst", "classifi cation", "diff erent"
    t = re.sub(r"(?<=[a-z])(fi|fl|ff)\s+(?=[a-z])", r"\1", t)
    t = re.sub(r"[ \t]+", " ", t)
    return rejoin_split_words(re.sub(r"\s*\n\s*", " ", t))


JOINED = None  # set to a list to record joins (for testing)


def rejoin_split_words(t):
    """Some PDFs break long words into syllables ("in de pen dent"). Rejoin runs of short pieces
    when the joined word is a common English word and the pieces mostly are not."""
    wf = need("wordfreq")
    toks = t.split(" ")
    out, i = [], 0
    while i < len(toks):
        done = False
        for size in (5, 4, 3, 2):
            run = toks[i:i + size]
            if len(run) < size or not all(re.fullmatch(r"[a-z]{1,8}", w) for w in run):
                continue
            joined, zs = "".join(run), [wf.zipf_frequency(w, "en") for w in run]
            jz = wf.zipf_frequency(joined, "en")
            if (jz >= 3.0 and sum(z >= 4.5 for z in zs) < size and min(zs) < 4.0) or (jz >= 2.5 and min(zs) < 3.0):
                if JOINED is not None: JOINED.append(" ".join(run) + " -> " + joined)
                out.append(joined); i += size; done = True
                break
        if not done:
            out.append(toks[i]); i += 1
    return " ".join(out)


CITE = re.compile(r"\(([^()]*\b(?:1[6-9]|20)\d\d[a-z]?\b[^()]*)\)")


def strip_citations(t):
    """Remove "(Gale 2011a, Blake 1987)" style citations; return the text and the names found in them."""
    names = set()
    for m in CITE.finditer(t):
        names.update(re.findall(r"\b([A-Z][a-zà-ÿ'’\-]+)", m.group(1)))
    for m in re.finditer(r"\b([A-Z][a-zà-ÿ'’\-]+)(?:\s+(?:and|&)\s+[A-Z][a-zà-ÿ'’\-]+|\s+et al\.)?\s*\(\s*(?:1[6-9]|20)\d\d", t):
        names.add(m.group(1))
    return CITE.sub(" ", t), names


def norm(s):
    """Compare spellings ignoring case, accents and hyphens."""
    import unicodedata
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("-", " "))).strip()
