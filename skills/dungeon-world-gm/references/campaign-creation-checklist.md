# Campaign Creation Checklist

Purpose: ordered setup for a **new** campaign. Present each step using
[elicitation](references/elicitation.md) — enumerate options, state defaults,
allow custom answers where noted.

Read when following [SKILL-1a-create.md](SKILL-1a-create.md) (or when auditing
incomplete setup). Skip when resuming a loaded campaign.

You are already on the **new campaign** path if 1a sent you here. Do not offer
resume / GM Assistant / rules-only as checklist exits — send those to
[SKILL.md](SKILL.md) Session Start if the user changes intent.

---

## How to run this checklist

1. Work steps **in order**. Do not skip a step silently.
2. For every closed set, **list the options** before asking
   ([elicitation](references/elicitation.md)).
3. Apply defaults only when the user skips and a default is stated — and **say**
   that you applied it.
4. Independent early fields (players + voice) may batch; branching stays sequential.
5. After setup, hand off to
   [character-creation-checklist](references/character-creation-checklist.md)
   or sheet upload.

---

## Steps

### 1. [ ] Confirm new campaign

Proceed with create. If they wanted resume / assistant / rules-only instead, leave
this checklist and use [SKILL.md](SKILL.md) Session Start.

### 2. [ ] Players

- How many players (humans at the table / in the chat)?
- Solo one PC, solo multi-PC, or multi-player?
- Names if known (else fill `players` later when sheets exist).

Kind: number + short free text.

### 3. [ ] Voice (`style_voice`)

Prose register — labels and short definitions in [SKILL.md](SKILL.md) narration
constitution. Do not invent a fourth house style without the user asking.

Present with [elicitation](references/elicitation.md):

1. **Dungeon World Pulpy** (default)
2. **Grim & Uncouth**
3. **Formal/Literary**
4. **Custom** — store their description in `style_voice`

Default: **Dungeon World Pulpy**. Write `style_voice` on the gmsecret once chosen.

### 4. [ ] Premise

| # | Option | Notes |
| --- | --- | --- |
| 1 | **I have a premise** | Free text; build fronts to match |
| 2 | **Surprise me** | Generators; ≥1 front without spoiling GM-secret detail |
| 3 | **Open world, light preferences** | Still ≥1 front ([llm-patches](references/llm-patches.md) + [fronts-and-worldbuilding](references/fronts-and-worldbuilding.md)) |

If they already stated a premise, record it and mark done. Optional follow-ups:
tone, tech/magic level, regions, banned content, one-shot vs long campaign.

### 5. [ ] Campaign slug

Propose short `snake_case` slug; confirm or take their alternative.
File: `<slug>_gmsecret.yaml`.

### 6. [ ] Characters

| # | Option |
| --- | --- |
| 1 | **Create new** via [character-creation-checklist](references/character-creation-checklist.md) |
| 2 | **Upload** existing character sheet YAML(s) |
| 3 | **Mix** |

Default: none — needs a pick before ready to play. If creating multiple PCs,
run the checklist **once per character, fully, in sequence** — never
"class/name/stats for everyone at once" (see [elicitation](references/elicitation.md)).

### 7. [ ] Front skeleton (GM-side)

Not a player menu. Before play:

- ≥1 front on gmsecret ([llm-patches](references/llm-patches.md),
  [fronts-and-worldbuilding](references/fronts-and-worldbuilding.md)).
- Generators OK; keep spoilers out of player-facing text.
- Optional: starting region/steading via `region_gen.py` / `steading_gen.py`.

### 8. [ ] Story log (`maintain_story`)

Keep a running `story.md`?

1. **Yes** — maintain the log (default)
2. **No** — skip `story.md`

Default: **yes**. If yes: set `maintain_story` true; **propose and confirm the
story title once here** (`# The Adventures of …`). Main loop does not re-ask
title unless missing. If no: set `maintain_story` false.

### 9. [ ] Ready to play

Only when:

- Still on new campaign
- gmsecret has slug, `session_number` **1**, `style_voice`, `maintain_story`, ≥1 front
- ≥1 character sheet in play
- 1a required refs loaded (fronts + gm-narration)

Then enter [SKILL-2-main-loop.md](SKILL-2-main-loop.md) and follow **Session
Number** there before announcing play has begun.

---

## Notes for future maintenance

- Keep fields aligned with gmsecret template/schema.
- Presentation rules: [elicitation](references/elicitation.md); this file owns
  which questions and defaults.
