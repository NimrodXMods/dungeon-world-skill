# Elicitation — how to ask the human for structured choices

Purpose: a **harness-agnostic** pattern for offering multi-choice and form-like
ELICITATION questions to the user. Inspired by MCP form-mode ELICITATION
(message + discrete fields + options + defaults) using clickable widgets
presented to users via tool calls. There is no shared cross-client tool for
this; do **not** invent or name harness-specific tooling.

Read this file **on demand** only as instructed to.

---

## When to use structured ELICITATION

**Use it** for out-of-fiction / meta decisions and explicit menus:

- Session start forks (new campaign vs resume vs GM Assistant vs rules-only)
- Campaign setup fields (players, tone, story log, slug, premise mode)
- Character creation steps with known option lists (class, race, alignment, gear)
- Explicit yes/no with a real default (e.g. maintain a story log)

**Do not use it** for ordinary in-fiction play:

- Do not use: soft GM moves, "what do you do?", fictional forks inside a scene
- Do not use: Open creative questions with no closed set ("name your deity",
  "describe the scar")

When in doubt: if the skill already knows a finite list, **list it** as a menu.
If the answer is free invention, ask open and optionally offer 2–3 examples
without forcing them.

---

## The pattern (shape, not wire format)

For each decision, hold this structure in mind:

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

### Presentation: clickable ELICITATION widget form presented by tool calls

If you have tool calls available for presenting the necessary clickable/tappable
ELICITATION widgets/forms to obtain structured data from the user then use
those when they fit. There are no standard tool calls for these so you are
not expected to have any particular tools for this but you should check anyway.
If you do not then use the instructions in **Presentation: plain chat** below.

If your runtime knows MCP form-mode
ELICITATION (`elicitation/create` + `requestedSchema`), treat the markdown below
as the same shape as that schema — map fields/options/defaults mentally, then
render with whatever structured-ask facility you have **or** as numbered questions
in chat with lettered options. Do **not** dump raw MCP JSON or protocol envelopes
at the user unless their client is an MCP form UI that expects that.

### Presentation: plain chat

**Number the questions**, **letter the options**. Keep labels short;
put detail in a half-line gloss. Always say how to reply
(letter, Y/N, or free text). **This chat formatting is the UI.**

```markdown
**Class** — pick one playbook (or name a homebrew and we'll improvise).
Default: none — this needs an explicit pick.

A. Fighter — frontline, Signature Weapon
B. Wizard — spellbook, fragile, versatile magic
C. Cleric — deity, healing and divine magic
… (list every option the skill actually supports)

Reply with a letter, a name, or your own idea.
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

```markdown
**Story log** — keep a running `story.md` narrative of the campaign?
Default: **yes**.

A. [Y]es — maintain the log (default)
B. [N]o — skip story.md

Reply A, B, Y, N, yes, or no.
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
   product's ask-user helper). If you can use clickable ELICITATION widget
   form mode or similar tool calls, that is fine — still present a clear
   multi-choice to the human.
3. **Defaults are first-class.** When the skill or template has a default, say
   it out loud before the user answers.
4. **Chat is the default UI.** The JSON examples above are a **mapping aid** for
   agents that understand clickable widget MCP form ELICITATION — not something
   to paste at the player mid-session unless their client is literally
   driving an MCP form.
5. **Multi-select:** say how many to pick ("choose two") and list the full set.
   Note that some tool call descriptions state false limits on their number of
   options and they can display more than their claimed limit.
6. **Locked choices** (e.g. Paladin is Human only): state the lock; do not fake
   a menu of one meaningful option unless clarifying.
7. **One PC at a time** for character creation (see Batching). No parallel
   multi-character questionnaires by default unless the user explicitly requests
   this.

---

## Worked example 1 — session start fork

```text
1. How do you want to proceed?
Default: none — needs a pick.

A. Start a **new campaign** (setup world + characters)
B. **Resume** from a campaign save zip
C. **GM Assistant** — you GM; the agent assists
D. Rules / reference only (not starting a session yet)

Reply with a letter or matching phrase.
```

---

## Worked example 2 — one chargen step after class is known

```text
2. **Race** (Fighter) — each race grants a different race move.
Default: none — needs a pick.

A. Dwarf
B. Elf
C. Halfling
D. Human

Or describe a custom ancestry and we'll fit a move. Reply with a letter or name.
```

---

## Reuse

The same shape works anywhere an agent must collect discrete user input without
a shared UI tool: **message · kind · options · default · escape · response
handling**. Keep option lists next to the procedure that owns them; this file
only defines *how* to present, not the domain lists themselves.

Domain option lists for this skill live in:

- [campaign-creation-checklist](references/campaign-creation-checklist.md) — setup fields and defaults
- [character-creation-checklist](references/character-creation-checklist.md) — playbook decisions
- [SKILL.md](SKILL.md) narration constitution — prose register / `style_voice` labels
- [gm-narration](references/gm-narration.md) — full narration essays (warm at create/loop)
