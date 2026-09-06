# {{PROJECT_NAME}}

## Overview

このプロジェクトは、特定テーマに関する技術資料をPPTX形式で作成するための作業場です。

資料は発表用ではなく、読者が手元で閲覧し、資料単体で技術内容を理解できることを主目的とします。

技術的な正確性、説明の十分性、図・本文・コード・出典の整合性を重視します。

## Workflow

作業は次のフェーズに分けて進めます。

0. プロジェクト初期化
1. 技術情報調査
2. スライド構成提案
3. スライド作成・レビュー
4. 資料全体の最終レビュー

**各フェーズの手順・テンプレート・状態語彙は `techdeck-workflow` スキルにあります。**
このリポジトリには複製していません（二重管理を避けるため）。
PPTXの編集・レンダリング・コメント抽出は `pptx-toolkit` スキルを使います。

`workflows/` と `templates/` は通常このプロジェクトには置きません。スキル側の同名ファイルを
使います。1つだけ差し替えたい場合に限り、同じ相対パスで置くと優先されます（SKILL.md §11）。
**セット全体を fork しないでください。**

Phase 3では、**既定でスライドをまとめて作成します**（既定の単位は章）。
作成した各スライドはユーザーに渡す前に build → review → fix のループを通り、
未解決の `CRITICAL` / `HIGH` が無くなった時点で `AWAITING_REVIEW` になります。
**ループの合格は承認ではありません** ─ `APPROVED` はユーザーの明示的な指示によってのみ
設定されます。1枚ずつの作成も、明示的に指示すれば利用できます。
PowerPointコメントによるレビューは、コメントの付いた全スライドを一括で扱います。

## Directory structure

| Path                       | Purpose                                    |
| -------------------------- | ------------------------------------------ |
| `AGENTS.md`                | スキルへの案内とプロジェクト固有の原則（shim）          |
| `TASK.md`                  | テーマ、対象読者、対象バージョン、範囲、**Current phase** |
| `.gitignore`               | バックアップ・レンダリング成果物の除外                   |
| `sources/`                 | 出典管理（`SRC-NNN`）                           |
| `notes/`                   | 調査結果、用語、判断（`DEC-NNN`）、未確認事項（`OQ-NNN`）  |
| `examples/`                | 実行可能なサンプルコード                            |
| `assets/diagrams/`         | UML図などの編集可能ソースと生成画像                    |
| `assets/screenshots/`      | 実行結果や画面のスクリーンショット                      |
| `assets/templates/`        | PPTXテンプレートや共通素材                         |
| `slides/`                  | スライド構成、設計、レビュー状態、作業中PPTX              |
| `slides/deck-profile.json` | 配色・フォント・寸法・表記規約                        |
| `slides/reviews/`          | コメント記録・レビュー記録                          |
| `slides/review-input/`     | コメント付き原本（**読み取り専用の証跡**）              |
| `slides/review-output/`    | ラウンドごとの修正版PPTX                          |
| `output/pptx/`             | 最終PPTX                                    |
| `output/pdf/`              | レビュー用または最終PDF（git 管理外）                  |

## Key files

### `TASK.md`

テーマ / 対象読者 / 対象バージョン / 対象範囲 / 必須技術項目 / **Current phase** / 最終成果物。

`Current phase` はワークフローのルーティング起点です。フェーズを進めたら更新します。

### `slides/outline.md` / `slides/storyboard.md`

章立てとスライド順、各スライドの目的・説明・図・コード・出典。**Phase 2 で作成されます。**

### `slides/review_state.md`

スライドごとの作成・レビュー状態。**Phase 2 で初期化されます。**
状態語彙はスキルの `reference/status-vocabulary.md` が正です。

### `slides/deck.pptx`

編集中のPPTXです。最終成果物は `output/` 配下へ出力します。

## Basic rules

* 作業開始時に `TASK.md` の `Current phase` を確認し、`techdeck-workflow` スキルを呼ぶ。
* 指定されたフェーズだけを実行する。フェーズを自動で進めない。
* エージェント自身の判断でスライドを `APPROVED` にしない。
* 技術的な内容を、見栄えだけを理由に削除しない。
* 情報量が多い場合は、削除ではなくスライド分割を検討する。
* 実行可能な完全版コードは `examples/` に置く。
* UMLなどの図の編集可能ソースは `assets/diagrams/` に残す。
* `output/` 配下のファイルを一次原稿として直接編集しない。
* `slides/review-input/` 配下を編集しない。
