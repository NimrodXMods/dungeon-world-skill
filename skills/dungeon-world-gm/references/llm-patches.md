# LLM "Patches" File

This file contains rule clarifications that models often get wrong. Read it when
entering the main gameplay loop ([SKILL-2-main-loop.md](SKILL-2-main-loop.md)),
not on every skill load. Style labels + hard narration bullets:
[SKILL.md](SKILL.md). Full narration essays: [gm-narration](references/gm-narration.md).

## Rule Clarifications

### Closing Open Threads and Adding Deeds

When a thread in `pause_state.open_threads` is answered, superseded by a bigger thread, or dead-ends, **remove it then and there**. If it was resolved rather than abandoned, append a `deeds` entry in the _same_ edit - naming the PCs and any NPCs who helped, and what came of it ("Fred and Joe solved the mystery of the disappearing cattle in Cowsburg with Old Marta's help, and gained the gratitude of the townsfolk"). One deed can close several threads that turned out to be one story. Threads are a live working set; `deeds` is the permanent record. Never rewrite or reorder existing deeds. A dead-ended thread with no deed associated is deleted without a deed.

### Fronts

There should always be at least one front. If user doesn't really have any preferences other than "go adventuring in an open world", always create at least one front at random anyway and don't tell them if there is a front or not, just whatever they learn as they learn it. "Open world" with no particular character goals except explore and wander around doesn't mean there's nothing going on in the world and nothing looking for them, or somehow getting in their way.

### Ranger Animal Companion

Ranger's Animal Companion "fight humanoids" free training (F-027, rulebook-digest) is always granted regardless of Cunning score. Read as "always free, doesn't count against the Cunning-based training budget".
