---
name: dungeon-world-gm
description: Reference material and tools for running Dungeon World (a Powered-by-the-Apocalypse tabletop RPG) as GM - condensed move lists, GM principles, combat guidance, front/danger-writing, NPC/name/steading generators, equipment and treasure tables, and a dice-rolling script. Use this whenever GMing a Dungeon World session, prepping a front or custom move, statting a monster on the fly, generating NPCs/names/loot, or rolling dice for the game (2d6 moves, damage dice, etc.), even if the user doesn't say "Dungeon World" by name and just references moves, fronts, HP, or GMing this specific game.
compatibility: Anthropic Claude Sonnet 5, xAI Grok 4.5, OpenAI GPT 4.5, equivalent or better model. Requires bash or other CLI with python 3.0+, python pyz support, temporary file storage that persists between turns, multi-step tool use, and reliable long-context campaign state tracking. Network optional. Creative writing temperature optional.
license: CC-BY-NC-SA-4.0
metadata:
  version: "0.12.0"
  type: game
  author: NimrodX
  creator-model: Anthropic Claude Sonnet 5 (claude-sonnet-5)
  last-modified-by-model: Anthropic Claude Opus 5 (claude-opus-5)
  updated: "2026-08-07"
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

> 🏰⚔️ Dungeon World Skill, by NimrodX. Based on Dungeon World by Sage LaTorra & Adam Koebel.

## First Contact / Generic Invocation

If this skill is invoked with no other instructions or context to act on (e.g. the user
just says "let's play Dungeon World" with nothing else to go on), or the user asks a
generic question like "what is this?" or "what is Dungeon World?", output the contents
of **[[dw-intro]]** verbatim as your entire response - don't summarize, paraphrase, or
add anything before/after it. It ends by asking the user where to start, so let their
next message answer that rather than pre-empting it here. If the user's first message
already gives enough to act on (a campaign zip upload, a clear "be my GM," specific
setup details, etc.) skip the intro and go straight to Session Start below.

## Game Session Workflow

This part is a sequential workflow reference to aid in determining next action. A session has
three possible states: start, main gameplay loop, end.

### Session Start

Before starting a game session, one of the following things should happen. Ask the user which one they intend if they don't state up front.

- **Resuming a Campaign:** The User uploads a .zip file of an existing campaign. Use `session_load.py` to extract the zip file. Run `session_load.py --help` for usage. Example: `python3 scripts/session_load.py campaign_s3.zip --dir .` This unzips everything, rot13-decodes the gmsecret back to a plain working `.yaml`, rot13 decodes the handoff.md and prints a summary (campaign, session number, character files found, and the full `pause_state` - location/situation/open threads) so you have immediate narrative context without necessarily needing a separate read of the whole file. Read all files to determine all of the game state, and if anything seems missing ask the user if they can remember it. Other conversations in the same project can also be searched for details as game sessions are likely to be in the same project. Also be warned that yaml files could fail validation because of new additions to or changes to the skill. If this happens it usually just means the yaml files need migration to a new schema. Migrate according to current schemas, docs, and best effort.
- **Starting a New Campaign:** Read **[[fronts-and-worldbuilding]]** and also check **rulebook-digest/L0-index** for information on creating one or more fronts. To do this, ask the user some questions about what sort of world they want, what sort of campaign they want to play, how many players there will be, and anything else that is useful to write at least one front and set up the campaign scenario. Use `idea_gen.py` (see below) to help. Suggest a 'campaign slug' to identify the game, ask user to confirm or suggest new slug, and store decisions in the `<campaign_slug>_gmsecret.yaml` file (see below) as they are made. Ask the user if they'd like to maintain a running story based on the game (see **Writing `story.md`** below), the default answer is yes so assume yes unless otherwise stated.

**`session_number`**: This should be set to 1 _at the start of the first session for a new campaign only_. For resuming a previous campaign, advancing it is an explicit act at the **start** of a new session, once you've confirmed from what the person said - or by asking - that a new session is actually beginning. Simply loading a save is not by itself the start of a session. To increment the session number, run `python3 scripts/yamledit.pyz --help-llm` to get the full documentation for `yamledit.pyz` and perform on edit of the gmsecret file incrementing `session_number` +1 , then announce `Beginning session <new number>...`.

**Reconciling `pause_state` on load:** `pause_state.situation` and `pause_state.open_threads`
are not independent - `situation` is the authoritative snapshot of where things stand right
now, while `open_threads` is a working list that should already reflect it. If they disagree
(e.g. a thread's text implies something hasn't happened yet, but `situation` or the prior
session's narrative shows it already did), trust `situation` and correct or prune the stale
thread immediately as part of session load - before narrating anything to the player. Don't
narrate off the first `open_threads` entry you read without checking it against `situation`.

When you have verified that the session has started, ensure you have read `handoff.md` and delete it. Only delete `handoff.md` after reading and after the session actually starts, not before.

Never narrate the new session as begun before that edit has actually run. If two sessions end up sharing a number, the increment was skipped - fix it forward, don't rewrite history.

Always read at session start: **[[gameplay-loop]]**, **[[core-moves]]**, **[[gm-agenda-principles-moves]]**, **[[llm-patches]]**, and yaml templates in `assets/yaml_templates` (they serve as documentation of yaml use). Other references should be read only as needed.

Once all the session start details are resolved, either by restoring a previous session or starting a new campaign, the
game state moves to the main gameplay loop.

### Main Gameplay Loop

Immediately upon starting a session, read **[[gameplay-loop]]** for a brief reminder of the core gameplay loop. This file is intentionally kept short and can be reread as needed to fix context drift. The main things you need for moves, dice rolling, and such are detailed in further sections below.

The loop repeats until the user (player or player(s)) decide to end the session with the "End of Session" move. Once that happens,
switch to the session end state. This can be triggered by the person saying "end session", "let's end the session", etc.

### Session End

The easiest place to end a session is during a "Make Camp" (move) or arriving at safe lodging, but this isn't absolutely required. (It should be recommended if the characters' situation allows for it easily.) If the characters are not in a safe-ish resting place for sufficient time, moves like "Level Up" aren't available.

Read **[[session-end]]** when it's time to end a session. This file isn't needed until then, and reading it early will usually
result in it being partially forgotten by session end time.

## Dice Rolling

Never fabricate a "random" dice result from priors - always run `roll.py`. Check previous
turns for a fabricated roll; if you find one, offer the player a re-roll and treat the
lapse as a signal to recheck subsequent turns too, so it doesn't repeat.

How to roll dice for real without fabrication: run `scripts/roll.py --help-llm` for
instructions.

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
the first result is never mandatory. It's also fine to run a script a few times (~3) and
keep whichever result fits best, or mix and match details from multiple outputs.

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
- `idea_gen.py` (general-purpose ideas: treasure, discoveries, dangers, creatures, equipment tags,
  GM moves, DR/Spout Lore miss tricks, named magic items, misc details) - For every other question that
  arises about the PC party and what they discover, or questions about anything requiring a creative
  answer, use this script. Note that the 'creatures' table is good for vague ideas about creature
  encounters, but doesn't generate specific creature stats so can be used to help re-use existing
  creature types.

Run `python3 scripts/<script>.py --help-llm` before using any of these scripts (once per
script per session is enough) - it prints a dense reference written for LLM callers with
the full option list, choices, defaults, and output format, and won't drift out of date
the way hardcoded examples here would.

**Never use the `--seed` option as part of the skill; it is only for software development use.**

Do not be concerned if the tables in the script do not precisely match the rulebook;
scripts may contain extra content from the skill author.

**If a script generates a grammatically awkward name (like "Hill of King") then just repair
the bad grammar in some way ("Hill of the King", "King's Hill", "Kingshill") before using.**

## Running a Campaign (required for agent as GM, optional for agent as GM Assistant)

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

## GM Assistant "Mode"

**GM Assistant mode** (low priority, not yet in active use): a second mode where the
user is GM and the agent assists rather than running the game directly. Details TBD -
don't assume this "mode" applies unless the user requests it. If this mode is requested
then expect that the details will need to be worked out ad hoc and the skill updated
to reflect different variants of it. Some possibilities are:

- The agent keeps track of all data for user GM and Players, suggests all details of
  setting and next actions, gets confirmation from user GM or is asked to recreate or
  change based on GM (user) specifications. The agent may or may not roll some or all dice.
- The agent keeps track of all data for GM and Players but GM decides all details of
  setting and next actions. In this case the user (GM) has to give the agent info
  about what is going on and what needs to be tracked, but may keep some details
  in their head. The agent may or may not roll some or all the dice for everyone.
- The agent keeps track of only GM data and players use their own character sheets. The
  agent may or may not help with dice rolls, or may only roll dice for the GM but not players.

Use the above as guidelines to help ask questions to clarify what the agent should do if
the user ever requests GM assistant mode.

## Reference Index

- **[[dw-intro]]** - the generic "what is this / what is Dungeon World" answer, output verbatim on a no-argument or generic invocation (see First Contact section above). Not meant to be read during play otherwise.
- **[[core-moves]]** - always read - every basic/special player move, stat mod table, debilities, encumbrance, XP, damage-by-severity, range tags. Start here for "what move is this?" or "what happens on a 7-9 for move X?"
- **[[llm-patches]]** - Contains corrective prose and rule clarifications for models.
- **[[gm-agenda-principles-moves]]** - always read - GM agenda/principles, the GM move list, soft vs. hard moves, dungeon-level moves, scene framing/ending, spotlight management, general GMing tips. Start here for "what do I do right now as GM?"
- **[[combat-and-custom-moves]]** - defer reading until combat occurs or a custom move is needed. How DW combat actually flows without initiative, multi-enemy math, adjusting difficulty live, running a swarm, and a checklist for writing good custom moves.
- **[[fronts-and-worldbuilding]]** - Fronts/Dangers/Portents, danger types with their GM move lists and impending dooms, "draw maps leave blanks," a full worked sample Front, and the six-angle (who/what/where/when/why/how) worldbuilding question technique.
- **[[npc-tools]]** - Use this for: NPC creation questions, quest hooks, hireling stats, steading tags + quick-build recipes, instincts/knacks lists, name lists by ancestry, a steading name generator, and per-class background questions.
- **[[follower-moves]]** - Perilous Wilds' "Lead the Way" alternative follower system (Recruit, Order Follower, Do Their Thing, Call for Assistance, Pay Up, Watch Them Go) with Quality/Loyalty/Cost stats and the full follower-tags glossary, replacing [[npc-tools]]'s basic hireling rules if you want the fuller system. Follower _creation_ (stat generation) isn't in this file - it's `npc_gen.py --follower` instead, since that reuses the script's existing name lists.
- **[[equipment-and-services]]** - weapons, armor, gear, poisons, tags, services, transport, land prices, bribes, gifts, plus specific consumable in-use effects.
- **[[magic-items]]** - ~30 named official magic items with unique mechanical effects, ready to hand out or use as homebrew templates.
- **[[tag-reference]]** - the official complete alphabetical tag glossary (equipment + monster + steading tags in one place) for fast lookup.
- **[[treasure-and-monster-building]]** - for monsters prefer using `monster_gen.py`, which now returns official rulebook monsters by default (complete with description, instinct and moves). Use this [[treasure-and-monster-building]] guide when fiction needs special custom monsters and a full description of the options is needed: it helps with the modular "pick from each category" builder behind custom `monster_gen.py` for improvising an enemy that isn't in the bestiary. Also read this if you need to generate from the treasure roll table; make sure there's always some treasure for defeating monsters and it's occasionally something good. Sometimes random generation from `monster_gen.py` may be lacking sufficient treasure.
- **[[weather]]** - only read this if bad weather is used as part of story or a GM move.
- **[[hacking-and-conversion]]** - only read this for _writing custom moves_, building new classes, and converting non-DW adventures/monsters into Dungeon World terms (includes a Direct Conversion stat cheat-sheet).
- **rulebook-digest** - a hierarchical (L0/L1/L2) digest of the full 410-page core rulebook, built as an `advanced-digest`. `L0-index.md` tracks chapter-by-chapter coverage; `L1-digest.md` holds one paragraph per section plus ~60 atomic L2 facts (`F-NNN`) and full catalogs for anything genuinely precise a paraphrase would lose - including the complete bestiary (9 chapters, ~130 monsters/NPCs), all 8 playbooks, and the full Wizard/Cleric spell lists. Several durable findings were also folded directly into the other reference files above (corrections are noted inline where that happened) - read `L0-index.md` first for an overview of what's where. For anything that would require L3, use the `[xml:...]` anchor on the relevant `L1-digest.md` section header with `scripts/rulebook.py`, as described below.
- **rulebook-digest/source/xml/** - the complete core rulebook text (~100k words) as the authors' own published XML, one file per chapter. **Never read these files directly** - they are markup, and a chapter is thousands of words. Read them only through `scripts/rulebook.py`, which addresses the book by ANCHOR (`moves#basic-moves/hack-and-slash`) rather than by page: `--outline` to find an anchor, `--anchor` to read one section, `--search` to find wording whose location you don't know. Run `rulebook.py --help-llm` for the full interface. Every section header in `L1-digest.md` carries the `[xml:...]` anchor for its own L3 source.
  - The `(pNN-NN)` page ranges throughout `L0-index.md` and `L1-digest.md` are **not** a retrieval mechanism - nothing resolves them. They exist so you can tell a user where to look in their printed 1st-edition book ("that's Hack and Slash, around p60"). Treat them as an approximate courtesy pointer, not an authoritative citation, and never try to look anything up by page.
  - One gap: the **Tag Reference** appendix is print-only and absent from the XML. [[tag-reference]] is the authority for it; there is nothing to re-fetch.
- **[[ATTRIBUTION.md]]** - never read this unless user asks about authors, license, copyright, or attribution of the material. All of this is moved to this file so that it doesn't fill up context for no reason. It contains no game mechanics.

## `advanced-digest` Retrieval for **rulebook-digest**

It is important to retrieve only as many lines as needed. When seeking information or answering a question from a digest:

0. Make sure you have run `scripts/rulebook.py --help-llm` first for the query options if needed.
1. **Start at L0.** Scan tags/titles for the matching source(s). This narrows scope for free — don't open L1 files you don't need.
2. **Read the matching L1 section(s) first.** Most questions resolve here. Only descend to L2 if the L1 paragraph doesn't contain the specific figure, name, or claim being asked about, and only open L3 if exact wording (not just the fact) matters. For L3, take the `[xml:...]` anchor off that section's header and run `scripts/rulebook.py` with an anchor query; prefer the narrowest anchor that answers the question over a whole-chapter one.
3. **Climb back up for context when starting from a fact.** If a search or link lands you on an L2 fact or L3 quote, read its `[s-NNN]` parent for surrounding context before answering — a fact line is self-contained but not context-complete.
4. **Decompress on the way out, don't quote the digest verbatim.** L1/L2 are deliberately lossy — surprisal-only residue, not prose meant to be read aloud to the user. When using a digest to answer a question, re-expand the kept residue using your own general knowledge to reconstruct full, natural context, the same way you'd explain a topic you knew well, rather than pasting the compressed paragraph as the answer. The digest tells you _what_ was worth keeping; you still supply the connective tissue.
   - **Mind the decoder.** Because a digest is lossy compression _against the authoring model's weights as a shared dictionary_ the `generated_by` model in the frontmatter records the dictionary the drops assumed. Decoding with a _different_ model still works, but reliability is **capability-relative, not identity-relative**: a decoder at least as capable as — and as knowledgeable in this domain as — the author can trust the drops, whereas a **weaker or differently-specialized** decoder may hit residue the author cut as "common knowledge" that it can't actually reconstruct. When decoding a digest authored by a stronger model, treat thin spots as possible gaps and lean harder on the Verification procedure / re-fetch. (Effort affects _authoring_ quality, not the decoder's dictionary, so it's secondary to model identity here.)

## Writing `story.md` - running narrative log

Only maintain `story.md` if `maintain_story` is `true` (true is default).

This is lightweight, prose-only story log that accumulates alongside the gmsecret
and character sheets, giving a readable "story so far" without anyone having
to re-read the structured YAML.

### Format

- Title (`# The Adventures of Blah`): propose a title to the user on
  starting a new campaign and use whatever they specify.
- Section headers per session (`## Chapter N` with N being the session number),
  plain prose paragraphs under each - no bullet points, no mechanical tags,
  no dice/HP/stat detail.
- It's fine for entries to read a little jumpy or unevenly paced - this is a
  running log built incrementally during live play, not a polished summary
  written after the fact.
- Skip mechanics entirely (rolls, HP, XP, move names) - narrative only, the
  same way you'd describe the scene and character actions in a novel.

### When to append

Append **after a scene concludes**, not on a fixed turn interval - a fight
ends, a conversation wraps, a big reveal lands, or the party changes location.
In practice this is roughly every 3-8 turns, but the trigger is narrative
closure, not a count. Hold the scene in mind and write one or two paragraphs
covering it in one append call, rather than editing the file after every
individual turn. Try to describe the environment, characters, foes, NPCs, and
all the action since the last update.

### How to append

Plain append, never `str_replace` - a growing log makes `str_replace`
increasingly fragile to match uniquely as the file gets longer. Since
`story.md` is plain prose (not YAML), no special escaping is needed; a normal
heredoc append is fine:

```bash
cat >> story.md << 'EOF'

New paragraph(s) here.
EOF
```

Don't reread the whole file before appending — the scene you're summarizing
is already in context. Only tail `story.md` if checking tone/continuity
against earlier entries, which should be rare.

### At session end

Do one final append covering anything since the last update, then include
`story.md` in the same directory as the character files and gmsecret file.
(`session_save.py` will look for it in the "character directory".)

### Retroactive backfill (one-time, not part of the ongoing workflow above)

This is _only_ needed if a user initially did not want a `story.md` maintained
but later changed their mind and wants to reconstruct one from past sessions.

If starting `story.md` partway through an existing campaign, earlier sessions
can be reconstructed from past conversation history (`conversation_search` /
`read_conversation` by session title) rather than from `session_log` recaps
alone — the recaps are usually too compressed to produce real prose, while
the actual transcripts have the scene-level detail needed for a readable
narrative. This only needs to happen once per campaign.

## Possible Future Additions

- GM Assistant mode workflow/file scheme (see above) - not yet designed, lower priority.
- Eventual HTML artifact to render a character sheet YAML nicely - explicitly deferred by the user for now.
- Maybe some images or image generation for dice rolls, but depends on the UI front end ability to display which seems uncertain right now.
