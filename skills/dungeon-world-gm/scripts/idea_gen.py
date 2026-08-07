#!/usr/bin/env python3
"""
idea_gen.py – RPG random generation tables
(Treasure Finder, Finding-treasure detail, Discovery, Danger, Creature, Details)

For a generic NPC appearance/personality/quirk trait, see npc_gen.py
instead - it's rolled there by default for every NPC (see --no-traits/
--full-traits), since that's where it's actually used.

Usage:
  python idea_gen.py                  # one result from every table
  python idea_gen.py treasure         # only treasure
  python idea_gen.py danger creature details
  python idea_gen.py details
  python idea_gen.py equipment-tag -n 2   # roll 2 equipment tags at once
  python idea_gen.py -n 3 gmmove        # a GM move prompt
  python idea_gen.py drsl-miss          # a Discern Realities/Spout Lore miss trick
  python idea_gen.py std-magicitem      # a named item from magic-items.md
"""

import random
import argparse
import sys
from typing import List, Tuple, Dict, Any

# ---------------------------------------------------------------------------
# Dice helpers
# ---------------------------------------------------------------------------

def d(sides: int) -> int:
    return random.randint(1, sides)

def nd(n: int, sides: int) -> int:
    return sum(d(sides) for _ in range(n))

# ---------------------------------------------------------------------------
# Treasure table (1–18)
# ---------------------------------------------------------------------------

TREASURE = {
    1:  "A few coins, 2d8 or so",
    2:  "A useful item worth 2d6 coins or so",
    3:  "Several coins, about 4d10",
    4:  "A small valuable (gem, art), worth 2d10x10 coins, 0 weight",
    5:  "Some minor magical trinket",
    6:  "Useful clue (map, note, etc.)",
    7:  "Bag of coins, 1d4x100, 1 weight per 100",
    8:  "A small item (gem, art) of great value (2d6x100 coins, 0 weight)",
    9:  "A chest of coins and other small valuables (worth 3d6x100 coins, 1 weight per 100)",
    10: "A magical item or magical effect",
    11: "Many bags of coins, 2d4x100 or so",
    12: "The useful clue is also highly valuable and worth 3d4x100 coins (1 weight)",
    13: "It's also unusually heavy but worth +2d4x100 more coins (+1 weight)",
    14: "Unique item worth at least 5d4x100 coins",
    15: "Everything needed to learn a new spell, and roll again",
    16: "A portal or secret path (or directions to one), and roll again",
    17: "Something relating to one of the characters, and roll again",
    18: "A hoard: 1d10x1000 coins (1 weight per 100), and 1d10x10 gems worth 2d6x100 each",
}

def roll_treasure(depth: int = 0, max_depth: int = 3) -> str:
    """Roll 1d6, +1d6 on 6 up to 3d6 total  Recurse on 'roll again'."""
    total = d(6)
    result = []
    # on 6, count the 6 but add another d6
    if total == 6:
        result.append(TREASURE[total])
        next_roll = d(6)
        total += next_roll
        # on another 6, count 12 but add another d6
        if next_roll == 6:
            result.append(TREASURE[total])
            total += d(6)

    # clamp to table range just in case
    total = max(1, min(18, total))
    result.append(TREASURE[total])
    for i in range(0, len(result)):
        if "and roll again" in result[i] and depth < max_depth:
            result[i] = result[i].replace(", and roll again", "")
            extra = roll_treasure(depth + 1, max_depth)
            result.append(extra)
    result_str = "\n".join(result)
    return f"{result_str}"

# ---------------------------------------------------------------------------
# Finding-treasure detail (utility / art item)
# ---------------------------------------------------------------------------

UTILITY = [
    "key/lockpick", "potion/food", "clothing/cloak", "decanter/vessel/cup",
    "cage/box/coffer", "instrument/tool", "book/scroll", "weapon/staff/wand",
    "armor/shield/helm", "mirror/hourglass", "pet/mount", "device/construct"
]

ART = [
    "trinket/charm", "painting/pottery", "ring/gloves", "carpet/tapestry",
    "statuette/idol", "flag/banner", "bracelet/armband", "necklace/amulet",
    "belt/harness", "hat/mask", "orb/sigil/rod", "crown/scepter"
]

def roll_item_detail() -> str:
    cat_roll = d(12)
    if cat_roll <= 8:
        category = "utility item"
        specific = UTILITY[d(12) - 1]
    else:
        category = "art item"
        specific = ART[d(12) - 1]
    return f"{category} → {specific} (1d12 category={cat_roll})"

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
        return f"Discovery → creature → Not an immediate threat, but it might become one: " + roll_creature()

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
        return f"Danger → creature →  immediate threat: " + roll_creature()

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

def roll_creature() -> str:
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
# Details (alphabetical prompt tables)
# ---------------------------------------------------------------------------

DETAILS = {
    "aberrance": [
        (1, 1, "multicephalous"),
        (2, 2, "profuse sensory organs"),
        (3, 4, "anatomical oddity"),
        (5, 5, "many limbs/digits"),
        (6, 6, "acephalous/decentralized"),
        (7, 7, "tentacles/feelers"),
        (8, 8, "gibbering/babbling"),
        (9, 9, "exudes chaos/blight"),
        (10, 10, "shapechanging"),
        (11, 12, "roll 1d10 twice"),
    ],
    "ability": [
        (1, 1, "bless/curse"),
        (2, 2, "entrap/paralyze"),
        (3, 3, "levitate/fly/teleport"),
        (4, 4, "telepathy/mind control"),
        (5, 5, "mimic/camouflage"),
        (6, 6, "seduce/hypnotize"),
        (7, 7, "dissolve/disintegrate"),
        (8, 8, "based on aspect"),
        (9, 9, "based on element"),
        (10, 10, "drain life/drain magic"),
        (11, 11, "magic type"),
        (12, 12, "roll 1d10+1 twice"),
    ],
    "activity": [
        (1, 1, "laying trap/ambush"),
        (2, 2, "fighting/at war"),
        (3, 3, "prowling/on patrol"),
        (4, 4, "hunting/foraging"),
        (5, 5, "eating/resting/camping"),
        (6, 6, "arguing/infighting"),
        (7, 7, "traveling/exploring"),
        (8, 8, "trading/negotiating"),
        (9, 9, "fleeing/running away"),
        (10, 10, "building/excavating"),
        (11, 11, "sleeping/unconscious"),
        (12, 12, "nursing injury/dying"),
    ],
    "adjective": [
        (1, 1, "slick/slimy"),
        (2, 2, "rough/hard/sharp"),
        (3, 3, "smooth/soft/dull"),
        (4, 4, "corroded/rusty"),
        (5, 5, "rotten/decaying"),
        (6, 6, "broken/brittle"),
        (7, 7, "stinking/smelly"),
        (8, 8, "weak/thin/drained"),
        (9, 9, "strong/fat/full"),
        (10, 10, "pale/poor/shallow"),
        (11, 11, "dark/rich/deep"),
        (12, 12, "colorful"),
    ],
    "age": [
        (1, 1, "unborn/nascent"),
        (2, 2, "being born/budding"),
        (3, 3, "newborn/blossoming"),
        (4, 6, "young/green"),
        (7, 9, "mature/ripe"),
        (10, 10, "old/going soft"),
        (11, 11, "dead/withered/ancient"),
        (12, 12, "dust/pre-historic"),
    ],
    "alignment": [
        (1, 2, "evil"),
        (3, 4, "chaotic"),
        (5, 8, "neutral"),
        (9, 10, "lawful"),
        (11, 12, "good"),
    ],
    "aspect": [
        (1, 1, "war/discord"),
        (2, 2, "hate/envy"),
        (3, 3, "power/strength"),
        (4, 4, "trickery/dexterity"),
        (5, 5, "time/constitution"),
        (6, 6, "lore/intelligence"),
        (7, 7, "nature/wisdom"),
        (8, 8, "culture/charisma"),
        (9, 9, "luck/fortune"),
        (10, 10, "love/admiration"),
        (11, 11, "peace/balance"),
        (12, 12, "glory/divinity"),
    ],
    "color": [
        (1, 1, "white/bright/pale"),
        (2, 2, "red/pink/maroon"),
        (3, 3, "orange/peach"),
        (4, 4, "yellow/mustard/ochre"),
        (5, 5, "green/chartreuse/sage"),
        (6, 6, "blue/aquamarine/indigo"),
        (7, 7, "violet/purple"),
        (8, 8, "gray/slate"),
        (9, 9, "brown/beige/tan"),
        (10, 10, "black/dark"),
        (11, 11, "metallic/prismatic"),
        (12, 12, "transparent/clear"),
    ],
    "condition": [
        (1, 1, "being built/born"),
        (2, 4, "intact/healthy"),
        (5, 7, "active/alert"),
        (8, 9, "weathered/tired/weak"),
        (10, 10, "vacant/lost"),
        (11, 11, "damaged/hurt/dying"),
        (12, 12, "broken/missing/dead"),
    ],
    "damage type": [
        (1, 2, "blunt/bludgeoning"),
        (3, 3, "edged/slashing"),
        (4, 5, "pointed/piercing"),
        (6, 6, "constricting/crushing"),
        (7, 7, "poison/toxic"),
        (8, 8, "acid/dissolving"),
        (9, 9, "choking/asphyxiating"),
        (10, 10, "element"),
        (11, 12, "roll 1d10 twice"),
    ],
    "design": [
        (1, 1, "blank/plain"),
        (2, 2, "floral/organic"),
        (3, 3, "circular/curvilinear"),
        (4, 4, "geometric/triangular"),
        (5, 5, "asymmetrical"),
        (6, 6, "square/rectilinear"),
        (7, 7, "meandering/labyrinthine"),
        (8, 8, "oceanic/wavelike"),
        (9, 9, "astrological/cosmic"),
        (10, 10, "balanced/harmonious"),
        (11, 11, "erratic/chaotic/random"),
        (12, 12, "roll 1d10+1 twice"),
    ],
    "disposition": [
        (1, 1, "attacking"),
        (2, 4, "hostile/aggressive"),
        (5, 6, "cautious/doubtful"),
        (7, 7, "fearful/fleeing"),
        (8, 10, "neutral"),
        (11, 11, "curious/hopeful"),
        (12, 12, "friendly"),
    ],
    "element": [
        (1, 1, "void"),
        (2, 2, "death/darkness"),
        (3, 4, "fire/metal/smoke"),
        (5, 6, "earth/stone/vegetation"),
        (7, 8, "water/ice/mist"),
        (9, 10, "air/wind/storm"),
        (11, 11, "life/light"),
        (12, 12, "stars/cosmos"),
    ],
    "magic type": [
        (1, 1, "necromancy"),
        (2, 3, "evocation/destruction"),
        (4, 4, "conjuration/summoning"),
        (5, 5, "illusion/glamour"),
        (6, 6, "enchantment/artifice"),
        (7, 7, "transformation"),
        (8, 8, "warding/binding"),
        (9, 10, "elemental"),
        (11, 11, "restoration/healing"),
        (12, 12, "divination/scrying"),
    ],
    "no. appearing": [
        (1, 2, "horde (4d6 per wave)"),
        (3, 8, "group (1d6+2)"),
        (9, 12, "solitary (1)"),
    ],
    "oddity": [
        (1, 1, "bright/garish/harsh"),
        (2, 2, "geometric/concentric"),
        (3, 3, "web/network"),
        (4, 4, "crystalline/glassy"),
        (5, 5, "fungal/slimy/moldy"),
        (6, 6, "gaseous/misty/illusory"),
        (7, 7, "volcanic/explosive"),
        (8, 8, "magnetic/repellant"),
        (9, 9, "multilevel/tiered"),
        (10, 10, "absurd/impossible"),
        (11, 12, "roll 1d10 twice"),
    ],
    "orientation": [
        (1, 2, "down/earthward"),
        (3, 3, "north"),
        (4, 4, "northeast"),
        (5, 5, "east"),
        (6, 6, "southeast"),
        (7, 7, "south"),
        (8, 8, "southwest"),
        (9, 9, "west"),
        (10, 10, "northwest"),
        (11, 12, "up/skyward"),
    ],
    "ruination": [
        (1, 1, "arcane disaster"),
        (2, 2, "damnation/curse"),
        (3, 4, "earthquake/fire/flood"),
        (5, 6, "plague/famine/drought"),
        (7, 8, "overrun by monsters"),
        (9, 10, "war/invasion"),
        (11, 11, "depleted resources"),
        (12, 12, "emigration"),
    ],
    "size": [
        (1, 1, "tiny"),
        (2, 3, "small"),
        (4, 9, "medium-sized"),
        (10, 11, "large"),
        (12, 12, "huge"),
    ],
    "tag": [
        (1, 1, "amorphous"),
        (2, 2, "cautious"),
        (3, 3, "construct"),
        (4, 4, "devious"),
        (5, 5, "intelligent"),
        (6, 6, "magical"),
        (7, 7, "organized"),
        (8, 8, "planar"),
        (9, 9, "stealthy"),
        (10, 10, "terrifying"),
        (11, 12, "roll 1d10 twice"),
    ],
    "terrain": [
        (1, 1, "sea/ocean"),
        (2, 2, "wasteland/desert"),
        (3, 5, "lowland/plains"),
        (6, 6, "wetland/swamp"),
        (7, 8, "woodland/jungle"),
        (9, 10, "highland/hills"),
        (11, 11, "mountains"),
        (12, 12, "roll 1d10+1, +oddity"),
    ],
    "visibility": [
        (1, 2, "buried/hidden/invisible"),
        (3, 6, "obscured/overgrown"),
        (7, 9, "obvious/in plain sight"),
        (10, 11, "visible at near distance"),
        (12, 12, "visible at far distance"),
    ],
}

def roll_details(specific: str = None) -> str:
    """Roll one random detail table (or a named one)."""
    if specific and specific in DETAILS:
        name = specific
    else:
        name = random.choice(list(DETAILS.keys()))
    table = DETAILS[name]
    result = pick_range(table, d(12))
    return f"Details → {name} → {result}"

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
    return f"{item} (grep from magic-items.md or search line in rulebook digest)"

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

TABLES = {
    "treasure":  ("Treasure Table", roll_treasure),
    "detail":    ("Treasure detail (utility/art)", roll_item_detail),
    "discovery": ("Discovery", roll_discovery),
    "danger":    ("Danger", roll_danger),
    "creature":  ("Creature", roll_creature),
    "details":   ("Random Details Prompt", roll_details),
    "equipment-tag": ("Equipment Tag", roll_equipment_tag),
    "gmmove":    ("GM Move", roll_gm_move),
    "drsl-miss": ("DR/Spout Lore Miss", roll_drsl_miss),
    "std-magicitem": ("Standard Magic Item", roll_std_magicitem),
}

HELP_LLM = """\
idea_gen.py - general-purpose RPG random-idea tables (treasure, discoveries,
dangers, creatures, equipment tags, GM moves, Discern Realities/Spout Lore
miss tricks, named magic items, misc detail prompts), useful any time a
random prompt would help creativity, independent of the other generators.
For a generic NPC appearance/personality/quirk trait, use npc_gen.py instead
(rolled there by default for every NPC - see its --no-traits/--full-traits).

USAGE
  idea_gen.py [TABLE ...] [-n N] [--seed N]

TABLE (zero or more; default: every table, one result each)
  treasure         Treasure Table (1-18 finding-treasure roll)
  detail           Treasure detail (a rolled item's utility/art description)
  discovery        Discovery prompt
  danger           Danger prompt
  creature         Creature prompt
  details          Random Details Prompt (generic scene-detail seed)
  equipment-tag     a random equipment tag (see references/tag-reference.md)
  gmmove            a GM move prompt (which move to make, not how to word it)
  drsl-miss         a Discern Realities / Spout Lore miss trick
  std-magicitem     a named item pulled from magic-items.md

-n N       how many of each requested table to roll at once (default 1).
           For "equipment-tag" this rolls N tags as one combined result
           rather than N separate single-tag results.
--seed N   reproducible output - dev/debug only, NEVER during play

OUTPUT
  For each requested table (in the order given), a "=== Title ===" header
  followed by -n result(s).
  Always ends with a reminder to update yaml files if anything changed.

Err on the side of using this script too much rather than not enough - even
when a result doesn't perfectly fit the situation, it injects entropy that
counteracts an LLM's tendency to repeat its own priors when improvising.

EXAMPLES
  idea_gen.py                        one result from every table
  idea_gen.py treasure                only treasure
  idea_gen.py danger creature details  all three of the listed tables
  idea_gen.py equipment-tag -n 2       roll 2 equipment tags at once
  idea_gen.py -n 3 gmmove               3 GM move prompts
  idea_gen.py drsl-miss
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
    parser.add_argument("-n", type=int, default=1,
                         help="how many of each to roll at once (default: 1)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed, for reproducibility")
    parser.add_argument("--help-llm", action="store_true", dest="help_llm",
                         help="print the dense full reference written for LLM callers, then exit")
    args = parser.parse_args()

    if args.seed is not None:
        print("Warning: Do not use --seed in a real game! If you did then re-read gameplay-loop.md now!")
        random.seed(args.seed)

    unknown = [t for t in args.tables if t not in TABLES]
    if unknown:
        print(f"Unknown table(s): {unknown}")
        print("Available:", ", ".join(TABLES))
        return

    for name in args.tables:
        title, fn = TABLES[name]
        print(f"=== {title} ===")
        if name == "equipment-tag":
            print(fn(args.n))
        else:
            for i in range(0, args.n):
                print(fn())
        print()

    print("Reminder: accepting the results isn't mandatory. Re-rolling is an option if results don't fit.")
    print("Reminder: update gm and character yaml files if anything changed since last update!")

if __name__ == "__main__":
    main()
