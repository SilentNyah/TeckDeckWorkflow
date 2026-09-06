# Comment Import Template

<!--
ファイル名: slides/reviews/comment-import-rNNN.md

雛形は `pptx-toolkit` の extract_comments.py が生成する。
生成直後は 分類 / 重要度 / 状態 / 対応 が空欄なので、エージェントが埋める。

コメント本文は原文を保持する。要約・整形・誤字修正をしない。
-->

# Comment Import — rNNN

## Source

* レビュー入力: `slides/review-input/deck-review-rNNN.pptx`
* 入力モード: A（別ファイル） / B（作業中 deck に直接付与 → 編集前にスナップショット済み）
* 抽出日: YYYY-MM-DD
* 作成者: <ppt/authors.xml の name>
* コメント形式: PowerPoint modern comments（`ppt/comments/modernComment_*.xml`）
* 抽出件数: N件 / M スライド

## Round の性格

<!-- 任意。前ラウンドへの再フィードバックか、新規章の初レビューか等。
     ラウンドの全体像が分かると、個別対応の判断根拠が追いやすくなる。 -->

---

## コメント

<!--
1件 = 1つの ### 見出し。メタ情報は見出しに圧縮する。

  ### CMT-rNNN-NNN — Slide N / sp=<shape id>（アンカーの説明）/ `[分類][重要度]`

アンカーが特定できない場合は sp= の代わりに `slide-level` と書く。
分類タグがユーザーによって付いていない場合は、本文から判断して付ける。
-->

### CMT-rNNN-001 — Slide N / sp=NN（対象要素の説明）/ `[EXPLAIN][HIGH]`

原文:

```text
<ユーザーのコメント本文をそのまま。改行も保持する>
```

対応 `APPLIED`: <何をどう直したか。判断が入った場合はその理由も>

---

### CMT-rNNN-002 — Slide N / `slide-level` / `[DIAGRAM][MEDIUM]`

原文:

```text
...
```

対応 `NEEDS_CLARIFICATION`: <なぜ意図が判断できないか。推測で修正しないこと>

---

## 技術確認の記録

<!--
コメントをそのまま反映しなかった場合、または反映前に一次情報で確認した場合はここに書く。
「ユーザーの指摘は X の点で正しいが、機構としては Y なので Z と表現した」のような
判断は必ず残す。後のラウンドで蒸し返さないため。
-->

---

## 波及・要確認

<!--
* 他スライドへの影響（変更はせず報告のみ）
* ユーザーに再確認したい判断
* 今回対応しなかった既知の不整合とその理由
-->

---

## Not applied / Rejected

<!-- `REJECTED` のコメントと、反映しなかった根拠。無ければ「なし」と明記する。 -->

## 適用済み残存コメント（再修正なし）

<!--
前ラウンドで対応済みだが、PPTX 上にコメントが残っているもの。
`VERIFIED` として列挙し、当ラウンドでは再修正しない。
-->
