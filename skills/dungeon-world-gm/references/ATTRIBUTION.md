# Attribution

## Dungeon World GM Agent Skill

This skill was developed by NimrodX (steam, discord) - GitHub username NimrodXMods.

Copyright (C) 2026 by NimrodX - Except as otherwise specified, all contents of dungeon-world-skill are licensed according to CC BY-NC-SA 4.0 Attribution-NonCommercial-ShareAlike 4.0. See [LICENSE](https://github.com/NimrodXMods/dungeon-world-skill/blob/main/LICENSE.md) in the repo for more.

## Source Material

### Dungeon World (Core Rulebook)

Condensed from: the Dungeon World core rulebook (2012, Sage LaTorra & Adam Koebel, CC BY 3.0) - fully digested at `rulebook-digest/`

The "full" rulebook text is vendored verbatim at `rulebook-digest/source/xml/`, in the authors' own published XML (Sagelt/Dungeon-World `text/` on GitHub, at a pinned commit). See `rulebook-digest/source/ATTRIBUTION.md` for the exact commit, license detail, and refresh instructions. (Ask for [source-attribution](references\rulebook-digest\source\ATTRIBUTION.md) to see the whole thing.)

`assets/monsters.json` (the bestiary) is extracted from that same vendored copy - specifically `rulebook-digest/source/xml/monster_settings/`. See `tools/extract_monsters.py`'s docstring for regeneration instructions.

Dungeon World is the work of **Sage LaTorra** and **Adam Koebel**, and the text of the game is licensed under the **Creative Commons Attribution 3.0 Unported License** (CC BY 3.0). Per the license and the authors' own stated terms, this text may be used, modified, and redistributed freely provided the authors are credited.

- Dungeon World License on GitHub: <https://github.com/Sagelt/Dungeon-World/blob/master/LICENSE>

### Supplements

A number of third-party supplements were used to create the skill. Any reproductions are partial or summarized; none are fully reproduced in the skill.

- a "Dungeon World Guide" (Eon Fontes-May & Sean M. Dunstan)
- "Playbooks" (Version 2.4) - Designer: Stefan Grambart - source of Barbarian and Immolator classes
- "The Inexhaustive List of Dungeon World Questions" (Veilheim, CC BY-NC-SA 4.0)
- Alex Leone's "Dungeon World Quick Reference GM Book" (CC BY-SA 4.0, itself drawing on Truncheon World and Suddenly Ogres)
- Jason Lutes' "The Perilous Wilds" (Revised Edition, CC BY-SA 3.0) - the source of the follower system in [follower-moves](references/follower-moves.md) and the starting basis of several of the generator scripts' tables (name lists, NPC occupations, steadings, regions/areas/sites, dungeons - see each script's own docstring for exactly which tables and page numbers).
