#!/usr/bin/env python3
"""Shared treasure data and composition, for monster_gen.py and idea_gen.py.

Not a CLI. This is a sibling module: running `python3 scripts/<name>.py` puts
scripts/ on sys.path[0], so callers reach it with a bare `import _treasure` and
no package, __init__.py or install step is needed. The leading underscore is
deliberate - sys.path[0] being the scripts directory means an unprefixed name
here could shadow a stdlib module for every script in the skill.

It holds no roll scheme of its own. The two callers roll INTO the table
differently on purpose: monster_gen.py rolls the monster's damage die plus tag
bonuses, and idea_gen.py, which has no monster and so no damage die, rolls an
exploding d6. Sharing the data without sharing the roll is the whole point -
the table used to exist twice and had already drifted (see assets/treasure.json).

Nothing here runs at import time.
"""

import json
import random
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "assets" / "treasure.json"

DICE_EXPR = re.compile(r"^(\d+)d(\d+)(?:\*(\d+))?$")

# How many appearances to offer for one abstract value-table entry. It is a
# menu, not a decision: "a small valuable item worth 140 coins" says nothing
# about what the thing IS, and committing to one look would make this the only
# part of the pipeline that decides for the model instead of handing over
# options. Three is enough to choose between without being a list to wade
# through - the same reasoning, and the same number, as monster_gen.py's
# QUALITY_OPTIONS and FORM_OPTIONS.
OBJECT_OPTIONS = 3

# Traits the composer understands. assets/treasure.json documents what each
# means for authors; validate_skill.py checks every one is used by at least one
# object_type, which catches a trait renamed in one place and not the other.
KNOWN_TRAITS = ("gem", "gem_optional", "depicts", "liquid")

# Traits held back when the menu is describing a value_table entry. Those
# entries name their own kind - "a small valuable item (gem or art)", "a large
# art item" - so a potion or a vial of poison contradicts the very line it is
# meant to be illustrating. They stay in the table and stay reachable from a
# bare object roll, where nothing has claimed the thing is art.
VALUE_EXCLUDED = ("liquid",)

# One time in six a material comes from the exotic tier instead of the mundane
# one, and a gem_optional object is actually set with a stone one time in three.
# Both are "rare enough to stay an event" rather than tuned numbers.
EXOTIC_IN = 6
GEM_OPTIONAL_IN = 3

_CACHE = None


class TreasureDataError(Exception):
    """Raised when the asset is missing or unusable - callers decide how loudly
    to fail, since monster_gen.py exits and idea_gen.py may want to carry on."""


def load():
    """Read and cache assets/treasure.json."""
    global _CACHE
    if _CACHE is None:
        try:
            with DATA.open(encoding="utf-8") as handle:
                _CACHE = json.load(handle)
        except OSError as exc:
            raise TreasureDataError("cannot read {}: {}".format(DATA, exc))
        except ValueError as exc:
            raise TreasureDataError("{} is not valid JSON: {}".format(DATA, exc))
    return _CACHE


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


def roll_again_values():
    """Entries that give a result AND send the roller back for another."""
    return tuple(load().get("roll_again", ()))


def value_entry(roll):
    """One value-table entry with its dice resolved.

    Returns (text, is_object). is_object marks an entry whose appearance is left
    abstract and can therefore carry composed options - see describe_options.
    """
    table = load()["value_table"]
    key = str(min(max(int(roll), 1), 18))
    entry = table[key]
    values = {name: roll_expr(expr) for name, expr in entry.get("dice", {}).items()}
    template = entry["template"]
    if "{weight}" in template and "coins" in values:
        values["weight"] = max(1, values["coins"] // 100)
    return template.format(**values), bool(entry.get("object"))


def describe_value(roll):
    """value_entry's text alone, for callers that don't care about options."""
    return value_entry(roll)[0]


# --- appearance -----------------------------------------------------------


def categories():
    """Independently rollable appearance categories, for #19's per-axis access."""
    objects = load()["objects"]
    return sorted(objects.keys())


def roll_category(name):
    """One roll from a single named category.

    Deliberately one result rather than a menu: the caller has already narrowed
    to one axis, and callers that want several can ask several times.
    """
    objects = load()["objects"]
    if name not in objects:
        raise KeyError(name)
    table = objects[name]
    if name == "material":
        return _roll_material(table)
    if name == "object_type":
        return random.choice(table)["name"]
    return random.choice(table)


def _roll_material(table=None):
    table = table if table is not None else load()["objects"]["material"]
    tier = "exotic" if random.randint(1, EXOTIC_IN) == 1 else "mundane"
    return random.choice(table[tier])


def _a(phrase):
    """'iron hand mirror' -> 'an iron hand mirror'. Good enough for these word
    lists, which contain no 'a unicorn'/'an hour' traps."""
    return "{} {}".format("an" if phrase[:1].lower() in "aeiou" else "a", phrase)


def _compose(object_type):
    """One object description, and the categories that went into it.

    The traits are what keep this from being mad-libs. A gem IS its own
    material and cannot be engraved with a portrait; a potion has no material
    of its own, only a vessel.

    The category list is returned alongside because which tables fired varies
    with the traits - a gem uses gem_type and color where a censer uses
    material and motif - so it is the only honest way to show what a given
    result was built from, and it doubles as a menu of the axes a caller can
    reroll on its own with treasure-object:CATEGORY.
    """
    objects = load()["objects"]
    traits = set(object_type.get("traits", ()))
    name = object_type["name"]
    used = ["object_type"]

    if "gem" in traits:
        head = _a("{} {}".format(
            random.choice(objects["color"]), random.choice(objects["gem_type"])
        ))
        used += ["color", "gem_type"]
        if name != "loose stone":
            head += " ({})".format(name)
    elif "liquid" in traits:
        head = "{} in {} vial".format(_a(name), _a(_roll_material()))
        used.append("material")
    else:
        head = _a("{} {}".format(_roll_material(), name))
        used.append("material")
        if "gem_optional" in traits and random.randint(1, GEM_OPTIONAL_IN) == 1:
            head += ", set with {}".format(_a("{} {}".format(
                random.choice(objects["color"]), random.choice(objects["gem_type"])
            )))
            used += ["color", "gem_type"]

    parts = [head, random.choice(objects["condition"]), random.choice(objects["provenance"])]
    used += ["condition", "provenance"]
    if "depicts" in traits:
        parts.append("showing {}".format(random.choice(objects["motif"])))
        used.append("motif")
    return {"text": ", ".join(parts), "categories": used}


def describe_options(count=OBJECT_OPTIONS, exclude_traits=()):
    """`count` alternative appearances for the SAME piece of treasure.

    The value and weight were rolled once by the caller and are not re-rolled
    here - only the look differs, so which option gets picked never changes what
    the thing is worth. Types are drawn without replacement so a menu never
    offers three variations of one idea.

    exclude_traits drops whole kinds of object from the draw. It exists because
    the value-table entries say what they are ("a small valuable item (gem or
    art)"), and a potion offered against that line contradicts the text it is
    supposed to be describing - see VALUE_EXCLUDED.

    Each option is {"text": ..., "categories": [...]} - see _compose.
    """
    pool = [
        ot for ot in load()["objects"]["object_type"]
        if not (set(ot.get("traits", ())) & set(exclude_traits))
    ]
    count = max(1, min(count, len(pool)))
    return [_compose(ot) for ot in random.sample(pool, count)]
