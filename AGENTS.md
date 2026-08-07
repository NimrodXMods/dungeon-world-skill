# AGENTS.md

Guidance for coding agents working in this repository.

## Committing

**Never commit automatically.** Do not run `git commit`, `git push`, or `git tag` on your own
initiative — not after finishing a change, not at the end of a task, not "to be safe." When work
reaches a point where a commit makes sense, stop and tell the user, then wait for them to ask.

This includes tags: pushing a `v*` tag triggers a public GitHub Release, so it is a
commit-class action and needs the user's say-so.

## Before you push

Run `python tools/validate_skill.py` — it is the pre-flight check CI runs, and it catches
the repo's unenforceable conventions (broken wikilinks, orphaned reference files, scripts
that lost `--help-llm`, templates that drifted from their schemas).

## Everything else

The full project guide — repo layout, the runtime context-budget rules, script conventions,
campaign state format, and the manual verification commands — lives in [CLAUDE.md](CLAUDE.md).
Read it before making changes. Keep the two files in sync when project-wide rules change.
