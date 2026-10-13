# `workflows/phase4-deck-final-review.md`

# Phase 4: 資料全体の最終レビュー

## Purpose

全スライド承認後に、資料全体の技術的整合性、構成、表記、表示品質を横断的に確認し、最終化の可否を判定する。

## Preconditions

次を確認する。

* すべてのスライドが `APPROVED`
* `AWAITING_REVIEW`、`REVISION_REQUIRED`、`BLOCKED` が存在しない
* 重大な未確認事項が残っていない
* ユーザーから最終レビューの指示がある
* `slides/review_state.md` の `## Approved slide change requests` に `OPEN` が残っていれば、
  **先に一覧を出して処理の可否を諮る**（既定の処理時期がここである）。処理したスライドは
  `AWAITING_REVIEW` に戻るので、再承認を得てから最終レビューに入る

条件を満たさない場合は、レビューを開始せず不足事項を報告する。

## Review procedure

1. `TASK.md` の目的、対象読者、必須項目、**Deliverable（形式・出力先・出さないもの）**と資料を比較する。
2. PPTX全体をPDFへ変換し、全スライドを確認する。
3. 章構成とスライド順の論理性を確認する。
4. 必須技術項目の説明漏れを確認する。
5. スライド間の矛盾、重複、表記ゆれを確認する。
6. 図、本文、コード、出典の整合性を確認する。
7. 前提条件、対象バージョン、制約、例外を確認する。
8. 用語、略語、クラス名、API名の表記を確認する。
9. 図、コード、表、文字の表示崩れを確認する。
10. 最終化を妨げる問題を分類する。
11. 観点を分けて複数のレビュー担当に並行で見せた場合は、**同じ場所への判断の食い違い**と、
    **過去の `DEC-NNN` との食い違い**を一覧にしてユーザーに回す（観点 A は指摘し、観点 B は
    過去の決定に従って指摘しなかった、という食い違いはまとめの段でしか拾えない）。

## Severity

* `CRITICAL`: 最終化不可となる重大な技術的誤りやファイル破損
* `HIGH`: 最終化前に修正すべき重要な問題
* `MEDIUM`: 原則として修正を推奨する説明・整合性の問題
* `LOW`: 最終化を妨げない軽微な問題

## Handling findings

* スライド単体の問題は `phase3-slide-review.md` へ戻す。
* 構成上の問題は `phase2-structure.md` へ戻す。
* 根拠不足や追加調査が必要な場合は `phase1-research.md` へ戻す。
* 承認済みスライドをユーザーの指示なしに修正しない。
* **直す提案をするときは、各対象スライドの今の文字数と予算の余裕を添える。**
  `LOW` をまとめて直す承認を得たあとで、1 枚が上限ぎりぎりで足せないと分かり、
  もう一度聞くことになった実例がある。余裕の無いスライドは分割か移動の案を同時に出す。

## Outputs

* `slides/reviews/deck-final-review.md`
* `output/pdf/deck-final-review.pdf`

レビュー記録は `templates/review-report.md` を使用する。

レビュー結果は次のいずれかとする。

* `PASS`
* `PASS_WITH_MINOR_FIXES`
* `REVISION_REQUIRED`
* `BLOCKED`

## Finalization

次をすべて満たし、ユーザーが最終化を指示した場合だけ最終成果物を出力する。

* 結果が `PASS` または `PASS_WITH_MINOR_FIXES`
* Phase 3 のループ離脱条件はこの節の基準と同一だが、**ループ通過は最終化の許可ではない**。
  「すべてのスライドが `APPROVED`」は依然として独立した前提条件である
* 未解決の `CRITICAL` / `HIGH` がない
* すべてのスライドが `APPROVED`
* PPTXとPDFの表示確認が完了している
* **`TASK.md` の `## Deliverable` と照らした**（形式・出力先・出さないもの。「詳細版は PDF を
  作らない」を見落として既定どおり PDF を出した実例がある）

出力先（`TASK.md` の Deliverable が優先。無ければ次の既定）:

* `output/pptx/<final-name>.pptx`
* `output/pdf/<final-name>.pdf`

## Completion

次を報告する。

* レビュー対象とスライド枚数
* 全体評価
* 重要度別の問題数
* 技術的な問題
* 構成・説明・表示上の問題
* 戻るべきフェーズ
* 最終化の可否
* 更新・出力したファイル

問題がある場合は修正せず、ユーザーの指示を待つ。
