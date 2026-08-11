#!/usr/bin/env python3
"""Validate the dungeon-world-gm skill.

Most of what makes this skill correct is convention rather than syntax: a
Markdown skill-root link that resolves, a reference file that actually appears
in SKILL.md's index (one that doesn't is invisible at runtime), a generator that
still answers --help-llm, a template that still satisfies its schema. Nothing
about those fails loudly on its own, so they are checked here.

No pip dependencies, by design. The vendored yamledit.pyz already bundles
ruamel.yaml and fastjsonschema, so this script borrows them off its sys.path -
CI needs nothing but a Python interpreter, exactly like the skill itself.

Every check runs even after an earlier one fails; problems are reported together
at the end. Exit 0 = clean, 1 = at least one error.
"""
import argparse
import ast
import hashlib
import json
import os
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
# Underscore modules (_treasure.py, _util.py) are not CLIs - they are sibling
# libraries imported by the generators and have no interface for a model to read.
NO_HELP_LLM = {"session_load.py", "session_save.py", "_treasure.py", "_util.py"}

# Arguments a generator needs before it actually generates anything. Most take
# none. monster_gen.py requires a bestiary setting tag - run bare it prints its
# setting menu and exits 0, which would leave check_determinism and
# check_encoding_safety passing while exercising nothing at all. Each entry is
# a list of argument lists; every one is run.
GENERATOR_INVOCATIONS = {
    "monster_gen.py": [
        ["cavern"],
        ["--custom", "--random"],
        ["--custom", "--random", "--theme", "swamp,undead"],
    ],
}
DEFAULT_INVOCATION = [[]]


def invocations_for(name):
    return GENERATOR_INVOCATIONS.get(name, DEFAULT_INVOCATION)


# --quick is a fast local loop, not a pre-push check. Almost all runtime here is
# subprocess spawning, so it trims the per-seed sweeps and skips the save/load
# round-trip (the single most expensive check at ~8s). Whatever it gives up is
# listed back to the user by name - a reduced run must never be mistakable for
# a full one.
QUICK = False
skipped = []

# (full, quick) seed sets for the two sweeping checks.
DETERMINISM_SEEDS = (("3", "7", "11"), ("3",))
ENCODING_SEEDS = (tuple(str(n) for n in range(1, 9)), ("1",))


def seeds_for(pair):
    return pair[1] if QUICK else pair[0]

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
# Legacy Obsidian-style; not part of Agent Skills — fail if any remain.
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
# Agent Skills file refs: skill-root-relative Markdown links to .md paths.
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+\.md)(?:#[^)]*)?\)")

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


def skill_md_docs():
    """Markdown under the skill tree that participates in the link graph.

    Excludes vendored rulebook XML and non-doc trees. Includes SKILL.md,
    SKILL-*.md procedure packs, and references/**/*.md (including the digest).
    """
    docs = []
    for path in SKILL_DIR.rglob("*.md"):
        s = str(path).replace("\\", "/")
        if "/source/xml/" in s or "/__pycache__/" in s:
            continue
        docs.append(path)
    return sorted(docs)


def check_skill_links():
    """Skill-root Markdown links must resolve; reference files must be linked."""
    docs = skill_md_docs()
    available_refs = {path.stem for path in REFERENCES.glob("*.md")}
    linked_refs = set()

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for raw in WIKILINK.findall(line):
                fail(
                    "{}:{}".format(rel(doc), lineno),
                    "legacy wikilink [[{}]] — use skill-root Markdown "
                    "[label](path/from/skill-root.md) instead".format(raw),
                )
            for href in MD_LINK.findall(line):
                # strip optional query-ish noise; keep path only
                href = href.strip().split()[0].rstrip(")")
                # External URLs are not skill-root paths
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                # skill-root relative (Agent Skills convention)
                target = (SKILL_DIR / href).resolve()
                try:
                    target.relative_to(SKILL_DIR.resolve())
                except ValueError:
                    fail(
                        "{}:{}".format(rel(doc), lineno),
                        "link escapes skill root: ({})".format(href),
                    )
                    continue
                if not target.is_file():
                    fail(
                        "{}:{}".format(rel(doc), lineno),
                        "broken link ({}) — no file at skill-root path".format(href),
                    )
                    continue
                # orphan tracking: top-level references/*.md only
                try:
                    rel_to_refs = target.relative_to(REFERENCES.resolve())
                except ValueError:
                    continue
                if len(rel_to_refs.parts) == 1 and rel_to_refs.suffix == ".md":
                    linked_refs.add(rel_to_refs.stem)

    for orphan in sorted(available_refs - linked_refs):
        fail(
            "references/{}.md".format(orphan),
            "is never linked from SKILL.md, SKILL-*.md, or another skill markdown "
            "file - it will not be read at runtime",
        )


def run(*args, stdin=None, env=None):
    """Run a skill script the way SKILL.md tells the model to: from the skill
    directory, with a scripts/-relative path. stdin carries yamledit's
    operation script, which is where its edits come from. env overlays extra
    variables on the current environment (see check_encoding_safety)."""
    child_env = None
    if env:
        child_env = dict(os.environ)
        child_env.update(env)
    return subprocess.run(
        [sys.executable] + list(args),
        input=stdin,
        cwd=str(SKILL_DIR),
        capture_output=True,
        encoding="utf-8",  # not text=True: the locale codec mangles non-ASCII output
        errors="replace",
        timeout=120,
        env=child_env,
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
    """--seed is dev-only, but it is also the only handle CI has on these.

    Swept across several seeds and every generator rather than one seed of one
    script: output is data-driven, so a single seed exercises only a sliver of
    the tables and can miss a whole class of defect (a cp1252 crash hid behind
    exactly this gap - see check_encoding_safety).
    """
    scripts = sorted(SCRIPTS.glob("*_gen.py"))
    if not scripts:
        return
    for script in scripts:
        for extra in invocations_for(script.name):
            for seed in seeds_for(DETERMINISM_SEEDS):
                args = ["scripts/" + script.name] + extra + ["--seed", seed]
                outputs = []
                for _ in range(2):
                    result = run(*args)
                    if result.returncode != 0:
                        fail(
                            rel(script),
                            "{} --seed {} exited {}: {}".format(
                                " ".join(extra) or "(no args)",
                                seed,
                                result.returncode,
                                (result.stderr or "").strip().splitlines()[-1:],
                            ),
                        )
                        break
                    outputs.append(result.stdout)
                if len(outputs) == 2 and outputs[0] != outputs[1]:
                    fail(
                        rel(script),
                        "{} --seed {} produced different output on two "
                        "runs".format(" ".join(extra) or "(no args)", seed),
                    )


def check_encoding_safety():
    """Every generator must survive a legacy 8-bit stdout.

    On Windows, sys.stdout falls back to the ANSI code page (cp1252) whenever
    stdout is not a real console - a pipe or a redirect is enough. cp1252 has
    only 256 slots, so printing a character outside it (U+2192 and U+2734 both
    occur in this skill) raises UnicodeEncodeError and the script dies. That is
    invisible on a Linux runner, where the locale is UTF-8 and the bug simply
    cannot reproduce, so CI has to force the condition to test for it.

    Seeds are swept because output is data-driven: any single seed may happen
    to avoid the offending character, which is exactly how this shipped
    broken (see _util.force_utf8_stdio).
    """
    # NO_COLOR keeps Python 3.13+ colourised tracebacks from leaking ANSI
    # escapes into the CI log.
    env = {"PYTHONIOENCODING": "cp1252", "NO_COLOR": "1"}
    seeds = seeds_for(ENCODING_SEEDS)

    for script in sorted(SCRIPTS.glob("*_gen.py")):
        broken = False
        for extra in invocations_for(script.name):
            if broken:
                break
            for seed in seeds:
                args = ["scripts/" + script.name] + extra + ["--seed", seed]
                result = run(*args, env=env)
                if result.returncode == 0:
                    continue
                detail = (result.stderr or "").strip().splitlines()
                reason = detail[-1] if detail else "exit {}".format(result.returncode)
                fail(
                    rel(script),
                    "dies with a cp1252 stdout ({} --seed {}): {}\n"
                    "      Call force_utf8_stdio() from _util at import, as the "
                    "other scripts do.".format(
                        " ".join(extra) or "(no args)", seed, reason
                    ),
                )
                broken = True  # one report per script is enough
                break

    # rulebook.py is not seeded, but it renders rulebook prose containing
    # characters no 8-bit code page can represent.
    rulebook = SCRIPTS / "rulebook.py"
    if rulebook.is_file():
        result = run(
            "scripts/rulebook.py", "--anchor", "moves#special-moves", env=env
        )
        if result.returncode != 0:
            detail = (result.stderr or "").strip().splitlines()
            fail(
                rel(rulebook),
                "dies with a cp1252 stdout: {}".format(
                    detail[-1] if detail else "exit {}".format(result.returncode)
                ),
            )


def _literal_constant(script, name):
    """Read a module-level constant out of a script without importing it.

    The skill's scripts are not importable from here (different tree, and they
    run side effects at import), but the validator needs monster_gen's category
    list to check the lexicon against. Parsing it keeps the script the single
    source of truth instead of duplicating the list here.
    """
    try:
        tree = ast.parse(script.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                try:
                    return ast.literal_eval(node.value)
                except ValueError:
                    return None
    return None


def check_lexicon():
    """monster_gen's seed vocabulary must be complete for every theme.

    A theme missing a category would not crash - random.sample of an empty list
    returns [] - it would just quietly stop seeding that field, which is
    exactly the blank-page problem the lexicon exists to solve.
    """
    lexicon_path = ASSETS / "monster_words.json"
    script = SCRIPTS / "monster_gen.py"
    if not lexicon_path.is_file():
        fail(rel(lexicon_path), "missing - monster_gen.py --custom needs it for seed words")
        return

    try:
        lexicon = json.loads(lexicon_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        fail(rel(lexicon_path), "is not valid JSON ({})".format(exc))
        return

    categories = _literal_constant(script, "WORD_CATEGORIES")
    if not categories:
        fail(rel(script), "WORD_CATEGORIES could not be read - cannot check the lexicon")
        return

    # Read the form vocabularies the same way and for the same reason: a theme's
    # favour lists name morphologies and physiologies, and a typo in one would
    # silently never match rather than erroring.
    form_vocab = {}
    for key, const in (("morphology_favour", "MORPHOLOGY"),
                       ("physiology_favour", "PHYSIOLOGY")):
        entries = _literal_constant(script, const)
        if entries:
            form_vocab[key] = {entry[0] for entry in entries}
        else:
            fail(rel(script), "{} could not be read - cannot check the theme "
                              "favour lists".format(const))

    themes = {k: v for k, v in lexicon.get("themes", {}).items() if not k.startswith("_")}
    if not themes:
        fail(rel(lexicon_path), "has no themes")
        return
    if "generic" not in themes:
        fail(rel(lexicon_path), "has no 'generic' theme, which is the default")

    for name in sorted(themes):
        theme = themes[name]
        if not isinstance(theme, dict):
            fail(rel(lexicon_path), "theme {!r} is not an object".format(name))
            continue
        for category in categories:
            words = theme.get(category)
            if not words:
                fail(
                    rel(lexicon_path),
                    "theme {!r} is missing or has an empty {!r} - every theme "
                    "must carry every category".format(name, category),
                )
            elif not all(isinstance(w, str) and w.strip() for w in words):
                fail(
                    rel(lexicon_path),
                    "theme {!r} has a non-string or blank entry in {!r}".format(
                        name, category
                    ),
                )

        # Unlike the word categories these are OPTIONAL - a theme without them
        # simply rolls form unbiased - so only the values are checked, never
        # their presence. That is what lets a new theme be added without
        # touching monster_gen.py.
        for key, allowed in form_vocab.items():
            for value in theme.get(key) or []:
                if value not in allowed:
                    fail(
                        rel(lexicon_path),
                        "theme {!r} lists {!r} in {!r}, which is not a value "
                        "monster_gen.py offers".format(name, value, key),
                    )

    tiers = _literal_constant(script, "DEADLINESS_TIERS") or ()
    ladder = lexicon.get("deadliness", {})
    for tier in tiers:
        if not ladder.get(tier):
            fail(
                rel(lexicon_path),
                "deadliness ladder is missing tier {!r} - monster_gen names "
                "monsters off it".format(tier),
            )


def check_treasure_asset():
    """The shared treasure table and its appearance tables must be whole.

    This asset exists because the 1-18 table used to be copied into both
    monster_gen.py and idea_gen.py and the copies drifted at entries 12 and 13.
    Nothing here can tell you an entry is WORDED wrong against the rulebook -
    that stays a human job - but a missing entry, an unrollable dice expression
    or an empty category all fail silently at play time, which is worse: the
    generator keeps working and quietly stops describing something.
    """
    path = ASSETS / "treasure.json"
    module = SCRIPTS / "_treasure.py"
    if not path.is_file():
        fail(rel(path), "missing - monster_gen.py and idea_gen.py both roll on it")
        return

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        fail(rel(path), "is not valid JSON ({})".format(exc))
        return

    table = data.get("value_table") or {}
    for roll in range(1, 19):
        entry = table.get(str(roll))
        if not entry:
            fail(rel(path), "value_table is missing entry {} - the rulebook table "
                            "is 1-18 and callers clamp into it".format(roll))
            continue
        template = entry.get("template", "")
        dice = entry.get("dice") or {}
        for name in dice:
            if "{%s}" % name not in template:
                fail(rel(path), "entry {} rolls {!r} but never uses it in its "
                                "template".format(roll, name))
        for name in re.findall(r"\{(\w+)\}", template):
            # {weight} is derived from the coin count, not rolled.
            if name not in dice and name != "weight":
                fail(rel(path), "entry {} uses {{{}}} but nothing rolls it - "
                                "format() will raise at play time".format(roll, name))
        for name, expr in dice.items():
            if not re.match(r"^\d+d\d+(\*\d+)?$", str(expr)):
                fail(rel(path), "entry {} has dice expression {!r} for {!r}, which "
                                "_treasure.roll_expr cannot parse".format(roll, expr, name))

    if not data.get("roll_again"):
        fail(rel(path), "has no roll_again entries - 15/16/17 give a result AND "
                        "send the roller back for another")

    objects = data.get("objects") or {}
    for category in ("object_type", "material", "gem_type", "color", "condition",
                     "provenance", "motif"):
        if not objects.get(category):
            fail(rel(path), "objects is missing or has an empty {!r}".format(category))
    for tier in ("mundane", "exotic"):
        if not (objects.get("material") or {}).get(tier):
            fail(rel(path), "material is missing its {!r} tier".format(tier))

    # Every trait the composer branches on must be carried by some object, or
    # that branch is dead code and the objects it was written for read as bland
    # rather than as broken.
    known = _literal_constant(module, "KNOWN_TRAITS") or ()
    if not known:
        fail(rel(module), "KNOWN_TRAITS could not be read - cannot check object traits")
    used = set()
    for entry in objects.get("object_type") or []:
        if not entry.get("name"):
            fail(rel(path), "an object_type entry has no name")
        for trait in entry.get("traits") or []:
            used.add(trait)
            if known and trait not in known:
                fail(rel(path), "object_type {!r} carries trait {!r}, which "
                                "_treasure.py does not understand and will "
                                "ignore".format(entry.get("name"), trait))
    for trait in known:
        if trait not in used:
            fail(rel(module), "KNOWN_TRAITS lists {!r} but no object_type in "
                              "treasure.json uses it".format(trait))


def check_monster_json():
    """monster_gen.py promises JSON on stdout; prove stdout stays parseable.

    Warnings, the seed notice and the yaml reminder all go to stderr precisely
    so a caller can pipe stdout straight into a parser. That contract is easy
    to break with a stray print(), and nothing else here would notice.
    """
    script = SCRIPTS / "monster_gen.py"
    if not script.is_file():
        return

    cases = [
        (["cavern", "--seed", "3"], "setting"),
        (["cavern", "--party-levels", "4", "--random", "2", "--seed", "3"], "setting"),
        (["--custom", "--random", "--treasure", "--seed", "3"], "custom"),
    ]
    for extra, label in cases:
        result = run("scripts/monster_gen.py", *extra)
        if result.returncode != 0:
            fail(rel(script), "{} exited {}".format(" ".join(extra), result.returncode))
            continue
        try:
            payload = json.loads(result.stdout)
        except ValueError as exc:
            fail(
                rel(script),
                "stdout is not valid JSON for '{}' ({}) - something is "
                "printing to stdout that belongs on stderr".format(
                    " ".join(extra), exc
                ),
            )
            continue
        if not payload.get("monsters"):
            fail(rel(script), "'{}' returned no monsters".format(" ".join(extra)))
            continue
        if label == "setting":
            missing = [
                m.get("name", "?")
                for m in payload["monsters"]
                if not m.get("instinct") or not m.get("moves")
            ]
            if missing:
                fail(
                    rel(script),
                    "bestiary monsters came back without instinct/moves: {} - "
                    "the whole point of preferring official monsters is that "
                    "these are already written".format(", ".join(missing)),
                )


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

        # Zip payloads are LF-canonical; rot13'd members and plain text members
        # must not smuggle CR into the archive (Windows line-ending noise).
        with zipfile.ZipFile(archive) as zf:
            for name in zf.namelist():
                raw = zf.read(name)
                if b"\r" in raw:
                    fail(
                        rel(save),
                        "zip member {!r} contains CR bytes; session zip text "
                        "must be LF-only".format(name),
                    )

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


def main(argv=None):
    global QUICK
    parser = argparse.ArgumentParser(
        description="Validate the dungeon-world-gm skill.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="trim the per-seed sweeps to a single seed for a fast local loop. "
        "Every check still runs, but with less coverage - CI must run the full "
        "sweep, so do not use this as your pre-push check.",
    )
    args = parser.parse_args(argv)
    QUICK = args.quick

    fastjsonschema, yaml_mod = load_bundled_deps()
    if yaml_mod is None:
        print("FAIL: " + errors[0])
        return 1

    if not SKILL_DIR.is_dir():
        print("FAIL: {} does not exist".format(rel(SKILL_DIR)))
        return 1

    check_frontmatter(yaml_mod)
    check_skill_links()
    check_scripts()
    check_no_external_imports()
    check_determinism()
    check_encoding_safety()
    check_lexicon()
    check_treasure_asset()
    check_monster_json()
    if QUICK:
        skipped.append("session save/load round-trip (check_session_roundtrip)")
    else:
        check_session_roundtrip()
    check_schemas(fastjsonschema, yaml_mod)
    check_digest()
    check_yamledit_pin(yaml_mod)
    check_tracked_files()

    for warning in warnings:
        print("warning: " + warning)
    for error in errors:
        print("error:   " + error)

    suffix = " [QUICK - PARTIAL RUN]" if QUICK else ""
    if errors:
        print("\n{} error(s), {} warning(s){}".format(len(errors), len(warnings), suffix))
        return 1
    print("\nskill validation passed ({} warning(s)){}".format(len(warnings), suffix))
    if QUICK:
        print("  --quick reduced this run:")
        print("    - seed sweeps cut to 1 seed (determinism, encoding safety)")
        for item in skipped:
            print("    - skipped: " + item)
        print("  Run without --quick before pushing; CI always runs the full sweep.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
