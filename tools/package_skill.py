#!/usr/bin/env python3
"""Package the dungeon-world-gm skill into a distributable zip.

Layout inside the zip puts the skill directory at the top level, so SKILL.md
lands at dungeon-world-gm/SKILL.md - what a skill loader expects after
extraction, and what keeps the scripts/ and references/ paths in SKILL.md valid.

The rulebook source XML (references/rulebook-digest/source/xml/) is included on
purpose despite its size: it is the digest's L3 tier, read via scripts/rulebook.py
by anchor, and without it the digest bottoms out at L2.
"""
import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "dungeon-world-gm"
DIST = ROOT / "dist"

EXCLUDE_DIRS = {"__pycache__", ".pytest_cache"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}

VERSION_RE = re.compile(r"^\s{2}version:\s*[\"']?([0-9][^\"'\s]*)[\"']?\s*$", re.MULTILINE)


def skill_version():
    """Read metadata.version out of SKILL.md's frontmatter.

    Deliberately a regex rather than a YAML parse: packaging must not depend on
    the interpreter having a YAML library, and the field's shape is fixed.
    """
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    match = VERSION_RE.search(text[:end] if end != -1 else text)
    if not match:
        sys.exit("error: could not read metadata.version from SKILL.md")
    return match.group(1)


def included_files():
    for path in sorted(SKILL_DIR.rglob("*")):
        if not path.is_file():
            continue
        if EXCLUDE_DIRS.intersection(path.relative_to(SKILL_DIR).parts):
            continue
        if path.suffix in EXCLUDE_SUFFIXES or path.name in EXCLUDE_NAMES:
            continue
        yield path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expect-version",
        help="fail unless SKILL.md's metadata.version equals this (release guard)",
    )
    parser.add_argument("--outdir", default=str(DIST), help="where to write the zip")
    args = parser.parse_args()

    version = skill_version()
    if args.expect_version and args.expect_version != version:
        sys.exit(
            "error: SKILL.md says version {}, expected {} - bump the frontmatter "
            "and the tag together".format(version, args.expect_version)
        )

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / "{}-{}.zip".format(SKILL_DIR.name, version)

    count = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in included_files():
            arcname = Path(SKILL_DIR.name) / path.relative_to(SKILL_DIR)
            archive.write(path, arcname.as_posix())
            count += 1

    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    print("built   {}".format(target))
    print("files   {}".format(count))
    print("size    {:.1f} KiB".format(target.stat().st_size / 1024))
    print("sha256  {}".format(digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
