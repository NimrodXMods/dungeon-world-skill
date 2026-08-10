#!/usr/bin/env python3
"""
session_save.py - package a Dungeon World session for download.

Usage:
    python3 session_save.py CAMPAIGN_GMSECRET.yaml --kind session_end
    python3 session_save.py CAMPAIGN_GMSECRET.yaml --kind checkpoint

What it does:
    1. Reads `campaign_slug` and `session_number` from the gmsecret via
       yamledit.pyz, purely to build the output filename.
    2. Rot13-encodes a COPY of the gmsecret file's raw text and writes it into
       the zip as <slug>_gmsecret.txt. The working .yaml is left untouched on
       disk in plain text for you to keep editing.
    3. Bundles handoff.md (rot13'd) and every character *.yaml in the same
       directory into the zip, unmodified. story.md, if present, goes in as
       plain text - it is the narrative the player already saw, so unlike the
       gmsecret and handoff there is nothing in it to spoil.

       handoff.md is required for --kind session_end and optional for a
       checkpoint, which is taken mid-session before one exists.
    4. Prints the output path. You still need to call present_files/whatever
       your environment uses to actually hand the zip to the user - this
       script only builds it.

This script NEVER writes to the gmsecret. It does not touch `session_number`:
advancing that is an explicit act performed at the START of a session, once the
GM has confirmed a new session is actually beginning (see gameplay-loop.md), not
a side effect of packaging. So <slug>_s3.zip contains session_number: 3 - the
filename and the contents agree, and re-running this script is harmless.

It also never re-serialises the YAML. The gmsecret is treated as an opaque
string, so the explanatory comments in the file survive a save/load round trip;
dumping it through a YAML library would silently strip every one of them.

The campaign "slug" is derived from the `campaign_slug:` field in the YAML
(lowercased, spaces -> underscores, non-alnum stripped) unless --slug is
given explicitly.
"""
import argparse
import codecs
import glob
import json
import os
import re
import subprocess
import sys
import zipfile

from _util import force_utf8_stdio

force_utf8_stdio()

YAMLEDIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yamledit.pyz")

STORY_FILENAME = "story.md"


def read_fields(path, fields):
    """Read scalars from a YAML file via yamledit. Missing keys come back None."""
    if not os.path.exists(YAMLEDIT):
        sys.exit(f"ERROR: yamledit.pyz not found next to this script ({YAMLEDIT})")
    out = {f: None for f in fields}
    for field in fields:
        proc = subprocess.run(
            [sys.executable, YAMLEDIT, path, "--script", "-", "--json"],
            input=f"{field} -> ?\n", capture_output=True, text=True)
        if proc.returncode != 0:
            continue  # absent key; caller decides whether that is fatal
        try:
            records = json.loads(proc.stdout).get("records", [])
        except ValueError:
            continue
        if records:
            out[field] = records[0].get("value")
    return out


def slugify(name):
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def main():
    ap = argparse.ArgumentParser(description="Package a DW session for download.")
    ap.add_argument("gmsecret", help="Path to the plain-text gmsecret YAML working copy")
    ap.add_argument("--kind", choices=["session_end", "checkpoint"], required=True)
    ap.add_argument("--slug", default=None, help="Override the campaign slug used in filenames")
    ap.add_argument("--dir", default=None,
                     help="Directory to look for character *.yaml files in (default: gmsecret's directory)")
    ap.add_argument("--outdir", default=".", help="Where to write the zip (default: current dir)")
    args = ap.parse_args()

    # `campaign_slug` is the key the template and schema define; `campaign` is
    # accepted as a fallback for files written before that was settled.
    fields = read_fields(
        args.gmsecret, ["campaign_slug", "campaign", "session_number", "maintain_story"]
    )

    campaign = fields["campaign_slug"] or fields["campaign"]
    if not campaign and not args.slug:
        print("WARNING: gmsecret has no `campaign_slug`; falling back to "
              "'campaign' in filenames. Set it, or pass --slug.", file=sys.stderr)
    slug = args.slug or slugify(campaign or "campaign")
    char_dir = args.dir or (os.path.dirname(os.path.abspath(args.gmsecret)) or ".")

    if args.kind == "session_end":
        session_n = fields["session_number"]
        if session_n is None:
            sys.exit("ERROR: gmsecret has no `session_number`; cannot name the "
                     "session zip. The schema requires this key.")
        print(f"Session number is {session_n}.")
        zip_name = f"{slug}_s{session_n}.zip"
    else:
        zip_name = f"{slug}_checkpoint.zip"

    # Rot13 the gmsecret's raw text. Deliberately not re-serialised: a YAML
    # round trip would strip every comment out of the working file.
    with open(args.gmsecret) as f:
        encoded_gmsecret_text = codecs.encode(f.read(), "rot13")

    # encode handoff.md. Required at session end - that is the file the next
    # session picks up from - but a checkpoint is a mid-session snapshot taken
    # before any handoff exists, so there it is merely absent.
    print(f"Looking for handoff.md in {char_dir}...")
    encoded_handoff_text = None
    handoff_path = os.path.join(char_dir, "handoff.md")
    if os.path.exists(handoff_path):
        with open(handoff_path) as f:
            plain_text = f.read()
        encoded_handoff_text = codecs.encode(plain_text, "rot13")
    elif args.kind == "session_end":
        sys.exit(f"ERROR: no handoff.md found in {char_dir}. Write one before "
                 f"ending the session, or pass --dir if it lives elsewhere.")
    else:
        print("No handoff.md found, skipping (checkpoint).")

    char_files = sorted(
        p for p in glob.glob(os.path.join(char_dir, "*.yaml"))
        if not os.path.basename(p).endswith("_gmsecret.yaml")
    )

    # story.md rides along in plain text, unlike the gmsecret and handoff: it is
    # the narrative the player has already lived through, so there is nothing in
    # it to spoil. Only nag about a missing one when the campaign opted in.
    story_path = os.path.join(char_dir, STORY_FILENAME)
    has_story = os.path.exists(story_path)
    if not has_story and fields["maintain_story"]:
        print(f"Warning: maintain_story is set but no {STORY_FILENAME} found in {char_dir}",
              file=sys.stderr)

    zip_path = os.path.join(args.outdir, zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{slug}_gmsecret.txt", encoded_gmsecret_text)
        if encoded_handoff_text is not None:
            zf.writestr(f"{slug}_handoff.txt", encoded_handoff_text)
        for cf in char_files:
            zf.write(cf, arcname=os.path.basename(cf))
        if has_story:
            # arcname keeps it at the top of the zip; without it the whole
            # source path would be stored and extract to the wrong place.
            zf.write(story_path, arcname=STORY_FILENAME)

    print(f"Wrote {zip_path}")
    print(f"  - {slug}_gmsecret.txt (rot13-encoded)")
    if encoded_handoff_text is not None:
        print(f"  - {slug}_handoff.txt (rot13-encoded)")
    for cf in char_files:
        print(f"  - {os.path.basename(cf)}")
    if has_story:
        print(f"  - {STORY_FILENAME}")
    if not char_files:
        print("  (no character *.yaml files found alongside the gmsecret - is --dir right?)", file=sys.stderr)


if __name__ == "__main__":
    main()
