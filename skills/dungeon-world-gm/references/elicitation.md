# Elicitation — how to ask the human for structured choices

Purpose: a **harness-agnostic** pattern for offering multi-choice and form-like
questions to the user. Inspired by MCP form-mode elicitation (message + discrete
fields + options + defaults), but rendered as ordinary chat. There is no shared
cross-client tool for this; do **not** invent or name harness-specific tooling.

Read this **on demand** — when running setup checklists, offering a closed menu,
or any time a finite option set exists and the user has not already answered.

---

## When to use structured elicitation

**Use it** for out-of-fiction / meta decisions and explicit menus:

- Session start forks (new campaign vs resume vs GM Assistant vs rules-only)
- Campaign setup fields (players, tone, story log, slug, premise mode)
- Character creation steps with known option lists (class, race, alignment, gear)
- Explicit yes/no with a real default (e.g. maintain a story log)

**Do not use it** for ordinary in-fiction play:

- Soft GM moves, "what do you do?", fictional forks inside a scene
- Open creative questions with no closed set ("name your deity", "describe the scar")

When in doubt: if the skill already knows a finite list, **list it**. If the
answer is free invention, ask open and optionally offer 2–3 examples without
forcing them.

---

## The pattern (shape, not wire format)

For each decision, hold this structure in mind — present it in plain prose, not
as JSON or a protocol method:

| Piece | Role |
| --- | --- |
| **message** | One sentence: what you need and why |
| **kind** | `single-select` · `multi-select` · `boolean` · `number` · `free-text` |
| **options** | Short labels (+ optional one-line gloss). **Required** for select kinds |
| **default** | State it when one exists; say "no default — needs a pick" when not |
| **escape** | For game preferences: always allow "something else / write your own" |
| **response** | Accept → use it. Skip with a known default → apply default (say so). Decline/cancel with no default → re-ask **once**, then do not invent a silent choice |

### Batching

- **One primary decision per turn** when the next options depend on the answer
  (class → race → look).
- **Independent setup fields** may share one message (player count + story log +
  voice) as a short multi-field form.
- Prefer fewer turns over dumping an entire chargen sheet as one wall of text
  unless the user asks to go fast.
- **Characters are never batched across PCs.** Create **one character at a time**,
  finish their sheet (or a clear handoff point), then start the next. Do **not**
  ask parallel multi-PC questions such as "what are all three classes?" or
  "give me all three names at once." Same for stats, gear, and bonds: one PC's
  decisions only, until that PC is done. Solo multi-PC games still go sequential
  (PC 1 fully, then PC 2, …).

### Presentation (plain chat)

Number or letter the options. Keep labels short; put detail in a half-line gloss.
Always say how to reply (number, name, or free text).

**This chat formatting is the UI.** If your runtime knows MCP form-mode
elicitation (`elicitation/create` + `requestedSchema`), treat the markdown below
as the same shape as that schema — map fields/options/defaults mentally, then
render with whatever structured-ask facility you have **or** as numbered chat.
Do **not** dump raw MCP JSON or protocol envelopes at the user unless their
client is an MCP form UI that expects that.

```text
**Class** — pick one playbook (or name a homebrew and we'll improvise).
Default: none — this needs an explicit pick.

1. Fighter — frontline, Signature Weapon
2. Wizard — spellbook, fragile, versatile magic
3. Cleric — deity, healing and divine magic
… (list every option the skill actually supports)

Reply with a number, a name, or your own idea.
```

Treat that block as equivalent to a single-field MCP-style form like:

```json
{
  "mode": "form",
  "message": "Pick one playbook (or name a homebrew and we'll improvise).",
  "requestedSchema": {
    "type": "object",
    "properties": {
      "class": {
        "type": "string",
        "title": "Class",
        "description": "Playbook; custom/homebrew names allowed",
        "enum": ["Fighter", "Wizard", "Cleric"]
      }
    },
    "required": ["class"]
  }
}
```

(Expand `enum` to every class the skill actually supports; omit `default` when
there is none — same as "Default: none" in the chat form.)

Boolean example with default:

```text
**Story log** — keep a running `story.md` narrative of the campaign?
Default: **yes**.

1. Yes — maintain the log (default)
2. No — skip story.md

Reply 1, 2, yes, or no.
```

Equivalent shape:

```json
{
  "mode": "form",
  "message": "Keep a running story.md narrative of the campaign?",
  "requestedSchema": {
    "type": "object",
    "properties": {
      "maintain_story": {
        "type": "boolean",
        "title": "Story log",
        "description": "Maintain story.md",
        "default": true
      }
    },
    "required": ["maintain_story"]
  }
}
```

### Hard rules

1. **If a finite option set is known, always enumerate it** when eliciting.
   Never ask "what class?" without listing the playbooks.
2. **Never name harness-specific tool APIs** as required (e.g. a particular
   product's ask-user helper). Prefer the chat form above; if you map it to MCP
   form mode or similar, that is fine — still present a clear multi-choice to
   the human.
3. **Defaults are first-class.** When the skill or template has a default, say
   it out loud before the user answers.
4. **Chat is the default UI.** The JSON examples above are a **mapping aid** for
   agents that understand MCP form elicitation — not something to paste at the
   player mid-session unless their client is literally driving an MCP form.
5. **Multi-select:** say how many to pick ("choose two") and list the full set.
6. **Locked choices** (e.g. Paladin is Human only): state the lock; do not fake
   a menu of one meaningful option unless clarifying.
7. **One PC at a time** for character creation (see Batching). No parallel
   multi-character questionnaires.

---

## Worked example A — session start fork

```text
How do you want to proceed?
Default: none — needs a pick.

1. Start a **new campaign** (setup world + characters)
2. **Resume** from a campaign save zip
3. **GM Assistant** — you GM; the agent assists
4. Rules / reference only (not starting a session yet)

Reply with a number or a short phrase.
```

---

## Worked example B — one chargen step after class is known

```text
**Race** (Fighter) — each race grants a different race move.
Default: none — needs a pick.

1. Dwarf
2. Elf
3. Halfling
4. Human

Or describe a custom ancestry and we'll fit a move. Reply with a number or name.
```

---

## Reuse outside this skill

The same shape works anywhere an agent must collect discrete user input without
a shared UI tool: **message · kind · options · default · escape · response
handling**. Keep option lists next to the procedure that owns them; this file
only defines *how* to present, not the domain lists themselves.

Domain option lists for this skill live in:

- [campaign-creation-checklist](references/campaign-creation-checklist.md) — setup fields and defaults
- [character-creation-checklist](references/character-creation-checklist.md) — playbook decisions
- [SKILL.md](SKILL.md) narration constitution — prose register / `style_voice` labels
- [gm-narration](references/gm-narration.md) — full narration essays (warm at create/loop)
