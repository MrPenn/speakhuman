#!/usr/bin/env python3
"""Regenerate references/patterns.md from slop_rules.json.

    python3 tools/build_patterns.py

Run it after you add or change a rule. Entry bodies sit inside slop-lint off and
on markers because they quote banned words on purpose.
"""
import json
import os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
data = json.load(open(os.path.join(ROOT, "slop_rules.json"), encoding="utf-8"))
rules = data["rules"]

CAT_TITLES = {"ui-copy": "UI copy", "claims-evidence": "Claims and evidence", "endings-openings": "Endings and openings",
              "sentence-structure": "Sentence structure", "rhetorical-device": "Rhetorical devices",
              "editing-residue": "Editing residue", "chat-response": "Chat replies", "visual-design": "Visual design",
              "meta-guardrail": "Guardrails", "headline": "Headlines and headings"}
groups = OrderedDict()
for r in rules:
    groups.setdefault(r["category"], []).append(r)


def title(c):
    return CAT_TITLES.get(c, c.replace("-", " ").capitalize())


def anchor(t):
    return t.lower().replace(" ", "-")


def kind_label(r):
    k = r.get("kind", "pattern")
    if k == "engine":
        return "engine:" + r.get("check", "")
    return k


def render():
    """The catalogue as text. tests/run_tests.py compares it with references/patterns.md."""
    sev = {s: sum(1 for r in rules if r["severity"] == s) for s in ("error", "warn", "info")}
    manual = sum(1 for r in rules if r.get("kind") == "manual")
    out = []
    out.append("# Slop pattern catalogue\n")
    out.append("Every pattern the SpeakHuman skills know, grouped by category. Generated from `slop_rules.json` by "
               "`tools/build_patterns.py`; do not edit by hand.\n")
    out.append("How to read an entry: the severity is what the linter reports: `error` for mechanical rules, `warn` for candidates a person has to judge, and `info` for density and "
               "rhythm figures. The kind is how the linter looks for it: `pattern` (regexes), `density` (regex hits per 1,000 "
               "words), `engine:<check>` (a coded check in speakhuman_lint.py), or `manual`, which has no code at all and exists "
               "for the human review checklist.\n")
    out.append("Class says what kind of problem a hit is: `artifact` (model or editor residue), `evidence` (unsupported claims), "
               "`pattern` (common machine-writing moves), `density` (fine once, suspicious repeatedly) or `house_style` (a "
               "preference, not a defect). Switch classes off with `disable_classes` in the profile.\n")
    out.append("Each entry's body sits inside its own slop-lint off and on markers, because it quotes banned words on purpose. "
               "Typographic characters are described by code point so this file stays ASCII.\n")
    out.append("Totals: %d rules by severity: error %d, warn %d, info %d. %d are kind `manual` (no code).\n" % (
        len(rules), sev["error"], sev["warn"], sev["info"], manual))
    out.append("## Contents\n")
    for c, rs in groups.items():
        out.append("- [%s](#%s) (%d)" % (title(c), anchor(title(c)), len(rs)))
    out.append("")
    for c, rs in groups.items():
        out.append("## %s\n" % title(c))
        for r in rs:
            out.append("### `%s`\n" % r["id"])
            out.append("<!-- slop-lint off -->\n")
            note = " (not automated: human review checklist only)" if r.get("kind") == "manual" else ""
            dev = ", rhetorical device (fine once, a tell when repeated)" if r.get("device") else ""
            off = ", off unless a profile lists it in `enable_rules`" if r.get("default_off") else ""
            out.append("**%s.** Class `%s`, severity `%s`, kind `%s`%s%s%s.\n" % (
                r["name"], r.get("class", "pattern"), r["severity"], kind_label(r), dev, off, note))
            out.append(r["message"] + "\n")
            ex = r.get("examples") or {}
            if ex.get("bad"):
                out.append("Bad:\n")
                out += ["- `%s`" % e.replace("\n", " / ").encode("ascii", "backslashreplace").decode() for e in ex["bad"]]
                out.append("")
            if ex.get("good"):
                out.append("Good:\n")
                out += ["- `%s`" % e.replace("\n", " / ").encode("ascii", "backslashreplace").decode() for e in ex["good"]]
                out.append("")
            if r.get("fix"):
                out.append("Fix: " + r["fix"] + "\n")
            if r.get("false_positive_note"):
                out.append("False positives: " + r["false_positive_note"] + "\n")
            if r.get("sources"):
                out.append("Sources: " + "; ".join(r["sources"]) + "\n")
            if r.get("evidence"):
                out.append("Evidence: " + "; ".join(r["evidence"]) + "\n")
            out.append("<!-- slop-lint on -->\n")
    srcs = OrderedDict()
    for r in rules:
        for s in r.get("sources") or []:
            srcs[s] = 1
    out.append("## Sources\n")
    out += ["- " + s for s in srcs]
    out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    open(os.path.join(ROOT, "references", "patterns.md"), "w", encoding="ascii", errors="replace").write(render())
    print("wrote references/patterns.md with %d rules" % len(rules))
