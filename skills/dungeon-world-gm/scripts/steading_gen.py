#!/usr/bin/env python3
"""
Steading generator for Dungeon World.

Usage:
    python3 steading_gen.py                     # a random steading, any kind
    python3 steading_gen.py --kind town          # village | town | keep | city
    python3 steading_gen.py --name-only          # just a mad-libbed name
    python3 steading_gen.py --seed 7 -n 3         # three, reproducible
    python3 steading_gen.py --culture hungarian-like --name-only   # PW culture name alone
    python3 steading_gen.py --culture elven --name-only            # original Welsh-flavored elven names
    python3 steading_gen.py --culture dwarven --name-only          # original Old Norse-flavored dwarven names
    python3 steading_gen.py --culture halfling --name-only         # pastoral madlib variant (synonym: country)
    python3 steading_gen.py --culture human --name-only -n 5       # madlib + PW cultures + country, no elven/dwarven
    python3 steading_gen.py --culture any --name-only -n 5         # every culture, mixed
    python3 steading_gen.py --culture yoruba-like --show-gloss --name-only  # with English gloss

Data source: the Steading Tags system and quick-build recipes (core rulebook
"The World" chapter, p205-220), as condensed in this skill's references/npc-tools.md.
Verified against Perilous Wilds p50-51: its Steading table is the same core-rulebook
content reformatted as 1d12 rolls, not new tag content - except its p49 steading-size
roll (village 1-5, town 6-8, keep 9-11, city 12), which core doesn't specify and which
this script uses by default when --kind isn't given (--kind-weight uniform disables it).
The four "-like" culture steading-name lists are from The Perilous Wilds (Revised
Edition) by Jason Lutes, p72-75 (CC BY-SA 3.0). Note: those pages' name lists are
shared with npc_gen.py's gendered "-like" ancestries (same four invented cultures);
the *mount*-name column from those same tables is deliberately NOT included here -
mounts aren't steadings and belong with a future follower/hireling system instead.
The "elven" (Welsh-flavored) and "dwarven" (Old Norse-flavored) cultures are this
script's own original additions, not from Perilous Wilds or any other source -
see comments above each list for details on how each was built. "country"/
"halfling" reuse the default mad-lib machinery with a smaller, more pastoral
style/suffix pool (no fortress-scale suffixes, no color/thing/adjective
prefixes) rather than a separate word list - halfling steadings are Dungeon
World's core-book "human, but rustic" race, so this just biases the existing
generator rather than duplicating it wholesale.

Note on the mad-lib name generator (--culture madlib, the default): the source
material gives the mad-lib STRUCTURE (Part 1 categories like [Name]'s / [Food] /
[Color] / [Animal] + Part 2 suffix list) but doesn't supply word banks for every
Part 1 category itself - those are this script's own addition, built to fit the
pattern, not transcribed from the book.
"""
import argparse
import random
import sys


def _force_utf8_stdio():
    """Windows defaults sys.stdout to the ANSI code page (cp1252) whenever
    stdout is not a real console - a redirect or a pipe is enough. cp1252 has
    no mapping for characters this script prints (e.g. U+2192 "->"), so the
    write raises UnicodeEncodeError instead of degrading. Force UTF-8; a no-op
    where the stream does not support reconfiguring."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass


_force_utf8_stdio()

# --- Name generation -------------------------------------------------------

SUFFIXES = [
    "shire", "burg", "bridge", "crossing", "ford", "river", "bark", "field",
    "falls", "harbor", "bay", "wood", "gate", "hill", "ton", "moor", "land",
    "calm", "wall", "down", "fast", "bend", "hold", "fortress", "castle",
    "stone", "pit",
]

# Original addition (not in source material) - small word banks per Part 1
# category, built to fit the book's mad-lib structure.
COLORS = ["Gray", "Golden", "Silver", "Black", "White", "Crimson", "Amber", "Iron"]
THINGS = ["Nook", "Barrow", "Crystal", "Anvil", "Lantern", "Millstone", "Cairn", "Thorn"]
ADJECTIVES = ["Daunting", "Wry", "Quiet", "Broken", "Hollow", "Merry", "Grim", "Bright"]
ANIMALS = ["Wolf", "Raven", "Stag", "Boar", "Hawk", "Fox", "Bear", "Owl"]
JOBS = ["Tanner", "Miller", "Smith", "Fisher", "Cooper", "Weaver", "Mason", "Brewer"]
FOODS = ["Barley", "Honey", "Salt", "Mead", "Bramble", "Cider"]
PEOPLE = ["Tanner", "Nook", "Barrow", "Wren", "Thistle", "Corvin"]

PART1_STYLES = ["possessive", "color", "thing", "adjective", "animal", "job_possessive", "food"]

# Restricted style/suffix pools for the "country"/"halfling" flavor - same
# mad-lib machinery as the default, just biased toward homey, pastoral,
# down-to-earth results (no color/thing/adjective grandiosity, no
# fortress/castle-scale suffixes) to read as culturally distinct from
# generic human steading names.
PART1_COUNTRY_STYLES = ["possessive", "animal", "job_possessive", "food"]
SUFFIXES_COUNTRY = [
    "shire", "burg", "bridge", "crossing", "ford", "river", "bark", "field",
    "falls", "wood", "hill", "ton", "moor", "land", "calm", "down", "bend",
]

# Perilous Wilds p72-75 steading-name columns, one of the four "-like" cultures
# also used by npc_gen.py's gendered ancestries. Each entry is
# (invented_name, english_gloss) - the book's own parenthetical "translations."
# These are invented words loosely evoking the named real-world language, not
# actual translations - see npc_gen.py's docstring for the same disclaimer.
STEADING_NAMES = {
    "hungarian-like": [
        ("Aldott", "Blessed"), ("Almahid", "Applebridge"), ("Elesett", "Fallen"),
        ("Feketz", "Black Rock"), ("Godor", "Pit"), ("Kelegaz", "Eastford"),
        ("Kigyov", "Snake Swamp"), ("Kiralokas", "Queen's Castle"),
        ("Kiralsir", "King's Grave"), ("Magziklar", "Highcliff"), ("Mocsar", "Fen"),
        ("Nagyvros", "Hightown"), ("Okorm", "Oxfield"), ("Orkfal", "Orcwall"),
        ("Perov", "Redwater"), ("Soterdo", "Dark Wood"), ("Tehenvar", "Cow Town"),
        ("Toron", "Tower"), ("Torott", "Ironhold"), ("Utolszer", "Last Stand"),
        ("Valavolg", "Greendale"), ("Vastar", "Dwarf Watch"), ("Viz", "Oxfield"),
        ("Volgyom", "Valley"), ("Zoldom", "Green Hill"),
    ],
    "yoruba-like": [
        ("Asala Ilu", "Desert Town"), ("Atijo Ina", "Old Fire"),
        ("Bajesia", "Broken Banner"), ("Dudu Olomi", "Blackmarsh"),
        ("Ebutte Meta", "Three Ports"), ("Ejodo", "Snake River"),
        ("Esukale", "Devil's Dinner"), ("Fadormi", "Silver Spring"),
        ("Funfumi", "Whitewater"), ("Gooluna", "Gold Road"),
        ("Ijisofo", "Storm Hollow"), ("Ikukenu", "Dearth's Door"),
        ("Jinibi", "Far Place"), ("Oba Ile", "King's Home"),
        ("Oduroke", "Prayer Hill"), ("Ogbinibi", "Farming Place"),
        ("Ogunibi", "Battle Place"), ("Okanigi", "One Tree"),
        ("Okutasibo", "Stone Marker"), ("Olorusura", "God's Treasure"),
        ("Olusajeki", "Wizard's Keep"), ("Oluwakaji", "Lord's Tomb"),
        ("Opolokuta", "Many Stones"), ("Opoligi", "Many Trees"),
        ("Zoldom", "Green Hill"),
    ],
    "finnish-like": [
        ("Etuvartio", "Outpost"), ("Hopea Kaivos", "Silver Mine"),
        ("Kalapunki", "Fish Town"), ("Kivimurri", "Stone Wall"),
        ("Maaginen", "Magic"), ("Maki Linna", "Hill Castle"),
        ("Merenranta", "Seaside"), ("Metsasmaat", "Hunting Ground"),
        ("Mustakota", "Black Hut"), ("Maenrinne", "Hillside"),
        ("Paja", "Forge"), ("Pienni Paikka", "Low Place"),
        ("Pyha Paikka", "Holy Place"), ("Rantakallio", "Cliff"),
        ("Rikki", "Broken"), ("Suo", "Swamp"), ("Suosi", "Favored"),
        ("Torni", "Tower"), ("Turvapaikka", "Refuge"), ("Uusipunki", "New Town"),
        ("Valkoinen Kivi", "Whitestone"), ("Valtaistuin", "Throne"),
        ("Vapaanki", "Free Town"), ("Vihrea Paikka", "Green Place"),
        ("Viimeinen Koti", "Last Home"),
    ],
    "indonesian-like": [
        ("Airdib", "Blessed Waters"), ("Airjinh", "Clearwater"),
        ("Akhir Jalan", "Road's End"), ("Berdarah", "Bloody"),
        ("Bidang Bera", "Fallow Field"), ("Candibula", "Moon Temple"),
        ("Ditingga", "Forsaken"), ("Emasungai", "Gold Creek"),
        ("Gunung", "Mountain"), ("Kayu", "Timber"), ("Kuil", "Temple"),
        ("Ladang Hijau", "Greenfield"), ("Lembah", "Valley"),
        ("Menjau", "Far Away"), ("Ngarai", "Canyon"),
        ("Persimpangan", "Crossroads"), ("Puncakit", "Hilltop"),
        ("Sungairac", "Poison River"), ("Teibing", "Cliffside"),
        ("Tempat Aman", "Safe Place"), ("Tempat Istir", "Rest Place"),
        ("Terkutuk", "Cursed"), ("Tersentu", "Touched by God"),
        ("Wahah", "Oasis"), ("Yangtinggi", "High Tower"),
    ],
    # Original addition (not from Perilous Wilds or any other source material)
    # - Welsh-flavored invented place names for elven steadings, built from
    # real Welsh toponymic elements (Llan-/Aber-/Caer-/Cwm-/Ynys-/Nant-/
    # Bryn-/Coed- etc.) recombined into new words, not actual Welsh place
    # names. Same "loosely evokes, isn't literally" spirit as the PW lists.
    "elven": [
        ("Llanfaerith", "Blessed Hollow"), ("Abercarwen", "Riverbend"),
        ("Caerdduvel", "Dark Fortress"), ("Cwmerith", "Deep Valley"),
        ("Ynysgarrow", "Isle of Ravens"), ("Glanwyddon", "Silverbank"),
        ("Pendrallach", "Stonehead"), ("Trefynnon", "Wellspring Town"),
        ("Brynovaeth", "Windy Hill"), ("Nantcerith", "Whitewater"),
        ("Coedllanwy", "Deepwood"), ("Dduvaenor", "Blackstone"),
        ("Rhosgarreth", "Moor's Edge"), ("Llanbereth", "Sanctuary"),
        ("Aberllynwy", "Lakemouth"), ("Caerwyndhu", "Grey Keep"),
        ("Cwmfardden", "Songvale"), ("Ynysdaerith", "Farhaven Isle"),
        ("Glynmawreth", "Great Glen"), ("Pentrewy", "Riverhead"),
        ("Brynllethan", "Bright Ridge"), ("Nantglasion", "Greenstream"),
        ("Coedavrith", "Old Forest"), ("Dduncairwen", "Blessed Cairn"),
        ("Rhyddafan", "Freehold"), ("Llanmereth", "Peaceful Vale"),
        ("Abercorwyn", "Fair Ford"), ("Caerystradd", "Broken Wall"),
        ("Cwmdrallen", "Shadow Hollow"), ("Ynysbereth", "Sacred Isle"),
    ],
    # Original addition (not from Perilous Wilds or any other source material)
    # - Old Norse vocabulary recombined into compound place names for dwarven
    # steadings (per Tolkien's own convention of using Old Norse for dwarves).
    # Old Norse is a dead language, so unlike the other invented cultures here
    # these lean on real vocabulary rather than mutated approximations - just
    # checked against known real-world place names and discarded any hits.
    # Diacritics (þ/ð/ö etc.) flattened to ASCII to match this file's style.
    "dwarven": [
        ("Steinvirki", "Stonework"), ("Malmgardr", "Ore-yard"),
        ("Hamarskard", "Hammer Pass"), ("Grjotborg", "Rockfort"),
        ("Djupheim", "Deep Home"), ("Svartberg", "Black Mountain"),
        ("Gullsal", "Gold Hall"), ("Jarnhola", "Iron Pit"),
        ("Silfrgil", "Silver Ravine"), ("Thrymtindr", "Thunder Peak"),
        ("Smidjuvangr", "Forge Field"), ("Klettheim", "Crag Home"),
        ("Myrkgrof", "Dark Pit"), ("Fjallsholt", "Mountain Wood"),
        ("Hvitberg", "White Mountain"), ("Eldsmidja", "Fire-forge"),
        ("Bjargtun", "Rock Enclosure"), ("Grjotnes", "Stony Headland"),
        ("Malmvangr", "Metal Field"), ("Steinholl", "Stone Hall"),
        ("Dvergstad", "Dwarf-stead"), ("Ishamar", "Ice Crag"),
        ("Kolgrof", "Coal Pit"), ("Bergsund", "Mountain Strait"),
        ("Thungberg", "Heavy Mountain"), ("Vigholt", "Battle Wood"),
        ("Hraunborg", "Lava Fortress"), ("Stalvirki", "Steel-works"),
        ("Grafheim", "Pit Home"), ("Sorgfell", "Sorrow Mountain"),
    ],
}


# All culture keys gen_name() understands as a single, specific name source
# (i.e. not "any"/"human", which pick randomly from among these).
ALL_CULTURES = ["madlib", "country"] + list(STEADING_NAMES.keys())


def _gen_madlib_name(styles, suffixes):
    style = random.choice(styles)
    suffix = random.choice(suffixes)
    if style == "possessive":
        prefix = f"{random.choice(PEOPLE)}'s"
    elif style == "job_possessive":
        prefix = f"{random.choice(JOBS)}'s"
    elif style == "color":
        prefix = random.choice(COLORS)
    elif style == "thing":
        prefix = random.choice(THINGS)
    elif style == "adjective":
        prefix = random.choice(ADJECTIVES)
    elif style == "animal":
        prefix = random.choice(ANIMALS)
    else:  # food
        prefix = random.choice(FOODS)

    # possessive prefixes read better with a space before the suffix word
    if prefix.endswith("'s"):
        return f"{prefix} {suffix.capitalize()}"
    return f"{prefix}{suffix}"


def gen_name(culture="madlib", show_gloss=False):
    if culture == "halfling":
        culture = "country"

    if culture in ("any", "human"):
        pool = list(ALL_CULTURES)
        if culture == "human":
            pool = [c for c in pool if c not in ("elven", "dwarven")]
        culture = random.choice(pool)

    if culture == "country":
        return _gen_madlib_name(PART1_COUNTRY_STYLES, SUFFIXES_COUNTRY)

    if culture != "madlib":
        name, gloss = random.choice(STEADING_NAMES[culture])
        return f"{name} ({gloss})" if show_gloss else name

    return _gen_madlib_name(PART1_STYLES, SUFFIXES)


# --- Tag-based generation ---------------------------------------------------

RECIPES = {
    "village": {
        "base": ["Poor", "Steady", "Militia", "Resource (choice)", "Oath (another steading)"],
        "bonus_label": "if part of a kingdom",
        "bonus": [
            ("naturally defended", ["Safe", "-Defenses"]),
            ("abundant resources", ["+Prosperity", "Resource (choice)", "Enmity (choice)"]),
            ("protected by another steading", ["Oath (that steading)", "+Defenses"]),
            ("on a major road", ["Trade (choice)", "+Prosperity"]),
            ("built around a wizard's tower", ["Personage (the wizard)", "Blight (arcane creatures)"]),
            ("built on a site of religious significance", ["Divine", "History (choice)"]),
        ],
        "problem": [
            ("arid or uncultivable land", ["Need (Food)"]),
            ("dedicated to a deity", ["Religion (that deity)", "Enmity (a settlement of another deity)"]),
            ("recently fought a battle", ["-Population", "-Prosperity (if fought to the end)", "-Defenses (if lost)"]),
            ("has a monster problem", ["Blight (that monster)", "Need (adventurers)"]),
            ("absorbed another village", ["+Population", "Lawless"]),
            ("remote or unwelcoming", ["-Prosperity", "Dwarven or Elven"]),
        ],
    },
    "town": {
        "base": ["Moderate", "Steady", "Watch", "Trade (choice)", "Trade (choice)"],
        "bonus_label": "if listed as Trade by another steading",
        "bonus": [
            ("booming", ["Booming", "Lawless"]),
            ("stands on a crossroads", ["Market", "+Prosperity"]),
            ("defended by another steading", ["Oath (that steading)", "+Defenses"]),
            ("built around a church", ["Power (Divine)"]),
            ("built around a craft", ["Craft (choice)", "Resource (something required for that craft)"]),
            ("built around a military post", ["+Defenses"]),
        ],
        "problem": [
            ("outgrown an important supply", ["Need (that resource)", "Trade (a supplier of it)"]),
            ("offers defense to others", ["Oath (choice)", "-Defenses"]),
            ("notorious for an outlaw", ["Personage (the outlaw)", "Enmity (where the crimes were committed)"]),
            ("cornered the market on a good/service", ["Exotic (that good or service)", "Enmity (an ambitious settlement)"]),
            ("has a disease", ["-Population"]),
            ("a popular meeting place", ["+Population", "Lawless"]),
        ],
    },
    "keep": {
        "base": ["Poor", "Shrinking", "Guard", "Need (Supplies)", "Trade (a supplier)", "Oath (choice)"],
        "bonus_label": "if owed fealty by at least one settlement",
        "bonus": [
            ("belongs to a noble family", ["+Prosperity", "Power (Political)"]),
            ("run by a skilled commander", ["Personage (the commander)", "+Defenses"]),
            ("stands watch over a trade road", ["+Prosperity", "Guild (trade)"]),
            ("used to train special troops", ["Arcane", "-Population"]),
            ("surrounded by fertile land", ["remove Need (Supplies)"]),
            ("stands on a border", ["+Defenses", "Enmity (the other side of the border)"]),
        ],
        "problem": [
            ("built on a naturally defensible position", ["Safe", "-Population"]),
            ("was a conquest from another power", ["Enmity (steadings of that power)"]),
            ("a safe haven for brigands", ["Lawless"]),
            ("built to defend from a specific threat", ["Blight (that threat)"]),
            ("has seen horrible bloody war", ["History (Battle)", "Blight (Restless Spirits)"]),
            ("given the worst of the worst", ["Need (Skilled Recruits)"]),
        ],
    },
    "city": {
        "base": ["Moderate", "Steady", "Guard", "Market", "Guild (choice)", "Oath (a town)", "Oath (a keep)"],
        "bonus_label": "if it has trade and fealty",
        "bonus": [
            ("has permanent defenses, like walls", ["+Defenses", "Oath (choice)"]),
            ("ruled by one person", ["Personage (the ruler)", "Power (Political)"]),
            ("diverse", ["Dwarven", "Elven"]),
            ("a trade hub", ["Trade (every nearby steading)", "+Prosperity"]),
            ("ancient, built on its own ruins", ["History (choice)", "Divine"]),
            ("a center of learning", ["Arcane", "Craft (choice)", "Power (Arcane)"]),
        ],
        "problem": [
            ("has outgrown its resources", ["+Population", "Need (food)"]),
            ("has designs on nearby territory", ["Enmity (nearby steadings)", "+Defenses"]),
            ("ruled by a theocracy", ["-Defenses", "Power (Divine)"]),
            ("ruled by the people", ["-Defenses", "+Population"]),
            ("has supernatural defenses", ["+Defenses", "Blight (related supernatural creatures)"]),
            ("lies on a place of power", ["Arcane", "Personage (whoever watches it)", "Blight (arcane creatures)"]),
        ],
    },
}

# Perilous Wilds p49's steading-size roll (1d12: 1-5 village, 6-8 town,
# 9-11 keep, 12 city) - not in the core rulebook, which just presents the
# four sizes as options without a weighting. Used when --kind isn't given
# and --kind-weight is "weighted" (the default).
KIND_WEIGHTS = [("village", 5), ("town", 3), ("keep", 3), ("city", 1)]


def pick_kind(weighted=True):
    if not weighted:
        return random.choice(list(RECIPES.keys()))
    kinds, weights = zip(*KIND_WEIGHTS)
    return random.choices(kinds, weights=weights, k=1)[0]


def gen_steading(kind=None, culture="madlib", show_gloss=False, weighted=True):
    if kind is None:
        kind = pick_kind(weighted)
    recipe = RECIPES[kind]
    name = gen_name(culture, show_gloss)
    tags = list(recipe["base"])

    bonus_reason, bonus_tags = random.choice(recipe["bonus"])
    problem_reason, problem_tags = random.choice(recipe["problem"])

    lines = [f"{name} ({kind.title()})", f"  Base tags: {', '.join(tags)}"]
    lines.append(f"  Bonus ({recipe['bonus_label']} - {bonus_reason}): {', '.join(bonus_tags)}")
    lines.append(f"  Problem ({problem_reason}): {', '.join(problem_tags)}")
    return "\n".join(lines)


HELP_LLM = """\
steading_gen.py - tag-based Dungeon World steading generator (name + tags).

USAGE
  steading_gen.py [--kind K] [--kind-weight W] [--culture C] [--show-gloss]
                   [--name-only] [-n N] [--seed N]

--kind (default: random, weighted by --kind-weight)
  village | town | keep | city
  Each kind's recipe rolls a random Bonus tag and a random Problem tag on
  top of that kind's fixed Base tags.

--kind-weight (only matters when --kind is omitted)
  weighted (default) - Perilous Wilds p49's 1d12 distribution: village 1-5,
    town 6-8, keep 9-11, city 12
  uniform - equal probability among the four kinds

--culture (default: madlib)
  madlib              this script's own word-bank mad-lib generator
  country | halfling  synonyms - pastoral madlib variant (smaller, no
                       fortress-scale suffixes, no color/thing/adjective
                       prefixes)
  hungarian-like | yoruba-like | finnish-like | indonesian-like | elven |
  dwarven             a specific invented/flavored culture alone (elven and
                       dwarven are this script's own additions; the four
                       "-like" ones are Perilous Wilds p72-75, CC BY-SA 3.0)
  any                 combined pool of every culture above, uniform
  human               same as 'any' but excluding elven/dwarven

--show-gloss    for Perilous Wilds "-like" cultures, append the book's
                English gloss, e.g. "Toron (Tower)"
-n, --count N   how many to generate (default 1)
--name-only     just the name, skip tags
--seed N        reproducible output - dev/debug only, NEVER during play

OUTPUT
  "Name (Kind)" then Base tags / Bonus tags (with the reason rolled) /
  Problem tags (with the reason rolled). --name-only prints just the name.
  Multiple (-n/--count > 1) results are blank-line separated.
  Always ends with a reminder to update the gmsecret yaml.

Full steading tag glossary and quick-build recipes by hand (not this script's
random pick) are in references/npc-tools.md and references/tag-reference.md.

EXAMPLES
  steading_gen.py --kind town
  steading_gen.py --kind-weight uniform
  steading_gen.py --name-only -n 5
  steading_gen.py --culture hungarian-like --name-only
  steading_gen.py --culture any --name-only -n 5
"""


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return

    ap = argparse.ArgumentParser(description="Generate a Dungeon World steading.")
    ap.add_argument("--kind", choices=list(RECIPES.keys()), default=None,
                     help="village | town | keep | city (default: random, see --kind-weight)")
    ap.add_argument("--kind-weight", choices=["weighted", "uniform"], default="weighted",
                     help="How to pick --kind when it's not given explicitly. 'weighted' "
                          "(default) uses Perilous Wilds p49's 1d12 distribution "
                          "(village 1-5, town 6-8, keep 9-11, city 12). 'uniform' picks "
                          "among the four with equal probability.")
    ap.add_argument("--name-only", action="store_true", help="Just generate a name")
    ap.add_argument("--culture", choices=ALL_CULTURES + ["any", "human", "halfling"],
                     default="madlib",
                     help="Name source: 'madlib' (default, this script's own word-bank "
                          "generator), 'country' (pastoral madlib variant)/'halfling' "
                          "(synonym), a specific culture (alone), 'any' (combined pool: "
                          "every culture, uniform), or 'human' (same as 'any' but "
                          "excluding elven/dwarven)")
    ap.add_argument("--show-gloss", action="store_true",
                     help="For Perilous Wilds cultures, append the book's English gloss, e.g. 'Toron (Tower)'")
    ap.add_argument("-n", "--count", type=int, default=1, help="How many to generate")
    ap.add_argument("--seed", type=int, default=None, help="Random seed, for reproducibility")
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                     help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    if args.seed is not None:
        print("Warning: Do not use --seed in a real game! If you did then re-read gameplay-loop.md now!")
        random.seed(args.seed)

    weighted = args.kind_weight == "weighted"
    for i in range(args.count):
        if args.name_only:
            print(gen_name(args.culture, args.show_gloss))
        else:
            print(gen_steading(args.kind, args.culture, args.show_gloss, weighted))
        if args.count > 1 and i < args.count - 1:
            print()
    print("Alert: Update gmsecrets yaml now !")


if __name__ == "__main__":
    main()
