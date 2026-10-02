#!/usr/bin/env python3
"""Compare a revision with what the author gave you and list the specifics that changed.

    python3 tools/check_facts.py original.md revised.md [--source=notes.md ...] [--fail-on=MODE]
                                 [--profile=FILE] [--format=json]

A specific is a number with its unit and rate ("20 minutes", "$250 a year", "47%"), a frequency ("once a day",
"twice a week", "every Tuesday", "weekly"), a time or numeric date, a month or weekday, a name, an acronym, a
quotation of three or more words, a URL, a vague amount ("half", "most banks") or an unnamed authority ("studies
show", "experts say"). Number words count: "twenty minutes" and "20 minutes" are the same figure, and "daily",
"every day" and "once a day" are the same frequency. Each specific is counted, so one cut from a sentence is reported
even when the same figure survives elsewhere.

added:     in the revision but not in the original or any --source file. A fact the revision introduced: cut it,
           or confirm it with the author. A count or sum you worked out from the original is fine; say so.
dropped:   in the original but not in the revision, or there fewer times. Check that the cut was meant.
repeated:  in the revision more times than in the original. The fact is not new, so this never fails the run; it is
           there for a restatement you did not mean.
unchecked: a capitalized word that starts a sentence in the revision and appears nowhere in the original. It may be
           a new name ("Smith saw the pattern") or an ordinary word; a script cannot tell, so read each one.

--fail-on sets what fails the run: added (the default), added_or_dropped, or anything_unchecked. Without the flag
the profile's fact_check_fail_on decides, found the way the linter finds it (--profile, $SPEAKHUMAN_PROFILE, the
working directory, ~/.config/speakhuman, the skill folder).

Exit codes: 0 when nothing fails under that setting, 1 when something does, 2 on a usage error. The check reads
specifics only. A claim, a cause, a direction ("rose" to "fell"), a degree of certainty or who did what that
changed still needs a reader. Headings are read for numbers and acronyms only, because Title Case makes every word
look like a name.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.dont_write_bytecode = True
import speakhuman_lint as sl  # noqa: E402

MAX_BYTES = 2_000_000
FAIL_MODES = ("added", "added_or_dropped", "anything_unchecked")
ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen").split()
TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()
WORDS = {w: i for i, w in enumerate(ONES)}
WORDS.update({w: 10 * (i + 2) for i, w in enumerate(TENS)})
WORDS.update({"dozen": 12, "hundred": 100, "thousand": 1000})
# "one" and "zero" read as ordinary words ("one reason", "no one"), so only the other number words are checked.
QUIET_WORDS = {"zero", "one"}
SCALE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mm": 1e6, "million": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9,
         "t": 1e12, "trillion": 1e12}
UNITS = {"second": "second", "sec": "second", "minute": "minute", "min": "minute", "hour": "hour", "hr": "hour",
         "day": "day", "week": "week", "wk": "week", "month": "month", "mo": "month", "quarter": "quarter",
         "year": "year", "yr": "year", "decade": "decade", "mile": "mile", "km": "km", "kilometer": "km",
         "meter": "meter", "foot": "foot", "feet": "foot", "inch": "inch", "inche": "inch", "pound": "pound",
         "lb": "pound", "kg": "kg", "kilogram": "kg", "gram": "gram", "ounce": "ounce", "oz": "ounce",
         "liter": "liter", "litre": "liter", "gallon": "gallon", "dollar": "dollar", "cent": "cent", "euro": "euro"}
RATES = {"second": "second", "minute": "minute", "hour": "hour", "hr": "hour", "day": "day", "week": "week",
         "month": "month", "mo": "month", "quarter": "quarter", "year": "year", "yr": "year", "annually": "year",
         "yearly": "year", "monthly": "month", "weekly": "week", "daily": "day", "hourly": "hour"}
CAL = ("January February March April May June July August September October November December "
       "Monday Tuesday Wednesday Thursday Friday Saturday Sunday").split()
COMMON_ACRONYMS = {"AI", "OK", "FAQ", "PDF", "URL", "API", "CEO", "CFO", "CTO", "CMO", "COO", "HR", "IT", "PR",
                   "UI", "UX", "ID", "TV", "AM", "PM", "ETA", "FYI", "ASAP", "TBD", "PS"}
TITLES = {"Mr.", "Mrs.", "Ms.", "Dr.", "St.", "Jr.", "Sr.", "Inc.", "Co.", "Corp.", "Ltd.", "Mt.", "Ft."}
# Sentence openers that are ordinary words, so a new one is not reported as unchecked.
STARTERS = set("""a an the this that these those it its we our you your they their he his she her i my me us them
there here what which who whom whose why how when where while if then than so but and or nor yet for because since
although though after before once until unless as at by from in into of on onto over under with within without
about above across against along among around behind below beneath beside between beyond during except inside
near off out outside past through throughout toward towards upon each every all both either neither some any most
many much few several no not none one two three four five six seven eight nine ten first second third next last
finally also still instead however meanwhile otherwise therefore thus later now today tomorrow yesterday soon
often sometimes usually always never only just even again already perhaps maybe yes please let use check try
click add remove open close save send read see note keep make take give get put set run call ask tell find look
start stop go come do does did is are was were be been has have had will would can could should shall may might
must""".split())
WORD_NUM = r"(?:%s)(?:[- ](?:%s))?" % ("|".join(TENS + ONES[::-1] + ["dozen", "hundred", "thousand"]), "|".join(ONES[1:10]))
_RATE_ALT = "|".join(sorted(RATES, key=len, reverse=True))
NUM_RE = re.compile(
    r"(?:(?<![\w.])(?<![A-Za-z]-)(?P<cur>[$\u00a3\u20ac])?(?P<n>\d[\d,]*(?:\.\d+)?|\.\d+)(?:st|nd|rd|th)?"
    r"(?:\s?(?P<scale>k|mm|m|bn|b|t|thousand|million|billion|trillion)\b)?"
    r"(?:\s?(?P<pct>%|percent\b|per cent\b|percentage points?\b|pp\b|basis points?\b|bps\b))?"
    r"|\b(?P<w>" + WORD_NUM + r")\b(?:\s(?P<wscale>thousand|million|billion|trillion)\b)?"
    r"(?:\s(?P<wpct>percent|per cent)\b)?)"
    r"(?:[\s-](?P<unit>" + "|".join(sorted(UNITS, key=len, reverse=True)) + r")s?\b)?"
    r"(?:\s(?:a|an|per|each)\s(?P<rate>" + _RATE_ALT + r")\b"
    r"|/(?P<rate2>" + _RATE_ALT + r")\b"
    r"|\s(?P<rate3>annually|yearly|monthly|weekly|daily|hourly)\b)?",
    re.I)
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b|\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b")
URL_RE = re.compile(r"https?://[^\s)>\]\"']+")
QUOTE_RE = re.compile("[\"\u201c]([^\"\u201c\u201d\n]{3,300}?)[\"\u201d]")
CAP = r"[A-Z][\w'&.-]*"
NAME_RE = re.compile(r"%s(?:\s+(?:of|and|for|de|&)\s+%s|\s+%s)*" % (CAP, CAP, CAP))
ACRO_RE = re.compile(r"\b[A-Z][A-Z0-9&]{1,9}s?\b")
VAGUE_RE = re.compile(r"\b(?:half|a third|a quarter|two thirds|three quarters|(?:the |a )?(?:vast )?majority|"
                      r"a minority|nearly all|almost all|most (?:of )?(?:the |our |their |your )?[a-z]+s)\b", re.I)
ARTICLES = ("The", "A", "An", "In", "At", "On", "For", "By", "From", "And", "But")
_PERIODS = "hour|day|week|month|quarter|year"
FREQ_RE = re.compile(
    r"\b(?:(?P<n>once|twice|thrice|(?:\d+|" + "|".join(ONES[2:]) + r") times) (?:a|an|per|each) (?P<u>" + _PERIODS + r")"
    r"|every (?P<other>other )?(?P<eu>" + _PERIODS + r"|morning|afternoon|evening|night|weekday|weekend|monday|tuesday|"
    r"wednesday|thursday|friday|saturday|sunday)"
    r"|(?P<ly>hourly|daily|nightly|weekly|biweekly|monthly|quarterly|annually|yearly))\b", re.I)
FREQ_COUNT = {"once": 1, "twice": 2, "thrice": 3}
FREQ_LY = {"hourly": "1/hour", "daily": "1/day", "nightly": "1/night", "weekly": "1/week", "biweekly": "biweekly",
           "monthly": "1/month", "quarterly": "1/quarter", "annually": "1/year", "yearly": "1/year"}


def freq_key(m):
    """'once a day', 'daily' and 'every day' share one key: freq:1/day."""
    if m.group("ly"):
        return "freq:" + FREQ_LY[m.group("ly").lower()]
    if m.group("eu"):
        return "freq:%s/%s" % ("0.5" if m.group("other") else "1", m.group("eu").lower())
    n = m.group("n").lower()
    count = FREQ_COUNT.get(n) or (int(n.split()[0]) if n.split()[0].isdigit() else WORDS[n.split()[0]])
    return "freq:%s/%s" % (count, m.group("u").lower())


def overlaps(m, spans):
    return any(a < m.end() and m.start() < b for a, b in spans)


def authority_patterns():
    """The unnamed-authority patterns of the linter's weasel-attribution rule, so both tools agree."""
    data = json.load(open(sl.RULES_PATH, encoding="utf-8"))
    rule = next((r for r in data["rules"] if r["id"] == "weasel-attribution"), {})
    return [re.compile(x if isinstance(x, str) else x["re"], re.I) for x in rule.get("regexes") or []]


AUTH_RES = authority_patterns()


def unit(pct):
    p = (pct or "").lower()
    if not p:
        return ""
    if p.startswith(("percentage", "pp")):
        return " pp"
    if p.startswith(("basis", "bps")):
        return " bps"
    return "%"


def word_value(w):
    total = 0
    for part in re.split(r"[- ]", w.lower()):
        v = WORDS[part]
        total = total * v if v in (100, 1000) and total else total + v
    return total


def strip_noise(text):
    """Drop code, comments, list numbers and footnote markers, which are not claims. Line numbers stay put."""
    keep_lines = lambda m: "\n" * m.group().count("\n")  # noqa: E731
    text = re.sub(r"```.*?```|~~~.*?~~~", keep_lines, text, flags=re.S)
    text = re.sub(r"<!--.*?-->", keep_lines, text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"\[\^[^\]]*\]", " ", text)
    return re.sub(r"(?m)^(\s*)(?:\d+[.)]|[-*+>]|#+)\s+", r"\1", text)


def sentence_starts(line):
    return {m.end() for m in re.finditer(r"(?:^|[.!?:;]\s+|[(\"\u201c]\s*)(?=[A-Z])", line)}


def name_segments(text):
    """Split a run of capitalized words at a sentence end: 'May. The queue' is 'May', then a new sentence."""
    segs, cur = [], []
    for tok in text.split():
        cur.append(tok)
        if tok.endswith(".") and tok not in TITLES and not re.fullmatch(r"(?:[A-Z]\.)+", tok):
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    return segs


def specifics(text):
    """Return ({key: [kind, text, first line, count]}, {word: line} for sentence-initial capitalized words)."""
    out, starters, forms = {}, {}, {}

    def add(key, kind, shown, ln):
        shown = shown.strip().rstrip(",;:")
        if key in out:
            out[key][3] += 1
        else:
            out[key] = [kind, shown, ln, 1]
        if shown.lower() not in [f.lower() for f in forms.setdefault(key, [])]:
            forms[key].append(shown)
    raw = text.split("\n")
    for ln, line in enumerate(strip_noise(text).split("\n"), start=1):
        for m in URL_RE.finditer(line):
            add("url:" + m.group().rstrip(".,;").lower(), "url", m.group().rstrip(".,;"), ln)
        line = URL_RE.sub(" ", line)
        line = re.sub(r"\]\([^)]*\)", "]", line)
        for m in QUOTE_RE.finditer(line):
            q = m.group(1).strip()
            if len(q.split()) >= 3:
                add("quote:" + re.sub(r"\W+", " ", q).strip().lower(), "quote", '"%s"' % q, ln)
        for m in TIME_RE.finditer(line):
            add("time:" + m.group(), "time", m.group(), ln)
        rest = TIME_RE.sub(" ", line)
        nums = list(NUM_RE.finditer(rest))
        # A rate on a number ("$250 annually") belongs to the number; any other frequency stands on its own, and a
        # number word inside it ("two times a week") is part of the frequency, not a separate figure.
        rated = [(m.start(), m.end()) for m in nums if m.group("rate") or m.group("rate2") or m.group("rate3")]
        freqs = [m for m in FREQ_RE.finditer(rest) if not overlaps(m, rated)]
        for m in freqs:
            add(freq_key(m), "frequency", m.group(), ln)
        fspans = [(m.start(), m.end()) for m in freqs]
        for m in nums:
            if overlaps(m, fspans):
                continue
            if m.group("n"):
                try:
                    v = float(m.group("n").replace(",", ""))
                except ValueError:
                    continue
                v *= SCALE.get((m.group("scale") or "").lower(), 1)
                cur, u = m.group("cur") or "", unit(m.group("pct"))
            elif m.group("w"):
                if m.group("w").lower() in QUIET_WORDS and not (m.group("wscale") or m.group("wpct") or m.group("unit")):
                    continue
                v = word_value(m.group("w")) * SCALE.get((m.group("wscale") or "").lower(), 1)
                cur, u = "", unit(m.group("wpct"))
            else:
                continue
            base = "num:%s%s%s" % (cur, "%.6g" % v, u)
            un = UNITS.get((m.group("unit") or "").lower(), "")
            rate = RATES.get((m.group("rate") or m.group("rate2") or m.group("rate3") or "").lower(), "")
            add(base + (" " + un if un else "") + (" /" + rate if rate else ""), "number", m.group(), ln)
        for rx in [VAGUE_RE] + AUTH_RES:
            for m in rx.finditer(rest):
                add("claim:" + re.sub(r"\W+", " ", m.group()).strip().lower(), "claim", m.group(), ln)
        heading = ln <= len(raw) and re.match(r"\s*#+\s", raw[ln - 1]) is not None
        for m in ACRO_RE.finditer(line):
            a = m.group().rstrip("s") if m.group().endswith("s") and m.group()[:-1].isupper() else m.group()
            if a not in COMMON_ACRONYMS and not a.isdigit():
                add("name:" + a, "name", a, ln)
        if heading:
            continue
        starts = sentence_starts(line)
        for m in NAME_RE.finditer(line):
            for k, seg in enumerate(name_segments(m.group())):
                at_start = m.start() in starts if k == 0 else True
                dropped_article = at_start and len(seg) > 1 and seg[0] in ARTICLES
                if dropped_article:
                    seg = seg[1:]
                name = re.sub(r"'s$|[.'&-]+$", "", " ".join(seg))
                if not name or name == "I" or name.isupper():
                    continue
                words = name.split()
                if at_start and not dropped_article and len(words) < 2 and words[0] not in CAL:
                    w = words[0]
                    if w.lower() not in STARTERS and len(w) > 2 and not re.search(r"(?:s|ed|ing|ly)$", w):
                        starters.setdefault(w, ln)
                    continue
                add("name:" + name, "name", name, ln)
    for key, fs in forms.items():
        out[key][1] = " / ".join(fs[:3])   # every wording of the same fact: "once a day / daily"
    return out, starters


def present(key, kind, shown, pool, pool_text):
    if key in pool:
        return True
    if kind == "number" and " " not in key.split(":", 1)[1].lstrip("$"):
        # A bare figure matches the same figure with any unit or rate.
        return any(k.startswith(key + " ") for k in pool)
    if kind == "name":
        return re.search(r"(?<![\w-])" + re.escape(shown) + r"(?![\w-])", pool_text) is not None
    if kind in ("quote", "claim"):
        return re.sub(r"\W+", " ", shown).strip().lower() in re.sub(r"\W+", " ", pool_text).lower()
    return False


def compare(original, revised, sources=()):
    """Return (added, dropped, unchecked, repeated). added, dropped and repeated are [(key, [kind, text, line,
    count before, count after])]; unchecked is [(word, line)]."""
    base_text = "\n".join([original] + list(sources))
    base, _ = specifics(base_text)
    rev, rev_starters = specifics(revised)
    orig, _ = specifics(original)
    added = [(k, v[:3] + [0, v[3]]) for k, v in rev.items() if not present(k, v[0], v[1], base, base_text)]
    dropped = [(k, v[:3] + [v[3], 0]) for k, v in orig.items() if not present(k, v[0], v[1], rev, revised)]
    dropped += [(k, v[:3] + [v[3], rev[k][3]]) for k, v in orig.items() if k in rev and rev[k][3] < v[3]]
    repeated = [(k, v[:3] + [base[k][3], v[3]]) for k, v in rev.items() if k in base and v[3] > base[k][3]]
    low = base_text.lower()
    unchecked = [(w, ln) for w, ln in rev_starters.items()
                 if not re.search(r"(?<![\w-])" + re.escape(w.lower()) + r"(?![\w-])", low)]
    return added, dropped, unchecked, repeated


def read(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "rb") as fh:
        data = fh.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("%s is larger than %d bytes; split it" % (path, MAX_BYTES))
    return data.decode("utf-8", errors="replace")


def fail_mode(argv):
    """The --fail-on flag, else the profile's fact_check_fail_on, else 'added'."""
    flag = next((a.split("=", 1)[1] for a in argv if a.startswith("--fail-on=")), None)
    if flag:
        return flag
    explicit = next((a.split("=", 1)[1] for a in argv if a.startswith("--profile=")), None)
    prof, _ = sl.load_profile(explicit)
    return prof.get("fact_check_fail_on") or "added"


def main(argv):
    opts = ("--source=", "--format=", "--fail-on=", "--profile=")
    srcs = [a.split("=", 1)[1] for a in argv if a.startswith("--source=")]
    fmt = next((a.split("=", 1)[1] for a in argv if a.startswith("--format=")), "text")
    files = [a for a in argv if not a.startswith("--")]
    bad = [a for a in argv if a.startswith("--") and not a.startswith(opts)]
    if len(files) != 2 or bad or fmt not in ("text", "json") or files.count("-") > 1:
        sys.stderr.write(__doc__)
        return 2
    try:
        mode = fail_mode(argv)
        original, revised = read(files[0]), read(files[1])
        sources = [read(s) for s in srcs]
    except (OSError, ValueError) as e:
        sys.stderr.write("check_facts: %s\n" % e)
        return 2
    if mode not in FAIL_MODES:
        sys.stderr.write("check_facts: fail-on must be one of %s, not %r\n" % (", ".join(FAIL_MODES), mode))
        return 2
    added, dropped, unchecked, repeated = compare(original, revised, sources)
    failed = bool(added) or (mode != "added" and bool(dropped)) or (mode == "anything_unchecked" and bool(unchecked))
    if fmt == "json":
        row = lambda kv: {"kind": kv[1][0], "text": kv[1][1], "line": kv[1][2], "before": kv[1][3], "after": kv[1][4]}  # noqa: E731
        print(json.dumps({"added": [row(a) for a in added], "dropped": [row(d) for d in dropped],
                          "repeated": [row(r) for r in repeated],
                          "unchecked": [{"text": w, "line": ln} for w, ln in unchecked],
                          "fail_on": mode, "failed": failed}, indent=1))
    else:
        for label, items, where in (("added", added, files[1]), ("dropped", dropped, files[0]),
                                    ("repeated", repeated, files[1])):
            for _, (kind, shown, ln, before, after) in items:
                counts = " (%d in the original, %d now)" % (before, after) if before and after else ""
                print("%s:%d: %s %s: %s%s" % (where, ln, label, kind, shown, counts))
        for w, ln in unchecked:
            print("%s:%d: unchecked: %s (starts a sentence; a new name or an ordinary word?)" % (files[1], ln, w))
        print("check_facts: %d added (not in the original%s), %d dropped, %d repeated, %d unchecked; fails on %s: %s." % (
            len(added), " or the sources" if sources else "", len(dropped), len(repeated), len(unchecked), mode,
            "failed" if failed else "passed"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
