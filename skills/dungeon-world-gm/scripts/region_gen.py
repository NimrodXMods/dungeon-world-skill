#!/usr/bin/env python3
"""
Region/area/site name generator for Dungeon World (Perilous Wilds map-drawing
and dungeon-creation procedures).

Usage:
    python3 region_gen.py                        # default: a region + 3-7 areas
                                                    # (each area has a 30% chance of
                                                    # also getting a site)
    python3 region_gen.py --nareas 5               # a region + exactly 5 areas
    python3 region_gen.py --site-chance 0          # ...with no sites attached
    python3 region_gen.py --site-chance 1          # ...every area gets a site
    python3 region_gen.py --dungeon-chance 100     # ...every site is a dungeon, never a place
    python3 region_gen.py --dungeon-chance 0       # ...every site is a place, never a dungeon
    python3 region_gen.py --terrain-match 1        # ...every area shares its region's terrain
    python3 region_gen.py --terrain-match 0        # ...every area rolls independent terrain
    python3 region_gen.py -n 3                     # three region+areas sets
    python3 region_gen.py --tier region             # just a single region name
    python3 region_gen.py --tier area                # just a single area name
    python3 region_gen.py --tier site                 # just a single site name (50/50
                                                        # place/dungeon by default, or
                                                        # --dungeon-chance to weight it)
    python3 region_gen.py --tier site --site-kind dungeon  # force a dungeon-style site
    python3 region_gen.py --tier site --site-kind place    # force a place-style site
    python3 region_gen.py --seed 7                # reproducible
    python3 region_gen.py --name-ancestry elf      # ancestry to use if the rare
                                                    # "[Name]" noun slot is rolled

Definitions (this skill's own, not from the source material):
    Region - a large swath of land or sea, defined by its prevailing terrain
    type (dark forest, desert, frozen highland) or a political boundary
    (kingdom, barony, tribal lands). The first region on a map must contain
    the party's starting position.
    Area - a sub-region: terrain- or politically-defined, but contained
    within an existing region (a barren zone within wooded hills, islands
    within a sea, a lesser lord's fiefdom within a barony). Reuses the
    region tables themselves (not a separate word bank) - the only
    difference is that an area's name usually (70% of the time by default,
    see --terrain-match) omits the terrain word, since it's already
    implied by the parent region.
    Site - a single notable location within an area: typically a ruin or
    dungeon, though the GM can decide to treat one as a proper steading
    instead if that fits better (this script never does that
    automatically - it's a judgment call left entirely to the GM; run
    steading_gen.py by hand if a site turns out to warrant one). A site is
    randomly either a "place" (Perilous Wilds p21's place-name table) or a
    "dungeon" (p64's dungeon-name table, "Plumb the Depths" chapter) - see
    --dungeon-chance / --site-kind. What a non-dungeon "place" site
    actually is (a shrine, a fort, a grove, etc.) is left to the GM to
    decide from its name and surroundings; this script doesn't try to
    disambiguate further.

Default behavior generates a region together with its areas, using this
skill's own terrain-inheritance rule (not from the source material): an
area shares its parent region's terrain 70% of the time by default (in
which case its name omits the terrain word entirely - a fresh
region-style template is still rolled at random for shape variety, just
with the terrain slot dropped), or rolls its own independent region-style
name (own terrain and all) the other 30% of the time - see
gen_area_name() and --terrain-match (0.0-1.0) to configure this chance.
Each area
additionally has a 30% chance (--site-chance) of also getting a site,
itself 50/50 place-vs-dungeon by default (--dungeon-chance, 0-100, percent
chance of dungeon - 100 always dungeon, 0 always place). --tier
region/area/site bypass all of this and generate a single bare name from
just that tier's own table(s).

Data source: the region-name-template and word tables (Perilous Wilds
Revised Edition, p20, "Draw the Map" chapter) for the region tier (also
reused, with terrain sometimes omitted, for the area tier); the
place-name-template and word tables (p21) for site/"place"; and the
dungeon-name-template and word tables (p64, "Plumb the Depths" chapter)
for site/"dungeon" - CC BY-SA 3.0, Jason Lutes. Transcribed faithfully,
not reorganized: these are the book's actual templates and word banks,
not this script's own invention (contrast with steading_gen.py's mad-lib
name generator, which fills in a structure the book leaves blank). The
book marks some template words as optional - "(The)" at the start, "(the)"
before a noun - and other occurrences of "The"/"the" as mandatory (no
parens); this script always includes the mandatory ones, and for the
optional ones flips a coin each time rather than always including or
always omitting them, so output varies between e.g. "Ashen Bluffs" and
"The Ashen Bluffs" from the same template. (The p64 table's PDF extraction
renders two of its "(The)" markers as "[The)" - a known font/bracket
glitch in that particular PDF, not a deliberate different notation;
normalized to "(The)"/optional here for consistency with every other
instance in the book.)

All three word-bank tiers' noun tables have a first entry of "[Name]*",
with the book's own footnote: "Choose a name appropriate to your setting;
or, if you have a name list, roll one up." This script rolls one up -
from npc_gen.py's name lists, via --name-ancestry (default: any).
"""
import argparse
import random
import sys

from _util import apply_seed, force_utf8_stdio

force_utf8_stdio()

import npc_gen  # sibling script - reused for the "[Name]" slot


def _maybe_the(cap=True):
    """A book-optional '(The)'/'(the)' - included about half the time."""
    if random.random() < 0.5:
        return "The " if cap else "the "
    return ""


# --- Region name template (1d12) --------------------------------------------
# Perilous Wilds p20. Also reused for the area tier (see gen_area_name()) -
# an area is the same table with terrain usually omitted, not a separate
# word bank.

REGION_TEMPLATES = [
    (1, 4, "adj_terrain"),               # (The) [adjective] [terrain]
    (5, 7, "terrain_of_noun"),           # [terrain] of (the) [noun]
    (8, 8, "terrain_adj"),               # The [terrain] [adjective]
    (9, 10, "noun_terrain"),             # (The) [noun] [terrain]
    (11, 11, "noun_poss_adj_terrain"),   # (The) [noun]'s [adjective] [terrain]
    (12, 12, "adj_terrain_of_noun"),     # [adjective] [terrain] of (the) [noun]
]

# --- Region word tables (1d100 each, independently rolled) ------------------

REGION_TERRAINS = [
    "Bay", "Bluffs", "Bog", "Cliffs", "Desert", "Downs", "Dunes", "Expanse",
    "Fells", "Fen", "Flats", "Foothills", "Forest", "Groves", "Heath",
    "Heights", "Hills", "Hollows", "Jungle", "Lake", "Lowland", "March",
    "Marsh", "Meadows", "Moor", "Morass", "Mounds", "Mountains", "Peaks",
    "Plains", "Prairie", "Quagmire", "Range", "Reach", "Sands", "Savanna",
    "Scarps", "Sea", "Slough", "Sound", "Steppe", "Swamp", "Sweep", "Teeth",
    "Thicket", "Upland", "Wall", "Waste", "Wasteland", "Woods",
]

REGION_ADJECTIVES = [
    "Ageless", "Ashen", "Black", "Blessed", "Blighted", "Blue", "Broken",
    "Burning", "Cold", "Cursed", "Dark", "Dead", "Deadly", "Deep",
    "Desolate", "Diamond", "Dim", "Dismal", "Dun", "Eerie", "Endless",
    "Fallen", "Far", "Fell", "Flaming", "Forgotten", "Forsaken", "Frozen",
    "Glittering", "Golden", "Green", "Grim", "Holy", "Impassable",
    "Jagged", "Light", "Long", "Misty", "Perilous", "Purple", "Red",
    "Savage", "Shadowy", "Shattered", "Shifting", "Shining", "Silver",
    "White", "Wicked", "Yellow",
]

# First entry is the book's special "[Name]*" slot - see gen_region_name().
REGION_NOUNS = [
    "[Name]", "Ash", "Bone", "Darkness", "Dead", "Death", "Desolation",
    "Despair", "Devil", "Doom", "Dragon", "Fate", "Fear", "Fire", "Fury",
    "Ghost", "Giant", "God", "Gold", "Heaven", "Hell", "Honor", "Hope",
    "Horror", "King", "Life", "Light", "Lord", "Mist", "Peril", "Queen",
    "Rain", "Refuge", "Regret", "Savior", "Shadow", "Silver", "Skull",
    "Sky", "Smoke", "Snake", "Sorrow", "Storm", "Sun", "Thorn", "Thunder",
    "Traitor", "Troll", "Victory", "Witch",
]

# --- Place name template (1d12) - one of the two "site" sub-tables ---------
# Perilous Wilds p21's "place name" table (Step 3 of "Draw the Map": Add
# Places). Used here for the "place" half of site generation, not for
# areas (areas reuse the region tables instead - see above).

PLACE_TEMPLATES = [
    (1, 2, "the_place"),                 # The [place]
    (3, 4, "adj_place"),                 # The [adjective] [place]
    (5, 6, "place_of_noun"),             # The [place] of (the) [noun]
    (7, 8, "noun_poss_place"),           # (The) [noun]'s [place]
    (9, 10, "place_of_adj_noun"),        # [place] of the [adjective] [noun]
    (11, 12, "adj_noun"),                # The [adjective] [noun]
]

PLACE_PLACES = [
    "Barrier", "Beach", "Bowl", "Camp", "Cave", "Circle", "City", "Cliff",
    "Crater", "Crossing", "Crypt", "Den", "Ditch", "Falls", "Fence",
    "Field", "Fort", "Gate", "Grove", "Hill", "Hole", "Hut", "Keep",
    "Lake", "Marsh", "Meadow", "Mountain", "Pit", "Post", "Ridge", "Ring",
    "Rise", "Road", "Rock", "Ruin", "Shrine", "Spire", "Spring", "Stone",
    "Tangle", "Temple", "Throne", "Tomb", "Tower", "Town", "Tree", "Vale",
    "Valley", "Village", "Wall",
]

PLACE_ADJECTIVES = [
    "Ancient", "Ashen", "Black", "Bloody", "Blue", "Bright", "Broken",
    "Burning", "Clouded", "Copper", "Cracked", "Dark", "Dead", "Doomed",
    "Endless", "Fallen", "Far", "Fearsome", "Floating", "Forbidden",
    "Frozen", "Ghostly", "Gloomy", "Golden", "Grim", "Hidden", "High",
    "Iron", "Jagged", "Lonely", "Lost", "Low", "Near", "Petrified", "Red",
    "Screaming", "Sharp", "Shattered", "Shifting", "Shining", "Shivering",
    "Shrouded", "Silver", "Stalwart", "Stoney", "Sunken", "Thorny",
    "Thundering", "White", "Withered",
]

# First entry is the book's special "[Name]*" slot - see gen_place_name().
PLACE_NOUNS = [
    "[Name]", "Arm", "Ash", "Blood", "Child", "Cinder", "Corpse", "Crystal",
    "Dagger", "Death", "Demon", "Devil", "Doom", "Eye", "Fear", "Finger",
    "Fire", "Foot", "Ghost", "Giant", "Goblin", "God", "Gold", "Hand",
    "Head", "Heart", "Hero", "Hope", "King", "Knave", "Knight", "Muck",
    "Mud", "Priest", "Queen", "Sailor", "Silver", "Skull", "Smoke",
    "Souls", "Spear", "Spirit", "Stone", "Sword", "Thief", "Troll",
    "Warrior", "Water", "Witch", "Wizard",
]

# --- Dungeon name template (1d12) - the other "site" sub-table -------------
# Perilous Wilds p64's "dungeon name" table, from the "Plumb the Depths"
# (dungeon-creation) chapter. Used for the "dungeon" half of site
# generation - a different table from p21's place table above, with
# vocabulary suited to ruins and dungeons.

DUNGEON_TEMPLATES = [
    (1, 2, "the_place"),                 # The [place]
    (3, 4, "adj_place"),                 # (The) [adjective] [place]
    (5, 6, "place_of_noun"),             # (The) [place] of the [noun]
    (7, 8, "noun_poss_place"),           # (The) [noun]'s [place]
    (9, 10, "place_of_adj_noun"),        # [place] of the [adjective] [noun]
    (11, 12, "adj_noun"),                # (The) [adjective] [noun]
]

DUNGEON_PLACES = [
    "Archive", "Blight", "Boneyard", "Catacomb", "Cave(s)", "Cavern(s)",
    "Citadel", "Cliff", "Crack", "Crag", "Crypt", "Curse", "Deep", "Delve",
    "Den", "Finger", "Fist", "Fort", "Fortress", "Grave", "Haunt", "Hold",
    "Hole(s)", "Hollow(s)", "Home", "House", "Jaws", "Keep", "Lair", "Maw",
    "Maze", "Mountain", "Mouth", "Peak", "Pit", "Remnant", "Retreat",
    "Ruin", "Shrine", "Skull", "Spire", "Temple", "Throne", "Tomb",
    "Tooth", "Tower", "Tunnel(s)", "Vault", "Warren", "Wreck",
]

DUNGEON_ADJECTIVES = [
    "Ancient", "Ashen", "Black", "Bloody", "Blue", "Broken", "Burning",
    "Cracked", "Dark", "Dead", "Doomed", "Endless", "Evil", "Fallen",
    "Far", "Fearsome", "Floating", "Forbidden", "Forgotten", "Frozen",
    "Ghostly", "Gloomy", "Gray", "Grim", "Hidden", "High", "Holy", "Iron",
    "Jagged", "Lonely", "Lost", "Low", "Misty", "Petrified", "Red",
    "Screaming", "Sharp", "Shattered", "Shifting", "Shivering", "Shrouded",
    "Stoney", "Sunken", "Thorny", "Thundering", "Unholy", "White",
    "Wicked", "Withered", "Yellow",
]

# First entry is the book's special "[Name]*" slot - see gen_dungeon_name().
DUNGEON_NOUNS = [
    "[Name]", "Arm", "Ash", "Beast", "Behemoth", "Blood", "Child",
    "Cinder", "Corpse", "Crystal", "Dagger", "Death", "Demon", "Devil",
    "Doom", "Dragon", "Eye", "Fear", "Finger", "Fire", "Foot", "Frog",
    "Ghost", "Giant", "Goblin", "God", "Hand", "Head", "Heart", "Horror",
    "Hero", "Horn", "King", "Knave", "Priest", "Prophet", "Queen",
    "Shard", "Skull", "Souls", "Spear", "Spirit", "Stone", "Sword",
    "Troll", "Warrior", "Water", "Witch", "Wizard", "Worm",
]


def gen_region(name_ancestry="any"):
    """Returns (name, terrain) - most callers just want gen_region_name()."""
    roll = random.randint(1, 12)
    template = next(key for lo, hi, key in REGION_TEMPLATES if lo <= roll <= hi)

    terrain = random.choice(REGION_TERRAINS)
    adjective = random.choice(REGION_ADJECTIVES)
    noun = random.choice(REGION_NOUNS)
    if noun == "[Name]":
        noun, _ = npc_gen.gen_name(name_ancestry)

    if template == "adj_terrain":
        name = f"{_maybe_the()}{adjective} {terrain}"
    elif template == "terrain_of_noun":
        name = f"{terrain} of {_maybe_the(cap=False)}{noun}"
    elif template == "terrain_adj":
        name = f"The {terrain} {adjective}"  # mandatory "The" per the book
    elif template == "noun_terrain":
        name = f"{_maybe_the()}{noun} {terrain}"
    elif template == "noun_poss_adj_terrain":
        name = f"{_maybe_the()}{noun}'s {adjective} {terrain}"
    else:
        name = f"{adjective} {terrain} of {_maybe_the(cap=False)}{noun}"  # adj_terrain_of_noun
    return name, terrain


def gen_region_name(name_ancestry="any"):
    return gen_region(name_ancestry)[0]


# --- Area (this skill's own term - reuses the region tables) ---------------
# An area is a region-style name with the terrain word usually (70% of the
# time) omitted, since it's implied by the parent region. The template is
# still rolled at random even when terrain is omitted, so the shape/length
# of the name varies (bare noun, nominalized-adjective "of the" phrase,
# terse possessive, etc.) rather than collapsing to one fixed pattern.

DEFAULT_TERRAIN_MATCH_CHANCE = 0.7

# This skill's own invented word list (not from the source material): a
# handful of generic geography nouns used as an alternate terrain-omitted
# head, so the adjective can do its normal job (modifying the trailing
# noun) instead of standing in for a noun itself - "The Land of the
# Fallen King" as an alternative flavor to "The Fallen of the King".
GEO_FILLER_WORDS = ["Land", "Reach", "Vale", "Realm", "Domain", "Territory", "Marches", "Expanse"]


def _gen_region_style_terrain_omitted(name_ancestry="any"):
    roll = random.randint(1, 12)
    template = next(key for lo, hi, key in REGION_TEMPLATES if lo <= roll <= hi)

    adjective = random.choice(REGION_ADJECTIVES)
    noun = random.choice(REGION_NOUNS)
    if noun == "[Name]":
        noun, _ = npc_gen.gen_name(name_ancestry)

    if template in ("adj_terrain", "terrain_adj"):
        # "(The) [adjective] [terrain]" / "The [terrain] [adjective]" ->
        # the standard adjective+noun order.
        return f"{_maybe_the()}{adjective} {noun}"
    if template in ("terrain_of_noun", "adj_terrain_of_noun"):
        # "[terrain] of (the) [noun]" -> two alternate forms, since terrain
        # (the template's natural head noun) isn't available:
        #   1. nominalize the adjective in terrain's place ("The Fallen of
        #      the King") - a common enough fantasy-epithet construction.
        #   2. keep the adjective in its normal modifying role and use a
        #      generic geography word as the head instead ("The Land of
        #      the Fallen King") - see GEO_FILLER_WORDS.
        # "The" is mandatory in both (not a coin flip): a bare adjective
        # standing in for a noun reads fine with an article ("The Fallen
        # of the Traitor") but often badly without one ("Fallen of
        # Traitor").
        if random.random() < 0.5:
            return f"The {adjective} of the {noun}"
        filler = random.choice(GEO_FILLER_WORDS)
        return f"The {filler} of the {adjective} {noun}"
    if template == "noun_terrain":
        # "(The) [noun] [terrain]" -> bare noun, terrain dropped entirely.
        return f"{_maybe_the()}{noun}"
    # noun_poss_adj_terrain: "(The) [noun]'s [adjective] [terrain]" ->
    # terse possessive epithet, terrain dropped.
    return f"{_maybe_the()}{noun}'s {adjective}"


def gen_area_name(name_ancestry="any", terrain_match_chance=DEFAULT_TERRAIN_MATCH_CHANCE):
    if random.random() < terrain_match_chance:
        name = _gen_region_style_terrain_omitted(name_ancestry)
    else:
        name = gen_region_name(name_ancestry)
    return _apply_direction(name)


# This skill's own invented flavor for the area tier specifically (not
# from the source material): a positional/directional word, since areas
# are sub-regions and this is a common, low-risk way to distinguish one
# from another within the same parent region ("The Upper Ashen Heights",
# "Far Reach of the Traitor") without touching the terrain/grammar logic
# above at all.
AREA_DIRECTIONS = ["Upper", "Lower", "Far", "Near", "Outer", "Inner",
                   "Northern", "Southern", "Eastern", "Western"]
AREA_DIRECTION_CHANCE = 0.25


def _apply_direction(name):
    if random.random() >= AREA_DIRECTION_CHANCE:
        return name
    direction = random.choice(AREA_DIRECTIONS)
    if name.startswith("The "):
        return f"The {direction} {name[4:]}"
    return f"{direction} {name}"


# --- Site (this skill's own term) - randomly a "place" or a "dungeon" -----

DEFAULT_DUNGEON_CHANCE = 50  # percent; 100 = always dungeon, 0 = always place


def gen_place_name(name_ancestry="any"):
    roll = random.randint(1, 12)
    template = next(key for lo, hi, key in PLACE_TEMPLATES if lo <= roll <= hi)

    place = random.choice(PLACE_PLACES)
    adjective = random.choice(PLACE_ADJECTIVES)
    noun = random.choice(PLACE_NOUNS)
    if noun == "[Name]":
        noun, _ = npc_gen.gen_name(name_ancestry)

    if template == "the_place":
        return f"The {place}"  # mandatory "The"
    if template == "adj_place":
        return f"The {adjective} {place}"  # mandatory "The"
    if template == "place_of_noun":
        return f"The {place} of {_maybe_the(cap=False)}{noun}"  # mandatory lead, optional mid
    if template == "noun_poss_place":
        return f"{_maybe_the()}{noun}'s {place}"
    if template == "place_of_adj_noun":
        return f"{place} of the {adjective} {noun}"  # mandatory mid "the"
    return f"The {adjective} {noun}"  # adj_noun, mandatory "The"


def gen_dungeon_name(name_ancestry="any"):
    roll = random.randint(1, 12)
    template = next(key for lo, hi, key in DUNGEON_TEMPLATES if lo <= roll <= hi)

    place = random.choice(DUNGEON_PLACES)
    adjective = random.choice(DUNGEON_ADJECTIVES)
    noun = random.choice(DUNGEON_NOUNS)
    if noun == "[Name]":
        noun, _ = npc_gen.gen_name(name_ancestry)

    if template == "the_place":
        return f"The {place}"  # mandatory "The"
    if template == "adj_place":
        return f"{_maybe_the()}{adjective} {place}"
    if template == "place_of_noun":
        return f"{_maybe_the()}{place} of the {noun}"  # mandatory mid "the"
    if template == "noun_poss_place":
        return f"{_maybe_the()}{noun}'s {place}"
    if template == "place_of_adj_noun":
        return f"{place} of the {adjective} {noun}"  # mandatory mid "the"
    return f"{_maybe_the()}{adjective} {noun}"  # adj_noun


def gen_site_name(name_ancestry="any", kind=None, dungeon_chance=DEFAULT_DUNGEON_CHANCE):
    """kind: None (roll per dungeon_chance), 'place', or 'dungeon' (force one)."""
    if kind is None:
        kind = "dungeon" if random.uniform(0, 100) < dungeon_chance else "place"
    return gen_dungeon_name(name_ancestry) if kind == "dungeon" else gen_place_name(name_ancestry)


# --- Region-with-areas-and-sites composite (this script's own addition, not
# from the source material) --------------------------------------------

DEFAULT_NAREAS_RANGE = (3, 7)
DEFAULT_SITE_CHANCE = 0.3


def gen_region_with_areas(name_ancestry="any", nareas=None,
                           site_chance=DEFAULT_SITE_CHANCE,
                           dungeon_chance=DEFAULT_DUNGEON_CHANCE,
                           terrain_match_chance=DEFAULT_TERRAIN_MATCH_CHANCE):
    region_name, region_terrain = gen_region(name_ancestry)
    n = nareas if nareas is not None else random.randint(*DEFAULT_NAREAS_RANGE)
    areas = []
    for _ in range(n):
        area_name = gen_area_name(name_ancestry, terrain_match_chance)
        site_name = None
        if random.random() < site_chance:
            site_name = gen_site_name(name_ancestry, dungeon_chance=dungeon_chance)
        areas.append((area_name, site_name))
    return region_name, areas


def format_region_with_areas(region_name, areas):
    lines = [f"Region: {region_name}", "Areas (subdivisions):", ""]
    for i, (area_name, site_name) in enumerate(areas, 1):
        lines.append(f"{i}. {area_name}")
        if site_name:
            lines.append(f"   Site: {site_name}")
    return "\n".join(lines)


HELP_LLM = """\
region_gen.py - region/area/site name generator for Dungeon World (Perilous
Wilds map-drawing and dungeon-creation procedures).

TIERS (this skill's own definitions, not from the source material)
  Region  a large land/sea swath, terrain- or politically-defined. The first
          region on a map must contain the party's starting position.
  Area    a terrain- or politically-defined sub-region, contained in one
          region. Reuses the region tables (not a separate word bank) - its
          name usually omits the terrain word since the parent region
          already implies it (see --terrain-match).
  Site    a single notable location within an area - a "place" (Perilous
          Wilds p21) or "dungeon" (p64) name, 50/50 by default (see
          --dungeon-chance/--site-kind). Never auto-generates a steading;
          run steading_gen.py by hand if a site warrants one - that's a GM
          judgment call this script doesn't try to make.

USAGE
  region_gen.py [--tier region|area|site [--site-kind place|dungeon]]
                 [--nareas N] [--site-chance F] [--dungeon-chance P]
                 [--terrain-match F] [-n N] [--name-ancestry A] [--seed N]

Default mode (no --tier): generates one region plus its areas together,
with terrain inheritance and possible sites per area.

--tier region|area|site   generate a single name of just that tier and stop;
                           ignores --nareas/--site-chance (region+area mode
                           options)
--site-kind place|dungeon force a site's type (only with --tier site;
                           otherwise site type is rolled via --dungeon-chance)
--nareas N                 areas under the region (default: random 3-7);
                           default mode only
--site-chance F (0.0-1.0)  chance each area also gets a site (default:
                           {DEFAULT_SITE_CHANCE}; 0=never, 1=always); default
                           mode only. No steading is auto-generated for a
                           site - manual GM call.
--dungeon-chance P (0-100) chance a site is 'dungeon' not 'place' (default:
                           {DEFAULT_DUNGEON_CHANCE}); applies to --tier site
                           (unless --site-kind forces one) and every site in
                           default mode
--terrain-match F (0.0-1.0) chance an area shares its region's terrain and
                           omits the terrain word (default:
                           {DEFAULT_TERRAIN_MATCH_CHANCE}; 0=always
                           independent, 1=always match); applies to --tier
                           area and every area in default mode
-n, --count N               how many to generate (default 1)
--name-ancestry A           ancestry (npc_gen.py's list, or 'any') to draw
                           from if the rare "[Name]" noun slot is rolled
                           (default: any)
--seed N                    reproducible output - dev/debug only, NEVER
                           during play

OUTPUT
  --tier mode: one bare name per line. Default mode: the region name, then
  each area indented under it with its own name and adjacency/site info as
  generated. Multiple (-n/--count > 1) results are blank-line separated.
  Always ends with a reminder to update yaml files.

EXAMPLES
  region_gen.py                                     region + 3-7 areas
  region_gen.py --nareas 5 --site-chance 0            5 areas, no sites
  region_gen.py --dungeon-chance 100                  every site a dungeon
  region_gen.py --tier region -n 5                    5 bare region names
  region_gen.py --tier site --site-kind dungeon -n 5  5 dungeon-flavored sites
""".format(DEFAULT_SITE_CHANCE=DEFAULT_SITE_CHANCE,
           DEFAULT_DUNGEON_CHANCE=DEFAULT_DUNGEON_CHANCE,
           DEFAULT_TERRAIN_MATCH_CHANCE=DEFAULT_TERRAIN_MATCH_CHANCE)


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return

    ap = argparse.ArgumentParser(description="Generate Dungeon World region/area/site names.")
    ap.add_argument("--tier", choices=["region", "area", "site"], default=None,
                     help="Generate a single 'region', 'area', or 'site' name and "
                          "nothing else. Default (omitted): generate a region plus "
                          "its areas together, with terrain inheritance and possible "
                          "sites - see --nareas/--site-chance/--dungeon-chance.")
    ap.add_argument("--site-kind", choices=["place", "dungeon"], default=None,
                     help="Only used with --tier site: force a specific site type "
                          "instead of rolling one via --dungeon-chance.")
    ap.add_argument("--nareas", type=int, default=None,
                     help="Number of areas to generate under the region (default: "
                          "random 3-7). Only used in the default region+areas mode.")
    ap.add_argument("--site-chance", type=float, default=DEFAULT_SITE_CHANCE,
                     help=f"Chance (0.0-1.0) each area also gets a site (default: "
                          f"{DEFAULT_SITE_CHANCE}; use 0 to disable, 1 to always "
                          f"include). Only used in the default region+areas mode. "
                          f"No steading is auto-generated for a site - that's a "
                          f"manual GM call; run steading_gen.py yourself if wanted.")
    ap.add_argument("--dungeon-chance", type=float, default=DEFAULT_DUNGEON_CHANCE,
                     help=f"Percent chance (0-100) a site is a 'dungeon' rather than "
                          f"a 'place' (default: {DEFAULT_DUNGEON_CHANCE}; 100 = "
                          f"always dungeon, 0 = always place). Applies to both "
                          f"--tier site (unless --site-kind forces one) and every "
                          f"site rolled in the default region+areas mode.")
    ap.add_argument("--terrain-match", type=float, dest="terrain_match",
                     default=DEFAULT_TERRAIN_MATCH_CHANCE,
                     help=f"Chance (0.0-1.0) an area shares its parent region's "
                          f"terrain, omitting the terrain word from its name "
                          f"(default: {DEFAULT_TERRAIN_MATCH_CHANCE}; use 0 for "
                          f"every area to roll independent terrain, 1 to always "
                          f"match). Applies to --tier area and every area rolled "
                          f"in the default region+areas mode.")
    ap.add_argument("-n", "--count", type=int, default=1, help="How many to generate")
    ap.add_argument("--name-ancestry", choices=list(npc_gen.NAMES.keys()) + ["any"],
                     default="any",
                     help="Ancestry to draw from if the rare '[Name]' noun slot is "
                          "rolled (default: any)")
    ap.add_argument("--seed", type=int, default=None, help="Random seed, for reproducibility")
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                     help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    apply_seed(args.seed)

    if args.tier is not None:
        for _ in range(args.count):
            if args.tier == "region":
                print(gen_region_name(args.name_ancestry))
            elif args.tier == "area":
                print(gen_area_name(args.name_ancestry, args.terrain_match))
            else:
                print(gen_site_name(args.name_ancestry, args.site_kind, args.dungeon_chance))
        return

    for i in range(args.count):
        region_name, areas = gen_region_with_areas(
            args.name_ancestry, args.nareas, args.site_chance, args.dungeon_chance,
            args.terrain_match)
        print(format_region_with_areas(region_name, areas))
        if args.count > 1 and i < args.count - 1:
            print()

    print("Reminder: update gm and character yaml files now!")


if __name__ == "__main__":
    main()
