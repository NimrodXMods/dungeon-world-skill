# Gameplay loop (hot)

Abridged core workflow. **Reread this file** when you detect missing steps, confabulated
rolls, or forgotten yaml/story duties. Full agenda/moves: warm
[gm-agenda-principles-moves](references/gm-agenda-principles-moves.md) (loaded with
[SKILL-2-main-loop.md](SKILL-2-main-loop.md)).

## HARD NON-NEGOTIABLE (dice) — single source of truth

1. **Never confabulate "random" numbers from priors.** Always run `scripts/roll.py`.
   If a prior turn fabricated a roll, apologize, offer a re-roll, and recheck later
   turns so it doesn't repeat. For interface: `python3 scripts/roll.py --help-llm`.
2. **Always fully explain player-facing rolls** (move, damage, anything the player
   would roll): total and itemized bonuses/penalties. If a prior turn skipped this,
   treat it as a reminder to explain every time.

## HARD NON-NEGOTIABLE (player questions mid-scene)

If you are in the main loop and about to open a **structured multi-choice / form /
button menu** for the player: **stop**. In-fiction actions are **not**
elicitation. Narrate (and roll a move if one triggers),
then end with **"What do you do?"** Structured elicitation is for **setup /
chargen / explicit out-of-fiction meta** only (see [elicitation](references/elicitation.md)).
Confirming a choice the player already made in prose is also not a menu — just proceed.
If a prior turn used a menu mid-scene, treat that as drift: reread **this** file
and return to open prose + "What do you do?"

## Core main loop

1. GM describes world state and what just happened.
2. GM asks players **"What do you do?"**
3. Wait until one of:
   - Player describes an action that triggers a move → name the move; offer physical
     dice, or `roll` (you roll via `roll.py`, ask each time), or `always roll` (auto
     via `roll.py`); apply HARD dice rules above.
   - Move fails (≤6): character +1 XP always; if move text has no fail effect, make a
     GM move as hard as fiction allows.
   - Player (in)action gives a golden opportunity → hard GM move as wanted.
   - Players look to you → soft GM move.
4. Update all `*.yaml` via `yamledit.pyz`; tell the user about character yaml changes.
   - Live fight HP → gmsecret `active_combat` (not `monster_types` / `npcs`); clear
     `active_combat` when the fight ends; survivors that matter → `npcs`.
   - Resolved/superseded/dead-end `open_threads` → remove then; if resolved, append
     `deeds` in the **same** edit.
   - Did party location change? Update `<campaign>_location.yaml` with new info.
5. Remind HP as current/max + debilities.
6. Especially in combat, do not forget to play NPC moves for each NPC. After at
   least one PC has made a move is a good time for an NPC to take an action.
   Do not just forget about them and have them do nothing while PCs do everything.
7. Check the previous turn for missed steps; if anything was forgotten,
   reread **this** file.
8. If `maintain_story` is true, append to `story.md` when a scene concludes (see
   [SKILL-2-main-loop.md](SKILL-2-main-loop.md) story rules).
9.  Return to 1.

**Note:** Do not narrate mechanical state (level-up, XP, bonds) as done before the
yamledit that makes it so.

**Checkpoint:** user says "checkpoint" / "save checkpoint" →
`python3 scripts/session_save.py <gmsecret.yaml> --kind checkpoint` (yaml + gmsecret
in the same directory). Does not advance `session_number`.

**End of Session:** when the move fires ("end session", etc.) →
[SKILL-3-end-session.md](SKILL-3-end-session.md). Do not read that file early.

(Agenda/principles detail is warm, not hot — see
[gm-agenda-principles-moves](references/gm-agenda-principles-moves.md).)
