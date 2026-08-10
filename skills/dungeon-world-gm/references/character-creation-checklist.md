# Character Creation Checklist

Purpose: a decision checklist to run character creation reliably. Part 1 covers
every class. Part 2 covers class-specific decisions. Work through Part 1 in
order, then jump to the player's class in Part 2 for the choices unique to it.
Source: core rulebook (Sage LaTorra & Adam Koebel) for the 8 core classes;
"Playbooks" fan supplement by Stefan Grambart for Barbarian and Immolator.

Sources for full move text: use `rulebook-digest/L0-index` and
`python3 rulebook.py --help-llm` for the 8 core classes. Barbarian and
Immolator move text isn't in the digest; those are in `extra-classes/*`.

This checklist only tracks *what to decide*, not full move
wording — confirm exact move text against those sources when it matters.

How to *present* closed menus to the user: **[[elicitation]]** (on demand).

---

## How to run this checklist

1. Walk **Part 1 in order**. After **Class** is chosen, open that class's
   section in Part 2 and use it for every later closed list (race, look,
   alignment, gear, embedded starting-move choices).
2. For every step with a **closed option set** in Part 2, **list the options
   before asking** — never "what race?" without the class's race list, never
   "what alignment?" without the class's alignments. See [[elicitation]].
3. **Locked choices** (e.g. Paladin is Human only): state the lock and record
   it; do not pretend there is a free pick.
4. **Multi-select** steps (Fighter signature-weapon enhancements, Barbarian
   appetites, gear "choose two", etc.): say how many to pick and list the full
   set in one elicitation.
5. **Free-text** steps (name, custom look entries, deity name, companion name):
   open question; optional 2–3 examples from the class lists are fine without
   forcing them.
6. Do **not advance** past starting moves or gear while an embedded sub-choice
   is still TBD (spellbook picks, Signature Weapon build, Animal Companion
   block, poison choice, etc.).
7. Homebrew / not on the list is fine — say so when offering menus ("or name
   something else and we'll adapt").
8. Speed mode: if the user wants to go fast, you may batch several *independent*
   Part 2 picks for the same class in one message; keep branching picks
   (class → race) sequential.
9. When the sheet is complete, write/update the character YAML via the template
   and `yamledit` as usual; then return to campaign/session flow.

---

## Part 1: Universal Questions (Every Class)

These apply no matter what class the player picks. Ask them in this order.
When a step has options in Part 2, surface those options with [[elicitation]].

1. [ ] **Class.** Which class? (If two players want the same class in a party
   game, they should compromise — DW default is one of each.)
2. [ ] **Race** — *only if the class offers race options* (most do; a few, like
   Paladin, are locked to one race). Which race? This grants a specific race
   move — make sure to record it, not just the race name.
3. [ ] **Name.** Pick from the class's name list, mix-and-match a list with a
   custom name, or invent one entirely.
4. [ ] **Look.** One choice from *each* look category the class provides (eyes,
   hair, body, clothing — categories vary by class, see Part 2). Custom
   entries are always fine.
5. [ ] **Stats.** Assign 16(+2), 15(+1), 13(+1), 12(+0), 9(+0), 8(–1) to the six
   stats, one score per stat. Use separate elicitations to ask them what stat they
   want to assign each score to starting with 16 and moving down. Before and while
   doing this, advise them regarding what Part 2 gives for a stat-priority hint
   and what sort of moves are assisted by each stat bonus modifier. For example,
   they will want to know that spellcasting for a wizard will get a +2 by assigning
   the 16 to INT, or that assigning the 16 to STR will give +2 to hack and slash.
   Same for other standard and class moves. At the very end, print out all of their
   selections along with example moves that get each modifier and ask if they want
   to make any changes.
6. [ ] **Max HP.** Class base HP + Constitution score. Record it, start at max.
7. [ ] **Damage die.** Note the class's base damage die.
8. [ ] **Starting moves.** Walk the starting-moves list for the class (Part 2).
   Some are automatic; some require a choice (e.g. Fighter's Signature
   Weapon, Wizard's spellbook, Cleric's deity). Resolve every embedded choice
   now — don't leave "TBD" on a move that needs a sub-choice.
9. [ ] **Alignment.** Choose one of the class's alignment options (Part 2 lists
   them — they differ meaningfully by class and drive bonus XP, so don't
   treat this as a throwaway pick).
10. [ ] **Gear.** Work through the class's gear choices (weapon/armor loadout,
    the "choose one/two of these" consumables list). Total the armor and
    check Load (base + STR) against what's carried.
11. [ ] **Bonds.** Fill in **at least one** bond blank with another PC's name
    (Part 2 has the class's bond templates). More than one is encouraged.
    Custom bonds are fine too. In a solo game, bonds can point at key NPCs
    instead of party members — use judgment.
12. [ ] **Introduce the character.** Once everyone (or the solo player) is ready:
    share look, class, and anything else pertinent. This is the GM's cue to
    ask connective questions — "what do you think about that?", "have you
    met X before?" — to weave the character into the world and the party.
13. [ ] **Coin.** Record starting coin if the gear choices included any. There
    is no default minimum starting amount of coins. They have to be selected in
    lieu of other equipment.

Don't forget: some classes have a chargen sub-decision baked into a starting
move rather than a separate step (e.g. Cleric's deity/domain, Wizard's
spellbook, Ranger's animal companion). Those are called out per-class below
so they don't get skipped.

---

## Part 2: Class-Specific Questions

### Barbarian
*(An "extra class" in `extra-classes`, not in core rules.)*

- **Race:** "Outsider" — elf, dwarf, halfling, or human, but not from around
  here. The move (Outsider — GM asks about your homeland each session) is the
  same regardless of which race is chosen; race here is flavor only.
- **Look categories:** Body, Eyes, Decoration, Clothes.
- **Stat priority hint:** STR (Hack & Slash, Bend Bars) and CON (Last
  Breath-adjacent survivability, appetite rolls).
- **HP:** 8+CON.
- **Starting moves:**
  - Choose **one**: *Full Plate and Packing Steel* (ignore clumsy tag) or
    *Unencumbered, Unharmed* (+1 armor while under Load, unarmored, no
    shield).
  - Automatic: *The Upper Hand* (Last Breath bonus), *What Are You Waiting
    For?* (challenge roll).
  - *Herculean Appetites* — **choose two** appetites from: Pure destruction,
    Power over others, Mortal pleasures, Conquest, Riches and property, Fame
    and glory.
  - Automatic: *Musclebound* (weapons gain forceful + messy while wielded).
- **Alignment:** Chaotic (eschew a convention of the civilized world) or
  Neutral (teach someone the ways of your people). No Good/Evil option.
- **Gear:** Max Load 8+STR. Starts with Dungeon Rations, a Dagger, and a
  custom "token of where you've travelled." Choose weapon: Axe or
  Two-Handed Sword. Choose one: [Adventuring Gear + Dungeon Rations] or
  [Chainmail].
- **Bonds:** fill at least one — companion is puny/foolish but amusing;
  companion's ways are strange/confusing; companion is always getting into
  trouble, must protect them; companion shares my hunger for glory.

### Bard

- **Race options:** Elf or Human (each grants a distinct move).
- **Look categories:** Eyes, Hair, Clothes, Body.
- **Stat priority hint:** CHA (Arcane Art, Charming and Open).
- **HP:** 6+CON.
- **Starting moves (all automatic, but each has an embedded choice):**
  - *Arcane Art* — no chargen choice, but note it's their spell-like move.
  - *Bardic Lore* — choose **one area of expertise**: Spells and Magicks;
    The Dead and Undead; Grand Histories of the Known World; A Bestiary of
    Creatures Unusual; The Planar Spheres; Legends of Heroes Past; Gods and
    Their Servants.
  - *Charming and Open* — no chargen choice.
  - *A Port in the Storm* — no chargen choice.
- **Alignment:** Good (perform your art to aid someone), Neutral (avoid a
  conflict or defuse a tense situation), Chaotic (spur others to significant
  unplanned decisive action).
- **Gear:** Load 9+STR. Dungeon Rations. Choose an instrument (flavor only,
  0 weight): father's mandolin, fine lute, courting pipes, stolen horn,
  unplayed fiddle, or songbook in a forgotten tongue. Choose clothing:
  Leather armor or Ostentatious clothes. Choose armament: Dueling rapier, or
  [Worn bow + arrows + short sword]. Choose one: Adventuring gear, Bandages,
  Halfling pipeleaf, or 3 coins.
- **Bonds:** fill at least one — not my first adventure with X; sang stories
  of X before meeting them; X is the butt of my jokes; writing a ballad
  about X; X trusted me with a secret; X does not trust me (with reason).

### Cleric

- **Race options:** Dwarf or Human.
- **Look categories:** Eyes, Hair, Clothing, Body.
- **Stat priority hint:** WIS (Cast a Spell, Turn Undead, Commune).
- **HP:** 8+CON.
- **Starting moves — embedded choices:**
  - *Deity* — name your god, and choose **one domain**: Healing and
    Restoration; Bloody Conquest; Civilization; Knowledge and Hidden Things;
    The Downtrodden and Forgotten; What Lies Beneath.
  - Choose **one precept** of your religion (each adds a specific Petition):
    sanctity of suffering (Petition: Suffering); cultish/insular (Petition:
    Gaining Secrets); important sacrificial rites (Petition: Offering); trial
    by combat (Petition: Personal Victory).
  - *Commune* (performed at chargen to set starting spells) — granted spells
    whose total level ≤ level+1 (so 2 levels' worth at level 1), plus all
    rotes prepared free. Ask: which spells does the cleric start with
    prepared?
- **Alignment:** Good (endanger yourself to heal another), Lawful (endanger
  yourself following your church's precepts), Evil (harm another to prove
  your church's superiority).
- **Gear:** Load 10+STR. Dungeon Rations, a custom holy symbol. Choose
  defenses: Chainmail or Shield. Choose armament: Warhammer, Mace, or
  [Staff + bandages]. Choose one: [Adventuring gear + Dungeon rations] or
  Healing potion.
- **Bonds:** fill at least one — X has insulted my deity, I don't trust
  them; X is good and faithful, I trust them implicitly; X is in constant
  danger, I will keep them safe; I am working on converting X to my faith.

### Druid

- **Race options:** Elf, Human, or Halfling.
- **Look categories:** Eyes, Hair, Clothing.
- **Stat priority hint:** WIS (shapeshifting-adjacent rolls, Communion of
  Whispers).
- **HP:** 6+CON.
- **Starting moves — embedded choices:**
  - *Born of the Soil* — choose **one Land** you're attuned to (Great
    Forests, Whispering Plains, Vast Desert, Stinking Mire, River Delta,
    Depths of the Earth, Sapphire Islands, Open Sea, Towering Mountains,
    Frozen North, Blasted Wasteland). Also choose a **tell** — a physical
    trait marking them as born of the soil (animal feature or something more
    abstract) that persists through shapeshifting.
  - Automatic: *By Nature Sustained*, *Spirit Tongue*.
- **Alignment:** Chaotic (destroy a symbol of civilization), Good (help
  something/someone grow), Neutral (eliminate an unnatural menace).
- **Gear:** Load 6+STR. Custom token of your Land. Choose defenses: Hide
  armor or Wooden shield. Choose armament: Shillelagh, Staff, or Spear.
  Choose one: Adventuring gear, Poultices and herbs, Halfling pipeleaf, or 3
  antitoxin.
- **Bonds:** fill at least one — X smells more like prey than a hunter; the
  spirits warned me of danger following X; I've shown X a secret rite of
  the Land; X has tasted my blood and I theirs, we are bound by it.

### Fighter

- **Race options:** Dwarf, Elf, Halfling, or Human.
- **Look categories:** Eyes, Hair/Headgear, Skin, Body.
- **Stat priority hint:** STR (Hack & Slash, Bend Bars Lift Gates).
- **HP:** 10+CON.
- **Starting moves — embedded choice (Signature Weapon):**
  - Choose a base description (all 2 weight): Sword, Axe, Hammer, Spear,
    Flail, or Fists.
  - Choose its range: Hand, Close, or Reach.
  - Choose **two enhancements**: hooks and spikes (+1 dmg, +1 weight);
    sharp (+2 piercing); perfectly weighted (add precise); serrated edges
    (+1 dmg); glows near a chosen creature type; huge (add messy + forceful);
    versatile (add a range); well-crafted (–1 weight).
  - Choose a look for it: Ancient, Unblemished, Ornate, Blood-stained,
    Sinister.
- **Alignment:** Good (defend those weaker than you), Neutral (defeat a
  worthy opponent), Evil (kill a defenseless or surrendered enemy).
- **Gear:** Load 12+STR. Carries the Signature Weapon and Dungeon Rations.
  Choose defenses: [Chainmail + adventuring gear] or Scale armor. Choose
  **two**: 2 Healing potions, Shield, [Antitoxin + rations + poultices &
  herbs], or 22 coins.
- **Bonds:** fill at least one — X owes me their life, whether they admit it
  or not; I have sworn to protect X; I worry about X's ability to survive in
  the dungeon; X is soft, but I will make them hard like me.

### Immolator
*(An "extra class" in `extra-classes`, not in core rules.)*

- **Race options:** Human or Salamander (each grants a distinct move — note
  Salamander is a fire-touched species specific to this playbook, not a core
  DW race).
- **Look categories:** Body, Eyes, Voice, Demeanour.
- **Stat priority hint:** CON (Burning Brand) and WIS (Zuko Style, Lore of
  Flame).
- **HP:** 4+CON.
- **Starting moves:** all five are automatic, no chargen sub-choice —
  *Burning Brand*, *Give Me Fuel, Give Me Fire*, *Fighting Fire with Fire*,
  *Zuko Style*, *Hand Crafted*. (Burning Brand's tag choice happens at time
  of casting, not chargen.)
- **Alignment:** Evil (sacrifice an unwilling victim to the flames),
  Chaotic (spread a dangerous new idea), Neutral (exchange a freely-given
  sacrifice for a service rendered).
- **Gear:** Load 9+STR. No weapons or armor needed. Starts with a custom
  "symbol of your sacrifices past," Adventuring Gear, and 1 Healing Potion.
  Choose **two**: Dungeon Rations, 1 Healing Potion, or 10 Coins.
- **Bonds:** fill at least one — X has felt the hellish touch of fire, now
  they know my strength; I will teach X the true meaning of sacrifice; I
  cast something into the fire for X and still owe them their due.

### Paladin

- **Race:** Human only — no choice here, just note the automatic race move.
- **Look categories:** Eyes, Hair/Helmet, Holy Symbol, Body.
- **Stat priority hint:** CHA (Lay on Hands, I Am the Law) alongside
  STR/CON for melee durability.
- **HP:** 10+CON.
- **Starting moves — embedded choice:** none permanent but see Quest move.
- **Alignment:** Lawful (deny mercy to a criminal or unbeliever) or Good
  (endanger yourself to protect someone weaker than you). No Neutral/Evil/
  Chaotic option.
- **Gear:** Load 12+STR. Starts with Dungeon Rations, Scale armor, and a
  custom "mark of faith." Choose weapon: [Halberd] or [Long sword + shield].
  Choose one: Adventuring gear or [Dungeon rations + healing potion].
- **Bonds:** fill at least one — X's misguided behavior endangers their very
  soul; X has stood by me in battle, can be trusted completely; I respect
  X's beliefs but hope they'll see the true way; X is a brave soul, I have
  much to learn from them.

**Quest (move)** which players may wish to activate soon but isn't required:
"When you dedicate yourself to a mission through prayer and ritual cleansing,
state what you set out to do:"
  - State what the Quest targets: Slay ___, Defend ___, or Discover the
    truth of ___.
  - Choose **up to two boons**: unwavering direction to ___; invulnerability
    to ___ (e.g. edged weapons, fire, enchantment); a mark of divine
    authority; senses that pierce lies; a voice that transcends language;
    freedom from hunger/thirst/sleep.
  - The GM then assigns the vow(s) required to maintain the blessing:
    Honor (no cowardly tactics/tricks), Temperance (no gluttony), Piety
    (daily holy services required), Valor (no suffering an evil creature to
    live), Truth (no lies), or Hospitality (comfort to those in need
    required).

### Ranger

- **Race options:** Elf or Human.
- **Look categories:** Eyes, Hair, Clothing, Body.
- **Stat priority hint:** WIS (Hunt and Track) and DEX (Called Shot).
- **HP:** 8+CON.
- **Starting moves — embedded choice (Animal Companion):**
  - Name the companion and choose a species (wolf, cougar, bear, eagle, dog,
    hawk, cat, owl, pigeon, rat, mule — or similar).
  - Choose a **base stat block** (four presets trading off Ferocity,
    Cunning, Armor, Instinct).
  - Choose **strengths** up to its Ferocity score (fast, burly, huge, calm,
    adaptable, quick reflexes, tireless, camouflage, ferocious, intimidating,
    keen senses, stealthy).
  - It's automatically trained to fight humanoids; choose **additional
    trainings** up to its Cunning (hunt, search, scout, guard, fight
    monsters, perform, labor, travel).
  - Choose **weaknesses** up to its Instinct (flighty, savage, slow, broken,
    frightening, forgetful, stubborn, lame).
- **Alignment:** Chaotic (free someone from literal or figurative bonds),
  Good (endanger yourself to combat an unnatural threat), Neutral (help an
  animal or spirit of the wild).
- **Gear:** Load 11+STR. Dungeon Rations, Leather armor, a bundle of arrows.
  Choose armament: [Hunter's bow + short sword] or [Hunter's bow + spear].
  Choose one: [Adventuring gear + rations] or [Adventuring gear + arrows].
- **Bonds:** fill at least one — I have guided X before, they owe me for
  it; X is a friend of nature, so I will be their friend; X has no respect
  for nature, so I have none for them; X doesn't understand life in the
  wild, so I will teach them.

### Thief

- **Race options:** Halfling or Human.
- **Look categories:** Eyes, Hair, Clothing, Body.
- **Stat priority hint:** DEX (Trap Expert, Tricks of the Trade, Backstab).
- **HP:** 6+CON.
- **Starting moves — embedded choice (Poisoner):**
  - Choose **one poison** from: Oil of Tagit (applied — target falls into a
    light sleep); Bloodweed (touch — target deals –1d4 damage ongoing until
    cured); Goldenroot (applied — target treats the next creature they see
    as a trusted ally, until proved otherwise); Serpent's Tears (touch —
    anyone dealing damage to the target rolls twice and takes the better
    result). That poison becomes safe for the thief to handle, and they
    start with 3 uses of it.
  - Automatic: *Trap Expert*, *Tricks of the Trade*, *Backstab*, *Flexible
    Morals*.
- **Alignment:** Chaotic (leap into danger without a plan), Neutral (avoid
  detection or infiltrate a location), Evil (shift danger/blame from
  yourself to someone else).
- **Gear:** Load 9+STR. Dungeon Rations, Leather armor, 3 uses of chosen
  poison, 10 coins. Choose arms: [Dagger + short sword] or [Rapier]. Choose
  a ranged weapon: 3 throwing daggers or [Ragged Bow + arrows]. Choose one:
  Adventuring gear or Healing potion.
- **Bonds:** fill at least one — I stole something from X; X has my back
  when things go wrong; X knows incriminating details about me; X and I
  have a con running.

### Wizard

- **Race options:** Elf or Human.
- **Look categories:** Eyes, Hair, Robes, Body.
- **Stat priority hint:** INT (Cast a Spell).
- **HP:** 4+CON.
- **Starting moves — embedded choices:**
  - *Spellbook* — choose **three first-level spells** for the spellbook
    (plus cantrips, which don't count against any limit).
  - *Prepare Spells* (performed at chargen to set starting loadout) —
    prepare spells from the spellbook whose total level ≤ level+1, plus all
    cantrips. Ask: which spells does the wizard start with prepared?
- **Alignment:** Good (use magic to directly aid another), Neutral (discover
  something about a magical mystery), Evil (use magic to cause terror and
  fear).
- **Gear:** Load 7+STR. Spellbook, Dungeon Rations. Choose defenses:
  Leather armor or [Bag of books + 3 healing potions]. Choose weapon:
  Dagger or Staff. Choose one: Healing potion or 3 antitoxins.
- **Bonds:** fill at least one — X will play an important role in the
  events to come, I have foreseen it; X is keeping an important secret from
  me; X is woefully misinformed about the world, I will teach them all I
  can.

---

## Notes for future maintenance

- If new playbooks get added to the campaign (e.g. supplements, homebrew
  classes), extend Part 2 with the same structure: race options,
  look categories, stat hint, HP, starting-move embedded choices,
  alignment options, gear choices, bond templates.
