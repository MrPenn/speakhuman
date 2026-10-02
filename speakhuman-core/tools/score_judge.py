#!/usr/bin/env python3
"""Score judge verdicts against labeled slop.

    python3 tools/score_judge.py labels.json verdicts.json

labels.json:   [{"para_id": 1, "text": "...", "slop": [{"sentence": "exact sentence", "shape": "S1"}]}]
verdicts.json: [{"para_id": 1, "verdicts": [{"i": 0, "shape": "S1"}]}]  (i indexes the paragraph's sentences)
Prints per-paragraph recall and false-positive counts, then totals.

The score is refused (exit 1) when the inputs do not line up: a labeled sentence that matches no sentence or more
than one, a duplicate para_id, or a verdict index outside its paragraph. A label that silently failed to match
would leave the denominator and raise the recall. Exit 2 on a usage error.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.dont_write_bytecode = True
import speakhuman_lint as sl  # noqa: E402


def norm(s):
    return re.sub(r"\W+", " ", s).strip().lower()


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    try:
        labels = json.load(open(argv[0], encoding="utf-8"))
        vlist = json.load(open(argv[1], encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.stderr.write("score_judge: %s\n" % e)
        return 2
    problems, verd = [], {}
    for v in vlist:
        if v["para_id"] in verd:
            problems.append("verdicts: para_id %s appears more than once" % v["para_id"])
        verd[v["para_id"]] = v["verdicts"]
    ids = [p["para_id"] for p in labels]
    problems += ["labels: para_id %s appears more than once" % i for i in sorted({i for i in ids if ids.count(i) > 1})]
    tot_slop = tot_hit = tot_fp = tot_clean = 0
    lines = []
    for p in labels:
        doc = sl.read_doc("x.md", p["text"] + "\n")
        blocks = [b for b in doc.blocks if b.ctx == "prose"]
        if len(blocks) != 1:
            problems.append("para %s: the text must be one paragraph, found %d" % (p["para_id"], len(blocks)))
            continue
        blk = blocks[0]
        sents = [blk.text[a:e].strip() for a, e in blk.sents()]
        slop_idx = set()
        for s in p["slop"]:
            key = norm(s["sentence"])
            hits = [i for i, t in enumerate(sents) if key and key in norm(t)]
            if len(hits) != 1:
                problems.append("para %s: label %r matches %d sentences; it must match exactly one"
                                % (p["para_id"], s["sentence"][:60], len(hits)))
            slop_idx.update(hits[:1])
        flagged = set()
        for v in verd.get(p["para_id"], []):
            i = v.get("i")
            if not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < len(sents):
                problems.append("para %s: verdict index %r is outside the paragraph's %d sentences"
                                % (p["para_id"], i, len(sents)))
                continue
            flagged.add(i)
        hit, fp = slop_idx & flagged, flagged - slop_idx
        tot_slop += len(slop_idx)
        tot_hit += len(hit)
        tot_fp += len(fp)
        tot_clean += len(sents) - len(slop_idx)
        lines.append("para %2d: caught %d of %d slop sentences; %d false flag(s) on %d clean sentences" % (
            p["para_id"], len(hit), len(slop_idx), len(fp), len(sents) - len(slop_idx)))
        lines += ["         missed: " + sents[i][:90] for i in sorted(slop_idx - flagged)]
        lines += ["         false:  " + sents[i][:90] for i in sorted(fp)]
    for extra in sorted(set(verd) - set(ids), key=str):
        problems.append("verdicts: para_id %s has no labeled paragraph" % extra)
    if problems:
        print("NOT SCORED: the labels and verdicts do not line up.")
        for pr in problems:
            print("  " + pr)
        return 1
    print("\n".join(lines))
    print("TOTAL: caught %d of %d (%.0f%%); false flags %d of %d clean sentences" % (
        tot_hit, tot_slop, 100.0 * tot_hit / max(1, tot_slop), tot_fp, tot_clean))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
