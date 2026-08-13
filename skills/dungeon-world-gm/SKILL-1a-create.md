# Phase 1a: Create New Campaign

## Overview

Store decisions in `<campaign_slug>_gmsecret.yaml` as they are made (template:
`assets/yaml_templates/gmsecret_template.yaml`). Never show the plain gmsecret
to the player. The template is the canonical schema use documentation for itself.

For Fronts / dangers / "draw maps leave blanks" mechanics, use
[fronts-and-worldbuilding](references/fronts-and-worldbuilding.md) and generators
(`idea_gen.py`, `region_gen.py`, etc.) as needed. The checklist is the
*procedure*; that reference is the *craft*. Especially when in doubt or at a
loss, use `idea_gen.py` for an injection of enlightening material.

## Read needed references

- Always read now: [fronts-and-worldbuilding](references/fronts-and-worldbuilding.md)
- Always read now: [gm-narration](references/gm-narration.md) (if not already
  loaded this session) — theory-of-mind and description depth while inventing the world
- Only read [hacking-and-conversion](references/hacking-and-conversion.md) if the
  user wants conversions from other games (e.g. D&D character → DW). Otherwise skip.

Do **not** require [gm-agenda-principles-moves](references/gm-agenda-principles-moves.md)
here; that loads with the main loop.

## Procedural checklist

You are already on the **new campaign** path. Complete
[campaign-creation-checklist](references/campaign-creation-checklist.md) now
(skip any top-level intent fork that would leave create — stay on new campaign).

## Present the dashboard

Once the campaign files exist and `<slug>_environment.yaml` has a `where`, show the
player `DW_Dashboard.html` **once**. Any `yamledit.pyz` write keeps it current from
then on, but on some clients it stays invisible until it has been presented once this
session, and re-opening it re-reads the file from disk.

Use whatever this client offers for showing a file to the user. If it offers nothing,
say where the file is.

Only when the checklist **Ready to play** requirements are met, enter the main
loop via [SKILL-2-main-loop.md](SKILL-2-main-loop.md). Follow **Session Number**
there before announcing that play has begun (`session_number` is 1 for a brand-new
campaign — do not invent a start announcement here).
