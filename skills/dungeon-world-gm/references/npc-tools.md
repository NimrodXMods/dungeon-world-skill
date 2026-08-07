# NPC & World Population Tools

## NPC Creation Questions

Always use `npc_gen.py` and `idea_gen.py` to help answer these.

1. What do they have that the PCs want?
2. What do they want, themselves?
3. What have they got right now?
4. How are they weird?

## Quest Motivations (why hire/send the party)

Well-suited for a job / a dark force threatens you or something you care about / retrieve something valuable / you're more than you seem / a distress call from a stranger (minor) / revenge for past injuries (minor) / a natural disaster looms (minor) / receive a mysterious gift (minor) - use `idea_gen.py`

**"I want to hire you to..."**: escort cargo/a person along a dangerous road / keep a place, person, or thing safe / retrieve an item or person / eliminate an existing threat - use `idea_gen.py`

## On a Missed Knowledge Roll (WIS/INT), if you want a "Suddenly Ogres"-style twist instead of plain failure

It's worse than it seemed / it's worse than you thought (ask the player first) / your answer is in another castle / the abyss gazes into you / you find trouble halfway there / trouble you missed earlier finds you / trigger a Front/Dungeon move or reveal a Grim Portent / make an off-screen move (after telling the truth) - use `idea_gen.py`

## Hirelings (official mechanics)

**Order Hirelings move**: hirelings do what you say so long as it isn't obviously dangerous/degrading/stupid and their cost is being met. When an order actually puts one in a dangerous/degrading/crazy spot, roll+Loyalty: 10+ they stand firm and do it. 7-9 they do it now but come back later with serious demands - meet those demands or they quit on the worst terms.

**Making one on the fly**: use `npc_gen.py`

**Loyalty shifts during play**: a real kindness or bonus is +1 Loyalty forward; disrespect is -1 forward; going too long without paying the agreed cost is -1 Loyalty *ongoing* until paid. A genuine shared triumph can permanently raise Loyalty; a serious failure or beating can permanently lower it.

**Skills**:

Use `npc_gen.py`, `idea_gen.py`, and adjust as needed.

- **Adept**: Arcane Assistance - aiding a lower-level spell than their skill improves its range/duration/potency (GM's call, told before casting); any backlash from the casting lands on the adept first.
- **Burglar**: Experimental Trap Disarming - leading the way through a trap, the burglar eats the full effect but the party gets +skill against it and +skill armor against it; usually needs healing after; can fully disarm it during a Make Camp near it.
- **Minstrel**: A Hero's Welcome - entering anywhere serving food/drink/entertainment with a minstrel, you're treated as a friend by default; also subtract their skill from all prices in that town.
- **Priest**: Ministry - healing at Make Camp with a priest present heals +skill HP extra. First Aid - a priest's hands-on healing heals 2×skill HP, but you take -1 forward (painful, distracting).
- **Protector**: Sentry - standing between you and an attack adds their skill to your armor against it, then reduces their skill by 1 until they heal/rest. Intervene - helping you Defy Danger, you may take a flat +1 from their aid instead of rolling normally, but then a 10+ result is capped at counting as a 7-9.
- **Tracker**: Track - given time to study a trail while making camp, can follow it to the next major change in terrain/travel/weather once camp breaks. Guide - leading the way, auto-succeeds on any Perilous Journey shorter (in rations) than their skill.
- **Warrior**: Man-at-arms - aiding your damage adds their skill to it, but they eat any resulting consequence (like a counterattack) instead of you.

## Steading Tags (for building settlements on the fly)

Use `steading_gen.py` and consult this for reference.

**Prosperity**: Dirt(1) nothing -> Poor(2) bare necessities -> Moderate(3) most mundane items -> Wealthy(4) any mundane item, most skilled labor -> Rich(5) any mundane item + pricey specialists
**Population**: Exodus(1) collapsing -> Shrinking(2) -> Steady(3) -> Growing(4) more people than buildings -> Booming(5) resources stretched thin
**Defenses**: None(1) -> Militia(2) -> Watch(3) -> Guard(4) standing defenders <100 -> Garrison(5) 100-300 -> Battalion(6) up to 1000 -> Legion(7) thousands

## Per-Class Background Questions (use during character creation, or to flesh out an NPC of that class)

- **Bard**: What are you running from? Who trained you? Why travel so much - want to settle?
- **Cleric**: Ever failed your deity, how'd you atone? Family's feelings on your calling? What'd you do before?
- **Druid**: Always like this, or something changed you? Who lives on your lands, what problems? Favorite animal?
- **Thief**: Part of a guild, why/not? Biggest score ever? Who's your competition? Why'd you return the last thing you stole?
- **Wizard**: Refused a wealthy stranger's ritual request - who were they? How do people treat known wizards? What magical mystery haunts you?
- **Barbarian**: Anyone from home with you? Most dangerous creature from your homeland? Why can't you go back?
- **Fighter**: Anyone ask to be your apprentice? Willing draftee or conscript? Who wielded your signature weapon before you?
- **Paladin**: Dedicated to a lord/deity, or a personal quest? What are you atoning for? Why'd your family send you away?
- **Ranger**: What did you lose out here, who took it? What's the one thing in this forest that must be protected? Where'd you meet your animal companion?
