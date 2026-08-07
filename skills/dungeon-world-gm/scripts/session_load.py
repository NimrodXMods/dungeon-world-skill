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
    3. Leaves the character *.yaml files as extracted, untouched.
    4. Prints a short summary (campaign name, session number, pause_state,
       character files found) so you have immediate narrative context without
       necessarily needing to open and re-read the whole gmsecret file.

This script is read-only with respect to campaign state: it does NOT advance
`session_number`. Beginning a new session is an explicit act the GM performs
after confirming that is what the player actually wants (see gameplay-loop.md).
That keeps loading idempotent - re-running it after a sandbox reset, or just to
re-read the pause_state, can never silently skip a session number.

If more than one *_gmsecret.txt is found (shouldn't happen), the first is used
and a warning is printed.
"""
import argparse
import codecs
import os
import sys
import zipfile

import yaml


def main():
    ap = argparse.ArgumentParser(description="Restore a saved DW session.")
    ap.add_argument("zipfile", help="Path to the saved session zip")
    ap.add_argument("--dir", default=".", help="Directory to extract into (default: current dir)")
    args = ap.parse_args()

    os.makedirs(args.dir, exist_ok=True)
    with zipfile.ZipFile(args.zipfile) as zf:
        zf.extractall(args.dir)
        names = zf.namelist()

    secret_files = [n for n in names if n.endswith("_gmsecret.txt")]
    handoff_files = [n for n in names if n.endswith("_handoff.txt")]
    if not secret_files:
        print("ERROR: no *_gmsecret.txt found in the zip", file=sys.stderr)
        sys.exit(1)
    if len(secret_files) > 1:
        print(f"WARNING: multiple gmsecret files found, using {secret_files[0]!r}", file=sys.stderr)
    if not handoff_files:
        print("WARNING: no *_handoff.txt found in the zip", file=sys.stderr)

    # extract/decode gmsecret
    secret_path = os.path.join(args.dir, secret_files[0])
    with open(secret_path) as f:
        encoded_text = f.read()
    plain_text = codecs.encode(encoded_text, "rot13")
    data = yaml.safe_load(plain_text)
    slug = secret_files[0][: -len("_gmsecret.txt")]
    yaml_path = os.path.join(args.dir, f"{slug}_gmsecret.yaml")
    with open(yaml_path, "w") as f:
        f.write(plain_text)
    os.remove(secret_path)

    # extract/decode handoff.md
    for fn in handoff_files:
        handoff_path = os.path.join(args.dir, fn)
        with open(handoff_path) as f:
            encoded_text = f.read()
        plain_text = codecs.encode(encoded_text, "rot13")
        handoff_md_path = os.path.join(args.dir, os.path.basename(fn).replace("_handoff.txt", "_handoff.md"))
        with open(handoff_md_path, "w") as f:
            f.write(plain_text)
        os.remove(handoff_path)

    char_files = sorted(
        n for n in names if n.endswith(".yaml") and not n.endswith("_gmsecret.yaml")
    )

    print(f"Loaded campaign: {data.get('campaign', '(unnamed)')}")
    # The number of the session this save came from. This script never advances
    # it - starting a new session is an explicit act by the GM, so loading is
    # read-only with respect to campaign state and safe to re-run.
    print(f"Loaded Session {data.get('session_number', '?')}.")
    print(f"Working gmsecret: {yaml_path}")
    print(f"Handoff file(s): {', '.join(handoff_files) if handoff_files else '(none)'}")
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
