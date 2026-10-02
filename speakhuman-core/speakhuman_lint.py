#!/usr/bin/env python3
"""SpeakHuman linter: catch AI-sounding writing in prose, site copy, UI strings and replies.

    speakhuman_lint.py <files-or-dirs|-> [options]

    --format=text|json       output format (default text)
    --strict                 exit 1 on warnings too, not only errors
    --verbose                list every hit behind density figures, and per-file metrics
    --min-severity=LEVEL     error | warn | info (default info); "warning" is accepted
                             for warn, since text output prints the warn level as "warning"
    --only=ids               comma-separated rule ids (wildcards allowed: x-not-y*)
    --ignore=ids             comma-separated rule ids to skip
    --baseline=FILE          report only findings not listed in FILE
    --write-baseline=FILE    write current findings to FILE and exit 0
    --dest=markdown|plain    how to read stdin and .md/.txt input (plain = email,
                             LinkedIn, commit message: markdown syntax is a finding)
    --profile=FILE           personal settings (JSON). Default search order: --profile,
                             $SPEAKHUMAN_PROFILE, ./speakhuman-profile.json,
                             ~/.config/speakhuman/profile.json, profile.json beside this file
    --voice                  print what the writing skills read before drafting: the profile's call to
                             action, voice notes, retired terms and the voice_file it names, then exit
    --nominate               print JSON of every sentence with its structural features, and the
                             share of the body the judge pass will see
    --checklist              always print the human review checklist (it prints on its own
                             for inputs of 800 words or more)
    --list-rules             print the rule table and exit

Reads .md .mdx .txt .html .astro .njk as prose, user-facing string literals in
.js .ts .jsx .tsx .vue .svelte, and stdin ("-") for replies and commit messages.

Suppress one line:     <!-- slop-ok: rule-id (reason) -->  or  // slop-ok: rule-id
                       (same line or the line above; a slop-ok with no rule id
                       suppresses nothing and is reported)
Skip a region:         <!-- slop-lint off --> ... <!-- slop-lint on -->
Retire a metaphor:     <!-- slop-lint retired: flywheel, north star, engine room -->
The summary line counts what slop-ok and off regions hid. In plain-text copy a
directive ships with the text, so use --ignore=rule-id there instead.

Exit codes: 0 clean; 1 if any error (or any warning with --strict or a profile that sets
fail_on_warnings); 2 on usage error.
Text output prints the levels as error, warning and info; --format=json and the
flags use error, warn and info.

Rules live in slop_rules.json beside this file; the profile (see profile.json) turns
rules on and off, adds banned and allowed words, rejected phrases and retired terms.
Python 3 standard library only.
"""

import bisect
import fnmatch
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(HERE, "slop_rules.json")

SEV_RANK = {"info": 0, "warn": 1, "error": 2}
PROSE_EXT = (".md", ".mdx", ".markdown")
PLAIN_EXT = (".txt",)
HTML_EXT = (".html", ".htm", ".njk")
JS_EXT = (".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx")
ALL_EXT = PROSE_EXT + PLAIN_EXT + HTML_EXT + JS_EXT + (".astro", ".vue", ".svelte")
# Locale files hold UI copy. In a folder scan a .json file is read only when it looks like one (en.json,
# pt-BR.json, or any .json inside a locales or i18n folder); a .json file named on the command line is always read.
LOCALE_DIRS = {"locales", "locale", "i18n", "l10n", "lang", "langs", "translations", "messages", "strings"}
LOCALE_FILE_RE = re.compile(r"^[a-z]{2,3}(?:[-_][A-Za-z]{2,4})?\.json$")
CONFIG_JSON_RE = re.compile(r"^(?:package(?:-lock)?|[tj]sconfig.*|composer|manifest|vercel|netlify|firebase|\..*)\.json$", re.I)
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".astro", ".next", ".nuxt", ".output", "coverage",
             "vendor", "__pycache__", ".venv", "venv", ".cache", ".turbo", ".vercel", ".svelte-kit"}
MAX_BYTES = 2_000_000


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

class Rule:
    def __init__(self, d):
        self.d = d
        self.id = d["id"]
        self.severity = d["severity"]
        self.kind = d.get("kind", "pattern")
        self.check = d.get("check")
        self.contexts = set(d.get("contexts") or [])
        self.dests = set(d.get("dests") or ["markdown", "plain"])
        self.target = d.get("target", "text")
        self.kinds = set(d.get("kinds") or [])
        self.params = d.get("params") or {}
        self.density = d.get("density")
        self.cls = d.get("class", "pattern")
        self.device = bool(d.get("device"))
        self.allow = [a.lower() for a in (d.get("allow") or [])]
        self.skip_proper = bool(d.get("skip_proper"))
        self.unless_cited = bool(d.get("unless_cited"))
        us = d.get("unless_sentence")
        self.unless_sentence = re.compile(us, re.I) if us else None
        sp = d.get("skip_paths")
        self.skip_paths = re.compile(sp, re.I) if sp else None
        self.patterns = []   # (compiled, scope, position, contexts)
        self.conds = []      # per pattern: None or {"unless", "unless_prev", "skip_roles"}
        for rx in d.get("regexes") or []:
            cond = None
            if isinstance(rx, dict):
                pat, scope, pos = rx["re"], rx.get("scope", "block"), rx.get("position", "any")
                ctxs = set(rx["contexts"]) if rx.get("contexts") else self.contexts
                if rx.get("unless") or rx.get("unless_prev") or rx.get("skip_roles"):
                    cond = {"unless": re.compile(rx["unless"], re.I) if rx.get("unless") else None,
                            "unless_prev": re.compile(rx["unless_prev"], re.I) if rx.get("unless_prev") else None,
                            "skip_roles": frozenset(rx.get("skip_roles") or [])}
            else:
                pat, scope, pos, ctxs = rx, "block", "any", self.contexts
            self.patterns.append((re.compile(pat, re.I), scope, pos, ctxs))
            self.conds.append(cond)
        words = d.get("words") or []
        if words:
            alts = []
            for w in sorted(words, key=len, reverse=True):
                star = w.endswith("*")
                body = re.escape(w.rstrip("*")).replace(r"\ ", r"\s+")
                alts.append(body + (r"\w*" if star else ""))
            pat = r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])"
            self.patterns.append((re.compile(pat, re.I), "block", "any", self.contexts))
            self.conds.append(None)


PROFILE_DEFAULTS = {
    "name": "default",
    "ascii_only": False,
    "disable_rules": [],
    "enable_rules": [],
    "severity_overrides": {},
    "extra_banned_words": [],
    "allowed_words": [],
    "rejected_phrases": [],
    "retired_terms": [],
    "short_closers_allowed": None,
    "disable_classes": [],
    "device_policy": "density",
    "device_min": 2,
    "allow_regex": False,
    "fail_on_warnings": False,
    "device_scope": "piece",
    "fact_check_fail_on": "added",
    "cta_line": "",
    "voice_notes": "",
    "voice_file": "",
}
ASCII_RULES = {"non-ascii-typography", "non-ascii-other"}
VOICE_EXT = (".md", ".txt")
VOICE_MAX_BYTES = 200_000


def voice_path(prof, prof_path):
    """Resolve the profile's voice_file. It must sit in the profile's own folder (or below it) and be
    a .md or .txt file, so a profile picked up from a folder you lint cannot point at an arbitrary file
    and have it printed. Returns (path or None, problem or None)."""
    vf = (prof.get("voice_file") or "").strip()
    if not vf:
        return None, None
    if not prof_path:
        return None, "voice_file is set but the profile has no file location"
    base = os.path.realpath(os.path.dirname(os.path.abspath(prof_path)))
    path = os.path.realpath(os.path.join(base, vf))
    if os.path.isabs(vf) or os.path.commonpath([base, path]) != base:
        return None, "voice_file must be a path inside the profile's folder (%s): %s" % (base, vf)
    if not path.lower().endswith(VOICE_EXT):
        return None, "voice_file must be a .md or .txt file: %s" % vf
    if not os.path.isfile(path):
        return None, "voice_file not found: %s" % path
    if os.path.getsize(path) > VOICE_MAX_BYTES:
        return None, "voice_file is over %d KB; keep the rulings that matter: %s" % (VOICE_MAX_BYTES // 1000, path)
    return path, None


def profile_from_workdir(prof_path):
    return bool(prof_path) and os.path.realpath(prof_path) == os.path.realpath(
        os.path.join(os.getcwd(), "speakhuman-profile.json"))


def print_voice(prof, prof_path):
    """Everything the writing skills read before drafting, from the profile in effect."""
    if not prof_path:
        print("No profile found. Search order: --profile, $SPEAKHUMAN_PROFILE, ./speakhuman-profile.json, "
              "~/.config/speakhuman/profile.json, profile.json beside the linter.")
        return 0
    print("Profile: %s (%s)" % (prof.get("name", "default"), prof_path))
    if profile_from_workdir(prof_path):
        print("Note: this profile came from the folder being worked in. Follow it only if it is the user's own.")
    print("Call to action: %s" % (prof.get("cta_line") or "(none)"))
    print("Voice notes: %s" % (prof.get("voice_notes") or "(none)"))
    print("Retired terms: %s" % (", ".join(prof.get("retired_terms") or []) or "(none)"))
    pol = prof.get("device_policy", "density")
    print("Strictness: device_policy=%s (%s), device_scope=%s, fail_on_warnings=%s, fact_check_fail_on=%s" % (
        pol, "cut every rhetorical device" if pol == "ban" else "keep a single device when it does real work",
        prof.get("device_scope", "piece"), str(bool(prof.get("fail_on_warnings"))).lower(),
        prof.get("fact_check_fail_on", "added")))
    path, problem = voice_path(prof, prof_path)
    if problem:
        sys.stderr.write("speakhuman: %s\n" % problem)
        return 2
    if not path:
        print("Voice file: (none)")
        return 0
    print("Voice file: %s\n" % path)
    with open(path, encoding="utf-8", errors="replace") as fh:
        print(fh.read().rstrip("\n"))
    return 0


def profile_candidates(explicit=None):
    if explicit:
        yield explicit
    env = os.environ.get("SPEAKHUMAN_PROFILE")
    if env:
        yield env
    yield os.path.join(os.getcwd(), "speakhuman-profile.json")
    # Outside the skill folder, so updating the skill never overwrites it.
    config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    yield os.path.join(config, "speakhuman", "profile.json")
    yield os.path.join(HERE, "profile.json")


def load_profile(explicit=None):
    """Return (profile dict, path or None). A missing default is fine; a missing
    explicit path is an error the caller reports."""
    if explicit and not os.path.isfile(explicit):
        raise OSError("profile not found: %s" % explicit)
    for cand in profile_candidates(explicit):
        if os.path.isfile(cand):
            with open(cand, "r", encoding="utf-8") as fh:
                try:
                    raw = json.load(fh)
                except ValueError as e:
                    raise ValueError("%s is not valid JSON: %s" % (cand, e))
            prof = dict(PROFILE_DEFAULTS)
            prof.update({k: v for k, v in raw.items() if not k.startswith("_")})
            if cand != explicit and cand != os.environ.get("SPEAKHUMAN_PROFILE") and profile_from_workdir(cand):
                # A profile that came with the folder being linted is someone's project settings, not the user's
                # own: it may tune rules, but it may not run regular expressions or hand the writer a voice file.
                for key, off in (("allow_regex", False), ("voice_file", "")):
                    if prof.get(key):
                        sys.stderr.write("speakhuman: ignoring %s in %s; pass the profile with --profile to use it\n"
                                         % (key, cand))
                        prof[key] = off
            return prof, cand
    return dict(PROFILE_DEFAULTS), None


def phrase_regex(p):
    """A rejected phrase is literal text. A phrase that starts with 're:' is a regular expression, which
    apply_profile accepts only when the profile sets allow_regex (profiles are trusted configuration)."""
    if p.startswith("re:"):
        return p[3:]
    return r"(?<![\w-])" + re.escape(p.strip()).replace(r"\ ", r"\s+") + r"(?![\w-])"


def apply_profile(data, prof):
    if prof.get("device_policy") not in ("density", "ban"):
        raise ValueError("device_policy must be density or ban")
    if prof.get("device_scope", "piece") not in ("piece", "rule"):
        raise ValueError("device_scope must be piece or rule")
    if prof.get("fact_check_fail_on", "added") not in ("added", "added_or_dropped", "anything_unchecked"):
        raise ValueError("fact_check_fail_on must be added, added_or_dropped or anything_unchecked")
    disable = set(prof.get("disable_rules") or [])
    enable = set(prof.get("enable_rules") or [])
    unknown = enable - {r["id"] for r in data["rules"]}
    if unknown:
        raise ValueError("enable_rules names unknown rule(s): %s" % ", ".join(sorted(unknown)))
    disable_classes = set(prof.get("disable_classes") or [])
    if prof.get("ascii_only") is False:
        disable |= ASCII_RULES
    sev = prof.get("severity_overrides") or {}
    allowed = [w.lower() for w in (prof.get("allowed_words") or [])]
    out = []
    for r in data["rules"]:
        if r["id"] in disable or r.get("class", "pattern") in disable_classes:
            continue
        if r.get("default_off") and r["id"] not in enable:
            continue
        r = dict(r)
        if r["id"] in sev:
            if sev[r["id"]] not in SEV_RANK:
                raise ValueError("severity_overrides.%s must be error, warn or info" % r["id"])
            r["severity"] = sev[r["id"]]
        if allowed and r.get("category") == "vocabulary":
            r["allow"] = allowed
        if r["id"] == "house-banned-vocabulary" and prof.get("extra_banned_words"):
            r["words"] = list(r.get("words") or []) + list(prof["extra_banned_words"])
        if r["id"] == "profile-rejected-phrasing":
            phrases = []
            for ph in prof.get("rejected_phrases") or []:
                if ph.startswith("re:") and not prof.get("allow_regex"):
                    sys.stderr.write("speakhuman: ignoring regex phrase %r (set allow_regex in a trusted profile)\n" % ph)
                    continue
                phrases.append(phrase_regex(ph))
            r["regexes"] = phrases
        if r["id"] == "short-closer-density" and prof.get("short_closers_allowed") is not None:
            r["params"] = dict(r.get("params") or {}, allowed=int(prof["short_closers_allowed"]))
        out.append(r)
    return out


KNOWN_IDS = set()   # every rule id in the rules file, including ones a profile turns off


def load_rules(path=RULES_PATH, profile=None):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    KNOWN_IDS.update(r["id"] for r in data["rules"])
    rules = apply_profile(data, profile) if profile else data["rules"]
    return [Rule(d) for d in rules]


# ---------------------------------------------------------------------------
# Text blocks with an offset map back into the source file
# ---------------------------------------------------------------------------

class Block:
    """roles: what the surrounding HTML says the text is, from class names and
    tags: pullquote, summary (glance box, tl;dr, deck), dialogue (a scripted
    speaker exchange), nav, select (option lists)."""
    __slots__ = ("ctx", "text", "omap", "dest", "cite", "fm", "idx", "holes", "roles", "_sents")

    def __init__(self, ctx, text, omap, dest, cite=False, fm=False, holes=False, roles=frozenset()):
        self.ctx, self.text, self.omap, self.dest = ctx, text, omap, dest
        self.cite, self.fm, self.holes, self.idx, self._sents = cite, fm, holes, -1, None
        self.roles = roles

    def sents(self):
        if self._sents is None:
            self._sents = split_sentences(self.text)
        return self._sents


ASCII_WS = " \t\n\r\f\v"


class TB:
    """Accumulates (char, offset) pairs, then collapses ASCII whitespace on finish.
    Unicode spaces (no-break, thin, zero-width) are kept so the typography rule sees them."""

    def __init__(self):
        self.ch, self.off, self.cite, self.pend, self.holes = [], [], False, None, False

    def addc(self, c, off):
        if self.pend is not None:
            if self.ch and self.ch[-1].isalnum() and c.isalnum():
                self.ch.append(" ")
                self.off.append(self.pend)
            self.pend = None
        self.ch.append(c)
        self.off.append(off)

    def gap(self, off):
        """Something was dropped here; keep words on either side apart."""
        if self.pend is None:
            self.pend = off

    def space(self, off):
        self.ch.append(" ")
        self.off.append(off)

    def finish(self, ctx, dest, cite=False, fm=False, roles=frozenset()):
        out, om, prev_ws = [], [], True
        for c, o in zip(self.ch, self.off):
            if c in ASCII_WS:
                if not prev_ws:
                    out.append(" ")
                    om.append(o)
                prev_ws = True
            else:
                out.append(c)
                om.append(o)
                prev_ws = False
        while out and out[-1] == " ":
            out.pop()
            om.pop()
        if not out:
            return None
        return Block(ctx, "".join(out), om, dest, cite or self.cite, fm, self.holes, roles)


class Doc:
    def __init__(self, path, src, dest, kind="md"):
        self.path, self.src, self.dest, self.kind = path, src, dest, kind
        self.blocks, self.raw_lines = [], []
        self.retired, self.suppress = [], {}
        # directives: (line, offset, "ok" | "off" | "on", rule ids); suppressed: rule id -> findings hidden
        self.directives, self.suppressed, self.off_lines, self.off_unclosed = [], {}, 0, None
        self.not_english = 0
        self.line_starts = [0] + [m.end() for m in re.finditer(r"\n", src)]

    def add(self, blk):
        if blk is not None and blk.text:
            blk.idx = len(self.blocks)
            self.blocks.append(blk)

    def pos(self, off):
        li = bisect.bisect_right(self.line_starts, off) - 1
        return li + 1, off - self.line_starts[li] + 1

    def next_body(self, blk):
        for b in self.blocks[blk.idx + 1:]:
            if b.ctx != "ui":
                return b
        return None

    def cited_near(self, blk, ahead=3):
        """True if blk, or one of the next few body blocks before a heading, cites a source."""
        if blk.cite:
            return True
        seen = 0
        for b in self.blocks[blk.idx + 1:]:
            if b.ctx in ("heading", "title"):
                return False
            if b.ctx == "ui":
                continue
            if b.cite:
                return True
            seen += 1
            if seen >= ahead:
                return False
        return False


def blank(src, a, b):
    """Replace src[a:b] with spaces, keeping newlines so offsets and lines hold."""
    return src[:a] + re.sub(r"[^\n]", " ", src[a:b]) + src[b:]


# ---------------------------------------------------------------------------
# Sentences
# ---------------------------------------------------------------------------

SENT_END = re.compile(r"[.!?]+[\"')\]*_]*(?=\s|$)")
ABBR = {"e.g", "i.e", "etc", "vs", "mr", "mrs", "ms", "dr", "st", "inc", "ltd", "co", "corp", "no", "fig", "u.s",
        "u.k", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "al", "approx",
        "cf", "p", "pp", "vol", "ed", "jr", "sr", "a.m", "p.m"}
WORD_RE = re.compile(r"[A-Za-z0-9$%&][\w'&;$%.,/-]*")


def split_sentences(text):
    spans, start, n = [], 0, len(text)
    for m in SENT_END.finditer(text):
        end = m.end()
        k = end
        while k < n and text[k] == " ":
            k += 1
        if k < n and not (text[k].isupper() or text[k].isdigit() or text[k] in "\"'([$*<"):
            continue
        if m.group()[0] == ".":
            w = re.search(r"([A-Za-z][A-Za-z.]*)$", text[start:m.start()])
            if w:
                tok = w.group(1).lower().rstrip(".")
                if tok in ABBR or len(tok) == 1:
                    continue
        if text[start:end].strip():
            spans.append((start, end))
        start = k
    if start < n and text[start:].strip():
        spans.append((start, n))
    return spans


def nwords(s):
    return len(WORD_RE.findall(s))


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})(?:[ \t]+|$)")
HR_RE = re.compile(r"^\s{0,3}(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
LIST_RE = re.compile(r"^(\s*)(?:[-*+]|\d{1,9}[.)])[ \t]+")
QUOTE_RE = re.compile(r"^\s{0,3}>[ \t]?")
FOOTDEF_RE = re.compile(r"^\s{0,3}\[\^[^\]\s]+\]:[ \t]?")
LINKDEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*\S+\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)*\|?\s*$")
HTML_BLOCK_RE = re.compile(
    r"^\s{0,3}</?(?:address|article|aside|blockquote|body|caption|center|details|dialog|dd|div|dl|dt|fieldset|"
    r"figcaption|figure|footer|form|h[1-6]|header|hr|iframe|legend|li|main|nav|noscript|ol|p|picture|pre|script|"
    r"section|style|summary|svg|table|tbody|td|template|tfoot|th|thead|tr|ul|video|audio|source)\b", re.I)

INLINE_CODE = re.compile(r"(`+)(.+?)\1", re.S)
IMAGE_RE = re.compile(r"!\[([^\]\n]*)\]\(([^)\n]*)\)")
LINK_RE = re.compile(r"\[([^\]\n]*)\]\(([^)\n]*)\)")
REFLINK_RE = re.compile(r"\[([^\]\n]+)\]\[[^\]\n]*\]")
FOOTREF_RE = re.compile(r"\[\^[^\]\s]+\]")
AUTOLINK_RE = re.compile(r"<(?:https?://|mailto:)[^>\s]+>")
URL_RE = re.compile(r"\bhttps?://[^\s)<>\]\"']+")
TAG_RE = re.compile(r"</?[A-Za-z][\w:-]*(?:\s+[^\s=/>]+(?:\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+))?)*\s*/?>")
EMPH_RE = re.compile(r"(?<![\w*\\])\*{1,3}(?=\S)|(?<=\S)\*{1,3}(?![\w*])|(?<![\w\\])_{1,3}(?=[^\s_])|(?<=[^\s_])_{1,3}(?!\w)")
ATTR_RE = re.compile(r"([^\s=/>\"']+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)')")
ATTR_LINT = {"alt": "ui", "aria-label": "ui", "title": "ui", "placeholder": "ui", "aria-description": "ui",
             "aria-placeholder": "ui"}
META_LINT = {"description": "prose", "og:description": "prose", "twitter:description": "prose",
             "og:title": "title", "twitter:title": "title"}

FM_TITLE = {"title", "headline", "seo_title", "og_title", "seotitle"}
FM_PROSE = {"description", "summary", "excerpt", "subtitle", "dek", "deck", "lede", "lead", "tagline", "brief",
            "abstract", "intro", "teaser", "cta", "caption", "alt", "og_description", "seo_description",
            "social_description", "blurb", "note", "notes", "short_version", "shortversion", "standfirst"}
FM_HEAD = {"kicker", "eyebrow", "label"}


def harvest_attrs(doc, tagtext, offfn, dest):
    m = re.match(r"</?([A-Za-z][\w:-]*)", tagtext)
    if not m or tagtext.startswith("</"):
        return
    tag = m.group(1).lower()
    attrs = {}
    for am in ATTR_RE.finditer(tagtext, m.end()):
        name = am.group(1).lower()
        if am.group(2) is not None:
            val, vs = am.group(2), am.start(2)
        else:
            val, vs = am.group(3), am.start(3)
        attrs[name] = (val, vs)
    for name, (val, vs) in attrs.items():
        ctx = ATTR_LINT.get(name)
        if tag == "meta" and name == "content":
            meta = (attrs.get("name") or attrs.get("property") or ("", 0))[0].lower()
            ctx = META_LINT.get(meta)
        if ctx and val.strip() and not name.startswith((":", "@", "v-")):
            tb = TB()
            for k, c in enumerate(val):
                tb.addc(c, offfn(vs + k))
            doc.add(tb.finish(ctx, dest))


def md_inline(doc, s, omap, ctx, dest, fm=False):
    """Strip inline markdown and HTML from s (offsets in omap) and add a block."""
    n = len(s)
    if not n:
        return
    drop = bytearray(n)
    cite = False

    def mark(a, b):
        drop[a:b] = b"\x01" * (b - a)

    if dest == "markdown":
        for m in INLINE_CODE.finditer(s):
            mark(m.start(), m.end())
        for m in IMAGE_RE.finditer(s):
            if drop[m.start()]:
                continue
            mark(m.start(), m.end())
            if m.group(1).strip():
                tb = TB()
                for k in range(m.start(1), m.end(1)):
                    tb.addc(s[k], omap[k])
                doc.add(tb.finish("ui", dest))
        for m in LINK_RE.finditer(s):
            if drop[m.start()]:
                continue
            mark(m.start(), m.start() + 1)
            mark(m.end(1), m.end())
            cite = True
        for m in REFLINK_RE.finditer(s):
            if drop[m.start()]:
                continue
            mark(m.start(), m.start() + 1)
            mark(m.end(1), m.end())
        for m in FOOTREF_RE.finditer(s):
            if not drop[m.start()]:
                mark(m.start(), m.end())
                cite = True
    for m in AUTOLINK_RE.finditer(s):
        if not drop[m.start()]:
            mark(m.start(), m.end())
            cite = True
    for m in TAG_RE.finditer(s):
        if drop[m.start()]:
            continue
        mark(m.start(), m.end())
        tt = m.group()
        if re.match(r"<a\b[^>]*\bhref=", tt, re.I) or re.match(r"<sup\b", tt, re.I):
            cite = True
        harvest_attrs(doc, tt, lambda k, base=m.start(): omap[base + k], dest)
    for m in URL_RE.finditer(s):
        if not drop[m.start()]:
            mark(m.start(), m.end())
            cite = True
    if dest == "markdown":
        for m in EMPH_RE.finditer(s):
            if not drop[m.start()]:
                mark(m.start(), m.end())
        for i in range(n - 1):
            if s[i] == "\\" and s[i + 1] in "\\`*_{}[]()#+-.!|<>" and not drop[i]:
                drop[i] = 1
    tb = TB()
    for i in range(n):
        if drop[i]:
            tb.gap(omap[i])
            continue
        tb.addc(s[i], omap[i])
    doc.add(tb.finish(ctx, dest, cite=cite, fm=fm))


def lines_to_s(lines):
    """[(text, offset)] -> joined string and offset map (newline -> space)."""
    chars, om = [], []
    for k, (t, off) in enumerate(lines):
        if k:
            chars.append(" ")
            om.append(off - 1)
        chars.extend(t)
        om.extend(range(off, off + len(t)))
    return "".join(chars), om


def yaml_scalar(text, off):
    """Decode a YAML scalar into (string, offsets)."""
    s, om = [], []
    if text.startswith("'"):
        k = 1
        while k < len(text):
            if text[k] == "'":
                if k + 1 < len(text) and text[k + 1] == "'":
                    s.append("'")
                    om.append(off + k)
                    k += 2
                    continue
                break
            s.append(text[k])
            om.append(off + k)
            k += 1
    elif text.startswith('"'):
        k = 1
        while k < len(text):
            c = text[k]
            if c == "\\" and k + 1 < len(text):
                nx = text[k + 1]
                s.append(" " if nx in "nrt" else nx)
                om.append(off + k)
                k += 2
                continue
            if c == '"':
                break
            s.append(c)
            om.append(off + k)
            k += 1
    else:
        body = re.sub(r"\s+#.*$", "", text)
        s = list(body)
        om = list(range(off, off + len(body)))
    return "".join(s), om


def parse_frontmatter(doc, lines):
    k = 0
    while k < len(lines):
        text, off = lines[k]
        m = re.match(r"^(\s*)([A-Za-z_][\w-]*)\s*:[ \t]?(.*)$", text)
        if not m:
            k += 1
            continue
        indent, key, rest = len(m.group(1)), m.group(2).lower(), m.group(3).rstrip()
        ctx = "title" if key in FM_TITLE else "prose" if key in FM_PROSE else "heading" if key in FM_HEAD else None
        k += 1
        if ctx is None:
            continue
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            body = []
            while k < len(lines) and (not lines[k][0].strip() or len(lines[k][0]) - len(lines[k][0].lstrip()) > indent):
                t, o = lines[k]
                st = len(t) - len(t.lstrip())
                body.append((t[st:], o + st))
                k += 1
            s, om = lines_to_s([b for b in body if b[0]])
            md_inline(doc, s, om, ctx, "markdown", fm=True)
        elif rest == "":
            while k < len(lines):
                im = re.match(r"^(\s*)-\s+(.*)$", lines[k][0])
                if not im:
                    break
                s, om = yaml_scalar(im.group(2).rstrip(), lines[k][1] + im.start(2))
                md_inline(doc, s, om, ctx, "markdown", fm=True)
                k += 1
        elif rest.startswith("["):
            continue
        else:
            s, om = yaml_scalar(rest, off + m.start(3))
            md_inline(doc, s, om, ctx, "markdown", fm=True)


def table_cells(line, off):
    cells, cur, start, tick = [], [], None, False
    k = 0
    t = line
    while k < len(t):
        c = t[k]
        if c == "`":
            tick = not tick
        if c == "|" and not tick and (k == 0 or t[k - 1] != "\\"):
            if cur:
                cells.append(("".join(cur), off + start))
            cur, start = [], None
        else:
            if start is None:
                start = k
            cur.append(c)
        k += 1
    if cur:
        cells.append(("".join(cur), off + start))
    return [(c, o) for c, o in cells if c.strip()]


def parse_markdown(doc, src, dest="markdown", mdx=False):
    lines, off = [], 0
    for ln in src.split("\n"):
        lines.append((ln, off))
        off += len(ln) + 1
    n = len(lines)
    i = 0
    if n and lines[0][0].strip() == "---":
        for j in range(1, n):
            if lines[j][0].strip() in ("---", "..."):
                parse_frontmatter(doc, lines[1:j])
                i = j + 1
                break
    para, pctx = [], "prose"

    def flush():
        nonlocal para, pctx
        if para:
            if pctx == "html":
                parse_html(doc, "\n".join(t for t, _ in para), para[0][1], dest=dest)
            else:
                s, om = lines_to_s(para)
                md_inline(doc, s, om, pctx, dest)
        para, pctx = [], "prose"

    fence = None
    while i < n:
        text, loff = lines[i]
        if fence:
            if re.match(r"^\s{0,3}" + re.escape(fence), text):
                fence = None
            i += 1
            continue
        fm_ = FENCE_RE.match(text)
        if fm_:
            flush()
            fence = fm_.group(1)[0] * 3
            i += 1
            continue
        if not text.strip():
            flush()
            doc.raw_lines.append((text, loff, "blank"))
            i += 1
            continue
        if mdx and re.match(r"^(?:import|export)\s", text):
            flush()
            i += 1
            continue
        if pctx == "html":
            para.append((text, loff))
            i += 1
            continue
        hm = HEADING_RE.match(text)
        if hm:
            flush()
            body = re.sub(r"[ \t]+#+[ \t]*$", "", text[hm.end():])
            level = len(hm.group(1))
            doc.raw_lines.append((text, loff, "heading"))
            md_inline(doc, body, list(range(loff + hm.end(), loff + hm.end() + len(body))),
                      "title" if level == 1 else "heading", dest)
            i += 1
            continue
        if HR_RE.match(text):
            flush()
            i += 1
            continue
        if HTML_BLOCK_RE.match(text) and not para:
            pctx = "html"
            para.append((text, loff))
            i += 1
            continue
        if LINKDEF_RE.match(text) and not FOOTDEF_RE.match(text):
            flush()
            i += 1
            continue
        fdm = FOOTDEF_RE.match(text)
        if fdm:
            flush()
            doc.raw_lines.append((text, loff, "footnote"))
            para, pctx = [(text[fdm.end():], loff + fdm.end())], "footnote"
            i += 1
            while i < n and lines[i][0].strip() and lines[i][0].startswith(("  ", "\t")):
                t, o = lines[i]
                st = len(t) - len(t.lstrip())
                para.append((t[st:], o + st))
                i += 1
            before = len(doc.blocks)
            md_inline(doc, *lines_to_s(para), "footnote", dest)
            for b in doc.blocks[before:]:
                b.cite = True
            para, pctx = [], "prose"
            continue
        is_table = text.lstrip().startswith("|") or (
            "|" in text and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1][0]) and "-" in lines[i + 1][0])
        if is_table and not para:
            while i < n and lines[i][0].strip() and "|" in lines[i][0]:
                t, o = lines[i]
                if not TABLE_SEP_RE.match(t):
                    doc.raw_lines.append((t, o, "table"))
                    for cell, co in table_cells(t, o):
                        st = len(cell) - len(cell.lstrip())
                        c2 = cell.strip()
                        md_inline(doc, c2, list(range(co + st, co + st + len(c2))), "table", dest)
                i += 1
            continue
        qm = QUOTE_RE.match(text)
        if qm:
            if pctx != "quote":
                flush()
                pctx = "quote"
            rest = text[qm.end():]
            if not rest.strip():
                flush()
                pctx = "quote"
            else:
                para.append((rest, loff + qm.end()))
            doc.raw_lines.append((text, loff, "quote"))
            i += 1
            continue
        lm = LIST_RE.match(text)
        if lm:
            flush()
            pctx = "list"
            para.append((text[lm.end():], loff + lm.end()))
            doc.raw_lines.append((text, loff, "list"))
            i += 1
            continue
        if pctx == "quote":
            flush()
        doc.raw_lines.append((text, loff, pctx if pctx == "list" else "prose"))
        st = len(text) - len(text.lstrip())
        para.append((text[st:], loff + st))
        i += 1
    flush()


def parse_plain(doc, src):
    """Plain text (email, post, commit message). Fenced blocks and indented blocks after a blank
    line are code, such as pasted terminal output: their lines are not prose and not raw-linted.
    The fence lines themselves stay raw, so markdown-leak still reports the ``` in plain copy."""
    para, off, fence, prev_blank, in_indent = [], 0, None, True, False

    def flush():
        nonlocal para
        if para:
            md_inline(doc, *lines_to_s(para), "prose", "plain")
            para = []

    for ln in src.split("\n"):
        fm_ = FENCE_RE.match(ln)
        if fence or fm_:
            if fm_ and not fence:
                flush()
                fence = fm_.group(1)[0] * 3
                doc.raw_lines.append((ln, off, "prose"))
            elif fm_ and ln.strip().startswith(fence):
                fence = None
                doc.raw_lines.append((ln, off, "prose"))
            else:
                doc.raw_lines.append((ln, off, "code"))
            off += len(ln) + 1
            prev_blank = False
            continue
        indented = ln.strip() and (ln.startswith("    ") or ln.startswith("\t"))
        if indented and (prev_blank or in_indent):
            flush()
            in_indent = True
            doc.raw_lines.append((ln, off, "code"))
            off += len(ln) + 1
            prev_blank = False
            continue
        if ln.strip():
            in_indent = False
        prev_blank = not ln.strip()
        doc.raw_lines.append((ln, off, "prose" if ln.strip() else "blank"))
        if ln.strip():
            st = len(ln) - len(ln.lstrip())
            para.append((ln[st:], off + st))
        elif para:
            md_inline(doc, *lines_to_s(para), "prose", "plain")
            para = []
        off += len(ln) + 1
    if para:
        md_inline(doc, *lines_to_s(para), "prose", "plain")


# ---------------------------------------------------------------------------
# HTML (and Astro / Vue / Svelte / Nunjucks templates)
# ---------------------------------------------------------------------------

BLOCK_TAGS = {"address", "article", "aside", "blockquote", "body", "button", "caption", "center", "details", "dialog",
              "dd", "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4",
              "h5", "h6", "head", "header", "hr", "html", "iframe", "label", "legend", "li", "main", "nav", "noscript",
              "ol", "option", "p", "picture", "section", "select", "summary", "table", "tbody", "td", "template",
              "tfoot", "th", "thead", "title", "tr", "ul", "video", "audio", "source", "img", "meta", "link", "input",
              "canvas", "slot"}
VOID_TAGS = {"hr", "img", "meta", "link", "input", "source", "br", "wbr", "area", "base", "col", "embed", "param",
             "track"}
SKIP_TAGS = {"pre", "code", "kbd", "samp", "var", "svg", "math", "textarea", "sup", "style"}


def html_ctx(stack, default):
    for t in reversed(stack):
        if t in ("h1", "title"):
            return "title"
        if t in ("h2", "h3", "h4", "h5", "h6"):
            return "heading"
        if t in ("li", "dt", "dd"):
            return "list"
        if t == "blockquote":
            return "quote"
        if t in ("td", "th", "caption"):
            return "table"
        if t in ("button", "label", "option", "summary", "legend", "select"):
            return "ui"
        if t in ("p", "figcaption"):
            return "prose"
    return default


# Class-name tokens that say what a block is. A token matches when the word is
# the whole token or one hyphen/underscore part of it (fd-pq, glance-item).
ROLE_CLASS = [
    ("pullquote", re.compile(r"(?:^|[-_])(?:pq|pullquote|pull-quote|callout)(?:$|[-_])", re.I)),
    ("summary", re.compile(r"(?:^|[-_])(?:glance|at-a-glance|tldr|tl-dr|summary|synopsis|recap|highlights|"
                           r"key-?points|deck|dek|standfirst|brief|abstract)(?:$|[-_])", re.I)),
    ("dialogue", re.compile(r"(?:^|[-_])(?:dialogue|conversation|transcript)(?:$|[-_])", re.I)),
    ("nav", re.compile(r"(?:^|[-_])(?:nav|navbar|navigation|breadcrumbs?)(?:$|[-_])", re.I)),
]
ROLE_TAG = {"nav": "nav", "select": "select", "option": "select", "datalist": "select", "optgroup": "select"}


def html_roles(stack, classes):
    roles = set()
    for t in stack:
        if t in ROLE_TAG:
            roles.add(ROLE_TAG[t])
    for cl in classes:
        for tok in cl:
            for role, rx in ROLE_CLASS:
                if rx.search(tok):
                    roles.add(role)
    return frozenset(roles)


def tag_classes(tt):
    m = re.search(r"\bclass(?:Name)?\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", tt)
    if not m:
        return ()
    return tuple((m.group(1) if m.group(1) is not None else m.group(2)).split())


def tag_end(src, k):
    """Index just past the '>' that closes a tag, skipping quotes and {braces}."""
    q, depth, n = None, 0, len(src)
    while k < n:
        c = src[k]
        if q:
            if c == q:
                q = None
        elif c in "\"'":
            q = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth = max(0, depth - 1)
        elif c == ">" and depth == 0:
            return k + 1
        k += 1
    return n


def brace_end(src, k):
    """src[k] == '{'; return index of the matching '}' (skips JS strings)."""
    depth, n = 0, len(src)
    while k < n:
        c = src[k]
        if c in "\"'`":
            k = js_string_end(src, k)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return n - 1


def parse_html(doc, src, base, dest="markdown", expr=None, default="ui", roles=frozenset()):
    n, i = len(src), 0
    stack, classes, skip = [], [], 0
    tb = TB()

    def flush():
        nonlocal tb
        doc.add(tb.finish(html_ctx(stack, default), dest, roles=roles | html_roles(stack, classes)))
        tb = TB()

    while i < n:
        c = src[i]
        if c == "<":
            if src.startswith("<!--", i):
                j = src.find("-->", i + 4)
                i = n if j < 0 else j + 3
                tb.gap(base + i - 1)
                continue
            if src.startswith("<!", i) or src.startswith("<?", i):
                j = src.find(">", i)
                i = n if j < 0 else j + 1
                continue
            m = re.match(r"</?([A-Za-z][\w:.-]*)", src[i:i + 64])
            if m:
                j = tag_end(src, i + m.end())
                tt = src[i:j]
                name = m.group(1).lower()
                closing = tt.startswith("</")
                selfclose = tt.rstrip().endswith("/>")
                if not closing:
                    harvest_attrs(doc, tt, lambda k, b=base + i: b + k, dest)
                    if name == "a" and re.search(r"\bhref\s*=", tt, re.I):
                        tb.cite = True
                if name in ("script", "style") and not closing and not selfclose:
                    endm = re.compile(r"</" + name + r"\s*>", re.I).search(src, j)
                    end = endm.start() if endm else n
                    if name == "script" and not re.search(r"type\s*=\s*[\"']?text/(?:template|html)", tt, re.I):
                        parse_js(doc, src[j:end], base + j, dest=dest)
                    i = endm.end() if endm else n
                    continue
                if name in SKIP_TAGS:
                    if name == "sup":
                        tb.cite = True
                    if closing:
                        skip = max(0, skip - 1)
                    elif not selfclose:
                        skip += 1
                    tb.gap(base + i)
                    i = j
                    continue
                if name in BLOCK_TAGS:
                    flush()
                    if closing:
                        while stack:
                            classes.pop()
                            if stack.pop() == name:
                                break
                    elif not selfclose and name not in VOID_TAGS:
                        stack.append(name)
                        classes.append(tag_classes(tt))
                    i = j
                    continue
                if name == "br":
                    tb.space(base + i)
                    i = j
                    continue
                tb.gap(base + i)
                i = j
                continue
        if expr:
            if expr in ("njk", "vue") and src.startswith("{{", i):
                j = src.find("}}", i + 2)
                j = n if j < 0 else j + 2
                parse_js(doc, src[i + 2:max(i + 2, j - 2)], base + i + 2, dest=dest)
                tb.gap(base + i)
                tb.holes = True
                i = j
                continue
            if expr == "njk" and (src.startswith("{%", i) or src.startswith("{#", i)):
                close = "%}" if src[i + 1] == "%" else "#}"
                j = src.find(close, i + 2)
                i = n if j < 0 else j + 2
                tb.gap(base + i - 1)
                continue
            if expr in ("astro", "svelte") and c == "{":
                j = brace_end(src, i)
                parse_js(doc, src[i + 1:j], base + i + 1, dest=dest)
                tb.gap(base + i)
                tb.holes = True
                i = j + 1
                continue
            if expr == "template" and src.startswith("${", i):
                j = brace_end(src, i + 1)
                tb.gap(base + i)
                tb.holes = True
                i = j + 1
                continue
        if skip:
            i += 1
            continue
        tb.addc(c, base + i)
        i += 1
    flush()


# ---------------------------------------------------------------------------
# JS / TS string literals
# ---------------------------------------------------------------------------

IDENT_RE = re.compile(r"(?:[^\W\d]|\$)[\w$]*")
REGEX_PREV = set("(,=:[!&|?{};+-*%<>~^") | {"", "return", "typeof", "case", "do", "else", "in", "of", "new",
                                              "delete", "void", "throw", "yield", "await"}
SKIP_BEFORE = re.compile(
    r"(?:\bimport\b[^;]*|\bfrom|\brequire\s*\(|console\.\w+\s*\(|querySelector(?:All)?\s*\(|getElementById\s*\(|"
    r"getElementsBy\w+\s*\(|classList\.\w+\s*\(|(?:add|remove)EventListener\s*\(|[sg]etAttribute\s*\(|"
    r"matchMedia\s*\(|fetch\s*\(|new\s+RegExp\s*\(|\.(?:test|match|matchAll|replace|replaceAll|split|join|"
    r"startsWith|endsWith|includes|indexOf|getItem|setItem|removeItem|closest|matches)\s*\(|"
    r"new\s+\w*Error\s*\(|\bcase|\btypeof\s+\w+\s*[!=]==?)\s*$")
HTMLISH = re.compile(r"<\s*/?[A-Za-z][\w-]*[\s>/]")
CODEY = re.compile(r"https?://|www\.|\.(?:js|ts|css|png|jpe?g|svg|webp|json|html|md)\b|[{}]|=>|&&|\|\||==|"
                   r"\w\(|</|/>|\$\{|;\S|^\s*[.#@][\w-]")


def js_string_end(src, i):
    q, k, n = src[i], i + 1, len(src)
    while k < n:
        c = src[k]
        if c == "\\":
            k += 2
            continue
        if q == "`" and c == "$" and k + 1 < n and src[k + 1] == "{":
            k = brace_end(src, k + 1) + 1
            continue
        if c == q:
            return k + 1
        if c == "\n" and q != "`":
            return k
        k += 1
    return n


def is_prose(t):
    t = t.strip()
    if len(t) < 8 or " " not in t:
        return False
    if CODEY.search(t):
        return False
    body = t.replace(" ", "")
    if sum(ch.isalpha() for ch in body) < 0.6 * len(body):
        return False
    if len(re.findall(r"[A-Za-z]{2,}", t)) < 2:
        return False
    toks = t.split()
    codey = sum(1 for tok in toks if re.fullmatch(r"[.#]?[a-z0-9]+(?:[-_:/.\[\]=][a-z0-9\[\]%().]*)+", tok))
    if codey >= max(2, len(toks) * 0.5):
        return False
    if re.match(r"^\s*(?:select|insert|update|delete|create|alter|drop|with)\b.*\b(?:from|into|table|set|where)\b", t,
                re.I | re.S):
        return False
    if re.fullmatch(r"[A-Z0-9_]+(?: [A-Z0-9_]+)*", t):
        return False
    return True


def js_literal(doc, src, a, b, base, masked_prefix, dest):
    """A string literal src[a:b] (quotes included)."""
    q = src[a]
    raw = src[a + 1:b - 1] if b - 1 > a and src[b - 1] == q else src[a + 1:b]
    if SKIP_BEFORE.search(masked_prefix[-160:]):
        return
    if HTMLISH.search(raw):
        parse_html(doc, raw, base + a + 1, dest=dest, expr="template" if q == "`" else None, default="ui")
        return
    tb = TB()
    k, end = a + 1, a + 1 + len(raw)
    while k < end:
        c = src[k]
        if c == "\\" and k + 1 < end:
            nx = src[k + 1]
            if nx in "nrt":
                tb.addc(" ", base + k)
                k += 2
            elif nx == "u":
                mm = re.match(r"u\{([0-9a-fA-F]{1,6})\}|u([0-9a-fA-F]{4})", src[k + 1:k + 10])
                if mm:
                    ch = chr(int(mm.group(1) or mm.group(2), 16))
                    # An escaped curly quote is typography chosen on purpose in an ASCII source file
                    # (the same thing smartypants does for markdown), so read it as the straight quote.
                    ch = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}.get(ch, ch)
                    tb.addc(ch, base + k)
                    k += 1 + mm.end()
                else:
                    k += 2
            elif nx == "x" and re.match(r"x[0-9a-fA-F]{2}", src[k + 1:k + 4]):
                tb.addc(chr(int(src[k + 2:k + 4], 16)), base + k)
                k += 4
            else:
                tb.addc(nx, base + k)
                k += 2
            continue
        if q == "`" and c == "$" and k + 1 < end and src[k + 1] == "{":
            j = brace_end(src, k + 1)
            tb.gap(base + k)
            tb.holes = True
            k = j + 1
            continue
        tb.addc(c, base + k)
        k += 1
    text = "".join(tb.ch)
    if is_prose(re.sub(r"\s+", " ", text)):
        doc.add(tb.finish("ui", dest))


JSX_GENERIC = re.compile(r"[A-Za-z_$][\w$.]*\s*(?:,|extends\b)")


def parse_js(doc, src, base, jsx=False, dest="markdown"):
    """Scan JS/TS for user-facing string literals. With jsx, track elements so the text between tags is
    read as text: an apostrophe in "Don't worry, it's fine" is not a string delimiter there.
    stack frames: ["tag", closing, braces] inside <...>; ["elem"] in an element's children;
    ["expr", braces] inside a {...} child expression."""
    n, i = len(src), 0
    masked = list(src)
    prev = ""
    stack, jsx_texts = [], []

    def mask(a, b):
        for k in range(a, b):
            if masked[k] != "\n":
                masked[k] = " "

    def after_element():
        """Back in code (or an expression) after an element closed; in children, keep reading text."""
        return "jsx" if not stack or stack[-1][0] != "elem" else prev

    while i < n:
        c = src[i]
        if jsx and stack and stack[-1][0] == "elem":
            j = i
            while j < n and src[j] not in "<{":
                j += 1
            if src[i:j].strip():
                jsx_texts.append((i, j))
            mask(i, j)
            i = j
            if i >= n:
                break
            if src[i] == "{":
                stack.append(["expr", 1])
                prev = "{"
                i += 1
            elif src.startswith("</", i):
                stack.append(["tag", True, 0])
                mask(i, i + 2)
                i += 2
            else:
                stack.append(["tag", False, 0])
                mask(i, i + 1)
                i += 1
            continue
        if c in " \t\r\n":
            i += 1
            continue
        if jsx and stack and stack[-1][0] == "tag" and stack[-1][2] == 0:
            closing = stack[-1][1]
            # Mask the delimiters this loop consumes, so the fallback below cannot anchor on them.
            if c == "/" and i + 1 < n and src[i + 1] == ">":
                mask(i, i + 2)
                stack.pop()
                prev = after_element()
                i += 2
                continue
            if c == ">":
                mask(i, i + 1)
                stack.pop()
                if closing:
                    if stack and stack[-1][0] == "elem":
                        stack.pop()
                    prev = after_element()
                else:
                    stack.append(["elem"])
                i += 1
                continue
        if (jsx and c == "<" and prev in REGEX_PREV and i + 1 < n and (src[i + 1].isalpha() or src[i + 1] in "_$>")
                and not JSX_GENERIC.match(src, i + 1)):
            stack.append(["tag", False, 0])
            mask(i, i + 1)
            prev = "<"
            i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            j = n if j < 0 else j
            mask(i, j)
            i = j
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            mask(i, j)
            i = j
            continue
        if c in "\"'`":
            j = js_string_end(src, i)
            js_literal(doc, src, i, j, base, "".join(masked[max(0, i - 200):i]), dest)
            mask(i, j)
            prev = "str"
            i = j
            continue
        if c == "/" and prev in REGEX_PREV:
            k, cls = i + 1, False
            while k < n and src[k] != "\n":
                ch = src[k]
                if ch == "\\":
                    k += 2
                    continue
                if ch == "[":
                    cls = True
                elif ch == "]":
                    cls = False
                elif ch == "/" and not cls:
                    break
                k += 1
            mask(i, min(n, k + 1))
            i = k + 1
            prev = "re"
            continue
        if c.isalpha() or c in "_$":
            m = IDENT_RE.match(src, i)
            prev = m.group()
            i = m.end()
            continue
        if c.isdigit():
            m = re.match(r"[\w.]+", src[i:])
            prev = "num"
            i += m.end()
            continue
        if jsx and stack and c in "{}":
            top = stack[-1]
            k = 2 if top[0] == "tag" else 1
            top[k] = top[k] + 1 if c == "{" else max(0, top[k] - 1)
            if top[0] == "expr" and top[k] == 0:
                stack.pop()
        prev = c
        i += 1
    for a, b in jsx_texts:
        # Text between tags is always shown to the reader, so it gets the HTML text-node treatment,
        # not the 20-character prose test that keeps keys and class lists out of string literals.
        if re.search(r"[A-Za-z]{2,}", src[a:b]):
            tb = TB()
            for k in range(a, b):
                tb.addc(src[k], base + k)
            doc.add(tb.finish("ui", dest))
    if jsx:
        # Fallback for text the element tracking did not reach; text it read is already masked.
        ms = "".join(masked)
        for m in re.finditer(r">([^<>{}]+)<", ms):
            t = m.group(1)
            if is_prose(re.sub(r"\s+", " ", t)):
                tb = TB()
                for k in range(m.start(1), m.end(1)):
                    tb.addc(src[k], base + k)
                doc.add(tb.finish("ui", dest))


# ---------------------------------------------------------------------------
# Reading a document
# ---------------------------------------------------------------------------

# Directives count only inside a comment (HTML, //, /* */ or #), and never inside
# a fenced code block or an inline code span, so docs can show them as examples.
CMT = r"(?:<!--|//|/\*|#)[ \t]*"
OKLINE_RE = re.compile(CMT + r"slop-ok\b(?:[ \t]*:([^\n]*))?")
RULE_ID_RE = re.compile(r"(?<![\w-])(?:[a-z0-9]+(?:-[a-z0-9]+)+|\*)(?![\w-])")
LEAD_IDS_RE = re.compile(r"[ \t]*(?:(?:[a-z0-9]+(?:-[a-z0-9]+)+|\*)(?:[ \t]*,[ \t]*|[ \t]+|(?=[^\w-])|$))*")
RETIRED_RE = re.compile(CMT + r"slop-lint[ \t]+retired[ \t]*:[ \t]*([^\n]*?)[ \t]*(?:-->|\*/|$)", re.M)
# The rest of the comment (" -->" or " */") is part of the directive, so it is
# blanked with the region instead of leaking into the text as a stray "-->".
OFFON_RE = re.compile(CMT + r"slop-lint[ \t]+(off|on)\b(?:[^\n]*?(?:-->|\*/))?")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def code_lines(src):
    """Line numbers inside fenced code blocks (markdown)."""
    out, fence = set(), None
    for li, line in enumerate(src.split("\n"), start=1):
        if fence:
            out.add(li)
            if re.match(r"^\s{0,3}" + re.escape(fence), line):
                fence = None
            continue
        fm = FENCE_RE.match(line)
        if fm:
            fence = fm.group(1)[0] * 3
            out.add(li)
    return out


def read_doc(path, src, dest_override=None):
    low = path.lower()
    if path == "<stdin>":
        kind = "plain" if dest_override == "plain" else "md"
    elif low.endswith(PROSE_EXT):
        kind = "plain" if dest_override == "plain" else "md"
    elif low.endswith(PLAIN_EXT):
        kind = "md" if dest_override == "markdown" else "plain"
    elif low.endswith(HTML_EXT):
        kind = "html"
    elif low.endswith(".astro"):
        kind = "astro"
    elif low.endswith((".vue", ".svelte")):
        kind = low.rsplit(".", 1)[1]
    elif low.endswith(JS_EXT):
        kind = "js"
    elif low.endswith(".json"):
        kind = "json"
    else:
        kind = "plain" if dest_override != "markdown" else "md"
    dest = "plain" if kind == "plain" else "markdown"
    doc = Doc(path, src, dest, kind)

    fenced = code_lines(src) if kind in ("md", "plain") else set()

    def live(m):
        li = doc.pos(m.start())[0]
        line = src[doc.line_starts[li - 1]:m.start()]
        return li not in fenced and line.count("`") % 2 == 0

    for m in OKLINE_RE.finditer(src):
        if live(m):
            # The rule ids lead the directive ("slop-ok: rule-a, rule-b (reason)"); the reason is free text.
            body = (m.group(1) or "").split("-->")[0].split("*/")[0]
            ids = LEAD_IDS_RE.match(body).group(0)
            ids = set(RULE_ID_RE.findall(ids)) - {"*"}
            li = doc.pos(m.start())[0]
            doc.directives.append((li, m.start(), "ok", sorted(ids)))
            if ids:
                doc.suppress[li] = doc.suppress.get(li, set()) | ids
    for m in RETIRED_RE.finditer(src):
        if not live(m):
            continue
        for term in m.group(1).split(","):
            term = term.strip().strip("-").strip()
            if term:
                doc.retired.append(term)

    # Mask off-regions, then comments (their directives are already read).
    work, off_at = src, None
    for m in OFFON_RE.finditer(src):
        if not live(m):
            continue
        doc.directives.append((doc.pos(m.start())[0], m.start(), m.group(1), []))
        if m.group(1) == "off" and off_at is None:
            off_at = m.start()
        elif m.group(1) == "on" and off_at is not None:
            work = blank(work, off_at, m.end())
            doc.off_lines += src.count("\n", off_at, m.end()) + 1
            off_at = None
    if off_at is not None:
        work = blank(work, off_at, len(work))
        doc.off_lines += src.count("\n", off_at, len(src.rstrip("\n"))) + 1
        doc.off_unclosed = off_at
    if kind in ("md", "html", "astro", "vue", "svelte"):
        for m in COMMENT_RE.finditer(work):
            work = blank(work, m.start(), m.end())

    if kind == "md":
        parse_markdown(doc, work, mdx=low.endswith(".mdx"))
    elif kind == "plain":
        parse_plain(doc, work)
    elif kind == "html":
        parse_html(doc, work, 0, expr="njk")
    elif kind == "astro":
        start = 0
        fm = re.match(r"\s*---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", work, re.S)
        if fm:
            parse_js(doc, fm.group(1), fm.start(1))
            start = fm.end()
        parse_html(doc, work[start:], start, expr="astro")
    elif kind in ("vue", "svelte"):
        parse_html(doc, work, 0, expr="vue" if kind == "vue" else "svelte")
    elif kind == "json":
        parse_locale_json(doc, work, dest)
    else:
        parse_js(doc, work, 0, jsx=low.endswith((".jsx", ".tsx")))
    english_only(doc)
    return doc


def english_only(doc):
    """SpeakHuman's rules are written for English. A block that is mostly non-Latin script is set aside and
    counted, so the summary says what was not checked instead of reporting every character as typography."""
    kept = []
    for b in doc.blocks:
        letters = [ch for ch in b.text if ch.isalpha()]
        if len(letters) >= 3 and sum(1 for ch in letters if ord(ch) >= 0x250) > 0.5 * len(letters):
            doc.not_english += 1
            continue
        b.idx = len(kept)
        kept.append(b)
    doc.blocks = kept


JSON_STR_RE = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def parse_locale_json(doc, src, dest):
    """Every string value in a locale file is UI copy; keys are not. Escapes are decoded and each character keeps
    the offset of its source so findings point at the right column."""
    for m in JSON_STR_RE.finditer(src):
        after = src[m.end():m.end() + 40].lstrip()
        if after.startswith(":"):
            continue
        raw = m.group()[1:-1]
        if not re.search(r"[A-Za-z]{2,}", raw) or re.fullmatch(r"\s*(?:https?://|mailto:|/|\.{0,2}/)\S*\s*", raw):
            continue
        tb, k, base = TB(), 0, m.start() + 1
        while k < len(raw):
            if raw[k] == "\\" and k + 1 < len(raw):
                n = 6 if raw[k + 1] == "u" else 2
                try:
                    ch = json.loads('"' + raw[k:k + n] + '"')
                except ValueError:
                    ch = raw[k + 1]
                tb.addc(ch, base + k)
                k += n
                continue
            tb.addc(raw[k], base + k)
            k += 1
        doc.add(tb.finish("ui", dest))


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

class Finding:
    __slots__ = ("path", "line", "col", "rule", "severity", "category", "match", "message", "fix", "ctx",
                 "hits", "doc_level", "cls", "device")

    def as_dict(self):
        d = {k: getattr(self, k) for k in self.__slots__ if k not in ("hits", "doc_level", "device")}
        d["class"] = d.pop("cls")
        if self.hits:
            d["hits"] = [{"line": l, "col": c, "match": t} for l, c, t in self.hits]
        return d


def mk(doc, rule, off, match, ctx, message=None):
    f = Finding()
    f.path = doc.path
    f.line, f.col = doc.pos(off)
    f.rule, f.severity = rule.id, rule.severity
    f.category = rule.d.get("category", "")
    f.cls, f.device = rule.cls, rule.device
    f.match = re.sub(r"\s+", " ", match).strip()[:160]
    f.message = message or rule.d.get("message", "")
    f.fix = rule.d.get("fix", "")
    f.ctx, f.hits, f.doc_level = ctx, [], False
    return f


def sentence_at(blk, k):
    for a, b in blk.sents():
        if a <= k < b:
            return blk.text[a:b]
    return blk.text


def sentences_before(blk, k, count=2):
    """Up to `count` sentences of the same block that end before offset k."""
    prev = [(a, b) for a, b in blk.sents() if b <= k]
    return " ".join(blk.text[a:b] for a, b in prev[-count:])


def proper_skip(blk, a, b):
    """True when the hit looks like a proper noun: Title-case (Cornerstone, Pivotal) and
    either mid-sentence or followed by another capitalized word. Acronym
    compounds (AI-powered) are not proper nouns."""
    t = blk.text
    w = t[a:b]
    if not (w[:1].isupper() and w[1:2].islower()):
        return False
    before = t[:a].rstrip()
    at_start = (not before) or before[-1] in ".!?:\"'(" or before.endswith(("*", "-"))
    if not at_start:
        return True
    after = t[b:].lstrip()
    return bool(after[:1].isupper())


def pattern_hits(rule, doc):
    """Yield (block, start, end) for every regex hit of a pattern/density rule."""
    for blk in doc.blocks:
        if blk.dest not in rule.dests or rule.target != "text":
            continue
        taken = []
        for k_, (rx, scope, pos, ctxs) in enumerate(rule.patterns):
            if blk.ctx not in ctxs:
                continue
            cond = rule.conds[k_]
            if cond and cond["skip_roles"] & blk.roles:
                continue
            spans = []
            if scope == "sentence":
                ss = blk.sents()
                if not ss:
                    continue
                if pos == "first":
                    cands = [ss[0]]
                elif pos == "lead":
                    # the first sentence, or the second after a short opener ("Great question!")
                    cands = ss[:2] if len(ss) > 1 and nwords(blk.text[ss[0][0]:ss[0][1]]) <= 4 else [ss[0]]
                elif pos == "last":
                    cands = [ss[-1]]
                elif pos == "only":
                    cands = [ss[0]] if len(ss) == 1 else []
                elif pos == "last2":
                    cands = [(ss[-2][0], ss[-1][1])] if len(ss) >= 2 else []
                else:
                    cands = ss
                for a, b in cands:
                    m = rx.search(blk.text[a:b])
                    if m:
                        spans.append((a + m.start(), a + m.end()))
            else:
                spans = [(m.start(), m.end()) for m in rx.finditer(blk.text) if m.end() > m.start()]
            for a, b in spans:
                if any(a < tb_ and ta < b for ta, tb_ in taken):
                    continue
                if rule.skip_proper and proper_skip(blk, a, b):
                    continue
                if rule.unless_sentence and rule.unless_sentence.search(sentence_at(blk, a)):
                    continue
                if cond and cond["unless"] and cond["unless"].search(sentence_at(blk, a)):
                    continue
                if cond and cond["unless_prev"] and cond["unless_prev"].search(sentences_before(blk, a)):
                    continue
                if rule.unless_cited and doc.cited_near(blk):
                    continue
                taken.append((a, b))
                yield blk, a, b


def raw_hits(rule, doc):
    if doc.dest not in rule.dests:
        return
    for text, off, kind in doc.raw_lines:
        if kind in ("blank", "footnote", "table", "code"):
            continue
        for rx, _scope, _pos, _ctxs in rule.patterns:
            for m in rx.finditer(text):
                yield off + m.start(), m.group()


# ---------------------------------------------------------------------------
# Engine checks
# ---------------------------------------------------------------------------

def blocks_in(doc, rule, body_only=True):
    for b in doc.blocks:
        if b.ctx in rule.contexts and not (body_only and b.fm):
            yield b


def chk_fragment_run(rule, doc):
    mx, mn = rule.params.get("max_words", 3), rule.params.get("min_run", 3)
    for b in blocks_in(doc, rule):
        if b.holes:
            continue
        ss = b.sents()
        run = []
        for a, e in ss + [(None, None)]:
            if a is not None and nwords(b.text[a:e]) <= mx:
                run.append((a, e))
                continue
            if len(run) >= mn:
                yield mk(doc, rule, b.omap[run[0][0]], b.text[run[0][0]:run[-1][1]], b.ctx)
            run = []


def chk_anaphora(rule, doc):
    mn, stop = rule.params.get("min_run", 3), set(rule.params.get("stop", []))
    cond_openers = set(rule.params.get("list_openers", []))
    for b in blocks_in(doc, rule):
        ss = b.sents()
        firsts = []
        for a, e in ss:
            m = re.match(r"[\"'(*_]*([A-Za-z']+)", b.text[a:e])
            firsts.append(m.group(1).lower() if m else "")
        k = 0
        while k < len(firsts):
            j = k
            while j + 1 < len(firsts) and firsts[j + 1] == firsts[k]:
                j += 1
            if firsts[k] and firsts[k] not in stop and j - k + 1 >= mn:
                f = mk(doc, rule, b.omap[ss[k][0]], b.text[ss[k][0]:ss[j][1]], b.ctx,
                       rule.d["message"] + " (%d sentences open on '%s')" % (j - k + 1, firsts[k]))
                # A run at the minimum that is a list of questions or conditions
                # ("Would X? Would Y? Would Z?", "If A... If B... If C...") is the
                # deliberate kind the rule allows; report it as info, not a warning.
                questions = all(b.text[a:e].rstrip("\"')*_ ").endswith("?") for a, e in ss[k:j + 1])
                if j - k + 1 == mn and (questions or firsts[k] in cond_openers):
                    f.severity = "info"
                    f.message += "; a list of questions or conditions, so read it aloud before changing it"
                yield f
            k = j + 1


# A plain word item ("rest anim", "serve 2"); identifiers, paths, camelCase and
# parenthesized values are data lists, not options offered to a reader.
OPTION_ITEM_RE = re.compile(r"^[A-Za-z][A-Za-z'-]*(?: [A-Za-z0-9][A-Za-z0-9'-]*){0,3}$")


def option_item(it, mx):
    w = nwords(it)
    plain = bool(OPTION_ITEM_RE.match(it.strip(" .;!?"))) and not re.search(r"[a-z][A-Z]", it)
    return 1 <= w <= mx and plain


def chk_option_overload(rule, doc):
    mn, mx = rule.params.get("min_items", 8), rule.params.get("max_words", 3)
    # 1. A comma run inside one sentence ("serve, serve 2, blocks, help, ...").
    for b in blocks_in(doc, rule):
        for a, e in b.sents():
            s = b.text[a:e]
            items = [re.sub(r"^(?:and|or)\s+", "", x.strip()) for x in re.split(r",", s)]
            if items and ":" in items[0]:
                items[0] = items[0].rsplit(":", 1)[1]
            run = best = 0
            for it in items:
                run = run + 1 if option_item(it, mx) else 0
                best = max(best, run)
            if best >= mn:
                yield mk(doc, rule, b.omap[a], s, b.ctx,
                         rule.d["message"] + " (%d items)" % best)
    # 2. Consecutive list items or buttons, each a short plain label (a menu or
    # toolbar). Site navigation and <select> options are directories, not choices.
    walk = [c for c in ("list", "ui") if c in rule.contexts]
    run = []
    for b in doc.blocks + [None]:
        if (b is not None and b.ctx in walk and not b.fm and not (b.roles & {"nav", "select"})
                and option_item(b.text, mx)):
            run.append(b)
            continue
        if len(run) >= mn:
            yield mk(doc, rule, run[0].omap[0], ", ".join(x.text for x in run[:12]), run[0].ctx,
                     rule.d["message"] + " (%d list items or buttons in a row)" % len(run))
        run = []


DUP_EXEMPT_ROLES = {"pullquote", "summary"}


def chk_duplication(rule, doc):
    """A sentence of min_words or more that appears again, whole or embedded in
    a longer sentence ("Later, the committee noted that <same sentence>").
    A pull quote, a callout or a glance/summary box repeats body text by design."""
    mn = rule.params.get("min_words", 8)
    sents = []   # (block, start, end, words)
    for b in blocks_in(doc, rule):
        for a, e in b.sents():
            key = re.sub(r"[^a-z0-9 ]+", "", b.text[a:e].lower())
            sents.append((b, a, e, key.split()))
    index = {}
    for i, (_b, _a, _e, w) in enumerate(sents):
        for k in range(len(w) - mn + 1):
            index.setdefault(tuple(w[k:k + mn]), set()).add(i)
    reported = set()
    for i, (b, a, e, w) in enumerate(sents):
        if len(w) < mn:
            continue
        n = len(w)
        for j in sorted(index.get(tuple(w[:mn]), ())):
            if j == i:
                continue
            tb, ta, te, tw = sents[j]
            if len(tw) < n or not any(tw[k:k + n] == w for k in range(len(tw) - n + 1)):
                continue
            if len(tw) == n and j > i:
                continue   # an exact repeat is reported once, at the later copy
            if ((b.ctx == "quote" or b.roles & DUP_EXEMPT_ROLES) or
                    (tb.ctx == "quote" or tb.roles & DUP_EXEMPT_ROLES)):
                continue
            later, first = (sents[j], sents[i]) if j > i else (sents[i], sents[j])
            if (later[0].idx, later[1]) in reported:
                continue
            reported.add((later[0].idx, later[1]))
            lb, la, le, _ = later
            yield mk(doc, rule, lb.omap[la], lb.text[la:le], lb.ctx,
                     rule.d["message"] + " (first at line %d)" % doc.pos(first[0].omap[first[1]])[0])


def chk_broetry(rule, doc):
    mn, mx = rule.params.get("min_run", 5), rule.params.get("max_words", 15)
    run = []
    for b in doc.blocks + [None]:
        if b is not None and b.ctx == "ui":
            continue
        ok = (b is not None and b.ctx == "prose" and not b.fm and len(b.sents()) == 1 and nwords(b.text) <= mx
              and b.text.rstrip("\"')*_").endswith((".", "!", "?")))
        if ok:
            run.append(b)
            continue
        if len(run) >= mn:
            yield mk(doc, rule, run[0].omap[0], " / ".join(x.text for x in run[:6]), "prose",
                     rule.d["message"] + " (%d in a row)" % len(run))
        run = []


def prose_sentence_lengths(doc):
    out = []
    for b in doc.blocks:
        if b.ctx == "prose" and not b.fm:
            for a, e in b.sents():
                w = nwords(b.text[a:e])
                if w:
                    out.append(w)
    return out


def chk_sentence_cv(rule, doc):
    lens = prose_sentence_lengths(doc)
    if len(lens) < rule.params.get("min_sentences", 15):
        return
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    if cv < rule.params.get("cv_below", 0.35):
        first = next(b for b in doc.blocks if b.ctx == "prose" and not b.fm)
        f = mk(doc, rule, first.omap[0], "CV %.2f, mean %.1f words, %d sentences" % (cv, mean, len(lens)), "prose",
               rule.d["message"] + " (variation %.2f; human long-form usually runs above %.2f)" % (
                   cv, rule.params.get("cv_below", 0.35)))
        f.doc_level = True
        yield f


def chk_paragraph_cv(rule, doc):
    counts = [len(b.sents()) for b in doc.blocks if b.ctx == "prose" and not b.fm]
    if len(counts) < rule.params.get("min_paragraphs", 8):
        return
    mean = statistics.mean(counts)
    cv = statistics.pstdev(counts) / mean if mean else 0
    if cv < rule.params.get("cv_below", 0.25):
        first = next(b for b in doc.blocks if b.ctx == "prose" and not b.fm)
        f = mk(doc, rule, first.omap[0], "CV %.2f over %d paragraphs" % (cv, len(counts)), "prose",
               rule.d["message"] + " (variation %.2f over %d paragraphs)" % (cv, len(counts)))
        f.doc_level = True
        yield f


NUMBER_WORD_RE = re.compile(r"\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|"
                            r"fifty|hundred|thousand|million|billion|half|third|quarter|fifth|once|twice)\b", re.I)


def carries_fact(s):
    """The longform keep-test: a closer with a number or a name carries a fact."""
    return bool(re.search(r"\d", s) or NUMBER_WORD_RE.search(s) or re.search(r"(?<=[a-z,;] )[A-Z][a-z]", s))


def short_closers(doc, mx):
    """Last sentences of prose paragraphs that are short and carry no number or
    name, plus one-sentence paragraphs of that kind. Scripted dialogue, decks,
    glance boxes and pull quotes are display text, not paragraph endings."""
    out = []
    for b in doc.blocks:
        if (b.ctx == "prose" and not b.fm and not b.cite and not b.holes
                and not (b.roles & {"dialogue", "summary", "pullquote"})):
            ss = b.sents()
            if not ss:
                continue
            a, e = ss[-1]
            s = b.text[a:e]
            if not (2 <= nwords(s) <= mx) or carries_fact(s):
                continue
            if len(ss) == 1 and not s.rstrip("\"')*_").endswith((".", "!", "?")):
                continue   # a label or caption, not a sentence
            out.append((b, a, e))
    return out


def chk_short_closers(rule, doc):
    mx, allowed = rule.params.get("max_words", 8), rule.params.get("allowed", 3)
    sc = short_closers(doc, mx)
    if len(sc) > allowed:
        b, a, e = sc[0]
        rate = len(sc) * 1000.0 / max(1, doc_words(doc))
        f = mk(doc, rule, b.omap[a], "%d short closers" % len(sc), "prose",
               rule.d["message"] + " (%d closers of %d words or fewer, %.1f per 1000 words; allowed %d)" % (
                   len(sc), mx, rate, allowed))
        f.doc_level = True
        f.hits = [doc.pos(x.omap[s]) + (x.text[s:t],) for x, s, t in sc]
        yield f


FIG_RE = re.compile(r"\$\d[\d,]*(?:\.\d+)?(?:\s?(?:k|m|mm|b|bn|thousand|million|billion|trillion)\b)?|"
                    r"\b\d[\d,]*(?:\.\d+)?\s?%|\b\d[\d,]*(?:\.\d+)? percent\b")


def fig_key(s):
    """'$10 billion' and '$10billion' match; '52 percent' and '52%' match."""
    return re.sub(r"[\s,]+", "", s.lower()).replace("percent", "%")


def chk_unsourced(rule, doc):
    # A figure that was cited earlier in the piece is sourced when it is reused
    # later. Only earlier: an unrelated "90 percent" in a later footnote does not
    # source a different claim.
    sourced, hits = set(), []
    for b in doc.blocks:
        cited = doc.cited_near(b)
        if (not cited and b.ctx in rule.contexts and not b.fm
                and not (b.roles & {"dialogue", "pullquote"})):
            figs = [m for m in FIG_RE.finditer(b.text) if fig_key(m.group()) not in sourced]
            if figs:
                hits.append((b, figs[0].start()))
        if cited:
            sourced.update(fig_key(m.group()) for m in FIG_RE.finditer(b.text))
    if hits:
        b, k = hits[0]
        f = mk(doc, rule, b.omap[k], "%d paragraph(s)" % len(hits), b.ctx,
               rule.d["message"] + " (%d paragraph(s))" % len(hits))
        f.doc_level = True
        f.hits = [doc.pos(x.omap[s]) + (x.text[s:s + 60],) for x, s in hits]
        yield f


def chk_stapled(rule, doc):
    if doc_words(doc) < rule.params.get("min_words", 300):
        return
    last = None
    for b in doc.blocks:
        if b.ctx == "prose" and not b.fm:
            last = b
    if last is None:
        return
    t = last.text
    if re.search(r"\d", t):
        return
    for a, e in last.sents():
        if re.search(r"(?<=[a-z,;] )[A-Z][a-z]", t[a:e]):
            return
    f = mk(doc, rule, last.omap[0], t[:120], "prose")
    f.doc_level = True
    yield f


def chk_retired(rule, doc):
    if not doc.retired:
        return
    alts = sorted({re.escape(t).replace(r"\ ", r"\s+") for t in doc.retired}, key=len, reverse=True)
    rx = re.compile(r"(?<![\w-])(?:" + "|".join(alts) + r")(?![\w-])", re.I)
    for b in doc.blocks:
        for m in rx.finditer(b.text):
            yield mk(doc, rule, b.omap[m.start()], m.group(), b.ctx,
                     rule.d["message"] + " (retired term: '%s')" % m.group().lower())


def chk_closer_no_fact(rule, doc):
    """A paragraph of three or more sentences whose last sentence is short, much
    shorter than the rest, and carries no number, name or figure. That is the
    shape of a stinger: the paragraph made its point, then added a moral."""
    p = rule.params
    min_s, max_w, ratio = p.get("min_sentences", 3), p.get("max_words", 12), p.get("ratio", 0.5)
    for b in doc.blocks:
        if (b.ctx != "prose" or b.fm or b.cite or b.holes
                or b.roles & {"dialogue", "summary", "pullquote", "nav", "select"}):
            continue
        ss = b.sents()
        if len(ss) < min_s:
            continue
        a, e = ss[-1]
        last = b.text[a:e]
        n = nwords(last)
        if n < 2 or n > max_w or carries_fact(last) or last.rstrip("\"')*_").endswith("?"):
            continue
        rest = [nwords(b.text[x:y]) for x, y in ss[:-1]]
        mean = sum(rest) / len(rest)
        if n > mean * ratio:
            continue
        yield mk(doc, rule, b.omap[a], last, "prose",
                 rule.d["message"] + " (%d words after sentences averaging %.0f)" % (n, mean))


ECHO_STOP = {"that", "this", "with", "from", "have", "were", "been", "they", "their", "there", "what", "when", "will",
             "would", "could", "should", "about", "which", "these", "those", "then", "than", "into", "just", "also"}
ECHO_PAYOFF = re.compile(r"\b(?:nothing|nobody|no one|never|none|more|less|faster|slower|worse|better|harder|easier|"
                         r"longer|shorter|still|only|again|instead|anyway|everything)\b", re.I)


ECHO_FLIP = re.compile(r"^(?:the |a |an |our |your )?[\w'-]+(?: [\w'-]+){0,2} (?:did not|does not|do not|didn't|doesn't|"
                       r"will not|won't|was not|wasn't|is not|isn't|could not|couldn't)[.!]$", re.I)


def chk_echo_pair(rule, doc):
    """Last two sentences of a paragraph: both short, sharing a content word,
    the second ending on a payoff word and carrying no number or name."""
    mx = rule.params.get("max_words", 8)
    for b in doc.blocks:
        if (b.ctx != "prose" or b.fm or b.cite or b.holes
                or b.roles & {"dialogue", "summary", "pullquote", "nav", "select"}):
            continue
        ss = b.sents()
        if len(ss) < 2:
            continue
        (a1, e1), (a2, e2) = ss[-2], ss[-1]
        s1, s2 = b.text[a1:e1], b.text[a2:e2]
        if not (2 <= nwords(s1) <= mx and 2 <= nwords(s2) <= mx) or carries_fact(s2) or s2.rstrip("\"')*_").endswith("?"):
            continue
        w1 = {w for w in re.findall(r"[a-z']+", s1.lower()) if len(w) >= 4 and w not in ECHO_STOP}
        w2 = {w for w in re.findall(r"[a-z']+", s2.lower()) if len(w) >= 4 and w not in ECHO_STOP}
        if ((w1 & w2) and ECHO_PAYOFF.search(s2)) or ECHO_FLIP.search(s2):
            yield mk(doc, rule, b.omap[a1], s1 + " " + s2, "prose")


# ---------------------------------------------------------------------------
# Nominations for the judge pass (high recall, low precision, no word lists)
# ---------------------------------------------------------------------------

COPULA_RE = re.compile(r"\b(?:is|are|was|were|becomes?|remains?)\s+(?:a|an|the|where|what|how|about|less|more)\b", re.I)
UNIVERSAL_RE = re.compile(r"^(?:every|all|most|many|no|great|good|the best|the worst|nothing|everything|anyone|"
                          r"nobody|people|teams|leaders|customers|beginners|founders|children|parents)\b", re.I)
CONTRAST_RE = re.compile(r"\b(?:not|never|n't|less|more than|rather than|instead of)\b", re.I)


def sentence_features(doc, blk, i, n_blocks_pos):
    ss = blk.sents()
    a, e = ss[i]
    s = blk.text[a:e]
    prev = blk.text[ss[i - 1][0]:ss[i - 1][1]] if i else ""
    w = nwords(s)
    feats = []
    fact = carries_fact(s)
    generic = not fact and not re.search(r"\b(?:i|we|my|our|us)\b", s, re.I)
    if generic and COPULA_RE.search(s):
        feats.append("copula-claim")
    if generic and i == len(ss) - 1 and len(ss) >= 2:
        feats.append("paragraph-final-generic")
    if generic and w <= 10 and len(ss) >= 2:
        feats.append("short-generic")
    if generic and UNIVERSAL_RE.search(s):
        feats.append("universal-claim")
    if CONTRAST_RE.search(s) and (CONTRAST_RE.search(prev) or i + 1 < len(ss)) and not fact:
        feats.append("contrast")
    if prev and w <= 10 and nwords(prev) <= 10 and not fact:
        feats.append("parallel-pair")
    if generic and re.search(r"\b(?:is|are) (?:a|an) [\w'-]+(?: [\w'-]+){0,3} (?:in|of|on|for|that|which|where|between|at)\b", s, re.I):
        feats.append("image-predicate")
    if i and INFER_RE.search(s) and FIG_PREV.search(prev):
        feats.append("inference-restatement")
    if re.search(r",\s+(?:allowing|enabling|helping|letting|ensuring|driving|fueling|leading to|resulting in|making it \w+)\b", s, re.I):
        feats.append("causal-glue")
    return s, feats


# The judge reads every block. These kinds are someone else's words, or words repeated on purpose: the judge flags
# slop in them so the author knows it is there, and suggests no change.
JUDGE_FLAG_ONLY = {"quote", "dialogue", "pull quote"}
JUDGE_KIND = {"prose": "prose", "list": "list", "heading": "heading", "title": "title", "quote": "quote",
              "table": "table", "footnote": "footnote", "ui": "ui string"}


def unit_kind(b):
    if "dialogue" in b.roles:
        return "dialogue"
    if "pullquote" in b.roles:
        return "pull quote"
    if "summary" in b.roles:
        return "summary box"
    if b.roles & {"nav", "select"}:
        return "navigation"
    if b.fm:
        return "title"
    return JUDGE_KIND.get(b.ctx, b.ctx)


def judge_units(doc):
    """Every block with a sentence in it, in document order. Runs of list items are grouped as one unit. A unit
    with a link or footnote is marked cited: a source weighs against a finding but does not clear the sentences
    around it. Quotes, dialogue and pull quotes are flag-only."""
    units, prev = [], None
    for b in doc.blocks:
        if not b.sents():
            continue
        kind = unit_kind(b)
        if kind == "list" and prev is not None and prev["kind"] == "list":
            prev["blocks"].append(b)
            prev["cited"] = prev["cited"] or b.cite
            continue
        prev = {"kind": kind, "blocks": [b], "cited": b.cite, "holes": b.holes}
        units.append(prev)
    return units


def nominations(doc):
    """Per unit: its kind, its position in the body (opener, middle, closer) for prose and lists, whether the judge
    may suggest a change, and its sentences with the structural features that make each worth a second look. A
    feature is a nomination, not a finding. The judge pass decides."""
    units = judge_units(doc)
    body = [u for u in units if u["kind"] in ("prose", "list")]
    out = []
    for pi, u in enumerate(units):
        if u["kind"] in ("prose", "list"):
            bi = body.index(u)
            pos = "opener" if bi == 0 else ("closer" if bi == len(body) - 1 else "middle")
        else:
            pos = u["kind"]
        sents, i = [], 0
        for b in u["blocks"]:
            for k in range(len(b.sents())):
                s, feats = sentence_features(doc, b, k, pos)
                sents.append({"i": i, "text": s, "features": feats})
                i += 1
        out.append({"para": pi, "position": pos, "kind": u["kind"], "flag_only": u["kind"] in JUDGE_FLAG_ONLY,
                    "repeats_body": u["kind"] in ("pull quote", "summary box"), "cited": bool(u["cited"]),
                    "line": doc.pos(u["blocks"][0].omap[0])[0], "sentences": sents})
    return out


def judge_coverage(doc, noms):
    """How much of the document's text the judge will see. Every block counts, so a heading or a summary box the
    judge skipped would lower the share."""
    body = sum(nwords(b.text) for b in doc.blocks)
    judged = sum(nwords(s["text"]) for p in noms for s in p["sentences"])
    return {"judged_words": judged, "body_words": body, "share": round(judged / body, 2) if body else 0.0}


INFER_RE = re.compile(r"^(?:(?:that|this|which|it)\s+(?:means|shows|demonstrates|suggests|proves|indicates|highlights|"
                      r"reflects|signals|confirms)\b|(?:clearly|obviously|evidently|naturally),?\s)", re.I)
FIG_PREV = re.compile(r"\d")


def chk_inference(rule, doc):
    """A sentence that restates the conclusion a reader draws from the figure in the sentence before it."""
    for b in doc.blocks:
        if (b.ctx != "prose" or b.fm or b.cite or b.holes
                or b.roles & {"dialogue", "summary", "pullquote", "nav", "select"}):
            continue
        ss = b.sents()
        for i in range(1, len(ss)):
            prev = b.text[ss[i - 1][0]:ss[i - 1][1]]
            cur = b.text[ss[i][0]:ss[i][1]]
            if INFER_RE.search(cur) and FIG_PREV.search(prev):
                yield mk(doc, rule, b.omap[ss[i][0]], cur, "prose")


def chk_directives(rule, doc):
    """Suppression has to be visible: a slop-ok with no rule id, an unknown id, an off region that
    never ends, and any directive in plain-text copy, where the comment ships with the text."""
    for li, off, kind, ids in doc.directives:
        end = doc.src.find("\n", off)
        text = doc.src[off:end if end >= 0 else len(doc.src)][:80]
        if kind == "ok" and not ids:
            yield mk(doc, rule, off, text, "raw", "slop-ok without a rule id suppresses nothing. Name the rule: "
                                                  "slop-ok: rule-id (reason).")
        unknown = [i for i in ids if KNOWN_IDS and i not in KNOWN_IDS]
        if unknown:
            yield mk(doc, rule, off, text, "raw", "slop-ok names a rule that does not exist: %s (see --list-rules)."
                     % ", ".join(unknown))
        if doc.dest == "plain":
            yield mk(doc, rule, off, text, "raw", "A linter directive in plain-text copy ships with the text. Remove "
                                                  "it; to accept a finding for one run, pass --ignore=rule-id.")
    if doc.off_unclosed is not None:
        f = mk(doc, rule, doc.off_unclosed, doc.src[doc.off_unclosed:doc.off_unclosed + 40], "raw",
               "slop-lint off has no matching on, so the rest of the file (%d lines) is not checked."
               % (doc.src.count("\n", doc.off_unclosed, len(doc.src.rstrip("\n"))) + 1))
        yield f


def allowed_hit(match, words):
    """True when the matched text contains a word from allowed_words, in any common form:
    'leverage' covers leveraged and leveraging, 'synergy' covers synergies, 'circle back' is a phrase,
    and a trailing * matches any ending."""
    low = match.lower()
    toks = re.findall(r"[a-z][a-z']*", low)
    for w in words:
        w = w.lower().strip()
        if not w:
            continue
        if " " in w:
            if re.search(r"(?<![\w-])" + re.escape(w).replace(r"\ ", r"\s+") + r"(?![\w-])", low):
                return True
            continue
        if w.endswith("*"):
            if any(t.startswith(w[:-1]) for t in toks):
                return True
            continue
        stems = {w}
        if w.endswith("e"):
            stems.add(w[:-1])
        if w.endswith("y"):
            stems.add(w[:-1] + "i")
        if re.search(r"[^aeiou][aeiou][bdgklmnprt]$", w):
            stems.add(w + w[-1])
        ends = ("", "s", "es", "d", "ed", "ing", "er", "ers", "ly", "ment", "ments", "ness", "ion", "ions", "al")
        if any(t == s + e for t in toks for s in stems for e in ends):
            return True
    return False


ENGINE = {"fragment-run": chk_fragment_run, "anaphora": chk_anaphora, "option-overload": chk_option_overload,
          "content-duplication": chk_duplication, "broetry": chk_broetry, "sentence-length-cv": chk_sentence_cv,
          "paragraph-shape-cv": chk_paragraph_cv, "short-closers": chk_short_closers,
          "unsourced-figure": chk_unsourced, "stapled-ending": chk_stapled, "retired": chk_retired,
          "closer-no-fact": chk_closer_no_fact, "echo-pair": chk_echo_pair,
          "inference": chk_inference, "directives": chk_directives}


def doc_words(doc):
    if not hasattr(doc, "_words"):
        doc._words = sum(nwords(b.text) for b in doc.blocks)
    return doc._words


def lint_doc(doc, rules, policy=None):
    """policy: None or {"mode": "ban"|"density", "min": N}. In density mode, rhetorical-device rules show as
    information unless the piece uses at least N of them: one X-not-Y is a choice, a pattern of them is a tell."""
    out = []
    words = doc_words(doc)
    path = doc.path.replace("\\", "/")
    for rule in rules:
        if rule.kind == "manual" or (rule.kinds and doc.kind not in rule.kinds):
            continue
        if rule.skip_paths and rule.skip_paths.search(path):
            continue
        found = []
        if rule.patterns:
            if rule.target == "raw":
                for off, text in raw_hits(rule, doc):
                    found.append(mk(doc, rule, off, text, "raw"))
            else:
                for blk, a, b in pattern_hits(rule, doc):
                    found.append(mk(doc, rule, blk.omap[a], blk.text[a:b], blk.ctx))
        if rule.check:
            found.extend(ENGINE[rule.check](rule, doc))
        if rule.allow:
            found = [f for f in found if not allowed_hit(f.match, rule.allow)]
        if rule.kind == "density" and found:
            dn = rule.density or {}
            n = len(found)
            rate = n * 1000.0 / max(1, words)
            if n >= dn.get("min_count", 1) and rate > dn.get("per_1000", 0):
                f = found[0]
                f.hits = [(x.line, x.col, x.match) for x in found]
                f.match = "%d hits" % n
                f.message = rule.d["message"] + " (%d in %d words, %.1f per 1000; threshold %s per 1000, min %d)" % (
                    n, words, rate, dn.get("per_1000", 0), dn.get("min_count", 1))
                f.doc_level = True
                out.append(f)
            continue
        out.extend(found)
    kept = []
    for f in out:
        ids = doc.suppress.get(f.line, set()) | doc.suppress.get(f.line - 1, set())
        if f.rule in ids:
            doc.suppressed[f.rule] = doc.suppressed.get(f.rule, 0) + 1
            continue
        kept.append(f)
    if policy and policy.get("mode") == "density":
        dev = [f for f in kept if f.device and f.severity != "info"]
        # scope "piece": devices of every kind count together; "rule": each device is counted on its own.
        groups = {}
        for f in dev:
            groups.setdefault(f.rule if policy.get("scope") == "rule" else "all", []).append(f)
        for grp in groups.values():
            if len(grp) < policy.get("min", 2):
                for f in grp:
                    f.severity = "info"
                    f.message = "Single use, fine unless repeated: " + f.message
    kept.sort(key=lambda f: (f.line, f.col, -SEV_RANK[f.severity], f.rule))
    return kept


def metrics(doc):
    lens = prose_sentence_lengths(doc)
    paras = [b for b in doc.blocks if b.ctx == "prose" and not b.fm]
    m = {"words": doc_words(doc), "blocks": len(doc.blocks), "prose_paragraphs": len(paras),
         "prose_sentences": len(lens)}
    if lens:
        mean = statistics.mean(lens)
        m["sentence_mean_words"] = round(mean, 1)
        m["sentence_length_cv"] = round(statistics.pstdev(lens) / mean, 2) if mean else 0
    m["short_closers"] = len(short_closers(doc, 8))
    return m


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def walk(paths):
    files = []
    for p in paths:
        if p == "-":
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
                for nm in sorted(names):
                    low = nm.lower()
                    if low.endswith(ALL_EXT) and not low.endswith((".min.js", ".d.ts")):
                        files.append(os.path.join(root, nm))
                    elif (low.endswith(".json") and not CONFIG_JSON_RE.match(nm)
                          and (LOCALE_FILE_RE.match(nm) or os.path.basename(root).lower() in LOCALE_DIRS)):
                        files.append(os.path.join(root, nm))
        else:
            files.append(p)
    return files


def fingerprint(f):
    key = "doc" if f.doc_level else re.sub(r"\s+", " ", f.match.lower()).strip()[:60].strip()
    path = f.path if f.path == "<stdin>" else os.path.relpath(f.path).replace(os.sep, "/")
    return "%s\t%s\t%s" % (f.rule, path, key)


def ascii_safe(s):
    return s.encode("ascii", "backslashreplace").decode("ascii")


def print_text(findings, verbose, per_file_metrics):
    for f in findings:
        sev = {"error": "error", "warn": "warning", "info": "info"}[f.severity]
        tag = f.rule + (" | house style" if f.cls == "house_style" else "")
        print("%s:%d:%d: %s [%s] %s" % (f.path, f.line, f.col, sev, tag, ascii_safe(f.message)))
        if not f.doc_level:
            print("    > " + ascii_safe(f.match))
        if f.fix and (f.severity != "info" or verbose):
            print("    fix: " + ascii_safe(f.fix))
        if verbose and f.hits:
            for hl, hc, ht in f.hits[:200]:
                print("      - %d:%d %s" % (hl, hc, ascii_safe(ht)))
    if verbose:
        for path, m in per_file_metrics:
            print("%s: metrics %s" % (path, json.dumps(m)))


# The same twelve items as the "Review checklist" in speakhuman-long/SKILL.md; run_tests.py fails if they drift.
REVIEW_ITEMS = [
    "Does the last paragraph use a number, person or fact from the piece? If it could close any article, cut it.",
    "Read the last sentence of every paragraph. Could it go with no fact lost? Then it goes. Keep three short "
    "closers at most, and only where they argue.",
    "Does any section end by restating itself or reaching for significance? Cut the restatement.",
    "Is any image doing the work a plain claim should do, or saying something mechanically false? State the claim, "
    "then keep the image only if it still earns its place.",
    "Was a frame dropped during drafting? List its words as retired and rename every label that depended on it.",
    "Check the dates of the last one or two pieces. A shared spine metaphor or signature device means pick another.",
    "Does any paragraph repeat a number or claim already made, in new words? Keep the version that gives the reader "
    "something to act on.",
    "Read three paragraphs aloud. Same length, same shape, same closer each time? Vary it. The "
    "`uniform-sentence-length` figure helps.",
    "Would the author say this about themselves and their work? No borrowed frames, no scrambling-job-seeker tone. "
    "When unsure, use their words or ask.",
    "Does each figure have a clear provenance: a source for external facts, a stated basis for calculations, a label "
    "on illustrations?",
    "Does each list or set of options have a reason for its count, with no item added to reach three?",
    "Does the call to action match the profile's `cta_line`, with no timeframe promise?",
]
REVIEW_CHECKLIST = ("\nHuman review (the linter cannot do these; answer each before you show the piece):\n" +
                    "\n".join("%3d. %s" % (k, t) for k, t in enumerate(REVIEW_ITEMS, start=1)))


def usage_error(msg):
    sys.stderr.write("speakhuman: %s\n" % msg)
    sys.stderr.write("usage: speakhuman_lint.py <files-or-dirs|-> [--format=text|json] [--strict] [--verbose] "
                     "[--min-severity=error|warn|info] [--only=ids] [--ignore=ids] [--baseline=F] "
                     "[--write-baseline=F] [--dest=markdown|plain] [--profile=F] [--voice] [--nominate] [--checklist] "
                     "[--list-rules]\n")
    return 2


def main(argv):
    fmt, strict, verbose, min_sev = "text", False, False, "info"
    only, ignore, baseline, write_bl, dest, list_rules = [], [], None, None, None, False
    profile_arg, show_check, nominate, voice = None, False, False, False
    paths, unknown = [], []
    for a in argv:
        if a.startswith("--format="):
            fmt = a.split("=", 1)[1]
        elif a in ("--strict", "-s"):
            strict = True
        elif a in ("--verbose", "-v"):
            verbose = True
        elif a.startswith("--min-severity="):
            min_sev = a.split("=", 1)[1]
            min_sev = "warn" if min_sev == "warning" else min_sev
        elif a.startswith("--only="):
            only += [x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()]
        elif a.startswith("--ignore="):
            ignore += [x.strip() for x in a.split("=", 1)[1].split(",") if x.strip()]
        elif a.startswith("--baseline="):
            baseline = a.split("=", 1)[1]
        elif a.startswith("--write-baseline="):
            write_bl = a.split("=", 1)[1]
        elif a.startswith("--dest="):
            dest = a.split("=", 1)[1]
        elif a.startswith("--profile="):
            profile_arg = a.split("=", 1)[1]
        elif a == "--nominate":
            nominate = True
        elif a == "--checklist":
            show_check = True
        elif a == "--voice":
            voice = True
        elif a == "--list-rules":
            list_rules = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a == "-" or not a.startswith("-"):
            paths.append(a)
        else:
            unknown.append(a)
    if unknown:
        return usage_error("unknown option(s): " + " ".join(unknown))
    if fmt not in ("text", "json"):
        return usage_error("--format must be text or json")
    if min_sev not in SEV_RANK:
        return usage_error("--min-severity must be error, warn (or warning) or info")
    if dest not in (None, "markdown", "plain"):
        return usage_error("--dest must be markdown or plain")
    try:
        prof, prof_path = load_profile(profile_arg)
    except (OSError, ValueError) as e:
        sys.stderr.write("speakhuman: cannot load the profile: %s\n" % e)
        return 2
    if voice:
        return print_voice(prof, prof_path)
    _, voice_problem = voice_path(prof, prof_path)
    if voice_problem:
        sys.stderr.write("speakhuman: %s\n" % voice_problem)
    try:
        rules = load_rules(profile=prof)
    except ValueError as e:
        # apply_profile raises ValueError for a bad value in the profile; json raises it for a broken rules file
        what = "the rules file %s" % RULES_PATH if isinstance(e, json.JSONDecodeError) else "the profile %s" % prof_path
        sys.stderr.write("speakhuman: cannot load %s: %s\n" % (what, e))
        return 2
    except (OSError, re.error) as e:
        sys.stderr.write("speakhuman: cannot load the rules file %s: %s\n" % (RULES_PATH, e))
        return 2
    known = {r.id for r in rules}
    for pat in only + ignore:
        if not any(fnmatch.fnmatch(i, pat) for i in known):
            return usage_error("no rule matches '%s' (see --list-rules)" % pat)
    if only:
        rules = [r for r in rules if any(fnmatch.fnmatch(r.id, p) for p in only)]
    if ignore:
        rules = [r for r in rules if not any(fnmatch.fnmatch(r.id, p) for p in ignore)]

    if list_rules:
        if fmt == "json":
            print(json.dumps([r.d for r in rules], indent=1))
        else:
            print("%-32s %-7s %-8s %-12s %-19s %s" % ("id", "sev", "kind", "class", "category", "name"))
            for r in rules:
                print("%-32s %-7s %-8s %-12s %-19s %s" % (r.id, r.severity, r.kind, r.d.get("class", "pattern"),
                                                           r.d.get("category", ""), r.d.get("name", "")))
        return 0
    if not paths:
        return usage_error("no input (pass files, directories, or - for stdin)")
    missing = [p for p in paths if p != "-" and not os.path.exists(p)]
    if missing:
        return usage_error("path(s) not found: " + " ".join(missing))

    files = walk(paths)
    readable = [f for f in files if f == "-" or os.path.getsize(f) <= MAX_BYTES]
    for f in files:
        if f not in readable:
            sys.stderr.write("speakhuman: skipped %s: larger than %d MB\n" % (f, MAX_BYTES // 1_000_000))
    if not readable:
        sys.stderr.write("speakhuman: nothing was checked: %s\n" % (
            "every file was larger than %d MB" % (MAX_BYTES // 1_000_000) if files else
            "no file under %s is one the linter reads (markdown, text, HTML, Astro, Vue, Svelte, JS or TS, "
            "locale JSON)" % " ".join(paths)))
        return 2
    skipped = [f for f in files if f not in readable]
    if nominate:
        outn = []
        for path in readable:
            src = sys.stdin.read() if path == "-" else open(path, encoding="utf-8", errors="replace").read()
            doc = read_doc("<stdin>" if path == "-" else path, src, dest)
            noms = nominations(doc)
            outn.append({"file": doc.path, "paragraphs": noms, "coverage": judge_coverage(doc, noms)})
        print(json.dumps(outn if len(outn) != 1 else outn[0], indent=1, ensure_ascii=True))
        return 0
    findings, per_file, total_words, n_supp, n_off, not_english = [], [], 0, 0, 0, 0
    for path in readable:
        if path == "-":
            src, name = sys.stdin.read(), "<stdin>"
        else:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    src = fh.read()
            except OSError as e:
                sys.stderr.write("speakhuman: cannot read %s: %s\n" % (path, e))
                return 2
            name = path
        doc = read_doc(name, src, dest)
        doc.retired = list(doc.retired) + list(prof.get("retired_terms") or [])
        fs = lint_doc(doc, rules, {"mode": prof.get("device_policy", "density"), "min": prof.get("device_min", 2),
                                   "scope": prof.get("device_scope", "piece")})
        findings.extend(fs)
        m = metrics(doc)
        m["suppressed"], m["off_lines"] = sum(doc.suppressed.values()), doc.off_lines
        n_supp += m["suppressed"]
        n_off += doc.off_lines
        not_english += doc.not_english
        total_words += m["words"]
        per_file.append((name, m))
    findings = [f for f in findings if SEV_RANK[f.severity] >= SEV_RANK[min_sev]]

    if write_bl is not None:
        fps = sorted({fingerprint(f) for f in findings})
        with open(write_bl, "w", encoding="utf-8") as fh:
            fh.write("# speakhuman baseline: accepted findings. Only findings NOT listed here are reported.\n")
            fh.write("# Regenerate: speakhuman_lint.py --write-baseline=%s %s\n" % (write_bl, " ".join(paths)))
            for fp in fps:
                fh.write(fp + "\n")
        print("speakhuman: wrote %d baseline fingerprints to %s" % (len(fps), write_bl))
        return 0
    n_base = 0
    if baseline is not None:
        try:
            with open(baseline, "r", encoding="utf-8") as fh:
                base = {ln.rstrip("\n") for ln in fh if ln.strip() and not ln.startswith("#")}
        except OSError as e:
            return usage_error("cannot read baseline %s: %s" % (baseline, e))
        kept = [f for f in findings if fingerprint(f) not in base]
        n_base = len(findings) - len(kept)
        findings = kept

    ne = sum(1 for f in findings if f.severity == "error")
    nw = sum(1 for f in findings if f.severity == "warn")
    ni = sum(1 for f in findings if f.severity == "info")
    if fmt == "json":
        print(json.dumps({"summary": {"files": len(per_file), "words": total_words, "errors": ne, "warnings": nw,
                                      "info": ni, "baselined": n_base, "suppressed": n_supp, "off_lines": n_off,
                                      "skipped": skipped, "not_english_blocks": not_english, "profile": prof_path},
                          "files": [{"path": p, "metrics": m} for p, m in per_file],
                          "findings": [f.as_dict() for f in findings]}, indent=1, ensure_ascii=True))
    else:
        print_text(findings, verbose, per_file)
        tail = " (%d baselined)" % n_base if baseline is not None else ""
        by_cls = {}
        for f in findings:
            if f.severity != "info":
                by_cls[f.cls] = by_cls.get(f.cls, 0) + 1
        if by_cls:
            print("By class (errors and warnings): " + ", ".join("%s %d" % (k.replace("_", " "), v) for k, v in sorted(by_cls.items())) +
                  (". House style findings are preferences from your profile, not defects." if "house_style" in by_cls else "."))
        if n_supp or n_off:
            print("Suppressed: %d finding(s) by slop-ok, %d line(s) inside slop-lint off regions." % (n_supp, n_off))
        gaps = (["%d file(s) larger than %d MB" % (len(skipped), MAX_BYTES // 1_000_000)] if skipped else []) + \
               (["%d block(s) not in English (SpeakHuman checks English only)" % not_english] if not_english else [])
        if gaps:
            print("Not checked: %s." % ", ".join(gaps))
        print("speakhuman: %d file(s), %d words: %d error(s), %d warning(s), %d info%s. Profile: %s." % (
            len(per_file), total_words, ne, nw, ni, tail,
            "%s (%s)" % (prof.get("name", "default"), prof_path) if prof_path else "built-in defaults"))
    if fmt == "text" and (show_check or total_words >= 800):
        print(REVIEW_CHECKLIST)
    if ne or ((strict or prof.get("fail_on_warnings") is True) and nw):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
