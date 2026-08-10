#!/usr/bin/env python3
"""
idea_gen.py – RPG random generation tables
(Treasure, Treasure Objects, Discovery, Danger, story hooks, room clutter,
rumors, and misc prompts)

Treasure here is treasure no monster owns. A monster's own haul comes from
monster_gen.py --treasure, which rolls the creature's damage die against the
same shared table in assets/treasure.json.

For a generic NPC appearance/personality/quirk trait, see npc_gen.py
instead - it's rolled there by default for every NPC (see --no-traits/
--full-traits), since that's where it's actually used.

Usage:
  python idea_gen.py                  # every table, three results each (default -n 3)
  python idea_gen.py treasure
  python idea_gen.py danger discovery
  python idea_gen.py equipment-tag -n 2   # N tags in one combined result
  python idea_gen.py gmmove
  python idea_gen.py story-hook -n 1      # single result when you want one
  python idea_gen.py rumor
  python idea_gen.py treasure-object      # three separate looks to choose among
"""

import argparse
import math
import random
import sys
from typing import List, Tuple, Dict, Any

from _util import apply_seed, d, force_utf8_stdio

force_utf8_stdio()

import _treasure  # sibling module - the treasure table and its objects

# ---------------------------------------------------------------------------
# Treasure (1–18)
#
# The table itself lives in assets/treasure.json, shared with monster_gen.py -
# it used to be copied here and the copy drifted. What stays here is the roll,
# which has to differ: monster_gen.py rolls the monster's damage die, and
# treasure that no monster owns has no damage die to roll.
# ---------------------------------------------------------------------------

def _render_options(options, indent: str) -> List[str]:
    """A bullet menu, each option followed by the categories that built it.

    The category line is not decoration: it is a runnable token. Printing it in
    the comma form that roll_treasure_object accepts means rerolling one axis,
    or a few, is a copy-paste of the line rather than something the reader has
    to remember is possible.
    """
    lines = []
    for opt in options:
        lines.append(f"{indent}- {opt['text']}")
        lines.append("{}  > rolled with treasure-object:{}".format(
            indent, ",".join(opt["categories"])
        ))
    return lines


def _render_value(value: int) -> List[str]:
    """One table entry, plus a menu of looks when the entry leaves them open."""
    text, is_object = _treasure.value_entry(value)
    lines = ["* " + text]
    if is_object:
        options = _treasure.describe_options(exclude_traits=_treasure.VALUE_EXCLUDED)
        lines.append("  looks like (pick one, or mix them):")
        lines.extend(_render_options(options, "    "))
    return lines


def roll_treasure(depth: int = 0, max_depth: int = 3) -> str:
    """Roll 1d6, +1d6 on a 6, up to 3d6 total. Recurse on 'roll again'.

    A 6 counts as its own result and sends you higher up the table, which is
    what lets a monster-free roll reach the top of a table the rulebook expects
    to be reached with a damage die.
    """
    total = d(6)
    hits = []
    # on 6, count the 6 but add another d6
    if total == 6:
        hits.append(6)
        next_roll = d(6)
        total += next_roll
        # on another 6, count 12 but add another d6
        if next_roll == 6:
            hits.append(12)
            total += d(6)

    # clamp to table range just in case
    hits.append(max(1, min(18, total)))

    lines: List[str] = []
    for value in hits:
        lines.extend(_render_value(value))
        if value in _treasure.roll_again_values() and depth < max_depth:
            lines.append(roll_treasure(depth + 1, max_depth))
    return "\n".join(lines)


def roll_treasure_object(spec: str = None) -> str:
    """A whole object as a menu, or one roll from each named category.

    `spec` is one or more category names separated by commas. That is the same
    shape the "rolled with" line prints, deliberately: a caller can lift that
    line out of a result and rerun any part of it verbatim, without having to
    know that the comma form exists.

    Named categories return one result each rather than a menu - the caller has
    already narrowed the axis, and -n covers wanting several.
    """
    if spec:
        names = [name.strip() for name in spec.split(",") if name.strip()]
        unknown = [name for name in names if name not in _treasure.categories()]
        if unknown or not names:
            return ("Unknown treasure-object category: {}. Valid categories, "
                    "usable singly or comma-separated: {}".format(
                        ", ".join(unknown) or "(none given)",
                        ",".join(_treasure.categories())))
        return "\n".join(
            f"{name} → {_treasure.roll_category(name)}" for name in names
        )
    return "\n".join(_render_options(_treasure.describe_options(1), "  "))

# ---------------------------------------------------------------------------
# Discovery (1d12 × 3 nested tables)
# ---------------------------------------------------------------------------

def pick_range(table: List[Tuple[int, int, str]], roll: int) -> str:
    for lo, hi, val in table:
        if lo <= roll <= hi:
            return val
    return "???"

# Main category (1d12)
DISCOVERY_MAIN = [
    (1, 1, "unnatural feature"),
    (2, 4, "natural feature"),
    (5, 6, "evidence"),
    (7, 8, "creature"),
    (9, 12, "structure"),
]

# --- unnatural feature ---
UNNATURAL_SUB = [
    (1, 1, "divine"),
    (2, 3, "planar"),
    (4, 12, "arcane"),
]
UNNATURAL_DIVINE = [
    (1, 1, "presence/manifestation"),
    (2, 7, "protected place"),
    (8, 10, "cursed/defiled place"),
    (11, 12, "blessed/sacred place"),
]
UNNATURAL_PLANAR = [
    (1, 1, "outpost"),
    (2, 4, "portal/gate"),
    (5, 8, "rift/tear"),
    (9, 12, "distortion/warp"),
]
UNNATURAL_ARCANE = [
    (1, 4, "blight/mutation"),
    (5, 7, "enchantment/portal"),
    (8, 10, "taint/residue"),
    (11, 12, "source/resource"),
]

NATURAL_SUB = [
    (1, 2, "lair"),
    (3, 5, "terrain change"),
    (6, 7, "water feature"),
    (8, 9, "landmark"),
    (10, 11, "flora/fauna"),
    (12, 12, "resource"),
]
NATURAL_LAIR = [
    (1, 4, "ruin"),
    (5, 7, "cave/tunnel"),
    (8, 9, "nest/hive/aerie"),
    (10, 12, "den/burrow/warren"),
]
NATURAL_TERRAIN = [
    (1, 3, "hollow/cleft/defile"),
    (4, 6, "canyon/valley/vale/dale"),
    (7, 8, "multilevel/tiered"),
    (9, 10, "pocket of terrain"),
    (11, 12, "slope up/down"),
]
NATURAL_WATER = [
    (1, 1, "sea/ocean"),
    (2, 4, "river"),
    (5, 6, "lake/pond/mere/tarn"),
    (7, 10, "brook/stream/rill"),
    (11, 12, "spring/hot spring"),
]
NATURAL_LANDMARK = [
    (1, 1, "oddity"),
    (2, 3, "striking landscape"),
    (4, 6, "earth-based"),
    (7, 9, "plant-based"),
    (10, 12, "water-based"),
]
NATURAL_FLORA = [
    (1, 3, "notable plant/flower"),
    (4, 5, "notable tree/brush"),
    (6, 8, "notable beast"),
    (9, 10, "useful plant/herb/root"),
    (11, 12, "useful beast"),
]
NATURAL_RESOURCE = [
    (1, 3, "game/fruit/vegetable"),
    (4, 6, "timber/stone"),
    (7, 9, "herbs/spice/dye source"),
    (10, 11, "copper/tin/iron"),
    (12, 12, "gold/silver/gems"),
]

# --- evidence ---
EVIDENCE_SUB = [
    (1, 6, "tracks/spoor"),
    (7, 10, "remains/debris"),
    (11, 12, "stash/cache"),
]
EVIDENCE_TRACKS = [
    (1, 2, "trail of blood/fluid"),
    (3, 4, "signs of violence"),
    (5, 7, "multiple/many signs"),
    (8, 10, "definite/recent/clear"),
    (11, 12, "faint/old/unclear"),
]
EVIDENCE_REMAINS = [
    (1, 4, "bones of creature"),
    (5, 7, "creature carcass"),
    (8, 10, "junk/refuse"),
    (11, 11, "lost supplies/cargo"),
    (12, 12, "tools/weapons/armor"),
]
EVIDENCE_STASH = [
    (1, 5, "trinkets/coins"),
    (6, 8, "tools/weapons/armor"),
    (9, 10, "map/note"),
    (11, 11, "food/supplies"),
    (12, 12, "treasure"),
]

# --- structure ---
STRUCTURE_SUB = [
    (1, 1, "enigmatic"),
    (2, 3, "infrastructure"),
    (4, 5, "dwelling"),
    (6, 7, "religious"),
    (8, 11, "ruin"),
    (12, 12, "steading"),
]
STRUCTURE_ENIGMATIC = [
    (1, 2, "oddity"),
    (3, 6, "mound/earthworks"),
    (7, 9, "monument/megalith"),
    (10, 12, "statue/idol/totem"),
]
STRUCTURE_INFRA = [
    (1, 4, "signpost/marker"),
    (5, 6, "bridge/aqueduct"),
    (7, 10, "track/path/trail/road"),
    (11, 12, "mine/quarry"),
]
STRUCTURE_DWELLING = [
    (1, 4, "campsite/hovel/hut"),
    (5, 7, "homestead/farmstead"),
    (8, 10, "inn/toll house/mill"),
    (11, 12, "tower/keep/castle"),
]
STRUCTURE_RELIGIOUS = [
    (1, 3, "grave marker"),
    (4, 6, "graveyard/burial ground"),
    (7, 9, "tomb/crypt/barrow"),
    (10, 11, "temple/monastery"),
    (12, 12, "great temple/sanctuary"),
]
STRUCTURE_RUIN = [
    (1, 3, "dungeon"),
    (4, 6, "steading"),
    (7, 8, "religious (1d8+4)"),
    (9, 10, "dwelling (1d8+4)"),
    (11, 12, "infrastructure (1d8+4)"),
]
STRUCTURE_STEADING = [
    (1, 5, "village"),
    (6, 8, "town"),
    (9, 11, "keep"),
    (12, 12, "city"),
]

def roll_discovery() -> str:
    main_roll = d(12)
    main = pick_range(DISCOVERY_MAIN, main_roll)

    if main == "unnatural feature":
        sub_roll = d(12)
        sub = pick_range(UNNATURAL_SUB, sub_roll)
        if sub == "divine":
            detail = pick_range(UNNATURAL_DIVINE, d(12))
        elif sub == "planar":
            detail = pick_range(UNNATURAL_PLANAR, d(12))
        else:  # arcane
            detail = pick_range(UNNATURAL_ARCANE, d(12))
        return f"Discovery → unnatural feature → {sub} → {detail}"

    elif main == "natural feature":
        sub_roll = d(12)
        sub = pick_range(NATURAL_SUB, sub_roll)
        if sub == "lair":
            detail = pick_range(NATURAL_LAIR, d(12))
        elif sub == "terrain change":
            detail = pick_range(NATURAL_TERRAIN, d(12))
        elif sub == "water feature":
            detail = pick_range(NATURAL_WATER, d(12))
        elif sub == "landmark":
            detail = pick_range(NATURAL_LANDMARK, d(12))
        elif sub == "flora/fauna":
            detail = pick_range(NATURAL_FLORA, d(12))
        else:  # resource
            detail = pick_range(NATURAL_RESOURCE, d(12))
        return f"Discovery → natural feature → {sub} → {detail}"

    elif main == "evidence":
        sub_roll = d(12)
        sub = pick_range(EVIDENCE_SUB, sub_roll)
        if sub == "tracks/spoor":
            detail = pick_range(EVIDENCE_TRACKS, d(12))
        elif sub == "remains/debris":
            detail = pick_range(EVIDENCE_REMAINS, d(12))
        else:  # stash/cache
            detail = pick_range(EVIDENCE_STASH, d(12))
        return f"Discovery → evidence → {sub} → {detail}"

    elif main == "creature":
        return (f"Discovery → creature → Not an immediate threat, but it might become one: "
                + _creature_seed() + "  (seed only - stat it with monster_gen.py)")

    else:  # structure
        sub_roll = d(12)
        sub = pick_range(STRUCTURE_SUB, sub_roll)
        if sub == "enigmatic":
            detail = pick_range(STRUCTURE_ENIGMATIC, d(12))
        elif sub == "infrastructure":
            detail = pick_range(STRUCTURE_INFRA, d(12))
        elif sub == "dwelling":
            detail = pick_range(STRUCTURE_DWELLING, d(12))
        elif sub == "religious":
            detail = pick_range(STRUCTURE_RELIGIOUS, d(12))
        elif sub == "ruin":
            detail = pick_range(STRUCTURE_RUIN, d(12))
        else:  # steading
            detail = pick_range(STRUCTURE_STEADING, d(12))
        return f"Discovery → structure → {sub} → {detail}"

# ---------------------------------------------------------------------------
# Danger (1d12 × 3 nested)
# ---------------------------------------------------------------------------

DANGER_MAIN = [
    (1, 1, "unnatural entity"),
    (2, 6, "hazard"),
    (7, 12, "creature"),
]

# unnatural entity
DANGER_UNNATURAL_SUB = [
    (1, 1, "divine"),
    (2, 3, "planar"),
    (4, 12, "arcane"),
]
DANGER_UNNATURAL_DIVINE = [
    (1, 1, "presence/manifestation"),
    (2, 7, "protected place"),
    (8, 10, "cursed/defiled place"),
    (11, 12, "blessed/sacred place"),
]
DANGER_UNNATURAL_PLANAR = [
    (1, 1, "outpost"),
    (2, 4, "portal/gate"),
    (5, 8, "rift/tear"),
    (9, 12, "distortion/warp"),
]
DANGER_UNNATURAL_ARCANE = [
    (1, 4, "blight/mutation"),
    (5, 7, "enchantment/portal"),
    (8, 10, "taint/residue"),
    (11, 12, "source/resource"),
]

# hazard
# only one that's d10 in this series
DANGER_HAZARD_SUB = [
    (1, 2, "unnatural"),
    (3, 10, "natural"),
]
DANGER_HAZARD_UNNATURAL = [
    (1, 5, "taint/blight/curse"),
    (6, 9, "magical: natural + magic type"),
    (10, 11, "planar: natural + element"),
    (12, 12, "divine: natural + deity"),
]
DANGER_HAZARD_NATURAL = [
    (1, 1, "oddity-based"),
    (2, 2, "tectonic/volcanic"),
    (3, 4, "unseen pitfall (chasm, crevasse, abyss, rift)"),
    (5, 6, "ensnaring (bog, mire, tarpit, quicksand, etc.)"),
    (7, 7, "defensive (created by local creature)"),
    (8, 10, "meteorological (blizzard, thunderstorm, sandstorm, etc.)"),
    (11, 11, "seasonal (fire, flood, avalanche, etc.)"),
    (12, 12, "impairing (mist, fog, murk, gloom, miasma, etc.)"),
]

def roll_danger() -> str:
    main_roll = d(12)
    main = pick_range(DANGER_MAIN, main_roll)

    if main == "unnatural entity":
        sub_roll = d(12)
        sub = pick_range(DANGER_UNNATURAL_SUB, sub_roll)
        if sub == "divine":
            detail = pick_range(DANGER_UNNATURAL_DIVINE, d(12))
        elif sub == "planar":
            detail = pick_range(DANGER_UNNATURAL_PLANAR, d(12))
        else:
            detail = pick_range(DANGER_UNNATURAL_ARCANE, d(12))
        return f"Danger → unnatural entity → {sub} → {detail}"

    elif main == "hazard":
        sub_roll = d(10)
        sub = pick_range(DANGER_HAZARD_SUB, sub_roll)
        if sub == "unnatural":
            detail = pick_range(DANGER_HAZARD_UNNATURAL, d(12))
        else:
            detail = pick_range(DANGER_HAZARD_NATURAL, d(12))
        return f"Danger → hazard → {sub} → {detail}"

    else:  # creature
        return (f"Danger → creature →  immediate threat: " + _creature_seed()
                + "  (seed only - stat it with monster_gen.py)")

# ---------------------------------------------------------------------------
# Creature (full nested table)
# ---------------------------------------------------------------------------

CREATURE_MAIN = [
    (1, 4, "monster"),
    (5, 10, "beast"),
    (11, 12, "humanoid"),
]

CREATURE_MONSTER_SUB = [
    (1, 1, "extraplanar"),
    (2, 2, "legendary"),
    (3, 5, "undead"),
    (6, 7, "unusual"),
    (8, 9, "beastly"),
    (10, 12, "wild humanoid"),
]
CREATURE_MONSTER_EXTRAPLANAR = [
    (1, 1, "divine/demonic lord"),
    (2, 2, "angel/demon"),
    (3, 5, "cherub/imp"),
    (6, 12, "elemental"),
]
CREATURE_MONSTER_LEGENDARY = [
    (1, 1, "huge + oddity"),
    (2, 2, "dragon/giant + beast"),
    (3, 4, "dragon/giant"),
    (5, 12, "beast + huge"),
]
CREATURE_MONSTER_UNDEAD = [
    (1, 1, "lich/vampire/mummy"),
    (2, 2, "wight/wraith"),
    (3, 4, "wisp/ghost/specter"),
    (5, 12, "skeleton/zombie/ghoul"),
]
CREATURE_MONSTER_UNUSUAL = [
    (1, 4, "slime/ooze/jelly"),
    (5, 8, "plant/fungus/parasite"),
    (9, 10, "golem/homunculus"),
    (11, 12, "fey/fairy"),
]
CREATURE_MONSTER_BEASTLY = [
    (1, 1, "beast + aberrance"),
    (2, 2, "beast + element"),
    (3, 3, "beast + oddity"),
    (4, 7, "beast + ability"),
    (8, 12, "beast + beast"),
]
CREATURE_MONSTER_WILD = [
    (1, 1, "ogre/troll/giant"),
    (2, 5, "orc/hobgoblin/gnoll"),
    (6, 9, "goblin/kobold"),
    (10, 10, "humanoid + oddity"),
    (11, 12, "human + beast"),
]

CREATURE_BEAST_SUB = [
    (1, 2, "water-going"),
    (3, 5, "airborne"),
    (6, 12, "earthbound"),
]
CREATURE_BEAST_WATER = [
    (1, 1, "whale"),
    (2, 2, "squid/octopus"),
    (3, 3, "dolphin/shark"),
    (4, 4, "alligator/crocodile"),
    (5, 5, "turtle"),
    (6, 6, "fish"),
    (7, 7, "crab/lobster"),
    (8, 8, "frog/toad"),
    (9, 9, "eel/snake"),
    (10, 10, "clam/oyster/snail"),
    (11, 11, "jelly/anemone"),
    (12, 12, "insect"),
]
CREATURE_BEAST_AIR = [
    (1, 1, "pteranodon"),
    (2, 2, "condor"),
    (3, 3, "eagle/owl"),
    (4, 4, "hawk/falcon"),
    (5, 5, "heron/crane/stork"),
    (6, 6, "crow/raven"),
    (7, 7, "gull/waterbird"),
    (8, 8, "songbird/parrot"),
    (9, 9, "chicken/duck/goose"),
    (10, 10, "bee/wasp"),
    (11, 11, "locust/dragonfly/moth"),
    (12, 12, "mosquito/gnat/firefly"),
]
CREATURE_BEAST_EARTH = [
    (1, 1, "mammoth/dinosaur"),
    (2, 2, "ox/rhino"),
    (3, 3, "bear/ape/gorilla"),
    (4, 4, "deer/horse/camel"),
    (5, 5, "cat/lion/panther"),
    (6, 6, "boar/pig"),
    (7, 7, "dog/fox/wolf"),
    (8, 8, "vole/rat/weasel"),
    (9, 9, "snake/lizard"),
    (10, 10, "ant/centipede/scorpion"),
    (11, 11, "snail/slug/worm"),
    (12, 12, "termite/tick/louse"),
]

CREATURE_HUMANOID_SUB = [
    (1, 1, "rare"),
    (2, 5, "uncommon"),
    (6, 12, "common"),
]
CREATURE_HUMANOID_RARE = [
    (1, 8, "elf (or 4th most populous demi-human)"),
    (9, 12, "dwarf (or 3rd most populous demi-human)"),
]
CREATURE_HUMANOID_UNCOMMON = [
    (1, 3, "mixed demi-human group (roll for number and each member type)"),
    (4, 7, "dwarf (or 3rd most populous demi-human)"),
    (8, 12, "human (or most populous demi-human)"),
]
CREATURE_HUMANOID_COMMON = [
    (1, 1, "human foreigner"),
    (2, 8, "human"),
    (9, 12, "halfling (or 2nd most populous demi-human)"),
]

def _creature_seed() -> str:
    """A vague "what sort of thing is it" seed, for discovery and danger only.

    NOT exposed as a table of its own. monster_gen.py answers "what creature?"
    with a real stat block - HP, damage, instinct, moves - and having a second
    entry point here that returns only a category ("beast -> earthbound ->
    vole/rat/weasel") invites a model to take this as the answer and improvise
    stats it did not need to invent. It survives because the discovery and
    danger tables both branch into "there is a creature here" and need
    something to say next; treat that as a prompt for which monster to look up,
    not as a substitute for looking one up.
    """
    main_roll = d(12)
    main = pick_range(CREATURE_MAIN, main_roll)

    if main == "monster":
        sub_roll = d(12)
        sub = pick_range(CREATURE_MONSTER_SUB, sub_roll)
        if sub == "extraplanar":
            detail = pick_range(CREATURE_MONSTER_EXTRAPLANAR, d(12))
        elif sub == "legendary":
            detail = pick_range(CREATURE_MONSTER_LEGENDARY, d(12))
        elif sub == "undead":
            detail = pick_range(CREATURE_MONSTER_UNDEAD, d(12))
        elif sub == "unusual":
            detail = pick_range(CREATURE_MONSTER_UNUSUAL, d(12))
        elif sub == "beastly":
            detail = pick_range(CREATURE_MONSTER_BEASTLY, d(12))
        else:  # wild humanoid
            detail = pick_range(CREATURE_MONSTER_WILD, d(12))
        return f"Creature → monster → {sub} → {detail}"

    elif main == "beast":
        sub_roll = d(12)
        sub = pick_range(CREATURE_BEAST_SUB, sub_roll)
        if sub == "water-going":
            detail = pick_range(CREATURE_BEAST_WATER, d(12))
        elif sub == "airborne":
            detail = pick_range(CREATURE_BEAST_AIR, d(12))
        else:
            detail = pick_range(CREATURE_BEAST_EARTH, d(12))
        return f"Creature → beast → {sub} → {detail}"

    else:  # humanoid
        sub_roll = d(12)
        sub = pick_range(CREATURE_HUMANOID_SUB, sub_roll)
        if sub == "rare":
            detail = pick_range(CREATURE_HUMANOID_RARE, d(12))
        elif sub == "uncommon":
            detail = pick_range(CREATURE_HUMANOID_UNCOMMON, d(12))
        else:
            detail = pick_range(CREATURE_HUMANOID_COMMON, d(12))
        return f"Creature → humanoid → {sub} → {detail}"

# ---------------------------------------------------------------------------
# Equipment Tags (this skill's own addition - a random prompt over the
# equipment tags already defined in references/tag-reference.md, useful
# when improvising a new item's tags on the fly rather than picking by hand)
# ---------------------------------------------------------------------------

EQUIPMENT_TAGS = [
    ("Applied", "consumed/inhaled by target"),
    ("Awkward", "unwieldy"),
    ("Dangerous", "GM may freely invoke consequences of careless use"),
    ("Ration", "edible"),
    ("Requires", "needs a condition met to work"),
    ("Slow", "takes minutes+ to use"),
    ("Touch", "used by touching to skin"),
    ("Forceful", "can knock someone back/off feet"),
    ("Messy", "destructively rips things apart"),
    ("Precise", "Hack & Slash with DEX instead of STR"),
    ("Reload", "takes a beat to reset after use"),
    ("Stun", "stun damage instead of normal"),
    ("Clumsy", "-1 ongoing cumulative while worn"),
]

def roll_equipment_tag(n: int = 1) -> str:
    """Roll n equipment tags (default 1), without repeats if n <= len(table)."""
    n = max(1, min(n, len(EQUIPMENT_TAGS)))
    picks = random.sample(EQUIPMENT_TAGS, n)
    lines = [f"{tag}: {desc}" for tag, desc in picks]
    return f"Equipment Tag(s) → " + " | ".join(lines)

# ---------------------------------------------------------------------------
# GM Move (this skill's own addition - a random prompt over the core GM
# move list already in references/gm-agenda-principles-moves.md, for when
# a soft/hard move is called for and nothing specific comes to mind)
# ---------------------------------------------------------------------------

GM_MOVES = [
    "Use a monster, danger, or location move",
    "Reveal an unwelcome truth",
    "Show signs of an approaching threat",
    "Deal damage",
    "Use up their resources",
    "Turn their move back on them",
    "Separate them",
    "Give an opportunity that fits a class's abilities",
    "Show a downside to their class, race, or equipment",
    "Offer an opportunity, with or without cost",
    "Put someone in a spot",
    "Tell them the requirements or consequences and ask",
    "Bad weather - see references/weather.md for ideas and moves",
]

def roll_gm_move() -> str:
    move = random.choice(GM_MOVES)
    return f"GM Move → {move}"

# ---------------------------------------------------------------------------
# Discern Realities / Spout Lore Miss (this skill's own addition - a random
# prompt over the trick list already in
# references/gm-agenda-principles-moves.md, for when a pure-info move
# misses and a flat "you don't know" isn't good enough)
# ---------------------------------------------------------------------------

DRSL_MISS = [
    ("Worse than it seemed", "answer for real, just with an unwelcome truth"),
    ("Worse than you thought", "ask what they expected, twist their own guess against them"),
    ("Another castle", "the real answer is out of reach; turn it into a lead/quest hook"),
    ("The abyss gazes back", "what they're studying notices them right back"),
    ("Missed the obvious", "wrong thing entirely; the real danger was elsewhere"),
    ("Change the subject", "skip the answer, throw a complication at them instead (use sparingly)"),
    ("Too late", "the time spent looking cost them their window to act"),
    ("Got separated", "the search pulled them from the group right as trouble shows up alone"),
    ("Trouble halfway", "the act of finding out is itself dangerous"),
    ("Trouble missed earlier", "an old miss comes back to bite them now"),
    ("A lie", "answer wrong, ranging from an obvious lie to a fully convincing one "
              "(use sparingly - \"say what the fiction demands\" still applies)"),
    ("Front/Dungeon move, or offscreen", "reach for the GM move list, or let it happen "
                                         "off view and reveal it later"),
]

def roll_drsl_miss() -> str:
    name, desc = random.choice(DRSL_MISS)
    return f"DR/Spout Lore Miss → {name}: {desc}"

# ---------------------------------------------------------------------------
# Story Hook (object is more than decorative - seed for why it matters)
# Standalone table; where to *suggest* calling it is left to the GM / later
# routing work, not auto-attached to treasure rolls.
# ---------------------------------------------------------------------------

STORY_HOOKS = [
    ("Hidden compartment",
     "a false bottom, hollow hilt, or sewn lining - invent what is inside and "
     "who hid it"),
    ("Maker's mark",
     "monogram, guild stamp, or workshop brand - tie it to a known NPC, "
     "faction, or steading and say why that matters now"),
    ("Old bloodstain / residue",
     "dried blood, ichor, or soot that does not match the current owner - "
     "whose, and what act left it"),
    ("Faint warmth or cold",
     "slightly wrong temperature for the material - a lingering magic, "
     "curse, or bond; invent the source"),
    ("Wrong weight",
     "heavier or lighter than it should be - denser core, void inside, or "
     "something else sharing the mass"),
    ("Repaired break",
     "crack, weld, or re-stitch that does not match the original craft - "
     "when was it broken, and who fixed it"),
    ("Chip matching something known",
     "a missing piece elsewhere (weapon, statue, door, ring) - invent the "
     "mate and who would notice"),
    ("Whisper of curse or blessing",
     "a one-line omen when touched or worn - soft fiction only until you "
     "decide it has teeth"),
    ("Double life",
     "mundane use plus one odd property (opens a lock, points north of a "
     "thing, answers to a name) - keep the odd part small"),
    ("Ownership claim",
     "engraved name, bounty tag, or 'property of…' - someone wants it back"),
    ("Map or note inside",
     "fragment, cipher, or sketch folded/scratched into it - one lead, not "
     "a full quest map"),
    ("Scent or memory trigger",
     "smell or texture that forces a PC or NPC memory - ask who recognizes "
     "it and what it costs them"),
    ("Stolen / return-to",
     "looks recently taken, or bears a plea to return it - invent the "
     "rightful owner and the risk of keeping it"),
    ("Evidence of a recent act",
     "fresh wear, mud, ash, or fingerprints from something that just "
     "happened nearby - connect it to the scene"),
    ("Counts as a key",
     "shape, pattern, or material matches a lock, ward, or door you have "
     "not shown yet - invent the door when they try it"),
    ("Beloved or hated by someone present",
     "an NPC in or near the scene has a strong personal tie - invent who "
     "and what they will do about it"),
]


def roll_story_hook() -> str:
    name, desc = random.choice(STORY_HOOKS)
    return f"Story Hook → {name}: {desc}"


# ---------------------------------------------------------------------------
# Room Clutter (ordinary space junk - not discovery, not dungeon dressing)
# Backs llm-patches "familiar environments": few adjectives, ordinary baseline,
# optional ordinary-but-for-X twist. For dungeon areas use dungeon_gen.py
# dressing instead.
# ---------------------------------------------------------------------------

ROOM_CLUTTER = [
    ("Dust and neglect",
     "thick dust, cobwebs, or a room that has not been used in a while - "
     "ordinary, not a trap"),
    ("Draft or smell",
     "a draft from a crack, kitchen smell, damp, smoke, or perfume - "
     "one sensory note"),
    ("Worn furniture",
     "scuffed chair, sagging bed, nicked table - lived-in ordinary"),
    ("Tools of the trade",
     "needle and thread, hammer, ledger, cooking knife - match the room's "
     "owner if known"),
    ("Food remnants",
     "crumb trail, half-eaten meal, empty cup, greasy napkin"),
    ("Personal scrap",
     "sock, toy, prayer bead, hair ribbon, cheap charm - human scale"),
    ("Vermin sign",
     "mouse droppings, gnawed corner, beetle under a bowl - ordinary pest, "
     "not a monster unless you promote it"),
    ("Weather through the opening",
     "rain streak on the sill, sun stripe, soot from the hearth"),
    ("Religious nick-nack",
     "small idol, chalked holy mark, wilted offering - local faith flavor"),
    ("Work leftover",
     "wood shavings, ink blot, clay scraps, unfinished mending"),
    ("Empty containers",
     "jars, crates, sacks - most empty or half-full of dull staples"),
    ("Chalk or scratch marks",
     "tally marks, a child's drawing, a height mark on a doorframe"),
    ("Laundry or linens",
     "drying cloth, folded blanket, stained apron"),
    ("Ordinary but for one odd detail",
     "describe the room as typical for its kind, then one elaborate "
     "difference that stands out (llm-patches familiar-environments pattern)"),
    ("Something recently moved",
     "scrape mark, dust ring where an object sat, chair not pushed in - "
     "someone was here, not necessarily danger"),
    ("Borrowed light",
     "candle stub, oil lamp low, shutter half-open - lighting only"),
    ("Game or idle pastime",
     "half-finished <dice game/cards/knucklebones>, a scratched board, cheap "
     "stakes left on the table"),
    ("Music left out",
     "a <lute/pipe/drum/whistle> with a broken string or missing stick - not "
     "treasure, just put down"),
    ("Wet gear drying",
     "<cloak/boots/saddle blanket> dripping by the <hearth/door/window> - "
     "ordinary travel mess"),
    ("Medicine or remedies",
     "a clay pot of <salve/poultices/bitter tea>, stained rag, no magic labels"),
    ("Writing mid-task",
     "open <ledger/letter/recipe> with a blot where the pen stopped; ink still "
     "damp or dried mid-word"),
    ("Children's clutter",
     "wooden <horse/sword/doll>, chalk dust, sticky fingerprints on the "
     "<table/wall/shutter>"),
    ("Hunting or farm take",
     "a brace of <rabbits/birds/fish>, feathers, gutting board - food work, "
     "not a scene clue unless you promote it"),
    ("Mending pile",
     "basket of clothes with <patches/darning/new buttons> half done; needle "
     "still stuck in the fabric"),
    ("Ash and firecare",
     "cold ash raked, fresh <log/peat/dung bricks>, poker still warm or long "
     "cold - match the season"),
    ("Guest traces",
     "extra <cup/bowl/bedroll> that does not match the household set - someone "
     "slept or ate here"),
    ("Ward against bad luck",
     "a <braid of herbs/iron nail over the door/circle of salt> that every "
     "local home has; ordinary superstition"),
    ("Stored bulk",
     "stacked <firewood/sacks of grain/empty casks> taking half the room - "
     "domestic stockpile"),
    ("Broken ordinary thing",
     "a cracked <mug/plate/stool> set aside 'to fix later' and clearly never "
     "fixed"),
    ("Smell that belongs",
     "the room smells strongly of <onions/tallow/wet dog/old beer/tannin> and "
     "nothing else odd"),
    ("Same as always, almost",
     "everything expected for a <kitchen/barracks/shop/cell> - only the "
     "<one object you name> is slightly wrong; keep the rest boring"),
]


def roll_room_clutter() -> str:
    name, desc = random.choice(ROOM_CLUTTER)
    return f"Room Clutter → {name}: {desc}"


# ---------------------------------------------------------------------------
# Rumor (tavern/town secondhand claim + a 0..99 score)
# The score is printed as several interchangeable labels (true-chance /
# truth-strength / true-content ratio) so it is not read as a hard probability.
# Drawn from a mixture: mostly flat Uniform(40, 80) (mean 60 - a bit better
# than a coin flip), thin triangular shoulders toward 0 and 99. Clamped to
# 0..99 (never 100). Optional: later roll d100 under the score for a resolve.
# ---------------------------------------------------------------------------

# P(bulk) on the flat mid band; remainder split equally into lower/upper tails.
_RUMOR_TRUE_BULK = 0.92

RUMORS = [
    "The road (to <steading> or north/e/s/w/ne/nw/se/sw) is closed - bandits, washout, or something worse.",
    "The <keep/government>'s new tax is funding a secret war chest.",
    "Someone important went missing last <market day/other day> and nobody will say who.",
    "<Lights/effects> have been seen over the <old barrow/site> <three/four/more> nights running.",
    "The merchant who just arrived is selling stolen goods.",
    "<festival or holy day> is <coming early or was cancelled>.",
    "A monster (or 'monster') was sighted near the <mill/wood/ford/etc>.",
    "<A noble/official>'s scandal is about to break, and half the steading already knows.",
    "The real treasure from the last expedition never left town.",
    "Bad weather is an omen - someone is cursing the valley.",
    "The <priest/elder/reeve> is not who they claim to be.",
    "<A rival steading> is hiring blades for a quiet job.",
    "The <well/spring/river> is tainted, and people are getting sick.",
    "An old war debt is coming due and outsiders will be blamed.",
    "The map the party <carries or will find> is a deliberate fake.",
    "Someone in this <tavern or room> is an informant for a danger the PCs have not met yet.",
    "The <bridge/ferry/gate> will not open after <dark/the bell> - the watch has orders from someone higher.",
    "A <caravan/messenger/pilgrim band> never arrived from <neighboring steading/the capital> and the guild is pretending nothing is wrong.",
    "The <mine/quarry/forest cut> is closed because they found <bones/old iron/something that should stay buried>.",
    "Children have been singing a <new/old> rhyme about the <party's last fight/a local hero/a coming doom> and no one taught them.",
    "The <innkeeper/barkeep/stablehand> is paying in <foreign coin/old coin/chips of crystal> that nobody mints anymore.",
    "Someone is buying up every <ration/arrow/healing herb/blank parchment> in town at twice the price.",
    "The <cemetery/urn field/sea cliff> has fresh graves that were not there last <week/moon>.",
    "A <wanted poster/bounty notice> went up overnight for a face that looks a lot like <a PC/an ally/someone the party just met>.",
    "The <wizard/hedge-witch/scholar> at the edge of town has stopped taking visitors - smoke still comes from the chimney at odd hours.",
    "Livestock will not drink from the <trough/pond/downstream bend> and the farmers blame <the new mill/the temple/outsiders>.",
    "A wedding between <house A/house B> and <house C/house D> was called off because of a <blood oath/debt/curse> nobody will name.",
    "The night watch is short-handed; half of them have gone to guard a <private warehouse/noble's garden/empty barn>.",
    "Someone carved the same <mark/rune/beast-sigil> on three doors along <Market Street/the docks/the temple lane>.",
    "A <ship/coach/mule train> was expected with <grain/steel/a named passenger> and only the empty <hull/wagon/leads> came back.",
    "The <mayor/reeve/guildmaster> is not sleeping at home - they have a room at the <tavern/temple/keep> under another name.",
    "Dreams of a <flood/fire/crowned stranger/empty throne> are common enough that the <priest/elder> started asking who else saw them.",
]


def _rumor_true_chance() -> int:
    """Integer 0..99 score for a rumor (never 100).

    Not a single fixed meaning - printed as true-chance / truth-strength /
    true-content ratio so the caller picks how to read it. Mixture (flatter
    mid than normal/lognormal):
      - 92%: Uniform(40, 80)  — flat band, mean 60
      -  4%: triangular(0, 40, mode=40)   — trails off toward 0
      -  4%: triangular(80, 100, mode=80) — trails off toward 99 (high is
        100 before clamp so 99 can still appear; result never stays 100)
    Extremes are rare; output is always in 0..99.
    """
    u = random.random()
    if u < _RUMOR_TRUE_BULK:
        sample = random.uniform(40.0, 80.0)
    elif u < _RUMOR_TRUE_BULK + (1.0 - _RUMOR_TRUE_BULK) / 2.0:
        sample = random.triangular(0.0, 40.0, 40.0)
    else:
        # high=100 so the tail can reach 99 after floor; clamp drops 100.
        sample = random.triangular(80.0, 100.0, 80.0)
    return max(0, min(99, math.floor(sample)))


def roll_rumor() -> str:
    claim = random.choice(RUMORS)
    chance = _rumor_true_chance()
    return f'Rumor → "{claim}" (quality = {chance}/100)'


# ---------------------------------------------------------------------------
# Standard Magic Item (this skill's own addition - a random pick from the
# named items in references/magic-items.md; this table just names one, it
# doesn't reproduce the item's effects here, so the GM still needs to look
# it up)
# ---------------------------------------------------------------------------

STD_MAGICITEM = [
    'Argo-Thaan, Holy Avenger',
    'Arrows of Acheron',
    'Axe of the Conqueror-King',
    'Barb of the Black Gate',
    'Bag of Holding',
    'The Burning Wheel',
    "Captain Bligh's Cornucopia",
    'The Carcosan Spire',
    'Cloak of Silent Stars',
    'Coin of Remembering',
    'Common Scroll',
    'Devilsbane Oil',
    'Earworm Wax',
    'The Echo',
    'The Epoch Lens',
    'Farsight Stone',
    'The Fiasco Codex',
    'Flask of Breath',
    'Folly Held Aloft / The Wax Wings',
    'Immovable Rod',
    'Infinite Book',
    'Inspectacles',
    "The Ku'meh Maneuver",
    'Lamented Memento',
    'Lodestone Shield',
    'Map of the Last Patrol',
    "Ned's Head",
    "Nightsider's Key",
    'Sacred Herbs',
    'The Sartar Duck',
    'Tears of Annalise',
    'Teleportation Room',
    "Timunn's Armor",
    "Titus' Truthful Tallow",
    'Tricksy Rope',
    'The Sterling Hand',
    "Vellius's Gauntlets",
    'Violation Glaive',
    'Vorpal Sword',
]

def roll_std_magicitem() -> str:
    item = random.choice(STD_MAGICITEM)
    return f"{item}"

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

TABLES = {
    "treasure":  ("Treasure Table", roll_treasure),
    "treasure-object": ("Treasure Object", roll_treasure_object),
    "discovery": ("Discovery", roll_discovery),
    "danger":    ("Danger", roll_danger),
    "equipment-tag": ("Equipment Tag", roll_equipment_tag),
    "gmmove":    ("GM Move", roll_gm_move),
    "drsl-miss": ("DR/Spout Lore Miss", roll_drsl_miss),
    "story-hook": ("Story Hook", roll_story_hook),
    "room-clutter": ("Room Clutter", roll_room_clutter),
    "rumor":     ("Rumor", roll_rumor),
    "std-magicitem": ("Standard Magic Item", roll_std_magicitem),
}

def resolve_table(name: str):
    """(title, callable) for a requested table, or None if there is no such one.

    "treasure-object:material" asks for one category of a composed object. The
    colon keeps that to a single positional token, so it needs no flag of its
    own and -n keeps working; the categories come from assets/treasure.json
    rather than being listed here, so adding one to the asset is enough.
    """
    if name in TABLES:
        return TABLES[name]
    prefix = "treasure-object:"
    if name.startswith(prefix):
        category = name[len(prefix):]
        return ("Treasure Object: " + category, lambda: roll_treasure_object(category))
    return None


HELP_LLM = """\
idea_gen.py - general-purpose RPG random-idea tables (treasure and what it looks
like, discoveries, dangers, equipment tags, GM moves, Discern Realities/Spout
Lore miss tricks, story hooks, room clutter, rumors, named magic items), useful
any time a random prompt would help creativity, independent of the other
generators.
Default is `-n 3` so you get a short menu to pick from (or mix), not a single
locked-in result. Pass `-n 1` only when you truly want one line.
For a generic NPC appearance/personality/quirk trait, use npc_gen.py instead
(rolled there by default for every NPC - see its --no-traits/--full-traits).
For "what creature is it?", use monster_gen.py - it answers with a real stat
block rather than a category, so there is no creature table here.

USAGE
  idea_gen.py [TABLE ...] [-n N] [--seed N]

TABLE (zero or more; default if omitted: every table below)
  treasure         Treasure Table (1-18 finding-treasure roll) for treasure that
                   no monster owns - a cache, a reward, something washed up. For
                   a monster's own haul use monster_gen.py --treasure instead,
                   which rolls the creature's damage die against the same table.
                   All dice are resolved, so you get "A bag of 300 coins" rather
                   than "1d4x100".
  treasure-object  one composed look per result (bullet + "rolled with" token).
                   Default -n 3 gives three separate looks to choose among.
                   When you know a thing is valuable but not what it IS. You
                   rarely need to ask for it directly: a "treasure" roll that
                   lands on an actual object already brings its own multi-option
                   looks-like menu (see OUTPUT).
  treasure-object:CATEGORY[,CATEGORY...]
                   one roll from each named axis, when you do not want a whole
                   object - or want to redo part of one. Comma-separated, no
                   spaces: treasure-object:material,motif. The seven axes:
                     object_type   what kind of thing it is
                     material      what it is made of
                     gem_type      which stone
                     color         what colour the stone is
                     condition     what shape it is in
                     provenance    who made it, and where from
                     motif         what is shown or engraved
                   Every composed object prints the exact token it was rolled
                   with, so rerolling part of one is a copy-paste.
  discovery        Discovery prompt
  danger           Danger prompt
  equipment-tag    a random equipment tag (see references/tag-reference.md)
  gmmove           a GM move prompt (which move to make, not how to word it)
  drsl-miss        a Discern Realities / Spout Lore miss trick
  story-hook       why an object is more than decorative (hidden compartment,
                   maker's mark, old blood, wrong weight, etc.) - invent the
                   rest; standalone seed, not auto-rolled with treasure
  room-clutter     what's scattered in an ordinary room/scene - few adjectives,
                   familiar-environment junk (see llm-patches). Not discovery
                   (footer reminds: promote only if fiction demands). For
                   dungeon area sensory dressing use dungeon_gen.py dressing
  rumor            tavern/town secondhand claim with angle-bracket slots to
                   fill, plus (quality = N/100). N is 0..99 (never 100), drawn
                   mostly flat on 40-80 (mean ~60). A footer explains that
                   'quality' means true-chance, truth-strength, or true content
                   ratio - not a hard probability. Optional: roll d100 under N
                   later. Does not invent a full front (see fronts reference)
  std-magicitem    a named item from magic-items.md; footer points you to grep
                   that file or the rulebook digest for effects

-n N       how many of each requested table to roll at once (default 3).
           Pass -n 1 for a single result. Exception: "equipment-tag" rolls N
           tags as one combined result rather than N separate single-tag results.
--seed N   reproducible output - dev/debug only, NEVER during play

OUTPUT
  For each requested table (in the order given), a header carrying the exact
  token that produced it - "=== Treasure Object: material === [ TABLE=
  treasure-object:material ]" - followed by -n result line(s). Reuse the
  table token after TABLE= verbatim to ask for more of the same.
  Treasure value lines are prefixed with "* ". Composed looks use bullet
  lines ("- …") each followed by "  > rolled with treasure-object:a,b,c".
  That a,b,c token IS a whole runnable table name - pass it back, whole or
  trimmed to the axes you want, for a different composition.
  A treasure roll that lands on an actual object whose appearance the table
  leaves open is followed by an indented "looks like (pick one, or mix them)"
  menu (several bullets; value shared). Results that are not objects get NO
  menu: coins are coins, and "Useful information" / portal / magical effect
  lines are yours to invent (for the last, see magic-items.md or
  std-magicitem).
  After the results for some tables, a one-line footer may appear:
    room-clutter   ordinary-junk / promote-to-discovery note
    rumor          how to read 'quality'
    std-magicitem  where to look up the item's effects
  Always ends with two reminders: re-roll/modify is fine, and review turns +
  update gm/character yaml if needed.

Err on the side of using this script too much rather than not enough - even
when a result doesn't perfectly fit the situation, it injects entropy that
counteracts an LLM's tendency to repeat its own priors when improvising.

EXAMPLES
  idea_gen.py                        every table, three results each (default)
  idea_gen.py treasure               three treasure rolls
  idea_gen.py danger discovery
  idea_gen.py treasure-object        three separate looks to choose among
  idea_gen.py treasure-object:material
  idea_gen.py treasure-object:material,motif
  idea_gen.py equipment-tag -n 2     two tags in one combined line
  idea_gen.py gmmove
  idea_gen.py story-hook -n 1        one hook only
  idea_gen.py rumor
  idea_gen.py std-magicitem
"""

def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return

    parser = argparse.ArgumentParser(description="RPG idea generator from the provided tables")
    parser.add_argument(
        "tables", nargs="*", default=list(TABLES.keys()),
        help="which tables to roll (default: all). Choices: " + ", ".join(TABLES)
    )
    parser.add_argument("-n", type=int, default=3,
                         help="how many of each to roll at once (default: 3)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed, for reproducibility")
    parser.add_argument("--help-llm", action="store_true", dest="help_llm",
                         help="print the dense full reference written for LLM callers, then exit")
    args = parser.parse_args()

    apply_seed(args.seed)

    resolved = [(name, resolve_table(name)) for name in args.tables]
    unknown = [name for name, entry in resolved if entry is None]
    if unknown:
        print(f"Unknown table(s): {unknown}")
        print("Available:", ", ".join(TABLES))
        print("Plus treasure-object:CATEGORY for one axis of an object -",
              ", ".join(_treasure.categories()))
        return

    for name, (title, fn) in resolved:
        # The tag repeats the exact token that produced this block. Without it a
        # reader sees "=== Treasure Object: material ===" and has to guess the
        # spelling to ask again - and the colon forms are the easiest to guess
        # wrong, since nothing else in the output shows they exist.
        print(f"=== {title} === [ TABLE={name} ]")
        if name == "equipment-tag":
            print(fn(args.n))
        else:
            for i in range(0, args.n):
                print(fn())
            if name == "std-magicitem":
                print("(grep from magic-items.md or search line in rulebook digest)")
            elif name == "room-clutter":
                print("(ordinary junk - promote to discovery only if fiction demands)")
            elif name == "rumor":
                print("('quality' should be interpreted as true-chance, truth-strength, or true content ratio)")

        print()

    print("Reminder: accepting the results as-is isn't mandatory. Modify or re-roll if results don't fit.")
    print("Reminder: review previous turns and update gm and character yaml files if needed!")

if __name__ == "__main__":
    main()
