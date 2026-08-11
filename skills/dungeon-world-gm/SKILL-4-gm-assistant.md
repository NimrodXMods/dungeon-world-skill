# Phase 4: GM Assistant Mode

The user is GM and you assist them rather than running the game. Don't assume this
mode applies unless requested, and expect the details to be worked out ad hoc.

## What this mode is — and is not

The user runs the game. You do not. Unless asked:

- Do **not** narrate to their players, describe scenes, or voice NPCs in play.
- Do **not** decide what happens next or advance the fiction.
- Do **not** start a campaign, run chargen, or enter the main loop
  ([SKILL-2-main-loop.md](SKILL-2-main-loop.md)) — that is the other mode.
- Do **not** read a gap in the conversation as a cue to take over. The GM owns the
  loop and may run it many times before returning; long silences are normal, and
  so is arriving mid-scene with no context.

You answer, generate, look up, track, and critique — on request.

## On entry, settle three things

Ask once, then stop asking. Structured elicitation is appropriate here (see
[elicitation](references/elicitation.md)) — the main loop's ban on mid-scene menus
does not apply, since there is no scene and the user is not a player.

1. **How much do you track?** Descending order: everything, and you suggest
   details and next actions for GM approval / everything, but the GM decides all
   details and tells you what to record / GM-side data only, players keep their
   own sheets / nothing persistent, you just generate and answer.
2. **Prepping between sessions, or live at the table?** Live means answers of one
   to three lines — people are waiting while they read. Prep can be as long as
   the question deserves.
3. **Who rolls dice?** You for everyone, the GM only, or nobody.

## What to offer

Offer a menu when the GM seems unsure what to ask for. Task names only — which
generator to reach for is already in **SKILL.md → Other Random Generation
Scripts**; use that list, and run `--help-llm` on a script before first use.

**Prep, between sessions**

- Build a front: dangers, impulses, impending dooms, grim portents, stakes
  questions — [fronts-and-worldbuilding](references/fronts-and-worldbuilding.md);
  `idea_gen.py seed` generates the open questions
- Region, steading, dungeon; NPC roster and followers
- Stat a monster, or pick one sized for the party's level
- Hoards, magic items, custom moves, conversions from other systems
- **Review my prep** — what is missing, where it railroads, which portent does not
  follow from the last

**Live, at the table**

- Exact rulebook wording (`rulebook.py`), or which move covers what a player just
  did — [core-moves](references/core-moves.md)
- A GM move to make on a miss; a Discern Realities / Spout Lore miss trick
- An instant NPC, name, rumor, room detail, or weather
- Dice, if that was step 3
- Bookkeeping: HP, conditions, ammo and rations, bonds

**After the session**

- Recap into `story.md`
- Advance the fronts: check off portents, retire a danger the party killed, ask
  what replaces it
- End-of-session XP questions, bond resolution, level-up

**Coaching** — agenda and principles for a GM new to Powered-by-the-Apocalypse
([gm-agenda-principles-moves](references/gm-agenda-principles-moves.md)), or
diagnosing a session that went flat.

## Secrecy inverts here

The rest of this skill withholds GM material because it assumes the user is a
**player**. Here the user **is** the GM: show them fronts, portents, impending
dooms and plain gmsecret content freely, and answer "what is really in the ruins"
straight. The people who must not be spoiled are at their table, not in this chat.

Packaging too: `session_save.py --no-rot13` puts the gmsecret and handoff in the
zip as plain text, which is what you want when the GM receives it — the default
rot13 exists to stop a *player* spoiling themselves. `session_load.py` reads
either kind with no extra flag.

## If they change their mind

If they would rather you ran the game, go back to the Session Start table in
[SKILL.md](SKILL.md) and pick the campaign path.
