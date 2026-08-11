# Hacking Dungeon World: Custom Content, New Classes, and Conversion

Source: "Advanced Delving" chapter and the Teaching the Game / Adventure Conversion appendices. Complements [combat-and-custom-moves](references/combat-and-custom-moves.md) (which covers the fan-supplement take on writing custom moves) with the official design guidance.

## Where Moves Come From
Three entry points, most-to-least common:
- **Start with the trigger** - an action keeps coming up that feels distinct enough to need its own rule.
- **Start with the effect** - you know a class needs to *do* X, so work out what triggers it (this is how most class moves get written).
- **Start with the mechanics** (rare, be wary) - a cool mechanical idea first. Since moves flow from fiction, a purely-mechanical starting point is the weakest kind - make sure it earns a fictional trigger before it's real.

You can also port a move from another PbtA-style game, or adapt one.

## Categorizing a Move (helps you decide where it lives)
- **Special/world move**: about the environment or something you added to the setting - usually GM-facing, print it where players can see it unless it covers something PCs wouldn't know about.
- **Class move**: a specific competency tied to one class - add it to that class directly.
- **Basic/special move**: something any player might do, not class- or theme-specific. Comes up constantly → basic move. Comes up rarely → special move.
- **Player move tied to a monster**: rare - the player-side response to a specific monster's effect (a disease, a knockback wind). Most monster interactions already route through existing basic/class moves.
- **Monster move**: what a monster does *to* players - never a player move, no matter how tempting to make it "fair." Forcing every monster ability into player-move form kills the GM's creative flexibility.

## Writing a World/Custom Move (design notes)
Strongest when tied to a specific place/moment (a sewer hatch you know the party will open, a cursed lake), not a generic reskin of Defy Danger. Benefits: (1) pre-decides the tough choices so you're not improvising on the spot, (2) the specific trigger phrasing itself signals to players "this thing is always dangerous," which plain Defy Danger doesn't.

## Adding Class Moves
Don't let one class's moves creep into another's niche (a Thief-tier Cast a Spell would gut the Wizard's identity) - this is exactly why Multiclass moves apply at your level minus one, to protect each class's specialty. Be especially cautious about moves that just add flat damage or armor bonuses outside the existing progression - the game's danger level assumes the printed totals; padding them undermines threats you've built.

## Building a New Class
Steps beyond just writing moves: HP (base 4/6/8/10 + CON - 4 is deliberately fragile/needs backup, 6 can take a hit but isn't a fighter, 8 can mix it up some, 10 is a frontline warrior; giving a new class more than 10 steals the Fighter/Paladin's spotlight, giving it less than 4 risks making it unplayable), damage die (d4-d10, static bonuses optional - HP and damage tend to scale together, but a "fragile glass cannon" or "tanky pacifist" combo is legitimate design space), Alignment (most classes should offer Neutral; a *good* alignment move requires something beyond the ordinary flow of play - "when you gain treasure" is too passive, "when you gain treasure through lies and deceit" actually reflects character), Bonds (4 is the default count - add one for an unusually social class, remove one for a cloistered one; avoid moralizing bonds, but do reflect how the class interacts with allies; never hardcode proper names into a starting bond), Look (include at least one clothing option), Gear (always at least one weapon option and one armor option unless the class is deliberately non-combat capable; dungeon rations are close to mandatory).

## Move Structure Taxonomy (useful vocabulary when designing)
**Never write a trigger around a concrete unit of time** (a round, a fixed number of seconds/minutes) - Dungeon World's pacing is fluid like film editing, not a clock. "When you spend an hour studying" is wrong for the same reason "when you start a round adjacent to a dragon" is wrong.
Trigger types: action ("when you attack"), action-under-specific-circumstances ("when you attack a surprised enemy"), circumstance-with-no-character-action (Order Hirelings, End of Session), using-a-thing (magic items, a signature weapon), or from-now-on (a permanent standing effect, like Serenity or Poisoner).
Effect types (a move can combine several): roll, substitute one stat for another, negate damage, give a forward/ongoing bonus or penalty, deal/heal damage, offer a menu of choices, hold-and-spend, ask-and-answer, change circumstances going forward, mark XP, call for more information, add options to an existing move.
**Changing the basics** (e.g. replacing damage dice with flat numbers) is possible but should be rare and deliberate - never contradict the GM agenda/principles or break "take the action to get the effect."

## Direct Conversion (porting a non-DW monster stat block)
When you don't want to rebuild a monster from scratch via the normal creation questions, translate its existing stats directly:
- **Damage**: single die + bonus up to +10 → keep as-is. Multiple dice of the *same* size → roll them, take the highest. Multiple dice of *different* sizes → roll only the largest die, take the highest result.
- **HP**: given as Hit Dice → take the max value of the first HD, +1 per additional HD. Given as a flat number with no HD → divide by 4.
- **Armor**: average AC → 1 armor. Low AC → 0. High AC → 2 (3 for a defense-specialist). Nearly invulnerable → 4. +1 armor on top if the defense is explicitly magical.
- **Moves/Instinct**: derive directly from the original's special abilities/attacks list.

## Converting a Full Adventure/Module
1. Read the whole module once for a broad sense of factions, cool monsters, threats, and things PCs might care about - don't memorize stat blocks, and deliberately leave blanks for play to fill.
2. **Fronts first**: turn each faction/threat/NPC-group into a Danger inside one or more Fronts (per the normal Front rules) - ask "what's the worst version of this if the PCs never showed up?" for hard-move ammunition later. This is also where module NPCs become full Dangers or cast members.
3. **Monsters**: reuse existing DW stat blocks where they fit (just note the page); homebrew or Direct-Convert (above) anything unique. Don't chase "balance" - ask what the monster's *narrative purpose* is instead.
4. **Maps**: redraw freehand rather than copying 1:1, deliberately blanking rooms you don't care about and adding a tunnel or two - or, if short on time, keep the original map but only lightly annotate it and improvise the rest live rather than "looking it up."
5. **Magic & Treasure**: the module's magic items matter less mechanically in DW (advancement isn't item-driven) - reframe by purpose ("what's this for?") rather than by bonus, and it's fine to leave an item's exact effect as a note-to-self to discover in play.
6. **Optional - Introductory Moves**: for a con/one-shot without time for full character creation, write a short custom move per class (or a shared one) that fires right after chargen and hooks the character into the adventure's specific stakes - see example in the source if wanted.

## Teaching the Game (tips for a first session)
- **Pitch it in your own words** - don't read a script; be honest about why you're excited, and pitch *this specific adventure*, not the system in the abstract.
- **Present classes before rules** - describe what each class *does* in plain terms (the fighter has a one-of-a-kind signature weapon) rather than explaining the mechanics behind it, unless asked.
- **Character creation IS the rules tutorial** - don't frontload explanations; each player naturally encounters the rules relevant to their own class as they build it, in a sensible order.
- **Open on something that demands action** - a fight or a tense negotiation are the safest choices for brand-new players; don't assume they'll know what they want to do without a prompt.
- **Keep early monsters mechanically simple** (bleed normally, low/no armor, no piercing) so players learn ordinary damage/armor before hitting the exceptions.
- **Lean on Show Signs of an Approaching Threat especially with new players** - their danger-sense calibration may differ from what you expect; telegraph clearly at first, then dial it back as they learn.
- **If you're a first-time GM, anchor on just three moves**: Show Signs of an Approaching Threat, Deal Damage, Put Someone in a Spot - only check the full move list when none of those three fit. Familiarity with the rest comes with reps.
- **Treat session 1 as a pilot** - feel free to retcon, let a player swap classes, or scrap the opening adventure if it's not working; the level/bond cycle doesn't really kick in until a handful of sessions deep, so if the first one or two go well, plan for at least 5-10 more.
