#!/usr/bin/env python3
"""
session_load.py - restore a Dungeon World session from a saved zip.

Usage:
    python3 session_load.py CAMPAIGN_S3.zip [--dir .]

What it does:
    1. Unzips everything into --dir (default: current directory).
    2. Finds the *_gmsecret.txt inside, rot13-decodes it (rot13 undoes itself),
       and writes it out as <slug>_gmsecret.yaml - a plain-text working copy
       ready to edit with yamledit.pyz or a text editor. The original .txt is
       removed after a successful decode (it's still inside the zip if needed).
       A zip written with `session_save.py --no-rot13` stores those two files
       plainly, as <slug>_gmsecret.yaml and handoff.md. This script tells the
       two apart by FILENAME and decodes only what was encoded.
    3. Extracts the *_environment.yaml file. This is player-facing, so it is
       stored plain and needs no decode.
    4. Character *.yaml and story.md are extracted.
    5. Prints a short summary (campaign name, session number, pause_state,
       character files found) so you have immediate narrative context without
       necessarily needing to open and re-read the whole gmsecret file.

This script is read-only with respect to campaign state: it does NOT advance
`session_number`. Beginning a new session is an explicit act the GM performs
after confirming that is what the player actually wants (see gameplay-loop.md).
That keeps loading idempotent - re-running it after a sandbox reset, or just to
re-read the pause_state, can never silently skip a session number.

If more than one *_gmsecret.txt is found (shouldn't happen), the first is used
and a warning is printed.

Every extracted text file is rewritten with host-native line endings (LF→CRLF
on Windows) so local diffs and editors match after a save→load round trip. Zip
payloads themselves stay LF-canonical.
"""
import argparse
import codecs
import os
import sys
import zipfile

from _util import force_utf8_stdio, normalize_newlines_to_lf, read_text_utf8, write_text_utf8_local

force_utf8_stdio()

# The YAML parser comes out of the vendored zipapp rather than a pip install:
# the target sandbox has nothing installed, and yamledit.pyz is already the one
# dependency this skill is guaranteed to have (session_save.py leans on it too).
_YAMLEDIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yamledit.pyz")
if not os.path.isfile(_YAMLEDIT):
    sys.exit(f"ERROR: yamledit.pyz not found next to this script ({_YAMLEDIT})")
sys.path.insert(0, _YAMLEDIT)
from ruamel.yaml import YAML  # noqa: E402


HELP_LLM = """session_load.py - restore a Dungeon World campaign from a saved zip.

WHAT IT IS
  The inverse of session_save.py. Unpacks a session zip into a working
  directory and leaves every file in the exact shape the play-time scripts and
  yamledit.pyz expect: gmsecret decoded to YAML, handoff back to handoff.md,
  everything rewritten to host-native line endings.

  Call it at the START of a session, on the zip the user hands back.

USAGE
  python3 scripts/session_load.py ZIPFILE [--dir DIR]

  ZIPFILE   The saved session zip (<slug>_s<N>.zip or <slug>_checkpoint.zip).
  --dir     Directory to extract into. Default: current directory.

WHAT IT PRODUCES
  <slug>_gmsecret.yaml     decoded working copy; the .txt is removed after a
                           successful decode (still recoverable from the zip)
  handoff.md               decoded; always this name, whichever way it was saved
  <slug>_environment.yaml  player-visible; extracted as-is
  *.yaml                   character sheets
  story.md                 when the save carried one

  IT TAKES NO ROT13 FLAG. The encoding is read off the filename inside the zip
  (.txt = rot13, .yaml/.md = plain, from --no-rot13). Since rot13 is its own
  inverse, a flag could be set wrong and would corrupt silently rather than
  fail - so there is deliberately nothing to get wrong here.

WHAT IT DOES NOT DO
  It does NOT advance `session_number`. Beginning a new session is an explicit
  act you perform after confirming that is what the user wants, which keeps
  loading idempotent: re-running after a sandbox reset, or just to re-read the
  pause_state, can never silently skip a session. Increment it yourself with
  yamledit.pyz once the user confirms.

OUTPUT
  Prints campaign name, session number, the files found, and the gmsecret's
  `pause_state` (location, situation, open threads) - enough narrative context
  to resume without re-reading the whole gmsecret.

EXIT CODES
  0  restored
  1  no gmsecret of either kind found in the zip

NOTES
  - Missing handoff or environment files are warnings, not errors.
  - Re-running over an existing directory overwrites the working copies.
  - Save again with: python3 scripts/session_save.py <gmsecret> --kind ...
"""

def _load_yaml(text):
    return YAML(typ="safe").load(text)


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return 0

    ap = argparse.ArgumentParser(description="Restore a saved DW session.")
    ap.add_argument("zipfile", help="Path to the saved session zip")
    ap.add_argument("--dir", default=".", help="Directory to extract into (default: current dir)")
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                    help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    os.makedirs(args.dir, exist_ok=True)
    with zipfile.ZipFile(args.zipfile) as zf:
        zf.extractall(args.dir)
        names = zf.namelist()

    # The filename says how the file was stored: .txt is rot13, .yaml/.md is
    # plain (session_save.py --no-rot13). Reading the encoding off the name is
    # what lets this script take no flag - and rot13 is its own inverse, so a
    # wrong guess would silently produce gibberish rather than fail.
    secret_files = [n for n in names if n.endswith("_gmsecret.txt")]
    plain_secret_files = [n for n in names if n.endswith("_gmsecret.yaml")]
    handoff_files = [n for n in names if n.endswith("_handoff.txt")]
    environment_files = [n for n in names if n.endswith("_environment.yaml")]

    plain_handoff = "handoff.md" if "handoff.md" in names else None
    if not secret_files and not plain_secret_files:
        print("ERROR: no *_gmsecret.txt or *_gmsecret.yaml found in the zip",
              file=sys.stderr)
        sys.exit(1)
    if secret_files and plain_secret_files:
        print("WARNING: zip has both an encoded and a plain gmsecret; using the "
              f"encoded {secret_files[0]!r}", file=sys.stderr)
    elif len(secret_files) > 1 or len(plain_secret_files) > 1:
        print("WARNING: multiple gmsecret files found, using "
              f"{(secret_files or plain_secret_files)[0]!r}", file=sys.stderr)
    if not handoff_files and plain_handoff is None:
        print("WARNING: no handoff found in the zip", file=sys.stderr)
    if not environment_files:
        print("WARNING: no environment file found in zip", file=sys.stderr)

    # extract/decode gmsecret — zip payload is UTF-8 LF; write host-native newlines
    if secret_files:
        secret_path = os.path.join(args.dir, secret_files[0])
        plain_text = codecs.encode(
            normalize_newlines_to_lf(read_text_utf8(secret_path)), "rot13")
        slug = secret_files[0][: -len("_gmsecret.txt")]
        yaml_path = os.path.join(args.dir, f"{slug}_gmsecret.yaml")
        write_text_utf8_local(yaml_path, plain_text)
        os.remove(secret_path)
    else:
        # Already plain and already named as the working copy: only the line
        # endings need converting, and there is no .txt to clean up.
        yaml_path = os.path.join(args.dir, plain_secret_files[0])
        plain_text = normalize_newlines_to_lf(read_text_utf8(yaml_path))
        write_text_utf8_local(yaml_path, plain_text)
    data = _load_yaml(plain_text)

    # extract/decode handoff — encoded zip name is <slug>_handoff.txt; working
    # file is always handoff.md (session_save looks for that basename next to
    # the gmsecret), which is also what a --no-rot13 zip stores it as.
    for fn in handoff_files:
        handoff_path = os.path.join(args.dir, fn)
        encoded_text = normalize_newlines_to_lf(read_text_utf8(handoff_path))
        plain_text = codecs.encode(encoded_text, "rot13")
        write_text_utf8_local(os.path.join(args.dir, "handoff.md"), plain_text)
        os.remove(handoff_path)
    if plain_handoff:
        handoff_path = os.path.join(args.dir, "handoff.md")
        write_text_utf8_local(handoff_path, read_text_utf8(handoff_path))

    # Character sheets and story.md were extracted binary-as-stored (LF in zip).
    # Rewrite to host-native newlines so Windows editors and diffs match local
    # working copies after save→load.
    char_files = sorted(
        n for n in names if n.endswith(".yaml") and not
            ( n.endswith("_gmsecret.yaml") or n.endswith("_environment.yaml") )
    )
    for n in char_files:
        p = os.path.join(args.dir, n)
        if os.path.isfile(p):
            write_text_utf8_local(p, read_text_utf8(p))

    # The environment file gets its own pass rather than riding along with the
    # character sheets: it is not a character (it must not be counted as one in
    # the summary, or a campaign with no PCs looks like it has one), but it is
    # still a working YAML the GM edits, so it needs the same LF->host rewrite.
    for n in environment_files:
        p = os.path.join(args.dir, n)
        if os.path.isfile(p):
            write_text_utf8_local(p, read_text_utf8(p))

    story_path = os.path.join(args.dir, "story.md")
    if os.path.isfile(story_path):
        write_text_utf8_local(story_path, read_text_utf8(story_path))

    campaign = data.get("campaign_slug") or data.get("campaign") or "(unnamed)"
    print(f"Loaded campaign: {campaign}")
    # The number of the session this save came from. This script never advances
    # it - starting a new session is an explicit act by the GM, so loading is
    # read-only with respect to campaign state and safe to re-run.
    print(f"Loaded Session {data.get('session_number', '?')}.")
    print(f"Working gmsecret: {yaml_path}")
    found_handoff = handoff_files + ([plain_handoff] if plain_handoff else [])
    print(f"Handoff file(s): {', '.join(found_handoff) if found_handoff else '(none)'}")
    print(f"Environment file: {environment_files[0] if environment_files else '(none)'}")
    print(f"Character sheets found: {', '.join(char_files) if char_files else '(none)'}")
    print(f"Warning: Don't forget to increment the session number and inform the user when beginning a new session.")

    pause = data.get("pause_state")
    if pause:
        print("\n--- pause_state ---")
        loc = pause.get("location")
        if loc:
            print(f"Location: {loc}")
        situation = pause.get("situation")
        if situation:
            print(f"Situation:\n{situation}")
        threads = pause.get("open_threads")
        if threads:
            print("Open threads:")
            for t in threads:
                print(f"  - {t}")


if __name__ == "__main__":
    main()
