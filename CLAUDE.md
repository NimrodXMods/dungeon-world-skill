# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Committing

**Never commit automatically.** Do not run `git commit`, `git push`, or `git tag` on your own
initiative — not after finishing a change, not at the end of a task, not "to be safe." When work
reaches a point where a commit makes sense, stop and tell the user, then wait for them to ask.

## What this repo is

This repo is not an application — it is the source of a single distributable **Claude Skill**,
`skills/dungeon-world-gm/`, for running the tabletop RPG Dungeon World. Everything outside that
directory is packaging (`.gitignore`, VS Code workspace, empty `README.md`). The deliverable is the
skill directory itself: prose references an LLM reads at runtime, plus Python scripts it shells out to.

Two audiences must be kept in mind when editing: the **model at play time** (context is scarce; every
file should be read only when needed) and the **maintainer**. Most of the "architecture" is really
context-budget discipline.

## Layout and how the pieces relate

- `SKILL.md` — the entry point and the only file loaded unconditionally. It encodes the session state
  machine (Session Start → Main Gameplay Loop → Session End), which reference files to read when, and
  the rules for calling every script. **Any change to a script's interface, a reference file's name, or
  the file-state scheme must be mirrored in `SKILL.md`** — the model has no other index.
- `references/*.md` — topic files, cross-linked as `[[filename-without-extension]]`. Each is listed in
  SKILL.md's "Reference Index" with an explicit read-eagerly / read-on-demand note. Preserve that
  distinction when adding files; a new reference that isn't in the index is invisible at runtime.
- `references/rulebook-digest/` — an `advanced-digest`: `L0-index.md` (coverage map) → `L1-digest.md`
  (one paragraph per section + atomic `F-NNN` facts) → `source/core-rulebook-full-text.txt` (full
  `pdftotext -layout` conversion, ~670KB, with `===== PAGE N =====` markers). The digest is
  deliberately lossy compression against the authoring model's weights; page markers exist so L3
  lookups are `grep -n "===== PAGE 91 ====="` rather than whole-file reads. Never read the source file
  wholesale.
- `scripts/*.py` — generators and utilities, all stdlib-only, invoked as `python3 scripts/<name>.py`.
- `assets/yaml_templates/` and `assets/yaml_schemas/` — the campaign state format. Templates double as
  runtime documentation; schemas are *selectively* open (fixed shapes like `hp` closed so typos error,
  containers like fronts/NPCs open so campaigns can grow fields).

## Runtime state model

Campaign state lives in files, not model memory: `<name>_<class>.yaml` character sheets and one
`<campaign_slug>_gmsecret.yaml` (GM-only, never shown to the user). `session_save.py` packages these
into a downloadable zip, rot13-ing the gmsecret and `handoff.md` so a player can hold the file without
spoiling themselves; `session_load.py` reverses that and prints a summary. rot13 here is
spoiler-obfuscation, not security — don't "upgrade" it to encryption.

Edits to those YAMLs go through `scripts/yamledit.pyz` (a bundled yamlpath-based tool) with
`--schema assets/yaml_schemas/<type>.schema.yaml` passed on every call — there are two document types,
so no single configured default works.

## Script conventions

Every script carries a `--help-llm` flag printing a dense LLM-facing reference; this is the
canonical interface documentation, intentionally *not* duplicated as examples in `SKILL.md` (which
would drift). **A new or changed script must keep `--help-llm` accurate.**

`*_gen.py` scripts take `--seed` for reproducibility. That flag is development-only — SKILL.md
forbids the model from using it at play time, so don't add gameplay guidance that relies on it.

## Working commands

There is no build, no test suite, no linter configured. Verification is manual:

```bash
# smoke-test a generator (repo root)
python3 skills/dungeon-world-gm/scripts/idea_gen.py --seed 1
python3 skills/dungeon-world-gm/scripts/roll.py 2d6+1 --moves
python3 skills/dungeon-world-gm/scripts/<name>.py --help-llm   # check LLM docs still render

# check a template still validates against its schema
python3 skills/dungeon-world-gm/scripts/yamledit.pyz \
  skills/dungeon-world-gm/assets/yaml_templates/character_template.yaml \
  --get hp --schema skills/dungeon-world-gm/assets/yaml_schemas/character.schema.yaml
```

Note: the Bash tool's working directory persists between calls — `cd` to the repo root explicitly
rather than assuming it.

## CI and releasing

`.github/workflows/validate.yml` runs `tools/validate_skill.py` on every push and PR;
`release.yml` runs it again on `v*` tags, then packages and publishes. Run the validator
locally before pushing — it is the pre-flight command for this repo:

```bash
python tools/validate_skill.py
```

It enforces the conventions described above that nothing else can: wikilinks resolve, no
reference file is orphaned from the index, generators still answer `--help-llm`, templates
still satisfy their schemas, the rulebook's page markers are contiguous, and
`scripts/yamledit.pyz` still matches `tools/yamledit.lock` (version + sha256). The validator
has no pip dependencies — it borrows `ruamel.yaml` and `fastjsonschema` off the vendored
pyz's `sys.path`, so keep it that way.

Releasing: the frontmatter version should already be current (see the next section — it is
kept up to date with every skill edit, not bumped at release time), so releasing is just
commit, then tag `vX.Y.Z` matching `metadata.version`. The tag's version must equal the
frontmatter's or the release job fails by design. A tag
with a suffix (`v0.8.0-rc1`) publishes as a prerelease against the same base version.
**Tagging is a commit-class action — ask the user, never tag automatically.**

## Skill frontmatter — update it automatically, every time

**Any edit to anything under `skills/` requires updating that skill's `SKILL.md`
frontmatter in the same change.** This is not a release-time step and it is not something to
ask about — do it as part of the edit, whether you touched a reference file, a script, a
schema, a template, or SKILL.md itself. If a change spans more than one skill, update each
affected skill's own frontmatter.

Three fields, always together:

- `metadata.version` — bump per the policy below.
- `metadata.updated` — today's date, `"YYYY-MM-DD"`.
- `metadata.last-modified-by-model` — the model making the edit, in the existing
  `Vendor Model Name (model-id)` form, e.g. `Anthropic Claude Opus 5 (claude-opus-5)`.
  Overwrite it; it records who touched it last, not a history. Leave `creator-model` alone.

Semver policy for `metadata.version`:

| Part | When |
|-------|------|
| major | Only ever for major changes — a redesign, a break in how the skill is used or how campaign state is stored. |
| minor | Any feature or functionality addition. |
| patch | Any fix, or an extremely trivial addition. |

Never bump more than one part, and never bump for a change that doesn't touch `skills/`
(edits to `tools/`, workflows, or this file are not skill changes).

CI enforces this: `tools/check_version_bump.py` fails the build when a commit touches a
skill without moving its `metadata.version`, when the version moves but `metadata.updated`
doesn't, or when the version goes backwards. It can't judge *which* part you bumped — that
part is still on you. Run it locally against whatever you're branched from:

```bash
python tools/check_version_bump.py --base origin/main
```

## Licensing

The skill is CC-BY-NC-SA-4.0 and distills the Dungeon World core rulebook plus fan supplements. All
credit/copyright detail lives in `references/ATTRIBUTION.md`, deliberately isolated so it never
consumes play-time context — keep new attributions there rather than inline.
