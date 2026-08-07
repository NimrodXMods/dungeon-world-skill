# Dungeon World Core Moves (Quick Reference)

## Terminology

Some Moves say:

- “deal damage.” - means roll the damage dice for character's class + any damage bonuses
- “take +1 forward.” - means to take +1 (or -1 or other specified) to next same or specified move(s) roll
- “take +1 ongoing.” = means to take +1 (or other +/- specified) to all or specified move rolls. Also says what causes it to end, like “until you dismiss the spell” or “until you atone to your deity.”
- Gives a player “hold.” Hold is currency that allows players to make some choices later on by spending the hold as the move describes.

**Track ongoing conditions and hold on the character yaml.**

Moves can also:

- Present a choice for the player.
- Give players a chance to say something about the character and their history.

Missed/failed moves:

- **Characters always gain +1 XP on all failed rolls <=6 for any basic, special, or other move roll!** They learn from failure.
- Usually moves specify no default consequence for 6-
- See [[gm-agenda-principles-moves]] for "hard GM move" ideas.

## Basic Moves (Immediate, Short Timescale Actions)

These are used for actions on a short timescale such as attacks in combat, death-defying stunts, searching for objects or information, or negotiating with NPCs.

**Hack & Slash** (+STR) - melee attack

- 10+: deal damage, avoid enemy's attack
- 7-9: deal damage, enemy deals damage back
- 6- : simple default: enemy deals damage, doesn't take any. (and/or custom GM hard move)

**Volley** (+DEX) - ranged attack

- 10+: deal damage, don't subtract an ammo
- 7-9: deal damage, choose one: enemy closes distance / you're exposed / you use up one ammo
- 6- : simple default: complete miss, lose one ammo. (and/or custom GM hard move, but always lose one ammo)

**Defend** (+CON) - protect a person/item/location under attack

- 10+: hold 3
- 7-9: hold 1
- Spend hold 1-for-1 on: redirect an attack to you, halve damage/effect, deal damage equal to your level to the attacker (when they miss)

**Defy Danger** - act despite/react to an imminent threat. Pick the stat that fits the fictional approach:

- STR: powering through
- DEX: getting out of the way, acting fast
- CON: enduring
- INT: quick thinking
- WIS: mental fortitude
- CHA: charm and social grace
- 10+: you do it
- 7-9: worse outcome, hard bargain, or ugly choice

**Discern Realities** (+WIS) - closely study a situation/person

- 10+: ask 3 from the list below
- 7-9: ask 1
- Questions: What happened here recently? / What is about to happen? / What should I be on the lookout for? / What here is useful or valuable to me? / Who's really in control here? / What here is not what it appears to be?
- Take +1 forward when acting on the answers. **NOTE:** Notify the player of +1 to next answer-related skill roll.

**Spout Lore** (+INT) - consult accumulated knowledge

- 10+: learn something interesting and useful
- 7-9: learn something interesting, GM decides if it's useful (may come with a cost/complication)
- GM always asks player: How do you know this?

*Neither Discern Realities nor Spout Lore lists a 6- outcome - that's true of every move (6- is GM territory, see the GM Move List in [[gm-agenda-principles-moves]]), but it's a bigger blank page for these two than most. That file also has a dedicated menu of tricks specifically for DR/Spout Lore misses, since "you don't know" is the weakest option and there's rarely a natural damage/cost to fall back on.*

**Parley** (+CHA) - when you have leverage on an NPC (something they need/want) and press them

- 10+: they do what you ask, or offer a solid promise
- 7-9: they'll do it, but need something concrete first (payment, proof, a promise from you)

**Aid or Interfere** (+Bond, or relevant stat if using Flags - see below)

- 10+: +1 or -2 to their roll (their choice which)
- 7-9: as above, but you expose yourself to danger/cost

## Long Timescale Moves

These moves are for actions that typically take half a day or more. Also included on the list is Last Breath where characters have a chance to escape death when their HP reaches 0.

**Undertake a Perilous Journey** (+WIS) - traveling hostile territory

- 10+ (choose a role - Quartermaster/Trailblazer/Scout): reduce rations needed / reduce travel time / get the drop on foes
- 7-9: things go about as well as can be expected

**Make Camp**: consume a ration; on waking after uninterrupted rest, heal half max HP.

**Take Watch** (+WIS)

- 10+: wake the camp, prep a response, camp takes +1 forward
- 7-9: react a moment too late - you have weapons/armor, little else
- 6-: whatever's out there gets the drop on you - GM hard move

**Outstanding Warrants** (+CHA) - returning somewhere you've caused trouble

- 10+: word has spread, everyone recognizes your deeds
- 7-9: as above + a complication (warrant, bounty, an ally in a bad spot)

**Carouse** - return triumphant, throw a party, spend 100+ coin, roll + (extra hundreds spent)

- 10+: choose 3
- 7-9: choose 1
- 6- : still choose 1 but things get out of hand - GM hard move
- Options: befriend a useful NPC / hear rumors of an opportunity / gain useful info / avoid being entangled, ensorcelled, or tricked

**Bolster** - spend time in study/meditation/practice to gain "preparation" (1 for a week+, 3 for a month+). Spend 1 preparation for +1 to a roll when it pays off (player chooses). No roll needed for this.

**Supply** (+CHA) - seeking something special/rare

- 10+: find it at a fair price
- 7-9: pay more, or settle for something similar

**Last Breath** (+nothing) - when HP hits 0

- 10+: alive, gain 1d4 HP, unstable
- 7-9: Death bargains with you - it won't be pretty
- 6-: Death takes you; make a new character

**Level Up**: subtract (current level + 7) from XP, +1 level, choose an advanced move, +1 to one stat (max 18). Wizards also gain a new spell.

**End of Session**: read **[[session-end]]** when this move is triggered. This is the move that says "we want to end the
session" and there's no need to read the file about it beforehand.

## Flags (alternative to Bonds - see [[fronts-and-worldbuilding]] source notes)

Flags are instructions to other players on how to treat your character (creates tension/tone rather than backstory). Mark XP if someone hits your flag this session, or if you hit someone else's. When Aiding/Interfering, roll the stat that fits how you're helping rather than a flat Bond bonus.

## Stat Modifier Table

| Score | Mod |
| ----- | --- |
| 1-3   | -3  |
| 4-5   | -2  |
| 6-8   | -1  |
| 9-12  | 0   |
| 13-15 | +1  |
| 16-17 | +2  |
| 18    | +3  |

## Debilities

- **Weak** (STR): can't exert much force
- **Shaky** (DEX): unsteady, shaking hands
- **Sick** (CON): something's wrong inside
- **Stunned** (INT): brain not work so good
- **Confused** (WIS): out of it, blurred/ringing
- **Scarred** (CHA): don't look so good

## Encumbrance

- At or under Load: fine
- Load+1 or Load+2: -1 on all rolls
- Greater than Load+2: automatic fail

## Damage by Severity (when improvising, no stat block handy)

- Bruises/scrapes at worst: d4
- Spills blood, nothing horrendous: d6
- Could break bones: d8
- Could kill a common person: d10

## Range Tags

Hand (within reach) < Close (reach + a foot or two) < Reach (several feet) < Near (whites of their eyes) < Far (shouting distance)
