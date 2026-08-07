#!/usr/bin/env python3
"""
Extract Dungeon World bestiary data from the official monster_settings XML
(https://github.com/Sagelt/Dungeon-World/tree/master/text/monster_settings,
CC BY 3.0, credit Sage LaTorra & Adam Koebel) into structured JSON.

Provenance: skills/dungeon-world-gm/assets/monsters.json was generated from
this script against a clone of Sagelt/Dungeon-World at commit
e67bd51c09d24518a7f989149b76094fbcc7fecc (2023-02-27). To regenerate against
an updated source, re-clone that repo's text/monster_settings/ directory and
rerun this script; diff the output before committing, since the difficulty
formula and setting descriptions below are hand-tuned for this repo's needs
and not part of the upstream source.

Usage: python3 extract_monsters.py <xml_dir> <output.json>
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --- setting metadata (slug -> short/long description) -------------------
# Short/long descriptions are condensed paraphrases, not verbatim book text.
SETTING_META = {
    "Caverns.xml": {
        "slug": "cavern",
        "short_description": "Underground caverns and dungeons.",
        "long_description": (
            "The dark, close spaces beneath the earth - tunnels, caves, and "
            "delved-out dungeons. Home to burrowing things, cave-dwelling "
            "predators, and the folk (dwarven and otherwise) who carve out a "
            "living underground."
        ),
    },
    "Depths.xml": {
        "slug": "depths",
        "short_description": "The deep places below the world, past where most dare go.",
        "long_description": (
            "Far beneath the caverns lie the lower depths - ancient, alien "
            "spaces few mortals have seen. What lives here is old, powerful, "
            "and often unconcerned with anything happening on the surface."
        ),
    },
    "Experiments.xml": {
        "slug": "experiments",
        "short_description": "Twisted creations of magic and unnatural science.",
        "long_description": (
            "Things that were made, not born - constructs, magical hybrids, "
            "and the failed (or all-too-successful) results of someone's "
            "experiments. Unnatural, often unstable, and rarely grateful to "
            "their creators."
        ),
    },
    "Folk.xml": {
        "slug": "folk",
        "short_description": "The people and near-people of the civilized world.",
        "long_description": (
            "Humanoid folk who live in and around civilization - some "
            "friendly, some hostile, most just trying to get by. Includes "
            "bandits, cultists, and other people the party might have to "
            "fight, trick, or befriend."
        ),
    },
    "Hordes.xml": {
        "slug": "hordes",
        "short_description": "Creatures that come in overwhelming numbers.",
        "long_description": (
            "Swarming, breeding, ravenous things that rarely travel alone. "
            "Individually they may be weak, but a horde is a different kind "
            "of threat entirely - and some of what lurks among them is not "
            "weak at all."
        ),
    },
    "Planes.xml": {
        "slug": "planes",
        "short_description": "Beings from beyond Dungeon World entirely.",
        "long_description": (
            "Visitors and invaders from other planes of existence - "
            "elemental, celestial, infernal, and stranger things still. "
            "They follow rules that don't quite match the rest of the "
            "world, because they aren't from it."
        ),
    },
    "Swamp.xml": {
        "slug": "swamp",
        "short_description": "Denizens of bogs, marshes, and wetlands.",
        "long_description": (
            "The fetid, waterlogged places where things grow strange and "
            "hungry. Amphibious predators, swamp-dwelling folk, and old "
            "magic gone soft and rotten in the muck."
        ),
    },
    "Undead.xml": {
        "slug": "undead",
        "short_description": "The restless dead and those who command them.",
        "long_description": (
            "Creatures that should have stayed dead but didn't - risen by "
            "curse, necromancy, unfinished business, or spite. Ranges from "
            "shambling husks to cunning liches with plans centuries in the "
            "making."
        ),
    },
    "Woods.xml": {
        "slug": "woods",
        "short_description": "Creatures of the deep, wild forest.",
        "long_description": (
            "The old woods beyond the reach of civilization - fey things, "
            "beast-folk, and guardians of groves best left undisturbed. The "
            "forest has its own rules, and travelers ignore them at their "
            "peril."
        ),
    },
}

RANGE_WORDS = {"close", "reach", "near", "far", "hand"}
ORG_WORDS = {"solitary", "horde", "group"}
SIZE_WORDS = {"small", "medium", "large", "huge"}

# damage-die factor bucket, keyed by die size
DIE_FACTOR = {4: 0.5, 6: 0.8, 8: 1.0, 10: 1.2, 12: 1.5}


def die_factor(size):
    return DIE_FACTOR.get(size, 2.0)  # "larger" bucket for anything unlisted


def parse_damage_expr(expr):
    """
    Parse a damage expression like 'd8+1', 'b[2d12]+9', 'w[2d8-2]', 'd6-2'.
    Returns (die_factor_value, flat_modifier:int).
    """
    expr = expr.strip()
    # modifier may appear inside the brackets (w[2d8-2]) or after them (b[2d12]+9)
    m = re.match(r'^[bw]\[(\d+)d(\d+)([+-]\d+)?\]([+-]\d+)?$', expr)
    if m:
        count, size = int(m.group(1)), int(m.group(2))
        mod = m.group(3) or m.group(4)
        factor = count * die_factor(size)
        return factor, int(mod) if mod else 0
    m = re.match(r'^d(\d+)([+-]\d+)?$', expr)
    if m:
        size, mod = int(m.group(1)), m.group(2)
        return die_factor(size), int(mod) if mod else 0
    raise ValueError(f"unrecognized damage expression: {expr!r}")


def compute_difficulty(hp, armor, attack_str, special_quality_count):
    if hp is None or not attack_str:
        return None
    dm = re.search(r'\(([^)]*damage[^)]*)\)', attack_str)
    inner = dm.group(1) if dm else ""
    # split off the leading dice expression from qualifiers like
    # ", 1 piercing" / " ignores armor"
    parts = [p.strip() for p in inner.split(",")]
    first = parts[0]
    # first looks like "d8+1 damage" or "d8 damage ignores armor"
    m = re.match(r'^([bw]?\[?[\dd+\-\]]+)\s*damage', first)
    dice_expr = m.group(1) if m else first.split()[0]
    df, flat_mod = parse_damage_expr(dice_expr)

    # count special-ability units: qualifiers on the attack line itself
    # (ignores armor, piercing, messy, forceful, etc.) + Special Qualities items
    attack_quals = 0
    lowered = inner.lower()
    if "ignores armor" in lowered:
        attack_quals += 1
    if "piercing" in lowered:
        attack_quals += 1
    if "messy" in lowered:
        attack_quals += 1
    if "forceful" in lowered:
        attack_quals += 1
    total_special = attack_quals + special_quality_count

    difficulty = (
        hp
        * (1 + armor * 0.3)
        * df
        * (1 + 0.2 * flat_mod)
        * (1 + 0.3 * total_special)
    )
    return round(difficulty, 2)


def split_tags(tag_text):
    """Split a top tag string like 'Group, Large' into organization/size/traits."""
    items = [t.strip() for t in tag_text.split(",") if t.strip()]
    organization = None
    size = None
    traits = []
    for it in items:
        low = it.lower()
        if low in ORG_WORDS and organization is None:
            organization = it
        elif low in SIZE_WORDS and size is None:
            size = it
        else:
            traits.append(it)
    return organization, size, traits


def strip_ns(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def text_content(elem):
    """Get all text content of an element including tail text of children,
    stripping any leftover markup semantics (em/strong become plain text)."""
    parts = [elem.text or ""]
    for child in elem:
        parts.append(text_content(child))
        parts.append(child.tail or "")
    return "".join(parts)


def parse_file(path):
    tree = ET.parse(path)
    root = tree.getroot()

    h1 = root.find(".//h1")
    chapter_title = h1.text.strip() if h1 is not None and h1.text else ""

    body = root.find(".//Body")
    monsters = []
    current = None

    def flush():
        nonlocal current
        if current is not None:
            monsters.append(current)
        current = None

    for elem in body:
        tag = strip_ns(elem.tag)
        pstyle = elem.get("aid:pstyle") or elem.get(
            "{http://ns.adobe.com/AdobeInDesign/4.0/}pstyle"
        )
        if tag == "p" and pstyle == "MonsterName":
            flush()
            raw = text_content(elem)
            name_part, _, tag_part = raw.partition("\t")
            name = name_part.strip()
            organization, size, traits = split_tags(tag_part)
            current = {
                "name": name,
                "_top_organization": organization,
                "_top_size": size,
                "_top_traits": traits,
                "attack": None,
                "hp": None,
                "armor": None,
                "_range": [],
                "special_quality": "",
                "_special_quality_count": 0,
                "description": "",
                "instinct": "",
                "moves": [],
            }
        elif tag == "p" and pstyle == "MonsterStats":
            raw = text_content(elem)
            if "damage" in raw and current.get("attack") is None:
                # Attack (dmg)\tHP HP\tN Armor
                fields = raw.split("\t")
                attack_str = fields[0].strip()
                hp_m = re.search(r'(\d+)\s*HP', raw)
                armor_m = re.search(r'(\d+)\s*Armor', raw)
                current["attack"] = attack_str
                current["hp"] = int(hp_m.group(1)) if hp_m else None
                current["armor"] = int(armor_m.group(1)) if armor_m else None
            else:
                # range-tags-only line, e.g. "Close, Reach"
                items = [t.strip() for t in raw.split(",") if t.strip()]
                current["_range"].extend(items)
        elif tag == "p" and pstyle == "MonsterQualities":
            raw = text_content(elem)
            raw = re.sub(r'^\s*Special Qualities:\s*', '', raw).strip()
            current["special_quality"] = raw
            current["_special_quality_count"] = len(
                [q for q in raw.split(",") if q.strip()]
            )
        elif tag == "p" and pstyle == "MonsterDescription":
            raw = text_content(elem)
            m = re.search(r'Instinct:\s*(.*)$', raw)
            if m:
                current["instinct"] = m.group(1).strip()
                desc = raw[: m.start()]
            else:
                desc = raw
            desc = re.sub(r'\s+Instinct:\s*$', '', desc).strip()
            current["description"] = desc.strip()
        elif tag == "p" and pstyle == "NoIndent":
            # Used for a couple of entries whose flavor text is formatted as
            # verse rather than a prose paragraph (e.g. Treant). We do not
            # reproduce verse/poem text; only pull out the mechanical
            # Instinct line if it lands in one of these paragraphs. The
            # `description` field is left blank here and can be manually
            # backfilled with an original (non-quoting) description.
            raw = text_content(elem)
            m = re.search(r'Instinct:\s*(.*)$', raw)
            if m and current is not None:
                current["instinct"] = m.group(1).strip()
        elif tag == "ul":
            for li in elem:
                if strip_ns(li.tag) == "li":
                    current["moves"].append(text_content(li).strip())
    flush()

    # finalize: compute difficulty, assemble tags object, drop temp fields
    final_monsters = []
    for m in monsters:
        try:
            difficulty = compute_difficulty(
                m["hp"] or 0,
                m["armor"] or 0,
                m["attack"] or "",
                m["_special_quality_count"],
            )
        except Exception as e:
            raise RuntimeError(f"failed on monster {m['name']!r} attack={m['attack']!r}: {e}")
        description = DESCRIPTION_OVERRIDES.get(m["name"], m["description"])
        final_monsters.append(
            {
                "name": m["name"],
                "attack": m["attack"],
                "difficulty": difficulty,
                "special_quality": m["special_quality"],
                "hp": m["hp"],
                "armor": m["armor"],
                "tags": {
                    "range": m["_range"],
                    "organization": m["_top_organization"],
                    "size": m["_top_size"],
                    "traits": m["_top_traits"],
                },
                "description": description,
                "instinct": m["instinct"],
                "moves": m["moves"],
            }
        )
    return chapter_title, final_monsters


# A couple of entries have flavor text formatted as verse in the source
# rather than prose. We don't reproduce verse; these are original
# descriptions written independently, not paraphrases of the source poem.
DESCRIPTION_OVERRIDES = {
    "Treant": (
        "An ancient, towering tree given animate life and purpose. Treants "
        "move and react slowly, but are immensely strong once roused, and "
        "consider themselves the forest's rightful guardians - woodcutters "
        "and anyone else who threatens the trees should expect a hostile "
        "reception."
    ),
}


def main():
    xml_dir = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    result = {}
    for fname, meta in SETTING_META.items():
        fpath = xml_dir / fname
        chapter_title, monsters = parse_file(fpath)
        result[meta["slug"]] = {
            "name": chapter_title,
            "short_description": meta["short_description"],
            "long_description": meta["long_description"],
            "monsters": monsters,
        }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    total = sum(len(v["monsters"]) for v in result.values())
    print(f"Wrote {total} monsters across {len(result)} settings to {out_path}")


if __name__ == "__main__":
    main()
