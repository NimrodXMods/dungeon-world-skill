#!/usr/bin/env python3
"""
session_save.py - package a Dungeon World session for download.

Usage:
    python3 session_save.py CAMPAIGN_GMSECRET.yaml --kind session_end
    python3 session_save.py CAMPAIGN_GMSECRET.yaml --kind checkpoint

What it does:
    1. Reads `campaign` and `session_number` from the gmsecret via
       yamledit.pyz, purely to build the output filename.
    2. Rot13-encodes a COPY of the gmsecret file's raw text and writes it into
       the zip as <slug>_gmsecret.txt. The working .yaml is left untouched on
       disk in plain text for you to keep editing.
    3. Bundles handoff.md (rot13'd) and every character *.yaml in the same
       directory into the zip, unmodified.
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

The campaign "slug" is derived from the `campaign:` field in the YAML
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

YAMLEDIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yamledit.pyz")


def read_fields(path, fields):
    """Read scalars from a YAML file via yamledit. Missing keys come back None."""
    if not os.path.exists(YAMLEDIT):
        sys.exit(f"ERROR: yamledit.pyz not found next to this script ({YAMLEDIT})")
    out = {f: None for f in fields}
    for field in fields:
        proc = subprocess.run(
            [sys.executable, YAMLEDIT, path, field, "--get", "--json"],
            capture_output=True, text=True)
        if proc.returncode != 0:
            continue  # absent key; caller decides whether that is fatal
        try:
            results = json.loads(proc.stdout).get("results", [])
        except ValueError:
            continue
        if results:
            out[field] = results[0].get("value")
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

    fields = read_fields(args.gmsecret, ["campaign", "session_number"])

    slug = args.slug or slugify(fields["campaign"] or "campaign")
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

    # encode handoff.md
    print(f"Looking for handoff.md in {char_dir}...")
    encoded_handoff_text = None
    if os.path.exists(os.path.join(char_dir, "handoff.md")):
        with open(os.path.join(char_dir, "handoff.md")) as f:
            plain_text = f.read()
        encoded_handoff_text = codecs.encode(plain_text, "rot13")
    else:
        print("No handoff.md found, skipping.")

    char_files = sorted(
        p for p in glob.glob(os.path.join(char_dir, "*.yaml"))
        if not os.path.basename(p).endswith("_gmsecret.yaml")
    )

    zip_path = os.path.join(args.outdir, zip_name)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{slug}_gmsecret.txt", encoded_gmsecret_text)
        if encoded_handoff_text is not None:
            zf.writestr(f"{slug}_handoff.txt", encoded_handoff_text)
        for cf in char_files:
            zf.write(cf, arcname=os.path.basename(cf))

    print(f"Wrote {zip_path}")
    print(f"  - {slug}_gmsecret.txt (rot13-encoded)")
    if encoded_handoff_text is not None:
        print(f"  - {slug}_handoff.txt (rot13-encoded)")
    for cf in char_files:
        print(f"  - {os.path.basename(cf)}")
    if not char_files:
        print("  (no character *.yaml files found alongside the gmsecret - is --dir right?)", file=sys.stderr)


if __name__ == "__main__":
    main()
