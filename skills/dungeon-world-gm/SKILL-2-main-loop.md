# Phase 2: Main Gameplay Loop

## Before starting the loop

### Session Number

Order:

1. Confirm the user wants to **begin play** for a session (not only review files).
2. **Brand-new campaign:** `session_number` should already be `1` from create — do
   not increment again; announce `Beginning session 1...` only after warm docs
   below are loaded (or load then announce).
3. **Resume:** advancing is explicit at the start of a **new** play session.
   Loading a save is not enough. If this entry has not already advanced the
   number, yamledit the gmsecret: `session_number` +1, then announce
   `Beginning session <new number>...`. Never announce before the edit succeeds.
4. If two sessions share a number, the increment was skipped — fix forward, do
   not rewrite history.

Use `python3 scripts/yamledit.pyz --help-llm` for the editor interface.

## Read documentation (warm — once when entering this state)

If not already loaded this session, read all of:

- [gameplay-loop](references/gameplay-loop.md) — **hot**; also reread on drift
- [core-moves](references/core-moves.md)
- [gm-agenda-principles-moves](references/gm-agenda-principles-moves.md)
- [llm-patches](references/llm-patches.md) — rule clarifications
- [gm-narration](references/gm-narration.md) — narration essays (skip if loaded in 1a)

Other references only as needed (cold).

## Writing `story.md` — running narrative log

Only if `maintain_story` is `true` (default true).

### Format

- Title (`# The Adventures of …`): **already set at campaign create** when the
  user chose a story log. Only propose/confirm a title here if the file is
  missing a title or `maintain_story` was turned on later.
- Section headers per session (`## Chapter N` with N = `session_number`), plain
  prose under each — no bullets, no dice/HP/stat/move names.
- Uneven pacing is fine; this is a live log, not a polished recap.

### When / how to append

After a **scene concludes** (fight ends, conversation wraps, reveal, location
change) — not every turn. Roughly every 3–8 turns. One or two paragraphs per
append covering since last update.

Plain append only (not fragile search-replace), e.g.:

```bash
cat >> story.md << 'EOF'

New paragraph(s) here.
EOF
```

Don't reread the whole file before appending; tail only if checking continuity.

### At session end

Final append for anything since last update; keep `story.md` next to character
yaml and gmsecret (`session_save.py` looks in that directory).

### Retroactive backfill

Only if the user later wants a log after playing without one: reconstruct from
conversation history when possible; once per campaign.

## Begin and repeat the main loop

Follow [gameplay-loop](references/gameplay-loop.md). Loop until End of Session
("end session", etc.) → [SKILL-3-end-session.md](SKILL-3-end-session.md).
