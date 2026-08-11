# Phase 2: Main Gameplay Loop

## Before starting the loop

### Session Number

**`session_number`**: This should be set to 1 _at the start of the first session for a new campaign only_.

For resuming a previous campaign, advancing it is an explicit act at the **start** of a new session, once you've confirmed from what the person said - or by asking - that a new session is actually beginning. Simply loading a save is not by itself the start of a session; sometimes users may wish to review/verify the data or have other tasks before starting the game session.

To increment the session number, run `python3 scripts/yamledit.pyz --help-llm` to get the full documentation for `yamledit.pyz` and perform an edit of the gmsecret file incrementing `session_number` +1 , then announce `Beginning session <new number>...`.

## Read Documentation

These documents are needed for this state. Read them all now.

- [gameplay-loop](references/gameplay-loop.md) — brief core loop; reread on drift
- [core-moves](references/core-moves.md)
- [gm-agenda-principles-moves](references/gm-agenda-principles-moves.md)
- [llm-patches](references/llm-patches.md) — rule clarifications (not prose voice; that is in SKILL.md)

Other references should be read only as needed.

## Writing `story.md` - running narrative log

Only maintain `story.md` if `maintain_story` is `true` (true is default).

This is lightweight, prose-only story log that accumulates alongside the gmsecret
and character sheets, giving a readable "story so far" without anyone having
to re-read the structured YAML.

### Format

- Title (`# The Adventures of Blah`): propose a title to the user on
  starting a new campaign, ask them what they want to use, and use whatever they specify.
- Section headers per session (`## Chapter N` with N being the session number),
  plain prose paragraphs under each - no bullet points, no mechanical tags,
  no dice/HP/stat detail.
- It's fine for entries to read a little jumpy or unevenly paced - this is a
  running log built incrementally during live play, not a polished summary
  written after the fact.
- Skip mechanics entirely (rolls, HP, XP, move names) - narrative only, the
  same way you'd describe the scene and character actions in a novel.

### When to append

Append **after a scene concludes**, not on a fixed turn interval - a fight
ends, a conversation wraps, a big reveal lands, or the party changes location.
In practice this is roughly every 3-8 turns, but the trigger is narrative
closure, not a count. Hold the scene in mind and write one or two paragraphs
covering it in one append call, rather than editing the file after every
individual turn. Try to describe the environment, characters, foes, NPCs, and
all the action since the last update.

### How to append

Plain append, never `str_replace` - a growing log makes `str_replace`
increasingly fragile to match uniquely as the file gets longer. Since
`story.md` is plain prose (not YAML), no special escaping is needed; a normal
heredoc append is fine:

```bash
cat >> story.md << 'EOF'

New paragraph(s) here.
EOF
```

Don't reread the whole file before appending — the scene you're summarizing
is already in context. Only tail `story.md` if checking tone/continuity
against earlier entries, which should be rare.

### At session end

Do one final append covering anything since the last update, then include
`story.md` in the same directory as the character files and gmsecret file.
(`session_save.py` will look for it in the "character directory".)

### Retroactive backfill (one-time, not part of the ongoing workflow above)

This is _only_ needed if a user initially did not want a `story.md` maintained
but later changed their mind and wants to reconstruct one from past sessions.

If starting `story.md` partway through an existing campaign, earlier sessions
can be reconstructed from past conversation history (`conversation_search` /
`read_conversation` by session title) rather than from `session_log` recaps
alone — the recaps are usually too compressed to produce real prose, while
the actual transcripts have the scene-level detail needed for a readable
narrative. This only needs to happen once per campaign.

## Begin and Repeat the Main Loop

The loop repeats until the user (player or player(s)) decide to end the session with
the "End of Session" move. Once that happens, enter [SKILL-3-end-session.md](SKILL-3-end-session.md)
(triggered by "end session", "let's end the session", etc.).
