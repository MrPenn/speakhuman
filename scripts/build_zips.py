#!/usr/bin/env python3
"""Build the SpeakHuman zips.

    python3 scripts/build_zips.py [--profile=PATH] [--out=DIR]

Writes to dist/ (or --out):
  speakhuman-short.zip, speakhuman-long.zip, speakhuman-core.zip
      one per skill, each with its folder at the root of the zip: upload all three in claude.ai
      under Settings, Capabilities, Skills.
  speakhuman.zip
      the whole bundle (README and the three folders) to share or to unpack for Claude Code.

--profile=PATH puts that file into speakhuman-core.zip as profile.json, in place of the default,
and the voice_file it names as voice.md (or voice.txt) beside it. claude.ai has no home folder
that persists, so this is how a personal profile reaches it. The bundle zip always carries the
default profile, so a personal one is never shared by accident.

Only the skills' own file types are packaged (.md, .py, .json, .txt). Symlinks, dotfiles such as .env, a voice file
left in speakhuman-core, and any other file type are skipped with a warning. The build stops if
speakhuman-core/profile.json holds personal settings, because every zip would carry them.
"""
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = ("speakhuman-short", "speakhuman-long", "speakhuman-core")
SKIP_DIRS = {"__pycache__", ".git", "dist"}
SKIP_FILES = {".DS_Store"}
SHIP_EXT = (".md", ".py", ".json", ".txt")
# Test data kept on the maintainer's machine only (see speakhuman-core/tests/human/README.md); never packaged.
LOCAL_ONLY = {os.path.join("speakhuman-core", "tests", "human", "enron-sent-mail.json")}
PERSONAL_FIELDS = ("cta_line", "voice_notes", "voice_file", "rejected_phrases", "extra_banned_words", "allowed_words",
                   "retired_terms")


def files_under(folder):
    """The files a skill folder ships: its own file types, no symlinks, no dotfiles, no stray voice file."""
    for base, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for nm in sorted(names):
            path = os.path.join(base, nm)
            if nm in SKIP_FILES or nm.endswith(".pyc"):
                continue
            rel = os.path.relpath(path, ROOT)
            if os.path.islink(path):
                why = "a symlink"
            elif nm.startswith("."):
                why = "a dotfile"
            elif not nm.lower().endswith(SHIP_EXT):
                why = "not a file type the skills use"
            elif rel in LOCAL_ONLY:
                continue
            elif rel in (os.path.join("speakhuman-core", "voice.md"), os.path.join("speakhuman-core", "voice.txt")):
                why = "a voice file; personal voice files are packaged only with --profile"
            else:
                yield path
                continue
            sys.stderr.write("build_zips: skipped %s: %s\n" % (rel, why))


def check_default_profile():
    """Every zip carries speakhuman-core/profile.json, so it must hold no one's personal settings."""
    path = os.path.join(ROOT, "speakhuman-core", "profile.json")
    prof = json.load(open(path, encoding="utf-8"))
    personal = [k for k in PERSONAL_FIELDS if prof.get(k)]
    if personal:
        raise SystemExit("build_zips: speakhuman-core/profile.json holds personal settings (%s). Move them to "
                         "~/.config/speakhuman/profile.json and build a personal core zip with --profile."
                         % ", ".join(personal))


def write_zip(path, entries):
    """entries: (source file or bytes, name inside the zip)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for src, arc in entries:
            if isinstance(src, bytes):
                z.writestr(arc, src)
            else:
                z.write(src, arc)


def personal_files(profile):
    """The profile as it goes into the core zip, plus its voice file renamed to sit beside it.
    The linter's own check (voice_path) decides whether the voice file is acceptable."""
    sys.path.insert(0, os.path.join(ROOT, "speakhuman-core"))
    sys.dont_write_bytecode = True
    import speakhuman_lint as sl
    prof, _ = sl.load_profile(profile)
    raw = json.load(open(profile, encoding="utf-8"))
    extra = []
    path, problem = sl.voice_path(prof, profile)
    if problem:
        raise SystemExit("build_zips: %s" % problem)
    if path:
        name = "voice" + os.path.splitext(path)[1].lower()
        raw["voice_file"] = name
        extra.append((path, "speakhuman-core/" + name))
    return json.dumps(raw, indent=2).encode("utf-8") + b"\n", extra


def main(argv):
    profile = next((a.split("=", 1)[1] for a in argv if a.startswith("--profile=")), None)
    out = next((a.split("=", 1)[1] for a in argv if a.startswith("--out=")), os.path.join(ROOT, "dist"))
    unknown = [a for a in argv if not a.startswith(("--profile=", "--out="))]
    if unknown:
        sys.stderr.write(__doc__)
        return 2
    if profile and not os.path.isfile(profile):
        sys.stderr.write("build_zips: profile not found: %s\n" % profile)
        return 2
    check_default_profile()
    personal, extra = personal_files(profile) if profile else (None, [])
    os.makedirs(out, exist_ok=True)
    bundle = [(os.path.join(ROOT, "README.md"), "speakhuman/README.md")]
    for skill in SKILLS:
        folder = os.path.join(ROOT, skill)
        entries = []
        for src in files_under(folder):
            arc = os.path.relpath(src, ROOT)
            bundle.append((src, "speakhuman/" + arc))
            if personal and arc == os.path.join("speakhuman-core", "profile.json"):
                src = personal
            entries.append((src, arc))
        if skill == "speakhuman-core":
            entries += extra
        write_zip(os.path.join(out, skill + ".zip"), entries)
        print("wrote %s (%d files%s)" % (os.path.join(out, skill + ".zip"), len(entries),
                                         ", profile from " + profile if profile and skill == "speakhuman-core" else ""))
    for src in files_under(os.path.join(ROOT, "scripts")):
        bundle.append((src, "speakhuman/" + os.path.relpath(src, ROOT)))
    write_zip(os.path.join(out, "speakhuman.zip"), bundle)
    print("wrote %s (%d files)" % (os.path.join(out, "speakhuman.zip"), len(bundle)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
