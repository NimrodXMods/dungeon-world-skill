# AGENTS.md

Guidance for coding agents working in this repository. This is the canonical project
guide — [CLAUDE.md](CLAUDE.md) just points here, so there is nothing to keep in sync.

## Who may edit `CLAUDE.md`

**Only Anthropic Claude models may modify `CLAUDE.md`.** That file is Claude Code harness
specifics (tool names, `@`-imports, and similar). Project-wide rules belong here in
`AGENTS.md`.

If you are **not** an Anthropic Claude model:

- Treat `CLAUDE.md` as **read-only**. Do **not** update, rewrite, or “sync” it.
- You should not need to read it for normal work; prefer this file.
- Read `CLAUDE.md` only when there is a concrete need (e.g. the user asked about Claude
  Code wiring, or you are diagnosing something that clearly lives only there). Still do
  not modify it — if a change is required, tell the user (or leave it for Claude).

Humans may edit either file. Claude models that touch `CLAUDE.md` should keep general
rules out of it and point at `AGENTS.md` instead (see that file’s own “What belongs here”
section).

## Committing

**Never commit automatically.** Do not run `git commit`, `git push`, or `git tag` on your own
initiative — not after finishing a change, not at the end of a task, not "to be safe." When work
reaches a point where a commit makes sense, stop and tell the user, then wait for them to ask.

Tagging is commit-class too, and then some: pushing a `v*` tag triggers a public GitHub
Release. Always ask.

### After a PR merges

The repo has GitHub **"Automatically delete head branches"** enabled: the remote feature
branch is removed when the PR merges. That is intentional and safe here — GitHub still
offers restore / undelete of a deleted branch for a period afterward, so this is not a
permanent one-click loss of the ref.

Post-merge cleanup agents should do when asked:

1. Check out `main` (or the default branch) and `git pull`.
2. Delete only the **local** feature branch (`git branch -d <name>`).
3. **Do not** `git push origin --delete <name>` and **do not** flag a missing remote branch
   as a failure — auto-delete already handled it. Optional: `git fetch --prune` to drop
   stale remote-tracking refs.

## Before you push

Run both pre-flight checks CI runs:

```bash
python tools/validate_skill.py
python tools/check_version_bump.py --base origin/main
```

The first catches the repo's otherwise-unenforceable conventions (broken skill-root
Markdown links, leftover `[[wikilinks]]`, orphaned reference files, scripts that lost
`--help-llm`, templates that drifted from their schemas, third-party imports that won't
exist in the sandbox). The second catches a skill edit that forgot its frontmatter bump.
Both are described in more detail under [CI and releasing](#ci-and-releasing).

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
- `references/*.md` — topic files. Cross-link with **skill-root-relative Markdown links**
  (Agent Skills style), e.g. `[core-moves](references/core-moves.md)`, not Obsidian
  `[[wikilinks]]` (those do not render on GitHub and are not in the Agent Skills
  standard). Procedure packs live next to `SKILL.md` as `SKILL-*.md` and are linked the
  same way (`[Phase 2](SKILL-2-main-loop.md)`). Each topic is listed in SKILL.md's
  Reference Index with a load note; a new reference that is never linked is invisible
  at runtime (CI checks this).
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
  - Known gap: the Tag Reference appendix is print-only and absent upstream;
    [tag-reference](skills/dungeon-world-gm/references/tag-reference.md) is the authority for it.
- `scripts/*.py` — generators and utilities, all stdlib-only, invoked as `python3 scripts/<name>.py`.
- `assets/yaml_templates/` and `assets/yaml_schemas/` — the campaign state format. Templates double as
  runtime documentation; schemas are *selectively* open (fixed shapes like `hp` closed so typos error,
  containers like fronts/NPCs open so campaigns can grow fields).
- `tmp/` — gitignored scratch, at the repo root. Put anything temporary here: design notes,
  working files, one-off scripts, generator output you want to eyeball. Nothing in it ships or
  is committed, so prefer it over the system temp directory — it keeps the work next to the
  repo and visible to the user, and keeps stray files out of `git status`.

  This includes **design and plan documents**: a spec written before implementing an issue
  belongs in `tmp/docs/` (e.g. `tmp/docs/superpowers/specs/YYYY-MM-DD-<slug>-design.md`), not
  in a tracked `docs/` directory and not in the system temp directory. They are working
  documents for one change, so they are deliberately never committed — if something in one
  needs to outlive the change, put it in this file, in `SKILL.md`, or in the issue itself.
  Note the consequence: a plan doc exists only in the working copy that created it, so link
  or paste the relevant part into the GitHub issue if another session will need it.

## Runtime state model

Campaign state lives in files, not model memory: `<name>_<class>.yaml` character sheets, one
`<campaign_slug>_gmsecret.yaml` (GM-only, never shown to the user), and one
`<campaign_slug>_environment.yaml` (player-visible; see the dashboard section below).
`session_save.py` packages these
into a downloadable zip, rot13-ing the gmsecret and `handoff.md` so a player can hold the file without
spoiling themselves; `session_load.py` reverses that and prints a summary. rot13 here is
spoiler-obfuscation, not security — don't "upgrade" it to encryption.

`session_save.py --no-rot13` stores both plainly, for when the person holding the zip is
the GM (assistant mode, or a solo GM archiving prep). The choice is recorded by **filename**
— `_gmsecret.txt`/`_handoff.txt` when encoded, `_gmsecret.yaml`/`handoff.md` when plain — so
`session_load.py` takes no matching flag and cannot guess wrong. Since rot13 is its own
inverse, a guess would corrupt silently rather than fail, which is why the encoding is in the
name and not in a header.

Edits to those YAMLs go through `scripts/yamledit.pyz` (a bundled yamlpath-based tool) with
`--schema assets/yaml_schemas/<type>.schema.yaml` passed on every call — there are three document
types, so no single configured default works. `scripts/yamledit.yaml` does exist, but it sets
**only** the dashboard hook and deliberately no `schema`; don't add one.

### The player dashboard, and why the environment file exists

`scripts/dashboard.py` renders `DW_Dashboard.html`: a location header, a card per PC, and the
basic/special move reference. It is wired as yamledit's **post-write hook**, so every successful
edit rewrites the page and there is no step for the model to remember.

Three things here are load-bearing and easy to undo by accident:

- **`dashboard.py` must never read `*_gmsecret.yaml`.** The page is what the player is looking at,
  and the gmsecret is rot13'd on save precisely so holding the zip doesn't spoil them. The
  exclusion is by *filename, before any read* — keep it that way rather than filtering content
  later. The spoiler canary in `check_dashboard_hook()` is the regression test that matters.
- **`<slug>_environment.yaml` is not a copy of the gmsecret's `current_location`.** The gmsecret
  records ground truth; the environment file records what the characters *perceive* — what they
  see, are told, or believe, which may be wrong. The party may know a place only as "A Suspicious
  and Evil-Looking Forest of Weirdness" while the gmsecret calls it "Wizard X's Forest of
  Experiments". Divergence is the feature. Do not "deduplicate" them.
- **A failing hook is silent by design.** yamledit warns to stderr and does not change its exit
  code, so a broken dashboard can never make the model think its edit failed. The cost is that a
  typo in `yamledit.yaml` breaks the feature with no symptom, which is why `check_dashboard_hook()`
  runs a *real* yamledit write and asserts the page appeared.

The page is a static template (`assets/html_templates/dashboard_template.html`) plus one injected
JSON blob spliced between two `<!--DW-DATA-...-->` markers. Every value reaches the DOM through
`textContent`; `dashboard.py` has exactly one data path and one escaping rule, and nothing may
route around it with `innerHTML`.

**The `<script>` raw-text trap.** The content of a `<script>` element is raw text, so those HTML
comment markers are *not* comments there — the page receives them as literal characters around the
JSON, and `JSON.parse` throws unless they are stripped first. That failure is invisible: the catch
falls back to the "no campaign loaded" placeholder, which looks exactly like a working page with an
empty campaign. This shipped once. Two consequences:

- The template's renderer must strip the markers before parsing, and `check_dashboard_hook()`
  asserts it does.
- **Verify the page by executing its JS against what a browser actually hands it** — extract the
  `#dw-data` element's raw text verbatim, markers and all. A checker that slices the JSON out
  itself tests a situation no browser produces and will pass a completely broken page. The same
  rule applies to the validator, which is why it reads the carrier with a regex rather than
  slicing between markers.

## Script conventions

Every script carries a `--help-llm` flag printing a dense LLM-facing reference; this is the
canonical interface documentation. **A new or changed script must keep `--help-llm` accurate.**

### Script output is also a memory aid — seed it with clues about what to do next

The model reading a script's output is hours into a session and its attention has drifted. It
read `--help-llm` once, long ago, and `SKILL.md` before that. **Assume it has forgotten what
else the script can do, and what the result is meant to be used for.** Output is the only
channel that reaches it at the moment it is actually deciding something, so spend a little of
that output reminding it.

In practice, results should carry small pointers to the next or alternative action:

- **Echo the exact token that produced a block**, so asking again does not require recalling
  the spelling: `=== Treasure Object: material === [ TABLE=treasure-object:material ]`.
- **Name the sub-options a result was built from**, which advertises axes the model would
  otherwise never learn existed — `idea_gen.py`'s composed objects print a `rolled on:` line
  listing the `treasure-object:CATEGORY` tokens behind them, so rerolling one detail instead of
  the whole object becomes an obvious move rather than a documented one.
- **Route to the right tool when the result is only a seed**, e.g. `idea_gen.py`'s discovery and
  danger creature lines end with `(seed only - stat it with monster_gen.py)`.
- **Restate standing obligations** the model drifts away from — the yaml-update and
  re-roll-is-allowed reminders every `idea_gen.py` run ends with are the oldest example.

This is a real cost in tokens and in visual noise, so it buys the most where a capability is
*invisible* from the output alone. A hint nobody needs is clutter; keep them terse, keep them
next to the thing they describe, and prefer one line over a paragraph. Note the tension with
the rule above: `--help-llm` remains the canonical *interface* documentation, and these hints
are not a second copy of it — they are pointers, not explanations.

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

### Generated assets: regenerate, don't hand-edit

`assets/monsters.json` and `assets/moves.json` are build products of `tools/`, which is
not shipped inside the skill. Edit the extractor and re-run it; a hand-patch is lost the
next time anyone regenerates.

- `tools/extract_moves.py` → `assets/moves.json` — basic moves, special moves, and every
  class's starting/advanced moves, read out of the vendored rulebook XML for the player
  dashboard. Paragraphs are stored as bold/plain **spans** rather than HTML so the page can
  keep the rulebook's bolded trigger while still setting every string with `textContent`.

  ```bash
  python3 tools/extract_moves.py \
      skills/dungeon-world-gm/references/rulebook-digest/source/xml \
      skills/dungeon-world-gm/assets/moves.json
  ```

  The parser walks a *layout*-driven document — headings and their prose are siblings
  inside `<Story>`/`<Body>`/`<div>` wrappers that nest differently from file to file, which
  is why it flattens containers into one stream instead of recursing structurally. That
  makes it quietly fragile against an upstream refresh: a changed wrapper yields a valid
  JSON file with empty move lists. `check_moves_asset()` in the validator is the guard —
  it enforces move-count floors and that no move has empty text.

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

# rebuild the dashboard for a scratch campaign under tmp/ (the hook does this
# automatically on any yamledit write; run it by hand to force or debug)
python3 skills/dungeon-world-gm/scripts/dashboard.py --dir tmp/<campaign> --out tmp/x.html
```

For dashboard *rendering*, opening the file in a browser is the only way to judge the CSS, but the
DOM the JS builds can be checked without one: run the page's own renderer against a small DOM stub
under `node`, feeding it the `#dw-data` element's raw text verbatim (see the `<script>` raw-text
trap above — a stub that pre-slices the JSON proves nothing). Such harnesses belong in gitignored
`tmp/`, so they exist only in the working copy that wrote them.

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

`--quick` cuts the per-seed sweeps to a single seed and skips the two checks that shell out
heavily — the session save/load round-trip and the dashboard hook end-to-end test. It prints
exactly what it gave up and tags the result
`[QUICK - PARTIAL RUN]`. **It is not the pre-flight command** — a passing `--quick` run is not
evidence the build is green, because CI always runs the full sweep. Run the plain command before
pushing.

Nearly all of the runtime is subprocess spawning, not analysis, so if the validator gets slow
again look for a check that shells out per-seed or per-script rather than for slow logic.

It enforces the conventions described above that nothing else can: skill-root Markdown
links resolve, no `[[wikilinks]]` remain, no top-level reference file is orphaned from the
link graph, generators still answer `--help-llm`, templates still satisfy their schemas,
the rulebook's page markers are contiguous, `assets/moves.json` still carries real move text,
the dashboard hook still fires and still keeps the gmsecret off the page, and
`scripts/yamledit.pyz` still matches
`tools/yamledit.lock` (version + sha256). The validator has no pip dependencies — it
borrows `ruamel.yaml` and `fastjsonschema` off the vendored pyz's `sys.path`, so keep it
that way.

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
- `metadata.updated` — today's date in **UTC**, `"YYYY-MM-DD"`. Use the UTC calendar
  day (CI runners typically run in UTC; a local evening commit must not use a
  local date that is still "yesterday" in UTC). Unchanged is correct when today's
  UTC date is already what's there: several edits in one day share a date.
- `metadata.last-assisting-model` — when a coding model assisted with the change,
  overwrite this with that model in `Vendor Model Name (model-id)` form, e.g.
  `Anthropic Claude Opus 5 (claude-opus-5)` or `xAI Grok 4.5 (grok-4.5)`. Leave
  `creator-model` alone.

  **Meaning (narrow):** the last model that *assisted the human* on any edit to
  this skill — a breadcrumb for maintainers, not a history and not an audit log.

  **Not meaning:**
  - Not blame or praise for the quality of the last update.
  - Not a claim that the last update was primarily model-generated vs human-authored.
  - Not "the model responsible for this skill" or "who owns this version."
  - Not evidence of who decided the design; humans may drive the change while a
    model only applies diffs, or the reverse.

  If a human edits with no model assist, they may leave the field unchanged or
  set it only when a model later helps. Agents that *do* assist must overwrite it
  with themselves as part of the edit.

  **Name history:** formerly `last-modified-by-model`. Renamed so it cannot be
  read as "this model made / is accountable for the last modification."

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
