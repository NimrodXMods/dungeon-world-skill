# Phase 1b: Resuming a Campaign

## Procedure

### Loading Previous Campaign State

The User uploads a .zip file of an existing campaign or tells you where to find one. Use `session_load.py` to extract the zip file. Run `session_load.py --help` for usage.

- Example: `python3 scripts/session_load.py campaign_s3.zip --dir .`

This unzips everything, rot13-decodes the gmsecret back to a plain working `.yaml`, rot13 decodes the handoff.md and prints a summary (campaign, session number, character files found, and the full `pause_state` - location/situation/open threads) so you have immediate narrative context without necessarily needing a separate read of the whole file. There should also be a `handoff.md` for as a prose non-structured general handoff and safety net for missing information.

Read all files to determine all of the game state, and if anything seems missing ask the user if they can remember it. If you have tools for searching other conversaions you can try using those if needed as the previous game session may be in another conversation context in your environment.

Also be warned that yaml files could fail validation because of new additions to or changes to the skill. If this happens it usually means the yaml files need migration to a new schema. Migrate the files according to special instructions if any, followed by: current schemas, docs, and best effort inference.

###  Reconciling `pause_state` on load

`pause_state.situation` and `pause_state.open_threads`
are not independent - `situation` is the authoritative snapshot of where things stand right
now, while `open_threads` is a working list that should already reflect it. If they disagree
(e.g. a thread's text implies something hasn't happened yet, but `situation` or the prior
session's narrative shows it already did), trust `situation` and correct or prune the stale
thread immediately as part of session load - before narrating anything to the player. Don't
narrate off the first `open_threads` entry you read without checking it against `situation`.

## `handoff.md`

When you have verified that the session has started, ensure you have read `handoff.md` and delete it. Only delete `handoff.md` after reading and after the session actually starts, not before.

## Rules/Checks

- Never narrate the new session as begun before that edit has actually run.
- If two sessions end up sharing a number, the increment was skipped - fix it forward, don't rewrite history.
- Read yaml templates in `assets/yaml_templates` as documentation of yaml use.
- Use `yamledit.pyz` exclusively for editing the active yaml files.
- Additional references should be read only as instructed and/or needed.

## Transition Game State to Main Loop

Once all the session start details are resolved, the game state moves to the
main gameplay loop. Enter via [SKILL-2-main-loop.md](SKILL-2-main-loop.md).