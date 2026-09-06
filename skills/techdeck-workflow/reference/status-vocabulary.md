# 状態語彙（Status vocabulary）

このファイルが、本スキルで使うすべての状態語彙の**唯一の定義元**である。
workflow やテンプレートに書かれた値と食い違った場合は、このファイルを正とする。

## 重要: 6つは別々の名前空間

スライド・PPTXコメント・レビュー判定・レビュー指摘・調査結果は**別種のオブジェクト**であり、
たまたま同じ綴りのトークンを共有しているだけである。混同しないこと。

とくに `REVISION_REQUIRED` は **(1) スライドの状態** と **(3) レビューの総合判定** の両方に存在するが、
別物である。`REJECTED` も **(2) コメント状態** と **(5) レビュー指摘状態** で意味が異なる。

---

## (1) スライド状態 — `slides/review_state.md` の Progress 表

| 値 | 意味 | 誰が設定するか |
| --- | --- | --- |
| `NOT_STARTED` | 構成は確定しているが未作成 | Phase 2 の初期化 |
| `DRAFTING` | 作成中・レビューループ中の一時状態 | エージェント |
| `AWAITING_REVIEW` | 作成・修正が終わりユーザーのレビュー待ち | エージェント |
| `REVISION_REQUIRED` | ユーザーが修正を要求した | エージェント（ユーザー指摘を受けて） |
| `APPROVED` | ユーザーが明示的に承認した | **ユーザーのみ** |
| `BLOCKED` | 未解決の技術的疑問等で進行不能 | エージェント |
| `CUT` | デッキから削除。設計は storyboard に温存 | ユーザー指示を受けてエージェント |
| `REUSED` | 既存スライドを流用。今回の作成対象外 | エージェント |

**ゲート:** エージェントは自分の判断で `APPROVED` にしてはならない。
`CUT` と `REUSED` は実運用で先に使われ、後から正式化した値
（`REUSED` は表示上「既存」と書いてもよいが、機械可読の Status 列にはこの英字トークンを使う）。

遷移:

```
NOT_STARTED → DRAFTING → AWAITING_REVIEW ⇄ REVISION_REQUIRED → APPROVED
                              ↓
                           BLOCKED / CUT
```

---

## (2) PPTXコメント状態 — `slides/reviews/comment-import-rNNN.md`

| 値 | 意味 |
| --- | --- |
| `OPEN` | 未対応 |
| `APPLIED` | 修正を反映済み |
| `VERIFIED` | 修正後の確認済み（前ラウンドで対応済み、当ラウンドでは再修正しない場合を含む） |
| `NEEDS_CLARIFICATION` | 意図や対象が不明。**推測して修正してはならない** |
| `REJECTED` | 根拠があり反映しなかった（理由と根拠を必ず記録） |
| `CLOSED` | ユーザーが対応完了を確認した |

**ゲート:** エージェントは自分の判断で `CLOSED` にしてはならない。

---

## (3) レビュー総合判定 — `slides/reviews/*.md` の Overall result

| 値 | 意味 |
| --- | --- |
| `PASS` | 問題なし |
| `PASS_WITH_MINOR_FIXES` | 軽微な修正のみで最終化可 |
| `REVISION_REQUIRED` | 修正が必要（※スライド状態の同名トークンとは別物） |
| `BLOCKED` | 判定不能・前提条件が未達 |
| `AWAITING_USER_REVIEW` | エージェント側の確認は終わり、ユーザー判断待ち |

---

## (4) 重要度（Severity）

`CRITICAL` / `HIGH` / `MEDIUM` / `LOW` — **大文字に統一する。**

| 値 | 意味 |
| --- | --- |
| `CRITICAL` | 最終化を妨げる技術的誤り、またはファイル破損 |
| `HIGH` | 最終化前に必ず直す |
| `MEDIUM` | 修正を推奨 |
| `LOW` | 最終化を妨げない |

PPTXコメントのタグ表記（`[TECH][HIGH]`）とレビュー記録の Severity 欄は同じ尺度を指す。

---

## (5) レビュー指摘の状態 — Review report の Findings

| 値 | 意味 |
| --- | --- |
| `OPEN` | 未対応 |
| `RESOLVED` | 解決済み |
| `DEFERRED` | 意図的に先送り |
| `REJECTED` | 指摘自体を採らない（※コメント状態の同名トークンとは別物） |

---

## ループ判定と承認の分離

build → review → fix ループが出す値は **(3) レビュー総合判定 / (4) 重要度 / (5) 指摘状態**
の名前空間に属し、**(1) スライド状態には属さない。**

レビュー用エージェントは `PASS` を出せるが `APPROVED` は出せない ─
**(3) に `APPROVED` という値が存在しない**からである。

ループの合格基準「未解決の `CRITICAL` / `HIGH` が 0」は
`workflows/phase4-deck-final-review.md` の最終化基準と同一のバーであり、
**そのバーを満たしたスライドの終端は `AWAITING_REVIEW`** である。

`APPROVED` への経路は、ユーザーの明示的な指示ただ一つ。

これは3つの独立した仕組みで担保されている。

| # | 仕組み |
| --- | --- |
| 1 | **語彙** ─ (3) に `APPROVED` が無い |
| 2 | **権限** ─ レビュー用エージェントは `Write` / `Edit` を持たず、状態ファイルを書けない |
| 3 | **終端** ─ ループの全経路が `AWAITING_REVIEW` か `BLOCKED` に落ちる |

**判断を持つエージェントは書けず、書けるエージェントは判断を持たない。**

---

## (6) 調査結果の状態 — `notes/findings.md`

| 値 | 意味 |
| --- | --- |
| `CONFIRMED` | 一次情報で確認済み |
| `PARTIALLY_CONFIRMED` | 一部のみ確認 |
| `DISPUTED` | 情報源間で矛盾がある |
| `DRAFT` | 未確認・記述途中 |

補助尺度: **Reliability** `High`/`Medium`/`Low`（出典の信頼度）、
**Confidence** `High`/`Medium`/`Low`（推論の確信度）。

---

## 決定の状態 — `notes/decisions.md`

| 値 | 意味 |
| --- | --- |
| `ACCEPTED` | 採用し有効 |
| `SUPERSEDED` | 後続の DEC に置き換えられた（置換先の DEC 番号を明記） |
| `REVERTED` | 撤回した（理由を明記） |

方針を反転させる決定（例: 一度詳細化したものを削除する）は、
**元の DEC を `SUPERSEDED` にせず両方残し**、新しい DEC に「DEC-NNN の反転」と明記する。
経緯が追えることを優先する。

---

## コメント分類タグ

ユーザーが PowerPoint コメントの先頭に任意で付けられる。

`[TECH]` 技術的な正確性 / `[EXPLAIN]` 説明不足 / `[DIAGRAM]` 図 / `[CODE]` コード /
`[SOURCE]` 出典 / `[CONSISTENCY]` 整合性 / `[LAYOUT]` レイアウト /
`[VISUAL]` 視覚的強調・情報設計

`[LAYOUT]` と `[VISUAL]` は別物である。
`[LAYOUT]` は**壊れている**（はみ出し・重なり・切れ ─ ルーブリック `R5`）。
`[VISUAL]` は**壊れてはいないが優先順位が伝わらない**（`R8` / `reference/visual-design.md`）。

重要度を続けてもよい: `[TECH][HIGH] この説明には成立条件が不足しています。`

**タグが無い場合は、コメント本文から内容を読んでエージェントが分類する。**

この8タグは、PPTXコメントとレビュー指摘（`templates/review-report.md` の
Category 欄、レビュー用エージェントの `Category`）で共通の**唯一の分類語彙**である。

---

## ID 体系

| 接頭辞 | 対象 | 例 |
| --- | --- | --- |
| `SRC-NNN` | 出典 | `SRC-039` |
| `FINDING-NNN` | 調査結果 | `FINDING-012` |
| `OQ-NNN` | 未解決の問い | `OQ-015` |
| `DEC-NNN` | 決定 | `DEC-025` |
| `VIS-NNN` | 視覚参照（Phase 1 で見た図） | `VIS-004` |
| `REVIEW-NNN` | レビュー記録 | `REVIEW-003` |
| `CMT-rNNN-NNN` | PPTXコメント | `CMT-r002-014` |
| `rNNN` | レビューラウンド | `r002` |
| `bNNN` | 作成バッチ | `b003` |
| `Slide NNN` | スライド | `Slide 039` |

`FINDING-NNN` は調査結果とレビュー指摘の両方で使われる。参照時は文脈を明記すること。
番号は各系列で連番。**既存の最大値の次**を使い、欠番を埋めない。
