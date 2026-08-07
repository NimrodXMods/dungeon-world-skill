#!/usr/bin/env python3
"""Validate the dungeon-world-gm skill.

Most of what makes this skill correct is convention rather than syntax: a
[[wikilink]] that resolves, a reference file that actually appears in SKILL.md's
index (one that doesn't is invisible at runtime), a generator that still answers
--help-llm, a template that still satisfies its schema. Nothing about those
fails loudly on its own, so they are checked here.

No pip dependencies, by design. The vendored yamledit.pyz already bundles
ruamel.yaml and fastjsonschema, so this script borrows them off its sys.path -
CI needs nothing but a Python interpreter, exactly like the skill itself.

Every check runs even after an earlier one fails; problems are reported together
at the end. Exit 0 = clean, 1 = at least one error.
"""
import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "dungeon-world-gm"
SCRIPTS = SKILL_DIR / "scripts"
REFERENCES = SKILL_DIR / "references"
ASSETS = SKILL_DIR / "assets"
PYZ = SCRIPTS / "yamledit.pyz"
LOCK = ROOT / "tools" / "yamledit.lock"

# Scripts that intentionally have --help only. Everything else in scripts/ is
# reached by the model through --help-llm, which is the canonical interface doc.
NO_HELP_LLM = {"session_load.py", "session_save.py"}

# Documents that must keep validating against their schema.
TEMPLATE_SCHEMA_PAIRS = [
    ("character_template.yaml", "character.schema.yaml"),
    ("gmsecret_template.yaml", "gmsecret.schema.yaml"),
]

# Live campaign files must never be committed - the gmsecret is spoiler material
# and the zips are player downloads. gmsecret_template.yaml is the deliberate
# near-miss and has to stay allowed.
FORBIDDEN_TRACKED = [
    re.compile(r"(^|/)[^/]*_gmsecret\.yaml$"),
    re.compile(r"(^|/)handoff\.md$"),
    re.compile(r"\.zip$"),
]

SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
PAGE_MARKER = re.compile(r"^===== PAGE (\d+) =====")

errors = []
warnings = []


def fail(where, message):
    errors.append("{}: {}".format(where, message))


def warn(where, message):
    warnings.append("{}: {}".format(where, message))


def rel(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_bundled_deps():
    """Borrow ruamel.yaml and fastjsonschema from the vendored zipapp."""
    if not PYZ.is_file():
        fail(rel(PYZ), "missing - the whole validator depends on its bundled deps")
        return None, None
    sys.path.insert(0, str(PYZ))
    try:
        import fastjsonschema
        import ruamel.yaml
    except ImportError as exc:
        fail(rel(PYZ), "does not carry the expected bundled deps ({})".format(exc))
        return None, None
    return fastjsonschema, ruamel.yaml


def read_yaml(yaml_mod, path_or_text, where):
    loader = yaml_mod.YAML(typ="safe")
    try:
        if isinstance(path_or_text, Path):
            with path_or_text.open(encoding="utf-8") as handle:
                return loader.load(handle)
        return loader.load(path_or_text)
    except Exception as exc:
        fail(where, "YAML does not parse ({})".format(exc))
        return None


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_frontmatter(yaml_mod):
    """SKILL.md's frontmatter is what a skill loader reads first."""
    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.is_file():
        fail(rel(skill_md), "missing")
        return None
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(rel(skill_md), "does not begin with a YAML frontmatter block")
        return None
    end = text.find("\n---", 4)
    if end == -1:
        fail(rel(skill_md), "frontmatter block is never closed")
        return None
    meta = read_yaml(yaml_mod, text[4:end], rel(skill_md) + " frontmatter")
    if not isinstance(meta, dict):
        return None

    for field in ("name", "description", "license"):
        if not meta.get(field):
            fail(rel(skill_md), "frontmatter is missing '{}'".format(field))

    name = meta.get("name", "")
    if name and not KEBAB.match(name):
        fail(rel(skill_md), "name '{}' is not kebab-case".format(name))
    if name and name != SKILL_DIR.name:
        fail(rel(skill_md), "name '{}' != directory '{}'".format(name, SKILL_DIR.name))

    description = meta.get("description", "")
    if len(description) > 1024:
        fail(rel(skill_md), "description is {} chars, limit is 1024".format(len(description)))

    version = str((meta.get("metadata") or {}).get("version", ""))
    if not version:
        fail(rel(skill_md), "frontmatter is missing metadata.version")
    elif not SEMVER.match(version):
        fail(rel(skill_md), "metadata.version '{}' is not semver".format(version))
    return version


def check_wikilinks():
    """A reference nobody links to is a reference the model never opens."""
    docs = [SKILL_DIR / "SKILL.md"] + sorted(REFERENCES.glob("*.md"))
    available = {path.stem for path in REFERENCES.glob("*.md")}
    linked = set()
    spellings = {}

    for doc in docs:
        for lineno, line in enumerate(doc.read_text(encoding="utf-8").splitlines(), 1):
            for raw in WIKILINK.findall(line):
                target = raw[:-3] if raw.endswith(".md") else raw
                linked.add(target)
                spellings.setdefault(target, set()).add(raw)
                if target not in available:
                    fail(
                        "{}:{}".format(rel(doc), lineno),
                        "[[{}]] does not resolve to references/{}.md".format(raw, target),
                    )

    for orphan in sorted(available - linked):
        fail(
            "references/{}.md".format(orphan),
            "is never linked from SKILL.md or another reference - it will not be read at runtime",
        )

    for target, forms in sorted(spellings.items()):
        if len(forms) > 1:
            warn(
                "references/{}.md".format(target),
                "linked inconsistently as {}".format(", ".join(sorted("[[%s]]" % f for f in forms))),
            )


def run(*args):
    """Run a skill script the way SKILL.md tells the model to: from the skill
    directory, with a scripts/-relative path."""
    return subprocess.run(
        [sys.executable] + list(args),
        cwd=str(SKILL_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )


def check_scripts():
    scripts = sorted(SCRIPTS.glob("*.py"))
    if not scripts:
        fail("scripts/", "no Python scripts found")
        return

    for script in scripts:
        try:
            compile(script.read_text(encoding="utf-8"), str(script), "exec")
        except SyntaxError as exc:
            fail(rel(script), "does not compile ({})".format(exc))
            continue

        result = run("scripts/" + script.name, "--help")
        if result.returncode != 0:
            fail(rel(script), "--help exited {}".format(result.returncode))

        if script.name not in NO_HELP_LLM:
            result = run("scripts/" + script.name, "--help-llm")
            if result.returncode != 0:
                fail(
                    rel(script),
                    "--help-llm exited {} - it is the canonical interface doc "
                    "and must keep working".format(result.returncode),
                )


def check_determinism():
    """--seed is dev-only, but it is also the only handle CI has on these."""
    script = SCRIPTS / "idea_gen.py"
    if not script.is_file():
        return
    outputs = []
    for _ in range(2):
        result = run("scripts/" + script.name, "--seed", "7", "treasure")
        if result.returncode != 0:
            fail(rel(script), "--seed run exited {}".format(result.returncode))
            return
        outputs.append(result.stdout)
    if outputs[0] != outputs[1]:
        fail(rel(script), "same --seed produced different output")


def check_schemas(fastjsonschema, yaml_mod):
    for template_name, schema_name in TEMPLATE_SCHEMA_PAIRS:
        template = ASSETS / "yaml_templates" / template_name
        schema_path = ASSETS / "yaml_schemas" / schema_name
        if not template.is_file() or not schema_path.is_file():
            fail("assets/", "missing {} or {}".format(template_name, schema_name))
            continue

        schema = read_yaml(yaml_mod, schema_path, rel(schema_path))
        document = read_yaml(yaml_mod, template, rel(template))
        if schema is None or document is None:
            continue

        try:
            validate = fastjsonschema.compile(schema)
        except Exception as exc:
            fail(rel(schema_path), "is not a valid JSON Schema ({})".format(exc))
            continue

        try:
            validate(document)
        except Exception as exc:
            fail(rel(template), "does not satisfy {} ({})".format(schema_name, exc))


def check_digest():
    digest = REFERENCES / "rulebook-digest"
    for required in ("L0-index.md", "L1-digest.md"):
        if not (digest / required).is_file():
            fail("references/rulebook-digest/" + required, "missing")

    source = digest / "source" / "core-rulebook-full-text.txt"
    if not source.is_file():
        fail(rel(source), "missing - SKILL.md's L3 page lookups depend on it")
        return

    pages = []
    with source.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = PAGE_MARKER.match(line)
            if match:
                pages.append(int(match.group(1)))

    if not pages:
        fail(rel(source), "has no '===== PAGE N =====' markers - grep-by-page lookups would break")
        return
    if pages[0] != 1:
        fail(rel(source), "first page marker is {}, expected 1".format(pages[0]))
    for previous, current in zip(pages, pages[1:]):
        if current != previous + 1:
            fail(rel(source), "page markers jump from {} to {}".format(previous, current))
            break


def check_yamledit_pin(yaml_mod):
    if not LOCK.is_file():
        fail(rel(LOCK), "missing")
        return
    lock = read_yaml(yaml_mod, LOCK, rel(LOCK))
    if not isinstance(lock, dict):
        return
    if not PYZ.is_file():
        return

    digest = hashlib.sha256(PYZ.read_bytes()).hexdigest()
    if digest != lock.get("sha256"):
        fail(
            rel(PYZ),
            "sha256 {} does not match {} - rebuild and update the lock together".format(
                digest[:16] + "...", rel(LOCK)
            ),
        )

    if not zipfile.is_zipfile(PYZ):
        fail(rel(PYZ), "is not a valid zipapp")
        return

    result = run("scripts/" + PYZ.name, "--version")
    reported = result.stdout.strip().split()[-1] if result.stdout.strip() else ""
    expected = str(lock.get("version", ""))
    if result.returncode != 0:
        fail(rel(PYZ), "--version exited {}".format(result.returncode))
    elif reported != expected:
        fail(rel(PYZ), "reports version {}, lock says {}".format(reported or "?", expected))


def check_tracked_files():
    """Campaign state is player-facing or spoiler material; it must not ship."""
    try:
        result = subprocess.run(
            ["git", "ls-files"], cwd=str(ROOT), capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        warn("git", "not available - skipped the tracked-file hygiene check")
        return
    if result.returncode != 0:
        warn("git", "ls-files failed - skipped the tracked-file hygiene check")
        return

    for tracked in result.stdout.splitlines():
        for pattern in FORBIDDEN_TRACKED:
            if pattern.search(tracked):
                fail(tracked, "is campaign state or a session package and must not be committed")


def main():
    fastjsonschema, yaml_mod = load_bundled_deps()
    if yaml_mod is None:
        print("FAIL: " + errors[0])
        return 1

    if not SKILL_DIR.is_dir():
        print("FAIL: {} does not exist".format(rel(SKILL_DIR)))
        return 1

    check_frontmatter(yaml_mod)
    check_wikilinks()
    check_scripts()
    check_determinism()
    check_schemas(fastjsonschema, yaml_mod)
    check_digest()
    check_yamledit_pin(yaml_mod)
    check_tracked_files()

    for warning in warnings:
        print("warning: " + warning)
    for error in errors:
        print("error:   " + error)

    if errors:
        print("\n{} error(s), {} warning(s)".format(len(errors), len(warnings)))
        return 1
    print("\nskill validation passed ({} warning(s))".format(len(warnings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
