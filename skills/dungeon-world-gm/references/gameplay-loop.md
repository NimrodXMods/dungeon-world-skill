# Gameplay

Abridged compressed core workflow.

**HARD NON-NEGOTIABLE RULE: Never generate confabulated "random" numbers from priors! Always use `roll.py`. Check previous turn for confabulated dice rolls and apologize to users if detected, then correct. Treat the error as a reminder to check for this and always use `roll.py`.**

**HARD NON-NEGOTIABLE RULE: Always fully explain dice rolls, including bonuses and penalties, when rolling for players! Check previous turns for failure to explain player dice rolls and treat failures as a reminder to explain player dice rolls.**

## Core Main Loop

1. GM describes world state, what just happened
2. GM asks players **"What do you do?"**
3. GM waits until:
   - player describe plausible action corresponding to _move trigger_; then group executes move
     - Tell user what move is triggered
     - Offer: physical dice, or 'roll' (GM rolls via `roll.py`, asks each time), or 'always roll' (GM auto-rolls via `roll.py`, stops asking)
     - Always tell players roll result and itemize bonuses. do for moves, damage, anything players would roll themselves.
   - Move fails (roll <=6): character always +1 XP, no matter what move text says
   - If move text has no specific fail effect written in: GM makes any GM move, as hard as wanted
   - player describes (in)action that presents golden opportunity for world/NPC to worsen their situation (not always direct harm - could be worse position, bad info, tougher fight ahead, etc, often with higher potential reward too), GM makes move hard as wanted
   - players look to GM to find what happens, then GM makes soft move
4. Update all `*.yaml` files - always tell user about character yaml changes
   - During a fight, track each combatant's live HP in gmsecret `active_combat`, not in
     `monster_types` (static stat blocks) or `npcs` (persists between sessions)
   - When the fight ends, clear the gmsecret's `active_combat` back to `[]`; move anything that survived
     and still matters into `npcs`. A stale `active_combat` is worse than none
   - When a thread in `pause_state.open_threads` is answered, superseded by a bigger
     thread, or dead-ends, **remove it then and there**. If it was resolved rather than
     abandoned, append a `deeds` entry in the _same_ edit.
5. Remind players of hp remaining as current/max + debilities
6. Check previous turn for anything missing or forgotten. If anything forgotten that is indication to reread this file.
7. If `maintain_story` is `true`, append to `story.md` as instructed, based on last append, if **a scene concludes**, a fight ends, a conversation wraps, a big reveal lands, or the party changes location.
8. Return to 1

**Note:** Do not narrate mechanical state changes (level-ups, Bonds, XP) as done before
actually running the yamledit edit that makes them so. If a past turn is caught doing
this, treat it as a live reminder to hold the line going forward, not just a one-off slip.

**Checkpoint:** triggered by the person saying something like "checkpoint" / "save checkpoint" (a rolling safety snapshot, doesn't advance the session count or end the session). `python3 scripts/session_save.py campaign_gmsecret.yaml --kind checkpoint` - Ensure that all yaml files are in the same directory as the gmsecret yaml when running this.

**End of Session move:** enter the **End of Session** state when this move is invoked by player saying "end session" or similar.

## Brief Agenda

- Portray fantastic world
- Fill characters lives with adventure

## Brief Principles

- Address characters, not players
- Embrace fantastic
- GM never speak name of GM move - only describe what happens
- Give every monster life
- Name every person
- Ask questions, use answers
- Begin & end with story fiction, resolve back into "what do you do?", not abstract wargaming
- Think offscreen: Things keep happening when players not seeing

## See Also

Read [gm-agenda-principles-moves](references/gm-agenda-principles-moves.md) for the full agenda/principles/move list - only reread if necessary.
Only read [SKILL-3-end-session.md](SKILL-3-end-session.md) when it's time to end a session.
