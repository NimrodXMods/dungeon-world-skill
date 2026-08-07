# Dungeon World LLM Skill(s)

Have you ever wanted to _not_ be the GM, but nobody else around seemed to be
willing or able to GM either? Well here's your solution!

Have you ever just wanted some assistance with being a GM to keep the
game moving? Well, this may be your solution as well.

Does it work? Well, LLMs aren't the most creative but it's not unplayable.
LLMs will do a better job as GM assistants.

## What is Dungeon World?

Dungeon World is a TTRPG (table top role-playing game) where a small group tells
a shared fantasy story together, guided by simple rules that stay out of the way
until they matter. Normally it's played around a table with one person as GM --
describing the world, playing every NPC and monster, posing problems -- while
everyone else plays their adventuresome character.

Play moves through conversation: when a character tries something risky, the
player rolls 2d6 plus a stat, and the result (strong hit, partial success, or a
miss) shapes what happens next. No map grid, no turn tracker — just fiction,
moves, and dice.

## dungeon-world-gm

This is an LLM "skill" designed to either act entirely as the Game Master (GM)
or assisting the human game master by generating random stuff, looking up
rules, or keeping track of things.

Since LLMs aren't really known for being the best at creativility, a large
number of random generation scripts are provided to assist them. They still
aren't that great at creativity, but having a random way to generate almost
everything 10 times over at least helps made them somewhat passable, and they
can also use the same scripts when assisting a GM.

For dice rolls in the game, you can still roll your own dice. Just tell the
agent that you'll be doing the rolling.

## Installation

Download the .zip file and install it according to your agent provider's
skill installation procedure. It follows standard skill packaging convensions
and should work with Anthropic Claude, xAI Grok, and OpenAI ChatGPT.

**Requirements:**

- A model equivalent to Anthropic Claude Sonnet 5, xAI Grok 4.5, OpenAI GPT 4.5,
  or better. Should work with anything with similar capability.
- Multi-step tool use capability.
- Reliable long-context tracking. The skill is designed to address attention
  drift with reminders from scripts and prompted reloads of key text.
- _Network access is NOT required._ Once the skill is installed, the agent does
  not need to browse the web or download other information.
- **A sandbox container or similar execution environment with a `bash` or other
  CLI tool call is needed.** This is pretty standard these days though.
- The execution environment must have python 3.0+, python pyz support, and
  temporary file storage that persists between turns. No special tool calls or
  MCP servers are needed, though they could be one means for saving game data.
- Some place for the skill to save campaign data, which can just be you
  downloading the campaign's `.zip` archive from the agent and uploading it
  again later to new sessions.

## Copyrights and Licenses

### dungeon-world-skill Copyright (C) 2026 by NimrodX

Except as otherwise specified, all contents of dungeon-world-skill are
licened according to CC BY-NC-SA 4.0 Attribution-NonCommercial-ShareAlike 4.0

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

Parts of the skill's references are condensed from the followiong:

- a "Dungeon World Guide" (Eon Fontes-May & Sean M. Dunstan)
- "The Inexhaustive List of Dungeon World Questions" (Veilheim, CC BY-NC-SA 4.0)
- Alex Leone's "Dungeon World Quick Reference GM Book" (CC BY-SA 4.0, itself
  drawing on Truncheon World and Suddenly Ogres)
- Jason Lutes' "The Perilous Wilds" (Revised Edition, CC BY-SA 3.0) - the source
  of the follower system in [[follower-moves]] and several of the generator
  scripts' tables (name lists, NPC occupations, steadings, regions/areas/sites,
  dungeons - see each script's own docstring for exactly which tables and page
  numbers).

See [[LICENSE]] for more details.