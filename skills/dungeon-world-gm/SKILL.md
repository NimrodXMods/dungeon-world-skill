---
name: dungeon-world-gm
description: Reference material and tools for running Dungeon World (a Powered-by-the-Apocalypse tabletop RPG) as GM - condensed move lists, GM principles, combat guidance, front/danger-writing, NPC/name/steading generators, equipment and treasure tables, and a dice-rolling script. Use this whenever GMing a Dungeon World session, prepping a front or custom move, statting a monster on the fly, generating NPCs/names/loot, or rolling dice for the game (2d6 moves, damage dice, etc.), even if the user doesn't say "Dungeon World" by name and just references moves, fronts, HP, or GMing this specific game.
compatibility: Anthropic Claude Sonnet 5, xAI Grok 4.5, OpenAI GPT 4.5, equivalent or better model. Requires bash or other CLI with python 3.0+, python pyz support, temporary file storage that persists between turns, multi-step tool use, and reliable long-context campaign state tracking. Network optional. Creative writing temperature optional.
license: CC-BY-NC-SA-4.0
metadata:
  version: "0.22.1"
  type: game
  author: NimrodX
  creator-model: Anthropic Claude Sonnet 5 (claude-sonnet-5)
  last-assisting-model: Anthropic Claude Opus 5 (claude-opus-5)
  updated: "2026-08-11"
  license-url: "https://creativecommons.org/licenses/by-nc-sa/4.0/"
---

# Dungeon World GM Skill Toolkit

Condensed, LLM-friendly reference material distilled from the core rulebook and several
fan-made supplements the user provided, plus scripts for various tasks, including dice. This is meant
to be consulted _during play_ - reach for the specific reference file you need rather
than re-reading everything. This is enough for an LLM to act as a GM or assist a human GM.

This skill is written to be model-agnostic - nothing here assumes a specific AI provider
or product.

## When to use this

- Running a live Dungeon World session as GM (any point: framing scenes, calling for moves, resolving combat, handing out loot, introducing NPCs)
- Prepping between sessions: writing a Front, a custom move, a monster, a settlement
- Rolling dice for the game (use `scripts/roll.py`, don't estimate or hand-wave a roll)
- If user asks for assistance with GMing a Dungeon World game (see assistant mode)

## Every Time This Skill Is First Loaded

The very first line of your response after this skill is first loaded in a session must be
this exact text, before any other content or tool calls:

> 🏰⚔️ Dungeon World Skill, by NimrodX. Based on _Dungeon World_ by Sage LaTorra & Adam Koebel.
> Other third-party content was used in creating this skill. Say "about" for full attribution.

If the user says "about", "about this skill" or similar, display the full contents
of [ATTRIBUTION.md](references/ATTRIBUTION.md) either: 1) using md file
presentation tools (preferred) or 2) replayed into the session output.

## First Contact / Generic Invocation

If this skill is invoked with no other instructions or context to act on (e.g. the user
just says "/dungeon-world-gm" or "let's play Dungeon World" with nothing else to go on),
or the user asks a generic question like "what is this?" or "what is Dungeon World?", output the contents
of [dw-intro](references/dw-intro.md) verbatim as your entire response - don't summarize, paraphrase, or
add anything before/after it. It ends by asking the user where to start, so let their
next message answer that rather than pre-empting it here.

If the user's first message already gives enough to act on (a campaign zip upload,
a clear "be my GM," specific setup details, etc.) skip the intro and go straight to the proper point below.

## Game Session Workflow

This part is a sequential workflow reference to aid in determining next action. A session has
two "modes":
- **Agent as GM:** (options 1 and 2 below) three possible states: start, main gameplay loop, end.
- **GM Assistant:** (options 3 and 4 below) the agent acts as an assistant for a human GM

### Session Start

If the user invoked the skill with a request, then skip directly to the matching option.
Otherwise, present each step using [elicitation](references/elicitation.md); ask the user
which one they want.

What does the user want right now from the skill?

| # | Option | Next |
| --- | --- | --- |
| 1 | **New campaign** | [Phase 1a Create](SKILL-1a-create.md) |
| 2 | **Resume** from a campaign save | [Phase 1b Resume](SKILL-1b-resume.md) |
| 3 | **GM Assistant** | [Phase 4 GM Assistant](SKILL-4-gm-assistant.md) |
| 4 | **Rules / reference only** | Answer questions; do not start session state |

Default: **none** — needs an explicit pick if unclear. Load only the linked phase file
when that path is chosen (progressive disclosure).

### Phase files (procedure packs)

| Phase | File | When |
| --- | --- | --- |
| 1a Create | [SKILL-1a-create.md](SKILL-1a-create.md) | New campaign |
| 1b Resume | [SKILL-1b-resume.md](SKILL-1b-resume.md) | Load save zip |
| 2 Main loop | [SKILL-2-main-loop.md](SKILL-2-main-loop.md) | Play after start resolved |
| 3 End session | [SKILL-3-end-session.md](SKILL-3-end-session.md) | End of Session move |
| 4 GM Assistant | [SKILL-4-gm-assistant.md](SKILL-4-gm-assistant.md) | Human is GM |

## How to "Write" the Game (narration constitution — always on)

Keep this block short so it stays early-context and hard to dilute. Full essays:
[gm-narration](references/gm-narration.md) — load when creating a campaign or entering
the main loop (see those phase files).

**Prose register** — default to gmsecret `style_voice`, else **Dungeon World Pulpy**:

- **Dungeon World Pulpy (default)** — irreverent, punchy, dark with a wink; short
  sentences; danger real but brisk.
- **Grim & Uncouth** — Howard/Leiber; mean, visceral, serious violence.
- **Formal/Literary** — denser, elevated; use sparingly for epic beats.
- **Custom** — store the user's description in `style_voice`.

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

## Dice Rolling

**Never confabulate dice from priors** — always `scripts/roll.py`. Full hard rules
(explain every player-facing roll, re-roll if confabulated) live in
[gameplay-loop](references/gameplay-loop.md) (read with main loop; reread on drift).
Interface: `python3 scripts/roll.py --help-llm`.

## Other Random Generation Scripts

The `*_gen.py` scripts handle mechanics that involve heavy random generation, saving time and effort.
`idea_gen.py` is different: it's not required by any mechanic, but it's needed to counter
models' tendency to fall back on the same few "creative" choices when priors dominate over
genuine variation.

Use `idea_gen.py` whenever a creative, open-ended question needs an answer and no more
specific script fits - any time there's a wide range of options with no fixed way to pick
among them. Run it even when the result doesn't quite match the situation: the point isn't
just the output, but the entropy it injects into context, which counters repetition and
priors-driven sameness that's noticeable to users even when the model itself can't detect
it. When in doubt, use `*_gen.py` scripts more rather than less.

Review each script's output before using it, and re-run if it doesn't fit the situation -
the first result is never mandatory. It's also fine to mix and match details from multiple outputs.

Available generator scripts and "trigger" situations for using them:

- `region_gen.py` (region/area/site names) - Use this, especially at the start of a campaign,
  to determine what the "map" looks like. What land are the player characters in? This will
  help determine geography and possible interesting locations.
- `steading_gen.py` (tag-based steadings) - Use this any time details for any settlement from the
  smallest village to the largest city need to be determined. What village is up ahead? This helps answer.
- `dungeon_gen.py` (dungeon concepts) - Use this whenever a (usually dangerous) site for adventure,
  exploration, and investigation is needed. Where do we find adventure and treasure around here?
  What's that strange place that you said is in this area? This will help answer. (Note that a "dungeon"
  is not necessarily a literal dungeon, but any sort of point of interest for adventuresome risk and reward.)
- `npc_gen.py` (instant NPCs and Perilous Wilds followers) - Use any time a new NPC needs to be created.
  For example, when the characters meet a new NPC friend, enemy, or someone neutral they may repeatedly
  communicate with such as a tradesman or shop keeper. It is also used when they seek out followers to
  aid them.
- `monster_gen.py` (official bestiary picker, and a custom stat-block builder) - Use this when player
  characters are running into troublesome creatures of some sort. The characters run into creatures,
  but what sort? This will help answer. By default it returns a real monster from the core rulebook
  bestiary, with its written description, instinct and moves already filled in, but it can help with custom
  monster generation.
- `idea_gen.py` (general-purpose ideas: treasure and what a piece of treasure looks like, discoveries,
  dangers, equipment tags, GM moves, DR/Spout Lore miss tricks, story hooks, room clutter, rumors,
  named magic items) - use its treasure tables for loot no monster owns (a cache, a reward); a
  monster's own haul comes from `monster_gen.py` instead, which rolls the creature's damage die
  against the same table. For every other question that arises about the PC party and what they
  discover, or questions about anything requiring a creative answer, use this script. It has no
  creature table - "what creature is it?" is `monster_gen.py`'s question, and it answers with a
  real stat block rather than a category.
  Its `seed` table is the odd one out: it hands back a *question* rather than an answer, rolling
  the Inexhaustive List of Questions from
  [fronts-and-worldbuilding](references/fronts-and-worldbuilding.md). Reach for it when writing a
  front's Stakes questions, when filling in the world around the party, or mid-session when the
  players point at something and the right move is to ask a good question about it rather than
  decide. It will not build a front for you, by design.

Run `python3 scripts/<script>.py --help-llm` before using any of these scripts (once per
script per session is enough) - it prints a dense reference written for LLM callers with
the full option list, choices, defaults, and output format, and won't drift out of date
the way hardcoded examples here would.

**Never use the `--seed` option as part of the skill; it is only for software development use.**

Do not be concerned if the tables in the script do not precisely match the rulebook;
scripts may contain extra content from the skill author.

**If a script generates a grammatically awkward name (like "Hill of King") then just repair
the bad grammar in some way ("Hill of the King", "King's Hill", "Kingshill") before using.**

## Running a Campaign

For sessions where the agent plays GM and the person plays one or more characters (naming
who's acting when there are multiple), campaign state lives in plain files, not memory -
deterministic, exact, and downloadable. Two file types, both YAML:

- **Character sheets**: `<name>_<class>.yaml` (e.g. `ragnar_warrior.yaml`). Template at
  `assets/yaml_templates/character_template.yaml`, schema at `assets/yaml_schemas/character.schema.yaml`.
- **GM secret state**: `<campaign_slug>_gmsecret.yaml` (working copy, plain - fronts,
  dangers, Grim Portents with checked/unchecked flags, custom moves, session log, and a
  `pause_state` block describing exactly where things stand for next time). Template at
  `assets/yaml_templates/gmsecret_template.yaml`, schema at `assets/yaml_schemas/gmsecret.schema.yaml`.
  Additional fields can be added as needed to store other information such as custom monsters,
  NPCs, XP bonus goals, or custom anything. **Never show this file's plain
  contents to the user** - it's GM-only spoiler material.

**Keeping yaml updated cheaply**: use `yamledit.pyz` for every HP change, XP
gain, gear pickup, etc. instead of rewriting/re-viewing the whole file - it's built for
exactly this. Run `python3 scripts/yamledit.pyz --help-llm` to get the full reference.

**Always pass `--schema` for the file being edited.** It catches a typo'd path
(`hp.currnet`, `portents[0].chekced`) that would otherwise silently become a new field,
which is the main way state files rot. This skill has two document types and a
`yamledit.yaml` config can only name one schema, so the flag must be passed per call -
there is no default that covers both.

For on-the-fly flexibility, all schemas are _selectively_ open:
fixed shapes (`hp`, `stats.str`, a portent, a `current_location` entry) are closed
so a misspelling is an error, while regions, NPCs,
fronts and the top level stay open so the campaign can grow new fields freely. Adding a
genuinely new field is fine but needs explicit flags as a safeguard.

**Note:** Warn the user if direct editing of a yaml file is needed because `yamledit.pyz`
can't perform a desired editing function. Always store a report in memory when `yamledit.pyz`
has problems. Always avoid bypassing `yamledit.pyz` for editing as much as possible.

## Reference Index

### Procedure packs (next to SKILL.md)

- **[SKILL-1a-create.md](SKILL-1a-create.md)** — new campaign only.
- **[SKILL-1b-resume.md](SKILL-1b-resume.md)** — load save zip; does not start a session alone.
- **[SKILL-2-main-loop.md](SKILL-2-main-loop.md)** — play; session_number; warm doc list; story.md rules.
- **[SKILL-3-end-session.md](SKILL-3-end-session.md)** — End of Session only (not early).
- **[SKILL-4-gm-assistant.md](SKILL-4-gm-assistant.md)** — human is GM.

### Hot / warm (play)

- **[gameplay-loop](references/gameplay-loop.md)** — **hot**: loop steps + dice hard rules SoT; reread on drift.
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
- **[equipment-and-services](references/equipment-and-services.md)** — gear and prices.
- **[magic-items](references/magic-items.md)** — named magic items.
- **[tag-reference](references/tag-reference.md)** — full tag glossary.
- **[treasure-and-monster-building](references/treasure-and-monster-building.md)** — custom monsters / treasure table detail (`monster_gen.py` first for bestiary).
- **[weather](references/weather.md)** — weather as threat/move.
- **[hacking-and-conversion](references/hacking-and-conversion.md)** — custom classes/moves, conversion.
- **[elicitation](references/elicitation.md)** — only when a procedure needs structured multi-choice, or auditing missed options. Chat form + MCP-schema-shaped mapping; one PC at a time for chargen.
- **[campaign-creation-checklist](references/campaign-creation-checklist.md)** — with 1a new campaign (or audit incomplete setup).
- **[character-creation-checklist](references/character-creation-checklist.md)** — creating/rebuilding PCs.
- **rulebook-digest** — L0 → L1 → L3 via `rulebook.py`; never read `source/xml/` wholesale. Tag Reference appendix is print-only; [tag-reference](references/tag-reference.md) is authority.
- **extra-classes/** — non-core playbooks (`classname.md`) when needed.
- **[ATTRIBUTION](references/ATTRIBUTION.md)** — only if user asks about authors/license ("about").

## `advanced-digest` Retrieval for **rulebook-digest**

It is important to retrieve only as many lines as needed. When seeking information or answering a question from a digest:

0. Make sure you have run `scripts/rulebook.py --help-llm` first for the query options if needed.
1. **Start at L0.** Scan tags/titles for the matching source(s). This narrows scope for free — don't open L1 files you don't need.
2. **Read the matching L1 section(s) first.** Most questions resolve here. Only descend to L2 if the L1 paragraph doesn't contain the specific figure, name, or claim being asked about, and only open L3 if exact wording (not just the fact) matters. For L3, take the `[xml:...]` anchor off that section's header and run `scripts/rulebook.py` with an anchor query; prefer the narrowest anchor that answers the question over a whole-chapter one.
3. **Climb back up for context when starting from a fact.** If a search or link lands you on an L2 fact or L3 quote, read its `[s-NNN]` parent for surrounding context before answering — a fact line is self-contained but not context-complete.
4. **Decompress on the way out, don't quote the digest verbatim.** L1/L2 are deliberately lossy — surprisal-only residue, not prose meant to be read aloud to the user. When using a digest to answer a question, re-expand the kept residue using your own general knowledge to reconstruct full, natural context, the same way you'd explain a topic you knew well, rather than pasting the compressed paragraph as the answer. The digest tells you _what_ was worth keeping; you still supply the connective tissue.
   - **Mind the decoder.** Because a digest is lossy compression _against the authoring model's weights as a shared dictionary_ the `generated_by` model in the frontmatter records the dictionary the drops assumed. Decoding with a _different_ model still works, but reliability is **capability-relative, not identity-relative**: a decoder at least as capable as — and as knowledgeable in this domain as — the author can trust the drops, whereas a **weaker or differently-specialized** decoder may hit residue the author cut as "common knowledge" that it can't actually reconstruct. When decoding a digest authored by a stronger model, treat thin spots as possible gaps and lean harder on the Verification procedure / re-fetch. (Effort affects _authoring_ quality, not the decoder's dictionary, so it's secondary to model identity here.)
