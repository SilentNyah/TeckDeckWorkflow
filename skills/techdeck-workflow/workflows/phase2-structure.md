# `workflows/phase2-structure.md`

# Phase 2: スライド構成提案

## Purpose

Phase 1の調査結果を、読者が段階的に理解できるスライド構成へ変換する。

このフェーズではPPTX本体を作成しない。

## Inputs

次を確認する。

* `TASK.md`
* `sources/source_index.md`
* `notes/findings.md`
* `notes/open_questions.md`
* `notes/glossary.md`
* `notes/decisions.md`

重大な未確認事項が構成へ影響する場合は、該当箇所を確定せず、追加調査が必要であることを報告する。

## Structure rules

* 前提知識から詳細へ段階的に進める。
* 「何か」だけでなく、「なぜ必要か」「どう動くか」も扱う。
* 前提条件、正常系、制約、例外を必要に応じて分ける。
* 1スライドにつき、1つの技術トピックまたは論理的なまとまりを扱う。
* 情報量が多い場合は、削除せず複数スライドへ分割する。
* スライドタイトルだけでも論理展開が分かるようにする。
* 重要な調査結果が構成から漏れないようにする。

## Procedure

1. `TASK.md` から目的、対象読者、範囲、必須項目を抽出する。
2. `notes/findings.md` から説明すべき技術項目を抽出する。
3. 技術項目間の前提関係を整理する。
4. 章構成とスライド順を決める。
5. 各スライドの目的、結論、図、コード、出典を設計する。
6. 必須項目とスライドの対応を確認する。
7. ユーザー判断が必要な点を整理する。

## Outputs

次を更新する。

* 全体構成: `slides/outline.md`
* 各スライドの設計: `slides/storyboard.md`
* 必要に応じた補足: `slides/speaker_notes.md`
* 構成上の判断: `notes/decisions.md`

Storyboardは `templates/storyboard-entry.md` の形式を使用する。

各スライドには最低限、次を定義する。

* タイトル
* 技術的な目的
* 主な結論
* 説明内容
* 前提条件、制約、例外
* 使用する図
* 掲載するコード
* Source ID
* 前後スライドとの関係

構成確定後、`slides/review_state.md` を**作成し**、全スライドを `NOT_STARTED` で初期化する。

このファイルは Phase 2 の成果物であり、Phase 0 / Phase 1 の時点では存在しない。
節の構成は `reference/state-schema.md` を参照する。

## Completion

完了時は次を報告する。

* 章構成
* 想定スライド枚数
* スライド一覧
* 使用予定のUML図、コード、表
* 調査結果との対応
* 未確定事項
* ユーザーに確認してほしい点

報告後は停止し、構成が承認されるまでPhase 3へ進まない。