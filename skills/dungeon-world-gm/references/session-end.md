# Session End

## Moves

The easiest place to end a session is during a "Make Camp" (move) but this isn't absolutely required. (It should be recommended if
the characters' situation allows for it easily.) If the characters are not in a safe resting place, moves like "Level Up" aren't available.

Characters gain XP at the end of a session. Gain 1 XP each for:

- did something to further their alignment
- learned something new & important about the world
- overcame a notable foe
- looted a memorable treasure
- Bonds, if used: XP for resolving bond.
- Flags variant, if being used: XP for hitting/being hit on a flag.
- check gmsecrets for any special goal resolutions earning XP. (The GM can designate some ahead of time and store in gmsecrets.)

Some typical session end moves that are recommended if conditions (safety, sufficient time) allow:

- "Make Camp" (resolve before end but make note to resolve "Take Watch" at the beginning of the next session if applicable.)
  - Class moves like "Prepare Spells" and "Commune" can be done if camped or loged for multiple hours.
  - "Level Up" can only be done if camped or loged for multiple hours, but can be done after rewarding end of session XP.
- "Supply" - Requires being in a stedding/settlement with NPCs to trade with, but can be done at session end.
- "Bolster" - Requires being in a permanent or long-term dwelling and takes at least one week.
- Not recommended: "Carouse", "Outstanding Warrants" - These require being in a stedding/settlement and if triggered should be deferred to start of next session. This is because they tend to trigger additional new time-consuming adventurous situations.

In summary, after awarding XP and possibly leveling up, only "maintenance" type moves should be allowed and only if required conditions are met. Offer to defer some moves to the beginning of next session if players' time is short and they need to end the session suddenly.

## Update `*_gmsecret.yaml` and All `*.yaml` Files

After this, make sure all `*.yaml` files are updated.

Update `pause_state` in the gmsecret file.

Before continuing, sweep `pause_state.open_threads` and `deeds`. Threads should already have
been pruned as they resolved during play; this is the backstop:

- Remove every thread that was answered, superseded by a larger thread (several clues
  collapsing into one replaces all of them), or dead-ended. A thread nobody has touched
  in two sessions is a dead end - cut it.
- For each thread that was _resolved_ rather than abandoned, append a `deeds` entry
  recording who did it - PCs and any NPCs who helped - and what resulted, e.g. "Fred and
  Joe solved the mystery of the disappearing cattle in Cowsburg with Old Marta's help,
  and gained the gratitude of the townsfolk". One deed may close several threads at once.
  `deeds` is append-only and sequential: never rewrite or reorder past entries. It is the
  campaign's memory, and the reason pruning threads loses nothing.

`open_threads` should end the session shorter than a plain accumulation would leave it. A
list that only grows stops being read.

Closing threads is one atomic call - the batch either all applies or nothing is written,
so the deed can never land without its threads being cleared. Put the deed prose in a file
and append it with `+@`, which avoids quoting problems with apostrophes and commas:

```
python3 scripts/yamledit.pyz campaign_gmsecret.yaml \
    deeds "+@deed.yaml" \
    pause_state.open_threads "-Cattle vanishing near Cowsburg" \
    pause_state.open_threads "-Strange tracks by the river" \
    --schema assets/yaml_schemas/gmsecret.schema.yaml
```

## Packaging Data

All of the data files below should be in the same directory to make this easy.

1. Ensure that the `*_gmsecret.yaml` is fully updated.
2. Ensure that the character sheet `*.yaml` files are fully updated.
3. Check previous turns for any missed yaml updates.
4. Write a `handoff.md` file alongside the yaml files with anything you need for the next session that isn't already in the other files. Err on the side of being redundant because this file is partly for error recovery if anything was left out of yaml and partly to allow for prose handoff without limitations of structured data.
5. Examine the help for the `session_save.py --help` script.
6. Run `python3 scripts/session_save.py campaign_gmsecret.yaml --kind session_end`

`session_number` is the session _currently being played_, and the first session is 1, never 0. Neither script writes it: `session_load.py` only reports it ("Loaded Session 3.") and `session_save.py` only reads it to name the zip, so `campaign_s3.zip` contains `session_number: 3` and re-running either script is harmless.

`session_save.py` also never re-serialises the gmsecret - it rot13s the raw file text, so
the explanatory comments in it survive a save/load round trip. A YAML round trip would
strip every one of them.

This rot13-encodes a copy of the gmsecret (rot13 leaves YAML's structural characters
readable but scrambles the words - a deliberate soft spoiler-guard, not real security),
and the handoff file, zips them with every character `*.yaml` in the same directory
as `<slug>_gmsecret.txt`, and names the zip `<slug>_checkpoint.zip` or `<slug>_s<N>.zip`.

Once the zip file is created, use `present_files` to actually hand the zip file to the person - the script only builds the zip, it doesn't deliver it.
