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

import random
import sys

SEED_WARNING = (
    "Warning: Do not use --seed in a real game! If you did then re-read "
    "gameplay-loop.md now!"
)


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
