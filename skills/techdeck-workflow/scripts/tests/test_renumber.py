# -*- coding: utf-8 -*-
"""Tests for renumber.py — run with  python -m unittest discover -s scripts/tests -t scripts

Modelled on the three real decks: 3-digit `Slide NNN` headings and references,
`Slides 008–015` ranges, `Slide 011・013` lists, bare `Previous slide: 002 ／ Next slide: 004`,
outline tables with the slide number in a `#` / `Slide` / `範囲` column, the Progress and
batch-ledger tables of review_state.md, carried-forward origins `Slide 006 由来`, the
`* 章: はじめに 1–2／第1章 3–4` line of the Deck structure note, and `p.N` page references
that mean deck pages in storyboard/outline/review_state but PDF pages in source_index.
"""
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import renumber  # noqa: E402


def write(path, text, eol='\n'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text.replace('\n', eol))


def read(path):
    with io.open(path, encoding='utf-8', newline='') as f:
        return f.read()


STORYBOARD = """# Storyboard

## Slide 001: 表紙

### Status

`APPROVED`

### Previous / Next slide relationship

* Previous slide: なし ／ Next slide: 002

### Sources

なし

## Slide 002: 二重派遣とは

### Status

`APPROVED`

### Body content

* 偽装請負（→ Slide 004）とは別の形。罰則は Slide 003 で扱う。詳細は Slides 003–004。
* 相談先は p.4。第1章の範囲。SRC-003 と DEC-003 と R6-4 と CF-26 は番号ではない。
* 旧 3 は付け替えの前の番号。3 枚目という言い方はしない。

### Previous / Next slide relationship

* Previous slide: 001 ／ Next slide: 003

## Slide 003: 違反するとどうなるか

### Status

`NOT_STARTED`

### Body content

* Slide 002・004 と揃える。

## Slide 004: 偽装請負

### Status

`NOT_STARTED`
"""

OUTLINE = """# Outline

## 2. 章構成

| 章 | 範囲 | 枚数 |
| --- | --- | --- |
| はじめに | 1–2 | 2 |
| 第1章 | 3–4 | 2 |

## 3. スライド一覧

| # | タイトル | 主な根拠 |
| --- | --- | --- |
| 1 | 表紙 | DEC-003 |
| 2 | 二重派遣とは | SRC-003 |
| 3 | 違反するとどうなるか | SRC-004 |
| 4 | 偽装請負 | SRC-003 |

| 章 | Slide | タイトル |
| --- | --- | --- |
| 第1章 | 3 | 違反するとどうなるか |
"""

REVIEW_STATE = """# Slide Review State

## Deck structure note

* 章: はじめに 1–2／第1章 3–4／付録 5–。
* バッチ: b001 1–2／b002 3–4。
* 番号の振り直しの履歴: なし。

## Current target

### バッチ b002（2026-10-06 ─ 第1章 3–4）

| Slide | Wave | Build | Review iter | Exit verdict | Open CRIT/HIGH | Deferred | 状態 |
| ----: | ---: | ----- | ----------: | ------------ | -------------: | -------- | ---- |
| 3 | 1 | — | 0 | — | — | — | `NOT_STARTED` |
| 4 | 1 | — | 0 | — | — | — | `NOT_STARTED` |

## Progress

| Slide (現位置) | Title | Status | Last updated | Notes |
| ----: | ----- | ----------- | ------------ | ------------ |
| 1 | 表紙 | `APPROVED` | 2026-10-06 | |
| 2 | 二重派遣とは | `APPROVED` | 2026-10-06 | p.4 を参照 |
| 3 | 違反するとどうなるか | `NOT_STARTED` | — | 旧 3 |
| 4 | 偽装請負 | `NOT_STARTED` | — | |

## Feedback carried forward

* 【b001 / Slide 002 由来 / R2-4 / 対象: 本文】→ Slide N を添える。
* 【b002 / Slide 003 由来 / R3-7 / 対象: 図】凡例を置く。
"""

SOURCE_INDEX = """# 出典一覧

## SRC-003: 労働者派遣法

* URL: https://example.invalid/a
* 本文 p.3 の第2段。Slide 003 で使う。
"""


class TmpProject(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='renumber-')
        self.sb = os.path.join(self.root, 'slides', 'storyboard.md')
        self.ol = os.path.join(self.root, 'slides', 'outline.md')
        self.st = os.path.join(self.root, 'slides', 'review_state.md')
        self.idx = os.path.join(self.root, 'sources', 'source_index.md')
        write(self.sb, STORYBOARD, eol='\r\n')     # CRLF on purpose
        write(self.ol, OUTLINE)
        write(self.st, REVIEW_STATE)
        write(self.idx, SOURCE_INDEX)
        os.makedirs(os.path.join(self.root, 'slides', 'reviews'))
        for n in (1, 2, 3, 4):
            write(os.path.join(self.root, 'slides', 'reviews', 'slide-%03d.md' % n), '# r\n')


class TestMapping(unittest.TestCase):
    def test_insert_after_shifts_only_later_slides(self):
        m = renumber.build_map([(2, 1)])
        self.assertEqual([m(n) for n in (1, 2, 3, 4)], [1, 2, 4, 5])

    def test_multiple_inserts_accumulate(self):
        m = renumber.build_map([(2, 1), (4, 2)])      # 'after' values are OLD numbers
        self.assertEqual([m(n) for n in (1, 2, 3, 4, 5)], [1, 2, 4, 5, 8])

    def test_explicit_map(self):
        m = renumber.build_map([], explicit={12: 13, 13: 14})
        self.assertEqual((m(11), m(12), m(13)), (11, 13, 14))

    def test_padding_follows_the_original_token(self):
        self.assertEqual(renumber.fmt_like('003', 4), '004')
        self.assertEqual(renumber.fmt_like('3', 4), '4')
        self.assertEqual(renumber.fmt_like('99', 100), '100')


class TestRewrite(TmpProject):
    def rewrite(self, text, pages=False, kind='deck'):
        m = renumber.build_map([(2, 1)])
        return renumber.rewrite_text(text, m, pages=pages, kind=kind)

    def test_storyboard_headings_refs_ranges_lists_prevnext(self):
        new, changes, review = self.rewrite(STORYBOARD)
        self.assertIn('## Slide 004: 違反するとどうなるか', new)
        self.assertIn('## Slide 005: 偽装請負', new)
        self.assertIn('## Slide 002: 二重派遣とは', new)            # unchanged
        self.assertIn('（→ Slide 005）', new)
        self.assertIn('罰則は Slide 004 で扱う', new)
        self.assertIn('詳細は Slides 004–005', new)
        self.assertIn('* Slide 002・005 と揃える', new)
        self.assertIn('* Previous slide: 001 ／ Next slide: 004', new)
        self.assertIn('* Previous slide: なし ／ Next slide: 002', new)

    def test_non_slide_numbers_are_untouched(self):
        new, _, review = self.rewrite(STORYBOARD)
        for token in ('SRC-003', 'DEC-003', 'R6-4', 'CF-26', '第1章', '旧 3 は', '3 枚目'):
            self.assertIn(token, new, token)
        # p.N is NOT rewritten without --pages, but it is reported for review
        self.assertIn('相談先は p.4。', new)
        self.assertTrue(any('p.4' in r[1] for r in review), review)
        self.assertTrue(any('旧 3' in r[1] for r in review), review)

    def test_pages_flag_rewrites_deck_page_refs_only_in_deck_files(self):
        new, _, _ = self.rewrite(STORYBOARD, pages=True)
        self.assertIn('相談先は p.5。', new)
        new_idx, changes, _ = self.rewrite(SOURCE_INDEX, pages=True, kind='index')
        self.assertIn('本文 p.3 の第2段', new_idx)                  # PDF page, never touched
        self.assertIn('Slide 004 で使う', new_idx)                  # slide ref still rewritten

    def test_outline_tables_by_column_header(self):
        new, _, _ = self.rewrite(OUTLINE)
        self.assertIn('| 第1章 | 4–5 | 2 |', new)
        self.assertIn('| はじめに | 1–2 | 2 |', new)
        self.assertIn('| 4 | 違反するとどうなるか | SRC-004 |', new)
        self.assertIn('| 5 | 偽装請負 | SRC-003 |', new)
        self.assertIn('| 第1章 | 4 | 違反するとどうなるか |', new)
        self.assertIn('| 2 | 二重派遣とは | SRC-003 |', new)
        self.assertNotIn('| 1–2 | 3 |', new)                        # 枚数 column untouched

    def test_review_state_tables_cf_origins_and_structure_note(self):
        new, _, _ = self.rewrite(REVIEW_STATE)
        self.assertIn('| 4 | 1 | — | 0 | — | — | — | `NOT_STARTED` |', new)
        self.assertIn('| 5 | 1 | — | 0 | — | — | — | `NOT_STARTED` |', new)
        self.assertIn('| 4 | 違反するとどうなるか | `NOT_STARTED` | — | 旧 3 |', new)
        self.assertIn('【b002 / Slide 004 由来 / R3-7 / 対象: 図】', new)
        self.assertIn('【b001 / Slide 002 由来 / R2-4 / 対象: 本文】', new)
        self.assertIn('* 章: はじめに 1–2／第1章 4–5／付録 6–。', new)
        self.assertIn('* バッチ: b001 1–2／b002 4–5。', new)
        self.assertIn('第1章 4–5）', new)                           # batch heading range

    def test_approved_impact_is_listed_separately(self):
        plan = renumber.plan(self.root, [(2, 1)], pages=False)
        approved = plan.approved_slides
        self.assertEqual(approved, {1, 2})
        # slide 2 is approved and its storyboard section contains references that change
        hits = [h for h in plan.approved_hits if h.slide == 2]
        self.assertTrue(hits, plan.approved_hits)
        self.assertTrue(all(h.path.endswith('storyboard.md') or h.path.endswith('review_state.md')
                            for h in hits))
        # no approved slide changes its own number here
        self.assertEqual(plan.approved_renumbered, [])
        plan2 = renumber.plan(self.root, [(1, 1)], pages=False)
        self.assertEqual(plan2.approved_renumbered, [(2, 3)])


class TestApply(TmpProject):
    def test_dry_run_writes_nothing(self):
        before = {p: read(p) for p in (self.sb, self.ol, self.st, self.idx)}
        plan = renumber.plan(self.root, [(2, 1)], pages=False)
        buf = io.StringIO()
        renumber.report(plan, out=buf)             # prints, must not write
        self.assertIn('renumber plan', buf.getvalue())
        self.assertNotIn('applied', buf.getvalue())   # report never writes, never claims to
        for p, t in before.items():
            self.assertEqual(read(p), t)

    def test_apply_preserves_crlf_and_skips_history_files(self):
        plan = renumber.plan(self.root, [(2, 1)], pages=False)
        renumber.apply(plan)
        sb = read(self.sb)
        self.assertIn('\r\n', sb)
        self.assertEqual(sb.count('\n'), sb.count('\r\n'))
        self.assertIn('## Slide 004: 違反するとどうなるか', sb)
        self.assertNotIn('\r', read(self.ol))
        # source_index is not a default target (history / PDF pages)
        self.assertIn('Slide 003 で使う', read(self.idx))

    def test_rename_reviews_descending_without_collision(self):
        plan = renumber.plan(self.root, [(2, 1)], pages=False, rename_reviews=True)
        renumber.apply(plan)
        names = sorted(os.listdir(os.path.join(self.root, 'slides', 'reviews')))
        self.assertEqual(names, ['slide-001.md', 'slide-002.md', 'slide-004.md', 'slide-005.md'])


if __name__ == '__main__':
    unittest.main()
