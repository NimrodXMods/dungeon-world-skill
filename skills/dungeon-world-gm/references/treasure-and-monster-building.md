# Treasure Table & Quick Monster Builder

Use `monster_gen.py`. Its default is the **official rulebook bestiary** - a real monster with a
description, instinct and moves already written - and that is almost always what you want. The
builder described on this page is the `--custom` path, for an enemy the bestiary doesn't cover;
it produces stats only, leaving the flavour for you to invent. Reference for the categories and
their effects is below.

Most monsters are disposable "ammunition" for whatever Danger you're running - no name needed until play puts a spotlight on one (a Spout Lore roll, a nasty retreat, the players' own questions), at which point naming it and maybe promoting it to a Danger is fair game. Dungeon World explicitly isn't about a "fair fight" or encounter balancing - aim for a real threat and a fantastic world instead.

**Monsters without stats**: for something on a scale where HP/damage/armor don't make sense (untouchable, cosmic, or just not built to fight), skip numeric stats entirely - give it tags, an instinct, and moves, and run it purely off those.

## Treasure Roll

One "treasure pile" per monster. If you only use 2 monsters, only use 2 treasure piles.

For each monster's treasure stash, roll the monster's damage die (+ any bonus dice below), read the result:
1: a few coins (2d8-ish) | 2: an item useful right now | 3: several coins (~4d10) | 4: small valuable item, 2d10x10c, 0wt | 5: minor magical trinket | 6: useful information | 7: bag of coins, 1d4x100 (1wt/100c) | 8: valuable small item, 2d6x100, 0wt | 9: chest of coins/valuables, 1wt, 3d6x100 | 10: a magical item or effect | 11: many bags of coin, 2d4x100 | 12: sign of office worth 3d4x100 | 13: large art item, 4d4x100, 1wt | 14: unique item, 5d4x100 | 15: info to learn a new spell, roll again | 16: a portal/secret path, roll again | 17: something relating to a PC, roll again | 18+: a hoard - 1d10x1000 coins + 1d10x10 gems worth 2d6x100 each

**Bonus dice modifiers**: Hoarder (roll damage die twice, take higher) - Far from home (+1 ration, any taste) - Magical (+strange/possibly magical item) - Divine (a sign of a deity) - Planar (something otherworldly) - Lord over others (+1d4 to roll) - Ancient/noteworthy (+1d4 to roll)

Note that just because a monster has treasure doesn't mean the party has found it yet. They may need to look around.

## Quick Monster Stat Builder

Pick one from each relevant category - no need for a full pre-written stat block, build it live.

**How it hunts/fights** (sets base HP/damage die):

- Horde (large groups): 3 HP, d6
- Group (small groups): 6 HP, d8
- Solitary: 12 HP, d10

**Size**:

- Tiny (cat or smaller): -2 damage, Hand range
- Small/human-sized: Close range
- Large (horse-sized): +4 HP, +1 damage, Reach
- Huge (elephant+): +8 HP, +3 damage, Reach

**Armor**:

- None: 0 | Leather/hide: 1 | Mail/scales: 2 | Steel/carapace: 3 | Magical wards: 4

**Known for** (stack as many as fit the fiction):

- Unrelenting strength: +2 damage, Forceful
- Skill in offense: +advantage (roll twice, take better)
- Skill in defense: +1 armor
- Deft strikes: +1 piercing
- Uncanny endurance: +4 HP

**Armaments**:

- Vicious & obvious: +2 damage
- Small & weak: -1 die size
- Can cut through metal: 1-3 piercing, Messy
- Ignores armor entirely

**Other traits** (stack as fit):

- Bears a shield: Cautious, +1 armor
- No discernible anatomy: +1 armor, +3 HP
- Favored by the gods: Divine, +2 damage/+2HP/both
- Animated beyond biology: +4 HP
- Primary danger isn't wounds: Devious, -1 die size
- Ancient (species): +1 die size
- Abhors violence: +disadvantage (roll twice, take worse)
- Descriptive tags as needed: Stealthy, Organized, Intelligent, Terrifying

## Debilities (reminder - full list in [[core-moves]])

Weak/Shaky/Sick/Stunned/Confused/Scarred - tied to STR/DEX/CON/INT/WIS/CHA respectively.

## Monster Tag Glossary (what the tags above actually mean at the table)

Magical - magical through and through. Devious - its main danger isn't straightforward combat. Amorphous - bizarre/unnatural anatomy. Organized - group structure aids survival; killing one may draw others' wrath or trigger an alarm. Intelligent - smart enough that individuals may have extra training. Hoarder - almost certainly has treasure. Stealthy - avoids detection, prefers surprise. Terrifying - presence/appearance evokes fear. Cautious - prizes survival over aggression. Construct - made, not born. Planar - from beyond this world.

## Monster Species/Type Naming Guidelines

Always come up with a name for any created monsters. The players won't necessarily
learn the name immediately without a successful Spout Lore move, but know what it
is ahead of time. If the characters want to name it themselves, they will need
to hire a minstrel or other follower to help them popularize the name if they want
anyone but themselves and their friends to use it.

### Naming Guidelines

These are guidelines for generating **monster type/species names** (not unique
individual creature names — that's a separate, generation class which can use
names like "The Eternal One" and such that are discouraged here). Apply when
synthesizing a name from seed words + generated stat-block characteristics
(org, size, armor, damage die, traits, etc.)

### Preferred backbone pattern

**Adjective + Noun / Compound Noun** is the reliable default structure for
species/type names. Most good results take one of these forms:

- Earthy compound noun: terrain/substance + body part or behavior
  (e.g. Mudscale, Rootfang, Gravelmaw, Sludgehide)
- Invented/alien single word, with or without apostrophe
  (e.g. Krillix, Xilth'ra, Vex'thul)
- Onomatopoeia or sound-fragment + body-part suffix
  (e.g. Skree-Fang, Chittergrind)
- Hyphenated noun + agentive-verb combo
  (e.g. Bone-Eater, Marrowsipper)
- Sharp/flavorful epithet + noun — NOT generic epithets
  (e.g. Curmudgeon Bramble, Hag Bramble — not "Old Man Bramble")
- Descriptive-feature + noun, using exoticized/non-plain phrasing for
  numbers or counts (e.g. "Triple-Eyed Wretch" — not "Three-Eyed Wretch")

## Patterns to avoid

- **"The + [abstract/poetic noun]"** (e.g. "The Whispering Rot," "The Gnaw,"
  "The Patient Rot") — reads as vague flavor text, not a creature name.
  Situational at best (only for specific eldritch/thematic monster types),
  wrong as a general default.
- **"The + [sentence/phrase]"** (e.g. "The Nothing That Follows") — this
  register reads as a *unique individual's* name, not a species/type name.
- **Titles** (Sir, Captain, etc.) — pushes tone into comedy/silliness.
- **Ordinal suffixes** ("...the Third") — implies a unique named individual,
  wrong for a generic type.
- **Plain color-adjective + generic noun** (e.g. "The Gray Creeper") — reads
  flat and uninteresting.
- **Generic/bland epithets** (e.g. "Old Man ___") — the epithet+noun pattern
  itself is fine, but the epithet needs to be sharp/flavorful, not bland.
- **Plain cardinal counting of features** (e.g. "Three-Eyed ___") — flat;
  exoticize the number word/phrasing instead.
- **Colloquial/childlike register** (e.g. "Long-Leg Nasty") — only works for
  minor, non-dangerous creatures; breaks down for anything meant to read as
  threatening.

## Deadliness word ladder (tentative, base die only — see caveat)

These are some guides as to what terms to use for description and naming of
custom creatures. If a die has +2 or more, bump it's "die" description level.
Bump another level if it's "best out of two rolls". Bump yet again for
especially resistant to defeat immunities and offensive increasing special
abilities.

| Die | Words |
|---|---|
| d4 | meek, puny, scrawny, nuisance, pest, try to come up with similar but better ones |
| d6 | biting, snappish, feral, nasty, quick, also try to come up with similar bit better |
| d8 | dangerous, mean, savage, brutal, hungry, also need to improve on these |
| d10 | killer, deadly, vicious, merciless, ravenous, grim, terror, Butcher |
| d12 | annihilator, doom-, doom-bringer, unstoppable, horror , Obliterator |

Beyond d12: Ravager, Reaper, Eradicator, Devourer, Executioner, Harrower, Extinguisher, Scourge, Bonebreaker, Skullcrusher, Gravemaker, Wrath-Bound, Blood-Sated, Cataclysm-Born, Inexorable, Undying, Relentless

Cataclysmic and beyond even the previous level, possibly un-killable: Worldender, Godslayer, Deathless, Cataclysm-Born, Cataclysmic, Armageddon, Undying

## Adjacent design notes (not naming, but gathered alongside it)

Behavioral generation gaps identified alongside naming — not yet
implemented, needs design work of its own:

- **Aggression scale** (-2 to +4): cowardly/runs like a deer → meek/keeps
  distance → ambivalent/raccoon-like (stands ground, doesn't chase) →
  cautiously aggressive/ambush-waits → aggressive/no patience → berserk →
  horror (100% all-out, exists only to kill target).
- **Flee/engage thresholds** per aggression level: negative levels flee
  always if possible and only fight when cornered; 0 stands ground unless
  outmatched; +1 may flee/hide if needed; +2 may flee/hide if overwhelmed;
  +3/+4 never flee, +4 never even gets distracted from the target.
- **Hide vs. run preference**, independent axis: some creatures only have
  "hide under/behind terrain," not true camouflage. +1/+2 use hiding to
  ambush; low/negative levels use hiding (or running) to escape; +3/+4
  don't hide to flee at all (only to ambush, if ever).

## How to use this in practice

When generating a name: take the seed words (noun/verb/adjective or
similar), cross-reference the stat block's die-tier + relevant traits, and
synthesize using one of the ✅ patterns above. Never default to "The + noun"
or "The + phrase" for a type/species name. Reject and regenerate anything
matching an ❌ pattern above before presenting it.
