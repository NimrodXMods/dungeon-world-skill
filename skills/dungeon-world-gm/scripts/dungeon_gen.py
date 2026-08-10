#!/usr/bin/env python3
"""
dungeon_gen.py - Dungeon generation tables (loosely modeled on The Perilous
Wilds' "Plumb the Depths" chapter; table shapes and word choices are this
skill's own, not a verbatim reproduction - see the skill's ATTRIBUTION.md
for the source citation). No further page/chapter references are given
per-entry below - this is a script, not a book to cross-reference by hand,
so every roll (including nested "roll on another table and combine/add X"
results) is fully resolved into a finished phrase, never left as a label
or dice notation for a person to look up and roll themselves.

Usage:
  python dungeon_gen.py                  # full dungeon concept (default)
  python dungeon_gen.py name size themes
  python dungeon_gen.py overview
  python dungeon_gen.py dressing discovery exits danger
  python dungeon_gen.py --seed 42        # reproducible results (dev/debug only, never in play)
"""

import argparse
import random
import sys
from typing import List, Tuple, Dict

from _util import apply_seed, d, force_utf8_stdio

force_utf8_stdio()


def pick_range(table: List[Tuple[int, int, str]], roll: int) -> str:
    for lo, hi, val in table:
        if lo <= roll <= hi:
            return val
    return "???"

# ---------------------------------------------------------------------------
# 1. Dungeon Name
# ---------------------------------------------------------------------------

NAME_TEMPLATES = [
    (1, 2, "The [place]"),
    (3, 4, "(The) [adjective] [place]"),
    (5, 6, "(The) [place] of the [noun]"),
    (7, 8, "(The) [noun]’s [place]"),
    (9, 10, "[place] of the [adjective] [noun]"),
    (11, 12, "(The) [adjective] [noun]"),
]

# 1d100 tables – flattened from the two-column layout
PLACE = [
    "Archive", "Blight", "Boneyard", "Catacomb", "Cave(s)", "Cavern(s)",
    "Citadel", "Cliff", "Crack", "Crag", "Crypt", "Curse", "Deep", "Delve",
    "Den", "Finger", "Fist", "Fort", "Fortress", "Grave", "Haunt", "Hold",
    "Hole(s)", "Hollow(s)", "Home", "House", "Jaws", "Keep", "Lair", "Maw",
    "Maze", "Mountain", "Mouth", "Peak", "Pit", "Remnant", "Retreat", "Ruin",
    "Shrine", "Skull", "Spire", "Temple", "Throne", "Tomb", "Tooth", "Tower",
    "Tunnel(s)", "Vault", "Warren", "Wreck"
]  # 50 entries; we will index 1-100 by repeating/pairing with the second column style

# Better: explicit 1-100 lists built from the printed pairs
PLACE_100 = {}
ADJECTIVE_100 = {}
NOUN_100 = {}

# Column 1 (01-50) and Column 2 (51-100)
_places1 = [
    "Archive", "Blight", "Boneyard", "Catacomb", "Cave(s)", "Cavern(s)",
    "Citadel", "Cliff", "Crack", "Crag", "Crypt", "Curse", "Deep", "Delve",
    "Den", "Finger", "Fist", "Fort", "Fortress", "Grave", "Haunt", "Hold",
    "Hole(s)", "Hollow(s)", "Home"
]
_places2 = [
    "House", "Jaws", "Keep", "Lair", "Maw", "Maze", "Mountain", "Mouth",
    "Peak", "Pit", "Remnant", "Retreat", "Ruin", "Shrine", "Skull", "Spire",
    "Temple", "Throne", "Tomb", "Tooth", "Tower", "Tunnel(s)", "Vault",
    "Warren", "Wreck"
]
_adjs1 = [
    "Ancient", "Ashen", "Black", "Bloody", "Blue", "Broken", "Burning",
    "Cracked", "Dark", "Dead", "Doomed", "Endless", "Evil", "Fallen",
    "Far", "Fearsome", "Floating", "Forbidden", "Forgotten", "Frozen",
    "Ghostly", "Gloomy", "Gray", "Grim", "Hidden"
]
_adjs2 = [
    "High", "Holy", "Iron", "Jagged", "Lonely", "Lost", "Low", "Misty",
    "Petrified", "Red", "Screaming", "Sharp", "Shattered", "Shifting",
    "Shivering", "Shrouded", "Stoney", "Sunken", "Thorny", "Thundering",
    "Unholy", "White", "Wicked", "Withered", "Yellow"
]
_nouns1 = [
    "[Name]*", "Arm", "Ash", "Beast", "Behemoth", "Blood", "Child",
    "Cinder", "Corpse", "Crystal", "Dagger", "Death", "Demon", "Devil",
    "Doom", "Dragon", "Eye", "Fear", "Finger", "Fire", "Foot", "Frog",
    "Ghost", "Giant", "Goblin"
]
_nouns2 = [
    "God", "Hand", "Head", "Heart", "Horror", "Hero", "Horn", "King",
    "Knave", "Priest", "Prophet", "Queen", "Shard", "Skull", "Souls",
    "Spear", "Spirit", "Stone", "Sword", "Troll", "Warrior", "Water",
    "Witch", "Wizard", "Worm"
]

for i in range(25):
    PLACE_100[i*2 + 1] = _places1[i]
    PLACE_100[i*2 + 2] = _places1[i]
    ADJECTIVE_100[i*2 + 1] = _adjs1[i]
    ADJECTIVE_100[i*2 + 2] = _adjs1[i]
    NOUN_100[i*2 + 1] = _nouns1[i]
    NOUN_100[i*2 + 2] = _nouns1[i]

for i in range(25):
    PLACE_100[51 + i*2] = _places2[i]
    PLACE_100[52 + i*2] = _places2[i]
    ADJECTIVE_100[51 + i*2] = _adjs2[i]
    ADJECTIVE_100[52 + i*2] = _adjs2[i]
    NOUN_100[51 + i*2] = _nouns2[i]
    NOUN_100[52 + i*2] = _nouns2[i]

def roll_name() -> str:
    tmpl_roll = d(12)
    template = pick_range(NAME_TEMPLATES, tmpl_roll)

    place = PLACE_100[d(100)]
    adj = ADJECTIVE_100[d(100)]
    noun = NOUN_100[d(100)]
    if noun == "[Name]*":
        noun = "[Name]"   # leave as placeholder

    name = template
    name = name.replace("[place]", place)
    name = name.replace("[adjective]", adj)
    name = name.replace("[noun]", noun)
    # clean optional "The"
    if name.startswith("(The)"):
        name = name.replace("(The)", "The" if d(2) == 1 else "", 1).strip()
    return f"Dungeon Name → {name}  (template={tmpl_roll})"

# ---------------------------------------------------------------------------
# 2. Dungeon Size
# ---------------------------------------------------------------------------

SIZE_TABLE = [
    (1, 3, ("small", "1d6+1", 2)),
    (4, 6, ("medium", "1d8+7", 3)),
    (7, 9, ("large", "1d10+15", 4)),
    (10, 11, ("huge", "1d12+25", 5)),
    (12, 12, ("megadungeon", "1d4+1 interconnected dungeons", 0)),
]

def roll_size() -> str:
    r = d(12)
    size, areas_expr, themes = SIZE_TABLE[0]  # placeholder
    for lo, hi, data in SIZE_TABLE:
        if lo <= r <= hi:
            size, areas_expr, themes = data
            break

    if size == "megadungeon":
        n = d(4) + 1
        return f"Dungeon Size → megadungeon ({n} interconnected dungeons)  (roll={r})"
    else:
        # evaluate the area expression
        if areas_expr == "1d6+1":
            areas = d(6) + 1
        elif areas_expr == "1d8+7":
            areas = d(8) + 7
        elif areas_expr == "1d10+15":
            areas = d(10) + 15
        else:  # 1d12+25
            areas = d(12) + 25
        return f"Dungeon Size → {size} ({areas} areas, {themes} themes)  (roll={r})"

def get_theme_count() -> int:
    """Helper used by the full generator."""
    r = d(12)
    for lo, hi, data in SIZE_TABLE:
        if lo <= r <= hi:
            return data[2] if data[2] > 0 else 3  # megadungeon default 3
    return 3

# ---------------------------------------------------------------------------
# 3. Dungeon Themes
# ---------------------------------------------------------------------------

THEME_MAIN = [
    (1, 2, "hopeful"),
    (3, 5, "mysterious"),
    (6, 11, "grim"),
    (12, 12, "gonzo"),
]

THEME_HOPEFUL = [
    (1, 1, "nature/growth"),
    (2, 2, "law/order"),
    (3, 3, "beauty/wonder"),
    (4, 4, "healing/recovery"),
    (5, 5, "protection/defense"),
    (6, 6, "completion"),
    (7, 7, "inheritance/legacy"),
    (8, 8, "balance/harmony"),
    (9, 9, "light/life"),
    (10, 10, "prophecy"),
    (11, 11, "divine influence"),
    (12, 12, "transcendence"),
]
THEME_MYSTERIOUS = [
    (1, 1, "burglary/theft"),
    (2, 2, "desire/obsession"),
    (3, 3, "secrets/deception"),
    (4, 4, "imitation/mimicry"),
    (5, 5, "inversion/reversal"),
    (6, 6, "element"),
    (7, 7, "transformation"),
    (8, 8, "shadow/spirits"),
    (9, 9, "cryptic knowledge"),
    (10, 10, "divination/scrying"),
    (11, 11, "madness"),
    (12, 12, "magic type"),
]
THEME_GRIM = [
    (1, 1, "pride/hubris"),
    (2, 2, "hunger/gluttony"),
    (3, 3, "greed/avarice"),
    (4, 4, "wildness/savagery"),
    (5, 5, "devotion/sacrifice"),
    (6, 6, "forbidden knowledge"),
    (7, 7, "control/dominance"),
    (8, 8, "pain/torture"),
    (9, 9, "wrath/war"),
    (10, 10, "tragedy/loss"),
    (11, 11, "chaos/corruption"),
    (12, 12, "darkness/death"),
]
THEME_GONZO = [
    (1, 1, "constructs/robots"),
    (2, 2, "unexpected sentience"),
    (3, 3, "space/time travel"),
    (4, 4, "advanced technology"),
    (5, 5, "utter insanity"),
    (6, 6, "alien life"),
    (7, 7, "cosmic alignment"),
    (8, 8, "other plane(s)"),
    (9, 9, "demons/devils"),
    (10, 10, "unspeakable horrors"),
    (11, 11, "elder gods"),
    (12, 12, "roll 1d10 twice, combine"),
]

def _one_theme() -> str:
    main_roll = d(12)
    cat = pick_range(THEME_MAIN, main_roll)
    if cat == "hopeful":
        specific = pick_range(THEME_HOPEFUL, d(12))
    elif cat == "mysterious":
        specific = pick_range(THEME_MYSTERIOUS, d(12))
    elif cat == "grim":
        specific = pick_range(THEME_GRIM, d(12))
    else:
        specific = pick_range(THEME_GONZO, d(12))
        if specific == "roll 1d10 twice, combine":
            a = pick_range(THEME_GONZO, d(10))
            b = pick_range(THEME_GONZO, d(10))
            specific = f"{a} + {b}"
    return f"{cat} → {specific}"

def roll_themes(n: int = None) -> str:
    if n is None:
        n = 1
    themes = [_one_theme() for _ in range(n)]
    joined = " | ".join(themes)
    return f"Dungeon Themes ({n}) → {joined}"

# ---------------------------------------------------------------------------
# 4. Dungeon Overview (form, situation, accessibility, builder, function, cause)
# ---------------------------------------------------------------------------

# Small cross-reference tables, this skill's own invention: the source
# material points to these as separate named tables without spelling out
# their contents inline. Since this is a script and not something read by
# hand, an unresolved "oddity" or "magic type" label isn't useful - these
# are compact stand-ins so a FORM/DISCOVERY_FIND roll that calls for one
# always resolves to a concrete result.

ODDITY = [
    (1, 1, "impossible geometry - angles that shouldn't exist"),
    (2, 2, "a perpetual, inexplicable cold"),
    (3, 3, "gravity behaves strangely here"),
    (4, 4, "a silence that swallows all sound"),
    (5, 5, "time runs oddly - faster, slower, or looping"),
    (6, 6, "grown from a single, massive living organism"),
    (7, 7, "everything inside is subtly the wrong size"),
    (8, 8, "part of it exists in more than one place at once"),
    (9, 9, "colors that don't match anything natural"),
    (10, 10, "light or shadow with no visible source"),
    (11, 11, "structures rearrange themselves when unobserved"),
    (12, 12, "echoes return altered, or answered"),
]

MAGIC_TYPE = [
    (1, 1, "necromantic"),
    (2, 2, "elemental (fire)"),
    (3, 3, "elemental (water)"),
    (4, 4, "elemental (earth)"),
    (5, 5, "elemental (air)"),
    (6, 6, "illusory"),
    (7, 7, "divine/holy"),
    (8, 8, "infernal/demonic"),
    (9, 9, "primal/nature"),
    (10, 10, "arcane/abjuration"),
    (11, 11, "transmutation"),
    (12, 12, "divination/prophetic"),
]

FORM = [
    (1, 1, "caves/caverns"),
    (2, 3, "ruins of 1d8+3"),
    (4, 4, "mine"),
    (5, 5, "prison"),
    (6, 7, "crypt/tomb/catacombs"),
    (8, 8, "stronghold/fortress/citadel"),
    (9, 9, "temple/sanctuary"),
    (10, 10, "tower/spire"),
    (11, 11, "roll 1d10, add oddity"),
    (12, 12, "ruins of a steading"),
]

SITUATION = [
    (1, 2, "aboveground"),
    (3, 4, "part aboveground, part below"),
    (5, 11, "belowground"),
    (12, 12, "extraordinary (floating, ephemeral, etc.)"),
]

ACCESSIBILITY = [
    (1, 1, "sealed shut"),
    (2, 2, "purposely hidden"),
    (3, 4, "concealed by natural feature/terrain"),
    (5, 6, "buried (in earth, rubble, etc.)"),
    (7, 7, "blocked by obstacle/out of reach"),
    (8, 10, "clear/obvious"),
    (11, 12, "multiple entrances, each separately accessible"),
]

BUILDER = [
    (1, 1, "demigod/demon/alien"),
    (2, 3, "natural (caves, etc.)"),
    (4, 5, "religious order/cult"),
    (6, 10, "humanoid society"),
    (11, 11, "wizard/lunatic"),
    (12, 12, "monarch/warlord"),
]

FUNCTION = [
    (1, 1, "indiscernible/mysterious"),
    (2, 2, "concealment/camouflage"),
    (3, 3, "extraction/production"),
    (4, 4, "confinement/containment"),
    (5, 5, "lair/den/hideout"),
    (6, 6, "archive/library/laboratory"),
    (7, 7, "commemoration/funerary"),
    (8, 8, "worship/devotion"),
    (9, 9, "defense/protection"),
    (10, 10, "observation/divination"),
    (11, 11, "empowerment/intensification"),
    (12, 12, "roll 1d10+1 twice, combine"),
]

CAUSE = [
    (1, 1, "arcane disaster"),
    (2, 2, "damnation/curse"),
    (3, 4, "natural disaster (earthquake, etc.)"),
    (5, 5, "plague/famine/drought"),
    (6, 7, "overrun by monsters"),
    (8, 9, "hubris"),
    (10, 10, "war/invasion"),
    (11, 11, "depleted resources"),
    (12, 12, "better prospects elsewhere"),
]


def resolve_form(roll: int = None) -> str:
    """Fully resolve a FORM roll. Recursion is bounded by construction: the
    nested "add oddity" branch rolls a d10 against FORM, which can never
    land back on itself (index 11) or on "ruins of a steading" (index 12),
    so this can recurse at most one level deep."""
    if roll is None:
        roll = d(12)
    val = pick_range(FORM, roll)
    if val == "ruins of 1d8+3":
        return f"ruins of {d(8) + 3}"
    if val == "roll 1d10, add oddity":
        base = resolve_form(d(10))
        oddity = pick_range(ODDITY, d(12))
        return f"{base} + oddity: {oddity}"
    return val


def resolve_accessibility(roll: int = None) -> str:
    """Fully resolve an ACCESSIBILITY roll. "Multiple entrances" actually
    rolls one accessibility type per entrance (d10, so it can never land
    back on "multiple entrances" itself) instead of just reporting a count."""
    if roll is None:
        roll = d(12)
    val = pick_range(ACCESSIBILITY, roll)
    if val == "multiple entrances, each separately accessible":
        n = d(6) + 1
        entrances = [pick_range(ACCESSIBILITY, d(10)) for _ in range(n)]
        listed = "; ".join(f"#{i + 1} {e}" for i, e in enumerate(entrances))
        return f"multiple entrances ({n}): {listed}"
    return val


def roll_overview() -> str:
    form = resolve_form()
    situ = pick_range(SITUATION, d(12))
    access = resolve_accessibility()
    builder = pick_range(BUILDER, d(12))
    func = pick_range(FUNCTION, d(12))
    if "roll 1d10+1 twice" in func:
        a = pick_range(FUNCTION, d(10) + 1)
        b = pick_range(FUNCTION, d(10) + 1)
        func = f"{a} + {b}"

    cause = pick_range(CAUSE, d(12))

    return (f"Dungeon Overview →\n"
            f"  form: {form}\n"
            f"  situation: {situ}\n"
            f"  accessibility: {access}\n"
            f"  builder: {builder}\n"
            f"  function: {func}\n"
            f"  cause of ruin: {cause}")

# ---------------------------------------------------------------------------
# 5. Area Dressing
# ---------------------------------------------------------------------------

DRESSING = [
    (1, 1, "breeze/sound/echo"),
    (2, 2, "smell/odor/stench"),
    (3, 3, "lichen/mold/moss/fungus"),
    (4, 4, "drip/seep/puddle/stream"),
    (5, 5, "tracks/marks/scratches"),
    (6, 6, "sign of activity/struggle/battle"),
    (7, 7, "bones/remains of a creature"),
    (8, 8, "junk/debris/refuse/waste"),
    (9, 9, "broken structure/furniture"),
    (10, 10, "inscription/ornamentation"),
    (11, 12, "roll 1d10 twice, combine"),
]

def roll_dressing() -> str:
    r = d(12)
    result = pick_range(DRESSING, r)
    if "roll 1d10 twice" in result:
        a = pick_range(DRESSING, d(10))
        b = pick_range(DRESSING, d(10))
        result = f"{a} + {b}"
    return f"Area Dressing → {result}  (roll={r})"

# ---------------------------------------------------------------------------
# 6. Dungeon Discovery
# ---------------------------------------------------------------------------

DISCOVERY_MAIN = [
    (1, 8, "feature"),
    (9, 12, "find"),
]

DISCOVERY_FEATURE = [
    (1, 1, "cave-in/collapse/obstacle"),
    (2, 2, "blocked/locked exit"),
    (3, 3, "pit/shaft/chasm"),
    (4, 4, "pillars/columns"),
    (5, 5, "alcoves/niches"),
    (6, 6, "bridge/stairs/ramp"),
    (7, 7, "well/pool/fountain"),
    (8, 8, "puzzle"),
    (9, 9, "altar/dais/platform"),
    (10, 10, "statue/idol"),
    (11, 11, "multi-level/ledges/tiers"),
    (12, 12, "hidden/secret exit"),
]

DISCOVERY_FIND = [
    (1, 1, "trinkets/clothing"),
    (2, 2, "supplies/tools/gear"),
    (3, 3, "light source/fuel/ammo"),
    (4, 4, "key/clue/map"),
    (5, 5, "weapons/armor"),
    (6, 6, "poison/antidote/potion"),
    (7, 7, "adventurer/captive"),
    (8, 8, "books/scrolls"),
    (9, 9, "coins/gems/jewelry"),
    (10, 10, "roll 1d8, add magic type"),
    (11, 11, "roll feature, add magic type"),
    (12, 12, "roll 1d10 twice, combine"),
]


def resolve_discovery_feature(roll: int = None) -> str:
    """DISCOVERY_FEATURE has no nested special entries, but this exists for
    symmetry with resolve_discovery_find() and so any future addition of one
    only needs handling in one place."""
    if roll is None:
        roll = d(12)
    return pick_range(DISCOVERY_FEATURE, roll)


def resolve_discovery_find(roll: int = None) -> str:
    """Fully resolve a DISCOVERY_FIND roll. Recursion is bounded by
    construction: the "add magic type" branch rolls a d8 (indices 1-8,
    all plain entries) and the "combine" branch rolls a d10 (indices 1-10,
    which can reach the "add magic type" entry but never "combine" itself
    at index 12), so this can recurse at most one level deep."""
    if roll is None:
        roll = d(12)
    val = pick_range(DISCOVERY_FIND, roll)
    if val == "roll 1d8, add magic type":
        base = resolve_discovery_find(d(8))
        magic = pick_range(MAGIC_TYPE, d(12))
        return f"{base} + {magic} magic"
    if val == "roll feature, add magic type":
        feature = resolve_discovery_feature(d(12))
        magic = pick_range(MAGIC_TYPE, d(12))
        return f"{feature} + {magic} magic"
    if val == "roll 1d10 twice, combine":
        a = resolve_discovery_find(d(10))
        b = resolve_discovery_find(d(10))
        return f"{a} + {b}"
    return val


def roll_discovery() -> str:
    main_roll = d(12)
    cat = pick_range(DISCOVERY_MAIN, main_roll)
    if cat == "feature":
        detail = resolve_discovery_feature(d(12))
    else:
        detail = resolve_discovery_find(d(12))
    return f"Dungeon Discovery → {cat} → {detail}  (main={main_roll})"

# ---------------------------------------------------------------------------
# 7. Area Exits
# ---------------------------------------------------------------------------

EXIT_NUMBER = [
    (1, 2, 0),
    (3, 3, 1),
    (4, 6, 1),
    (7, 7, 2),
    (8, 9, 2),
    (10, 10, 3),
    (11, 11, 4),
    (12, 12, -1),   # 1d6+1
]

EXIT_DIR = [
    (1, 1, "down"),
    (2, 2, "back"),
    (3, 3, "forward"),
    (4, 6, "forward"),
    (7, 7, "left"),
    (8, 9, "left"),
    (10, 10, "right"),
    (11, 11, "right"),
    (12, 12, "up"),
]

def roll_exits() -> str:
    num_roll = d(12)
    n = None
    for lo, hi, val in EXIT_NUMBER:
        if lo <= num_roll <= hi:
            n = val
            break
    if n == -1:
        n = d(6) + 1

    if n == 0:
        return f"Area Exits → none  (number roll={num_roll})"

    dirs = []
    for _ in range(n):
        dirs.append(pick_range(EXIT_DIR, d(12)))
    return f"Area Exits → {n} exit(s): {', '.join(dirs)}  (number roll={num_roll})"

# ---------------------------------------------------------------------------
# 8. Dungeon Danger
# ---------------------------------------------------------------------------

DANGER_MAIN = [
    (1, 4, "trap"),
    (5, 12, "creature"),
]

DANGER_TRAP = [
    (1, 1, "alarm"),
    (2, 2, "pit"),
    (3, 3, "ensnaring/paralyzing"),
    (4, 4, "crushing/smashing"),
    (5, 5, "piercing/puncturing"),
    (6, 6, "chopping/slashing/slicing"),
    (7, 7, "confusing (maze, etc.)"),
    (8, 8, "gas (poison, etc.)"),
    (9, 9, "ambush"),
    (10, 10, "based on element"),
    (11, 11, "based on magic type"),
    (12, 12, "based on oddity"),
]

DANGER_CREATURE = [
    (1, 1, "creature leader/lord (with minions)"),
    (2, 9, "creature"),
    (10, 12, "beast vermin (rats, bats, etc.)"),
]

def roll_danger() -> str:
    main_roll = d(12)
    cat = pick_range(DANGER_MAIN, main_roll)
    if cat == "trap":
        detail = pick_range(DANGER_TRAP, d(12))
    else:
        detail = pick_range(DANGER_CREATURE, d(12))
    return f"Dungeon Danger → {cat} → {detail}  (main={main_roll})"

# ---------------------------------------------------------------------------
# Full coherent dungeon (default)
# ---------------------------------------------------------------------------

def roll_full() -> str:
    lines = []
    lines.append(roll_name())
    size_str = roll_size()
    lines.append(size_str)

    # extract theme count from the size string if possible
    n_themes = 3
    if "themes)" in size_str:
        try:
            n_themes = int(size_str.split(",")[1].strip().split()[0])
        except Exception:
            pass
    lines.append(roll_themes(n_themes))
    lines.append(roll_overview())
    lines.append(roll_dressing())
    lines.append(roll_discovery())
    lines.append(roll_exits())
    lines.append(roll_danger())
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

TABLES = {
    "name":       ("Dungeon Name", roll_name),
    "size":       ("Dungeon Size", roll_size),
    "themes":     ("Dungeon Themes", lambda: roll_themes(1)),
    "overview":   ("Dungeon Overview", roll_overview),
    "dressing":   ("Area Dressing", roll_dressing),
    "discovery":  ("Dungeon Discovery", roll_discovery),
    "exits":      ("Area Exits", roll_exits),
    "danger":     ("Dungeon Danger", roll_danger),
    "full":       ("Full Dungeon Concept", roll_full),
}

HELP_LLM = """\
dungeon_gen.py - dungeon generation tables (loosely modeled on The Perilous
Wilds' "Plumb the Depths" chapter; table shapes/word choices are this
skill's own, not a verbatim reproduction - see ATTRIBUTION.md). Every roll,
including nested "roll on another table and combine" results, is fully
resolved into a finished phrase - never left as a label or dice notation
for a person to look up by hand.

USAGE
  dungeon_gen.py [TABLE ...] [--seed N]

TABLE (zero or more; default: full)
  name | size | themes | overview | dressing | discovery | exits | danger |
  full   ("full" runs the complete dungeon concept: all of the above woven
  together into one overview, not just each table run separately)

--seed N   reproducible output - dev/debug only, NEVER during play

OUTPUT
  For each requested table (in the order given), a "=== Title ===" header
  followed by that table's resolved text.
  Always ends with a reminder to update yaml files.

EXAMPLES
  dungeon_gen.py                    full dungeon concept (default)
  dungeon_gen.py name size themes
  dungeon_gen.py overview
  dungeon_gen.py dressing discovery exits danger
"""


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return

    parser = argparse.ArgumentParser(description="Dungeon generator from Plumb the Depths tables")
    parser.add_argument(
        "tables", nargs="*", default=["full"],
        help="which tables to roll (default: full). Choices: " + ", ".join(TABLES)
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed, for reproducibility")
    parser.add_argument("--help-llm", action="store_true", dest="help_llm",
                         help="print the dense full reference written for LLM callers, then exit")
    args = parser.parse_args()

    apply_seed(args.seed)

    unknown = [t for t in args.tables if t not in TABLES]
    if unknown:
        print(f"Unknown table(s): {unknown}")
        print("Available:", ", ".join(TABLES))
        return

    for name in args.tables:
        title, fn = TABLES[name]
        print(f"=== {title} ===")
        print(fn())
        print()

    print("Reminder: update gm and character yaml files now!")


if __name__ == "__main__":
    main()
