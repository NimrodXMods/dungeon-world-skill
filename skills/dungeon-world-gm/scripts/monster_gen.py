#!/usr/bin/env python3
"""
Monster stat-block builder for Dungeon World.

Walks the "pick one from each category" quick monster builder
(references/treasure-and-monster-building.md, from the core rulebook's
Monsters chapter) and outputs a finished stat block.

Usage:
    python3 monster_gen.py --random                       # fully random monster
    python3 monster_gen.py --org solitary --size huge --armor steel \\
        --known-for strength,endurance --armament vicious \\
        --traits ancient,terrifying --name "The Gray Wyrm"
    python3 monster_gen.py --random --treasure             # also roll its treasure
    python3 monster_gen.py --random --seed 7

Categories (all optional; unset ones are randomly rolled unless --no-fill-random):
  --org        horde | group | solitary
  --size       tiny | small | large | huge
  --armor      none | leather | mail | steel | magical
  --known-for  comma list from: strength, offense, defense, deft, endurance
  --armament   one of: vicious, weak, metal, ignores
  --traits     comma list from: shield, noanatomy, divine, animated, devious,
               ancient, abhors, stealthy, organized, intelligent, terrifying
  --divine-bonus  damage | hp | both   (only matters if 'divine' is in --traits)

Die ladder used for size-stepping effects (ancient/ devious/ weak/ small_weak):
d4 < d6 < d8 < d10 < d12
"""
import argparse
import random
import sys

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

TREASURE_TABLE = {
    1: "A few coins (2d8 or so)",
    2: "An item useful to the current situation",
    3: "Several coins (~4d10)",
    4: "A small valuable item (gem/art), worth 2d10x10 coins, 0 weight",
    5: "A minor magical trinket",
    6: "Useful information (clues, notes, etc.)",
    7: "A bag of coins, 1d4x100 (1 weight per 100 coins)",
    8: "A very valuable small item, worth 2d6x100 coins, 0 weight",
    9: "A chest of coins/valuables, 1 weight, worth 3d6x100 coins",
    10: "A magical item or effect",
    11: "Many bags of coins, 2d4x100",
    12: "A sign of office worth 3d4x100 coins",
    13: "A large art item worth 4d4x100 coins, 1 weight",
    14: "A unique item worth 5d4x100 coins",
    17: "Something relating to one of the characters",
    18: "A hoard: 1d10x1000 coins + 1d10x10 gems worth 2d6x100 each",
}


def step_die(size, steps):
    idx = DIE_LADDER.index(size)
    idx = max(0, min(len(DIE_LADDER) - 1, idx + steps))
    return DIE_LADDER[idx]


def build_monster(org, size, armor, known_for, armament, traits, divine_bonus, name):
    org_data = ORG[org]
    size_data = SIZE[size]

    hp = org_data["hp"] + size_data["hp_mod"]
    dmg_bonus = size_data["dmg_mod"]
    die = org_data["die"]
    armor_val = ARMOR[armor]
    tags = [org_data["label"].split(" (")[0], size, size_data["range"]]
    special_qualities = []
    move_notes = []

    for k in known_for:
        desc = KNOWN_FOR[k]
        if k == "strength":
            dmg_bonus += 2
            tags.append("Forceful")
        elif k == "offense":
            move_notes.append("roll damage twice, take the better (advantage)")
        elif k == "defense":
            armor_val += 1
        elif k == "deft":
            tags.append("1 piercing")
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
            tags += ["2 piercing", "Messy"]
        elif armament == "ignores":
            tags.append("Ignores Armor")

    for t in traits:
        desc = TRAITS[t]
        if t in DESCRIPTIVE_ONLY:
            tags.append(t.capitalize())
            continue
        if t == "divine":
            bonus_desc = {"damage": "+2 damage", "hp": "+2 HP", "both": "+2 damage and +2 HP"}[divine_bonus]
            desc = f"Favored by the gods (Divine, {bonus_desc})"
        special_qualities.append(desc)
        if t == "shield":
            tags.append("Cautious")
            armor_val += 1
        elif t == "noanatomy":
            armor_val += 1
            hp += 3
        elif t == "divine":
            tags.append("Divine")
            if divine_bonus in ("damage", "both"):
                dmg_bonus += 2
            if divine_bonus in ("hp", "both"):
                hp += 2
        elif t == "animated":
            hp += 4
        elif t == "devious":
            tags.append("Devious")
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

    lines = []
    lines.append(name or "(unnamed monster)")
    lines.append(f"  Tags: {', '.join(tags)}")
    lines.append(f"  Attack: {damage_str} damage" + (f" ({'; '.join(move_notes)})" if move_notes else ""))
    lines.append(f"  HP: {hp}   Armor: {armor_val}")
    if special_qualities:
        lines.append(f"  Special Qualities: {'; '.join(special_qualities)}")
    lines.append("  Instinct: (fill in - what does it want that causes problems for others?)")
    lines.append("  Moves: (write 1-3, describing its primary attack and any special qualities above)")
    return "\n".join(lines), die


def roll_treasure(die, bonus_dice_desc=None):
    total = random.randint(1, die)
    reroll_used = []
    while total in (15, 16, 17) and total in (15, 16):
        # 15/16 say "roll again"; 17 has its own text (kept), so only reroll 15/16
        reroll_used.append(total)
        total = random.randint(1, die)
    if total >= 18:
        desc = TREASURE_TABLE[18]
    elif total in (15, 16):
        desc = "roll again result: " + TREASURE_TABLE.get(total, "(reroll)")
    else:
        desc = TREASURE_TABLE.get(total, "(nothing - roll came up under the table's range)")
    return total, desc


HELP_LLM = """\
monster_gen.py - Dungeon World monster stat-block builder ("pick one from
each category" quick monster builder, references/treasure-and-monster-
building.md, core rulebook Monsters chapter).

USAGE
  monster_gen.py [--random] [--org O] [--size S] [--armor A]
                  [--known-for K1,K2,...] [--armament M] [--traits T1,T2,...]
                  [--divine-bonus damage|hp|both] [--name NAME] [--treasure]
                  [--seed N]

Every category is optional; --random fills in any category left unset
(rolled independently per category) instead of leaving it at its default.
Without --random, an unset category falls back to a fixed default
(org=solitary, size=small, armor=none, no known-for/armament/traits).

--org        horde | group | solitary
--size       tiny | small | large | huge
--armor      none | leather | mail | steel | magical
--known-for  comma list, any of: strength, offense, defense, deft, endurance
--armament   one of: vicious, weak, metal, ignores
--traits     comma list, any of: shield, noanatomy, divine, animated,
             devious, ancient, abhors, stealthy, organized, intelligent,
             terrifying
--divine-bonus damage|hp|both  (default both; only matters if 'divine' is
             in --traits)
--name NAME  give the stat block a name instead of leaving it blank
--treasure   also roll its treasure (1-18 table, keyed off final damage die)
--seed N     reproducible output - dev/debug only, NEVER during play

Die ladder used for size-stepping effects (ancient/devious/weak/small_weak
armament): d4 < d6 < d8 < d10 < d12.

OUTPUT
  A finished stat block (org/size/armor/HP/damage/tags resolved into final
  numbers, not left as separate modifiers to add up by hand), plus a
  Treasure line if --treasure was given.
  Always ends with a reminder to update yaml files.

EXAMPLES
  monster_gen.py --random --treasure
  monster_gen.py --org solitary --size huge --armor steel \\
      --known-for strength,endurance --armament vicious \\
      --traits ancient,terrifying --name "The Gray Wyrm"
  monster_gen.py --random --seed 7
"""


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return

    ap = argparse.ArgumentParser(description="Build a Dungeon World monster stat block.")
    ap.add_argument("--random", action="store_true", help="Randomly fill in any unset categories")
    ap.add_argument("--org", choices=list(ORG.keys()), default=None)
    ap.add_argument("--size", choices=list(SIZE.keys()), default=None)
    ap.add_argument("--armor", choices=list(ARMOR.keys()), default=None)
    ap.add_argument("--known-for", default="", help="Comma list: " + ",".join(KNOWN_FOR.keys()))
    ap.add_argument("--armament", choices=list(ARMAMENTS.keys()), default=None)
    ap.add_argument("--traits", default="", help="Comma list: " + ",".join(TRAITS.keys()))
    ap.add_argument("--divine-bonus", choices=["damage", "hp", "both"], default="both")
    ap.add_argument("--name", default=None)
    ap.add_argument("--treasure", action="store_true", help="Also roll its treasure")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                     help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    if args.seed is not None:
        print("Warning: Do not use --seed in a real game! If you did then re-read gameplay-loop.md now!")
        random.seed(args.seed)

    org = args.org or (random.choice(list(ORG.keys())) if args.random else "solitary")
    size = args.size or (random.choice(list(SIZE.keys())) if args.random else "small")
    armor = args.armor or (random.choice(list(ARMOR.keys())) if args.random else "none")
    known_for = [k.strip() for k in args.known_for.split(",") if k.strip()]
    armament = args.armament
    traits = [t.strip() for t in args.traits.split(",") if t.strip()]

    if args.random:
        if not known_for:
            known_for = random.sample(list(KNOWN_FOR.keys()), k=random.randint(0, 2))
        if armament is None:
            armament = random.choice(list(ARMAMENTS.keys()) + [None, None])  # weighted toward none
        if not traits:
            pool = [t for t in TRAITS if t != "divine"] + ["divine"]
            traits = random.sample(pool, k=random.randint(0, 2))

    stat_block, final_die = build_monster(
        org, size, armor, known_for, armament, traits, args.divine_bonus, args.name
    )
    print(stat_block)

    if args.treasure:
        roll, desc = roll_treasure(final_die)
        print(f"\n  Treasure (rolled {roll} on d{final_die}): {desc}")

    print("Reminder: update gm and character yaml files now!")


if __name__ == "__main__":
    main()
