---
name: pptx-toolkit
description: Create, edit, inspect, render, and comment-mine PowerPoint .pptx files programmatically with python-pptx and raw OOXML on Windows. Use when creating a new deck at a given slide size with a real background colour, adding, moving, resizing or deleting shapes in an existing deck, rewriting text runs while preserving formatting, deleting or reordering slides, exporting slides to PNG or PDF via PowerPoint COM (LibreOffice is not available), or extracting modern comments from ppt/comments/modernComment_*.xml and mapping them to slide numbers and anchor shapes. Also draws any preset geometry, syntax-highlights code fragments from the profile's code_palette, draws palette-coloured pictograms, and estimates text width so overflow and Japanese line breaks can be checked before rendering. Includes fixes for the white-on-white, corrupt-file and blank-paragraph failures that naive python-pptx or lxml edits cause.
---

# pptx-toolkit

Programmatic .pptx editing that survives contact with PowerPoint.

## Requirements

* **Windows + デスクトップ版 PowerPoint。** レンダリングは PowerPoint COM (`win32com`
  の `Dispatch('PowerPoint.Application')`) 経由のみで、**LibreOffice フォールバックは無い**。
  PowerPoint が無い環境では編集・検査はできるが、`render_deck.py` の PNG/PDF 書き出しは動かない。
* **Python 3.10 以上**（3.13.5 で検証）
* `pip install python-pptx pywin32 pypdfium2`

| パッケージ | 必要な範囲 | 検証版 |
| --- | --- | --- |
| `python-pptx` | 全スクリプト。これが無いと何も動かない | 1.0.2 |
| `lxml` | `deckkit` の raw OOXML 操作（python-pptx が依存として入れる） | — |
| `pywin32` | `render_deck.py` の PNG / PDF 書き出しのみ | — |
| `pypdfium2` | `render_deck.py --from-pdf`（既存 PDF のラスタ化）のみ | — |

PowerPoint の実行ファイルパスは指定不要。COM がレジストリから解決する。

## パス表記 — `<pptx-toolkit>` の読み替え

ドキュメントとレシピ中の `<pptx-toolkit>` は、このスキルが実際に置かれているディレクトリを指す。

| インストール形態 | `<pptx-toolkit>` |
| --- | --- |
| ユーザースキル | `~/.claude/skills/pptx-toolkit` |
| プロジェクトスキル | `<project>/.claude/skills/pptx-toolkit` |
| プラグイン | `${CLAUDE_PLUGIN_ROOT}/skills/pptx-toolkit` |

同様に `<project>` はデッキプロジェクトのルート。

スクリプトは `<pptx-toolkit>/scripts/` にある。CLI（`new_deck.py`, `inspect_deck.py`,
`check_deck.py`, `render_deck.py`, `extract_comments.py`, `pictogram.py`）は
そのままパス指定で実行すればよい。**使い捨てのバッチスクリプトから `deckkit` を
import する場合だけ**、先頭でこのディレクトリを絶対パスで `sys.path` に入れる:

```python
import sys
sys.path.insert(0, r'<pptx-toolkit>/scripts')   # ← 実際の絶対パスに置き換える
from deckkit import R, set_runs, shape_by_id
```

## Rule 0 — back up before any batch edit

Batch edits are not undoable. `deckkit.save_backup(path)` or a plain `cp` first.
If the deck is under git, an uncommitted deck is a deck you can lose.

## Creating a deck

**Never hand-roll `Presentation()`.** Its default is 10×7.5in (4:3) on a WHITE canvas,
while `deckkit.R()` defaults to near-white text — so a naive new deck is invisible text
at the wrong size, and every storyboard y-coordinate is off. Use:

```
python new_deck.py slides/deck.pptx --preset dark --write-profile slides/deck-profile.json
```

That sets the size *and* the `<p:sldSz @type>`, paints the background on the master,
clears it from every layout (so even a hand-added slide inherits it), and draws one
placeholder title slide as proof the palette is internally legible.

## The loop

1. **`inspect_deck.py`** — get shape ids. You cannot edit a shape you cannot identify.
2. Write a throwaway batch script that imports `deckkit` (see `reference/recipes.md`).
3. **`check_deck.py`** — static lint, no PowerPoint. Catches corruption *before* you spend
   a render cycle discovering it.
4. **`render_deck.py`** — export PNG.
5. **Look at the PNGs.** python-pptx will report text that PowerPoint refuses to draw.

## Eight gotchas that will bite you

Full symptoms and repros: `reference/ooxml-gotchas.md`.

1. **Build XML with `pptx.oxml.parse_xml`, never `lxml.etree.fromstring`.** Plain lxml
   elements lack python-pptx's custom element classes; `slide.shapes` iteration then dies
   with `'_Element' object has no attribute 'has_ph_elm'`. Use `deckkit.frag()`.
2. **When deleting by `p:cNvPr/@id`, only touch `sp|cxnSp|pic|graphicFrame|grpSp`.**
   `<p:nvGrpSpPr>` also carries a `cNvPr` (id="1"); removing it corrupts the spTree.
   PowerPoint then says 「ファイルを開けません」 **while python-pptx still opens it fine** —
   the worst possible asymmetry. Use `deckkit.delete_ids()` / `delete_range()`.
3. **`<a:endParaRPr>` must stay the LAST child of its paragraph.** Rebuild a paragraph's
   runs and append after a leftover endParaRPr, and the paragraph **renders BLANK** in
   PowerPoint though the XML looks right and python-pptx reads it back. Use `deckkit.set_para()`.
4. **Slide deletion needs the drop_rel dance:** `prs.slides._sldIdLst` →
   `prs.part.drop_rel(sldId.get(qn('r:id')))` → `sldIdLst.remove(sldId)`. Delete the
   highest position first. Comments anchored to a deleted slide drop with it.
   Use `deckkit.delete_slides()`.
5. **Rendering is PowerPoint COM only.** No LibreOffice. `render_deck.py` handles the
   COM lifecycle; a corrupt deck fails at `Presentations.Open` with a clear message.
6. **Never give a shape an adjust-value name it does not define.** `mathMultiply` has
   `adj1`, not `adj`; `flowChartManualOperation` has none. PowerPoint then refuses the
   file **while `check_deck.py` reports it clean** — the same asymmetry as gotcha 2.
   `shape()` maps an int to `name="adj"`, a list to `adj1, adj2, ...`, a dict to the names
   you give. **When unsure, pass no `adj` at all.**
7. **`spc_pct` is a percentage, not a multiplier.** `spc_pct=1.25` means 1.25% line
   spacing, and every paragraph draws on top of the first. You want `spc_pct=125`.
8. **`head=` is not the pointy end — draw arrows with `arrow()`.** OOXML's `<a:headEnd>`
   decorates the line's **start**, `<a:tailEnd>` its **end**, and `connector()` passes both
   straight through, so `connector(..., head='triangle')` puts the arrowhead on the end the
   arrow comes *from*. `flipH`/`flipV` then swap which box corner that is. Nothing errors and
   nothing looks broken — the diagram just **contradicts its own caption**, and only a human
   reading the rendered PNG catches it. Use `arrow(slide, x1,y1, x2,y2)`: the head always
   lands on `(x2,y2)`.

## Scripts

| Command | Purpose |
| --- | --- |
| `python new_deck.py <out> [--preset dark\|light] [--profile p.json] [--slides N] [--title ...] [--write-profile p] [--no-theme] [--force]` | create a deck: size + `sldSz type` + background on the master + theme accents + a placeholder title slide. Refuses to overwrite (exit 2) |
| `python inspect_deck.py <deck>` | slide count, size, per-slide first line |
| `python inspect_deck.py <deck> --slide 39 [--runs] [--json]` | every shape: id / type / x,y,w,h in inches / text. `--runs` adds per-run size, font, bold, colour |
| `python check_deck.py <deck> [--profile p.json] [--slide N] [--quiet] [--contrast]` | static lint. exit 0 clean, 1 findings, 2 unreadable. `--contrast` is advisory — see below |
| `python check_deck.py <deck> --infer-profile` | emit a starter deck-profile.json from the deck's own colours/fonts/geometry |
| `python extract_comments.py <deck> --dry-run` | list comments: slide, anchor, timestamp, first line |
| `python extract_comments.py <deck> --round r003 [--out path]` | write a `comment-import-r003.md` skeleton. Refuses to overwrite. Source deck is only read |
| `python render_deck.py <deck> --slides 20,22-25 --png-dir out/` | PNG via COM (default 1600x900) |
| `python render_deck.py <deck> --pdf out/deck.pdf` | whole-deck PDF via COM |
| `python render_deck.py --from-pdf x.pdf --pages 39 --png-dir out/` | raster an existing PDF (pypdfium2, no PowerPoint) — for the PPTX-vs-PDF diff check |
| `python pictogram.py <out.pptx> [--profile p.json]` | write a labelled contact sheet of every pictogram. **Run this after adding one** |

`deckkit.py` and `codehl.py` are **import-only**, not CLIs — every edit is bespoke.
`pictogram.py` is both: import `draw`, or run it to eyeball the catalogue.

## deckkit API

```python
import sys
sys.path.insert(0, r'<pptx-toolkit>/scripts')
from pptx import Presentation
from deckkit import R, set_runs, set_para, shape_by_id, el_by_id, set_xfrm, \
                    rrect, textbox, arrow, connector, move_before, move_after, save_backup
```

| Function | Purpose |
| --- | --- |
| `emu(inches)` | inches → EMU (914400/in) |
| `frag(xml)` | parse an XML fragment **correctly** (gotcha 1) |
| `spTree(slide)` / `shape_elements(slide)` | the shape tree / only real shape elements |
| `next_id(slide)` | next free `cNvPr@id` |
| `shape_by_id(slide, id)` | python-pptx shape object |
| `el_by_id(slide, id)` | raw lxml element (for xfrm / fill / line edits) |
| `delete_ids(slide, ids)` / `delete_range(slide, lo, hi, keep=())` | safe deletion (gotcha 2) |
| `move_before/after(slide, el, ref)` | z-order |
| `set_xfrm(el, x, y, w, h)` | position/size in inches; any subset |
| `R(text, sz, color, font, b, i, hl, u)` | one text run spec. `hl` = highlighter colour, `u` = underline |
| `set_runs(shape, paras)` | replace a whole text frame; `paras` = list of list-of-R |
| `set_para(shape, i, runs)` | replace one paragraph's runs (gotcha 3) |
| `textbox(slide, x,y,w,h, paras, algn, anchor, spc_pct)` | new text box |
| `rrect(slide, x,y,w,h, fill, line, lw, adj, shadow, fill_alpha, dash)` | rounded rectangle (a `shape()` wrapper) |
| `shape(slide, prst, x,y,w,h, ..., runs=, rot=, flipH=)` | **any** preset geometry, with text inside it. See gotcha 6 for `adj` |
| `text_in(el, paras, algn, anchor, ins)` | put text INSIDE an existing shape — one shape, not a box plus a label |
| `picture(slide, path, x,y, w=None, h=None)` | insert an image; give w or h alone to keep the aspect ratio |
| `measure(runs)` / `fits(runs, width_in)` | estimated drawn width in inches. **Advisory** |
| `wrap_ja(text, width_in, pt, font)` | break Japanese text with 禁則処理 |
| `contrast_ratio(fg, bg)` | WCAG ratio — check an accent before you commit to it |
| `arrow(slide, x1,y1, x2,y2, color, lw, dash, tip, both, back)` | **every arrow in every diagram.** Head always lands on `(x2,y2)`; the box and the flips are derived for you |
| `connector(slide, x,y,w,h, color, lw, dash, start, end, flipH, flipV)` | bare line, positioned by bounding box. `head=`/`tail=` still work but mean **start**/**end**, not "the pointy end" (gotcha 8) |
| `save_backup(path)` | timestamped copy — **call before batch edits** |
| `delete_slides(prs, positions)` | 1-based, handles drop_rel, descending (gotcha 4) |
| `move_slide(prs, frm, to)` | 1-based reorder |
| `slide_titles(prs)` | `[(pos, first line)]` — confirm before deleting |
| `load_profile(path)` | read a `deck-profile.json` |
| `use_defaults(text=, rule=, font=)` | point `R()`/`connector()` fallbacks at this palette. **Call first in every batch script** — on a light deck the built-in near-white default is invisible |
| `new_presentation(w, h, sz_type)` | zero-slide deck at the right size |
| `set_deck_size(prs, w, h, sz_type)` | size **and** the `sldSz type` python-pptx leaves stale (gotcha 8) |
| `blank_layout(prs)` | first placeholder-free layout |
| `add_slide(prs, layout=None, bg=None)` | append a slide, return it |
| `set_bg(obj, color)` / `clear_bg(obj)` | `<p:bg>` on a slide, layout or master |
| `apply_bg_all(prs, color)` | background every slide (retrofit) |
| `set_theme_colors(prs, {...})` | theme `clrScheme` accents only — for tables/charts PowerPoint styles itself |

## Emphasis, code and pictograms

Three modules exist because a deck built from `rrect` + `textbox` alone has no way to
say *this part matters more than that part*, and a reader cannot find the point.

### Emphasis inside a sentence

`R(..., b=True)`, `R(..., color=PAL['accent_red'])` and `R(..., hl='FFF0A8')` mark a span
**without splitting it into its own shape**. Bolding a whole text box makes a heading;
bolding two words inside a sentence is what actually directs the eye. `check_deck.py`
distinguishes the two and reports a slide whose every mark is a whole label.

### Syntax highlighting — `codehl.py`

```python
from codehl import highlight, code_block
code_block(slide, 1.0, 2.0, 7.0, 3.0, src, 'python', prof,
           line_numbers=True, mark_lines=[9, 10],
           mark_hl=PAL['highlight'], focus=True)
```

Applies the profile's `code_palette` (which existed for a long time with nothing to apply
it). `mark_lines` + `focus` keeps the marked lines at full strength and pushes the rest
**back by opacity, not by recolouring** — every line keeps its syntax colours, so the
fragment still reads as code while showing *which line the slide is about*. Tune the depth
with `dim_alpha` (default 0.55). Pass `dim_color` only when you deliberately want the
context flattened to a single colour: on a fragment where two lines of twenty are marked,
that is a grey wall with no highlighting left, and it fails R4-7.

`mark_hl` paints a highlighter band, so it comes from the deck palette
(`PAL['highlight']`) — a hard-coded light yellow is invisible on a dark deck.

Languages: python, java, kotlin, csharp, typescript/javascript, sql, json, yaml, xml/html,
bash, diff. **An unknown language falls back to `text` — no colour.** A wrong highlight
asserts a structure the code does not have, which is worse than no highlight.

### Pictograms — `pictogram.py`

```python
from pictogram import draw, names
draw(slide, 'warning', 1.0, 2.0, size=0.55,
     color=PAL['accent_red'], bg=PAL['bg'])
```

33 monochrome icons built from preset geometries: no font dependency, no licence, and the
colour comes from the palette so they always belong. `bg` is the knock-out colour — pass
what the icon actually sits on. `names()` lists the catalogue.

**Adding one: run `python pictogram.py out.pptx --profile slides/deck-profile.json` and
render EVERY page of it.** A preset that does not compose the way you expected is
invisible until you look (and see gotcha 6). The contact sheet sizes its grid from the
profile's geometry and paginates, so nothing is pushed off the slide unseen.
Check each figure's parts against each other, not just the silhouette: a head that is
not centred on its own body is the failure this catalogue has actually shipped.

### `check_deck.py` visual estimates

`--profile` also enables three advisory checks, all `MEDIUM`/`LOW` so they never change
the exit code:

| What | Why it matters |
| --- | --- |
| text estimated to overflow its own shape | the rubric's most common defect, previously findable only in the PNG |
| no in-sentence emphasis, or far too much | "everything is bold" reads the same as "nothing is bold" |
| character count over the profile's budget | the signal to convert prose into a diagram, or split the slide |

Tune them under `visual` in the deck profile; `--no-visual` turns them off.
**They are estimates.** They shrink the number of render cycles; they do not replace one.

### `--contrast` is advisory, not a gate

Text very often sits on top of a **separate** filled shape (badge chips, panels), which
cannot be resolved without z-order + geometry analysis. On a mature deck the naive
slide-background comparison produces heavy false positives — on the reference 43-slide
deck it flagged 26 legitimate badges. It is off by default and best used on a
**freshly generated** deck, where nothing overlaps yet.

The always-on background rule is the reliable one: no `<p:bg>` on slide, layout **or**
master means PowerPoint renders white, which this toolchain's defaults cannot survive.

Colours are RGB hex strings without `#` (`'34E2B0'`). Sizes are points. Positions are inches.

## Deck profile

Palette, fonts and geometry belong in the **project's** `slides/deck-profile.json`,
not in a script. `check_deck.py --profile` enforces the machine-checkable parts.
Schema: `techdeck-workflow/reference/deck-profile.md`.

Starting points live in `templates/presets/`: **`dark.json`** (the reference deck's
look) and **`light.json`**. A preset *is* a deck-profile, so `--preset dark` and
`--profile my.json` are the same code path — drop `presets/corporate.json` in to add one.

Accents cannot be shared between light and dark: `34E2B0` reads 11:1 on the dark bg and
about 1.5:1 on white. Each preset carries its own, verified against its own background.

## Comment extraction internals

Modern comments (PowerPoint 2018+) live in the package, not in the slide XML:

| Part | Role |
| --- | --- |
| `ppt/comments/modernComment_<hex>.xml` | the comments; one file per anchored slide |
| `ppt/slides/_rels/slideN.xml.rels` | maps a comment file to its slide number |
| `ppt/authors.xml` | `authorId` → display name |
| `<ac:spMk id="N">` inside a `<p188:cm>` | the anchor shape id; absent = slide-level |

`extract_comments.py` does all of this and resolves each anchor id to that shape's text,
so a reviewer's comment can be tied to what they were pointing at.
