# Dungeon World Agent Skill

[![CI Status](https://raw.githubusercontent.com/NimrodXMods/dungeon-world-skill/refs/heads/badges/status_main.svg)](https://github.com/NimrodXMods/dungeon-world-skill/actions/workflows/validate.yml)
[![Release](https://raw.githubusercontent.com/NimrodXMods/dungeon-world-skill/refs/heads/badges/release.svg)](https://github.com/NimrodXMods/dungeon-world-skill/releases/latest/download/dungeon-world-gm.zip)

## What ... and more imporatnly, Why?

This is a _highly experimental_ "Agent Skill" for any LLM of sufficient capability
that allows the LLM to actually run a tabletop RPG like a GM using the rules for the
Dungeon World RPG. In addition, it can also do lesser related things like answer rules
questions, generate one-off random encounters, or do whatever is a subset of running
a full game. Therefore it can also do one-off tasks to help with a game that it isn't
otherwise aware of.

Why? Primarily because you can't understand new technology and what it is or isn't
good for without experimenting with it. I used to play Infocom games like Zork, I
wrote code for MUDs (Multi-User Dungeons, the first online multiplayer RPGs), and
otherwise have previous experience with pushing the limits of technology when it
comes to RPGs. The latest developments in "AI" (which I consider to be a
misnomer) in the form of large language generative transformer models provide a new
opportunity to, yet again, experiment with what new technology can do just like
computers did, just like the internet did, and just like computer graphics did.

So I'm taking that opportunity to implement ideas primarily for the purpose of
learning what works well and what doesnt, and how to get things to work if they can
be done and seem worthwhile. This is ultimately the only way that anything new ever
gets invented.

## What is Dungeon World?

[Dungeon World](https://www.dungeon-world.com/about/) is a
TTRPG (table top role-playing game) where a small group similates a shared
fantasy world together, guided by simple rules that stay out of the way
until they matter. Normally it's played around a table with one person as GM --
describing the world, playing every NPC and monster, posing problems -- while
everyone else plays an adventureous character of so,e sort.

I picked this RPG over other more popular ones because it is simple. Most moves
are decided by 2d6 dice rolls. There's no map grid, no turn tracker — just fiction,
moves, and dice. This makes it less complex and less formal than more
wargame-like "d20" systems. The rulebook text os also CC-BY licensed making it
free to use as necessary.

## dungeon-world-gm

This is a standard [Agent Skill](https://agentskills.io/home) designed to
either act entirely as the Game Master (GM) or assist a human GM by generating
random stuff, looking up rules, or keeping track of things.

Since LLMs aren't really known for being the best at creativity, a large
number of random procedural generation scripts are provided to assist them.
They still aren't the best at creativity, but having a random way to generate
almost everything 10 times over at least helps made them somewhat passable by
themselves, and they can also use the same inference + procedure approach
when assisting a human who can better filter and modify the output.

### Features

- Be the GM and just use an LLM as an assistant for as much or as little as you
  want.
- Be a solo player with one or more characters and get the LLM to be the GM.
- Be a player with a group of other human players and get the LLM to be the GM.
- Interactive guided setup — For whatever you do, menu-driven character and
  campaign creation on hosts that support structured input, falling back to
  plain text elsewhere.
- Hierarchical digest of all DW rules built-in, plus the skill feeds a bunch of
  "GM screen" reference material to the model up front.
- Full LLM-optimized rules available for exact wording when needed (ugly LLM
  text not recommended for direct human consumption).
- "Suddenly Ogres" style roll miss handling gets applied as needed.
- For dice rolls in the game, you can still roll your own dice. Just tell the
  agent that you'll be doing the rolling.
- A dice rolling script using `os.urandom()` to seed the PRNG every time is
  included so the agent can roll the dice for you as well.
- Major random generation material from _The Perilous Wilds_ included.
- Different LLM-optimized `*_gen.py` scripts for randomly generating the
  stuff that LLMs aren't sufficiently creative about on their own:
  - Regions/Areas
  - Dungeons/Sites
  - Steadings (Villages/Cities)
  - NPCs (including "followers")
  - Monsters (standard and random procedural, party-aware difficulty selection)
  - Various random "ideas": treasures, details, discoveries, dangers,
    rumors (with a truth-quality score), room clutter, story hooks,
    standard named magic items, equipment tags, GM moves,
    Discern Realities/Spout Lore miss tricks, and MoRe!
  - Subject + angle (who/what/where/when/why/how) seed token generation.
- Game data stored in yaml format: one file per character sheet as plain
  readable YAML and a "GM Secrets" yaml file rot13 encoded.
- A `story.md` file is generated by default describing your party's exploits.
- All of the above is zipped up and presented for download when you say
  "checkpoint" or make the "End of Session" move.
- Campaigns can be resumed by invoking the skill and uploading the previously
  described zip archive, or the archive can be stored elsewhere depending on
  what file stores your agent has access to.
- Large skill library, but optimized for "progressive disclosure" so materials
  aren't loaded until needed.
- Hot/warm/cold context attention drift prevention for key prompt information.
  (These are agent-visible context injections of reminder strings and prompts
  that are sometimes reloaded as needed to prevent drift.)

### What this is not

This is not a way to crank out mass slop content in the form of poor quality
campaign supplement PDFs to spam the marlet with junk. Some effort has been
made to prevent it from being used in that manner.

### Installation

First check the requirements below, but it should work with Anthropic, SpaceX AI,
or OpenAI's minimum subscription level services at the very least. (I'm unsure if
free options from those providers will work though.)

[Download the latest skill `.zip` here](https://github.com/NimrodXMods/dungeon-world-skill/releases/latest/download/dungeon-world-gm.zip)
(stable link; always the current release asset). Versioned zips remain on
the [releases page](https://github.com/NimrodXMods/dungeon-world-skill/releases)
as well.

Upload it to your LLM agent of choice or install it according to your agent provider's
skill installation procedure. It follows standard [Agent Skill](https://agentskills.io/home)
packaging conventions and should work with Anthropic Claude, xAI Grok, OpenAI ChatGPT,
and probably others.

Then just invoke the skill, usually with: `/dungeon-world-gm`

**Requirements:**

- A model equivalent to Anthropic Claude Sonnet 5, xAI Grok 4.5, OpenAI GPT 4.5,
  or better. Should work with anything with similar capability.
- Multi-step tool use capability.
- Reliable long-context tracking. (The skill is designed to address attention
  drift with reminders from scripts and prompted reloads of key text, but there
  are limits to how much this can compensate with low context length models.)
- _Network access is NOT required._ Once the skill is installed, the agent does
  not need to browse the web or download other information.
- **A sandbox container or similar execution environment with a `bash` or other
  CLI tool call is needed.** This is pretty standard these days though.
- The execution environment must have python 3.0+, python pyz support, and
  temporary file storage that persists between turns. No special tool calls or
  MCP servers are needed, though ones that provide file storage could be one
  means for saving game data.
- Some place for the skill to save campaign data, which can just be you
  downloading the campaign's `.zip` archive from the agent and uploading it
  again later to new sessions or could be a cloud storage drive.

## Copyrights and Licenses

### dungeon-world-skill Copyright (C) 2026 by NimrodX

Except as otherwise specified, all contents of dungeon-world-skill are
licensed according to CC BY-NC-SA 4.0 Attribution-NonCommercial-ShareAlike 4.0

The `yamledit` utility is covered by the MIT license.

Parts of this skill's references are condensed from: the Dungeon World core
rulebook (2012, Sage LaTorra & Adam Koebel, CC BY 3.0) - see `rulebook-digest`

Dungeon World is the work of **Sage LaTorra** and **Adam Koebel**, and the text
of the game is licensed under the **Creative Commons Attribution 3.0 Unported
License** (CC BY 3.0). Per the license and the authors' own stated terms, this
text may be used, modified, and redistributed freely provided the authors are
credited.

- Dungeon World License: <https://github.com/Sagelt/Dungeon-World/blob/master/LICENSE>

### Supplements Used

Parts of the skill's references are condensed from the following:

- Jason Lutes' "The Perilous Wilds" (Revised Edition, CC BY-SA 3.0) - the source
  of the follower system in `follower-moves.md` and several of the generator
  scripts' tables (name lists, NPC occupations, steadings, regions/areas/sites,
  dungeons - see each script's own docstring for exactly which tables and page
  numbers).
- Alex Leone's "Dungeon World Quick Reference GM Book" (CC BY-SA 4.0, itself
  drawing on Truncheon World and Suddenly Ogres)
- a "Dungeon World Guide" (Eon Fontes-May & Sean M. Dunstan)
- "The Inexhaustive List of Dungeon World Questions" (Veilheim, CC BY-NC-SA 4.0)

See [LICENSE.md](LICENSE.md) for more details.