#!/usr/bin/env python3
"""
session_save.py - package a Dungeon World session for download.

Usage:
    python3 session_save.py CAMPAIGN_GMSECRET.yaml --kind session_end
    python3 session_save.py CAMPAIGN_GMSECRET.yaml --kind checkpoint
    python3 session_save.py CAMPAIGN_GMSECRET.yaml --kind checkpoint --no-rot13

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

--no-rot13 stores the gmsecret and handoff as plain text instead. Rot13 here is
spoiler-obfuscation, not security: it exists so a PLAYER can hold the save file
without spoiling themselves. When the person holding the zip is the GM - GM
assistant mode, or a solo GM archiving their own prep - obfuscating their own
notes from them is backwards, and this flag turns it off.

The choice is recorded in the zip by FILENAME, not a flag or header, so
session_load.py needs no matching option and cannot guess wrong:

    rot13     <slug>_gmsecret.txt    <slug>_handoff.txt
    plain     <slug>_gmsecret.yaml   handoff.md

which also means a plain zip opens readable in any zip viewer, with the working
filenames already correct.

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

Text in the zip is always UTF-8 with LF newlines (portable). Working copies on
disk use the host line ending (CRLF on Windows). session_load converts back.

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

from _util import force_utf8_stdio, normalize_newlines_to_lf, read_text_utf8

force_utf8_stdio()

YAMLEDIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yamledit.pyz")

HELP_LLM = """session_save.py - package a Dungeon World campaign into a downloadable zip.

WHAT IT IS
  Campaign state lives in files, not your memory. This bundles the whole
  working set - gmsecret, environment, character sheets, handoff, story - into
  one zip the user can download and hand back at the start of the next session.

  The gmsecret and handoff are rot13-encoded by default so a player can hold
  the zip without spoiling themselves. That is obfuscation, not security.

WHEN TO CALL IT
  --kind session_end   The session is over. handoff.md is REQUIRED; the script
                       exits with an error if it is missing, because that file
                       is what the next session picks up from. Names the zip
                       <slug>_s<session_number>.zip.
  --kind checkpoint    A mid-session snapshot. handoff.md is optional and
                       simply omitted when absent. Names the zip
                       <slug>_checkpoint.zip, overwriting any previous one.

USAGE
  python3 scripts/session_save.py GMSECRET --kind {session_end,checkpoint}
          [--slug SLUG] [--dir DIR] [--outdir OUTDIR] [--no-rot13]

  GMSECRET     Path to the plain-text gmsecret YAML working copy.
  --slug       Override the campaign slug used in filenames. Default: slugified
               `campaign_slug` (falling back to `campaign`) read from GMSECRET.
  --dir DIR    Where to look for character *.yaml, the environment file,
               handoff.md and story.md. Default: GMSECRET's own directory.
  --outdir     Where to write the zip. Default: current directory.
  --no-rot13   Store the gmsecret and handoff as plain text. Use when the person
               holding the zip IS the GM (GM-assistant mode, a solo GM archiving
               prep) - the obfuscation guards against a player spoiling
               themselves, which does not apply to them.

WHAT GOES IN THE ZIP
  <slug>_gmsecret.txt      rot13   (or <slug>_gmsecret.yaml with --no-rot13)
  <slug>_handoff.txt       rot13   (or handoff.md with --no-rot13)
  <slug>_environment.yaml  plain   player-visible; omitted if it does not exist
  *.yaml                   plain   character sheets
  story.md                 plain   only when the gmsecret has maintain_story

  The ENCODING IS CARRIED BY THE FILENAME, which is why session_load.py needs
  no matching flag and cannot guess wrong: rot13 is its own inverse, so a wrong
  guess would corrupt silently instead of failing.

  Payloads are normalized to LF inside the zip regardless of local line endings.

EXIT CODES
  0  zip written
  1  no handoff.md at session_end, or no session_number in the gmsecret

NOTES
  - A missing character sheet is a warning, not an error - check --dir if you
    see it, since the usual cause is pointing at the wrong directory.
  - The environment file is bundled but is NOT counted as a character sheet.
  - Re-running is harmless and idempotent; it just rewrites the same zip.
  - Restore with: python3 scripts/session_load.py <zip> [--dir .]
"""

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
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return 0

    ap = argparse.ArgumentParser(description="Package a DW session for download.")
    ap.add_argument("gmsecret", help="Path to the plain-text gmsecret YAML working copy")
    ap.add_argument("--kind", choices=["session_end", "checkpoint"], required=True)
    ap.add_argument("--slug", default=None, help="Override the campaign slug used in filenames")
    ap.add_argument("--dir", default=None,
                     help="Directory to look for character *.yaml files in (default: gmsecret's directory)")
    ap.add_argument("--outdir", default=".", help="Where to write the zip (default: current dir)")
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                     help="print the dense full reference written for LLM callers, then exit")
    ap.add_argument("--no-rot13", action="store_true", dest="no_rot13",
                     help="Store the gmsecret and handoff as plain text instead of "
                          "rot13. Use when the person holding the zip IS the GM "
                          "(GM assistant mode, solo GM archiving prep) - the "
                          "obfuscation exists to keep a player from spoiling "
                          "themselves, which does not apply to them.")
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

    # Rot13 the gmsecret's raw text after normalizing to LF (zip-canonical),
    # unless --no-rot13. Deliberately not re-serialised: a YAML round trip would
    # strip comments. UTF-8 + LF is the portable payload; load expands newlines
    # for the host.
    def maybe_rot13(text):
        return text if args.no_rot13 else codecs.encode(text, "rot13")

    # The names carry the encoding, so load needs no flag of its own and a plain
    # zip opens readable with the working filenames already right.
    gmsecret_name = f"{slug}_gmsecret.yaml" if args.no_rot13 else f"{slug}_gmsecret.txt"
    handoff_name = "handoff.md" if args.no_rot13 else f"{slug}_handoff.txt"

    encoded_gmsecret_text = maybe_rot13(
        normalize_newlines_to_lf(read_text_utf8(args.gmsecret))
    )

    # encode handoff.md. Required at session end - that is the file the next
    # session picks up from - but a checkpoint is a mid-session snapshot taken
    # before any handoff exists, so there it is merely absent.
    print(f"Looking for handoff.md in {char_dir}...")
    encoded_handoff_text = None
    handoff_path = os.path.join(char_dir, "handoff.md")
    if os.path.exists(handoff_path):
        encoded_handoff_text = maybe_rot13(
            normalize_newlines_to_lf(read_text_utf8(handoff_path))
        )
    elif args.kind == "session_end":
        sys.exit(f"ERROR: no handoff.md found in {char_dir}. Write one before "
                 f"ending the session, or pass --dir if it lives elsewhere.")
    else:
        print("No handoff.md found, skipping (checkpoint).")

    char_files = sorted(
        p for p in glob.glob(os.path.join(char_dir, "*.yaml"))
        if not (os.path.basename(p).endswith("_gmsecret.yaml")
                or os.path.basename(p).endswith("_environment.yaml"))
    )

    # The environment file is handled on its own rather than falling out of the
    # glob above: it is player-visible (so it rides along plain, never rot13'd)
    # but it is not a character, and counting it as one would make a campaign
    # with no PCs look like it has one. Absent is fine - a campaign may not have
    # written one yet.
    environment_path = os.path.join(char_dir, f"{slug}_environment.yaml")
    if not os.path.exists(environment_path):
        environment_path = None

    # story.md rides along in plain text, unlike the gmsecret and handoff: it is
    # the narrative the player has already lived through, so there is nothing in
    # it to spoil. Only nag about a missing one when the campaign opted in.
    # Still store as UTF-8 LF so the zip is platform-stable.
    story_path = os.path.join(char_dir, STORY_FILENAME)
    has_story = os.path.exists(story_path)
    if not has_story and fields["maintain_story"]:
        print(f"Warning: maintain_story is set but no {STORY_FILENAME} found in {char_dir}",
              file=sys.stderr)

    zip_path = os.path.join(args.outdir, zip_name)
    print(f"Writing {zip_path} ...")

    note = "plain text - readable by anyone holding the zip" if args.no_rot13 \
        else "rot13-encoded"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(gmsecret_name, encoded_gmsecret_text)
        print(f"  - {gmsecret_name} ({note})")
        if environment_path is not None:
            zf.writestr(
                os.path.basename(environment_path),
                normalize_newlines_to_lf(read_text_utf8(environment_path)),
            )
            print(f"  - {os.path.basename(environment_path)}")
        if encoded_handoff_text is not None:
            zf.writestr(handoff_name, encoded_handoff_text)
            print(f"  - {handoff_name} ({note})")
        for cf in char_files:
            # writestr + LF, not zf.write raw bytes: Windows working copies may
            # be CRLF on disk; the zip must stay LF-canonical.
            zf.writestr(
                os.path.basename(cf),
                normalize_newlines_to_lf(read_text_utf8(cf)),
            )
            print(f"  - {os.path.basename(cf)}")
        if has_story:
            zf.writestr(
                STORY_FILENAME,
                normalize_newlines_to_lf(read_text_utf8(story_path)),
            )
            print(f"  - {STORY_FILENAME}")
    print(f"Wrote {zip_path}")

    if not char_files:
        print("  (no character *.yaml files found alongside the gmsecret - is --dir right?)", file=sys.stderr)
    if args.no_rot13:
        print("  (spoilers are readable in this zip - hand it to a GM, not a player. "
              "session_load.py needs no flag: it reads the encoding off the filenames)")


if __name__ == "__main__":
    main()
