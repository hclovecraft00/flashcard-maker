"""Pronunciation guides: look words up on Wiktionary and turn the phonetic spelling (IPA) into an
easy guide with the stressed syllable in capitals, e.g. autotomy -> "aw-TOT-uh-mee".

Only the words themselves are sent to Wiktionary. Results are cached in the project, so each word
is looked up once.

    python3 pron.py "ˈɒsɪkəl" ossicle      (convert one phonetic spelling, for testing)
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "flashcard-maker-pronunciation-lookup/1.0 (https://github.com/hclovecraft00/flashcard-maker)"


def fetch(titles):
    """Return {title: wikitext} for up to 20 titles, following redirects; keys are the titles as asked."""
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
                                "format": "json", "redirects": 1, "titles": "|".join(titles)})
    req = urllib.request.Request("https://en.wiktionary.org/w/api.php?" + q, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            d = json.load(urllib.request.urlopen(req, timeout=30))["query"]
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(int(e.headers.get("Retry-After", 0) or 0) or 15 * (attempt + 1))
    back = {}
    for m in d.get("normalized", []) + d.get("redirects", []):
        back[m["to"]] = back.get(m["from"], m["from"])
    return {back.get(p["title"], p["title"]): p["revisions"][0]["slots"]["main"]["*"]
            for p in d["pages"].values() if "revisions" in p}


def english_ipa(wikitext, prefer="UK"):
    """Pick an English IPA from the English section: the preferred accent if listed, else the first."""
    sec = wikitext.split("==English==", 1)
    if len(sec) < 2:
        return None
    eng = re.split(r"\n==[^=]", sec[1])[0]
    want = r"UK|RP|GB" if prefer == "UK" else r"US|GA|General American"
    best = None
    for m in re.finditer(r"\{\{IPA\|en\|([^}]*)\}\}", eng):
        parts = m.group(1).split("|")
        ipas = [p for p in parts if p.startswith("/") or p.startswith("[")]
        acc = " ".join(p for p in parts if p.startswith("a="))
        if not ipas:
            continue
        if re.search(want, acc):
            return ipas[0].strip("/[]")
        best = best or ipas[0].strip("/[]")
    return best


def lookup(words, cache, prefer="UK", save=None, pause=3):
    """Fill cache {word: ipa or None} for any words not yet looked up. Calls save(cache) after each batch."""
    todo = sorted({x for w in words for x in (w, w.lower()) if len(w) > 1} - set(cache))
    for i in range(0, len(todo), 20):
        batch = todo[i:i + 20]
        try:
            got = fetch(batch)
        except Exception as e:  # offline or Wiktionary unavailable: leave these for the rules
            print(f"Wiktionary lookup failed ({e}); remaining words will need guides written by hand.")
            return cache
        for t in batch:
            cache[t] = english_ipa(got[t], prefer) if t in got else None
        if save:
            save(cache)
        time.sleep(pause)
    return cache


def guide_for(term, alts, cache):
    """A guide from the cache: the word's own entry; or, for a plural or spelling variant, a related form's."""
    def own(t):
        return cache.get(t) or cache.get(t.lower())

    def one(form, others):
        x = own(form)
        if x:
            return respell(x, form)
        for a in others:
            y = own(a)
            if not y:
                continue
            f, b = form.lower(), a.lower()
            if f in (b + "s", b + "es"):
                r = re.sub(r"i([^aeiouy\-]+)e$", r"y\1", respell(y, a))
                return r + ("s" if re.search(r"(p|t|k|f|th)$", r.lower()) else "z")
            if f.endswith("ae") and f[:-1] == b:
                return re.sub(r"(?i)uh$", "ee", respell(y, a))
            if f.replace("ae", "e").replace("oe", "e") == b.replace("ae", "e").replace("oe", "e"):
                return respell(y, a)
        return None

    r = one(term, alts)
    if not r and " " in term:
        parts = [one(p, []) for p in term.split()]
        r = " ".join(parts) if all(parts) else None
    return r


# ---------- IPA -> easy guide ----------

VOWELS = ["aɪə", "aʊə", "eɪ", "aɪ", "ɔɪ", "aʊ", "əʊ", "oʊ", "ɪə", "eə", "ɛə", "ʊə", "iː", "uː", "ɑː", "ɔː", "ɜː", "ɝ", "ɚ",
          "i", "ɪ", "e", "ɛ", "æ", "a", "ɑ", "ɒ", "ɔ", "ʌ", "ʊ", "u", "ə", "ɐ", "o", "ɘ", "ᵻ", "ɵ", "ɨ"]
CONS = {"t͡ʃ": "ch", "tʃ": "ch", "d͡ʒ": "j", "dʒ": "j", "θ": "th", "ð": "th", "ʃ": "sh", "ʒ": "zh", "ŋ": "ng", "j": "y",
        "ɹ": "r", "r": "r", "ɫ": "l", "ɾ": "t", "ʍ": "w", "ɻ": "r", "ɡ": "g", "g": "g", "x": "kh", "ʔ": "",
        "l̩": "ul", "n̩": "un", "m̩": "um"}
for c in "pbtdkfvszhmnlw":
    CONS.setdefault(c, c)
OPEN = {"aɪə": "yuh", "aʊə": "owuh", "eɪ": "ay", "aɪ": "y", "ɔɪ": "oy", "aʊ": "ow", "əʊ": "oh", "oʊ": "oh", "ɪə": "eer",
        "eə": "air", "ɛə": "air", "ʊə": "oor", "iː": "ee", "uː": "oo", "ɑː": "ah", "ɔː": "aw", "ɜː": "er", "ɝ": "er", "ɚ": "er",
        "i": "ee", "ɪ": "ih", "e": "eh", "ɛ": "eh", "æ": "a", "a": "a", "ɑ": "ah", "ɒ": "o", "ɔ": "aw", "ʌ": "uh", "ʊ": "uu",
        "u": "oo", "ə": "uh", "ɐ": "uh", "o": "oh", "ɘ": "uh", "ᵻ": "ih", "ɵ": "oh", "ɨ": "ih"}
CLOSED = dict(OPEN, **{"ɪ": "i", "e": "e", "ɛ": "e", "ʌ": "u", "ʊ": "u", "ə": "u", "ɐ": "u", "ᵻ": "i", "ɨ": "i", "ɘ": "u"})
ONSETS = {"pr", "br", "tr", "dr", "kr", "gr", "fr", "thr", "shr", "pl", "bl", "kl", "gl", "fl", "sl", "sp", "st", "sk", "sm",
          "sn", "sw", "tw", "kw", "dw", "py", "by", "ky", "gy", "my", "ny", "fy", "vy", "hy", "spr", "str", "skr", "spl", "skw", "sky"}
SHORT = {"æ", "ɒ", "ɛ", "e", "ʌ", "ʊ"}


def tokens(ipa):
    for junk in ("(", ")", "ˑ", "̯", "‿"):
        ipa = ipa.replace(junk, "")
    # newer British symbols, and three-vowel runs split into syllables
    for a, b in (("ʌɪ", "aɪ"), ("ɑɪ", "aɪ"), ("ʌʊ", "aʊ"), ("ɛː", "ɛə"), ("ɜ", "ɜː"), ("ɜːː", "ɜː"), ("ɒː", "ɔː"),
                 ("aɪə", "aɪ.ə"), ("aʊə", "aʊ.ə")):
        ipa = ipa.replace(a, b)
    out, i = [], 0
    keys = sorted(set(VOWELS) | set(CONS) | {"ˈ", "ˌ", ".", " "}, key=len, reverse=True)
    while i < len(ipa):
        for k in keys:
            if ipa.startswith(k, i):
                out.append(k)
                i += len(k)
                break
        else:
            i += 1  # an unknown diacritic
    return out


def respell(ipa, word=""):
    """Turn one IPA string into an easy guide. `word` is the written word; it helps with r-sounds
    that British IPA leaves out ("mor-FOL-uh-jee", not "maw-FOL-uh-jee")."""
    word = (word or "").lower()
    toks = [t for t in tokens(ipa) if t != " "]
    sylls, stress, cur, mark = [], [], [], None
    for t in toks:  # explicit syllable marks first
        if t in ("ˈ", "ˌ", "."):
            if cur:
                sylls.append(cur); stress.append(mark)
            cur, mark = [], ("p" if t == "ˈ" else ("s" if t == "ˌ" else None))
            continue
        cur.append(t)
    if cur:
        sylls.append(cur); stress.append(mark)
    final = []
    for s, m in zip(sylls, stress):  # then split between vowels, giving the next syllable the longest natural onset
        vidx = [i for i, t in enumerate(s) if t in VOWELS or t in ("l̩", "n̩", "m̩")]
        if len(vidx) <= 1:
            final.append((s, m)); continue
        start = 0
        for a, b in zip(vidx, vidx[1:]):
            gap, cluster, k = b - a - 1, s[a + 1:b], (1 if b - a - 1 >= 1 else 0)
            for size in (3, 2):
                if gap >= size and "".join(CONS.get(t, t) for t in cluster[-size:]) in ONSETS:
                    k = size; break
            final.append((s[start:b - k], m if start == 0 else None))
            start = b - k
        final.append((s[start:], None))
    final = [(list(a), b) for a, b in final]
    for i in range(len(final) - 1):  # a short vowel keeps the next consonant: "OS-ih-kul", not "O-sih-kul"
        cur, m = final[i]
        nxt = final[i + 1][0]
        yoo = cur and cur[-1] == "ʊ" and len(cur) > 1 and cur[-2] == "j"
        if cur and nxt and not yoo and (cur[-1] in SHORT or (cur[-1] == "ɪ" and m == "p")) and nxt[0] not in VOWELS and len(nxt) > 1:
            cur.append(nxt.pop(0))
    parts = []
    for idx, (s, m) in enumerate(final):
        vi = next((i for i, t in enumerate(s) if t in VOWELS), None)
        onset = "".join(CONS.get(t, t) for t in (s[:vi] if vi is not None else s))
        if vi is None:
            parts.append((onset, m)); continue
        v, coda = s[vi], "".join(CONS.get(t, t) for t in s[vi + 1:])
        if v in ("aɪ", "aɪə") and coda:
            syl = onset + ("i" + coda + "e" if len(coda) == 1 or coda in ("th", "sh", "ch") else "y" + coda)
        else:
            nuc = (CLOSED if coda else OPEN)[v]
            if v == "ɪə" and not re.search(r"(ear|eer|ier|ere|eri|eir)", word):
                nuc = "ee-u" if coda else "ee-uh"
            if v == "ʊ" and onset.endswith("y"):
                nuc = "oo"
            elif v == "ʊ" and "oo" in word:
                nuc = "uu"
            if v in ("ɪ", "i") and not coda and idx == len(final) - 1:
                nuc = "ee"
            if v in ("ɔː", "ɔ") and "or" in word:
                nuc = "or"
            if v in ("ɑː", "ɑ") and "ar" in word:
                nuc = "ar"
            if not onset and v == "aɪ":
                nuc = "eye"
            if v == "ə" and not coda and idx == len(final) - 1 and re.search(r"(er|or|ar|ure|our)s?$", word):
                nuc = "er"
            syl = onset + nuc + coda
        parts.append((re.sub(r"(er|ar|or|air|eer|oor)r", r"\1", syl), m))
    out = "-".join(p.upper() if m == "p" else p for p, m in parts if p)
    return re.sub(r"(?i)(air|eer|oor|er|or|ar)-r(?=[aeiouy])", lambda m: m.group(1) + "-", out)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        print(respell(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""))
    else:
        for w, ipa in [("ossicle", "ˈɒsɪkəl"), ("phylogeny", "faɪˈlɒd͡ʒəni"), ("autotomy", "ɔːˈtɒtəmi"),
                       ("madreporite", "ˌmæd.ɹəˈpɔɹ.aɪt"), ("diaphragm", "ˈdʌɪəfɹam"), ("footprint", "ˈfʊtpɹɪnt")]:
            print(w.ljust(12), respell(ipa, w))
