# `workflows/phase0-project-setup.md`

# Phase 0: プロジェクト初期化

## Purpose

空のフォルダから、Phase 1 を開始できる作業ツリーを作る。

このフェーズでは調査も構成もスライド内容も作らない。作るのは器だけ。

## Preconditions

次を確認する。

* 作業対象ディレクトリのパスが確定している
* `TASK.md` が無い、または `slides/` が無い
  （すでに揃っている場合は Phase 0 を実行せず、`TASK.md` の `Current phase` に従う）
* python-pptx が利用できる（`pptx-toolkit` スキルの Environment を参照）

すでに存在するファイルは**上書きしない**。既存ツリーの修復として実行する場合も同じ。

## Procedure

### 1. ユーザーに確認する

次の4点を確認し、確認が取れるまで先へ進まない。

* プロジェクト名（既定: フォルダ名）
* テーマの見出し（`TASK.md` の Goal に置く暫定の1行でよい）
* 配色プリセット `dark` / `light`（既定: `dark`）
* git 管理の有無（すでに git 管理下かどうかを併せて報告する）

### 2. 初期化スクリプトを実行する

```text
python <techdeck-workflow>/scripts/init_project.py <dir> --preset <preset> --name "<名前>"
```

git を使う場合のみ `--git` を付ける。**ユーザーの同意なく `--git` を付けない。**
自動で commit しない。

先に `--dry-run` を付けて、作成対象を確認してから実行してもよい。

### 3. 出力を確認する

`created` / `skipped` の一覧をそのまま確認する。

`slides/outline.md` `slides/storyboard.md` `slides/review_state.md` は
**Phase 2 の成果物なので、ここでは作らない。**
空の `outline.md` を置くと、フェーズ推論が新規案件をいきなり Phase 2 と判定してしまう。

### 4. デッキを検査する

```text
python <pptx-toolkit>/scripts/check_deck.py slides/deck.pptx --profile slides/deck-profile.json --contrast
```

findings が 0 であることを確認する。
新規デッキは重なりが無いので、`--contrast` を付けても誤検出は出ない。

### 5. レンダリングして目視する

```text
python <pptx-toolkit>/scripts/render_deck.py slides/deck.pptx --slides 1 --png-dir output/png/
```

**生成された PNG を実際に見る。** 背景色・文字色・罫線が意図どおりかを確認する。
ここで初めて、レンダリング経路（PowerPoint COM）がこの環境で動くことが確認できる。

文字が見えない場合は配色の組み合わせが破綻している。`deck-profile.json` を直して
4〜5 をやり直す。

### 6. `TASK.md` を埋める

Goal / Deliverable / Audience / Reading mode / Target version / Scope /
Required topics の空欄をユーザーと埋める。

**`Current phase` は `Phase 1` のまま維持する。**

### 7. 配色を確認する

`slides/deck-profile.json` の `palette` / `fonts` / `conventions` をユーザーに提示し、
案件固有の変更が必要かを確認する。変更した場合は 4〜5 をやり直す。

## Outputs

* `TASK.md` `AGENTS.md` `README.md` `.gitignore`
* `slides/deck-profile.json` `slides/deck.pptx`（仮タイトル1枚）`slides/AGENTS.md`
* `examples/AGENTS.md`
* `sources/source_index.md`
* `notes/findings.md` `notes/open_questions.md` `notes/glossary.md`
  `notes/decisions.md`（`DEC-001` に採用プリセットと寸法を記録）
* ディレクトリ:
  `notes/ sources/ examples/ assets/{diagrams,screenshots,templates}/`
  `slides/{reviews,review-input,review-output}/ output/{pptx,pdf}/`
* レンダリング確認用 PNG（`output/png/`。git 管理外）

## Completion

作業完了時は、次を報告する。

* 作成したディレクトリとファイル（`skipped` も含めて一覧で）
* 採用したプリセットと、スライド寸法・背景色・本文色
* `check_deck.py` の結果
* レンダリング PNG の目視結果
* `TASK.md` のうち未記入のまま残っている項目
* git 管理の状態と、ユーザーに判断してほしい点
* `slides/deck.pptx` の1枚目は Phase 0 が置いた**仮のタイトルスライド**であり、
  Phase 3 で storyboard に基づいて作り直す予定であること

報告後は停止し、`TASK.md` が埋まるまで Phase 1 へ進まない。
