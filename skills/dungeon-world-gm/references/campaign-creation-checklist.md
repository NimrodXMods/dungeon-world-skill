# Campaign Creation Checklist

Purpose: ordered setup for a **new** campaign (or clarifying intent at session
start). Present each step using **[[elicitation]]** — enumerate options, state
defaults, allow custom answers where noted.

Store decisions in `<campaign_slug>_gmsecret.yaml` as they are made (template:
`assets/yaml_templates/gmsecret_template.yaml`). Never show the plain gmsecret
to the player.

For Fronts / dangers / "draw maps leave blanks" mechanics, also use
**[[fronts-and-worldbuilding]]** and generators (`idea_gen.py`, `region_gen.py`,
etc.) as needed. This checklist is the *procedure*; that reference is the
*craft*.

Read **on demand** at Session Start when starting new (or when intent is
unclear). Skip when resuming a loaded campaign zip unless re-confirming a field.

---

## How to run this checklist

1. Work steps **in order**. Do not skip a step silently.
2. For every step with a closed set, **list the options** before asking
   ([[elicitation]]).
3. Apply defaults only when the user skips and a default is stated — and **say**
   that you applied it.
4. Independent early fields (players + voice + story log) may batch into one
   multi-field message; branching steps stay one-at-a-time.
5. After setup, hand off to **[[character-creation-checklist]]** or sheet upload.

---

## Steps

### 1. [ ] Intent

What does the user want right now? (skip if already clearly answered)

| # | Option | Next |
| --- | --- | --- |
| 1 | **New campaign** | Continue this checklist |
| 2 | **Resume** from a campaign save zip | `session_load.py` path in SKILL.md — leave this checklist |
| 3 | **GM Assistant** | Start **GM Assistant Mode** |
| 4 | **Rules / reference only** | Answer questions; do not start session state |

Default: **none** — needs an explicit pick if unclear.

### 2. [ ] Players

- How many players (humans at the table / in the chat)?
- Solo with one PC, solo with multiple PCs, or multi-player?
- Names if known (else fill `players` later when sheets exist).

Kind: number + short free text. No forced menu beyond clarifying solo vs party.

### 3. [ ] Voice (`style_voice`)

Prose register for GM narration. **Option labels and full descriptions live in
[[llm-patches]]** ("How to Write the Game") — do not invent a fourth house style
without the user asking.

Describe each style in one sentence and ask the user which style is preferred when starting a new campaign.
Present using **[[elicitation]]** as single-select (summaries ok; point at llm-patches if they want detail):

1. **Dungeon World Pulpy** (default)
2. **Grim & Uncouth**
3. **Formal/Literary**
4. **Custom** — user describes tone; store that string in `style_voice`

Default: **Dungeon World Pulpy**. Write `style_voice` on the gmsecret once chosen.

### 4. [ ] Story log (`maintain_story`)

Keep a running `story.md` narrative?

1. **Yes** — maintain the log (default)
2. **No** — skip `story.md`

Default: **true** / yes. Mirror SKILL.md: assume yes unless they say otherwise.

### 5. [ ] Premise

What kind of world / campaign do they want?

| # | Option | Notes |
| --- | --- | --- |
| 1 | **I have a premise** | Free text; take notes; build fronts to match |
| 2 | **Surprise me** | Use `idea_gen.py` / `region_gen.py` / etc.; invent at least one front without spoiling GM-secret detail |
| 3 | **Open world, light preferences** | Still create ≥1 front (see [[llm-patches]] Fronts note); preferences optional |

Default: none required if they already stated a premise in chat — record it and
mark this done.

Open follow-ups (free text, not every one mandatory): tone of danger, tech/magic
level, regions they care about, banned content, one-shot vs long campaign.

### 6. [ ] Campaign slug

Propose a short `snake_case` slug (from premise or a neutral name). Confirm or
accept their alternative.

Default: your proposal if they say "fine" / "sure"; otherwise their string.
File: `<slug>_gmsecret.yaml`.

### 7. [ ] Characters

| # | Option |
| --- | --- |
| 1 | **Create new** via [[character-creation-checklist]] |
| 2 | **Upload** existing character sheet YAML(s) |
| 3 | **Mix** — some new, some upload |

Default: none — needs a pick. Run chargen (or load sheets) before calling the
session truly ready to play.

### 8. [ ] Front skeleton (GM-side)

Not a player menu. Before play:

- Ensure **at least one front** exists on the gmsecret ([[llm-patches]],
  [[fronts-and-worldbuilding]]).
- Use generators when inventing; keep spoilers out of player-facing text.
- Optional: lightly name the starting region/steading via `region_gen.py` /
  `steading_gen.py` if fiction needs a place to stand.

### 9. [ ] Ready to play

Only when:

- Intent was new campaign (or resume already loaded elsewhere)
- gmsecret exists with slug, `session_number` (1 for brand-new), `style_voice`,
  `maintain_story`, and ≥1 front
- At least one character sheet is in play (created or uploaded)
- Session-start always-read refs are loaded per SKILL.md

Then move to the main gameplay loop. Do not narrate "session begins" until
session-number rules in SKILL.md are satisfied.

---

## Notes for future maintenance

- Keep field names aligned with `gmsecret` template/schema.
- Add steps here when new campaign-level toggles appear; do not bury them only
  in SKILL.md prose.
- Presentation rules stay in [[elicitation]]; this file owns **which** questions
  and **what** options/defaults.
