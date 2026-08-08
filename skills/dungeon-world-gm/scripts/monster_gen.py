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
    python3 monster_gen.py --custom --random              # old quick builder

Monsters are emitted as JSON, tab-indented. All warnings and reminders go to
stderr so stdout stays parseable.
"""
import argparse
import json
import math
import random
import re
import sys
from pathlib import Path


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

BESTIARY = Path(__file__).resolve().parent.parent / "assets" / "monsters.json"

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

# (template, {placeholder: dice expression}). The dice are rolled here and the
# concrete number substituted in, so a caller never gets "2d8 or so" back and
# never has to make a second tool call to find out what it actually got.
TREASURE_TABLE = {
    1: ("A few coins: {coins} coins", {"coins": "2d8"}),
    2: ("An item useful to the current situation", {}),
    3: ("Several coins: {coins} coins", {"coins": "4d10"}),
    4: ("A small valuable item (gem or art) worth {value} coins, 0 weight",
        {"value": "2d10*10"}),
    5: ("A minor magical trinket", {}),
    6: ("Useful information (clues, notes, etc.)", {}),
    7: ("A bag of {coins} coins, {weight} weight", {"coins": "1d4*100"}),
    8: ("A very valuable small item worth {value} coins, 0 weight",
        {"value": "2d6*100"}),
    9: ("A chest of coins and valuables worth {value} coins, 1 weight",
        {"value": "3d6*100"}),
    10: ("A magical item or effect", {}),
    11: ("Many bags of coins: {coins} coins, {weight} weight",
         {"coins": "2d4*100"}),
    12: ("A sign of office worth {value} coins", {"value": "3d4*100"}),
    13: ("A large art item worth {value} coins, 1 weight", {"value": "4d4*100"}),
    14: ("A unique item worth {value} coins", {"value": "5d4*100"}),
    15: ("Information leading to a new spell", {}),
    16: ("A portal or secret path", {}),
    17: ("Something relating to one of the characters", {}),
    18: ("A hoard: {coins} coins, plus {gems} gems worth {gem_value} coins each",
         {"coins": "1d10*1000", "gems": "1d10*10", "gem_value": "2d6*100"}),
}

# 15, 16 and 17 each give their own result AND send you back for another roll.
ROLL_AGAIN = (15, 16, 17)
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
    """Return (monster_dict, final_die) using the bestiary's own key names."""
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
        "special_quality": "; ".join(special_qualities),
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
    return monster, die


DICE_EXPR = re.compile(r"^(\d+)d(\d+)(?:\*(\d+))?$")
DAMAGE_DIE = re.compile(r"[bw]?\[?\s*\d*d(\d+)")


def roll_expr(expr):
    """'2d8' -> a rolled total; '2d10*10' -> that total times 10."""
    match = DICE_EXPR.match(expr)
    if not match:
        raise ValueError("bad dice expression: %r" % expr)
    count, sides, mult = (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3) or 1),
    )
    return sum(random.randint(1, sides) for _ in range(count)) * mult


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
    """One table entry, with its dice already rolled into real numbers."""
    template, spec = TREASURE_TABLE[min(max(roll, 1), 18)]
    values = {name: roll_expr(expr) for name, expr in spec.items()}
    if "{weight}" in template and "coins" in values:
        values["weight"] = max(1, values["coins"] // 100)
    return template.format(**values)


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
        if value not in ROLL_AGAIN:
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

CUSTOM OPTIONS (only with --custom)
  --random            fill any unset category randomly
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
  JSON on stdout, tab-indented: {setting, setting_name, filter, monsters[]}.
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


def emit(payload):
    json.dump(payload, sys.stdout, indent="\t", ensure_ascii=False)
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
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                    help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    if args.seed is not None:
        print(
            "Warning: Do not use --seed in a real game! If you did then re-read "
            "gameplay-loop.md now!",
            file=sys.stderr,
        )
        random.seed(args.seed)

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
        }
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
        }
    )
    print("Reminder: update gm and character yaml files now!", file=sys.stderr)
    return 0


def run_custom(args):
    random_fill = args.random is not None
    org = args.org or (random.choice(list(ORG.keys())) if random_fill else "solitary")
    size = args.size or (random.choice(list(SIZE.keys())) if random_fill else "small")
    armor = args.armor or (random.choice(list(ARMOR.keys())) if random_fill else "none")
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

    monster, final_die = build_monster(
        org, size, armor, known_for, armament, traits, args.divine_bonus, args.name
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
        "filter": None,
        "monsters": [monster],
    }
    emit(payload)

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
