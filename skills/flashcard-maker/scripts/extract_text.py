"""Find a PDF's chapters and save their clean text into a project folder.

  List the table of contents, with each entry's first and last page:
    python3 extract_text.py BOOK.pdf --list

  Save chapters (repeat --chapter; pages are PDF page numbers, first page = 1):
    python3 extract_text.py BOOK.pdf --project DIR --title "Book title" \
        --chapter 1 "Chapter title" 16 27 --chapter 2 "Another chapter" 28 36

Running it again adds chapters and keeps the ones already saved.
"""
import argparse
import re
import sys

from _lib import Project, clean_text, need


def outline(reader):
    rows = []

    def walk(items, depth):
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1)
                continue
            try:
                rows.append((depth, it.title.strip(), reader.get_destination_page_number(it) + 1))
            except Exception:
                pass
    walk(reader.outline, 0)
    rows.sort(key=lambda r: r[2])
    out = []
    for i, (d, title, start) in enumerate(rows):
        nxt = next((r[2] for r in rows[i + 1:] if r[2] > start), len(reader.pages) + 1)
        out.append((d, title, start, nxt - 1))
    return out


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "book"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--list", action="store_true", help="print the table of contents and stop")
    ap.add_argument("--project", help="the book's project folder")
    ap.add_argument("--title", help="the book's title (first run only)")
    ap.add_argument("--chapter", nargs=4, action="append", metavar=("N", "TITLE", "FIRST", "LAST"), default=[])
    a = ap.parse_args()

    pypdf = need("pypdf")
    reader = pypdf.PdfReader(a.pdf)
    if a.list:
        rows = outline(reader)
        if not rows:
            print(f"This PDF has no table of contents in its bookmarks ({len(reader.pages)} pages). "
                  "Ask the reader which pages each chapter covers.")
        for d, title, s, e in rows:
            print(f"{'  ' * d}{title}  [pages {s}-{e}]")
        return

    if not a.project or not a.chapter:
        sys.exit("Give --project and at least one --chapter (or use --list).")
    p = Project(a.project)
    book = p.book if p.book_path.exists() else {
        "id": slug(a.title or a.pdf.split("/")[-1]), "title": a.title or "", "pdf": a.pdf,
        "spelling": "british", "level": "beginner", "topics": {}, "chapters": [], "removed": [],
        "contents": [t for d, t, s, e in outline(reader)]}
    have = {c["n"]: c for c in book["chapters"]}
    for n, title, first, last in a.chapter:
        n, first, last = int(n), int(first), int(last)
        if not (1 <= first <= last <= len(reader.pages)):
            sys.exit(f"Chapter {n}: pages {first}-{last} are outside 1-{len(reader.pages)}.")
        pages = [reader.pages[i].extract_text() or "" for i in range(first - 1, last)]
        text = clean_text(pages)
        if len(text.split()) < 200:
            print(f"Warning: chapter {n} has only {len(text.split())} words of text. "
                  "The PDF may be scanned images, which this skill can't read.")
        p.path("text", f"ch{n}.txt").write_text(text, encoding="utf-8")
        have[n] = {"n": n, "title": title, "pages": [first, last]}
        print(f"chapter {n}: {title} (pages {first}-{last}, {len(text.split())} words)")
    book["chapters"] = [have[k] for k in sorted(have)]
    book["pdf"] = a.pdf
    p.save_book(book)
    print(f"saved to {p.dir}")


if __name__ == "__main__":
    main()
