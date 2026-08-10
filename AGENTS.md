# AGENTS.md

Guidance for coding agents working in this repository.

## Committing

**Never commit automatically.** Do not run `git commit`, `git push`, or `git tag` on your own
initiative — not after finishing a change, not at the end of a task, not "to be safe." When work
reaches a point where a commit makes sense, stop and tell the user, then wait for them to ask.

This includes tags: pushing a `v*` tag triggers a public GitHub Release, so it is a
commit-class action and needs the user's say-so.

### After a PR merges

This GitHub repo is configured to **delete the head branch automatically on merge**.
That is intentional and safe here: GitHub keeps a restore/undelete path for the branch
for some time afterward if something went wrong.

When the user asks to clean up after a merge:

1. `git checkout main` (or the default branch), then `git pull`.
2. Delete the **local** feature branch (`git branch -d <branch>`).
3. **Do not** try to delete the remote branch (`git push origin --delete …`), and do
   **not** treat a missing `origin/<branch>` as an error — the remote is already gone.
4. `git fetch --prune` is fine if stale remote-tracking refs linger.

## Editing a skill

Any edit under `skills/` must also update that skill's `SKILL.md` frontmatter in the same
change: `metadata.version` (major = major change, minor = added functionality, patch = fix
or trivial addition), `metadata.updated` (today's date in **UTC**, `YYYY-MM-DD` — CI is
usually UTC), and `metadata.last-assisting-model` (your model id when a model assisted).
Do it automatically — it is part of the edit, not a separate step to ask about. CI fails
the build if you skip version/`updated` policy. See [CLAUDE.md](CLAUDE.md) for the full
frontmatter policy, including what `last-assisting-model` does **not** mean.

## Before you push

Run both pre-flight checks CI runs:

```bash
python tools/validate_skill.py
python tools/check_version_bump.py --base origin/main
```

The first catches the repo's unenforceable conventions (broken wikilinks, orphaned
reference files, scripts that lost `--help-llm`, templates that drifted from their
schemas, third-party imports that won't exist in the sandbox). The second catches a skill
edit that forgot its frontmatter bump.

## Everything else

The full project guide — repo layout, the runtime context-budget rules, script conventions,
campaign state format, and the manual verification commands — lives in [CLAUDE.md](CLAUDE.md).
Read it before making changes. Keep the two files in sync when project-wide rules change.
