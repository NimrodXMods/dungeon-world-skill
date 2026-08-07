#!/usr/bin/env python3
"""
Dice roller for Dungeon World (and general NdM+K use).

Usage:
    python3 roll.py 2d6
    python3 roll.py 2d6+3
    python3 roll.py 1d8 -n 3            # roll 1d8 three times (separate rolls)
    python3 roll.py 3d8 --highest        # roll 3d8, report the single highest die
                                          # (DW rule: multiple attackers -> roll
                                          # one die per attacker at the largest
                                          # damage die among them, take the highest)
    python3 roll.py 2d6+1 --moves        # 2d6+mod, annotated with DW move result
                                          # (10+ / 7-9 / 6-)

Notation supported: NdM, NdM+K, NdM-K (N and K optional, default N=1, K=0)
"""
import argparse
import random
import re
import sys


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

DICE_RE = re.compile(r"^(\d*)d(\d+)([+-]\d+)?$", re.IGNORECASE)

HELP_LLM = """\
roll.py - dice roller for Dungeon World (2d6 moves, damage, NdM+K generally).
Always use this for any in-game roll; never fabricate a "random" result.

USAGE
  roll.py EXPR [-n N] [--highest] [--moves]

EXPR
  NdM, NdM+K, NdM-K (N optional, default 1; K optional, default 0)
  e.g. 2d6, 2d6+1, 1d8, 3d10-2

FLAGS
  -n, --times N   roll EXPR this many times, independently (default 1)
  --highest       with --times > 1, also report the single highest total -
                   use for DW's official multi-attacker damage rule: roll one
                   die per attacker at the largest attacker's damage die, take
                   the highest, and add +1 flat per additional attacker
                   yourself via EXPR's K (e.g. 1d8+2 for 3 attackers)
  --moves         annotate each roll with the 2d6 move result tier: 10+ full
                   success / 7-9 partial success or cost / 6- miss (GM makes
                   a move, character +1 XP)

No --seed option exists on this script, and none should be added - rolls
must always be as close to true-random as possible to simulate real dice.

OUTPUT
  One line per roll: "Roll N: EXPR = [dice] +/-K = total", with the move-tier
  annotation appended if --moves was given. With --times > 1: a trailing
  "Totals: [...]" line, plus "Highest: N" if --highest was also given.
  Always ends with two reminder lines: tell the player the roll verbatim
  (everything after "Roll N:"), and a prompt to re-check for/correct any
  fabricated rolls and update yaml if this roll changes game state.

EXAMPLES
  roll.py 2d6+1 --moves           a move roll, annotated 10+/7-9/6-
  roll.py 1d8                     a damage roll
  roll.py 1d6+2                   e.g. 2-attacker damage: highest die +1 flat
  roll.py 1d8 -n 2 --highest      "best of" / Aid-Interfere-style advantage
"""


def parse_and_roll(expr):
    m = DICE_RE.match(expr.strip())
    if not m:
        raise ValueError(f"Can't parse dice expression: {expr!r} (expected form like 2d6+1)")
    n = int(m.group(1)) if m.group(1) else 1
    sides = int(m.group(2))
    mod = int(m.group(3)) if m.group(3) else 0
    if n < 1 or sides < 1:
        raise ValueError("Number of dice and sides must be positive")
    rolls = [random.randint(1, sides) for _ in range(n)]
    total = sum(rolls) + mod
    return rolls, mod, total


def move_result(total):
    if total >= 10:
        return "10+ -> full success"
    elif total >= 7:
        return "7-9 -> partial success / cost"
    else:
        return "6-  -> miss, GM makes a move, character +1 XP"


def main():
    if "--help-llm" in sys.argv[1:]:
        sys.stdout.write(HELP_LLM)
        return

    ap = argparse.ArgumentParser(description="Roll dice for Dungeon World.")
    ap.add_argument("expr", help="Dice expression, e.g. 2d6+1, 1d8, 3d10-2")
    ap.add_argument("-n", "--times", type=int, default=1,
                     help="Roll this expression this many times (separate independent rolls)")
    ap.add_argument("--highest", action="store_true",
                     help="Across the --times rolls, also report just the single highest total "
                          "(e.g. DW's multi-attacker damage: roll one die per attacker, take highest)")
    ap.add_argument("--moves", action="store_true",
                     help="Annotate each roll with the DW 2d6 move result tier (10+/7-9/6-)")
    ap.add_argument("--help-llm", action="store_true", dest="help_llm",
                     help="print the dense full reference written for LLM callers, then exit")
    args = ap.parse_args()

    totals = []
    for i in range(args.times):
        rolls, mod, total = parse_and_roll(args.expr)
        totals.append(total)
        line = f"Roll {i+1}: {args.expr} = {rolls}"
        if mod:
            line += f" {'+' if mod > 0 else ''}{mod}"
        line += f" = {total}"
        if args.moves:
            line += f"  ->  [ {move_result(total)} ]"
        print(line)

    if args.times > 1:
        print(f"Totals: {totals}")
        if args.highest:
            print(f"Highest: {max(totals)}")

    print("When rolling for player, inform player of used roll using verbatim text but omitting 'Roll N:'")
    print("Reminder: if needed: yamledit files, always: mistake check, if mistake found: reread references/gameplay-loop.md")

if __name__ == "__main__":
    main()
