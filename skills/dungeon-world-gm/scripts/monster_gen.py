#!/usr/bin/env python3
"""
Monster picker and stat-block builder for Dungeon World.

By default this returns *official* monsters from the core rulebook bestiary
(assets/monsters.json, 154 monsters across 9 settings), complete with their
written descriptions, instincts and moves. A setting tag is always required -
a monster drawn from the whole book at random rarely makes sense in play.

Custom monsters (the "pick one from each category" quick builder from
references/treasure-and-monster-building.md) are still available behind
--custom, but they come back as a stat skeleton with the flavour left blank,
which is much harder to run well. Prefer the official bestiary.

Usage:
    python3 monster_gen.py                                # list the setting tags
    python3 monster_gen.py --setting-info cavern          # full setting description
    python3 monster_gen.py cavern                         # one random cavern monster
    python3 monster_gen.py cavern --party-levels 4        # ...scaled to the party
    python3 monster_gen.py undead --random 3 --party-levels 12
    python3 monster_gen.py woods --all --party-levels 8   # everything that fits
    python3 monster_gen.py --custom                       # quick builder, all rolled
    python3 monster_gen.py --custom --org horde --theme woods

Monsters are emitted as compact JSON on one line. Pass -p/--pretty for a
plain-text dump (labels, colons, parentheses; not JSON) when debugging by
hand. All warnings and reminders go to stderr so stdout stays parseable.
"""
import argparse
import json
import math
import random
import re
import sys
import textwrap
from pathlib import Path

from _util import apply_seed, force_utf8_stdio

force_utf8_stdio()

import _treasure  # sibling module - the treasure table and its objects

BESTIARY = Path(__file__).resolve().parent.parent / "assets" / "monsters.json"
LEXICON = Path(__file__).resolve().parent.parent / "assets" / "monster_words.json"

# Word categories every theme must carry. Kept here rather than in the asset so
# the script fails loudly on a malformed lexicon instead of quietly dropping a
# category; tools/validate_skill.py checks the asset against this same list.
WORD_CATEGORIES = (
    "substance",
    "bodypart",
    "action",
    "texture",
    "drive",
    "sound",
    "quality",
    "evocative",
)

# How many capabilities to offer in special_quality. It is a menu, not a
# decision: picking one for you would make this the only seeded field that
# commits, when everything else here hands over options and lets the model
# choose. Three is enough to choose between without being a list to wade
# through.
QUALITY_OPTIONS = 3

# How many of each to hand over. Enough to choose from, few enough that the
# model is not just picking the first one it reads.
SEEDS_PER_CATEGORY = 4

DEADLINESS_TIERS = ("d4", "d6", "d8", "d10", "d12", "beyond", "cataclysmic")

# --- behaviour scales -----------------------------------------------------
#
# These stay in Python rather than the lexicon: they are semantics, not
# vocabulary. FLEE_BY_AGGRESSION in particular is a derivation, not a table to
# roll on, and the nudge logic below indexes these lists positionally.

AGGRESSION = [
    (-2, "cowardly", "runs like a deer; fights only when cornered"),
    (-1, "meek", "keeps its distance; flees given any chance"),
    (0, "ambivalent", "stands its ground but will not chase"),
    (1, "cautious", "waits in ambush and picks its moment"),
    (2, "aggressive", "attacks with little patience"),
    (3, "berserk", "attacks relentlessly and does not break off"),
    (4, "horror", "exists to kill its target; nothing distracts it"),
]

# Derived from aggression, not rolled - the spec in
# references/treasure-and-monster-building.md defines flee behaviour per
# aggression level, so rolling it separately would manufacture contradictions
# the spec has already resolved.
FLEE_BY_AGGRESSION = {
    -2: "flees whenever it can; fights only when cornered",
    -1: "flees whenever it can; fights only when cornered",
    0: "stands its ground unless clearly outmatched",
    1: "may flee or hide if the fight turns against it",
    2: "may flee or hide only if overwhelmed",
    3: "never flees",
    4: "never flees and cannot be drawn off its target",
}

HIDE_OR_RUN = [
    ("ambusher", "hides in order to attack, never to escape"),
    ("camouflaged", "true concealment; can go unseen in the open"),
    ("terrain-hider", "gets behind or under cover to escape, not to stalk"),
    ("bolter", "runs in the open; makes no attempt to hide"),
    ("neither", "does not hide and does not run"),
]

INTELLIGENCE = [
    (-1, "no reflexes", "jellyfish"),
    (0, "reflex automaton", "ant: sense stimulus, react"),
    (1, "barely reflexive", "eats its own young"),
    (2, "clever reptile", "rat"),
    (3, "average mammal", "cat or dog"),
    (4, "smart mammal", "monkey"),
    (5, "smartest animal", "great ape"),
    (6, "dim human-like", "goblin"),
    (7, "primitive human-like", ""),
    (8, "human baseline", ""),
    (9, "human or better", "use ordinary INT from here up"),
]

INTIMIDATION = [
    (-1, "soothing", "friendly sounds and gestures even while killing you"),
    (0, "silent", "no display at all, like a constricting snake"),
    (1, "low-key", "quiet aggressive noises and posturing"),
    (2, "wolf-like", "growls and bares its teeth"),
    (3, "loud", "roaring and performative slashing"),
    (4, "screaming", "screams, roars, attacks the air in front of it"),
    (5, "frenzied", "extreme screeching and slashing at nothing"),
    (6, "horror show", "maximum chaotic screaming, roaring and violence"),
]

TERRITORIALITY = [
    ("lair-bound", "defends one place; leaving its ground ends the fight"),
    ("patrol", "walks a route, so it can be timed and avoided"),
    ("pursuer", "claims no ground but follows what it has marked"),
    ("wanderer", "opportunistic, with nothing to defend"),
    ("nomadic", "moves with its group, following food"),
]

SENSORY = [
    ("sight", "keen eyes; fooled by darkness and by stillness"),
    ("hearing", "hunts by sound; fooled by silence and misdirection"),
    ("smell", "tracks by scent; fooled by water and strong odours"),
    ("vibration", "feels movement through ground or water; fooled by stillness"),
    ("heat", "senses warmth; fooled by cold, confused by fire"),
    ("echolocation", "sounds the space out; fooled by silence and by noise"),
    ("magic-sense", "feels enchantment and life; blind to the purely mundane"),
]

POST_INJURY = [
    ("flees when hurt", "breaks off once meaningfully wounded"),
    ("cautious when hurt", "withdraws, circles, tries again"),
    ("calls for help", "signals or summons others once wounded"),
    ("fights harder", "wounded-animal fury; worse the closer it is to death"),
    ("indifferent", "damage does not change its behaviour until it drops"),
]

# --- form: morphology and physiology ---------------------------------------
#
# What the thing IS, as against how hard it hits (the stat block) and how it
# acts (the behaviour block). Without a body the model narrates "the creature
# moves toward you and attacks", and a rolled behaviour is unreadable on its
# own - hide_or_run "bolter" means something entirely different for a kangaroo
# than for a worm.
#
# Offered as a MENU, not rolled and committed, on the same contract as
# special_quality_options: the generator supplies material, the model decides.
# A few more words of output is cheaper than a re-rolled tool call, and it lets
# a GM fit the monster to the scene without starting over.
#
# Because nothing here commits, form deliberately does NOT feed behaviour_bias.
# An echolocating blob is not a bug to engineer around - the model simply picks
# whichever offered form suits the sensory result it already has, which is what
# having a menu is for.
#
# Morphology is SHAPE AND LOCOMOTION ONLY, never ecology. "worm" means shaped
# like a worm and moving by peristalsis, not living in soil; "bat" means flying
# mammal - fur and skin wings - not caves and echolocation; "snake" means
# elongate and slithering, not venom or even scales. Ecology already has axes
# of its own (SENSORY, TERRITORIALITY), and letting morphology imply it would
# contradict axes that have already committed.

FORM_OPTIONS = 3

# How much a theme's favour list raises the odds of an option. A multiplier and
# not a filter: a favour list says "more of this here", never "only this here".
FAVOUR_BOOST = 4.0

# Past this many limbs nobody counts. "47 legs" is not something anyone
# perceives, so the figure is reported as a magnitude band instead.
LIMB_COUNTABLE = 12
LIMB_BANDS = ("dozens of", "hundreds of", "thousands of")

# What a body plan's limbs are called. "2 limbs" undercounts a biped, which has
# two legs and its forelimbs free; a squid does not have legs at all. Bodies
# with no earthly analogue keep the vague word, because that is the honest one.
LIMB_NOUN = {
    "tentacled": "tentacles",
    "buoyant flyer": "limbs",
    "magical floater": "limbs",
    "geometric": "limbs",
    "exotic": "limbs",
    "blob": "limbs",
}
DEFAULT_LIMB_NOUN = "legs"

# Drawn from whenever a body plan does not fix its own covering.
INTEGUMENT_POOL = (
    "fur", "coarse hair", "hide", "bare skin", "slick skin", "scales",
    "chitin", "feathers", "quills", "shell plate", "bone plate",
    "stone plating", "crystal facets", "bark", "moss and creeper",
    "slime", "beaten metal", "no covering at all",
)

# (label, shape, limb spec, integument spec)
#
# Integument is a property of the body plan rather than an axis of its own: a
# bird is always feathered, a snake is snakeskin four times in five, a
# quadruped could be anything. One spec covers all three cases -
# (covering, probability), where 1.0 always holds and a fraction holds that
# often and otherwise draws from the pool; None always draws from the pool.
#
# Limb specs: ("fixed", n), ("range", lo, hi), ("weighted", {n: weight}) where
# the key "many" means an uncountable band, and ("open",) for bodies with no
# earthly analogue, which may have anything from none to uncountable.
MORPHOLOGY = [
    ("quadruped", "four-legged walker, built like a wolf or a bear",
     ("fixed", 4), None),
    ("bipedal walker", "upright on two legs, forelimbs free",
     ("fixed", 2), None),
    ("bipedal hopper", "two-legged bounder, kangaroo-like; crosses ground in leaps",
     ("fixed", 2), None),
    ("worm", "limbless cylinder moving by peristalsis",
     ("fixed", 0), ("wormskin", 0.8)),
    ("snake", "elongate and slithering",
     ("fixed", 0), ("snakeskin", 0.8)),
    ("fish", "fusiform swimmer driven by its own body, finned",
     ("fixed", 0), ("scales and slick skin", 0.8)),
    ("bird", "winged biped",
     ("fixed", 2), ("feathers", 1.0)),
    ("bat", "flying mammal - skin wings stretched on long fingers",
     ("fixed", 2), ("hide and fur", 1.0)),
    ("flying lizard", "winged reptile, leathery and long-tailed",
     ("fixed", 2), ("scales", 1.0)),
    ("insectoid", "segmented body carried on jointed legs",
     ("weighted", {6: 40, 8: 30, 9: 6, 10: 6, 11: 5, 12: 5, "many": 8}),
     ("chitin", 0.8)),
    ("spider", "compact body slung between long jointed legs",
     ("fixed", 8), ("chitin", 0.8)),
    ("many-legged crawler", "long segmented ribbon of a body, centipede-like",
     ("weighted", {12: 15, "many": 85}), ("chitin", 0.8)),
    ("symmetric multipod", "radially symmetric; no front and no back",
     ("range", 3, 12), None),
    ("tentacled", "squid- or octopus-like, boneless grasping arms",
     ("weighted", {4: 8, 5: 6, 6: 20, 8: 30, 10: 20, 12: 10, "many": 6}),
     ("squidlike skin", 0.8)),
    ("blob", "amorphous puddle or ball with no fixed shape at all",
     ("fixed", 0), ("slime", 0.8)),
    ("buoyant flyer", "drifts and bobs, gas-filled or lighter than air",
     ("open",), None),
    ("magical floater", "hangs in the air by no visible means",
     ("open",), None),
    ("geometric", "impossible solid - flat faces and sharp corners, or a "
                  "sphere, spheroid, prism or platonic solid",
     ("open",),
     ("flat plastic-metal sheen, closer to something rendered than grown", 0.8)),
    ("exotic", "no earthly analogue; build it out of the seed words",
     ("open",), None),
]

# (label, note, weight). Animal 50, plant 20, the remaining ten sharing 30, so
# a typical menu reads "animal, plant, something stranger" rather than three
# things nobody can picture.
PHYSIOLOGY = [
    ("animal biology", "ordinary flesh, blood and bone; it bleeds and it starves", 50),
    ("plant biology", "grown rather than born; sap, fibre and root", 20),
    ("magical biology", "alive, but beyond physical law (Magical)", 3),
    ("alien biology", "alive by rules nobody here has worked out", 3),
    ("undead", "was alive once and is not now", 3),
    ("magic construct", "made, not born, and animated by magic (Construct)", 3),
    ("mechanical construct", "made, not born, and driven by mechanism (Construct)", 3),
    ("immaterial spirit", "presence without substance; no body to speak of", 3),
    ("mineral-based", "stone or metal that lives", 3),
    ("extraplanar", "not of this world (Planar)", 3),
    ("elemental", "fire, water, air or earth given a will", 3),
    ("divine", "of the gods, for good or for ill (Divine)", 3),
]

# The escape route. If neither grounded option comes up in the three, one is
# appended, so a menu never arrives all-exotic with nothing ordinary to fall
# back to.
MUNDANE_PHYSIOLOGY = (("animal biology", 70), ("plant biology", 30))

# Traits settle these outright; see derive_form. Only traits the quick builder
# actually offers can appear here - TRAITS has no `magical` or `planar` key,
# those being bestiary tags rather than builder options, so they cannot serve
# as overrides however well they would map.
MORPHOLOGY_BY_TRAIT = {"noanatomy": "blob"}
ANIMATED_CONSTRUCT = (("magic construct", 70), ("mechanical construct", 30))

# A nudge shifts which end of a scale is likely, never which ends are possible.
# Every option keeps at least MIN_WEIGHT, so a huge fearsome thing can still
# roll timid and a coward can still posture like a horror - those combinations
# are the interesting ones, and the model can reconcile them.
MIN_WEIGHT = 0.25
DISTANCE_PENALTY = 0.18

# Weights for rolling unset categories. Uniform made one monster in five
# magically armoured and one in four huge, which reads as a parade of
# exceptions.
#
# These are BASE picks, and they are deliberately lower than the target: the
# Shield, No-anatomy and Skill-in-defense options each add +1 on top, so the
# armor a monster ends up with runs a step or so above what is rolled here.
# Tuned so the FINAL spread lands near the bestiary's own (0:18 1:40 2:20
# 3:11 4:9), with magical armor held down around 5% rather than the book's 9%
# so it stays a find rather than a fixture. Measure the final spread, not
# these numbers, if you retune.
ARMOR_WEIGHTS = {"none": 30, "leather": 43, "mail": 15, "steel": 9, "magical": 3}
SIZE_WEIGHTS = {"small": 40, "large": 28, "tiny": 20, "huge": 12}

# Organization drives the damage die (horde d6 < group d8 < solitary d10), so
# it is weighted down as power goes up, on the same principle. Note the
# bestiary runs the other way - 46% of its ENTRIES are solitary - but an entry
# is not an encounter: one solitary monster is one creature, where one horde
# entry is a dozen. Weighted for what a single rolled monster should look like.
ORG_WEIGHTS = {"horde": 40, "group": 35, "solitary": 25}

# Monte Carlo cap when hunting for a difficulty target. Uniform rolls are used
# for the search - deliberately not the weights above, because making powerful
# stats rare would make a powerful target slow to hit for no benefit.
DIFFICULTY_ATTEMPTS = 4000

# The bestiary's `difficulty` is a per-CREATURE score. How many you field is the
# GM's call, so the filter answers one question - "is a single one of these too
# much for this party?" - and that is a CEILING, not a band.
#
# It is deliberately not a window. An earlier version filtered on a 2L..8L band
# and was wrong: options slid instead of accumulating, so a level-10 party could
# not be offered a bandit (the whole `folk` setting emptied out at high level)
# while a starting party lost Skeletons. A strong party can always fight weak
# things; they are just easy, which is what SUGGESTED_NUMBER below is for.
#
# ceiling = CEILING_PER_LEVEL * L, where L is the SUM of the party's character
# levels (four level-1 PCs -> L=4). At k=4 a starting party gets Skeleton,
# Zombie, Mohrg and Nightwing out of `undead`; a Lich (99.84) needs L=25, i.e.
# four level-6 PCs. Raise it to loosen, lower it to tighten.
CEILING_PER_LEVEL = 4

# How many of a thing it is reasonable to field at once, by organization.
# Caps the suggested number: seven "Solitary" ghosts is not a Solitary monster
# any more, whatever the arithmetic says.
ORG_MAX_COUNT = {"horde": 12, "group": 5, "solitary": 1}
DEFAULT_MAX_COUNT = 1

# How hard each end of the suggested range is meant to be, as a share of the
# party's ceiling. "max" is the ceiling itself - as much as the party can take -
# so it is emphatically NOT the recommended number; "typical" is.
ENCOUNTER_WEIGHTS = (("min", 0.4), ("typical", 0.7), ("max", 1.0))

# --solo-threat keeps monsters that carry at least this share of the party's
# ceiling on their own. Not "needs exactly one to reach the ceiling": the
# ceiling is the most a party can survive, so by that test even a Lich (99.84
# against a level-10 party's ceiling of 160) counts as needing two, and the
# flag would empty the whole setting. Half the ceiling is already a serious
# fight for one creature.
SOLO_THREAT_FRACTION = 0.5

DIE_LADDER = [4, 6, 8, 10, 12]

ORG = {
    "horde": {"hp": 3, "die": 6, "label": "Horde (large groups)"},
    "group": {"hp": 6, "die": 8, "label": "Group (small groups)"},
    "solitary": {"hp": 12, "die": 10, "label": "Solitary"},
}

SIZE = {
    "tiny": {"dmg_mod": -2, "hp_mod": 0, "range": "Hand", "label": "Tiny (cat or smaller)"},
    "small": {"dmg_mod": 0, "hp_mod": 0, "range": "Close", "label": "Small/human-sized"},
    "large": {"dmg_mod": 1, "hp_mod": 4, "range": "Reach", "label": "Large (horse-sized)"},
    "huge": {"dmg_mod": 3, "hp_mod": 8, "range": "Reach", "label": "Huge (elephant+)"},
}

ARMOR = {"none": 0, "leather": 1, "mail": 2, "steel": 3, "magical": 4}

KNOWN_FOR = {
    "strength": "Unrelenting strength (+2 damage, Forceful)",
    "offense": "Skill in offense (roll damage twice, take the better)",
    "defense": "Skill in defense (+1 armor)",
    "deft": "Deft strikes (+1 piercing)",
    "endurance": "Uncanny endurance (+4 HP)",
}

ARMAMENTS = {
    "vicious": "Vicious & obvious (+2 damage)",
    "weak": "Small & weak (-1 die size)",
    "metal": "Can cut through metal (2 piercing, Messy)",
    "ignores": "Ignores armor entirely",
}

TRAITS = {
    "shield": "Bears a shield (Cautious, +1 armor)",
    "noanatomy": "No discernible anatomy (+1 armor, +3 HP)",
    "divine": "Favored by the gods (Divine, bonus per --divine-bonus)",
    "animated": "Animated beyond biology (+4 HP)",
    "devious": "Primary danger isn't wounds (Devious, -1 die size)",
    "ancient": "Ancient (species) (+1 die size)",
    "abhors": "Abhors violence (roll damage twice, take the worse)",
    "stealthy": "Stealthy",
    "organized": "Organized",
    "intelligent": "Intelligent",
    "terrifying": "Terrifying",
}

DESCRIPTIVE_ONLY = {"stealthy", "organized", "intelligent", "terrifying"}

# Mirrors tools/extract_monsters.py's DIE_FACTOR/compute_difficulty so a custom
# monster carries a score on the same scale as the bestiary and can be compared
# against a --party-levels band. Kept in sync by hand; the two live in different
# trees because tools/ is not shipped inside the skill.
DIE_FACTOR = {4: 0.5, 6: 0.8, 8: 1.0, 10: 1.2, 12: 1.5}

# The 1-18 table itself lives in assets/treasure.json and is reached through
# _treasure - idea_gen.py needs the same entries for treasure that no monster
# owns, and the copy that used to sit here had already drifted from that one.
# What stays here is the part that is genuinely monster-specific: rolling the
# creature's own damage die, and the tag bonuses below.

# 15, 16 and 17 each give their own result AND send you back for another roll.
MAX_REROLLS = 5  # a d12 with +1d4s cannot realistically chain, but do not hang

# Bonus-dice triggers that exist as monster tags in the bestiary. The rulebook
# also lists "far from home", "lord over others" and "ancient/noteworthy",
# which are GM judgement rather than tags, so they are not applied here.
TREASURE_TAG_EFFECTS = {
    "hoarder": ("advantage", "Hoarder: rolled the damage die twice, took the higher"),
    "magical": ("note", "Magical: add something strange, possibly magical"),
    "divine": ("note", "Divine: add a sign of a deity"),
    "planar": ("note", "Planar: add something otherworldly"),
}


# --- bestiary -------------------------------------------------------------


def load_bestiary():
    if not BESTIARY.is_file():
        sys.exit("error: bestiary not found at {}".format(BESTIARY))
    try:
        with BESTIARY.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        sys.exit("error: cannot read {}: {}".format(BESTIARY, exc))


def load_lexicon():
    if not LEXICON.is_file():
        sys.exit("error: seed lexicon not found at {}".format(LEXICON))
    try:
        with LEXICON.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        sys.exit("error: cannot read {}: {}".format(LEXICON, exc))


def theme_names(lexicon):
    return sorted(k for k in lexicon.get("themes", {}) if not k.startswith("_"))


def resolve_themes(lexicon, spec):
    """'cavern,undead' -> a merged word pool. Unknown tags are fatal."""
    themes = lexicon.get("themes", {})
    wanted = [t.strip().lower() for t in (spec or "generic").split(",") if t.strip()]
    if not wanted:
        wanted = ["generic"]

    unknown = [t for t in wanted if t not in themes]
    if unknown:
        sys.exit(
            "error: unknown theme(s) %s. Known: %s"
            % (", ".join(repr(u) for u in unknown), ", ".join(theme_names(lexicon)))
        )

    merged = {category: [] for category in WORD_CATEGORIES}
    for name in wanted:
        for category in WORD_CATEGORIES:
            for word in themes[name].get(category, []):
                if word not in merged[category]:
                    merged[category].append(word)
    return wanted, merged


def deadliness_tier(die, dmg_bonus, advantage, special_count):
    """Where this monster sits on the naming register.

    Bump rules come from references/treasure-and-monster-building.md: +2 or
    more damage bumps a tier, best-of-two bumps again, and defeat-resisting or
    offence-boosting specials bump once more.
    """
    try:
        index = DIE_LADDER.index(die)
    except ValueError:
        index = len(DIE_LADDER) - 1
    if dmg_bonus >= 2:
        index += 1
    if advantage:
        index += 1
    if special_count >= 2:
        index += 1
    return DEADLINESS_TIERS[min(index, len(DEADLINESS_TIERS) - 1)]


def seed_words(lexicon, pool, tier):
    """A handful from each category, plus the deadliness register."""
    picked = {}
    for category in WORD_CATEGORIES:
        words = pool.get(category) or []
        picked[category] = random.sample(words, k=min(SEEDS_PER_CATEGORY, len(words)))
    ladder = lexicon.get("deadliness", {}).get(tier) or []
    picked["deadliness"] = {
        "tier": tier,
        "words": random.sample(ladder, k=min(SEEDS_PER_CATEGORY, len(ladder))),
    }
    return picked


def nudged_choice(options, bias=0.0):
    """Pick from a scale, leaning toward one end without ever excluding the other.

    `bias` is an offset in index units applied to the centre of the scale. Every
    option keeps at least MIN_WEIGHT, so no outcome is ever unreachable - which
    is the point: an inconsistent-looking monster is usually a more interesting
    one, and the model can always reconcile or override it.
    """
    target = (len(options) - 1) / 2.0 + bias
    weights = [
        max(MIN_WEIGHT, 1.0 - DISTANCE_PENALTY * abs(i - target))
        for i in range(len(options))
    ]
    return random.choices(options, weights=weights, k=1)[0]


def behaviour_bias(size, die, org, traits, known_for):
    """Small stat-derived leanings, in index units. Deliberately gentle."""
    traits = set(traits or [])
    bias = {axis: 0.0 for axis in
            ("aggression", "intimidation", "intelligence", "territoriality",
             "post_injury", "hide_or_run", "sensory")}

    if size == "huge":
        bias["aggression"] += 1.0
        bias["intimidation"] += 1.0
    elif size == "large":
        bias["aggression"] += 0.5
    elif size == "tiny":
        bias["aggression"] -= 1.0
        bias["hide_or_run"] -= 0.5

    if die >= 10:
        bias["intimidation"] += 0.5
    elif die <= 4:
        bias["aggression"] -= 0.5

    if "terrifying" in traits:
        bias["intimidation"] += 1.5
    if "intelligent" in traits:
        bias["intelligence"] += 3.0
    if "organized" in traits:
        bias["intelligence"] += 1.0
    if "stealthy" in traits:
        bias["hide_or_run"] -= 1.0
    if "devious" in traits:
        bias["intelligence"] += 1.0
    if "animated" in traits or "noanatomy" in traits:
        bias["post_injury"] += 1.5
    if "abhors" in known_for or "abhors" in traits:
        bias["aggression"] -= 2.0

    if org == "solitary":
        bias["territoriality"] -= 1.0
    elif org == "horde":
        bias["intelligence"] -= 1.0
        bias["territoriality"] += 1.0

    return bias


def roll_behaviour(size, die, org, traits, known_for):
    bias = behaviour_bias(size, die, org, traits, known_for)

    aggression = nudged_choice(AGGRESSION, bias["aggression"])
    intelligence = nudged_choice(INTELLIGENCE, bias["intelligence"])
    intimidation = nudged_choice(INTIMIDATION, bias["intimidation"])
    hide = nudged_choice(HIDE_OR_RUN, bias["hide_or_run"])
    territory = nudged_choice(TERRITORIALITY, bias["territoriality"])
    sense = nudged_choice(SENSORY, bias["sensory"])
    injury = nudged_choice(POST_INJURY, bias["post_injury"])

    def scaled(entry):
        value, label, note = entry
        out = {"value": value, "label": label}
        if note:
            out["note"] = note
        return out

    def named(entry):
        label, note = entry
        return {"label": label, "note": note}

    return {
        "note": (
            "Rolled at random and only lightly steered by the stats. Disregard "
            "and rewrite any of these to fit the situation - a combination that "
            "looks inconsistent is usually the interesting one, not a mistake."
        ),
        "aggression": scaled(aggression),
        "flee": FLEE_BY_AGGRESSION[aggression[0]],
        "hide_or_run": named(hide),
        "intelligence": scaled(intelligence),
        "intimidation": scaled(intimidation),
        "territoriality": named(territory),
        "sensory": named(sense),
        "post_injury": named(injury),
    }


def _weighted_label(pairs):
    """Pick a label from ((label, weight), ...)."""
    return random.choices([p[0] for p in pairs],
                          weights=[p[1] for p in pairs], k=1)[0]


def favoured_sample(entries, favour, k, weight_of=None):
    """Draw k distinct entries, leaning toward a favoured subset.

    The nominal counterpart to nudged_choice: that one weights by distance
    along an ordered scale, which is meaningless here - a cavern favours worm
    AND crawler AND blob, at indices with no relation to one another. Favour
    multiplies the odds and never gates the pool, so nothing is unreachable,
    which is the same contract every other axis in this script keeps.
    """
    favour = set(favour or ())
    pool = list(entries)
    weights = [
        (weight_of(entry) if weight_of else 1.0)
        * (FAVOUR_BOOST if entry[0] in favour else 1.0)
        for entry in pool
    ]
    chosen = []
    for _ in range(min(k, len(pool))):
        index = random.choices(range(len(pool)), weights=weights, k=1)[0]
        chosen.append(pool.pop(index))
        weights.pop(index)
    return chosen


def roll_limbs(spec, noun=DEFAULT_LIMB_NOUN):
    """A body plan's limb count, as text. Most plans fix it; a few genuinely
    vary. Past LIMB_COUNTABLE it stops being a count and becomes a magnitude."""
    kind = spec[0]
    if kind == "fixed":
        count = spec[1]
    elif kind == "range":
        count = random.randint(spec[1], spec[2])
    elif kind == "weighted":
        table = spec[1]
        count = random.choices(list(table), weights=list(table.values()), k=1)[0]
    else:  # "open" - no earthly analogue, so anything from none to uncountable
        count = random.choices(
            [0, 1, 2, 3, 4, 5, 6, 8, 10, LIMB_COUNTABLE, "many"],
            weights=[14, 6, 10, 8, 10, 6, 8, 6, 5, 4, 8], k=1)[0]

    if count == "many":
        return "%s %s" % (random.choice(LIMB_BANDS), noun)
    if count == 0:
        return "no %s" % noun
    if count == 1:
        singular = noun[:-1] if noun.endswith("s") else noun
        return "1 %s" % singular
    return "%d %s" % (count, noun)


def roll_integument(spec):
    """A covering. None means the plan fixes nothing, so draw from the pool."""
    if spec is None:
        return random.choice(INTEGUMENT_POOL)
    covering, probability = spec
    if random.random() < probability:
        return covering
    return random.choice(INTEGUMENT_POOL)


def derive_form(traits, themes):
    """What the traits already settle. Returns (morphology, why, physiology, why).

    Traits win over the dice, and a settled value is emitted alone rather than
    beside alternatives - offering "animal biology" next to a construct would
    turn the override into a suggestion. Same reasoning as FLEE_BY_AGGRESSION:
    rolling something the rest of the build has already decided only
    manufactures contradictions.
    """
    traits = set(traits or [])
    themes = set(themes or [])
    forced_morph = source_morph = forced_phys = source_phys = None

    for trait, label in MORPHOLOGY_BY_TRAIT.items():
        if trait in traits:
            forced_morph = label
            source_morph = "determined by trait %s" % trait
            break

    if "divine" in traits:
        forced_phys = "divine"
        source_phys = "determined by trait divine"
    elif "animated" in traits:
        forced_phys = "undead" if "undead" in themes else _weighted_label(ANIMATED_CONSTRUCT)
        source_phys = "determined by trait animated"

    return forced_morph, source_morph, forced_phys, source_phys


def morphology_options(favour=(), forced=None):
    if forced:
        entries = [entry for entry in MORPHOLOGY if entry[0] == forced]
    else:
        entries = favoured_sample(MORPHOLOGY, favour, FORM_OPTIONS)
    return [
        {
            "morphology": label,
            "shape": shape,
            "limbs": roll_limbs(limbs, LIMB_NOUN.get(label, DEFAULT_LIMB_NOUN)),
            "integument": roll_integument(integument),
        }
        for label, shape, limbs, integument in entries
    ]


def physiology_options(favour=(), forced=None):
    if forced:
        entries = [entry for entry in PHYSIOLOGY if entry[0] == forced]
        return [{"physiology": label, "note": note} for label, note, _ in entries]

    picked = favoured_sample(PHYSIOLOGY, favour, FORM_OPTIONS,
                             weight_of=lambda entry: entry[2])
    options = [{"physiology": label, "note": note} for label, note, _ in picked]

    chosen = {option["physiology"] for option in options}
    if not any(label in chosen for label, _ in MUNDANE_PHYSIOLOGY):
        label = _weighted_label(MUNDANE_PHYSIOLOGY)
        note = next(entry[1] for entry in PHYSIOLOGY if entry[0] == label)
        options.append({"physiology": label, "note": note, "escape_route": True})
    return options


def roll_form(traits, themes, morphology_favour=(), physiology_favour=()):
    forced_morph, source_morph, forced_phys, source_phys = derive_form(traits, themes)

    form = {
        "note": (
            "Options, not decisions - pick one of each, write it into the "
            "description, and drop this block. Morphology is shape and "
            "movement only: it says nothing about where the thing lives or how "
            "it senses, which the behaviour block has already settled."
        ),
        "morphology_options": morphology_options(morphology_favour, forced_morph),
        "physiology_options": physiology_options(physiology_favour, forced_phys),
    }
    if source_morph:
        form["morphology_source"] = source_morph
    if source_phys:
        form["physiology_source"] = source_phys
    return form


def favour_lists(lexicon, themes, key):
    """Union the named themes' favour lists. Absent keys are fine - the lists
    are optional, so a theme can be added without touching any of this."""
    if not lexicon:
        return []
    found = []
    for name in themes or ():
        found.extend(lexicon.get("themes", {}).get(name, {}).get(key) or [])
    return found


def ceiling_for(party_levels):
    return CEILING_PER_LEVEL * party_levels


def max_count_for(monster):
    org = (monster.get("tags", {}).get("organization") or "").strip().lower()
    return ORG_MAX_COUNT.get(org, DEFAULT_MAX_COUNT)


def suggested_counts(monster, ceiling):
    """How many of this monster to field, as a range rather than one number.

    Returns {"min", "typical", "max"} - a light skirmish, a standard fight, and
    as much as the party can take. `max` is the ceiling, so it is the most
    dangerous option, NOT the recommendation; `typical` is what to reach for.
    An earlier version returned only the ceiling count and called it
    "suggested", which read as advice to run the hardest possible fight.

    Every value is clamped to what the organization can plausibly field, so a
    Solitary monster never comes back as "bring seven", and the three stay in
    order after clamping.
    """
    raw = monster.get("difficulty")
    if raw is None or raw <= 0 or ceiling is None:
        return None
    cap = max_count_for(monster)
    counts = {}
    for name, weight in ENCOUNTER_WEIGHTS:
        counts[name] = max(1, min(cap, round(weight * ceiling / raw)))
    # Clamping can collapse or invert the order (a Solitary cap of 1 flattens
    # all three); keep them monotonic so min <= typical <= max always holds.
    counts["typical"] = max(counts["min"], counts["typical"])
    counts["max"] = max(counts["typical"], counts["max"])
    return counts


def find_by_name(book, wanted):
    """Look a monster up by name across every setting.

    Returns a list of (slug, monster). An exact case-insensitive match wins
    outright; otherwise substring matches are returned so the caller can report
    the ambiguity rather than silently picking one.
    """
    needle = wanted.strip().lower()
    exact, partial = [], []
    for slug in sorted(book):
        for monster in book[slug].get("monsters", []):
            name = (monster.get("name") or "").strip().lower()
            if name == needle:
                exact.append((slug, monster))
            elif needle in name:
                partial.append((slug, monster))
    return exact or partial


def select_monsters(setting, args):
    """Filter one setting's roster, then either return all of it or sample.

    The difficulty test is a ceiling, not a band - see CEILING_PER_LEVEL.
    Monsters too weak to be a solo threat are kept (with a suggested number)
    unless --solo-threat asks for only what stands on its own.
    """
    monsters = list(setting.get("monsters", []))

    ceiling = None
    if args.party_levels is not None:
        ceiling = ceiling_for(args.party_levels)
    if args.difficulty_max is not None:
        ceiling = args.difficulty_max
    floor = args.difficulty_min

    kept = []
    unrated_skipped = 0
    weak_dropped = 0
    for monster in monsters:
        raw = monster.get("difficulty")
        if raw is None:
            if args.include_unrated:
                kept.append(dict(monster, suggested_number=None))
            else:
                unrated_skipped += 1
            continue
        if ceiling is not None and raw > ceiling:
            continue
        if floor is not None and raw < floor:
            continue

        if (
            args.solo_threat
            and ceiling is not None
            and raw < SOLO_THREAT_FRACTION * ceiling
        ):
            weak_dropped += 1
            continue
        kept.append(dict(monster, suggested_number=suggested_counts(monster, ceiling)))

    return kept, ceiling, unrated_skipped, weak_dropped


def print_setting_menu(book, stream=sys.stdout):
    print("Dungeon World bestiary - setting tags", file=stream)
    print(
        "\nA setting tag is required to get any monster. Pick the one that fits\n"
        "where the characters actually are:\n",
        file=stream,
    )
    for slug in sorted(book):
        print("  %-12s %s" % (slug, book[slug].get("short_description", "")), file=stream)
    print(
        "\nFor a fuller description of any setting, run:\n"
        "  monster_gen.py --setting-info <tag>      (or --setting-info for all)\n"
        "Run with --help-llm or --help for full help.",
        file=stream,
    )


def print_setting_info(book, tag):
    """Describe a setting, and for a named one list what actually lives there.

    The roster is the useful part - the bestiary chapters carry no intro prose
    of their own, so the descriptions are short hand-written summaries and
    "what monsters are in here" tells you far more about whether a setting
    fits. Names are quoted so they can be pasted straight back as arguments.

    'all' stays an overview: nine rosters is 154 lines, which is a context
    budget nobody asked to spend.
    """
    everything = tag in (None, "all")
    slugs = sorted(book) if everything else [tag]

    for slug in slugs:
        setting = book[slug]
        monsters = setting.get("monsters", [])
        print("%s - %s" % (slug, setting.get("name", "")))
        print("  %s" % setting.get("long_description", ""))

        if everything:
            print("  (%d monsters - run --setting-info %s for the roster)"
                  % (len(monsters), slug))
            print()
            continue

        print("  %d monsters, easiest first:" % len(monsters))
        ordered = sorted(
            monsters,
            key=lambda m: (m.get("difficulty") is None, m.get("difficulty") or 0),
        )
        for monster in ordered:
            difficulty = monster.get("difficulty")
            print(
                "    %-26s %9s   %s"
                % (
                    '"%s"' % monster.get("name", "?"),
                    "-" if difficulty is None else difficulty,
                    (monster.get("tags", {}).get("organization") or "-"),
                )
            )
        print()


# --- custom builder -------------------------------------------------------


def step_die(size, steps):
    idx = DIE_LADDER.index(size)
    idx = max(0, min(len(DIE_LADDER) - 1, idx + steps))
    return DIE_LADDER[idx]


def custom_difficulty(hp, armor_val, die, dmg_bonus, special_count):
    """Same shape as tools/extract_monsters.py:compute_difficulty. Approximate
    for custom monsters - it cannot see the source's Special Qualities prose,
    so it counts the builder's chosen qualities instead."""
    factor = DIE_FACTOR.get(die, 2.0)
    difficulty = (
        hp
        * (1 + armor_val * 0.3)
        * factor
        * (1 + 0.2 * max(0, dmg_bonus))
        * (1 + 0.3 * special_count)
    )
    return round(difficulty, 2)


def build_monster(org, size, armor, known_for, armament, traits, divine_bonus, name):
    """Return (monster_dict, final_die, meta) using the bestiary's own key names.

    `meta` carries what the deadliness tier needs but the stat block does not
    record: the final damage bonus, whether the monster rolls damage twice, and
    how many special qualities it ended up with.
    """
    org_data = ORG[org]
    size_data = SIZE[size]

    hp = org_data["hp"] + size_data["hp_mod"]
    dmg_bonus = size_data["dmg_mod"]
    die = org_data["die"]
    armor_val = ARMOR[armor]
    extra_tags = []
    special_qualities = []
    move_notes = []

    for k in known_for:
        desc = KNOWN_FOR[k]
        if k == "strength":
            dmg_bonus += 2
            extra_tags.append("Forceful")
        elif k == "offense":
            move_notes.append("roll damage twice, take the better (advantage)")
        elif k == "defense":
            armor_val += 1
        elif k == "deft":
            extra_tags.append("1 piercing")
        elif k == "endurance":
            hp += 4
        special_qualities.append(desc)

    if armament:
        desc = ARMAMENTS[armament]
        special_qualities.append(desc)
        if armament == "vicious":
            dmg_bonus += 2
        elif armament == "weak":
            die = step_die(die, -1)
        elif armament == "metal":
            extra_tags += ["2 piercing", "Messy"]
        elif armament == "ignores":
            extra_tags.append("Ignores Armor")

    for t in traits:
        desc = TRAITS[t]
        if t in DESCRIPTIVE_ONLY:
            extra_tags.append(t.capitalize())
            continue
        if t == "divine":
            bonus_desc = {
                "damage": "+2 damage",
                "hp": "+2 HP",
                "both": "+2 damage and +2 HP",
            }[divine_bonus]
            desc = f"Favored by the gods (Divine, {bonus_desc})"
        special_qualities.append(desc)
        if t == "shield":
            extra_tags.append("Cautious")
            armor_val += 1
        elif t == "noanatomy":
            armor_val += 1
            hp += 3
        elif t == "divine":
            extra_tags.append("Divine")
            if divine_bonus in ("damage", "both"):
                dmg_bonus += 2
            if divine_bonus in ("hp", "both"):
                hp += 2
        elif t == "animated":
            hp += 4
        elif t == "devious":
            extra_tags.append("Devious")
            die = step_die(die, -1)
        elif t == "ancient":
            die = step_die(die, 1)
        elif t == "abhors":
            move_notes.append("roll damage twice, take the worse (disadvantage)")

    damage_str = f"d{die}"
    if dmg_bonus > 0:
        damage_str += f"+{dmg_bonus}"
    elif dmg_bonus < 0:
        damage_str += str(dmg_bonus)
    hp = max(1, hp)

    attack = f"{damage_str} damage"
    if move_notes:
        attack += " (%s)" % "; ".join(move_notes)

    monster = {
        "name": name or "",
        "attack": attack,
        "difficulty": custom_difficulty(
            hp, armor_val, die, dmg_bonus, len(special_qualities)
        ),
        # Fictional capability, matching what the bestiary means by this key
        # (Burrowing, Camouflage, Fiery blood). Filled from the themed lexicon
        # in run_custom; the builder itself has no fiction to put here.
        "special_quality": "",
        # The builder's own arithmetic - which options produced the numbers
        # above. This used to sit in special_quality, which put derivation
        # bookkeeping in a field the bestiary uses for capability, so the two
        # kinds of content are now separated.
        "built_from": "; ".join(special_qualities),
        "hp": hp,
        "armor": armor_val,
        "tags": {
            "range": [size_data["range"]],
            "organization": org.capitalize(),
            "size": size,
            "traits": extra_tags,
        },
        "description": "(write one - what does it look like, and why is it a problem?)",
        "instinct": "(fill in - what does it want that causes problems for others?)",
        "moves": ["(write 1-3, describing its attack and any special qualities)"],
    }
    meta = {
        "dmg_bonus": dmg_bonus,
        "advantage": "offense" in known_for,
        "special_count": len(special_qualities),
    }
    return monster, die, meta


DAMAGE_DIE = re.compile(r"[bw]?\[?\s*\d*d(\d+)")


def parse_damage_die(attack):
    """Pull the damage die out of an attack line.

    Handles the bestiary's shapes: 'Claw (d6 damage)', 'Bite (d8+1 damage)',
    'Trusty knife (b[2d10] damage)' and 'Stolen dagger (w[2d8] damage)' - the
    b/w forms are best-of/worst-of, but the die itself is what treasure needs.
    """
    if not attack:
        return None
    match = DAMAGE_DIE.search(attack)
    return int(match.group(1)) if match else None


def describe_treasure(roll):
    """One table entry, with its dice already rolled into real numbers.

    Entries the table leaves abstract about appearance ("a small valuable item
    worth 140 coins") come back with a short menu of looks under "looks_like".
    The value was rolled once and is shared by all of them, so picking a
    different option never changes what the thing is worth - only what it is.
    """
    text, is_object = _treasure.value_entry(roll)
    result = {"text": text}
    if is_object:
        result["looks_like"] = _treasure.describe_options(
            exclude_traits=_treasure.VALUE_EXCLUDED
        )
    return result


def treasure_tag_effects(monster):
    """Bonus-dice modifiers derived from the monster's own tags."""
    tags = monster.get("tags") or {}
    present = {str(t).strip().lower() for t in (tags.get("traits") or [])}
    advantage = False
    notes = []
    for tag, (kind, text) in TREASURE_TAG_EFFECTS.items():
        if tag not in present:
            continue
        if kind == "advantage":
            advantage = True
        notes.append(text)
    return advantage, notes


def roll_treasure(die, advantage=False, bonus_d4=0):
    """Roll the treasure table, following the 'roll again' results.

    15, 16 and 17 each give their own result *and* send you back for another
    roll, so the return is a list - a single haul can be several things.

    bonus_d4 adds the rulebook's "+1d4" modifiers. It matters more than it
    looks: the biggest monster damage die is d12, so without a bonus the top
    of the table (13-18, including the hoard) is unreachable.
    """
    rolls, results = [], []
    for _ in range(MAX_REROLLS + 1):
        value = random.randint(1, die)
        if advantage:
            value = max(value, random.randint(1, die))
        value += sum(random.randint(1, 4) for _ in range(bonus_d4))
        rolls.append(value)
        results.append(describe_treasure(value))
        if value not in _treasure.roll_again_values():
            break
    return rolls, results


def treasure_for(monster, counts, bonus_d4=0):
    """One treasure haul per creature, each tagged to the creature it belongs to.

    Rolled for the MAXIMUM of the suggested range so there is always enough,
    and every haul carries its creature number. That pairing has to be explicit:
    a bare list of seven hauls beside a monster you decided to use three of is
    an easy way to hand out four piles of loot that nobody earned.
    """
    die = parse_damage_die(monster.get("attack"))
    if die is None:
        return None
    count = 1 if not counts else max(1, counts.get("max", 1))

    advantage, notes = treasure_tag_effects(monster)
    if bonus_d4:
        notes = notes + ["Bonus: +%dd4 on the roll" % bonus_d4]

    hauls = []
    for index in range(1, count + 1):
        rolls, results = roll_treasure(die, advantage=advantage, bonus_d4=bonus_d4)
        haul = {"creature": index, "die": die, "rolls": rolls, "results": results}
        if notes:
            haul["notes"] = notes
        hauls.append(haul)

    payload = {"rolled_for": count, "hauls": hauls}
    # The note only earns its space when hauls can be mis-paired with a smaller
    # number of creatures. With a single haul there is nothing to get wrong.
    if count > 1:
        payload["note"] = (
            "One haul per creature, numbered. Rolled for %d (the maximum of "
            "suggested_number). If you field fewer, use only that many hauls - "
            "creature 1 up to the number you actually use - and discard the "
            "rest." % count
        )
    return payload


HELP_LLM = """\
monster_gen.py - pick an official Dungeon World monster, or build a custom one.

DEFAULT BEHAVIOUR IS THE OFFICIAL BESTIARY. 154 monsters from the core rulebook
across 9 settings, each with a real name, description, instinct and written
moves. Normally prefer these: a custom monster comes back as a stat skeleton with the
flavour blank, which is much harder to run at the table. Standard monsters are
better for situations like traveling over dangerous but unremarkable countryside.

When special fiction demands custom monsters, `--custom` can be used but be
prepared to make special effort to fill in the gaps.

A SETTING TAG IS ALWAYS REQUIRED for monster output. Run with no arguments to
get the list of tags with one-line descriptions, then pick the one matching
where the characters are. All monsters from all settings are never returned at
once.

USAGE
  monster_gen.py                          list setting tags (start here)
  monster_gen.py --setting-info TAG       description PLUS the full roster for
                                          that setting: every monster's name
                                          (quoted), difficulty and organization,
                                          easiest first. Use this to see what
                                          actually lives somewhere before
                                          drawing from it.
  monster_gen.py --setting-info           overview of all 9 settings, without
                                          rosters (nine rosters is 154 lines).
                                          "all" is the same as omitting it.
  monster_gen.py --name "Fire Eels"       ONE named monster, from any setting.
                                          The only monster call that needs no
                                          setting tag - you already know what
                                          you want, so there is nothing to
                                          choose. Names come from
                                          --setting-info, already quoted.
                                          Case-insensitive; a partial name
                                          works if it is unambiguous, and an
                                          exact match always wins over a
                                          partial one.
  monster_gen.py SETTING [options]        get monsters from that setting
  monster_gen.py --custom [options]       the old quick builder

STANDARD OPTIONS
  --party-levels L    Filter to monsters suited to the party. L is the SUM of
                      the party's character levels - four level-1 PCs is L=4,
                      four level-5 PCs is L=20. USE THIS. Without it you get a
                      monster of any difficulty, which may be unbeatable.
  --random N          Return N unique monsters (default 1).
  --all               Return every monster matching the filter instead of
                      sampling. Still requires a setting tag.
  --include-unrated   Include monsters with no difficulty score (12 of them -
                      mostly stat-less Planar Powers). Excluded by default,
                      because a difficulty filter that quietly returns
                      unfilterable monsters is misleading.
  --solo-threat       Keep only monsters that are a serious fight on their own:
                      difficulty >= %(solo)d%% of the party's ceiling. Needs
                      --party-levels (or --difficulty-max) to measure against.
                      (--no-horde is an alias, but the test is "one of these is
                      most of an encounter", not the Horde tag - a weak
                      Solitary monster is dropped just the same.)
  --difficulty-min X / --difficulty-max X
                      Raw difficulty overrides. --difficulty-max replaces the
                      ceiling; --difficulty-min adds a floor there is normally
                      no reason to want. For tuning; --party-levels is the
                      normal way in.
  --no-treasure       Skip the treasure rolls (they are on by default).
  --treasure-bonus N  Add N d4 to every treasure roll. This is the rulebook's
                      "lord over others" / "ancient or noteworthy" modifier,
                      and it is a judgement call, so it is not automatic.

TREASURE
  Every returned monster comes with treasure already rolled, on its own damage
  die, so you do not need a second call to find out what it got. All dice are
  resolved to concrete numbers - you get "A bag of 300 coins, 3 weight", never
  "1d4x100".

  One haul PER CREATURE, because twelve skeletons are not one pile of loot.
  The shape is:
      "treasure": {"rolled_for": 7, "note": "...", "hauls": [ {"creature": 1,
                   "die": 6, "rolls": [...], "results": [...]}, ... ]}

  Each entry in "results" is {"text": "...", "looks_like": [...]}, and each
  option in "looks_like" is {"text": "...", "categories": [...]}.
  "looks_like" appears only on entries the table leaves abstract about
  appearance - "A small valuable item worth 140 coins" says what it is worth
  but not what it IS. It is a MENU: pick the one that suits the scene, or mix
  them. The value was rolled once and is shared by every option, so choosing
  between them never changes what the treasure is worth. Entries that are not
  objects ("Useful information", "A magical item or effect") have no
  "looks_like" - those are yours to invent.
  "categories" names the axes an option was rolled on, and they double as
  idea_gen.py table names: "idea_gen.py treasure-object:motif" rerolls just
  that axis when one detail is wrong and the rest of the object is fine.

  IMPORTANT - do not hand out loot nobody earned. Hauls are rolled for
  suggested_number.max, so there are usually MORE hauls than creatures you will
  actually use. Each haul is numbered. Decide how many creatures you are
  fielding first, then use hauls 1..that many and DISCARD the rest. Three
  skeletons do not drop seven skeletons' worth of treasure.

  Rolls of 15, 16 and 17 give their own result AND roll again, so a single
  haul's "results" can be a list of several things.

  These monster tags change the roll automatically:
    Hoarder  - roll the damage die twice, keep the higher
    Magical  - add something strange, possibly magical
    Divine   - add a sign of a deity
    Planar   - add something otherworldly
  The rulebook's other modifiers depend on fiction rather than tags, so they
  are yours to apply: "far from home" (add a ration), and the +1d4 ones via
  --treasure-bonus.

  NOTE: the largest monster damage die is d12, so WITHOUT --treasure-bonus the
  top of the table (13-18, including the hoard) cannot come up at all. If a
  monster is a warlord, a dragon, or otherwise noteworthy, pass
  --treasure-bonus 1 or 2 - otherwise its hoard will never appear.

HOW --party-levels WORKS
  Difficulty is PER CREATURE; how many you field is your call. So the filter
  asks only "is a single one of these too much for this party?" - a ceiling:
      monster difficulty  <=  %(k)d * L
  It is deliberately NOT a range. A strong party can still meet weak monsters;
  they are simply easy, and that is what suggested_number is for. (An earlier
  version used a band and was wrong - a high-level party could not be offered a
  bandit at all.)

  Every returned monster carries "suggested_number" as a RANGE, not a single
  number:
      {"min": 5, "typical": 8, "max": 11}
    min      a light skirmish        (~%(wmin)d%% of the ceiling)
    typical  a standard fight        (~%(wtyp)d%% of the ceiling)  <- use this
    max      as much as the party can take - the most DANGEROUS option, not
             the recommended one

  Reach for "typical" unless you specifically want an easy or a punishing
  fight. All three are capped by what the organization can plausibly muster
  (Horde up to %(horde)d, Group up to %(group)d, Solitary %(solitary)d), which
  is why a Solitary monster reads 1/1/1.

  It is a suggestion, not a rule. One straggler separated from its pack is
  always a legitimate scene - suggested_number just tells you what a serious
  fight would take, so you know the difference between a lone skeleton in a
  corridor and the ten that would actually threaten the party.

  Worked examples:
    L=4  (four level-1 PCs, ceiling %(c4)d)
      Skeleton (7.28, Horde) -> offered, %(sk4)s
      Lich     (99.84)       -> not offered, needs L=%(lich)d
    L=40 (four level-10 PCs, ceiling %(c40)d)
      Skeleton               -> still offered, %(sk40)s
      Lich     (Solitary)    -> offered, min/typical/max 1/1/1

SEED WORDS, FORM AND BEHAVIOUR (--custom only)
  A custom monster has no flavour of its own, so instead of handing back a bare
  "(write one)" the generator hands over raw material and says so. Three
  blocks:

  "seed_words" - themed vocabulary to synthesise from. substance + bodypart
  build a compound name (Mudscale, Rootfang), action gives agentive forms and
  move ideas, drive primes the instinct, texture primes the description, sound
  gives onomatopoeia, quality gives fictional capabilities, and "evocative" is
  the catch-all: whole surprising details, the entries most likely to produce a
  creature you would not have thought of. "deadliness" gives the naming
  register for its damage tier. The name/instinct/moves/description fields
  quote the relevant seeds back at you. NONE of it is meant to be used
  verbatim - pick, discard, recombine.

  "special_quality" arrives EMPTY, with the choice beside it:
      "special_quality": "",
      "special_quality_options": ["Burrowing", "Camouflage", "Drags under"],
      "special_quality_note": "Pick one, or coin a new one of about the same
                               length by combining two. ..."
  Pick or coin one, write it into special_quality, and drop the other two keys
  before the monster is used or saved. A stat block should not ship with its
  own menu attached.

  Options come from the theme's quality pool, in the register the bestiary
  uses: a bare noun phrase, usually 1-3 words (Burrowing, Fiery blood, Looks
  like a cloak). Whatever you write must match that FORM - not a sentence, and
  with no clause explaining how the quality works. "Mimics voices" is a
  quality; "Lures with a borrowed sound - mimics something it heard once to
  draw prey off the path" is a paragraph about one.

  special_quality itself stays a plain string, the same type bestiary monsters
  give it, so both kinds of monster can be read the same way. With --no-seeds
  none of the three keys is populated.

  "built_from" (custom monsters only) records which builder options produced
  the numbers - "Skill in defense (+1 armor); Bears a shield ...". That is
  derivation bookkeeping, not fiction, which is why it is no longer mixed into
  special_quality. Bestiary monsters have no such key.

  "form" - what the thing IS, as against how it hits or how it acts. A MENU,
  not a decision: three "morphology_options" and three "physiology_options",
  of which you pick one of each, write it into the description and drop the
  block. Each morphology option is a complete body - shape, limb count and
  integument already agreeing, so a bird is feathered and two-legged and a
  centipede has hundreds of legs rather than an unreadable number. Morphology
  is SHAPE AND LOCOMOTION ONLY and implies nothing about habitat or senses:
  "worm" means it is shaped like one and moves like one, not that it lives in
  soil; "bat" means flying mammal, not echolocation. Habitat and senses are
  the behaviour block's business, and it has already decided them - so an
  echolocating blob is not a contradiction to fix, it is why you get a choice.

  Physiology leans ordinary on purpose - animal biology half the time, plant
  biology a fifth, everything stranger sharing the rest - so a menu usually
  reads "animal, plant, something odder". If all three come back strange, a
  grounded fourth is appended and marked "escape_route", so there is always
  something ordinary to retreat to.

  Where a builder trait already settles the answer, NOTHING is rolled: the
  single determined value is emitted with a "morphology_source" or
  "physiology_source" saying which trait decided it. `animated` gives a
  construct, or the undead under an undead theme; `divine` gives divine;
  `noanatomy` gives a blob. Offering alternatives beside a determination would
  turn the override into a suggestion.

  "behavior" - eight rolled axes: aggression (-2..+4), the flee rule derived
  from it, hide-or-run, intelligence (-1..9), intimidation (-1..6),
  territoriality, sensory profile and post-injury behaviour. Rolled at random
  and only lightly steered by the stats, so a huge terrifying thing can still
  come back timid. THAT IS DELIBERATE - an odd combination is usually the
  interesting one. Disregard and rewrite any of it to fit the situation.

  --theme TAG[,TAG...]  Theme the seed words. Comma-separated tags UNION their
                      pools, so --theme cavern,undead draws on both. Defaults
                      to "generic". Run --list-themes for the list. Themes also
                      bias which forms come up: a swamp leans to worms and
                      snakes, the planes to floaters and impossible solids. A
                      lean, never a filter - any form can appear anywhere.
  --list-themes       Print the available themes and exit.
  --no-seeds          Omit seed words.
  --no-behavior       Omit the behaviour block.
  --no-form           Omit the morphology/physiology block.

CUSTOM OPTIONS (only with --custom)
  Unset categories are ROLLED BY DEFAULT. Set only the ones you care about and
  the rest are filled in for you - `--custom --org horde` rolls size, armor,
  known-for, armament and traits around that. --random is accepted and does
  nothing; it used to be required for this and is kept so old calls still work.

  --no-random         Do NOT roll unset categories. Falls back to the fixed
                      baseline: solitary, small, no armor, no extras - which is
                      always d10 damage, 12 HP, 0 armor. Only useful when you
                      want that exact starting point to build up from by hand.

  --party-levels L / --difficulty-min X / --difficulty-max X
                      Work on custom monsters too. The builder rerolls until
                      the result lands in the window (typically under 20 rolls)
                      and reports it under "filter". --party-levels L alone
                      targets a real fight rather than anything under the
                      ceiling: %(solo)d%% of it up to the ceiling itself.
                      Explicit --org/--size/--armor narrow what can be rolled,
                      so pinning several plus a tight window may not be
                      satisfiable - it warns and returns the closest it found.

  Unset categories are weighted, not uniform: most monsters come out lightly
  armoured and ordinary-sized, so a heavily armoured or huge one is a find
  rather than a coin flip. The search for a difficulty target rolls uniformly
  instead, since rare-by-design powerful stats would make a powerful target
  slow to hit for no benefit.
  --org horde|group|solitary        --size tiny|small|large|huge
  --armor none|leather|mail|steel|magical
  --known-for strength,offense,defense,deft,endurance
  --armament vicious|weak|metal|ignores
  --traits shield,noanatomy,divine,animated,devious,ancient,abhors,
           stealthy,organized,intelligent,terrifying
  --divine-bonus damage|hp|both     --treasure
  --name NAME         names the custom stat block. NOTE this flag means
                      something different WITHOUT --custom, where it looks the
                      name up in the bestiary instead (see USAGE above).

  --seed N            reproducible output - dev/debug only, NEVER during play

OUTPUT
  Compact JSON on stdout (one line): {setting, setting_name, filter, monsters[]}.
  Monster objects are reproduced verbatim from the bestiary. Warnings, the
  seed notice and the yaml reminder all go to stderr, so stdout stays
  parseable - pipe it straight into a JSON parser if you like.

EXAMPLES
  monster_gen.py
  monster_gen.py --setting-info undead
  monster_gen.py cavern --party-levels 4
  monster_gen.py undead --random 3 --party-levels 12
  monster_gen.py woods --all --party-levels 8
  monster_gen.py --custom --random --treasure
"""

# The worked examples above are computed from the constants, not typed in, so
# retuning CEILING_PER_LEVEL or ORG_MAX_COUNT cannot leave --help-llm lying.
# 7.28 and 99.84 are the bestiary's own difficulties for Skeleton and Lich.
_SKELETON, _LICH = 7.28, 99.84
_SKELETON_MONSTER = {
    "difficulty": _SKELETON,
    "tags": {"organization": "Horde"},
}


def _fmt_counts(monster, ceiling):
    counts = suggested_counts(monster, ceiling)
    return "min/typical/max %d/%d/%d" % (
        counts["min"],
        counts["typical"],
        counts["max"],
    )
HELP_LLM = HELP_LLM % {
    "k": CEILING_PER_LEVEL,
    "horde": ORG_MAX_COUNT["horde"],
    "group": ORG_MAX_COUNT["group"],
    "solitary": ORG_MAX_COUNT["solitary"],
    "c4": ceiling_for(4),
    "c40": ceiling_for(40),
    "sk4": _fmt_counts(_SKELETON_MONSTER, ceiling_for(4)),
    "sk40": _fmt_counts(_SKELETON_MONSTER, ceiling_for(40)),
    "lich": math.ceil(_LICH / CEILING_PER_LEVEL),
    "solo": int(SOLO_THREAT_FRACTION * 100),
    "wmin": int(dict(ENCOUNTER_WEIGHTS)["min"] * 100),
    "wtyp": int(dict(ENCOUNTER_WEIGHTS)["typical"] * 100),
}


# -p/--pretty dump style: labels with colons, 4-space indent, parens only for
# short same-line scalar lists. Null is <none> (angle brackets) so it is not
# mistaken for a list. Multi-line containers never wrap in parens. Long prose
# word-wraps; continuation lines indent one level deeper.
_PRETTY_INDENT = "    "
_PRETTY_LINE_BUDGET = 88  # soft wrap width (including indent)


def _is_scalar(value):
    return not isinstance(value, (dict, list, tuple))


def _fmt_scalar(value):
    if value is None:
        return "<none>"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _fmt_scalar_list_inline(items):
    """Paren form for a same-line scalar list: '( Close, Messy )' or '()'."""
    if not items:
        return "()"
    return "( %s )" % ", ".join(_fmt_scalar(item) for item in items)


def _inline_value(value):
    """Format a scalar or short scalar-list for a same-line 'key: value'."""
    if _is_scalar(value):
        return _fmt_scalar(value)
    if isinstance(value, (list, tuple)):
        return _fmt_scalar_list_inline(value)
    raise TypeError("not an inline-able value")


def _can_inline_scalar_list(items, budget):
    if any(not _is_scalar(item) for item in items):
        return False
    return len(_fmt_scalar_list_inline(items)) <= budget


def _is_simple_value(value, budget):
    """True when value can sit on a 'key: ...' line without nesting.

    Long scalars still count as simple (they word-wrap on their own line
    group); only nested dicts/lists become block children.
    """
    if _is_scalar(value):
        return True
    if isinstance(value, (list, tuple)):
        return _can_inline_scalar_list(value, budget)
    return False


def _kv_part(key, value):
    return "%s: %s" % (key, _inline_value(value))


def _is_short_packable(key, value, budget):
    """Only compact numeric/token fields share a line; prose stays solo.

    Haul rows become 'creature: 1, die: 8, rolls: ( 6 )'. Names, attacks and
    description never ride along with a neighbor.
    """
    if not _is_simple_value(value, budget):
        return False
    if _is_scalar(value):
        text = _fmt_scalar(value)
        # Empty or anything past a short token/number: own line only.
        if text == "" or len(text) > 12:
            return False
    elif isinstance(value, (list, tuple)):
        # Inline lists only pack when tiny (e.g. rolls: ( 6 )).
        if len(_fmt_scalar_list_inline(value)) > 16:
            return False
    part = _kv_part(key, value)
    return len(part) <= 24


def _wrap_block(text, initial_indent, subsequent_indent):
    """Word-wrap text; first line uses initial_indent, rest subsequent_indent."""
    if text == "":
        return [initial_indent.rstrip()] if initial_indent.strip() else [""]

    wrapper = textwrap.TextWrapper(
        width=_PRETTY_LINE_BUDGET,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_long_words=True,
        break_on_hyphens=False,
        replace_whitespace=True,
        drop_whitespace=True,
    )
    lines = []
    paragraphs = text.split("\n")
    for i, para in enumerate(paragraphs):
        if not para.strip():
            # Keep a blank line between paragraphs when source had one.
            if lines and i < len(paragraphs) - 1:
                lines.append("")
            continue
        wrapped = wrapper.wrap(para)
        if not wrapped:
            # textwrap drops pure-whitespace; still show the key line once.
            if not lines:
                lines.append(initial_indent.rstrip())
        else:
            lines.extend(wrapped)
        # Later paragraphs hang under the continuation indent only.
        wrapper.initial_indent = subsequent_indent
    return lines or [initial_indent.rstrip()]


def _pretty_scalar_kv(key, value, depth):
    """'key: value' with word-wrap; continuations indent one level deeper."""
    pad = _PRETTY_INDENT * depth
    text = _fmt_scalar(value)
    prefix = "%s%s: " % (pad, key)
    cont = pad + _PRETTY_INDENT
    if text == "":
        yield "%s%s:" % (pad, key)
        return
    if "\n" not in text and len(prefix) + len(text) <= _PRETTY_LINE_BUDGET:
        yield prefix + text
        return
    for line in _wrap_block(text, prefix, cont):
        yield line


def _pretty_bare_text(text, depth):
    """Word-wrap a bare (no key) string at the given indent depth."""
    pad = _PRETTY_INDENT * depth
    if text == "":
        yield pad.rstrip()
        return
    if "\n" not in text and len(pad) + len(text) <= _PRETTY_LINE_BUDGET:
        yield pad + text
        return
    cont = pad  # bare lines share one indent; wrap within the budget
    for line in _wrap_block(text, pad, cont):
        yield line


def _pretty_dict_body(mapping, depth, pack_simple=False):
    """Yield body lines for a dict at the given indent depth.

    pack_simple: when True (list items like a haul), pack short simple fields
    onto shared lines ('creature: 1, die: 8, rolls: ( 6 )'). Named nested
    dicts keep one key per line so tags stay scannable. Long scalars always
    get their own line even when packing. Key order is preserved.
    """
    pad = _PRETTY_INDENT * depth
    budget = max(24, _PRETTY_LINE_BUDGET - len(pad))
    pending = []  # short packable fields waiting to share a line

    def flush_pending():
        if not pending:
            return
        parts = []
        line_len = 0
        for key, value in pending:
            part = _kv_part(key, value)
            extra = len(part) + (2 if parts else 0)  # ", " between parts
            if parts and line_len + extra > budget:
                yield pad + ", ".join(parts)
                parts = [part]
                line_len = len(part)
            else:
                parts.append(part)
                line_len += extra
        if parts:
            yield pad + ", ".join(parts)
        pending.clear()

    for key, value in mapping.items():
        if not _is_simple_value(value, budget):
            yield from flush_pending()
            yield from _pretty_lines(key, value, depth)
        elif pack_simple and _is_short_packable(key, value, budget):
            pending.append((key, value))
        elif _is_scalar(value):
            yield from flush_pending()
            yield from _pretty_scalar_kv(key, value, depth)
        else:
            yield from flush_pending()
            # Short inline scalar list - one key per line.
            yield "%s%s" % (pad, _kv_part(key, value))
    yield from flush_pending()


def _pretty_lines(key, value, depth):
    """Human-readable lines for one key/value.

    Not JSON and not YAML. Four-space indent. Parentheses only for short
    same-line scalar lists; multi-line lists and objects are bare. Long
    text word-wraps with continuation lines indented one level deeper.
    """
    pad = _PRETTY_INDENT * depth
    budget = max(24, _PRETTY_LINE_BUDGET - len(pad) - len(str(key)) - 2)

    if isinstance(value, dict):
        yield "%s%s:" % (pad, key)
        if not value:
            yield "%s%s<empty>" % (pad, _PRETTY_INDENT)
            return
        yield from _pretty_dict_body(value, depth + 1, pack_simple=False)
        return

    if isinstance(value, (list, tuple)):
        if not value:
            yield "%s%s: ()" % (pad, key)
            return
        if _can_inline_scalar_list(value, budget):
            yield "%s%s: %s" % (pad, key, _fmt_scalar_list_inline(value))
            return

        # Multi-line list: no wrapping parens. Scalars one per line; dict
        # items pack their short fields; blank line between complex items.
        yield "%s%s:" % (pad, key)
        complex_items = any(isinstance(item, (dict, list, tuple)) for item in value)
        for i, item in enumerate(value):
            if i and complex_items:
                yield ""
            if isinstance(item, dict):
                if not item:
                    yield "%s%s<empty>" % (pad, _PRETTY_INDENT)
                else:
                    # List-of-objects: collapse short fields onto fewer lines.
                    yield from _pretty_dict_body(item, depth + 1, pack_simple=True)
            elif isinstance(item, (list, tuple)):
                yield from _pretty_lines("item", list(item), depth + 1)
            else:
                yield from _pretty_bare_text(_fmt_scalar(item), depth + 1)
        return

    yield from _pretty_scalar_kv(key, value, depth)


def format_pretty(payload):
    """Plain-text dump of a payload dict (or other value)."""
    if isinstance(payload, dict):
        lines = []
        for key, value in payload.items():
            lines.extend(_pretty_lines(key, value, 0))
        return "\n".join(lines) + "\n"
    # Non-dict root is unexpected, but don't crash a debug path.
    return "\n".join(_pretty_bare_text(_fmt_scalar(payload), 0)) + "\n"


def emit(payload, pretty=False):
    """Write the payload to stdout.

    Default is one compact JSON line (play-time / pipe-friendly). pretty=True
    is the human -p/--pretty path: a plain label/indent dump, not JSON. Keep
    that mode out of --help-llm so the model keeps using the compact default.
    """
    if pretty:
        sys.stdout.write(format_pretty(payload))
    else:
        json.dump(payload, sys.stdout, ensure_ascii=False, separators=(",", ":"))
        sys.stdout.write("\n")


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return 0

    ap = argparse.ArgumentParser(
        description="Pick an official Dungeon World monster, or build a custom one."
    )
    ap.add_argument("setting", nargs="?", default=None,
                    help="bestiary setting tag; run with no arguments to list them")
    ap.add_argument("--setting-info", nargs="?", const="all", default=None,
                    dest="setting_info", metavar="TAG",
                    help="print a setting's full description and exit")
    ap.add_argument("--party-levels", type=int, default=None, metavar="L",
                    help="sum of the party's character levels; filters difficulty")
    ap.add_argument("--difficulty-min", type=float, default=None)
    ap.add_argument("--difficulty-max", type=float, default=None)
    ap.add_argument("--include-unrated", action="store_true",
                    help="include monsters with no difficulty score")
    # --no-horde is the name this was first asked for; --solo-threat says what
    # it actually does, since "only dangerous in groups" is not the same set as
    # "tagged Horde" (a lone Ghost can need seven copies to matter).
    ap.add_argument("--solo-threat", "--no-horde", action="store_true",
                    dest="solo_threat",
                    help="keep only monsters that are a full encounter on their own")
    ap.add_argument("--all", action="store_true", dest="all_monsters",
                    help="return every match instead of sampling")
    # nargs="?" keeps the old custom-mode spelling (a bare --random) working
    # while giving standard mode a count.
    ap.add_argument("--random", nargs="?", type=int, const=1, default=None, metavar="N")
    ap.add_argument("--custom", action="store_true", help="use the quick builder")
    ap.add_argument("--theme", default=None, metavar="TAG[,TAG...]",
                    help="theme the seed words; comma-separated tags union their "
                         "pools (default: generic)")
    ap.add_argument("--list-themes", action="store_true", dest="list_themes",
                    help="print the available seed-word themes and exit")
    ap.add_argument("--no-random", action="store_true",
                    help="--custom: do not roll unset categories; use the fixed "
                         "baseline (solitary/small/none) instead")
    ap.add_argument("--no-seeds", action="store_true",
                    help="omit the seed words")
    ap.add_argument("--no-behavior", "--no-behaviour", action="store_true",
                    dest="no_behavior", help="omit the rolled behaviour block")
    ap.add_argument("--no-form", action="store_true",
                    help="omit the morphology/physiology block")
    ap.add_argument("--org", choices=list(ORG.keys()), default=None)
    ap.add_argument("--size", choices=list(SIZE.keys()), default=None)
    ap.add_argument("--armor", choices=list(ARMOR.keys()), default=None)
    ap.add_argument("--known-for", default="", help="Comma list: " + ",".join(KNOWN_FOR.keys()))
    ap.add_argument("--armament", choices=list(ARMAMENTS.keys()), default=None)
    ap.add_argument("--traits", default="", help="Comma list: " + ",".join(TRAITS.keys()))
    ap.add_argument("--divine-bonus", choices=["damage", "hp", "both"], default="both")
    ap.add_argument("--name", default=None)
    # Treasure now comes back by default for every monster returned. --treasure
    # is kept as an accepted no-op so old invocations do not break.
    ap.add_argument("--treasure", action="store_true",
                    help="(deprecated no-op: treasure is rolled by default)")
    ap.add_argument("--no-treasure", action="store_true",
                    help="do not roll treasure for the returned monsters")
    ap.add_argument("--treasure-bonus", type=int, default=0, metavar="N",
                    help="add N d4 to each treasure roll (the rulebook's 'lord "
                         "over others' / 'ancient or noteworthy' modifiers)")
    ap.add_argument("--seed", type=int, default=None)
    # Human debugging only: deliberately omitted from --help-llm so the model
    # keeps using the compact default (and so --help-llm cannot drift into
    # documenting a flag the runtime path is not meant to use).
    ap.add_argument(
        "-p", "--pretty", action="store_true",
        help="plain-text dump (labels/colons/parens, 4-space indent) instead of "
             "JSON; for human debugging (default is compact JSON)",
    )
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                    help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    apply_seed(args.seed)

    if args.list_themes:
        lexicon = load_lexicon()
        print("Seed-word themes (--theme TAG, comma-separate to merge pools):\n")
        for name in theme_names(lexicon):
            theme = lexicon["themes"][name]
            total = sum(len(theme.get(c) or []) for c in WORD_CATEGORIES)
            print("  %-12s %-22s %3d words" % (name, theme.get("label", ""), total))
        print("\nThemes only affect --custom monsters. Bestiary monsters come "
              "with their own flavour already written.")
        return 0

    if args.custom:
        return run_custom(args)

    book = load_bestiary()

    if args.setting_info is not None:
        if args.setting_info != "all" and args.setting_info not in book:
            sys.exit(
                "error: unknown setting %r. Known: %s"
                % (args.setting_info, ", ".join(sorted(book)))
            )
        if args.setting is not None:
            print(
                "Note: --setting-info takes precedence; the setting argument "
                "%r was ignored. Drop --setting-info to get monsters from it."
                % args.setting,
                file=sys.stderr,
            )
        print_setting_info(book, args.setting_info)
        return 0

    # A direct name lookup is the one case that needs no setting tag - you
    # already know exactly what you want, so there is nothing to choose.
    if args.name:
        return run_named(book, args)

    if args.setting is None:
        print_setting_menu(book)
        return 0

    if args.setting not in book:
        sys.exit(
            "error: unknown setting %r. Known: %s\nRun with no arguments for "
            "descriptions." % (args.setting, ", ".join(sorted(book)))
        )

    no_filter = (
        args.party_levels is None
        and args.difficulty_min is None
        and args.difficulty_max is None
    )
    if no_filter:
        print(
            "Warning: randomizing over all difficulty scores. This is not "
            "recommended unless the PCs can flee, because it could result in "
            "monsters too difficult for lower level characters to defeat.\n"
            "  Pass --party-levels L, where L is the SUM of the party's "
            "character levels (four level-1 PCs = 4). A monster is then kept "
            "when its own difficulty is at most %d*L, and each one comes back "
            "with a suggested_number saying how many to field."
            % CEILING_PER_LEVEL,
            file=sys.stderr,
        )

    if args.solo_threat and args.party_levels is None and args.difficulty_max is None:
        print(
            "Warning: --solo-threat needs something to measure against and was "
            "ignored. Add --party-levels L (or --difficulty-max).",
            file=sys.stderr,
        )

    setting = book[args.setting]
    kept, ceiling, unrated_skipped, weak_dropped = select_monsters(setting, args)

    if not kept:
        sys.exit(
            "error: no monsters in %r pass that filter (difficulty ceiling %s%s). "
            "Raise --party-levels, drop --solo-threat, or try another setting."
            % (
                args.setting,
                ceiling,
                ", --solo-threat dropped %d" % weak_dropped if weak_dropped else "",
            )
        )

    if args.all_monsters:
        chosen = kept
    else:
        count = args.random if args.random is not None else 1
        if count < 1:
            sys.exit("error: --random must be at least 1")
        count = min(count, len(kept))
        chosen = random.sample(kept, k=count)

    # Rolled only for what is actually returned, not for everything that
    # matched - --all over a whole setting would otherwise roll 20 hauls of
    # treasure nobody asked for.
    if not args.no_treasure:
        chosen = [
            dict(
                entry,
                treasure=treasure_for(
                    entry, entry.get("suggested_number"), args.treasure_bonus
                ),
            )
            for entry in chosen
        ]

    if unrated_skipped:
        print(
            "Note: %d monster(s) in this setting have no difficulty score and "
            "were excluded; use --include-unrated to see them."
            % unrated_skipped,
            file=sys.stderr,
        )

    if weak_dropped:
        print(
            "Note: --solo-threat dropped %d monster(s) that would need more "
            "than one to threaten this party." % weak_dropped,
            file=sys.stderr,
        )

    emit(
        {
            "setting": args.setting,
            "setting_name": setting.get("name", ""),
            "filter": {
                "party_levels": args.party_levels,
                "difficulty_ceiling": ceiling,
                "solo_threat_only": bool(args.solo_threat),
                "matched": len(kept),
                "returned": len(chosen),
            },
            "monsters": chosen,
        },
        pretty=args.pretty,
    )
    print("Reminder: update gm and character yaml files now!", file=sys.stderr)
    return 0


def run_named(book, args):
    """--name NAME: return one specific monster, no setting tag required."""
    matches = find_by_name(book, args.name)

    if not matches:
        sys.exit(
            "error: no monster named %r. Run --setting-info <tag> to list a "
            "setting's roster, or with no arguments for the setting tags."
            % args.name
        )
    if len(matches) > 1:
        sys.exit(
            "error: %r matches several monsters:\n  %s\nUse the full name."
            % (
                args.name,
                "\n  ".join(
                    '"%s" (%s)' % (m.get("name", "?"), slug) for slug, m in matches
                ),
            )
        )

    slug, monster = matches[0]
    ceiling = ceiling_for(args.party_levels) if args.party_levels is not None else None
    entry = dict(monster, suggested_number=suggested_counts(monster, ceiling))

    if not args.no_treasure:
        entry["treasure"] = treasure_for(
            entry, entry.get("suggested_number"), args.treasure_bonus
        )

    if ceiling is not None and (monster.get("difficulty") or 0) > ceiling:
        print(
            "Warning: %s has difficulty %s, above this party's ceiling of %d. "
            "You asked for it by name, so here it is - but it may be more than "
            "they can survive." % (monster.get("name"), monster.get("difficulty"), ceiling),
            file=sys.stderr,
        )

    emit(
        {
            "setting": slug,
            "setting_name": book[slug].get("name", ""),
            "filter": {
                "requested_name": args.name,
                "party_levels": args.party_levels,
                "difficulty_ceiling": ceiling,
                "matched": 1,
                "returned": 1,
            },
            "monsters": [entry],
        },
        pretty=args.pretty,
    )
    print("Reminder: update gm and character yaml files now!", file=sys.stderr)
    return 0


def weighted_pick(weights, uniform=False):
    keys = list(weights)
    if uniform:
        return random.choice(keys)
    return random.choices(keys, weights=[weights[k] for k in keys], k=1)[0]


def roll_custom_once(args, random_fill, uniform=False):
    """One roll of the quick builder. Explicit flags always win over the dice."""
    org = args.org or (weighted_pick(ORG_WEIGHTS, uniform) if random_fill else "solitary")
    size = args.size or (weighted_pick(SIZE_WEIGHTS, uniform) if random_fill else "small")
    armor = args.armor or (
        weighted_pick(ARMOR_WEIGHTS, uniform) if random_fill else "none"
    )
    known_for = [k.strip() for k in args.known_for.split(",") if k.strip()]
    armament = args.armament
    traits = [t.strip() for t in args.traits.split(",") if t.strip()]

    if random_fill:
        if not known_for:
            known_for = random.sample(list(KNOWN_FOR.keys()), k=random.randint(0, 2))
        if armament is None:
            armament = random.choice(list(ARMAMENTS.keys()) + [None, None])
        if not traits:
            pool = [t for t in TRAITS if t != "divine"] + ["divine"]
            traits = random.sample(pool, k=random.randint(0, 2))

    monster, final_die, meta = build_monster(
        org, size, armor, known_for, armament, traits, args.divine_bonus, args.name
    )
    return monster, final_die, meta, org, size, traits, known_for


def custom_difficulty_window(args):
    """(lo, hi) the custom monster must land in, or (None, None) for anywhere."""
    lo = args.difficulty_min
    hi = args.difficulty_max
    if args.party_levels is not None and hi is None:
        hi = ceiling_for(args.party_levels)
        if lo is None:
            # Aim at a real fight rather than anything at or under the ceiling,
            # which would usually return something trivially weak.
            lo = SOLO_THREAT_FRACTION * hi
    return lo, hi


def run_custom(args):
    # Unset categories are rolled unless --no-random. This used to be opt-in
    # via --random, which meant a bare `--custom` returned the same monster
    # every single time - solitary/small/none, i.e. d10, 12 HP, 0 armor - while
    # the bestiary path randomised by default. Two halves of one script with
    # opposite defaults, and the fixed one looked like a roll.
    random_fill = not args.no_random
    lo, hi = custom_difficulty_window(args)

    attempts = 1
    if lo is None and hi is None:
        rolled = roll_custom_once(args, random_fill)
    else:
        # Monte Carlo: reroll until the difficulty lands in the window, using
        # the same weighted rolls as an untargeted monster. Searching uniformly
        # converges in fewer attempts, but it gets there by leaning on whatever
        # single stat buys the most difficulty - typically maximum armor - so
        # the monster that comes back is an armor-5 lump rather than something
        # with its difficulty spread across the stat block. Measured cost of
        # weighting: see DIFFICULTY_ATTEMPTS.
        best = None
        for attempts in range(1, DIFFICULTY_ATTEMPTS + 1):
            candidate = roll_custom_once(args, random_fill)
            score = candidate[0]["difficulty"]
            if (lo is None or score >= lo) and (hi is None or score <= hi):
                best = candidate
                break
            if best is None or abs(score - ((lo or 0) + (hi or 0)) / 2) < abs(
                best[0]["difficulty"] - ((lo or 0) + (hi or 0)) / 2
            ):
                best = candidate
        else:
            print(
                "Warning: no roll landed in the difficulty window %s-%s after "
                "%d attempts; returning the closest (%s). Widen the window, or "
                "unpin some categories - explicit --org/--size/--armor flags "
                "limit what can be rolled."
                % (lo, hi, DIFFICULTY_ATTEMPTS, best[0]["difficulty"]),
                file=sys.stderr,
            )
        rolled = best

    monster, final_die, meta, org, size, traits, known_for = rolled

    # Themes drive the seed words and the form favour lists alike, so resolve
    # them once if either block is going to run.
    themes_used = None
    lexicon = None
    pool = {}
    if not (args.no_seeds and args.no_form):
        lexicon = load_lexicon()
        themes_used, pool = resolve_themes(lexicon, args.theme)

    # Rolled before the seed words so the blank-field hints can point at a body,
    # and outside the difficulty search above because form has no bearing on
    # difficulty - rolling it in there would be work thrown away on every retry.
    form = None
    if not args.no_form:
        form = roll_form(
            traits, themes_used,
            favour_lists(lexicon, themes_used, "morphology_favour"),
            favour_lists(lexicon, themes_used, "physiology_favour"),
        )
        monster = dict(monster, form=form)

    if not args.no_seeds:
        tier = deadliness_tier(
            final_die, meta["dmg_bonus"], meta["advantage"], meta["special_count"]
        )
        seeds = seed_words(lexicon, pool, tier)
        monster = dict(monster, seed_words=seeds)

        # Offer capabilities rather than choosing one. Same contract as every
        # other seeded field: the generator supplies material, the model
        # decides.
        #
        # The options live in their own key rather than inside special_quality,
        # so that field keeps the same type the bestiary gives it - a plain
        # string. Cramming a menu into it (as an "A OR B OR C" string, or by
        # making it a list) would mean custom and bestiary monsters disagree
        # about what special_quality is, which is the exact problem that moving
        # built_from out of it just fixed.
        pool_qualities = pool.get("quality") or []
        if pool_qualities:
            monster["special_quality_options"] = random.sample(
                pool_qualities, k=min(QUALITY_OPTIONS, len(pool_qualities))
            )
            # Constrain the FORM, not just the length. The failure this guards
            # against is an explanatory tail - "Lures with a borrowed sound -
            # mimics something it heard once (a call, a voice) to draw prey off
            # the path" - which is a sentence about a quality, not a quality.
            # A word cap alone would not catch it, and a hard cap of three
            # would reject real bestiary entries: 90% are 1-3 words, but
            # "Unerring sense of direction" and "Only killed by a blow to the
            # heart" are both legitimate.
            monster["special_quality_note"] = (
                "Pick one as-is, or coin a new one by combining two. Match the "
                "register: a bare noun phrase, 1-3 words (90% of the bestiary's "
                "are), five at the very most. No sentence, no verb clause "
                "explaining how it works, no parenthetical, no dash-tail. A "
                "comma may join two qualities; hyphens are fine. Write it into "
                "special_quality and drop these two keys - a stat block should "
                "not ship with its own menu."
            )

        # Point the blank fields at the material rather than leaving them as a
        # bare "(write one)". The generator supplies raw material and says so;
        # it does not pretend to have authored anything.
        # Naming the body first is the whole point of the form block: a
        # description written from textures alone is what produced vague
        # creatures that abstractly moved and abstractly attacked.
        body_hint = ""
        if form:
            body_hint = " settle a body first from form.morphology_options (%s) and a substance from form.physiology_options;" % (
                "; ".join(
                    "%s, %s, %s" % (option["morphology"], option["limbs"],
                                    option["integument"])
                    for option in form["morphology_options"]
                )
            )
        monster["description"] = (
            "(write one -%s seed textures: %s; detail to work in: %s)"
            % (body_hint, ", ".join(seeds["texture"]),
               (seeds["evocative"] or ["-"])[0])
        )
        monster["instinct"] = "(write one - seed drives: %s)" % ", ".join(seeds["drive"])
        monster["moves"] = [
            "(write 1-3 - seed actions: %s)" % ", ".join(seeds["action"])
        ]
        if not monster["name"]:
            monster["name"] = (
                "(name it - combine %s + %s, register: %s. See the naming "
                "patterns in references/treasure-and-monster-building.md)"
                % (
                    "/".join(seeds["substance"][:3]),
                    "/".join(seeds["bodypart"][:3]),
                    ", ".join(seeds["deadliness"]["words"][:3]),
                )
            )

    if not args.no_behavior:
        monster = dict(
            monster,
            behavior=roll_behaviour(size, final_die, org, traits, known_for),
        )

    if not args.no_treasure:
        advantage, notes = treasure_tag_effects(monster)
        if args.treasure_bonus:
            notes = notes + ["Bonus: +%dd4 on the roll" % args.treasure_bonus]
        rolls, results = roll_treasure(
            final_die, advantage=advantage, bonus_d4=args.treasure_bonus
        )
        haul = {"creature": 1, "die": final_die, "rolls": rolls, "results": results}
        if notes:
            haul["notes"] = notes
        # Same shape as the bestiary path: a custom monster is one creature, so
        # there is no pairing note to make.
        monster = dict(monster, treasure={"rolled_for": 1, "hauls": [haul]})

    payload = {
        "setting": None,
        "setting_name": "(custom monster - not from the bestiary)",
        "themes": themes_used,
        "filter": (
            None
            if lo is None and hi is None
            else {
                "party_levels": args.party_levels,
                "difficulty_window": [lo, hi],
                "difficulty": monster["difficulty"],
                "rolls_taken": attempts,
            }
        ),
        "monsters": [monster],
    }
    emit(payload, pretty=args.pretty)

    print(
        "Note: a custom monster has no description, instinct or moves - you "
        "must write them. An official monster (run with no arguments for the "
        "setting list) comes with all three already written.",
        file=sys.stderr,
    )
    print("Reminder: update gm and character yaml files now!", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
