#!/usr/bin/env python3
"""
NPC generator for Dungeon World.

Usage:
    python3 npc_gen.py                          # one full instant NPC (any ancestry)
    python3 npc_gen.py -n 5                      # five of them
    python3 npc_gen.py --ancestry elf            # name drawn from the elf list
    python3 npc_gen.py --ancestry hungarian-like --gender f   # gendered culture name
    python3 npc_gen.py --occupation               # add a rolled occupation
    python3 npc_gen.py --occupation --occ-category security
    python3 npc_gen.py --follower                # a Perilous Wilds follower instead
    python3 npc_gen.py --follower --ancestry dwarf
    python3 npc_gen.py --name-only               # just a name, no instinct/knack
    python3 npc_gen.py --no-traits                # skip the appearance/personality/quirk trait
    python3 npc_gen.py --full-traits               # roll all three traits instead of just one
    python3 npc_gen.py --seed 42                 # reproducible results

Ancestries: human, elf, dwarf, halfling, hungarian-like, yoruba-like,
finnish-like, indonesian-like, any (default: any)

The four "-like" cultures are gendered (use --gender m|f, or omit for
random) name lists for human NPCs who hail from a distinct invented
culture. Per the source material's own disclaimer: these are NOT real
words in the named language, just names built to loosely evoke one for
internal flavor consistency - don't mistake them for genuine Hungarian,
Yoruba, Finnish, or Indonesian names. Useful for e.g. assigning a
consistent "sounds vaguely Hungarian" flavor to a fictional nationality
or region.

Data source: names by ancestry, and the full 100-item Instincts and Knacks
tables, from the Dungeon World core rulebook's "Instant NPCs" appendix
(p392-395) plus the name lists scattered through the playbook chapters,
as condensed in this skill's references/npc-tools.md. The four "-like"
culture name lists and the NPC Occupation table are from The Perilous
Wilds (Revised Edition) by Jason Lutes, p56 and p72-75 - text licensed
CC BY-SA 3.0, reorganized here into data structures (not verbatim table
layout). Note: the Tamanarugan (Indonesian-like) masculine name column
is identical to the Finnish-like one in the source book itself - not a
transcription error here, just how it was printed. --follower's tables
are from the same book's "Lead the Way" chapter, p25-27 (follower
creation) - see references/follower-moves.md for that chapter's follower
*moves* (Recruit, Order Follower, etc.), not duplicated here.

A random appearance/personality/quirk trait (d12 category, d12 specific
prompt within it) is rolled for every NPC by default - regular or
follower - to give an instant hook beyond the instinct/knack, per common
GM-advice "give every NPC one memorable detail" guidance. Use
--no-traits to skip it, or --full-traits to roll all three categories
at once instead of just the one the d12 lands on.
"""
import argparse
import random
import sys

NAMES = {
    "human": [
        "Aeron", "Ajax", "Alester", "Ash", "Aytor", "Azra", "Bartleby", "Brianne",
        "Bryce", "Clarke", "Columbo", "Dahlia", "Diana", "Eddison", "Elizabeth",
        "Emory", "Finbar", "Gregor", "Hawthorn", "Jack", "Jared", "Kevan", "Lark",
        "Lily", "Maya", "Mildred", "Nestor", "Osmund", "Piotr", "Rickard", "Rowena",
        "Sabine", "Sayed", "Sule", "Viktor", "Warthog", "Xie", "Yasen", "Zamzomarr",
    ],
    "elf": [
        "Aegor", "Astrafel", "Cadeus", "Celion", "Cirdan", "Dagoliir", "Edrahil",
        "Eldar", "Galadiir", "Gwindor", "Idril", "Irime", "Luthien", "Melliandre",
        "Miriel", "Sinathel", "Taeros", "Thranduil", "Voronwe",
    ],
    "dwarf": [
        "Aelfar", "Azaghal", "Bjorn", "Bombur", "Brunhilda", "Drummond", "Dwalin",
        "Farin", "Freya", "Gerda", "Helga", "Janos", "Narvi", "Rurgosh", "Surtur",
        "Telchar",
    ],
    "halfling": [
        "Adelard", "Angelica", "Aubrey", "Baldwin", "Bartleby", "Becca", "Dunstan",
        "Estella", "Falco", "Finnegan", "Ivy", "Mab", "Olive", "Puck", "Robin",
        "Rose", "Serah", "Thistle", "Tobold",
    ],
    # Below: gendered "based loosely on <real-world language>" culture lists,
    # from The Perilous Wilds p72-75. dict with "m"/"f" keys instead of a
    # flat list - see gen_name().
    "hungarian-like": {
        "m": [
            "Agoston", "Arpad", "Attila", "Bognar", "Denes", "Edmond", "Erno",
            "Etele", "Ferdinand", "Florian", "Geza", "Gyula", "Hugo", "Karcsi",
            "Konrad", "Lazlo", "Lukas", "Marko", "Miklos", "Peti", "Robi",
            "Tamas", "Ronold", "Viktor", "Zoltan",
        ],
        "f": [
            "Abigel", "Aliz", "Amalia", "Andrea", "Aranka", "Csilla", "Edit",
            "Erzebet", "Gertrud", "Greta", "Iren", "Kamilla", "Lara", "Lia",
            "Lujza", "Matild", "Olga", "Otilia", "Panna", "Roza", "Terez",
            "Tunda", "Valeria", "Vilma", "Viola",
        ],
    },
    "yoruba-like": {
        "m": [
            "Adibemi", "Aboye", "Adegoke", "Ayokunle", "Babajide", "Babatunde",
            "Enitan", "Femi", "Kayin", "Kayode", "Lanre", "Lekan", "Mongo",
            "Nwachukwu", "Oban", "Ogun", "Olukayode", "Oluwalanni", "Oluwatoke",
            "Onipede", "Sijuade", "Toben", "Utiba", "Zaki", "Zoputan",
        ],
        "f": [
            "Abeni", "Ade", "Alaba", "Bolanle", "Bosade", "Daraja", "Fari",
            "Gbemisola", "Ife", "Ige", "Lewa", "Mojisola", "Monifa", "Olufemi",
            "Omolara", "Oni", "Orisa", "Osa", "Ronke", "Shanum", "Simisola",
            "Titlayo", "Yejide", "Yewande", "Zauna",
        ],
    },
    "finnish-like": {
        "m": [
            "Aatami", "Armas", "Arsi", "Arvi", "Eetu", "Hannu", "Heimo",
            "Ilkka", "Jorma", "Kaapo", "Kain", "Kauko", "Lari", "Manu",
            "Nuutti", "Petri", "Raimo", "Reima", "Risto", "Sakari", "Sampsa",
            "Seppo", "Taito", "Terho", "Vilppu",
        ],
        "f": [
            "Aija", "Aina", "Ainikki", "Heini", "Ilona", "Irja", "Jaana",
            "Kirsi", "Maija", "Marita", "Miina", "Mimmi", "Minja", "Mira",
            "Naemi", "Outi", "Pirjo", "Paivikki", "Riikka", "Saimi", "Suoma",
            "Suvi", "Tuula", "Vellamo", "Virpi",
        ],
    },
    "indonesian-like": {
        # Masculine list matches finnish-like in the source book itself.
        "m": [
            "Aatami", "Armas", "Arsi", "Arvi", "Eetu", "Hannu", "Heimo",
            "Ilkka", "Jorma", "Kaapo", "Kain", "Kauko", "Lari", "Manu",
            "Nuutti", "Petri", "Raimo", "Reima", "Risto", "Sakari", "Sampsa",
            "Seppo", "Taito", "Terho", "Vilppu",
        ],
        "f": [
            "Adah", "Bulan", "Candrakusuma", "Devi", "Hanjojo", "Iman",
            "Intan", "Laksmini", "Lestari", "Limijanto", "Marah", "Megawati",
            "Melati", "Nadiyya", "Ophrah", "Ramza", "Sapphiral", "Selah",
            "Suminten", "Tamar", "Tanjaya", "Tjokro", "Tri", "Wangi", "Zenze",
        ],
    },
}

# --- NPC Occupation table (Perilous Wilds p56) ------------------------------
# Roll 1d12 for category (ranges below), then 1d12 for the specific
# occupation within that category.

OCCUPATION_CATEGORIES = [
    (1, 1, "outsider"),
    (2, 3, "criminal"),
    (4, 6, "commoner"),
    (7, 7, "tradesperson"),
    (8, 8, "merchant"),
    (9, 9, "specialist"),
    (10, 10, "religious"),
    (11, 11, "security"),
    (12, 12, "authority"),
]

OCCUPATIONS = {
    "outsider": [
        "hermit/prophet", "fugitive/outlaw/exile", "fugitive/outlaw/exile",
        "barbarian", "barbarian", "beggar/vagrant/refugee",
        "beggar/vagrant/refugee", "herder/hunter/trapper",
        "herder/hunter/trapper", "diplomat/envoy", "rare humanoid",
        "otherworldly/arcane",
    ],
    "criminal": [
        "bandit/brigand/thug", "bandit/brigand/thug", "cutpurse/thief",
        "cutpurse/thief", "bodyguard/tough", "bodyguard/tough", "burglar",
        "con artist/swindler", "dealer/fence", "racketeer", "lieutenant",
        "boss/kingpin",
    ],
    "commoner": [
        "layabout/simpleton", "beggar/urchin", "laborer/gravedigger",
        "hunter/fisher", "hunter/fisher", "farmer/herder", "farmer/herder",
        "miner/quarrier", "servant/lackey", "driver/porter/sailor",
        "sentry/guard", "apprentice/adventurer",
    ],
    "tradesperson": [
        "musician/troubador", "artist/actor/acrobat",
        "cobbler/furrier/tailor", "weaver/basketmaker", "potter/carpenter",
        "mason/baker/chandler", "cooper/wheelwright", "tanner/ropemaker",
        "stablekeeper/herbalist", "vintner/jeweler", "inkeep/tavernkeep",
        "smith/armorer",
    ],
    "merchant": [
        "raw materials/supplies", "raw materials/supplies",
        "general goods/outfitter", "general goods/outfitter",
        "grain/livestock", "ale/wine/spirits", "clothing/jewelry",
        "weapons/armor", "spices/tobacco", "labor/slaves", "books/scrolls",
        "magic supplies/items",
    ],
    "specialist": [
        "clerk/scribe", "undertaker", "perfumer", "navigator/guide",
        "spy/diplomat", "cartographer", "locksmith/tinker",
        "architect/engineer", "physician/apothecary", "sage/scholar",
        "alchemist/astrologer", "inventor/wizard",
    ],
    "religious": [
        "heretic/apostate", "zealot", "mendicant/pilgrim",
        "mendicant/pilgrim", "acolyte/novice", "acolyte/novice",
        "monk/nun/cultist", "preacher/prophet", "missionary",
        "templar/protector", "priest/cult leader", "high priest",
    ],
    "security": [
        "militia", "militia", "scout/warden", "watch/patrol",
        "watch/patrol", "raw recruit", "foot soldier", "foot soldier",
        "archer", "officer/constable", "cavalry/knight", "hero/general",
    ],
    "authority": [
        "courier/messenger", "town crier", "tax collector",
        "clerk/administrator", "clerk/administrator", "armiger/gentry",
        "armiger/gentry", "magistrate/judge", "guildmaster",
        "lesser nobility", "greater nobility", "ruler/warlord",
    ],
}

INSTINCTS = [
    "To avenge", "To spread the good word", "To reunite with a loved one",
    "To make money", "To make amends", "To explore a mysterious place",
    "To uncover a hidden truth", "To locate a lost thing", "To kill a hated foe",
    "To conquer a faraway land", "To cure an illness", "To craft a masterwork",
    "To survive just one more day", "To earn affection", "To prove a point",
    "To be smarter, faster and stronger", "To heal an old wound",
    "To extinguish an evil forever", "To hide from a shameful fact",
    "To evangelize", "To spread suffering", "To prove worth", "To rise in rank",
    "To be praised", "To discover the truth", "To make good on a bet",
    "To get out of an obligation", "To convince someone to do their dirty work",
    "To steal something valuable", "To overcome a bad habit", "To commit an atrocity",
    "To earn renown", "To accumulate power", "To save someone from a monstrosity",
    "To teach", "To settle down", "To get just one more haul",
    "To preserve the law", "To discover", "To devour", "To restore the family name",
    "To live a quiet life", "To help others", "To atone", "To prove their worth",
    "To gain honor", "To expand their land", "To gain a title",
    "To retreat from society", "To escape", "To party", "To return home",
    "To serve", "To reclaim what was taken", "To do what must be done",
    "To be a champion", "To avoid notice", "To help a family member",
    "To perfect a skill", "To travel", "To overcome a disadvantage",
    "To play the game", "To establish a dynasty", "To improve the realm",
    "To retire", "To recover a lost memory", "To battle",
    "To become a terror to criminals", "To raise dragons",
    "To live up to expectations", "To become someone else",
    "To do what can't be done", "To be remembered in song", "To be forgotten",
    "To find true love", "To lose their mind", "To indulge",
    "To make the best of it", "To find the one", "To destroy an artifact",
    "To show them all", "To bring about unending summer", "To fly",
    "To find the six-fingered man", "To wake the ancient sleepers",
    "To entertain", "To follow an order", "To die gloriously", "To be careful",
    "To show kindness", "To not screw it all up", "To uncover the past",
    "To go where no man has gone before", "To do good", "To become a beast",
    "To spill blood", "To live forever", "To hunt the most dangerous game",
    "To hate", "To run away",
]

KNACKS = [
    "Criminal connections", "Muscle", "Skill with a specific weapon", "Hedge wizardry",
    "Comprehensive local knowledge", "Noble blood", "A one-of-a-kind item",
    "Special destiny", "Unique perspective", "Hidden knowledge", "Magical awareness",
    "Abnormal parentage", "Political leverage", "A tie to a monster", "A secret",
    "True love", "An innocent heart", "A plan for the perfect crime",
    "A one-way ticket to paradise", "A mysterious ore", "Money, money, money",
    "Divine blessing", "Immunity from the law", "Prophecy",
    "Secret martial arts techniques", "A ring of power", "A much-needed bag of taters",
    "A heart", "A fortified position", "Lawmaking", "Tongues", "A discerning eye",
    "Endurance", "A safe place", "Visions", "A beautiful mind", "A clear voice",
    "Stunning looks", "A catchy tune", "Invention", "Baking", "Brewing", "Smelting",
    "Woodworking", "Writing", "Immunity to fire", "Cooking", "Storytelling",
    "Ratcatching", "Lying", "Utter unremarkableness", "Mind-bending sexiness",
    "Undefinable coolness", "A way with knots", "Wheels of polished steel",
    "A magic carpet", "Endless ideas", "Persistence", "A stockpile of food",
    "A hidden path", "Piety", "Resistance to disease", "A library",
    "A silver tongue", "Bloodline", "An innate spell", "Balance", "Souls", "Speed",
    "A sense of right and wrong", "Certainty", "An eye for detail",
    "Heroic self-sacrifice", "Sense of direction", "A big idea",
    "A hidden entrance to the city", "The love of someone powerful",
    "Unquestioning loyalty", "Exotic fruit", "Poison", "Perfect memory",
    "The language of birds", "A key to an important door", "Metalworking",
    "Mysterious benefactors", "Steely nerves", "Bluffing", "A trained wolf",
    "A long-lost sibling, regained", "An arrow with your name on it", "A true name",
    "Luck", "The attention of supernatural powers", "Kindness", "Strange tattoos",
    "A majestic beard", "A book in a strange language", "Power overwhelming",
    "Delusions of grandeur", "The wind at his back and a spring in his step",
]


# --- Follower creation (Perilous Wilds p25-27, "Lead the Way" chapter) -----
# See references/follower-moves.md for the follower *moves* (Recruit, Order
# Follower, etc.) - this is just the character-creation side, wired up here
# because it reuses this script's name lists. Roll tables transcribed
# faithfully; a few steps are deliberately simplified per this skill's own
# design choice rather than modeled exactly - see gen_follower()'s docstring.

FOLLOWER_QUALITY = [
    # (lo, hi, value_str, label, tags_text, tags_num)
    (1, 3, "-1", "A liability", "+0 tags", 0),
    (4, 9, "+0", "Reasonably competent", "+1 tags", 1),
    (10, 11, "+1", "Fully capable", "+2 tags", 2),
    (12, 12, "+2", "An exceptional individual", "+4 tags", 4),
]

FOLLOWER_BACKGROUND = [
    # (lo, hi, label, effect_text_or_None, tag_effect)
    # tag_effect is a signed int, or "wise" for the one row that grants an
    # extra "-wise" tag instead of a plain count. "+meek" doesn't affect
    # tag count - it's informational text only, same as before.
    (1, 2, "Has lived a life of servitude and oppression", "+meek", 0),
    (3, 3, "Past their prime", "-1 to Quality, +1 wise", "wise"),
    (4, 5, "Has lived a life of danger", "+2 tags", 2),
    (6, 9, "Unremarkable", None, 0),
    (10, 10, "Has lived a life of privilege", "+1 tag", 1),
    (11, 11, "Specialist", "+1 to Quality, -2 tags", -2),
    # 12: "Roll 1d10+1 twice on this table" - handled in roll_follower_background().
]

# The 17 tags a follower can have beyond their "-wise" (Connected and Guide
# keep their book "( ___ )" blank as literal text - the GM fills in the
# specific place/steading/group when one gets rolled).
FOLLOWER_TAGS = [
    "Archer", "Athletic", "Beautiful", "Cautious", "Connected (___)",
    "Cunning", "Devious", "Group", "Guide (___)", "Hardy", "Healer",
    "Meek", "Magical", "Organized", "Self-sufficient", "Stealthy",
    "Warrior",
]

WISE_TAG_FULL = "___-wise - can roll +Quality to Spout Lore about ___ (GM fill in)"

FOLLOWER_INSTINCTS = [
    (1, 1, "Loot, pillage, and burn"),
    (2, 2, "Hold a grudge and seek payback"),
    (3, 3, "Question leadership or authority"),
    (4, 5, "Lord over others"),
    (6, 7, "Act impulsively"),
    (8, 9, "Give in to temptation"),
    (10, 11, "Slack off"),
    (12, 12, "Avoid danger or punishment"),
]

# (lo, hi, label) - also the source of the "other 7 costs" override list.
FOLLOWER_COSTS = [
    (1, 1, "Debauchery"),
    (2, 2, "Vengeance"),
    (3, 5, "Lucre"),
    (6, 7, "Renown"),
    (8, 9, "Glory"),
    (10, 10, "Affection"),
    (11, 11, "Knowledge"),
    (12, 12, "Good"),
]

FOLLOWER_HP = [
    (1, 3, "3", "Weak/frail/soft"),
    (4, 9, "6", "Able-bodied"),
    (10, 12, "9", "Tough/strong/hard"),
]

FOLLOWER_DAMAGE = [
    (1, 4, "d4", "Not very dangerous"),
    (5, 10, "d6", "Can defend themselves"),
    (11, 12, "d8", "Veteran fighter"),
]


# --- NPC Traits (appearance/personality/quirk grab-bag) --------------------
# Not from an official source - this skill's own addition, a generic
# "one memorable detail" table in the style of similar random-NPC-hook
# tables. Rolled for every NPC by default; see gen_npc()/gen_follower().

NPC_TRAIT_MAIN = [
    (1, 6, "appearance"),
    (7, 9, "personality"),
    (10, 12, "quirk"),
]

NPC_TRAIT_APPEARANCE = [
    (1, 1, "disfigured (missing teeth, eye, etc.)"),
    (2, 2, "lasting injury (bad leg, arm, etc.)"),
    (3, 3, "tattooed/pockmarked/scarred"),
    (4, 4, "unkempt/shabby/grubby"),
    (5, 5, "big/thick/brawny"),
    (6, 6, "small/scrawny/emaciated"),
    (7, 7, "notable hair (wild, long, none, etc.)"),
    (8, 8, "notable nose (big, hooked, etc.)"),
    (9, 9, "notable eyes (blue, bloodshot, etc.)"),
    (10, 10, "clean/well-dressed/well-groomed"),
    (11, 11, "attractive/handsome/stunning"),
    (12, 12, "roll twice"),
]

NPC_TRAIT_PERSONALITY = [
    (1, 1, "loner/alienated/antisocial"),
    (2, 2, "cruel/belligerent/bully"),
    (3, 3, "anxious/fearful/cowardly"),
    (4, 4, "envious/covetous/greedy"),
    (5, 5, "aloof/haughty/arrogant"),
    (6, 6, "awkward/shy/self-loathing"),
    (7, 7, "orderly/compulsive/controlling"),
    (8, 8, "confident/impulsive/reckless"),
    (9, 9, "kind/generous/compassionate"),
    (10, 10, "easygoing/relaxed/peaceful"),
    (11, 11, "cheerful/happy/optimistic"),
    (12, 12, "roll twice"),
]

NPC_TRAIT_QUIRK = [
    (1, 1, "insecure/racist/xenophobic"),
    (2, 2, "addict (sweets, drugs, sex, etc.)"),
    (3, 3, "phobia (spiders, fire, darkness, etc.)"),
    (4, 4, "allergic/asthmatic/chronically ill"),
    (5, 5, "skeptic/paranoid"),
    (6, 6, "superstitious/devout/fanatical"),
    (7, 7, "miser/pack-rat"),
    (8, 8, "spendthrift/wastrel"),
    (9, 9, "smart aleck/know-it-all"),
    (10, 10, "artistic/dreamer/delusional"),
    (11, 11, "naive/idealistic"),
    (12, 12, "roll twice"),
]


def _table_lookup(table, roll):
    for lo, hi, *rest in table:
        if lo <= roll <= hi:
            return rest[0] if len(rest) == 1 else rest


def _npc_trait_sub_roll(table, depth=0):
    """Roll on an NPC-trait sub-table; on 'roll twice' recurse (with a
    depth guard so a run of 12s can't recurse forever)."""
    if depth > 2:
        return _table_lookup(table, random.randint(1, 11))  # force non-12
    result = _table_lookup(table, random.randint(1, 12))
    if result == "roll twice":
        a = _npc_trait_sub_roll(table, depth + 1)
        b = _npc_trait_sub_roll(table, depth + 1)
        return f"{a} + {b}"
    return result


def roll_npc_trait(full=False):
    """Default: roll category (appearance/personality/quirk) + one prompt
    within it. full=True instead rolls one prompt in each category."""
    if full:
        app = _npc_trait_sub_roll(NPC_TRAIT_APPEARANCE)
        per = _npc_trait_sub_roll(NPC_TRAIT_PERSONALITY)
        qui = _npc_trait_sub_roll(NPC_TRAIT_QUIRK)
        return f"appearance: {app} | personality: {per} | quirk: {qui}"

    cat = _table_lookup(NPC_TRAIT_MAIN, random.randint(1, 12))
    table = {"appearance": NPC_TRAIT_APPEARANCE,
             "personality": NPC_TRAIT_PERSONALITY,
             "quirk": NPC_TRAIT_QUIRK}[cat]
    return f"{cat}: {_npc_trait_sub_roll(table)}"


def roll_follower_background():
    """Returns a list of (label, effect_text, tag_effect) rows - one entry
    normally, two if the roll is 12 (the book's own 'roll 1d10+1 twice'
    rule; that 2-11 range can't itself land on 12, so no recursion guard
    is needed)."""
    roll = random.randint(1, 12)
    if roll != 12:
        return [_table_lookup(FOLLOWER_BACKGROUND, roll)]
    first_roll = random.randint(1, 10) + 1
    second_roll = random.randint(1, 10) + 1
    return [_table_lookup(FOLLOWER_BACKGROUND, first_roll),
            _table_lookup(FOLLOWER_BACKGROUND, second_roll)]


def gen_follower_tags(quality_tags_num, background_rows):
    """Tracks the actual tag budget (Quality's base + Background's
    delta(s)) rather than just always suggesting a fixed number, and
    handles Background's "+1 wise" specially - it grants an *extra*
    "-wise" tag on top of the follower's normal mandatory one, not a
    generic tag-count point. Returns the list of output lines for the
    Tags section (not including the "Tags:" header itself)."""
    extra_wise_tags = 0
    tags = quality_tags_num
    for _, _, tag_effect in background_rows:
        if tag_effect == "wise":
            extra_wise_tags += 1
        else:
            tags += tag_effect
    tags = max(0, tags)

    lines = []
    if extra_wise_tags > 0:
        lines.append(WISE_TAG_FULL)
        for _ in range(extra_wise_tags - 1):
            lines.append("___-wise (background: wise +1)")

    if tags == 0 and extra_wise_tags == 0:
        lines.append("(no tags, too incompetent or specialized)")
        return lines

    if tags > 0:
        lines.append(WISE_TAG_FULL)  # the mandatory first tag, in addition to any extras above
        lines.extend(random.sample(FOLLOWER_TAGS, min(tags, len(FOLLOWER_TAGS))))
    lines.append("(GM can always replace tags as appropriate)")
    return lines


def gen_follower(ancestry="any", gender=None, traits=True, full_traits=False):
    """Generates a follower per Perilous Wilds p25-27."""
    name, actual_ancestry = gen_name(ancestry, gender)

    q_roll = random.randint(1, 12)
    q_value, q_label, q_tags_text, q_tags_num = _table_lookup(FOLLOWER_QUALITY, q_roll)

    background_rows = roll_follower_background()
    bg_parts = [f"{label} ({effect})" if effect else label
                for label, effect, _ in background_rows]
    background = " + ".join(bg_parts)
    if len(background_rows) == 2:
        background += " (rolled twice, per the '12' result)"

    tag_lines = gen_follower_tags(q_tags_num, background_rows)

    instinct_roll = random.randint(1, 12)
    instinct = _table_lookup(FOLLOWER_INSTINCTS, instinct_roll)

    cost_roll = random.randint(1, 12)
    cost = _table_lookup(FOLLOWER_COSTS, cost_roll)
    other_costs = [c for _, _, c in FOLLOWER_COSTS if c != cost]

    hp_roll = random.randint(1, 12)
    hp_value, hp_desc = _table_lookup(FOLLOWER_HP, hp_roll)

    dmg_roll = random.randint(1, 12)
    dmg_die, dmg_desc = _table_lookup(FOLLOWER_DAMAGE, dmg_roll)

    lines = [
        f"{name} ({actual_ancestry}) - Follower",
        f"  Quality: {q_value} ({q_label}, {q_tags_text})",
        f"  Background: {background}",
        "  Tags:",
    ]
    lines.extend(f"    {line}" for line in tag_lines)
    lines.extend([
        "  Moves: GM write moves according to follower type/skills",
        "  Starting Loyalty: 1 (+/- 1 depending on situation)",
        f"  Instinct: {instinct}",
        f"  Cost: {cost} (GM can override with one of: {', '.join(other_costs)})",
        f"  HP: {hp_value} ({hp_desc})",
        "  Armor: GM picks none=0, hide/leather=1, scale/chain=2, plate=3, shield=+1",
        f"  Damage: 1{dmg_die} ({dmg_desc}) - GM override 1d4/1d6/1d8 as needed",
        "  Load: 2 for human size, 1 smaller, 3 larger",
    ])
    if traits:
        lines.append(f"  Trait: {roll_npc_trait(full=full_traits)}")
    return "\n".join(lines)




def gen_name(ancestry, gender=None):
    if ancestry == "any":
        ancestry = random.choice(list(NAMES.keys()))
    entry = NAMES[ancestry]
    if isinstance(entry, dict):
        # Gendered culture list - pick m/f if not specified.
        g = gender if gender in ("m", "f") else random.choice(("m", "f"))
        return random.choice(entry[g]), ancestry
    return random.choice(entry), ancestry


def gen_occupation(category=None):
    if not category or category == "any":
        roll = random.randint(1, 12)
        for lo, hi, cat in OCCUPATION_CATEGORIES:
            if lo <= roll <= hi:
                category = cat
                break
    return category, random.choice(OCCUPATIONS[category])


def gen_npc(ancestry="any", name_only=False, gender=None,
            occupation=False, occ_category=None, traits=True, full_traits=False):
    name, actual_ancestry = gen_name(ancestry, gender)
    if name_only:
        return f"{name} ({actual_ancestry})"
    instinct = random.choice(INSTINCTS)
    knack = random.choice(KNACKS)
    lines = [
        f"{name} ({actual_ancestry})",
        f"  Instinct: {instinct}",
        f"  Knack:    {knack}",
    ]
    if occupation:
        category, occ = gen_occupation(occ_category)
        lines.append(f"  Occupation: {occ} ({category})")
    if traits:
        lines.append(f"  Trait:    {roll_npc_trait(full=full_traits)}")
    return "\n".join(lines)


HELP_LLM = """\
npc_gen.py - instant NPC / Perilous Wilds follower generator for Dungeon World.

USAGE
  npc_gen.py [-n N] [--ancestry A] [--gender m|f] [--name-only]
             [--occupation [--occ-category C]] [--follower]
             [--no-traits | --full-traits] [--seed N]

ANCESTRY (--ancestry, default: any)
  human | elf | dwarf | halfling | hungarian-like | yoruba-like |
  finnish-like | indonesian-like | any
  The four "-like" entries are gendered invented-culture name lists (use
  --gender m|f, random if omitted) - NOT real-language names, just built to
  evoke one for flavor consistency (per the source material's own disclaimer).

FLAGS
  -n, --count N     how many to generate (default 1)
  --gender m|f      only affects the four "-like" ancestries; random if omitted
  --name-only       just "Name (ancestry)", skip instinct/knack/trait
  --occupation      also roll an occupation (Perilous Wilds p56)
  --occ-category C  restrict occupation to one category (default: any) -
                     choices: outsider, criminal, commoner, tradesperson,
                     merchant, specialist, religious, security, authority
  --follower        generate a Perilous Wilds follower (p25-27) instead:
                     Quality/Background/Tags/Instinct/Cost/HP/Armor/Damage/
                     Load. Honors --ancestry/--gender for the name; ignores
                     --name-only/--occupation/--occ-category. For the Lead
                     the Way follower *moves* (Recruit, Order Follower, etc,
                     not duplicated here) see references/follower-moves.md.
  --no-traits       skip the appearance/personality/quirk trait rolled by
                     default for every NPC or follower
  --full-traits     roll all three trait categories (appearance + personality
                     + quirk) instead of just the one the d12 lands on
  --seed N          reproducible output - dev/debug only, NEVER during play

OUTPUT
  Regular NPC: "Name (ancestry)" then Instinct/Knack lines, plus Occupation
  if requested, plus Trait unless --no-traits. Follower: name/ancestry header
  then Quality/Background/Tags/Moves(blank, GM fills in)/Starting Loyalty/
  Instinct/Cost/HP/Armor(GM picks)/Damage/Load, plus Trait unless --no-traits.
  Multiple (-n/--count > 1) results are blank-line separated.
  Always ends with a reminder to update yaml files.

DATA SOURCES: ancestry names + Instincts/Knacks tables are the core rulebook's
"Instant NPCs" appendix (p392-395); the four "-like" culture name lists and
the Occupation table are Perilous Wilds (Revised) p56/p72-75, CC BY-SA 3.0;
--follower's tables are that book's "Lead the Way" chapter, p25-27. The
appearance/personality/quirk trait roll is this skill's own addition, not
from either source book.

EXAMPLES
  npc_gen.py -n 3
  npc_gen.py --ancestry elf --name-only
  npc_gen.py --ancestry hungarian-like --gender f
  npc_gen.py --occupation --occ-category security
  npc_gen.py --follower --ancestry dwarf
  npc_gen.py --full-traits
"""


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return

    ap = argparse.ArgumentParser(description="Generate Dungeon World NPCs.")
    ap.add_argument("--ancestry", choices=list(NAMES.keys()) + ["any"], default="any",
                     help="Restrict the name to one ancestry (default: any)")
    ap.add_argument("--gender", choices=["m", "f"], default=None,
                     help="For gendered '-like' culture ancestries only; random if omitted")
    ap.add_argument("-n", "--count", type=int, default=1, help="How many NPCs to generate")
    ap.add_argument("--name-only", action="store_true",
                     help="Just a name, skip the instinct/knack")
    ap.add_argument("--occupation", action="store_true",
                     help="Also roll an occupation (Perilous Wilds p56)")
    ap.add_argument("--occ-category", choices=list(OCCUPATIONS.keys()) + ["any"],
                     default="any", help="Restrict occupation to one category (default: any)")
    ap.add_argument("--follower", action="store_true",
                     help="Generate a Perilous Wilds follower (p25-27) instead of a "
                          "regular instant NPC - Quality/Background/Tags/Instinct/Cost/"
                          "HP/Armor/Damage/Load. Honors --ancestry/--gender for the "
                          "name; ignores --name-only/--occupation/--occ-category.")
    ap.add_argument("--no-traits", action="store_true",
                     help="Skip the appearance/personality/quirk trait rolled by default "
                          "for every NPC (regular or --follower)")
    ap.add_argument("--full-traits", action="store_true",
                     help="Roll all three trait categories (appearance + personality + "
                          "quirk) instead of just the one category the d12 lands on")
    ap.add_argument("--seed", type=int, default=None, help="Random seed, for reproducibility")
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                     help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    if args.seed is not None:
        print("Warning: Do not use --seed in a real game! If you did then re-read gameplay-loop.md now!")
        random.seed(args.seed)

    traits = not args.no_traits
    for i in range(args.count):
        if args.follower:
            print(gen_follower(args.ancestry, args.gender,
                                traits=traits, full_traits=args.full_traits))
        else:
            print(gen_npc(args.ancestry, args.name_only, args.gender,
                           args.occupation, args.occ_category,
                           traits=traits, full_traits=args.full_traits))
        if args.count > 1 and i < args.count - 1:
            print()
    print("Reminder: update gm and character yaml files now!")


if __name__ == "__main__":
    main()
