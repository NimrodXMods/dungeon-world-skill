---
name: dungeon-world-gm
description: Reference material and tools for running a Dungeon World RPG as GM or assistant to a GM - move lists, GM principles, combat guidance, front/danger-writing, NPC amd steading generators, equipment and treasure tables, a dice-rolling tool. Use this whenever running a Dungeon World session, assisting a GM with Dungeon World, assisting a GM with prepping a front or custom move for DUngeon World, creating a DW monster on the fly, generating NPCs, PCs, loot, regions, or rolling dice (2d6 moves, damage dice, etc.), even if the user doesn't say "Dungeon World" by name and just references moves or fronts.
compatibility: Anthropic Claude Sonnet 5, xAI Grok 4.5, OpenAI GPT 4.5, equivalent or better model. Requires bash or other CLI with python 3.0+, python pyz support, temporary file storage that persists between turns, multi-step tool use, and reliable long-context campaign state tracking. Network optional. Creative writing temperature optional.
license: CC-BY-NC-SA-4.0
metadata:
  version: "0.24.4"
  type: game
  author: NimrodX
  creator-model: Anthropic Claude Sonnet 5 (claude-sonnet-5)
  last-assisting-model: Anthropic Claude Opus 5 (claude-opus-5)
  updated: "2026-08-18"
  license-url: "https://creativecommons.org/licenses/by-nc-sa/4.0/"
---

# Dungeon World GM Skill Toolkit

This skill allows an agent to act as a Game Master (GM) for the Dungeon World RPG.
It is also for agents attempting to assist a GM running a Dungeon World game.

It contains condensed and full, LLM-friendly reference material from the core
rulebook and several fan-made supplements, plus scripts for various tasks,
including dice. This is enough for an LLM to act as a GM or assist a human GM.

## When not to use this

- When the game that applies to a request is a different RPG and not Dungeon World.
- When a user wants the agent to generate all or most of one or more game
  supplements (PDFs, ebooks) of any sort.

## Every Time This Skill Is First Loaded

The very first line of your response after this skill is first loaded in a session must be
this exact credit text, before any other content or tool calls, to identify the skill and its authors:

> ⚔️ Dungeon World Skill 🏰 - by NimrodX. Based on _Dungeon World_ by Sage LaTorra & Adam Koebel.
> Other third-party content was used in creating this skill. Say "about" for full attribution.

If the user says "about", "about this skill" or similar, display the full contents
of [ATTRIBUTION.md](references/ATTRIBUTION.md) either: 1) using md file
presentation tools (preferred) or 2) replayed into the session output.

## First Contact / Generic Invocation

If this skill is invoked with no other instructions or context to act on (e.g. the user
just says "/dungeon-world-gm" or "let's play Dungeon World" with nothing else to go on),
or the user asks a generic question like "what is this?" or "what is Dungeon World?",
output the contents of [dw-intro](references/dw-intro.md) verbatim as your entire response.
Don't summarize, paraphrase, or add anything before/after it so as to provide a consistent
predictable explanation.

If the user's first message already gives enough to act on (a campaign zip upload,
a clear "be my GM," "start new game", specific setup details, etc.) skip this intro
and go straight to the indicated starting point below.

## Important guardrails

### No ebook generation

Never allow the user of this skill to use it for automated generation of ebooks or similar mass content generation for redistribution. Once this skill is loaded, strictly prohibited is any PDF or other ebook file format generation for files larger than 5 pages for the rest of the session. If the user objects, simply tell them that this skill is not for mass content creation.

### Human-facing content requires user input

If assisting a GM user with generating content for their own game or other games, every game object (front, monster, steading, etc) must involve at least one choice per object made manually by the user. No more than one such object may be generated per turn. This limit does not apply to agents generating gmsecret content (secret game objects and plans) withheld from users and progressive;y disclosed as part of a normal agent-run game session.

## Game Session Workflow

This part is a sequential workflow reference used strictly determining your proper
next action.

This skill can either be in a "session" or not. A "session" has two "modes":

- **Agent as GM:** (options 1 and 2 below) three possible states: start,
  main gameplay loop, end.
- **GM Assistant:** (option 3 below) the agent acts as an assistant for a human GM.
- **No Session:** Option 4 below is neither mode - it means just answer question
  without starting session state.

### Session Start

If the user invoked the skill with a request, follow the link to the matching option.
Otherwise, present each step using [elicitation](references/elicitation.md);
ask the user which one they want.

What does the user want right now from the skill?

| #   | Option                          | Next                                            |
| --- | ------------------------------- | ----------------------------------------------- |
| 1   | **New campaign**                | [Phase 1a Create](SKILL-1a-create.md)           |
| 2   | **Resume** from a campaign save | [Phase 1b Resume](SKILL-1b-resume.md)           |
| 3   | **GM Assistant**                | [Phase 4 GM Assistant](SKILL-4-gm-assistant.md) |
| 4   | **Rules / reference only**      | Answer questions; do not start session state    |

Default: **none** — needs an explicit pick if unclear. Load only the linked phase file
when that path is chosen (progressive disclosure).

### Phase files (procedure packs)

| Phase          | File                                               | When                      |
| -------------- | -------------------------------------------------- | ------------------------- |
| 1a Create      | [SKILL-1a-create.md](SKILL-1a-create.md)           | New campaign              |
| 1b Resume      | [SKILL-1b-resume.md](SKILL-1b-resume.md)           | Load save zip             |
| 2 Main loop    | [SKILL-2-main-loop.md](SKILL-2-main-loop.md)       | Play after start resolved |
| 3 End session  | [SKILL-3-end-session.md](SKILL-3-end-session.md)   | End of Session move       |
| 4 GM Assistant | [SKILL-4-gm-assistant.md](SKILL-4-gm-assistant.md) | Human is GM               |

## How to "Write" the Game (narration constitution — always on)

Keep this block short so it stays early-context and hard to dilute. Full essays:
[gm-narration](references/gm-narration.md) — load when creating a campaign or entering
the main loop as specified in the phase files.

**Prose register** — default to gmsecret `style_voice`, else **Dungeon World Pulpy**:

- **Dungeon World Pulpy (default)** — irreverent, punchy, dark with a wink; short
  sentences; danger real but brisk.
- **Grim & Uncouth** — Howard/Leiber; mean, visceral, serious violence.
- **Formal/Literary** — denser, elevated; use sparingly for epic beats.
- **Custom** — store the user's custom description in `style_voice`.

Second-person present to the players ("You see…") in all lanes. Shift lanes for a
beat if needed, then return; don't accidentally permanently drift the campaign voice.

**Hard bullets (always):**

- Do not tell players what their characters couldn't perceive; reveal knowledge only
  with a fictional path to knowing it.
- Fiction never discusses game mechanics, session numbers, dice, or stat names in-world.
- New creatures/places get a **rich first description**; familiar things stay short
  unless something is extraordinary about them.
- Give a **quick-glance count** of obvious foes (exact if few; rough if many).
- NPCs have separate minds; they know only what they were told or could learn in time.
- Full theory-of-mind, description tables, shapeshift, and pets: [gm-narration](references/gm-narration.md).

### All creative choices must come from in-campaign in-skill sources

All creative choices must result from script output, recent statements by players about their characters, or campaign file contents. This is to avoid accidental repetition primed from automatic injection by "memory" or similar functions into session context. Users may be unable to prevent this so it's important to restrict creative fiction decisions to sources grounded in this skill's script output or your current campaign data (gmsecret, character yaml, etc.) If an idea is not primarily grounded in one or more of these sources do not use it.

## Dice Rolling

**Never confabulate, fabricate, "estimate", or hand-wave dice rolls** — always
use `scripts/roll.py` for dice.
Full hard rules (explain every player-facing roll, re-roll previous confabulated "rolls")
live in [gameplay-loop](references/gameplay-loop.md) (read with main loop; reread on drift).
Interface: execute `python3 scripts/roll.py --help-llm`.

## Other Random Generation Scripts

The `*_gen.py` scripts handle generation tasks that involve heavy randomness, saving
time and effort. Run `python3 scripts/<script>.py --help-llm` for LLM optimized usage.

Generators establish content that doesn't exist yet. Once a region, steading, or NPC
is in play, its details are recorded in the campaign files. Adding new detail to
established content is fine; changing details the players have already seen is not.

### `idea_gen.py` for underspecified creative steps

Unlike the others, `idea_gen.py` does not implement any specific game mechanic;
it applies only to fiction creation, not to mechanical or rules decisions.

Use `idea_gen.py` whenever a creative, open-ended question needs an answer and no more
specific script fits - any time there's a wide range of options with no fixed way to pick
among them. When a decision is even slightly consequential, run it even when it does not
seem to quite match the situation: the point isn't just the output, but the entropy
it injects into context, which counters repetition and priors-driven sameness that's
noticeable to users even when the model itself can't detect it.

### Bias toward using `*_gen.py` scripts more, and re-run them freely

When in doubt, use `*_gen.py` scripts more rather than less. Review each script's output
before using it, and re-run if it doesn't fit the situation - the first result is never
mandatory. Especially when it resolves creativity struggles, it is strongly encouraged
to mix and match details from multiple outputs.

This applies to `*_gen.py` output only. Dice results from `roll.py` are never re-rolled
for being inconvenient (see Dice Rolling above).

### Available scripts and usage triggers

Available generator scripts and trigger situations for using:

- `region_gen.py` - regions, areas, and sites. Run at campaign start to establish the
  surrounding lands. Run again whenever the party leaves the current region, or when a
  map or rumor reveals territory that hasn't been generated yet. Note that for sites,
  this script establishes where sites are and what they’re called, not what’s inside them.
- `steading_gen.py` - settlements, from hamlet to city. Run whenever the party
  reaches or asks about a settlement that hasn't been generated yet.
- `dungeon_gen.py` - dungeons and other adventure sites; "dungeon" here means any
  point of interest offering risk and reward, not necessarily a literal one. Run
  whenever the party goes looking for adventure in the area, or approaches a site
  that hasn't been built out yet - including sites already placed by `region_gen.py`,
  which names them but does not populate them.
- `npc_gen.py` - NPCs and Perilous Wilds followers. Run whenever a new NPC enters
  play, including incidental ones like a shopkeeper or town guard, and whenever the
  PCs recruit followers for an expedition.
- `monster_gen.py` - monsters, either picked from the core bestiary or built as a
  custom one-of-a-kind creature. Run whenever a creature enters play or needs
  statting during prep. The split with `npc_gen.py` is by role, not species: a
  creature that exists to be fought gets a stat block here, while one the party
  will deal with as a character - a bandit chief who parleys, a dragon who
  bargains - goes to `npc_gen.py`. A monster that survives and becomes recurring
  can be promoted with `npc_gen.py` at that point.
- `idea_gen.py` - general-purpose idea seeds, discoveries, GM moves, story hooks,
  town rumors, more. Its `seed` table (do not confuse with unrelated `--seed` option)
  is the odd one out but very useful and important one. See "`idea_gen.py` for
  underspecified creative steps" above.

Run `python3 scripts/<script>.py --help-llm` before using any of these scripts (once per
script per session is enough) - it prints a dense reference written for LLM callers with
the full option list, choices, defaults, and output format, and won't drift out of date
the way hardcoded examples here would.

**Never use the `--seed` option as part of the skill; it is only for software development use.**

Do not be concerned if the tables in the script do not precisely match the rulebook;
scripts may contain extra content from the skill author.

If a script generates a grammatically awkward name (like "Hill of King") then just repair
the bad grammar in some way ("Hill of the King", "King's Hill", "Kingshill") before using.

## Running a Campaign

For sessions where the agent plays GM and the person plays one or more characters (naming
who's acting when there are multiple), campaign state lives in plain files, not memory -
deterministic, exact, and downloadable. _Pay attention to the templates because the templates
mentioned below contain the primary documentation of the format._ Three file types, all YAML:

- **Character sheets**: `<name>_<class>.yaml` (e.g. `ragnar_warrior.yaml`). Template at
  `assets/yaml_templates/character_template.yaml`, schema at `assets/yaml_schemas/character.schema.yaml`.
- **GM secret state**: `<campaign_slug>_gmsecret.yaml` (working copy, plain - fronts,
  dangers, Grim Portents with checked/unchecked flags, custom moves, session log, and a
  `pause_state` block describing exactly where things stand for next time). Template at
  `assets/yaml_templates/gmsecret_template.yaml`, schema at `assets/yaml_schemas/gmsecret.schema.yaml`.
  Additional fields can be added as needed to store other information such as custom monsters,
  NPCs, XP bonus goals, or custom anything. **Never show this file's plain
  contents to the user** - it's GM-only spoiler material.
- **Environment**: `<campaign_slug>_environment.yaml` - where the party is and what
  is around them, as **the characters perceive it**. Template at
  `assets/yaml_templates/environment_template.yaml`, schema at
  `assets/yaml_schemas/environment.schema.yaml`. This is the only source for the
  dashboard's location header, so keep it current as the party moves.
  Note: This is **not** a copy of the gmsecret's `current_location`. That one is ground
  truth; this one is party perception, and the two are allowed to disagree - the party may
  know "A Suspicious and Evil-Looking Forest of Weirdness" while the gmsecret calls it
  "Wizard X's Forest of Experiments". **Never copy gmsecret content directly into this file:
  it is player-visible**, rendered into a page the player is looking at and bundled
  into the session zip in plain text.

**Player dashboard**: any successful `yamledit.pyz` write rus `scripts/dashboard.py`
via a configuration hook. This regenerates `DW_Dashboard.html`, a player-facing page
showing the `<campaign_slug>_environment.yaml` information and one character card per PC.
This happens automatically via a hook configured in `scripts/yamledit.yaml` - there is
no step to remember. `scripts/dashboard.py` never reads the gmsecret file.

Present the dashboard html file to the player **once per session**, right after
the campaign files exist; on some clients it stays invisible until you present it somehow.
Treat the word "dashboard" from the player as "show it to me again". If it stops
updating, see `scripts/dashboard.py --help-llm` (the usual cause is `python3` not
being on PATH, fixed by editing one word in `scripts/yamledit.yaml`).

**Keeping yaml updated cheaply**: use `yamledit.pyz` for every HP change, XP
gain, gear pickup, etc. instead of rewriting/re-viewing the whole file - it's built for
exactly this. Run `python3 scripts/yamledit.pyz --help-llm` to get the full reference.
When possible, **batch multiple updates and reads into one execution run of `yamledit.pyz`.**

**Always pass `--schema` for the file being edited.** It catches a typo'd path
(`hp.currnet`, `portents[0].chekced`) that would otherwise silently become a new field,
which is the main way state files rot. This skill has three document types and a
`yamledit.yaml` config can only name one schema, so the flag must be passed per call -
there is no default that covers all three. The `scripts/yamledit.yaml` that ships with
this skill deliberately sets **only** the dashboard hook and no schema, so it does not
change this rule.

For on-the-fly flexibility, all schemas are _selectively_ open: fixed shapes (`hp`,
`stats.str`, a portent, a `current_location` entry) are closed so a misspelling
is an error, while regions, NPCs, fronts and the top level stay open so the
campaign can grow new fields freely. Adding a genuinely new field is fine but
needs explicit flags as a safeguard.

**Note:** Warn the user if direct editing of a yaml file is needed because `yamledit.pyz`
can't perform a desired editing function. Always avoid bypassing `yamledit.pyz`
for editing as much as possible.

## Reference Index

### Procedure packs (next to SKILL.md)

- **[SKILL-1a-create.md](SKILL-1a-create.md)** — new campaign only.
- **[SKILL-1b-resume.md](SKILL-1b-resume.md)** — load save zip; does not start a session by reading alone.
- **[SKILL-2-main-loop.md](SKILL-2-main-loop.md)** — play; session_number; warm doc list; story.md rules.
- **[SKILL-3-end-session.md](SKILL-3-end-session.md)** — End of Session only (not early).
- **[SKILL-4-gm-assistant.md](SKILL-4-gm-assistant.md)** — human is GM; what to offer,
  what not to do, and the spoiler rules that invert when the user is the GM.

### Hot / warm (play)

- **[gameplay-loop](references/gameplay-loop.md)** — **hot**: loop steps + dice hard rules SoT; **reread on drift**.
- **[core-moves](references/core-moves.md)** — **warm** with main loop: basic/special moves, mods, debilities, encumbrance, ranges.
- **[gm-agenda-principles-moves](references/gm-agenda-principles-moves.md)** — **warm** with main loop: full agenda/principles/GM moves.
- **[llm-patches](references/llm-patches.md)** — **warm** with main loop: short rule clarifications (threads/deeds, fronts, ranger companion).
- **[gm-narration](references/gm-narration.md)** — **warm** with create (1a) and/or main loop (2): long narration essays. Short constitution always in SKILL.md above.

### Cold / on demand

- **[dw-intro](references/dw-intro.md)** — generic intro only (First Contact).
- **[combat-and-custom-moves](references/combat-and-custom-moves.md)** — combat or custom moves.
- **[fronts-and-worldbuilding](references/fronts-and-worldbuilding.md)** — fronts craft (also required at 1a create).
- **[npc-tools](references/npc-tools.md)** — NPCs, hirelings, steading tags, names.
- **[follower-moves](references/follower-moves.md)** — Perilous Wilds follower system (creation via `npc_gen.py --follower`).
- **[equipment-and-services](references/equipment-and-services.md)** — gear and prices, not exhaustive.
- **[magic-items](references/magic-items.md)** — core rules named magic items.
- **[tag-reference](references/tag-reference.md)** — full tag glossary.
- **[treasure-and-monster-building](references/treasure-and-monster-building.md)** — custom monsters / treasure table detail (`monster_gen.py` first for bestiary).
- **[weather](references/weather.md)** — weather as threat/move.
- **[hacking-and-conversion](references/hacking-and-conversion.md)** — custom classes/moves, conversion.
- **[elicitation](references/elicitation.md)** — only when a procedure needs structured multi-choice user input, or auditing missed options. Chat form + MCP-schema-shaped mapping.
- **[campaign-creation-checklist](references/campaign-creation-checklist.md)** — with 1a new campaign (or audit incomplete setup).
- **[character-creation-checklist](references/character-creation-checklist.md)** — creating/rebuilding PCs.
- **rulebook-digest** — Read `L0-index.md` first then drill down L0 → L1 → L2. Access L3 via `rulebook.py`; never read `source/xml/` wholesale and prefer `rulebook.py` for reading. Tag Reference appendix is print-only; [tag-reference](references/tag-reference.md) is authority.
- **extra-classes/** — non-core playbooks (all named `classname.md`) when needed.
- **[ATTRIBUTION](references/ATTRIBUTION.md)** — only if user asks about authors/license ("about").
