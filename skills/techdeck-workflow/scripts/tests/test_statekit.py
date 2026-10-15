# -*- coding: utf-8 -*-
"""Tests for statekit.py — run with  python -m unittest discover -s scripts/tests -t scripts

Every case is a failure that actually happened while writing state files by hand
(reflection note A-1, A-2, F-2, J-1, S): the fix landing in the wrong section,
`grep -c` passing while the placement was wrong, CRLF turned into LF, an ID
numbered twice, a table row "added" but not inside the table.
"""
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import statekit  # noqa: E402


def write(path, text, eol='\n'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text.replace('\n', eol))


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


SOURCE_INDEX = """# 出典一覧

---

## SRC-003: 労働者派遣法

* URL: https://laws.e-gov.go.jp/law/360AC0000000088
* Checked: 2026-09-01

### Key technical points

* 二重派遣は労働者供給に当たる。

---

## SRC-004: 職業安定法

* URL: https://laws.e-gov.go.jp/law/322AC0000000141/
* Checked: 2026-09-01

### Key technical points

* 44条。

### Applicable topics

* 第2章

### Update history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-09-01 | 初回登録 | |

---

## SRC-005: 同じ法令の別 URL 表記

* URL: https://laws.e-gov.go.jp/law/322AC0000000141#Mp-At_44
* Checked: 2026-09-02

### Key technical points

* 重複登録の疑い。
"""

STORYBOARD = """# Storyboard

## Slide 002: 二重派遣とは

### Status

`AWAITING_REVIEW`

### Key message

行1: 二重派遣は **労働者供給** に当たる。

### Sources

| Source ID | Used for | 依拠する逐語 |
| --------- | -------- | ------------ |
| `SRC-003` | 定義 | #1 |

### Known risks

*

## Slide 003: 違反するとどうなるか

### Status

`NOT_STARTED`

```text
### Known risks   ← これは例であり見出しではない
## Slide 999: 偽の見出し
```

### Sources

| Source ID | Used for | 依拠する逐語 |
| --------- | -------- | ------------ |
| `SRC-004` | 罰則 | #2 |

### Known risks

*
"""

REVIEW_STATE = """# Slide Review State

## Rules

* 状態はスライド単位で管理する。

## Current target

### バッチ b002（2026-10-06 ─ 第3章 11–19）

| Slide | Wave | Build | Review iter | Exit verdict | Open CRIT/HIGH | Deferred | 状態 |
| ----: | ---: | ----- | ----------: | ------------ | -------------: | -------- | ---- |
| 11 | 1 | done | 1 | `PASS` | 0 | — | `AWAITING_REVIEW` |
| 12 | 1 | done | 2 | `PASS_WITH_MINOR_FIXES` | 0 | FINDING-004 | `AWAITING_REVIEW` |

### バッチ b001（2026-10-06 ─ 第1章 1–10）── 承認済み

| Slide | Wave | Build | Review iter | Exit verdict | Open CRIT/HIGH | Deferred | 状態 |
| ----: | ---: | ----- | ----------: | ------------ | -------------: | -------- | ---- |
| 1 | 0 | done | 1 | `PASS` | 0 | — | `APPROVED` |
| 12 | 1 | done | 1 | `PASS` | 0 | — | `APPROVED` |

## Progress

| Slide (現位置) | Title | Status | Last updated | Notes |
| ----: | ----- | ----------- | ------------ | ------------ |
| 1 | 表紙 | `APPROVED` | 2026-10-06 | |
| ~~7~~ | ~~旧 7~~ | `CUT` | 2026-10-06 | DEC-014 |
| 12 | 罰則 | `AWAITING_REVIEW` | 2026-10-06 | rev2 |

## Feedback carried forward

* 【b001 / Slide 006 由来 / R3-7 / 対象: 図】凡例を置く。

## Approved slide change requests

| ID | Slide | 出所 | 内容 | 影響 | 処理時期 | 状態 |
| --- | ---: | --- | --- | --- | --- | --- |
| ASC-001 | 7 | b002 R6 | 限定語 | 字数 +8 | Phase 4 | `OPEN` |
"""


class TmpProject(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='statekit-')
        self.idx = os.path.join(self.root, 'sources', 'source_index.md')
        self.sb = os.path.join(self.root, 'slides', 'storyboard.md')
        self.st = os.path.join(self.root, 'slides', 'review_state.md')
        write(self.idx, SOURCE_INDEX, eol='\r\n')      # CRLF on purpose
        write(self.sb, STORYBOARD)
        write(self.st, REVIEW_STATE)
        write(os.path.join(self.root, 'notes', 'decisions.md'),
              "# 判断\n\n## DEC-007: x\n\n### Source IDs\n\n* SRC-009（参照だけ。未登録）\n")


class TestNextId(TmpProject):
    def test_next_id_counts_references_in_all_files(self):
        # SRC-005 is the highest definition but DEC-007 references SRC-009:
        # the next id must be past every mention, not just every heading.
        self.assertEqual(statekit.next_id(self.root, 'SRC'), 'SRC-010')

    def test_next_id_fresh_series(self):
        self.assertEqual(statekit.next_id(self.root, 'ASC'), 'ASC-002')
        self.assertEqual(statekit.next_id(self.root, 'VIS'), 'VIS-001')

    def test_check_id_reports_definitions_and_references(self):
        defs, refs = statekit.check_id(self.root, 'SRC-004')
        self.assertEqual(defs, 1)
        self.assertGreaterEqual(refs, 1)      # the storyboard Sources row
        defs, refs = statekit.check_id(self.root, 'SRC-024')
        self.assertEqual((defs, refs), (0, 0))


class TestDupes(TmpProject):
    def test_same_url_modulo_slash_and_fragment_is_a_dupe(self):
        with io.open(self.idx, encoding='utf-8') as f:
            groups = statekit.find_dupes(f.read())
        self.assertEqual(len(groups), 1)
        ids = sorted(groups[0][1])
        self.assertEqual(ids, ['SRC-004', 'SRC-005'])

    def test_distinct_urls_are_not_dupes(self):
        text = SOURCE_INDEX.replace('322AC0000000141#Mp-At_44', '999AC0000000999')
        self.assertEqual(statekit.find_dupes(text), [])

    def test_non_url_values_are_ignored(self):
        # Real indexes carry "* URL: 未確認", "* URL: *（複数）", "* URL: ローカルファイル":
        # those must not be reported as one big duplicate group.
        text = (SOURCE_INDEX
                .replace('https://laws.e-gov.go.jp/law/322AC0000000141/', '未確認')
                .replace('https://laws.e-gov.go.jp/law/322AC0000000141#Mp-At_44', '*（複数の通達）')
                .replace('https://laws.e-gov.go.jp/law/360AC0000000088', 'ローカルファイル'))
        self.assertEqual(statekit.find_dupes(text), [])


class TestSrcAppend(TmpProject):
    def test_appends_inside_the_named_section_not_the_next_one(self):
        # A-2: SRC-003 has no "### Update history"; the naive search found
        # SRC-004's and inserted there while grep -c still said 3.
        with io.open(self.idx, encoding='utf-8', newline='') as f:
            text = f.read().replace('\r\n', '\n')
        new, line = statekit.src_append(
            text, 'SRC-003', '| 2026-10-13 | 逐語を追記 | C-2 |', section='Update history')
        i003 = new.index('## SRC-003')
        i004 = new.index('## SRC-004')
        ins = new.index('| 2026-10-13 | 逐語を追記 | C-2 |')
        self.assertTrue(i003 < ins < i004, 'inserted outside SRC-003')
        # the subsection was created inside SRC-003, before its --- separator
        sec003 = new[i003:i004]
        self.assertIn('### Update history', sec003)
        self.assertLess(sec003.index('### Update history'), sec003.rindex('---'))
        self.assertEqual(new[:ins].count('\n') + 1, line)

    def test_appends_to_existing_subsection_at_its_end(self):
        text = SOURCE_INDEX
        new, _ = statekit.src_append(text, 'SRC-004', '| 2026-10-13 | 再確認 | |',
                                     section='Update history')
        sec = new[new.index('## SRC-004'):new.index('## SRC-005')]
        hist = sec[sec.index('### Update history'):]
        self.assertLess(hist.index('| 2026-09-01 | 初回登録 | |'), hist.index('| 2026-10-13 | 再確認 | |'))
        self.assertEqual(new.count('### Update history'), 1)   # reused, none created elsewhere

    def test_unknown_src_refuses(self):
        with self.assertRaises(statekit.StateError):
            statekit.src_append(SOURCE_INDEX, 'SRC-099', 'x')

    def test_file_level_api_preserves_crlf(self):
        statekit.src_append_file(self.idx, 'SRC-003', '| 2026-10-13 | 逐語 | |', section='Update history')
        b = read_bytes(self.idx)
        self.assertIn(b'\r\n', b)
        self.assertEqual(b.count(b'\n'), b.count(b'\r\n'), 'mixed line endings')


class TestStoryboard(TmpProject):
    def test_set_creates_missing_section_inside_the_right_slide(self):
        new, line = statekit.storyboard_set(STORYBOARD, '003', 'Current spec',
                                            '* キーメッセージ: 罰則は個人にも及ぶ')
        s2 = new.index('## Slide 002')
        s3 = new.index('## Slide 003')
        ins = new.index('* キーメッセージ: 罰則は個人にも及ぶ')
        self.assertGreater(ins, s3)
        self.assertNotIn('Current spec', new[s2:s3])
        self.assertEqual(new[:ins].count('\n') + 1, line)

    def test_set_replaces_body_of_existing_section(self):
        new, _ = statekit.storyboard_set(STORYBOARD, '002', 'Key message',
                                         '行1: 二重派遣は **労働者供給**。\n行2: 罰則は **個人にも**。')
        sec = new[new.index('## Slide 002'):new.index('## Slide 003')]
        self.assertNotIn('に当たる。', sec)
        self.assertIn('行2: 罰則は **個人にも**。', sec)
        self.assertEqual(sec.count('### Key message'), 1)

    def test_headings_inside_code_fences_are_ignored(self):
        # The fence in Slide 003 contains "## Slide 999" and "### Known risks".
        new, _ = statekit.storyboard_set(STORYBOARD, '003', 'Known risks', '* 本物の欄に書けた')
        sec = new[new.index('## Slide 003'):]
        fence = sec[sec.index('```text'):sec.index('```', sec.index('```text') + 3)]
        self.assertNotIn('本物の欄に書けた', fence)
        self.assertIn('* 本物の欄に書けた', sec)
        with self.assertRaises(statekit.StateError):
            statekit.storyboard_set(STORYBOARD, '999', 'Status', 'x')

    def test_sources_row_lands_in_the_table_of_that_slide(self):
        new, line = statekit.sources_row(STORYBOARD, '002', '| `SRC-004` | 罰則の条 | #2 |')
        sec = new[new.index('## Slide 002'):new.index('## Slide 003')]
        tbl_start = sec.index('| Source ID |')
        tbl_end = sec.index('### Known risks')
        self.assertIn('| `SRC-004` | 罰則の条 | #2 |', sec[tbl_start:tbl_end])
        # directly after the last existing row, no blank line in between
        self.assertIn('| `SRC-003` | 定義 | #1 |\n| `SRC-004` | 罰則の条 | #2 |', new)

    def test_sources_row_refuses_without_table(self):
        text = STORYBOARD.replace('| `SRC-003` | 定義 | #1 |\n', '').replace(
            '| Source ID | Used for | 依拠する逐語 |\n| --------- | -------- | ------------ |\n', 'なし\n', 1)
        with self.assertRaises(statekit.StateError):
            statekit.sources_row(text, '002', '| `SRC-004` | x | |')


class TestLedgerAndProgress(TmpProject):
    def test_ledger_set_updates_only_the_named_batch(self):
        # Slide 12 appears in b002 AND in b001's table; only b002 may change.
        new, line = statekit.ledger_set(REVIEW_STATE, 'b002', 12,
                                        {'Exit verdict': '`PASS`', 'Review iter': '3', '状態': '`AWAITING_REVIEW`'})
        b002 = new[new.index('### バッチ b002'):new.index('### バッチ b001')]
        b001 = new[new.index('### バッチ b001'):new.index('## Progress')]
        self.assertIn('| 12 | 1 | done | 3 | `PASS` | 0 | FINDING-004 | `AWAITING_REVIEW` |', b002)
        self.assertIn('| 12 | 1 | done | 1 | `PASS` | 0 | — | `APPROVED` |', b001)

    def test_ledger_set_unknown_column_or_slide_refuses(self):
        with self.assertRaises(statekit.StateError):
            statekit.ledger_set(REVIEW_STATE, 'b002', 12, {'Nope': 'x'})
        with self.assertRaises(statekit.StateError):
            statekit.ledger_set(REVIEW_STATE, 'b002', 99, {'Build': 'x'})

    def test_progress_set_status_date_notes(self):
        new, _ = statekit.progress_set(REVIEW_STATE, 12, status='APPROVED', date='2026-10-13',
                                       append_notes='ユーザー承認')
        self.assertIn('| 12 | 罰則 | `APPROVED` | 2026-10-13 | rev2。ユーザー承認 |', new)
        # the ledger table row for slide 12 is untouched by progress_set
        self.assertIn('| 12 | 1 | done | 2 | `PASS_WITH_MINOR_FIXES` | 0 | FINDING-004 | `AWAITING_REVIEW` |', new)

    def test_progress_set_matches_struck_rows(self):
        new, _ = statekit.progress_set(REVIEW_STATE, 7, notes='DEC-014。storyboard に温存')
        self.assertIn('| ~~7~~ | ~~旧 7~~ | `CUT` | 2026-10-06 | DEC-014。storyboard に温存 |', new)

    def test_asc_add_appends_row_with_next_id(self):
        new, line = statekit.asc_add(REVIEW_STATE, slide=13, source='b002 R6', content='凡例',
                                     impact='高さ +0.2in', when='Phase 4')
        self.assertIn('| ASC-002 | 13 | b002 R6 | 凡例 | 高さ +0.2in | Phase 4 | `OPEN` |', new)
        self.assertLess(new.index('| ASC-001 |'), new.index('| ASC-002 |'))


class TestReviewAppend(TmpProject):
    def test_appends_under_heading_creating_it_when_missing(self):
        text = "# Review Report\n\n## Findings\n\n### FINDING-001: x\n\n* Severity: `LOW`\n"
        new, _ = statekit.review_append(text, 'R6 notes', '* 凡例の頭に「凡例:」が無い')
        self.assertTrue(new.rstrip().endswith('## R6 notes\n\n* 凡例の頭に「凡例:」が無い'))
        new2, _ = statekit.review_append(new, 'R6 notes', '* 2件目')
        self.assertEqual(new2.count('## R6 notes'), 1)
        self.assertLess(new2.index('* 凡例の頭'), new2.index('* 2件目'))


class TestCli(TmpProject):
    def test_cli_next_id_and_dupes_exit_codes(self):
        import subprocess
        py = sys.executable
        kit = os.path.join(os.path.dirname(HERE), 'statekit.py')
        out = subprocess.run([py, '-X', 'utf8', kit, 'next-id', 'SRC', '--root', self.root],
                             capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), 'SRC-010')
        out = subprocess.run([py, '-X', 'utf8', kit, 'dupes', self.idx],
                             capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(out.returncode, 1)
        self.assertIn('SRC-004', out.stdout)
        self.assertIn('SRC-005', out.stdout)



# --------------------------------------------------------------------------- read side (show-*)
# Why these exist: in the 2026-10-15 benchmark an orchestrator turn made 28–40 tool calls, most
# of them partial reads of review_state.md / storyboard.md and re-reads of statekit.py because
# --help crashed under cp932. One call per turn is the target.

CF_MIXED = """# Slide Review State

## Rules

* 状態はスライド単位で管理する。
* エージェント自身の判断で `APPROVED` にしない。

## Current target

### バッチ b005（2026-10-13 ─ 第5章 Slide 032–035）

* Batch ID: `b005`

| Slide | Wave | Build | Review iter | Exit verdict | Open CRIT/HIGH | Deferred | 状態 |
| ----: | ---: | ----- | ----------: | ------------ | -------------: | -------- | ---- |
| 032 | 0 | done | 2 | `PASS` | 0 | — | `AWAITING_REVIEW` |
| 033 | 1 | done | 1 | `REVISION_REQUIRED` | 2 | — | `DRAFTING` |

### バッチ b004（2026-10-06 ─ 第4章）── 承認済み

| Slide | Wave | Build | Review iter | Exit verdict | Open CRIT/HIGH | Deferred | 状態 |
| ----: | ---: | ----- | ----------: | ------------ | -------------: | -------- | ---- |
| 030 | 1 | done | 2 | `PASS` | 0 | — | `APPROVED` |

## Progress

| Slide (現位置) | Title | Status | Last updated | Notes |
| ----: | ----- | ----------- | ------------ | ------------ |
| 30 | ViewModel | `APPROVED` | 2026-09-20 | b004 |
| 33 | コード編 | `DRAFTING` | 2026-10-13 | b005 iter1。ASC-005 を参照 |

## Feedback carried forward

今後の全スライドに効く横断ルール。

* **出典のない数値を書かない**（`DEC-008`）。テスト比率、saved state のサイズ上限。
* **図は公式の現物を貼らず、構造の型だけ翻案する**（`DEC-007`）。
  適用は Slide 024・058 のみ。

---

### バッチ b001 のパイロット（Slide 008）で追加された横断ルール

**CF-01 層の色は3色に固定する**（`DEC-013`。レビュー `FINDING-008-01`、`HIGH`）

| 層 | 色 |
| --- | --- |
| UI 層 | `accent_green` |

マスター図・凡例・表・章 kicker のすべてでこの3色を使う。
理由: ダークテーマでは「濃い＝土台」が成立しない。

**CF-02 凡例より前に矢印を使うスライドには前方参照を1行置く**（`FINDING-008-02`、`HIGH`）

線種の凡例は Slide 013 で初めて出る。

> 矢印が何を意味するかは Slide 011 で説明する。

* 【b003 / Slide 031 由来 / R3-6 / 対象: 図】矢印ラベルには必ず動作主体を書く
  （「join」ではなく「親が子を join」）。
* 【b003 / Slide 033 由来 / R1-C-4 / 対象: 用語】`CoroutineScope` は常にコードフォント。
* 【r002 / ユーザー指示 / 対象: コード】`mark_lines` を必ず付ける。

## Pending decisions

なし。

## Approved slide change requests

なし。
"""

STORYBOARD_033 = """# Storyboard

## Slide 032: 概念編

### Status

`AWAITING_REVIEW`

## Slide 033: 親は子の完了を暗黙に待つ（コード編）

### Status

`DRAFTING`

### Current spec

* キーメッセージ: 親スコープは、子コルーチンが終わるまで完了しない。

### Key message

行1: 親は **子の完了** を暗黙に待つ。

### Diagram

#### Diagram type

タイムライン（概念図）。

### Code

なし。

### Sources

| Source ID | Used for | 依拠する逐語 |
| --------- | -------- | ------------ |
| `SRC-039` | 機構 | #1 |

### Known risks

* 5 秒の意味を推測で書かない。

## Slide 034: 次

### Status

`NOT_STARTED`
"""


class TestCfRules(unittest.TestCase):
    def test_one_line_per_rule_and_count_is_preserved(self):
        rules = statekit.cf_rules(CF_MIXED)
        self.assertEqual(len(rules), 7)          # 2 top bullets + CF-01 + CF-02 + 3 tagged bullets
        for r in rules:
            self.assertNotIn('\n', r.text)

    def test_schema_bullet_keeps_tag_and_joins_continuation(self):
        r = [r for r in statekit.cf_rules(CF_MIXED) if '動作主体' in r.text][0]
        self.assertEqual(r.tags, ['図'])
        self.assertIn('親が子を join', r.text)

    def test_bold_heading_rule_drops_its_explanation_and_is_untagged(self):
        r = [r for r in statekit.cf_rules(CF_MIXED) if r.id == 'CF-01'][0]
        self.assertTrue(r.text.startswith('CF-01 層の色は3色に固定する'))
        self.assertNotIn('マスター図', r.text)
        self.assertEqual(r.tags, [])

    def test_filter_drops_only_rules_whose_tag_is_excluded(self):
        rules = statekit.cf_rules(CF_MIXED)
        kept = statekit.cf_filter(rules, exclude_tags=['コード'])
        self.assertEqual(len(kept), 6)
        self.assertFalse(any('mark_lines' in r.text for r in kept))
        self.assertTrue(any(r.id == 'CF-01' for r in kept))      # untagged always kept

    def test_show_cf_keeps_every_rule_and_drops_explanations(self):
        out = statekit.show_cf(CF_MIXED)
        self.assertIn('7 of 7 rules', out)
        self.assertEqual(sum(1 for l in out.splitlines() if l.startswith('* ')), 7)
        for dropped in ('マスター図', '理由:', '| UI 層', '矢印が何を意味するかは', '線種の凡例は Slide 013'):
            self.assertNotIn(dropped, out)


class TestShow(unittest.TestCase):
    def test_show_progress_prints_only_the_slide_row(self):
        out = statekit.show_progress(CF_MIXED, 33)
        self.assertIn('| 33 |', out)
        self.assertIn('DRAFTING', out)
        self.assertNotIn('| 30 |', out)

    def test_show_ledger_prints_batch_heading_and_the_slide_rows(self):
        out = statekit.show_ledger(CF_MIXED, slide=33)
        self.assertIn('### バッチ b005', out)
        self.assertIn('| 033 |', out)
        self.assertNotIn('| 032 |', out)
        self.assertNotIn('b004', out)

    def test_show_slide_whole_section_by_default(self):
        out = statekit.show_slide(STORYBOARD_033, 33)
        self.assertTrue(out.startswith('## Slide 033'))
        self.assertIn('### Known risks', out)
        self.assertNotIn('## Slide 034', out)

    def test_show_slide_sections_subset(self):
        out = statekit.show_slide(STORYBOARD_033, 33, sections=['Current spec', 'Sources'])
        self.assertIn('### Current spec', out)
        self.assertIn('SRC-039', out)
        self.assertNotIn('### Known risks', out)

    def test_slide_tags_derive_from_diagram_and_code_sections(self):
        self.assertEqual(statekit.slide_excluded_tags(STORYBOARD_033, 33), ['コード'])   # Diagram present, Code 'なし'

    def test_show_turn_composes_rules_progress_ledger_cf_and_slide(self):
        out = statekit.show_turn(CF_MIXED, STORYBOARD_033, 33)
        for needle in ('## Rules', '| 33 |', '### バッチ b005', 'CF-01', '動作主体', '### Current spec', '6 of 7 rules'):
            self.assertIn(needle, out)
        self.assertNotIn('mark_lines', out)   # コード rule dropped: the slide has no code


class TestAscNumbering(unittest.TestCase):
    def test_numbers_from_the_table_not_from_mentions_elsewhere(self):
        text = REVIEW_STATE.replace('| rev2 |', '| rev2。ASC-009 参照 |')
        new, _ = statekit.asc_add(text, slide=13, source='b002 R6', content='凡例', impact='', when='Phase 4')
        self.assertIn('| ASC-002 | 13 |', new)

    def test_first_row_replaces_the_placeholder_line(self):
        new, _ = statekit.asc_add(CF_MIXED, slide=33, source='b005 R6', content='凡例', impact='', when='Phase 4')
        sec = statekit.extract_section(new, 'Approved slide change requests')
        self.assertIn('| ASC-001 | 33 |', sec)
        self.assertNotIn('なし。', sec)


class TestReviewAppendFile(unittest.TestCase):
    def test_creates_the_record_file_when_missing(self):
        root = tempfile.mkdtemp(prefix='statekit-')
        path = os.path.join(root, 'slides', 'reviews', 'slide-033.md')
        line = statekit.review_append_file(path, 'R6 notes', '* 凡例の頭に「凡例:」が無い')
        with io.open(path, encoding='utf-8') as f:
            s = f.read()
        self.assertTrue(s.startswith('# Review Report'))
        self.assertIn('## R6 notes', s)
        self.assertIn('* 凡例の頭', s)
        self.assertGreater(line, 1)


class TestCliHelp(unittest.TestCase):
    def test_help_prints_when_stdout_is_cp932(self):
        buf = io.BytesIO()
        wrapper = io.TextIOWrapper(buf, encoding='cp932')   # keep a reference: GC would close buf
        saved = sys.stdout
        sys.stdout = wrapper
        try:
            with self.assertRaises(SystemExit) as cm:
                statekit.main(['--help'])
            wrapper.flush()
            data = buf.getvalue()
        finally:
            sys.stdout = saved
            wrapper.detach()
        self.assertEqual(cm.exception.code, 0)
        self.assertIn(b'show-turn', data)


if __name__ == '__main__':
    unittest.main()
