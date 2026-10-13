# `workflows/phase3-slide-creation.md`

# Phase 3: スライド作成

## Purpose

ユーザーが明示的に1枚だけを求めた場合に、新しいスライドを1枚作成する。

**既定はバッチ作成**（`phase3-batch-build.md`）。このワークフローは単枚モードである。
品質ループは単枚でも同じく適用する ─ 1枚だけを選んでも品質保証は落ちない。

## Preconditions

次を確認する。

* `TASK.md` のCurrent phaseがPhase 3である
* `slides/outline.md` と `slides/storyboard.md` が承認済みである
* 対象スライドがユーザーの指示で特定されている
* 対象スライドが `NOT_STARTED` である

> 旧版には「`review_state.md` にレビュー待ち・修正待ちがない」という前提条件があったが、
> **削除した。** レビュー待ちのスライドがあっても、`NOT_STARTED` の別スライドを作ることは
> 妨げられない（`SKILL.md` §3 のスコープ規則で保護される）。

条件を満たさない場合は作成せず、理由を報告する。

## Procedure

1. 対象スライドを特定する。
2. Storyboard、調査結果、出典、サンプルコードを確認する。
   **出典は一次情報に当たり直す**（`phase3-batch-build.md` §2「出典を確定する」。単枚でも省かない）。
3. 技術内容、前提条件、対象バージョン、制約を再確認する。
   ビルダーへの発注は `phase3-batch-build.md` の「発注文の契約」に従う。
4. 必要な図を `assets/diagrams/` に作成する。
5. 対象スライド1枚を `slides/deck.pptx` に作成する。

   `slides/deck.pptx` が存在しない場合は、内容を作る前に器を作る。

   ```text
   python <pptx-toolkit>/scripts/new_deck.py slides/deck.pptx \
       --profile slides/deck-profile.json --slides 0
   ```

   **素の `Presentation()` を書かない。** 4:3・白背景で生成され、
   既定の文字色（ほぼ白）と組み合わさって「何も見えないデッキ」になる。
6. スライドをPDFまたは画像へレンダリングする。
7. **評価ループを回す。** `reference/review-rubric.md` に照らして採点し、
   未解決の `CRITICAL` / `HIGH` が 0 になるまで修正を繰り返す。
   手順・反復上限・離脱条件・発振ガードは `phase3-batch-build.md` の
   「離脱条件」節と共通（バッチサイズ1として実行する）。

   評価は**必ずレンダリング結果（PNG）を見て**行う。
   `check_deck.py` が判定できるのは構造の6項目だけで、
   本文が枠からはみ出す事象すら検出できない。
8. 状態を `AWAITING_REVIEW` に更新する。

## Slide rules

* 技術的な正確性を見栄えより優先する。
* 資料本文だけで主要な内容を理解できるようにする。
* 図、本文、コード、出典を一致させる。
* UML図は対象内容に適した種類を使用する。
* 実行可能な完全版コードは `examples/` に置く。
* 1枚に収まらない場合は、内容を削らず分割案を提示する。
* 承認済みスライドを変更しない。

## Outputs

* `slides/deck.pptx`
* `slides/review_state.md`
* 必要に応じて `slides/reviews/slide-NNN.md`
* `output/pdf/slide-NNN-review.pdf`
* 必要に応じて `assets/diagrams/`

## Completion

次を報告する。

* 対象スライドとタイトル
* 技術的な目的
* 記載した内容
* 使用した図、コード、Source ID
* 自己レビュー結果
* ユーザーに確認してほしい点
* 未確認事項

報告後は停止し、ユーザーのレビューを待つ。