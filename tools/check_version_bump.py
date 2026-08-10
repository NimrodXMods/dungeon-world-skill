#!/usr/bin/env python3
"""Fail if a change touches a skill without bumping its SKILL.md version.

CLAUDE.md requires every edit under skills/ to update that skill's frontmatter
in the same change. Nothing about that is self-enforcing: a reference file can
be rewritten wholesale and the version left behind, and the mistake is only
visible later, when two different skill contents claim to be the same version.

Usage:
    check_version_bump.py --base <ref>

Skips cleanly (exit 0) when there is nothing to compare against - a brand-new
branch, a shallow clone, or a tag push, none of which introduce commits.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

VERSION_RE = re.compile(r"^\s{2}version:\s*[\"']?([0-9][^\"'\s]*)[\"']?\s*$", re.MULTILINE)
UPDATED_RE = re.compile(r"^\s{2}updated:\s*[\"']?([0-9][^\"'\s]*)[\"']?\s*$", re.MULTILINE)
EMPTY_SHA = re.compile(r"^0{40}$")


def git(*args, check=True):
    # encoding is explicit: text=True would decode with the locale codec, which
    # on a non-UTF-8 machine dies on the em dashes in SKILL.md and - because
    # that happens in a reader thread - silently yields no output, making every
    # check pass. A checker that fails open is worse than no checker.
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(ROOT),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        return None
    return result.stdout


def frontmatter_field(text, pattern):
    if not text:
        return None
    end = text.find("\n---", 4)
    match = pattern.search(text[:end] if end != -1 else text)
    return match.group(1) if match else None


def semver(value):
    try:
        return tuple(int(part) for part in value.split("-")[0].split(".")[:3])
    except (AttributeError, ValueError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="commit/ref to compare against")
    args = parser.parse_args()

    base = args.base.strip()
    if not base or EMPTY_SHA.match(base):
        print("no base commit to compare against - skipping version-bump check")
        return 0
    if git("cat-file", "-e", base + "^{commit}") is None:
        print("base {} is not in this clone (shallow fetch?) - skipping".format(base))
        return 0

    # Compare against the merge base, not the base tip: on a PR the tip has
    # moved on independently, and diffing against it would blame this branch
    # for skill edits somebody else landed on main.
    merge_base = git("merge-base", base, "HEAD")
    base = merge_base.strip() if merge_base and merge_base.strip() else base

    changed = git("diff", "--name-only", base, "HEAD")
    if changed is None:
        print("could not diff against {} - skipping".format(base))
        return 0
    changed = [line.strip().replace("\\", "/") for line in changed.splitlines() if line.strip()]

    problems = []
    for skill_md in sorted(SKILLS.glob("*/SKILL.md")):
        skill = skill_md.parent.name
        prefix = "skills/{}/".format(skill)
        touched = [path for path in changed if path.startswith(prefix)]
        if not touched:
            continue

        current_text = skill_md.read_text(encoding="utf-8")
        base_text = git("show", "{}:{}".format(base, prefix + "SKILL.md"))
        if base_text is None:
            continue  # newly added skill - nothing to bump from

        old = frontmatter_field(base_text, VERSION_RE)
        new = frontmatter_field(current_text, VERSION_RE)
        sample = ", ".join(touched[:3]) + (" (+{} more)".format(len(touched) - 3) if len(touched) > 3 else "")

        if new is None:
            problems.append("{}: SKILL.md has no metadata.version".format(skill))
            continue

        if old == new:
            problems.append(
                "{}: {} file(s) changed but metadata.version is still {} - bump it "
                "(major=major change, minor=new functionality, patch=fix), and set "
                "metadata.last-assisting-model plus metadata.updated if the date "
                "has moved on.\n"
                "    changed: {}".format(skill, len(touched), new, sample)
            )
            continue

        old_parts, new_parts = semver(old), semver(new)
        if old_parts and new_parts and new_parts < old_parts:
            problems.append("{}: metadata.version went backwards, {} -> {}".format(skill, old, new))
            continue

        # metadata.updated is deliberately NOT required to change: two edits on
        # the same day leave it correctly untouched. Only a date moving
        # backwards is wrong.
        old_updated = frontmatter_field(base_text, UPDATED_RE)
        new_updated = frontmatter_field(current_text, UPDATED_RE)
        if old_updated and new_updated and new_updated < old_updated:
            problems.append(
                "{}: metadata.updated went backwards, {} -> {}".format(
                    skill, old_updated, new_updated
                )
            )
            continue

        print("{}: {} -> {} ok ({} file(s) changed)".format(skill, old, new, len(touched)))

    if problems:
        print("\nversion-bump check failed:\n")
        for problem in problems:
            print("  " + problem)
        return 1

    print("version-bump check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
