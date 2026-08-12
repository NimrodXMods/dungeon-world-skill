# Phase 1b: Resuming a Campaign

## Procedure

### Loading previous campaign state

The user uploads a campaign `.zip` or tells you where to find one. Use
`session_load.py` to extract it. Run `session_load.py --help` for usage.

- Example: `python3 scripts/session_load.py campaign_s3.zip --dir .`

This unzips everything, rot13-decodes the gmsecret to a plain working `.yaml`,
rot13-decodes `handoff.md`, and prints a summary (campaign, session number,
character files, full `pause_state`) so you have narrative context without
necessarily reading every file first.

Read all campaign files to determine game state; if anything seems missing, ask
the user. If you can search other conversations in the same project, use that
when the prior session may live elsewhere.

Yaml may fail validation after skill schema changes — migrate using any special
instructions, then current schemas, docs, and best-effort inference.

A campaign saved before the environment file existed will have no
`<slug>_environment.yaml`. Create one from
`assets/yaml_templates/environment_template.yaml` and fill it from
`pause_state` — but only with what the characters actually perceive. It is
player-visible; the gmsecret's `current_location` is ground truth and may use
names or details the party has not earned.

### Reconciling `pause_state` on load

`pause_state.situation` is authoritative; `open_threads` is a working list that
should match it. If they disagree, trust `situation` and prune/correct threads
**before** narrating to the player. Do not narrate off a stale first thread.

## `handoff.md`

Read `handoff.md` when the user is ready to **play** a session (not merely
inspect files). Delete it only after reading **and** after the session has
actually started per [SKILL-2-main-loop.md](SKILL-2-main-loop.md) session-number
rules — not before.

## Rules / checks

- Read yaml templates in `assets/yaml_templates` as documentation of yaml shape.
- Use `yamledit.pyz` exclusively for editing active yaml.
- Other references only as instructed or needed.

## Present the dashboard

Once the campaign files are restored and verified, show the player
`DW_Dashboard.html` **once**. Any `yamledit.pyz` write keeps it current from then on,
but on some clients it stays invisible until it has been presented once this session,
and re-opening it re-reads the file from disk.

If no dashboard exists yet, run `scripts/dashboard.py` once by hand to create it
(`--help-llm` for how). Use whatever this client offers for showing a file to the
user; if it offers nothing, say where the file is.

## Transition to main loop

Do **not** announce `Beginning session N` and do **not** increment
`session_number` here. Load finished and files verified is **not** yet a new
session start; users may only want to review data.

When the user is ready to play, enter
[SKILL-2-main-loop.md](SKILL-2-main-loop.md) and follow **Session Number** there
before any in-fiction narration of a new session.
