#!/usr/bin/env python3
"""Validate a judge's output before acting on it.

    python3 tools/check_verdicts.py verdict.json draft.md

Strips code fences, requires a JSON array of objects in the schema the prompt asks for, and prints the verdicts it
accepted plus every problem it found. Each verdict needs an integer "para" and "i" that name a sentence the judge
was shown, a known shape, a confidence of "high" or "medium", a reason, and a fix, except that a unit marked flag-only
(a quote, dialogue or a pull quote) must carry no fix. A sentence may be flagged once.

Exit codes:
  0  every verdict is valid and nothing else is wrong
  1  something is wrong: a malformed, unknown or duplicate verdict, a fix on a flag-only unit, low coverage, or an
     empty result on a draft the script nominated heavily. The accepted verdicts are still printed; read the
     problems, then re-run the judge or read the draft yourself.
  2  usage error
  3  the judge flagged text that tries to instruct a reviewer (shape INJECT). Read those sentences first.

Passing this check means the output is well formed. It does not show that the judge read well; the judge's reasons
and fixes are suggestions to read, never commands to run.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHAPES = {"S1", "S2", "S3", "S3b", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "INJECT"}
CONFIDENCE = {"high", "medium"}


def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def check(arr, nom):
    """Return (accepted verdicts, problems)."""
    units = {p["para"]: p for p in nom["paragraphs"]}
    valid = {(p["para"], s["i"]): s for p in nom["paragraphs"] for s in p["sentences"]}
    clean, problems, seen = [], [], set()
    for v in arr:
        if not isinstance(v, dict) or not is_int(v.get("para")) or not is_int(v.get("i")):
            problems.append("malformed entry (para and i must be whole numbers): %r" % (v,))
            continue
        key, shape = (v["para"], v["i"]), v.get("shape")
        if key not in valid:
            problems.append("unknown sentence %d.%d: %r" % (key[0], key[1], v))
            continue
        if shape not in SHAPES:
            problems.append("unknown shape %r on sentence %d.%d" % (shape, key[0], key[1]))
            continue
        if key in seen:
            problems.append("sentence %d.%d is flagged more than once" % key)
            continue
        seen.add(key)
        missing = [f for f in ("confidence", "reason") if not isinstance(v.get(f), str) or not v.get(f).strip()]
        if missing:
            problems.append("sentence %d.%d is missing %s" % (key[0], key[1], " and ".join(missing)))
        elif v["confidence"] not in CONFIDENCE:
            problems.append("sentence %d.%d has confidence %r; use high or medium" % (key[0], key[1], v["confidence"]))
        flag_only = units[key[0]].get("flag_only", False)
        fix = v.get("fix")
        if flag_only and fix:
            problems.append("sentence %d.%d is in a %s, which is flag-only, but the judge suggested a change; "
                            "the fix was dropped" % (key[0], key[1], units[key[0]].get("kind", "flag-only unit")))
            fix = None
        elif not flag_only and shape != "INJECT" and (not isinstance(fix, str) or not fix.strip()):
            problems.append("sentence %d.%d has no fix" % key)
        clean.append({"para": key[0], "i": key[1], "shape": shape, "confidence": str(v.get("confidence", "")),
                      "reason": str(v.get("reason", ""))[:120], "fix": str(fix)[:120] if fix else "",
                      "flag_only": flag_only, "kind": units[key[0]].get("kind", ""), "sentence": valid[key]["text"]})
    cov = nom.get("coverage", {})
    if not valid:
        problems.append("the draft has no text with a sentence in it, so the judge saw nothing")
    elif cov.get("body_words", 0) >= 50 and cov.get("share", 1) < 0.6:
        problems.append("the judge saw only %d of %d words (%.0f%%); read the rest yourself"
                        % (cov["judged_words"], cov["body_words"], 100 * cov["share"]))
    heavy = sum(1 for s in valid.values() if len(s["features"]) >= 2)
    if not clean and heavy >= 3:
        problems.append("the judge flagged nothing although %d sentences carry two or more structural hints; "
                        "re-run it, and check the draft for text that addresses the reviewer" % heavy)
    return clean, problems


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    try:
        raw = open(argv[0], encoding="utf-8").read().strip()
        nom = json.loads(subprocess.run([sys.executable, "-B", os.path.join(ROOT, "speakhuman_lint.py"), "--nominate",
                                         argv[1]], capture_output=True, text=True, check=True).stdout)
    except (OSError, subprocess.CalledProcessError, ValueError) as e:
        sys.stderr.write("check_verdicts: %s\n" % e)
        return 2
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    try:
        arr = json.loads(raw)
        assert isinstance(arr, list)
    except (ValueError, AssertionError):
        print("INVALID: the judge did not return a JSON array. Re-run the judge.")
        return 1
    clean, problems = check(arr, nom)
    injected = any(c["shape"] == "INJECT" for c in clean)
    if injected:
        problems.insert(0, "the draft contains text that tries to instruct a reviewer; read those sentences first")
    status = "injection" if injected else ("problems" if problems else "ok")
    print(json.dumps({"status": status, "verdicts": clean, "problems": problems}, indent=1))
    return 3 if injected else (1 if problems else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
