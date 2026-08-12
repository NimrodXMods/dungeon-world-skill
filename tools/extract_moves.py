#!/usr/bin/env python3
"""
Extract Dungeon World move text from the vendored rulebook XML into structured
JSON for the player dashboard.

Source: skills/dungeon-world-gm/references/rulebook-digest/source/xml/
(the authors' own published text, CC BY 3.0, credit Sage LaTorra & Adam Koebel;
pinned - see that tree's source/ATTRIBUTION.md). Read from the vendored copy so
the dashboard and the rulebook digest can never be built from different
revisions of the text.

Output shape:

    {
      "basic":   [ {"name": ..., "blocks": [...]}, ... ],   # Moves.xml, <h1>Basic Moves
      "special": [ {"name": ..., "blocks": [...]}, ... ],   # Moves.xml, <h1>Special Moves
      "classes": { "Thief": { "starting": [...], "advanced": [...] }, ... }
    }

A block is either {"t": "p", "spans": [{"b": bool, "s": text}, ...]}
or {"t": "ul", "items": ["...", ...]}.

Paragraphs keep their bold spans because Dungeon World's convention is that the
move's *trigger* is bolded ("When you *attack an enemy in melee*..."), which is
the part a player scans for. Splitting into spans lets the page rebuild that
emphasis while still setting every string with textContent - the dashboard never
puts campaign or rulebook text through innerHTML.

Usage:
    python3 tools/extract_moves.py \\
        skills/dungeon-world-gm/references/rulebook-digest/source/xml \\
        skills/dungeon-world-gm/assets/moves.json
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# The XML declares the AdobeInDesign namespace for its pstyle attributes.
AID = "{http://ns.adobe.com/AdobeInDesign/4.0/}pstyle"

# One file per class. The class name is the <h1>, e.g. "The Thief" -> "Thief".
CLASS_FILES = [
    "Bard.xml", "Cleric.xml", "Druid.xml", "Fighter.xml",
    "Paladin.xml", "Ranger.xml", "Thief.xml", "Wizard.xml",
]

# Only these sections hold class moves. "Alignment" and the race entries also
# use <h3>, so a bare "every h3 in the file" sweep would drag them in.
MOVE_SECTIONS = {"Starting Moves": "starting", "Advanced Moves": "advanced"}


def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def spans_of(element):
    """Flatten a <p> into [{"b": is_bold, "s": text}], merging adjacent runs."""
    out = []

    def push(text, bold):
        if not text:
            return
        if out and out[-1]["b"] == bold:
            out[-1]["s"] += text
        else:
            out.append({"b": bold, "s": text})

    push(element.text or "", False)
    for child in element:
        bold = child.tag in ("strong", "b", "em", "i")
        inner = "".join(child.itertext())
        push(inner, bold)
        push(child.tail or "", False)

    for span in out:
        span["s"] = re.sub(r"\s+", " ", span["s"])
    # Trim the outer edges only; interior spacing carries meaning between spans.
    if out:
        out[0]["s"] = out[0]["s"].lstrip()
        out[-1]["s"] = out[-1]["s"].rstrip()
    return [s for s in out if s["s"]]


def blocks_until_next_heading(nodes, start, stop_tags):
    """Collect <p>/<ul> siblings following a heading, until the next heading."""
    blocks = []
    for node in nodes[start:]:
        if node.tag in stop_tags:
            break
        if node.tag == "p":
            spans = spans_of(node)
            if spans:
                blocks.append({"t": "p", "spans": spans})
        elif node.tag == "ul":
            items = [squash("".join(li.itertext())) for li in node.findall("li")]
            items = [i for i in items if i]
            if items:
                blocks.append({"t": "ul", "items": items})
    return blocks


# Layout wrappers with no semantic meaning. They nest inconsistently across the
# source files - Moves.xml splits one logical section across two <Story>
# elements, while the class files bury every <h3> inside a <div> that follows
# its <h2>. Hoisting them all into one linear stream means the parser never has
# to care where those boundaries happen to fall.
CONTAINERS = {"Story", "Body", "div", "Root"}


def flatten(root):
    """Depth-first stream of content elements, with layout wrappers removed."""
    out = []

    def walk(node):
        for child in node:
            if child.tag in CONTAINERS:
                walk(child)
            else:
                out.append(child)

    walk(root)
    return out


def parse_moves_file(path):
    """Moves.xml -> (basic, special), each a list of {name, blocks}."""
    nodes = flatten(ET.parse(path).getroot())
    sections = {}
    current = None

    for index, node in enumerate(nodes):
        if node.tag == "h1":
            current = squash("".join(node.itertext()))
            sections[current] = []
        elif node.tag == "h2" and current:
            sections[current].append({
                "name": squash("".join(node.itertext())),
                "blocks": blocks_until_next_heading(nodes, index + 1, ("h1", "h2")),
            })

    missing = [k for k in ("Basic Moves", "Special Moves") if not sections.get(k)]
    if missing:
        sys.exit("Moves.xml: no entries found for {}".format(", ".join(missing)))
    return sections["Basic Moves"], sections["Special Moves"]


def parse_class_file(path):
    """A class XML -> (class_name, {"starting": [...], "advanced": [...]})."""
    nodes = flatten(ET.parse(path).getroot())

    name = None
    for node in nodes:
        if node.tag == "h1":
            name = re.sub(r"^The\s+", "", squash("".join(node.itertext())))
            break
    if not name:
        sys.exit("{}: no <h1> class name".format(path.name))

    result = {"starting": [], "advanced": []}
    bucket = None

    for index, node in enumerate(nodes):
        if node.tag == "h2":
            bucket = MOVE_SECTIONS.get(squash("".join(node.itertext())))
        elif node.tag == "h3" and bucket:
            style = node.get(AID, "")
            # Race moves inside Starting Moves carry MoveName like the class
            # moves do, so style cannot separate them; they are filtered by the
            # caller against what characters actually record. Keep them all -
            # a Halfling Thief legitimately has "Halfling" as a starting move.
            result[bucket].append({
                "name": squash("".join(node.itertext())),
                "blocks": blocks_until_next_heading(nodes, index + 1, ("h1", "h2", "h3")),
                "style": style,
            })

    for bucket_name in result:
        for move in result[bucket_name]:
            move.pop("style", None)
    return name, result


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__.strip().splitlines()[-1])
    xml_dir = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    basic, special = parse_moves_file(xml_dir / "Moves.xml")

    classes = {}
    for filename in CLASS_FILES:
        path = xml_dir / filename
        if not path.is_file():
            sys.exit("missing class file: {}".format(path))
        name, moves = parse_class_file(path)
        classes[name] = moves

    payload = {"basic": basic, "special": special, "classes": classes}
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("wrote {}".format(out_path))
    print("  basic   : {} moves".format(len(basic)))
    print("  special : {} moves".format(len(special)))
    for name in sorted(classes):
        print("  {:9s}: {} starting, {} advanced".format(
            name, len(classes[name]["starting"]), len(classes[name]["advanced"])))


if __name__ == "__main__":
    main()
