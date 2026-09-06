# `workflows/phase3-slide-review.md`

# Phase 3: スライドレビュー・修正

## Purpose

ユーザーが指名したスライド（複数可）をレビューし、フィードバックに基づいて修正する。

## Inputs

次を確認する。

* ユーザーの最新フィードバック
* `slides/review_state.md`
* 対象スライドのStoryboard
* 対象スライドのレビュー用PDFまたは画像
* 関連する調査結果、出典、図、コード
* 過去のレビュー記録

## Procedure

1. 対象スライドを特定する。
2. フィードバックを分類する。分類語彙は `reference/status-vocabulary.md` の
   「分類タグ」（`[TECH]` `[EXPLAIN]` `[DIAGRAM]` `[CODE]` `[SOURCE]` `[CONSISTENCY]`
   `[LAYOUT]` `[VISUAL]`）が唯一の正である。

   「どこが重要か分からない」「文字が多い」「メリハリがない」の類は `[VISUAL]` であり、
   ルーブリック `R8` と `reference/visual-design.md` で扱う。
   `[LAYOUT]`（はみ出し・重なり＝壊れ）と混同しない。
3. 対象スライドを `reference/review-rubric.md` に照らして再確認する。
4. 状態を `REVISION_REQUIRED` にする。
5. 指名されたスライドだけを修正する。
6. 図を修正した場合は編集可能ソースも更新する。
7. 再レンダリングして表示を確認する。
8. **評価パスを回す。** 修正したスライドを `reference/review-rubric.md` で採点し、
   未解決の `CRITICAL` / `HIGH` が残る間は修正を繰り返す
   （反復上限・離脱条件・発振ガードは `phase3-batch-build.md` と共通）。
   **PNG を必ず見る。**
9. レビュー履歴を追記する。
10. 状態を `AWAITING_REVIEW` に戻す。

    **`APPROVED` にしない。** 評価パスの `PASS` は承認ではない。

## Revision rules

* ユーザーの意図を勝手に変更しない。
* 承認済みの他スライドを無断で変更しない。
* 承認済み・レビュー待ちの他スライドへの影響は報告だけ行う。
  ただし**同じバッチ内でまだユーザーに渡していないスライド**は、整合のために修正してよい。
* 1枚に収まらない場合は、削除ではなく分割を提案する。
* 技術的な疑義がある場合は一次情報を再確認する。
* エージェント自身の判断で `APPROVED` にしない。

ユーザーが承認した場合だけ対象スライドを `APPROVED` にする。

承認のみの場合は状態更新後に停止する。
「承認、次へ」と指示された場合だけ、次のバッチを作成する（`phase3-batch-build.md`）。

## Outputs

* `slides/deck.pptx`
* `slides/review_state.md`
* `slides/reviews/slide-NNN.md`
* `output/pdf/slide-NNN-review.pdf`
* 必要に応じて図、コード、Storyboard

レビュー記録は `templates/review-report.md` の形式を使用する。

## Completion

次を報告する。

* 修正対象
* ユーザーのフィードバック
* 修正した内容
* 再確認した技術事項
* 更新した図、コード、出典
* 他スライドへの影響
* 再確認してほしい点

報告後は停止し、ユーザーの再承認を待つ。