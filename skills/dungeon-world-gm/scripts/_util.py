#!/usr/bin/env python3
"""Shared helpers for skill scripts.

Not a CLI. Sibling-module pattern, same as _treasure.py: running
`python3 scripts/<name>.py` puts scripts/ on sys.path[0], so callers use a bare
`import _util` (or `from _util import ...`). The leading underscore is deliberate
- sys.path[0] being the scripts directory means an unprefixed name here could
shadow a stdlib module for every script in the skill.

Nothing here runs at import time. Call force_utf8_stdio() explicitly near the
top of each script, before any print that might emit non-ASCII.
"""

import os
import random
import sys

SEED_WARNING = (
    "Warning: Do not use --seed in a real game! If you did then re-read "
    "gameplay-loop.md now!"
)

# Campaign zip text is always UTF-8 with Unix (LF) newlines. Working copies on
# disk use the host's preferred line endings (CRLF on Windows, LF elsewhere).
# session_save / session_load convert at the boundary so save→load→save is
# stable and diffs are not pure line-ending noise.


def normalize_newlines_to_lf(text):
    """Canonical form for text stored in session zips (and rot13 payloads)."""
    if not isinstance(text, str):
        text = text.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def newlines_for_local(text):
    """Expand LF-only text to the host line ending for on-disk working files."""
    text = normalize_newlines_to_lf(text)
    if os.linesep == "\n":
        return text
    return text.replace("\n", os.linesep)


def read_text_utf8(path):
    """Read a text file as UTF-8 without locale encoding surprises.

    newline='' keeps CR/LF bytes as written so we can normalize explicitly;
    a UTF-8 BOM is stripped if present (common from some Windows editors).
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return f.read()


def write_text_utf8_local(path, text):
    """Write working-copy text as UTF-8 with host-native newlines (no BOM)."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(newlines_for_local(text))


def force_utf8_stdio():
    """Windows defaults sys.stdout to the ANSI code page (cp1252) whenever
    stdout is not a real console - a redirect or a pipe is enough. cp1252 has
    no mapping for characters skill scripts print (e.g. U+2192 "->"), so the
    write raises UnicodeEncodeError instead of degrading. Force UTF-8; a no-op
    where the stream does not support reconfiguring."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass


def apply_seed(seed):
    """If seed is not None, warn on stderr and seed the stdlib RNG.

    The warning goes to stderr so it never pollutes machine-readable stdout
    (monster_gen.py JSON) or gets mixed into table output. None is a no-op.
    """
    if seed is None:
        return
    print(SEED_WARNING, file=sys.stderr)
    random.seed(seed)


def d(sides):
    """Roll 1dN."""
    return random.randint(1, sides)


def nd(n, sides):
    """Roll NdM and sum the dice."""
    return sum(d(sides) for _ in range(n))
