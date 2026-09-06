# -*- coding: utf-8 -*-
"""Scaffold a technical-deck project so Phase 1 can start.

Creates the directory tree, the state files Phase 1 expects to find, TASK.md,
and (via pptx-toolkit's new_deck.py) a correctly-sized deck with a background.

    python init_project.py                       # cwd, dark preset
    python init_project.py path/to/proj --preset light --name "Some Topic"
    python init_project.py --dry-run
    python init_project.py --git                 # opt-in; never commits

NEVER overwrites. Existing paths are reported as `skipped` and left alone, so
re-running is a safe way to repair a half-built tree. Exit 0 unless something
genuinely failed.

Deliberately does NOT create slides/outline.md, storyboard.md or
review_state.md: those are Phase 2 outputs, and an empty outline.md would make
SKILL.md's phase inference jump a brand-new project straight to Phase 2.
"""
import argparse
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
SCAFFOLD = os.path.join(SKILL_DIR, 'templates', 'scaffold')
TEMPLATES = os.path.join(SKILL_DIR, 'templates')

DIRS = [
    'notes', 'sources', 'sources/images', 'examples',
    'assets/diagrams', 'assets/screenshots', 'assets/templates',
    'slides', 'slides/reviews', 'slides/review-input', 'slides/review-output',
    'output/pptx', 'output/pdf',
]
# tracked-but-empty dirs get a .gitkeep; output/pdf is gitignored so it doesn't
KEEP = ['examples', 'sources/images',
        'assets/diagrams', 'assets/screenshots', 'assets/templates',
        'slides/reviews', 'slides/review-input', 'slides/review-output', 'output/pptx']


def stub_sources():
    return """# 出典一覧

Source ID は `SRC-001` のように連番で付与する。
同じ URL を再調査した場合は、新規 ID を作らず既存項目の `### Update history` へ追記する。

項目の書式は `templates/source-entry.md` に従う。

---
"""


def stub_findings():
    return """# 調査結果

技術トピック単位でまとめる（情報源単位ではない）。
**確認済みの事実 / 推論 / 未確認** を必ず区別して書く。
見出しに根拠の `SRC-NNN` を併記する。

詳細な項目定義は `templates/finding-entry.md`。

---
"""


def stub_open_questions():
    return """# 未解決の問い

## ユーザー判断が必要な点

<!-- 番号付きリスト。技術的に決められず、ユーザーの意向が要るもの -->

## 追加調査候補

<!-- 調査すれば決まるもの -->

---

<!--
以降、ID を振った項目を積む。書式:

## OQ-001: <問い>

### Question
### Why it matters
### Current information
### Required investigation
### Status          OPEN / DEFERRED / RESOLVED
### Resolution      解決後に追記
-->
"""


def stub_visual_references():
    return """# 視覚参照

Phase 1 で見た図・図解・画像の記録。ID は `VIS-001` のように連番。

**記録するのは画像ではなく「構造の型」である。**
何を上手く表しているのかを言語化できないエントリは、書く意味がない。

画像そのものは `sources/images/` に保存する。
**既定ではデッキに現物を貼らない** ─ 型だけ翻案して自分で描く。
現物が必要なら `OQ-NNN` を立ててユーザーの判断を仰ぐ。

項目の書式は `templates/visual-reference-entry.md` に従う。
手順は `workflows/phase1-research.md` の Visual reference research。

---
"""


def stub_glossary():
    return """# 用語集

| Term | Full name | Definition | Related terms | Source |
| --- | --- | --- | --- | --- |

## Writing rules

* 資料全体で表記を統一する。略語は初出で展開する。
* 定義は一次情報に基づき、根拠の `SRC-NNN` を Source 欄に書く。
* 一般仕様と特定実装で意味が異なる用語は、その旨を Definition に明記する。
"""


def stub_decisions(name, preset, w, h, lang):
    d = datetime.date.today().isoformat()
    return """# 判断記録

判断とその理由を積む。書式は `reference/state-schema.md` を参照。
過去の方針を反転する場合も元の項目は書き換えず、新しい項目に「DEC-NNN の反転」と明記する。

---

## DEC-001: プロジェクト初期化

### Date

%s

### Status

`ACCEPTED`

### Context

「%s」の技術資料を作るため、`techdeck-workflow` スキルの Phase 0 で作業ツリーを初期化した。

### Decision

* 配色プリセット: `%s`
* スライド寸法: %.3f x %.3f in
* 資料の言語: `%s`
* 手順・テンプレートはスキル側を参照し、リポジトリには複製しない
* `slides/outline.md` / `storyboard.md` / `review_state.md` は Phase 2 の成果物なので
  この時点では作らない

### Reason

見た目の設定を `slides/deck-profile.json` の1箇所に集約し、案件固有の値と
汎用の手順を分離するため。

### Consequences

* 配色を変える場合は `deck-profile.json` を編集し、`check_deck.py --profile` で検証する。
* `slides/deck.pptx` の1枚目は Phase 0 が置いた仮のタイトルスライドであり、
  Phase 3 で storyboard に基づいて作り直す。

### Related files

* `slides/deck-profile.json`
* `slides/deck.pptx`
* `TASK.md`
""" % (d, name, preset, w, h, lang)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('dir', nargs='?', default='.')
    ap.add_argument('--preset', default='dark')
    ap.add_argument('--profile')
    ap.add_argument('--name')
    ap.add_argument('--language', default='ja')
    ap.add_argument('--git', action='store_true', help='run `git init` (never commits)')
    ap.add_argument('--no-deck', action='store_true')
    ap.add_argument('--pptx-toolkit', help='dir holding pptx-toolkit/scripts')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    root = os.path.abspath(a.dir)
    name = a.name or os.path.basename(root) or 'Technical Deck'
    tag = '[dry-run] ' if a.dry_run else ''
    made, skipped = [], []

    def mkdir(rel):
        p = os.path.join(root, rel)
        if os.path.isdir(p):
            skipped.append(rel + '/')
            return
        made.append(rel + '/')
        if not a.dry_run:
            os.makedirs(p, exist_ok=True)

    def write(rel, content):
        p = os.path.join(root, rel)
        if os.path.exists(p):
            skipped.append(rel)
            return False
        made.append(rel)
        if not a.dry_run:
            os.makedirs(os.path.dirname(p) or root, exist_ok=True)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(content)
        return True

    def from_scaffold(src, dst, subs=None):
        path = os.path.join(SCAFFOLD, src)
        if not os.path.exists(path):
            print('  !! missing scaffold file: %s' % path)
            return False
        with open(path, encoding='utf-8') as f:
            body = f.read()
        for k, v in (subs or {}).items():
            body = body.replace(k, v)
        return write(dst, body)

    if not a.dry_run:
        os.makedirs(root, exist_ok=True)

    for d in DIRS:
        mkdir(d)
    for d in KEEP:
        write(os.path.join(d, '.gitkeep').replace('\\', '/'), '')

    subs = {'{{SKILL_DIR}}': SKILL_DIR.replace('\\', '/'),
            '{{PROJECT_NAME}}': name}
    from_scaffold('AGENTS.md', 'AGENTS.md', subs)
    from_scaffold('README.md', 'README.md', subs)
    from_scaffold('gitignore', '.gitignore')
    from_scaffold('slides-AGENTS.md', 'slides/AGENTS.md', subs)
    from_scaffold('examples-AGENTS.md', 'examples/AGENTS.md', subs)

    task = os.path.join(TEMPLATES, 'task.md')
    if os.path.exists(task):
        with open(task, encoding='utf-8') as f:
            body = f.read()
        body = body.replace('## Goal\n\n<!-- 何を完成させるか。1〜2行。 -->',
                            '## Goal\n\n%s に関する技術資料を完成させること。' % name)
        write('TASK.md', body)

    write('sources/source_index.md', stub_sources())
    write('notes/findings.md', stub_findings())
    write('notes/open_questions.md', stub_open_questions())
    write('notes/glossary.md', stub_glossary())
    write('notes/visual-references.md', stub_visual_references())

    # deck (delegated to pptx-toolkit) -------------------------------------
    deck_rel = 'slides/deck.pptx'
    deck_abs = os.path.join(root, deck_rel)
    w, h = 10.0, 5.625
    deck_note = ''
    if a.no_deck:
        deck_note = 'skipped (--no-deck)'
    elif os.path.exists(deck_abs):
        skipped.append(deck_rel)
        deck_note = 'exists'
    else:
        tk = a.pptx_toolkit or os.path.join(os.path.dirname(SKILL_DIR),
                                            'pptx-toolkit', 'scripts')
        nd = os.path.join(tk, 'new_deck.py')
        if not os.path.exists(nd):
            deck_note = 'NOT CREATED - new_deck.py not found at %s' % nd
        elif a.dry_run:
            made.extend([deck_rel, 'slides/deck-profile.json'])
            deck_note = 'would run new_deck.py'
        else:
            cmd = [sys.executable, nd, deck_abs, '--title', name,
                   '--write-profile', os.path.join(root, 'slides', 'deck-profile.json')]
            cmd += ['--profile', os.path.abspath(a.profile)] if a.profile \
                else ['--preset', a.preset]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if r.returncode == 0:
                made.extend([deck_rel, 'slides/deck-profile.json'])
                deck_note = 'created'
            else:
                deck_note = 'FAILED (%s) %s' % (r.returncode,
                                                (r.stdout or r.stderr).strip()[:200])

    # decisions.md needs the geometry the deck actually got
    prof_abs = os.path.join(root, 'slides', 'deck-profile.json')
    if os.path.exists(prof_abs):
        try:
            import json
            with open(prof_abs, encoding='utf-8') as f:
                g = (json.load(f).get('geometry') or {})
            w, h = g.get('width_in', w), g.get('height_in', h)
        except Exception:
            pass
    write('notes/decisions.md', stub_decisions(name, a.preset, w, h, a.language))

    git_note = ''
    inside = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], cwd=root,
                            capture_output=True, text=True).stdout.strip() == 'true' \
        if os.path.isdir(root) else False
    if a.git:
        if inside:
            git_note = 'already inside a git work tree -- git init skipped'
        elif a.dry_run:
            git_note = 'would run git init'
        else:
            r = subprocess.run(['git', 'init', '-q'], cwd=root, capture_output=True, text=True)
            git_note = 'git init done (no commit made)' if r.returncode == 0 \
                else 'git init failed: %s' % r.stderr.strip()
    else:
        git_note = 'already inside a git work tree' if inside else 'not a git repo (--git to init)'

    # report ---------------------------------------------------------------
    print('%s%s' % (tag, root))
    print('  project   %s' % name)
    print('  preset    %s' % (a.profile or a.preset))
    print('  deck      %s' % deck_note)
    print('  git       %s' % git_note)
    print('  created   %d' % len(made))
    for m in made:
        print('    + %s' % m)
    if skipped:
        print('  skipped   %d (already existed, left untouched)' % len(skipped))
        for s in skipped:
            print('    = %s' % s)
    print('\n  not created by design (Phase 2 outputs):')
    print('    slides/outline.md  slides/storyboard.md  slides/review_state.md')
    print('\nnext: fill in TASK.md, then start Phase 1.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
