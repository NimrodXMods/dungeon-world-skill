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
  (one paragraph per section + atomic `F-NNN` facts) → `source/xml/` (the authors' own published
  rulebook XML, 37 files, ~700KB, vendored byte-identical from `Sagelt/Dungeon-World` at a pinned
  SHA — see `source/ATTRIBUTION.md`). The digest is deliberately lossy compression against the
  authoring model's weights; L3 exists so exact wording is recoverable.
  - L3 is addressed by **anchor**, not page: `scripts/rulebook.py --anchor moves#basic-moves/hack-and-slash`.
    Anchors are computed from the heading path at read time and never stored in the XML, which is
    what keeps an upstream refresh a clean diff. Each `L1-digest.md` section header carries its own
    `[xml:...]` anchor. Never read the XML files directly or wholesale.
  - The `(pNN-NN)` page ranges in the digest are retained **only** so the model can tell a user
    where to look in a printed 1st edition. Nothing resolves them and CI cannot check them. Don't
    reintroduce page-based lookup.
  - Known gap: the Tag Reference appendix is print-only and absent upstream; `[[tag-reference]]` is
    the authority for it.
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
canonical interface documentation. **A new or changed script must keep `--help-llm` accurate.**

### All script documentation goes in `--help-llm`, not `SKILL.md`

`--help-llm` is the **single source of truth** for how a script is invoked. Do not put script
documentation in `SKILL.md` unless it genuinely cannot live in `--help-llm`.

The reason is drift, and it is one-directional: `--help-llm` ships inside the script, so changing
the code and the help together is a single edit that CI can smoke-test. Anything copied into
`SKILL.md` is a second copy with nothing tying it to the code — it goes stale silently, and a
stale instruction in `SKILL.md` is worse than no instruction, because the model reads `SKILL.md`
unconditionally and trusts it.

`SKILL.md` may say **when to reach for a script** — that is routing, and it belongs there because
the model needs it before it has run anything. It must not say **how to call one**:

| Belongs in `SKILL.md` | Belongs in `--help-llm` |
|---|---|
| "Use `monster_gen.py` when the party runs into creatures" | flag names, arguments, defaults |
| "Never use `--seed` during play" (a play-time prohibition) | what `--seed` does |
| "Run `--help-llm` before first use each session" | output format, examples, exit codes |
| which script supersedes which reference file | how options interact, tuning constants |

Concretely: no flag lists, no usage examples, no output-format descriptions, no parameter
semantics in `SKILL.md`. If you catch yourself explaining an option there, the explanation belongs
in `--help-llm` and `SKILL.md` should point at it instead.

The rare genuine exception is a **safety or policy rule the model must know before it ever runs
the script** — the `--seed` prohibition is the archetype, since by the time `--help-llm` explains
the flag the model may already have used it. Keep such entries to one line and state the rule, not
the interface.

`*_gen.py` scripts take `--seed` for reproducibility. That flag is development-only — SKILL.md
forbids the model from using it at play time, so don't add gameplay guidance that relies on it.

### The monster difficulty formula is duplicated — keep it in sync by hand

`difficulty` is not in the upstream rulebook; it is invented by this repo. The formula lives in
**two places that CI cannot compare**, because `tools/` is not shipped inside the skill and the
skill's scripts may not import from it:

- `tools/extract_monsters.py` — `DIE_FACTOR` + `compute_difficulty()`, run once at extraction
  time to bake a `difficulty` number into every monster in `assets/monsters.json`.
- `skills/dungeon-world-gm/scripts/monster_gen.py` — `DIE_FACTOR` + `custom_difficulty()`, run at
  play time so a `--custom` monster carries a score on the same scale and can be compared against
  a `--party-levels` band.

```
difficulty = hp * (1 + armor*0.3) * DIE_FACTOR[die] * (1 + 0.2*flat_mod) * (1 + 0.3*special_count)
DIE_FACTOR = {4: 0.5, 6: 0.8, 8: 1.0, 10: 1.2, 12: 1.5}   # unlisted dice -> 2.0
```

**If you retune the extractor, `monster_gen.py` drifts silently.** Nothing errors: custom monsters
just start being scored on a different scale from bestiary monsters, so `--party-levels` filtering
quietly mismatches for one of the two. Change both together, and re-run `extract_monsters.py`
(diffing `monsters.json`) whenever the extractor side moves.

The two are *not* identical by nature and shouldn't be forced to be: the extractor reads Special
Qualities prose out of the source XML, whereas `custom_difficulty()` can only count the builder's
chosen qualities. It is deliberately an approximation — what must stay aligned is the **scale**,
not the exact number.

Consuming code — `CEILING_PER_LEVEL`, `ORG_MAX_COUNT` and `SOLO_THREAT_FRACTION` in
`monster_gen.py` — is calibrated against the *current* scale, so retuning the formula invalidates
that calibration too.

### monster_gen's difficulty filter is a ceiling, not a band

`--party-levels L` keeps a monster when `difficulty <= CEILING_PER_LEVEL * L`. There is
deliberately **no lower bound**, and organization plays no part in the filter.

An earlier version got this wrong twice over, and the reasoning is worth keeping so it isn't
reintroduced:

- It filtered on a `2L..8L` **band**, so options *slid* instead of accumulating. A level-10 party
  could not be offered a bandit — the whole `folk` setting emptied out at high level.
- It multiplied difficulty by an organization weight (Horde ×6). That pushed the classic
  low-level enemies *above* the ceiling: Skeleton (7.28 × 6 = 43.7) vanished for starting
  parties, the opposite of the intent.

The correct model: difficulty is **per creature**, and how many to field is the GM's call. So the
filter answers only "is a single one of these too much for this party?", and organization instead
drives `suggested_number` — how many make a real fight, capped by `ORG_MAX_COUNT` so a Solitary
monster never comes back as "bring seven". A strong party keeps access to weak monsters; they are
simply easy, which is what lets a GM run one straggling skeleton *and* know that ten would be a
threat.

`--solo-threat` (alias `--no-horde`) keeps only monsters worth `SOLO_THREAT_FRACTION` of the
ceiling on their own. Note it is *not* "needs exactly one to reach the ceiling" — by that test a
Lich fails against a level-10 party and the flag empties the setting.

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
  --schema skills/dungeon-world-gm/assets/yaml_schemas/character.schema.yaml <<'EOF'
hp -> ?
EOF
```

Note: the Bash tool's working directory persists between calls — `cd` to the repo root explicitly
rather than assuming it.

**Use the Bash tool for all commands in this repo**, even on Windows where a PowerShell tool is
also available. CI runs these same commands on Linux, so keeping local and CI on one dialect is
what keeps the commands above true in both places.

Do not mix shell dialects within a call. PowerShell syntax in a Bash call is the dangerous
direction, because it often stays *valid* Bash and fails silently — a PowerShell here-string
(`@'` … `'@`) used for a commit message parses as `@` plus a quoted string plus `@`, and quietly
wraps the message in stray `@` lines. For multi-line text use a quoted heredoc
(`git commit -F - <<'MSGEOF'` … `MSGEOF`), and verify with `git log -1 --format=%B` —
`git log --oneline` shows only the subject and hides exactly this corruption.

## CI and releasing

`.github/workflows/validate.yml` runs `tools/validate_skill.py` on every push and PR;
`release.yml` runs it again on `v*` tags, then packages and publishes. Run the validator
locally before pushing — it is the pre-flight command for this repo:

```bash
python tools/validate_skill.py
```

For a fast loop while iterating, `--quick` trims it from ~25s to ~8s:

```bash
python tools/validate_skill.py --quick
```

`--quick` cuts the per-seed sweeps to a single seed and skips the session save/load round-trip
(the most expensive single check). It prints exactly what it gave up and tags the result
`[QUICK - PARTIAL RUN]`. **It is not the pre-flight command** — a passing `--quick` run is not
evidence the build is green, because CI always runs the full sweep. Run the plain command before
pushing.

Nearly all of the runtime is subprocess spawning, not analysis, so if the validator gets slow
again look for a check that shells out per-seed or per-script rather than for slow logic.

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
- `metadata.updated` — today's date, `"YYYY-MM-DD"`. Unchanged is correct when today's
  date is already what's there: several edits in one day share a date.
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
skill without moving its `metadata.version`, or when `version`/`updated` move *backwards*.
It deliberately does not require `updated` to change — same-day edits share a date. It also
can't judge *which* part you bumped; that stays on you. Run it locally against whatever
you're branched from:

```bash
python tools/check_version_bump.py --base origin/main
```

## Licensing

The skill is CC-BY-NC-SA-4.0 and distills the Dungeon World core rulebook plus fan supplements. All
credit/copyright detail lives in `references/ATTRIBUTION.md`, deliberately isolated so it never
consumes play-time context — keep new attributions there rather than inline.
