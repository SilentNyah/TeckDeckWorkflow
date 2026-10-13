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


if __name__ == '__main__':
    unittest.main()
