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
import ast
import hashlib
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
import zipfile
from pathlib import Path
from textwrap import indent

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
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")

# The vendored rulebook text: 24 chapters + appendices/ (4) + monster_settings/
# (9). A short count means a partial copy, which would silently break L3.
EXPECTED_XML_FILES = 37

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

    # ISO order is what makes the "date never goes backwards" check in
    # check_version_bump.py a plain string comparison, so enforce the shape.
    updated = str((meta.get("metadata") or {}).get("updated", ""))
    if not updated:
        fail(rel(skill_md), "frontmatter is missing metadata.updated")
    elif not ISO_DATE.match(updated):
        fail(rel(skill_md), "metadata.updated '{}' is not YYYY-MM-DD".format(updated))

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


def run(*args, stdin=None):
    """Run a skill script the way SKILL.md tells the model to: from the skill
    directory, with a scripts/-relative path. stdin carries yamledit's
    operation script, which is where its edits come from."""
    return subprocess.run(
        [sys.executable] + list(args),
        input=stdin,
        cwd=str(SKILL_DIR),
        capture_output=True,
        encoding="utf-8",  # not text=True: the locale codec mangles non-ASCII output
        errors="replace",
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


def check_no_external_imports():
    """The skill must run in a sandbox with nothing pip-installed.

    A stray `import yaml` passes on any dev machine that happens to have PyYAML
    and then dies in the sandbox, which is how session_load.py once shipped
    unable to resume a campaign at all. ruamel/fastjsonschema are allowed
    because they are reached through the vendored yamledit.pyz, not pip.
    """
    stdlib = getattr(sys, "stdlib_module_names", None)
    if not stdlib:
        warn("python", "interpreter too old for stdlib_module_names - skipped the import check")
        return

    # Sibling scripts import each other (region_gen pulls npc_gen's name lists).
    siblings = {path.stem for path in SCRIPTS.glob("*.py")}
    allowed = set(stdlib) | siblings | {"ruamel", "fastjsonschema", "yamledit"}
    for script in sorted(SCRIPTS.glob("*.py")):
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"), str(script))
        except SyntaxError:
            continue  # already reported by check_scripts
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module] if node.level == 0 and node.module else []
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                if root not in allowed:
                    fail(
                        "{}:{}".format(rel(script), node.lineno),
                        "imports '{}', which is neither stdlib nor bundled in "
                        "yamledit.pyz - it will not exist in the sandbox".format(root),
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


def check_session_roundtrip():
    """Save a throwaway campaign and load it back.

    Resuming is the single most important thing the skill does, and it spans
    three components - session_save.py, session_load.py and yamledit.pyz -
    that agree only by convention about the campaign_slug key and the zip
    naming. --help proves none of that, so this exercises it end to end.
    """
    save = SCRIPTS / "session_save.py"
    load = SCRIPTS / "session_load.py"
    template = ASSETS / "yaml_templates" / "gmsecret_template.yaml"
    if not (save.is_file() and load.is_file() and template.is_file()):
        return

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "work"
        restored = Path(tmp) / "restored"
        work.mkdir()
        restored.mkdir()

        secret = work / "roundtrip_gmsecret.yaml"
        secret.write_bytes(template.read_bytes())
        (work / "handoff.md").write_text("test handoff\n", encoding="utf-8")
        (work / "someone_warrior.yaml").write_text("name: Someone\n", encoding="utf-8")
        # The campaign files deliberately live somewhere other than the cwd the
        # scripts run from - that is the normal arrangement, and a path handled
        # relative to the cwd instead of --dir has to fail here.
        (work / "story.md").write_text("# Story\n\n## Chapter 3\n\nProse.\n", encoding="utf-8")

        result = run(
            "scripts/yamledit.pyz", str(secret),
            "--schema", "assets/yaml_schemas/gmsecret.schema.yaml",
            stdin="campaign_slug -> roundtrip\nsession_number -> 3\n",
        )
        if result.returncode != 0:
            fail(rel(secret), "yamledit could not set up the fixture ({})".format(result.stderr.strip()))
            return

        result = run("scripts/" + save.name, str(secret), "--kind", "session_end", "--outdir", str(work))
        if result.returncode != 0:
            fail(rel(save), "session_end save failed ({})".format(result.stderr.strip()))
            return

        # The slug has to survive into the filename, or a loaded campaign comes
        # back as the generic "campaign" and the real name is lost.
        archive = work / "roundtrip_s3.zip"
        if not archive.is_file():
            found = sorted(p.name for p in work.glob("*.zip"))
            fail(
                rel(save),
                "expected roundtrip_s3.zip from campaign_slug + session_number, got {}".format(
                    found or "no zip"
                ),
            )
            return

        # story.md has to be stored at the top of the zip under a bare name, or
        # it extracts to a stray nested path on the way back out.
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
        if "story.md" not in names:
            fail(
                rel(save),
                "did not bundle story.md at the top of the zip (got {})".format(names),
            )

        result = run("scripts/" + load.name, str(archive), "--dir", str(restored))
        if result.returncode != 0:
            fail(rel(load), "could not load the zip back ({})".format(result.stderr.strip()))
            return

        if not (restored / "story.md").is_file():
            fail(rel(load), "did not restore story.md")
        if not (restored / "roundtrip_gmsecret.yaml").is_file():
            fail(rel(load), "did not restore a plain roundtrip_gmsecret.yaml working copy")
        if "roundtrip" not in result.stdout:
            fail(rel(load), "summary does not report the campaign slug")
        if (restored / "roundtrip_gmsecret.txt").exists():
            fail(rel(load), "left the rot13 .txt behind after decoding")

        # A checkpoint is taken mid-session, before any handoff.md exists, so
        # it must not require one the way session_end does.
        (work / "handoff.md").unlink()
        result = run("scripts/" + save.name, str(secret), "--kind", "checkpoint", "--outdir", str(work))
        if result.returncode != 0:
            fail(
                rel(save),
                "checkpoint save requires a handoff.md, but none exists mid-session ({})".format(
                    result.stderr.strip()
                ),
            )
        elif not (work / "roundtrip_checkpoint.zip").is_file():
            fail(rel(save), "checkpoint save produced no roundtrip_checkpoint.zip")


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
    """The digest bottoms out at L3 = the vendored rulebook XML. Verify the
    source is intact and that every [xml:...] citation actually resolves - a
    dangling citation silently drops a lookup back to L2 with no other signal."""
    digest = REFERENCES / "rulebook-digest"
    present = []
    for required in ("L0-index.md", "L1-digest.md"):
        if (digest / required).is_file():
            present.append(digest / required)
        else:
            fail("references/rulebook-digest/" + required, "missing")

    source = digest / "source" / "xml"
    if not source.is_dir():
        fail(rel(source), "missing - SKILL.md's L3 lookups depend on it")
        return

    xml_files = sorted(source.rglob("*.xml"))
    if len(xml_files) != EXPECTED_XML_FILES:
        fail(
            rel(source),
            "has {} .xml files, expected {} - the vendored copy looks partial "
            "(see source/ATTRIBUTION.md to refresh)".format(
                len(xml_files), EXPECTED_XML_FILES
            ),
        )
    if not xml_files:
        return

    for path in xml_files:
        try:
            ElementTree.parse(path)
        except ElementTree.ParseError as exc:
            fail(rel(path), "is not well-formed XML ({})".format(exc))

    if not present:
        return

    # rulebook.py owns anchor generation; shelling out keeps the validator from
    # reimplementing it and drifting.
    result = run(
        "scripts/rulebook.py",
        "--check-anchors",
        *[str(path) for path in present],
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        fail(
            "references/rulebook-digest",
            "has [xml:...] citations that do not resolve:\n"
            + indent(detail, "      "),
        )


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
            ["git", "ls-files"], cwd=str(ROOT), capture_output=True,
            encoding="utf-8", errors="replace", timeout=60
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
    check_no_external_imports()
    check_determinism()
    check_session_roundtrip()
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
