#!/usr/bin/env python3
"""
Structured lookup into the Dungeon World core rulebook text (L3 of rulebook-digest).

The rulebook ships as the authors' own Adobe InDesign story XML, one file per
chapter, under references/rulebook-digest/source/xml/. This script is the only
supported way to read it: it turns headings into stable anchors, renders the XML
to plain text, and searches it.

Usage:
    python3 rulebook.py --outline
    python3 rulebook.py --outline --file cleric --depth 3
    python3 rulebook.py --anchor moves#basic-moves/hack-and-slash
    python3 rulebook.py --search 'Defy Danger' -C 2
    python3 rulebook.py --xpath './/h2' --file equipment
    python3 rulebook.py --check-anchors ../references/rulebook-digest/L1-digest.md

Anchors are computed from the heading path, never stored in the XML, so the
vendored files stay byte-identical to upstream. See source/ATTRIBUTION.md.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from _util import force_utf8_stdio

force_utf8_stdio()

XML_ROOT = (
    Path(__file__).resolve().parent.parent
    / "references"
    / "rulebook-digest"
    / "source"
    / "xml"
)

AID_NS = "http://ns.adobe.com/AdobeInDesign/4.0/"
NAMESPACES = {"aid": AID_NS}

HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4}

# Pure structure in the InDesign export - carries no text of its own, so the
# walker descends through it without emitting anything.
CONTAINER_TAGS = {
    "Root",
    "Story",
    "Body",
    "div",
    "Center",
    "StatTable",
    "TableBody",
    "TableHeader",
}

# pstyle values worth keeping as a visible label; the rest are layout-only.
MEANINGFUL_PSTYLES = {
    "MonsterName",
    "MonsterStats",
    "MonsterQualities",
    "MoveName",
    "BasicMoveName",
    "SpellName",
    "MagicItem",
    "Requirement",
}

# Matches an anchor citation in the digest, e.g. "[xml:moves#basic-moves]" or
# "[xml:cleric#the-cleric/starting-moves, cleric_spells#cleric-spells]".
CITATION_RE = re.compile(r"\[xml:([^\]]+)\]")

# Inline code spans are stripped before scanning, so prose that *describes* the
# syntax (`[xml:...]`) isn't mistaken for a real citation.
CODE_SPAN_RE = re.compile(r"`[^`]*`")

HELP_LLM = """\
rulebook.py - structured L3 lookup into the Dungeon World core rulebook text.

This replaces the old `grep "===== PAGE N ====="` flow. The rulebook is stored as
the authors' InDesign story XML (37 files, one per chapter) and addressed by
ANCHOR, not by page number. Page numbers still appear in L1-digest.md, but only
as a courtesy pointer for a human holding the printed book - they are NOT how you
retrieve text. Do not try to look anything up by page.

ANCHOR FORMAT
  <file>#<heading>/<subheading>/...     all lowercase, spaces -> hyphens
  e.g.  moves#basic-moves/hack-and-slash
        cleric#the-cleric/starting-moves
        equipment#equipment/weapons/weapon-tags
        appendices/npcs#...      monster_settings/undead#...
  A bare <file> (no '#') means the whole chapter.
  Anchors are matched case-insensitively, and a unique suffix works too:
  '--anchor hack-and-slash' resolves if only one heading ends that way.

USAGE
  rulebook.py --outline [--file F] [--depth N]
        Table of contents: anchor + heading + word count. START HERE if you
        don't already know the anchor. Default depth 2 (chapters + sections);
        depth 3-4 gets individual moves/monsters/spells. Narrow with --file
        before raising --depth, or the output is large.

  rulebook.py --anchor ANCHOR [--no-children] [--max-words N]
        Print that heading's text, rendered to plain text. This is the main
        call - the L3 read itself. Includes nested subheadings unless
        --no-children. Prints a word count to stderr.

  rulebook.py --search REGEX [--file F] [-C N] [--max-hits N]
        Case-insensitive regex over the rendered text. Reports the anchor each
        hit lives under, so you can follow up with --anchor. Use this when you
        know the wording but not where it lives.

  rulebook.py --xpath EXPR [--file F]
        Escape hatch: raw ElementTree XPath (a SUBSET of XPath 1.0 - no
        ancestor/following axes, no functions). 'aid:' prefix is bound. Only
        reach for this when --outline/--anchor/--search genuinely can't express
        the query.

  rulebook.py --check-anchors FILE...
        Verify every [xml:...] citation in FILE resolves. Used by CI; exits
        non-zero and lists the bad ones. Not a play-time command.

RETRIEVAL DISCIPLINE
  Follow SKILL.md's digest procedure: L0 -> L1 -> L2 -> and only then here, when
  exact wording matters rather than just the fact. Resolve one anchor, not a
  chapter, whenever you can. Never dump a whole file - --outline first.
"""


def strip_ns(tag):
    """'{http://...}h1' -> 'h1'."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def pstyle(elem):
    return elem.get("{%s}pstyle" % AID_NS, "")


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def inline_text(elem, skip=()):
    """Render mixed inline content, keeping bold/italic as markdown."""
    parts = [elem.text or ""]
    for child in elem:
        tag = strip_ns(child.tag)
        if tag not in skip:
            inner = inline_text(child, skip).strip()
            if inner:
                if tag in ("strong", "Strong"):
                    parts.append("**%s**" % inner)
                elif tag == "em":
                    parts.append("_%s_" % inner)
                else:
                    parts.append(inner)
        parts.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(parts))


class Block:
    """One rendered unit of the chapter: a heading, paragraph, or list item."""

    __slots__ = ("kind", "level", "text", "style")

    def __init__(self, kind, level, text, style=""):
        self.kind = kind
        self.level = level
        self.text = text
        self.style = style

    def render(self):
        if self.kind == "h":
            return "%s %s" % ("#" * self.level, self.text)
        if self.kind == "li":
            return "%s- %s" % ("  " * (self.level - 1), self.text)
        if self.style in MEANINGFUL_PSTYLES:
            return "[%s] %s" % (self.style, self.text)
        return self.text


def walk(elem, blocks, depth=0):
    """Flatten the tree to Blocks in document order."""
    for child in elem:
        tag = strip_ns(child.tag)
        if tag in HEADING_TAGS:
            text = inline_text(child).strip()
            if text:
                blocks.append(Block("h", HEADING_TAGS[tag], text, pstyle(child)))
        elif tag == "p":
            text = inline_text(child, skip=("ul", "ol")).strip()
            if text:
                blocks.append(Block("p", 0, text, pstyle(child)))
            for nested in child:
                if strip_ns(nested.tag) in ("ul", "ol"):
                    walk(nested, blocks, depth + 1)
        elif tag in ("ul", "ol"):
            walk(child, blocks, depth + 1)
        elif tag == "li":
            text = inline_text(child, skip=("ul", "ol")).strip()
            if text:
                blocks.append(Block("li", max(depth, 1), text, pstyle(child)))
            for nested in child:
                if strip_ns(nested.tag) in ("ul", "ol"):
                    walk(nested, blocks, depth + 1)
        elif tag == "Cell":
            text = inline_text(child).strip()
            if text:
                blocks.append(Block("p", 0, text, pstyle(child)))
        elif tag in CONTAINER_TAGS:
            walk(child, blocks, depth)
        else:
            # Unknown tag: descend rather than drop, so a future upstream
            # revision that adds an element doesn't silently lose text.
            if len(child) == 0:
                text = inline_text(child).strip()
                if text:
                    blocks.append(Block("p", 0, text, pstyle(child)))
            else:
                walk(child, blocks, depth)


class Section:
    __slots__ = ("anchor", "level", "title", "file", "start", "end")

    def __init__(self, anchor, level, title, file, start):
        self.anchor = anchor
        self.level = level
        self.title = title
        self.file = file
        self.start = start
        self.end = None


class Book:
    def __init__(self, root=XML_ROOT):
        self.root = root
        self.chapters = {}  # file slug -> [Block]
        self.chapter_sections = {}  # file slug -> whole-chapter Section
        self.sections = []  # heading sections, document order
        self.by_anchor = {}
        self._load()

    def _load(self):
        if not self.root.is_dir():
            sys.exit("error: rulebook XML not found at %s" % self.root)
        paths = sorted(self.root.rglob("*.xml"), key=lambda p: str(p).lower())
        if not paths:
            sys.exit("error: no .xml files under %s" % self.root)
        for path in paths:
            rel = path.relative_to(self.root)
            slug = "/".join(slugify(part) for part in rel.parts[:-1] + (rel.stem,))
            try:
                tree = ET.parse(path)
            except ET.ParseError as exc:
                sys.exit("error: %s is not well-formed XML: %s" % (rel, exc))
            blocks = []
            walk(tree.getroot(), blocks)
            self.chapters[slug] = blocks
            # A bare chapter slug is itself a valid anchor meaning "the whole
            # file". Several digest sections summarise an entire chapter, and
            # some chapters (Introduction, Moves, Equipment) hold more than one
            # h1, so citing the first heading would silently under-select.
            # Registered before the headings so an exact match always wins.
            whole = Section(slug, 0, slug, slug, 0)
            whole.end = len(blocks)
            self.by_anchor[slug] = whole
            self.chapter_sections[slug] = whole
            self._index(slug, blocks)

    def _index(self, slug, blocks):
        stack = []  # (level, slug-part)
        open_sections = []  # (level, Section)
        for i, block in enumerate(blocks):
            if block.kind != "h":
                continue
            while stack and stack[-1][0] >= block.level:
                stack.pop()
            while open_sections and open_sections[-1][0] >= block.level:
                open_sections.pop()[1].end = i
            stack.append((block.level, slugify(block.text)))
            anchor = self._unique("%s#%s" % (slug, "/".join(p for _, p in stack)))
            section = Section(anchor, block.level, block.text, slug, i)
            self.sections.append(section)
            self.by_anchor[anchor] = section
            open_sections.append((block.level, section))
        for _, section in open_sections:
            section.end = len(blocks)

    def _unique(self, anchor):
        if anchor not in self.by_anchor:
            return anchor
        n = 2
        while "%s-%d" % (anchor, n) in self.by_anchor:
            n += 1
        return "%s-%d" % (anchor, n)

    def resolve(self, query):
        """Anchor -> Section, or None if unknown. Accepts exact,
        case-insensitive, or unique-suffix matches; returns a list of
        candidates when a suffix is ambiguous."""
        if query in self.by_anchor:
            return self.by_anchor[query]
        lowered = query.lower().strip()
        exact = [a for a in self.by_anchor if a.lower() == lowered]
        if len(exact) == 1:
            return self.by_anchor[exact[0]]
        suffix = [
            a
            for a in self.by_anchor
            if a.lower().endswith("/" + lowered) or a.lower().endswith("#" + lowered)
        ]
        if len(suffix) == 1:
            return self.by_anchor[suffix[0]]
        if len(suffix) > 1:
            return suffix
        return None

    def blocks_for(self, section, include_children=True):
        blocks = self.chapters[section.file]
        if include_children:
            return blocks[section.start : section.end]
        out = [blocks[section.start]]
        for block in blocks[section.start + 1 : section.end]:
            if block.kind == "h":
                break
            out.append(block)
        return out

    def section_at(self, slug, index):
        """Deepest section containing block `index` of chapter `slug`."""
        best = None
        for section in self.sections:
            if section.file == slug and section.start <= index < section.end:
                if best is None or section.level > best.level:
                    best = section
        return best


def word_count(blocks):
    return sum(len(block.text.split()) for block in blocks)


def render(blocks):
    lines = []
    for block in blocks:
        if block.kind == "h" and lines:
            lines.append("")
        lines.append(block.render())
    return "\n".join(lines)


def match_file(book, needle):
    if not needle:
        return None
    lowered = needle.lower().removesuffix(".xml")
    if lowered in book.chapters:
        return lowered
    hits = [s for s in book.chapters if s.endswith(lowered) or lowered in s]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit("error: no chapter matching %r" % needle)
    sys.exit(
        "error: %r matches several chapters: %s" % (needle, ", ".join(sorted(hits)))
    )


def cmd_outline(book, args):
    only = match_file(book, args.file)
    current = None
    for section in book.sections:
        if only and section.file != only:
            continue
        if section.file != current:
            current = section.file
            whole = book.chapter_sections[current]
            print(
                "%-60s [whole chapter] (%d words)"
                % (whole.anchor, word_count(book.blocks_for(whole)))
            )
        if section.level > args.depth:
            continue
        words = word_count(book.blocks_for(section))
        print(
            "%s%-58s %s (%d words)"
            % ("  " * section.level, section.anchor, section.title, words)
        )


def cmd_anchor(book, args):
    found = book.resolve(args.anchor)
    if found is None:
        sys.exit(
            "error: no anchor %r. Run --outline (optionally --file X --depth 3) "
            "to find it." % args.anchor
        )
    if isinstance(found, list):
        sys.exit(
            "error: %r is ambiguous, matches:\n  %s"
            % (args.anchor, "\n  ".join(sorted(found)))
        )
    blocks = book.blocks_for(found, include_children=not args.no_children)
    words = word_count(blocks)
    if args.max_words and words > args.max_words:
        sys.exit(
            "error: %s is %d words (over --max-words %d). Use --no-children, or "
            "--outline --depth 4 to pick a narrower anchor."
            % (found.anchor, words, args.max_words)
        )
    print("<!-- %s -->" % found.anchor)
    print(render(blocks))
    print("(%d words)" % words, file=sys.stderr)


def cmd_search(book, args):
    try:
        pattern = re.compile(args.search, re.IGNORECASE)
    except re.error as exc:
        sys.exit("error: bad regex: %s" % exc)
    only = match_file(book, args.file)
    hits = 0
    for slug, blocks in sorted(book.chapters.items()):
        if only and slug != only:
            continue
        for i, block in enumerate(blocks):
            if not pattern.search(block.text):
                continue
            hits += 1
            if hits > args.max_hits:
                print(
                    "... more hits suppressed (--max-hits %d); narrow with --file "
                    "or a tighter regex." % args.max_hits
                )
                return
            section = book.section_at(slug, i)
            print("%s:" % (section.anchor if section else slug))
            lo = max(0, i - args.context)
            hi = min(len(blocks), i + args.context + 1)
            for j in range(lo, hi):
                print("  %s %s" % (">" if j == i else " ", blocks[j].render()))
            print()
    if not hits:
        print("no match for %r" % args.search)


def cmd_xpath(book, args):
    only = match_file(book, args.file)
    for path in sorted(XML_ROOT.rglob("*.xml"), key=lambda p: str(p).lower()):
        rel = path.relative_to(XML_ROOT)
        slug = "/".join(slugify(p) for p in rel.parts[:-1] + (rel.stem,))
        if only and slug != only:
            continue
        try:
            found = ET.parse(path).getroot().findall(args.xpath, NAMESPACES)
        except SyntaxError as exc:
            sys.exit(
                "error: ElementTree can't parse that XPath (%s). It supports only "
                "a subset of XPath 1.0 - no ancestor/following axes, no functions."
                % exc
            )
        for elem in found:
            text = inline_text(elem).strip()
            if text:
                print("%s: <%s> %s" % (slug, strip_ns(elem.tag), text))


def cmd_check_anchors(book, args):
    bad = []
    checked = 0
    for name in args.check_anchors:
        path = Path(name)
        if not path.is_file():
            sys.exit("error: no such file: %s" % path)
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, 1):
            for citation in CITATION_RE.findall(CODE_SPAN_RE.sub("", line)):
                for anchor in citation.split(","):
                    anchor = anchor.strip()
                    if not anchor:
                        continue
                    checked += 1
                    found = book.resolve(anchor)
                    if found is None:
                        bad.append((path, lineno, anchor, "does not resolve"))
                    elif isinstance(found, list):
                        bad.append((path, lineno, anchor, "is ambiguous"))
    for path, lineno, anchor, why in bad:
        print("%s:%d: [xml:%s] %s" % (path, lineno, anchor, why), file=sys.stderr)
    print("checked %d anchor citation(s), %d bad" % (checked, len(bad)))
    return 1 if bad else 0


def main():
    parser = argparse.ArgumentParser(
        description="Structured lookup into the Dungeon World rulebook XML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--help-llm", action="store_true", help="dense LLM-facing reference"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--outline", action="store_true", help="print the table of contents")
    mode.add_argument("--anchor", metavar="ANCHOR", help="print one section's text")
    mode.add_argument("--search", metavar="REGEX", help="regex over the rendered text")
    mode.add_argument("--xpath", metavar="EXPR", help="raw ElementTree XPath escape hatch")
    mode.add_argument(
        "--check-anchors",
        nargs="+",
        metavar="FILE",
        help="verify [xml:...] citations resolve (CI)",
    )
    parser.add_argument("--file", metavar="F", help="restrict to one chapter")
    parser.add_argument(
        "--depth", type=int, default=2, help="--outline heading depth (default 2)"
    )
    parser.add_argument(
        "--no-children", action="store_true", help="--anchor: exclude nested subheadings"
    )
    parser.add_argument(
        "--max-words", type=int, default=0, help="--anchor: refuse output longer than this"
    )
    parser.add_argument("-C", "--context", type=int, default=1, help="--search context blocks")
    parser.add_argument(
        "--max-hits", type=int, default=40, help="--search hit cap (default 40)"
    )
    args = parser.parse_args()

    if args.help_llm:
        print(HELP_LLM)
        return 0

    book = Book()
    if args.outline:
        cmd_outline(book, args)
    elif args.anchor:
        cmd_anchor(book, args)
    elif args.search:
        cmd_search(book, args)
    elif args.xpath:
        cmd_xpath(book, args)
    elif args.check_anchors:
        return cmd_check_anchors(book, args)
    else:
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
