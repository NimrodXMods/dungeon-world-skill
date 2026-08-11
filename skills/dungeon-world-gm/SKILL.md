---
name: dungeon-world-gm
description: Reference material and tools for running Dungeon World (a Powered-by-the-Apocalypse tabletop RPG) as GM - condensed move lists, GM principles, combat guidance, front/danger-writing, NPC/name/steading generators, equipment and treasure tables, and a dice-rolling script. Use this whenever GMing a Dungeon World session, prepping a front or custom move, statting a monster on the fly, generating NPCs/names/loot, or rolling dice for the game (2d6 moves, damage dice, etc.), even if the user doesn't say "Dungeon World" by name and just references moves, fronts, HP, or GMing this specific game.
compatibility: Anthropic Claude Sonnet 5, xAI Grok 4.5, OpenAI GPT 4.5, equivalent or better model. Requires bash or other CLI with python 3.0+, python pyz support, temporary file storage that persists between turns, multi-step tool use, and reliable long-context campaign state tracking. Network optional. Creative writing temperature optional.
license: CC-BY-NC-SA-4.0
metadata:
  version: "0.19.0"
  type: game
  author: NimrodX
  creator-model: Anthropic Claude Sonnet 5 (claude-sonnet-5)
  last-assisting-model: xAI Grok 4.5 (grok-4.5)
  updated: "2026-08-10"
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
| 1 | **New campaign** | Go to **New Campaign** |
| 2 | **Resume** from a campaign save | Go to **Resuming a Campaign:** path below |
| 3 | **GM Assistant** | Start **GM Assistant Mode** state described below |
| 4 | **Rules / reference only** | Answer questions; do not start session state |

Default: **none** — needs an explicit pick if unclear.

#### New Campaign

To enter Create New Campaign state, read [Phase 1a Create](SKILL-1a-create.md) and continue there. Do not load this until/unless it is needed to continue.

#### Resuming a Campaign

To enter Resume an Existing Campaign state, Read [Phase 1b Resume](SKILL-1a-resume.md) and continue there. Do not load this until/unless it is needed to continue.

### Main Gameplay Loop

To enter the Main Gameplay Loop, read [Phase 2 Main Loop](SKILL-2-main-loop.md) and continue there. Do not load this until/unless it is needed to continue.

### End of Session or "Session End"

To enter the End of Session state, read [Phase 3 End Session](SKILL-3-end-session.md) and continue there. Do not load this until/unless it is needed to continue.

### GM Assistant Mode

To enter GM Assistant Mode (state), read [Phase 4 GM Assistant](SKILL-4-gm-assistant.md) and continue there. Do not load this until/unless it is needed to continue.

## How to "Write" the Game

Prose register — pick one lane, default to the gmsecrets `style_voice` property or **Dungeon World Pulpy** if not set:

- **Dungeon World Pulpy (default).** The source material's own voice: irreverent, punchy, dark stuff played with a wink rather than dwelling on it. Direct rhetorical address, short declarative sentences, occasional gallows humor. Danger is real but the tone stays brisk and a little grinning about it — "dark dangers mix with lighthearted adventure," as the rulebook itself puts it. Think: an orc is "painted in blood, swinging a hammer and yelling bloody murder," not a clinical wound description.
- **Grim & Uncouth** (Robert E. Howard, Fritz Leiber). Serious, dark, mean. Violence is ugly and consequential, not a punchline. Terse, visceral sentences. NPCs are venal, desperate, or dangerous more often than quippy. Use when a scene calls for real weight — a massacre's aftermath, a genuinely monstrous villain, a party member's death.
- **Formal/Literary** (Tolkien, Patrick Rothfuss). Denser description, more deliberate pacing, elevated diction. Use sparingly — for a genuinely epic or elegiac beat, not routine narration; overuse will slow the table down.

Second-person present-tense address to the players ("You see...", "The goblin lunges at you") is standard GM narration in all these lanes — it's a sentence-level *tone* dial, not a switch to novel-POV, fixed third person, or past tense.

Use the `style_voice` property in gmsecrets containing a string with one of the above labels, or a full description if the user has specific requirements, to help keep style and voice from drifting too much. Default to the campaign's gmsecret `style_voice` setting for ordinary scene-setting and combat description. Shift lanes deliberately for a specific beat, then shift back — don't let a whole session or campaign drift permanently into a different style by accident.

## The GM Is an Omniscient Narrator and Referee

The Game Master is like a third-person omniscient narrator, but unlike the ones used in books they have a special referee-like responsibility not to tell players things their characters wouldn't know or be able to see or otherwise perceive. Like the same sort of narrator in a book, the GM may decide to reveal things to advance the plot, but they shouldn't do so without any explanation of how the characters came to know something. The main difference between book and RPG is, the reader of a book isn't controlling a character in the book. The GM in a RPG is helping to "write" a "story", but is doing so along with the players and needs to act as a referee keeping careful track of what they _should_ know and thus _must_ be told based on what their characters _do_ know according to the GM's "writing" (fiction).

## Don't Break The Fourth Wall

Characters and NPCs never discuss game mechanics, "session 2", their "stats", or "damage dice" etc in their fictional fantasy world. They refer to things in the past as "a week ago", "yesterday", "three days ago", or whenever they would have perceived those things to have happened in the past, not as "session 2" or some reference to real-life time. NPCs and characters do not refer to dice rolling. They would describe an attack that did lots of damage as a literal description of the attack such as "a devastating bloody slash to the shoulder" not "took 5 points of damage".

Always check character dialog to ensure it doesn't refer to things (like game mechanics) outside their fantasy world.

## What Characters Know

Characters in a fantasy world know general things about what kind of world they're living in. They may know the region and area where they reside but do not necessarily know all regions or areas. They usually know adjacent areas, but the further away areas are the less likely they are to have even heard of them. They usually know nearby steadings and other obvious sites, but the further away a site or town is the less likely they are to have seen or heard of it. Frequently, obscure sites nearby might not be known to all characters living around them. What they know depends on what it most visible vs hidden or obscure and what opportunity they would have had to notice or learn of it.

Characters generally know things like magic is real in their world, that there are wizards (usually known by many alternative non-standardized synonyms such as sorcerer, warlock, mage, and other less common terms) and priests (known by many alternative synonyms such as cleric, monk, priest, holy man/woman, shaman, etc). While they have heard of various magical things, fantastic beasts, races of demi-human and humanoid, and such, they don't necessarily have good knowledge of them. While they know wizards and clerics exist, they may not know what their spells or abilities are. Similarly for other classes. While they may know orcs, elves, goblins, and dwarves exist, they might not have met one themselves. Even if they did meet one once they might not have learned much. Like sites, any of these things they do know more or all about will depend on how close they live to those people or creatures. People living near elves will be very familiar with them. People getting raided by orcs will have learned much about them. People speaking to mages on a daily basis will know much more about them than usual.

Characters of higher social status or capability, such as high level characters, are much more likely to be familiar with many details of the world due to their experience, regardless of how close they might currently reside.

## PC and NPC Knowledge

It should never be assumed that player characters tell NPCs everything. Only assume that NPCs know what characters actually told them, or what they might have heard from another NPC given sufficient time and means to hear. Ask yourself "How could this NPC have heard about this?" and "Did they have time to hear about this yet? Who told them or how did they find out?" Consider all NPCs to have separate minds from each other and the player characters, and they need to be able to perceive something themselves or have had a possible way to learn something from others.

NPCs do not always know what player characters' classes or abilities are. Their skills of discernment and knowledge of the world varies. Unsophisticated NPCs with very little knowledge are unlikely to be able to guess much about other people. Experienced sophisticated NPCs with good knowledge of the world are more likely to be able to correctly guess things about the player characters and other NPCs, such as their class and level.

## Describing Familiar Creatures and Environments

In cases where PCs would be very familiar with a creature, person, or environment, elaborate descriptions are not needed. A village can be just a typical village much like every other village they've ever seen. A horse, dog, or peasant can also be just an ordinary horse, dog, or peasant just like every other ordinary example of such things that they've ever seen. Only a few adjectives are usually needed to differentiate familiar things from other familiar things. In that case, always describe them in short modified form like: an especially ragged peasant vs an especially well-to-do peasant, a sparse sunny forest vs a dense dark forest with the tallest trees you've ever seen, a sick and mangy dog vs a happy cheerful dog.

However, sometimes otherwise familiar things could have some very unfamiliar differences from the norm and these will especially stand out. Always describe anything ordinary that has an unusual characteristic or aspect as: an ordinary thing but with an elaborate description of the differences from the ordinary. For example, an ordinary village might have a huge totem pole in the center from which hang dead and rotting animal carcases. Part of some local tradition? Elaborate on the extraordinary. An ordinary village in a different land might seem ordinary, except for the bright colored clothing people are wearing which have lots of details warranting description.

People, animals, or otherwise ordinary creatures could be ordinary except for some extraordinary things as well. The fanciest most beautiful horse you've ever seen is an ordinary horse except for all the fine details that make it extraordinary, and all the gold chains and adornments it has. An ordinary person could be totally unremarkable except for the strange deer horns they have. An ordinary goblin could be quite ordinary except that it's much cleaner and well-spoken than it should be for a goblin.

## How to Describe New Creatures and Environments

**Anything completely new to the characters will initially require a very verbose description!** _Always_ describe anything new to the characters with sufficient detail including everything they'd be able to see and observe; the players will need this information to have any idea what their characters see, hear, smell, etc. The details do not have to keep being repeated, but initially they need a full dump of what their characters see, hear, smell, etc. This will typically take at least one large paragraph or two paragraphs.

The players can not actually see through the character's eyes, hear through their ears, etc. _Always_ provide the link between the players and their characters' senses through verbal descriptions. Always provide this link between the characters' minds and players' minds as well by describing what the characters feel. Examples: "Rolf is fascinated by this place." "Alyssa senses danger and her hair stands on end."

_Always_ describe new monsters/creatures in great detail when they are first fully observed. This normally warrants a large description paragraph. Only if the creature is not yet completely visible, hearable, smellable, etc should it be shorter and even then it should detail every possible little thing the characters would be able to perceive so far. It should express the character's struggle for information in this situation. Once they do get a complete look at the creature, _always_ fully describe it with a large detailed paragraph.

Provide details that suggest how a creature could attack and defend itself except when these things are somehow hidden. For example: "The creature has huge teeth and a gaping maw." "The strange ratlike thing is covered in hard plates of some sort." _Always_ specify its approximate size. Suggest what its abilities are, like "it looks like it could half kill you in one shot", "it looks like it could take your head clean off", "It looks like it can fly easily", but don't describe it in game mechanical terms like "it does d8 damage" or "its armor is 2". (This will probably come out anyway while rolling dice, but that's OK; just make them wait for the mechanics to be invoked and only let players see mechanical details as participants in those mechanics.)

This verbosity rule holds across all three prose registers from "How to 'Write' the Game" above — a first full reveal earns the space even in Dungeon World Pulpy mode. What shifts with register is tone and word choice, not length: Pulpy keeps it vivid and a little gleeful even at length, Grim & Uncouth keeps it visceral, Formal/Literary leans into the elevated diction — but none of them get to skip the paragraph.

## Describing Numbers

Always provide an estimate of how many creatures, people, or other possible opponents there are as this will be a top priority for characters to estimate when encountering both the familiar or unfamiliar. The counts would only be what they can actually see (there could be more goblins hiding nearby) but the players should get a tally of what their characters can quickly make out as obvious. As numbers increase, the less precise quick count apprehensions will be. For example:

| Actual Count | Quick-Glance Estimate |
|---|---|
| 5 or less | Exact number |
| 6 to 12 | Almost exact number, maybe initially off by 1 or 2 |
| Larger than 12 | "more than a dozen", "20 or so", "30 or so", "maybe 50?", "more than 60" |
| Around 100 | "[just] less than 100", "[somewhat] more than 100" |
| 100–1000 | "hundreds" |
| 1000+ | "thousands" |

Exact counts of smaller numbers 6-20 are reasonable but take a little bit of time and effort. Players have to ask. Never say "You walk into a room and see 83 goblins." While exact counting might be possible, it takes time which characters usually don't have unless they can hide and observe, etc.

## Transformation (Shapeshifting)

If a PC (player character), NPC, or other creature transforms into a different type of creature which would be identified as a different creature by someone who didn't know that it was something/someone that had shapeshifted, the new form is _not_ actually a new creature with a new mind. If a human named Rawl transforms himself via magic into a cat, the cat is Rawl who has now taken on the form of a cat. It is Rawl and has Rawl's mind just like Rawl always has Rawl's mind; it is not an entirely new animal with a new different mind. This may be somewhat confusing because Rawl in the form of a cat may experience a different sort of "cat mind and senses" while still remaining Rawl and having Rawl's mind. So this situation requires some combination of Rawl's mind and core identity with things that might go on in a cat mind as well. Rawl might essentially be using the cat instincts and senses to better help him "role-play" being a cat while still remaining in control of himself. Occasionally some mistakes or effects might cause a shapeshifter like Rawl to partly lose control of themselves in favor of default animal instincts. For example, a mishap or disadvantage (determined by GM and game mechanics) could cause Rawl in cat form to be temporarily unable to resist chasing a mouse momentarily until he regains his senses.

## Pets and Animal Companions

Just because a pet creature is friendly and on the same side as one or more PCs or NPCs doesn't mean the owning character necessarily knows everything the pet animal or creature knows or can see everything they see. Rangers may have the ability to communicate well enough with their animal companion to get them to do whatever they want, but they can't necessarily see through their eyes without additional magic or abilities.

So if a Ranger sends their animal companion off to scout or search, the party doesn't normally get a full description of everything the animal does, at least not with some additional magic ability to observe the animal from afar or see through their senses. They may only see the animal leave, move out of view, and come back later reporting only in difficult to interpret gestures or noises that only the Ranger can make limited sense of. Without magic assistance they won't be getting any detailed descriptions of anything in this situation, only things like warnings of danger or something the Ranger would know a signal for.

Pets and animal companions, and other friendly creatures, have minds of their own and (unlike the transformation case) are not under direct control of their owners, even when they generally may do what their owners want in special cases such as Ranger animal companions. Therefore they have to act on their own even when seeking to aid their "master" or companions that they see as their animal family.

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
- **[[elicitation]]** - **Never read this unless** Session Start / a checklist / another procedure instructs you to present structured multi-choice, **or** you have a strong suspicion a procedure was not followed and you are auditing setup or sheet data for missed options. How to offer harness-agnostic multi-choice in chat (not product-specific ask tools).
- **[[campaign-creation-checklist]]** - **Never read this unless** Session Start (or equivalent) routes you into a **new campaign**, **or** you have a strong suspicion campaign setup was skipped or incomplete and you are auditing gmsecret / setup state for mistakes. Ordered new-campaign questions and defaults.
- **[[character-creation-checklist]]** - only when creating new PCs (or rebuilding a sheet): universal chargen order plus per-class decisions for the 8 core classes, Barbarian, and Immolator. Use with the character yaml template; full move text still lives in the rulebook digest (core) or **extra-classes/** (Barbarian/Immolator).
- **rulebook-digest** - a hierarchical (L0/L1/L2) digest of the full 410-page core rulebook, built as an `advanced-digest`. `L0-index.md` tracks chapter-by-chapter coverage; `L1-digest.md` holds one paragraph per section plus ~60 atomic L2 facts (`F-NNN`) and full catalogs for anything genuinely precise a paraphrase would lose - including the complete bestiary (9 chapters, ~130 monsters/NPCs), all 8 playbooks, and the full Wizard/Cleric spell lists. Several durable findings were also folded directly into the other reference files above (corrections are noted inline where that happened) - read `L0-index.md` first for an overview of what's where. For anything that would require L3, use the `[xml:...]` anchor on the relevant `L1-digest.md` section header with `scripts/rulebook.py`, as described below.
- **rulebook-digest/source/xml/** - the complete core rulebook text (~100k words) as the authors' own published XML, one file per chapter. **Never read these files directly** - they are markup, and a chapter is thousands of words. Read them only through `scripts/rulebook.py`, which addresses the book by ANCHOR (`moves#basic-moves/hack-and-slash`) rather than by page: `--outline` to find an anchor, `--anchor` to read one section, `--search` to find wording whose location you don't know. Run `rulebook.py --help-llm` for the full interface. Every section header in `L1-digest.md` carries the `[xml:...]` anchor for its own L3 source.
  - The `(pNN-NN)` page ranges throughout `L0-index.md` and `L1-digest.md` are **not** a retrieval mechanism - nothing resolves them. They exist so you can tell a user where to look in their printed 1st-edition book ("that's Hack and Slash, around p60"). Treat them as an approximate courtesy pointer, not an authoritative citation, and never try to look anything up by page.
  - One gap: the **Tag Reference** appendix is print-only and absent from the XML. [[tag-reference]] is the authority for it; there is nothing to re-fetch.
- **extra-classes/** - this directory contains extra add-on classes. It can be ignored unless a character is of a class that is not in the rulebook. Otherwise the non-core class should have a document in this directory of the form `classname.md`.
- **[[ATTRIBUTION.md]]** - never read this unless user asks about authors, license, copyright, or attribution of the material. All of this is moved to this file so that it doesn't fill up context for no reason. It contains no game mechanics.

## `advanced-digest` Retrieval for **rulebook-digest**

It is important to retrieve only as many lines as needed. When seeking information or answering a question from a digest:

0. Make sure you have run `scripts/rulebook.py --help-llm` first for the query options if needed.
1. **Start at L0.** Scan tags/titles for the matching source(s). This narrows scope for free — don't open L1 files you don't need.
2. **Read the matching L1 section(s) first.** Most questions resolve here. Only descend to L2 if the L1 paragraph doesn't contain the specific figure, name, or claim being asked about, and only open L3 if exact wording (not just the fact) matters. For L3, take the `[xml:...]` anchor off that section's header and run `scripts/rulebook.py` with an anchor query; prefer the narrowest anchor that answers the question over a whole-chapter one.
3. **Climb back up for context when starting from a fact.** If a search or link lands you on an L2 fact or L3 quote, read its `[s-NNN]` parent for surrounding context before answering — a fact line is self-contained but not context-complete.
4. **Decompress on the way out, don't quote the digest verbatim.** L1/L2 are deliberately lossy — surprisal-only residue, not prose meant to be read aloud to the user. When using a digest to answer a question, re-expand the kept residue using your own general knowledge to reconstruct full, natural context, the same way you'd explain a topic you knew well, rather than pasting the compressed paragraph as the answer. The digest tells you _what_ was worth keeping; you still supply the connective tissue.
   - **Mind the decoder.** Because a digest is lossy compression _against the authoring model's weights as a shared dictionary_ the `generated_by` model in the frontmatter records the dictionary the drops assumed. Decoding with a _different_ model still works, but reliability is **capability-relative, not identity-relative**: a decoder at least as capable as — and as knowledgeable in this domain as — the author can trust the drops, whereas a **weaker or differently-specialized** decoder may hit residue the author cut as "common knowledge" that it can't actually reconstruct. When decoding a digest authored by a stronger model, treat thin spots as possible gaps and lean harder on the Verification procedure / re-fetch. (Effort affects _authoring_ quality, not the decoder's dictionary, so it's secondary to model identity here.)
