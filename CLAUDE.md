# CLAUDE.md

The project guide for this repo lives in **[AGENTS.md](AGENTS.md)** — repo layout, commit
policy (including: never commit, push, or tag on your own initiative), the runtime
context-budget rules, script conventions, campaign state format, CI and the pre-flight
checks, and the skill-frontmatter policy. Read it before making changes.

@AGENTS.md

## What belongs in this file

`AGENTS.md` is canonical and every agent reads it. This file is **only** for things that are
true *because the reader is Claude Code specifically* — its tool names, harness behavior,
`@`-imports, skills/hooks/settings wiring.

Anything that would still be true for a different agent belongs in `AGENTS.md`, even if it
feels important enough to repeat here. Repeating it does not make it more available: the
`@AGENTS.md` import above already pulls the whole guide into context, so a second copy buys
only emphasis — and costs context every session, then drifts the moment the original changes.
These two files used to restate each other and disagreed as a result; keep it to one copy.

If a rule is general but its *application to Claude Code* is what needs saying, state the
Claude-Code-specific part and let `AGENTS.md` carry the rule.

## Claude Code specifics

- Use the **Bash** tool for commands in this repo, even though a **PowerShell** tool is also
  available on Windows. CI runs on Linux, so one dialect keeps AGENTS.md's documented commands
  true in both places. Never mix the two dialects within a single call — see AGENTS.md,
  "Working commands", for the silent-corruption failure mode this prevents.
