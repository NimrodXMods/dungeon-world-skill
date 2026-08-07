## Attribution — Dungeon World text

`xml/` is a verbatim copy of the *Dungeon World* core rulebook text as published by the
authors, in the Adobe InDesign story XML format they use to lay out the book. Artwork,
fonts, and layout files are not included.

Dungeon World is the work of **Sage LaTorra** and **Adam Koebel**, and the text of the
game is licensed under the **Creative Commons Attribution 3.0 Unported License**
(CC BY 3.0). Per the license and the authors' own stated terms, this text may be used,
modified, and redistributed freely provided the authors are credited.

Sources verifying the license and authorship:

- License: https://github.com/Sagelt/Dungeon-World/blob/master/LICENSE
- Repo README (confirms full text is released, art excluded, "credit the authors" is
  the only condition): https://github.com/Sagelt/Dungeon-World/blob/master/README.md
- `Sagelt` GitHub account = Sage LaTorra (co-author), confirmed via his own site:
  https://svirfnebl.in/2017/06/30/dungeon-world-five-years-in/
- `Sagelt` GitHub profile (displays "Sage LaTorra," links to the above site, and pins
  the `Dungeon-World` and `dwdotcom` — Dungeon World's own website source — repos):
  https://github.com/Sagelt

No claim of rights is made here beyond what CC BY 3.0 already grants. This copy exists
solely as reference material for the `dungeon-world-gm` skill.

## Provenance and refreshing

| | |
|---|---|
| Upstream | https://github.com/Sagelt/Dungeon-World |
| Path | `text/` |
| Commit | `e67bd51c09d24518a7f989149b76094fbcc7fecc` (2023-02-27) |
| Files | 37 `.xml` (24 chapters, `appendices/` ×4, `monster_settings/` ×9) |

The files are **byte-identical to upstream** — nothing is rewritten, reformatted, or
annotated on the way in. That is deliberate: it keeps a refresh a clean `git diff`, and it
means anchors must be *computed* from the heading structure rather than stored in the
files. `scripts/rulebook.py` does that computation and is the only place it happens.

To refresh:

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/Sagelt/Dungeon-World.git dw
cd dw && git sparse-checkout set text && git rev-parse HEAD   # record this SHA above
cp -r text/. <this-directory>/xml/
```

Then re-run `python tools/validate_skill.py` — it re-checks that every `[xml:...]` anchor
cited in `L1-digest.md` and `L0-index.md` still resolves, so a refresh that renames or
removes a heading fails loudly instead of silently breaking L3 lookups.

`tools/extract_monsters.py` reads `xml/monster_settings/` from this same vendored copy, so
it and the digest can never drift onto different revisions of the text.

## A note on the previous source

This directory previously held `core-rulebook-full-text.txt`, a `pdftotext -layout` dump
addressed by `===== PAGE N =====` markers. It was replaced by the XML because page
boundaries are an artifact of print layout rather than of meaning — a single move could
straddle two pages, and one page could hold three unrelated things. The page numbers cited
in `L1-digest.md` are retained, but now serve only as a courtesy pointer for a human
holding the printed 1st edition; they are no longer how the text is retrieved.
