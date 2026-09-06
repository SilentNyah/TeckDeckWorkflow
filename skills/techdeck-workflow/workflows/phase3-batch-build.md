# `workflows/phase3-batch-build.md`

# Phase 3: スライドのバッチ作成（既定）

## Purpose

承認済みの構成をもとに、**複数のスライドをまとめて作成する**。
作成した各スライドは、ユーザーに渡す前に build → review → fix のループを通す。

これが Phase 3 の新規作成の**既定の動作**である。1枚だけの作成は、
ユーザーが明示的に求めた場合のモード（`phase3-slide-creation.md`）。

## ループは承認を代行しない ─ 最初に読むこと

ループの合格基準は「未解決の `CRITICAL` / `HIGH` が 0」であり、これは
`phase4-deck-final-review.md` の最終化基準と同一のバーである。

**このバーを満たしたスライドの終端は `AWAITING_REVIEW` である。**
評価用エージェントが返す `PASS` はレビュー総合判定（`status-vocabulary.md` の名前空間(3)）
であって、スライド状態(1)の `APPROVED` ではない。両者は別の名前空間である。

**`APPROVED` へ至る経路は、ユーザーの明示的な指示ただ一つのままである。**

ループが上げるのは、ユーザーに届くスライドの下限であって、ユーザーの権限ではない。

## Preconditions

* `TASK.md` の Current phase が Phase 3 である
* `slides/outline.md` と `slides/storyboard.md` が承認済みである
* バッチ対象のスライドがすべて `NOT_STARTED` である
* `slides/deck.pptx` が存在する（無ければ `new_deck.py` で器を作ってから始める）

条件を満たさない場合は作成せず、理由を報告する。

### `review_state.md` の `## Rules` を確認する

**バッチ作業の最初の操作として**、対象プロジェクトの `slides/review_state.md` の
`## Rules` 節を読む。

「`AWAITING_REVIEW` または `REVISION_REQUIRED` のスライドがある間は、次のスライドを
作成しない」に相当する行があれば**旧版**である。バッチ作成と直接矛盾するため、
`reference/state-schema.md` の「既存プロジェクトの移行」に従って**置換を提案する**。

**黙って書き換えない。** ユーザーの承認を得てから置き換え、`notes/decisions.md` に DEC を立てる。

---

## Procedure

### 1. バッチを解決する

最初に一致したものを採用する。

| 条件 | バッチ |
| --- | --- |
| ユーザーが範囲を明示（「30〜43を作って」） | その集合 |
| ユーザーが章を指定（「Chapter 3 を作って」） | その章の `NOT_STARTED` スライド |
| 「続き」「次」または単に作成を依頼 | `outline.md` 上で `NOT_STARTED` を含む**次の章**のスライド |
| いずれも解決しない | **ユーザーに聞く。推測でバッチを決めない。** |

**対象は `NOT_STARTED` のスライドのみ。**
`AWAITING_REVIEW` / `REVISION_REQUIRED` / `APPROVED` のスライドは、
ユーザーの明示指示がない限りバッチに含めない。これが旧ブロッキング規則の代わりの保護である。

`slides/deck-profile.json` に `batch` キーがあればその設定を使う。無ければ既定値。

```json
"batch": { "unit": "chapter", "max_slides_per_wave": 8,
           "max_iterations": 3, "review_concurrency": 4 }
```

### 2. `## Current target` にバッチを記録する

`reference/state-schema.md` のバッチ形式で `slides/review_state.md` に台帳を書く。
バッチIDは `bNNN`（連番）。対象スライドを `DRAFTING` にする。

**`slides/review_state.md` を書くのはオーケストレータ（このターン）だけである。**
どちらのエージェントにも書かせない。

### 3. 波0 ─ パイロット1枚

バッチの先頭1枚だけを、単独でループに通す。

```
build → render → review → fix → review
```

得られた `Carry forward: yes` の指摘を `## Feedback carried forward` に統合する。

**なぜ先に1枚か:** 7枚を作ってからレビューすると、1枚目で分かった教訓が残り6枚に届かない。
先頭1枚でバッチ全体の作法を確立してから残りを作る。追加コストは COM セッション1回分。

バッチが3枚以下、または `## Feedback carried forward` が既に充実している場合は省略してよい。

### 4. 波1..n ─ 残りを `max_slides_per_wave` ずつ

各波で次を行う。

```
直列:  build × k                （deck.pptx は1ファイル。同時実行しない）
1回:   render_deck.py --slides 31-37 --png-dir <out>   （COMセッション1回にまとめる）
並列:  review × k               （≤ review_concurrency）
直列:  失敗したスライドだけ fix
1回:   修正したスライドだけ再render
並列:  修正したスライドだけ再review（差分モード）
```

反復は `max_iterations` まで。各波の終わりに `review_state.md` を更新する
（中断しても失うのは1波分になる）。

各 build 指示と各 review 指示には、**`## Feedback carried forward` の全文**を渡す。

review 指示には `RUBRIC` に加えて **`VISUAL`**（`reference/visual-design.md` の絶対パス）
を渡す。R8 の数値はそこにしか無く、渡さないと評価用エージェントが閾値を発明する。

### 5. バッチ整合パス

全スライドのレンダリング済み PNG を使い、評価用エージェントを `MODE: batch` で
**1回だけ**起動する。ルーブリック R6（スライド間の整合）のみを見る。

ここで、波の途中で追加された横断ルールが、それ以前に作ったスライドにも適用される。
`R6-8`（キーメッセージの体裁が全スライドで一致しているか）は、この整合パスでしか見つからない。

**完成済みスライドを新しい横断ルールのたびに再ループさせてはならない。**
それは発散する。整合の担保は末尾のこのパス1回で行う。

R6 の指摘を直列で fix し、再レンダリングする。

### 6. 記録して確定する

* スライドごとに `slides/reviews/slide-NNN.md` を書く（`templates/review-report.md` の形式）
* `## Current review request` にバッチの節を追記する（新しいものを上に積む）
* 各スライドの状態を離脱条件に従って更新する
* `## Feedback carried forward` を最終形にする

---

## 離脱条件

| 条件 | 総合判定 | スライド状態 | 追加の処理 |
| --- | --- | --- | --- |
| 未解決の指摘が0件 | `PASS` | `AWAITING_REVIEW` | ─ |
| 未解決の `CRITICAL`/`HIGH` が0、`MEDIUM`/`LOW` が残る | `PASS_WITH_MINOR_FIXES` | `AWAITING_REVIEW` | 残りを `DEFERRED` にし理由を報告 |
| 反復上限に達し `HIGH` が残る | `REVISION_REQUIRED` | `AWAITING_REVIEW` ⚠ | 指摘を `Points to review` と storyboard の `### Known risks` に転記 |
| 反復上限に達し `CRITICAL` が残る | `REVISION_REQUIRED` | **`BLOCKED`** | 技術的に誤っていると分かっているスライドをユーザーのレビューに回さない |
| 残りの未解決指摘がすべて `Fixable by builder: no` | `REVISION_REQUIRED` | 上の重要度に従う | **反復を消費せず即離脱** |
| 評価用エージェントが2回続けて `BLOCKED` を返す | ─ | `BLOCKED` | ツール／指示の不具合として報告 |

**`MEDIUM` はゲートしない。** `check_deck.py` のキャンバス外判定とコントラスト判定は
`MEDIUM` で誤検出が多く、これをゲートにするとループが空回りする。

### 発振ガード

> 反復 N の未解決指摘の集合が、反復 N−1 と同一（同じ locus × 同じ category）の場合、
> 残り反復を消費せず**即座にループを抜ける**。

同じ指摘が2回続くのは実行の問題ではなく**仕様の問題**である。
レビュアーの指摘とビルダーの反論を**両方そのまま** `Points to review` に載せ、
ユーザーに判断を委ねる。

### 修正できない指摘の扱い

`templates/review-report.md` の `#### Required workflow` の値で振り分ける。

| Required workflow | 処理 |
| --- | --- |
| `phase1-research.md` | `notes/open_questions.md` に `OQ-NNN` を立て、スライドを `BLOCKED` にして報告 |
| `phase2-structure.md` | 分割・順序変更を提案（削除ではなく分割）して停止 |
| `phase3-slide-review.md` | ループを続ける（通常の修正可能ケース） |
| なし ＋ `NEEDS_USER` | `Points to review` に載せ、`AWAITING_REVIEW` にする |

---

## エージェントの役割分担

| | `techdeck-slide-builder` | `techdeck-slide-reviewer` |
| --- | --- | --- |
| tools | Read, Write, Edit, Glob, Grep, Bash | **Read, Glob, Grep, Bash のみ** |
| `deck.pptx` | 書く（唯一の書き手） | 読むだけ |
| `review_state.md` | 書かない | 書けない |
| 品質判断 | しない | する |

**判断を持つエージェントは書けず、書けるエージェントは判断を持たない。**
`review_state.md` を書くのはオーケストレータだけで、それは独自の品質判断を持たない。

評価用エージェントには**ビルダーの言い分を渡さない**。成果物だけで判断させる。

## 直列化 ─ 性能ではなく正しさの制約

* **build と fix は常に直列。** `slides/deck.pptx` は1ファイルで、python-pptx は
  パッケージ全体を読み込み、メモリ上で変更し、全体を書き戻す。
  同時実行すると**後勝ちでスライドが無言で消える**。
* **レンダリングも直列。** PowerPoint COM の `Dispatch` は起動中のインスタンスに接続するため、
  同時実行すると先に終わった方の `app.Quit()` が他方の書き出しを殺す。
* **1波のレンダリングは1回の COM セッションにまとめる。**
  `render_deck.py <deck> --slides 31-37 --png-dir <out>` は7回の起動を1回にする。
  8枚×3反復で、1枚ずつなら24回、波まとめなら3回。
* **並列化してよいのはレビューだけ。** レビュアーは PNG とテキストしか読まない。

---

## サブエージェントが使えない場合

`techdeck-slide-builder` / `techdeck-slide-reviewer` が利用できない環境では、
**同じループをこのターン内で実行する。**

> **よくある原因: セッション開始後にエージェント定義を作った。**
> Claude Code は `~/.claude/agents/` をセッション開始時に読み込むため、
> 追加直後のセッションでは `Agent type not found` になる。
> **新しいセッションを開始すれば使える。** 定義ファイル自体の問題ではない。
> それまでは下記のインラインモードで進めてよい。

手順・ルーブリック・反復上限・離脱条件はすべて同一。
失われるのは文脈の独立性と並列性だけであり、
**安全側の性質（`APPROVED` を出さないこと）は変わらない。**

その場合も、レビューの段では**必ず PNG を実際に読む**こと。
自分が書いたスライドであっても、`reference/review-rubric.md` に照らして機械的に採点する。

---

## Outputs

* `slides/deck.pptx`（バッチ対象のスライド）
* `slides/review_state.md`（`## Current target` のバッチ台帳、`## Progress`、
  `## Current review request`、`## Feedback carried forward`）
* `slides/reviews/slide-NNN.md`（スライドごとのレビュー記録）
* `output/pdf/` または PNG（レンダリング結果）
* 必要に応じて `assets/diagrams/`、`examples/`

## Completion

作業完了時は、次を報告する。

* バッチID・対象スライド・波の構成
* スライドごとの: 反復回数 / 総合判定 / 未解決の `CRITICAL`・`HIGH` / 最終状態
* `DEFERRED` にした指摘とその理由
* `PUSHED_BACK`（技術的に誤っているとして反映しなかった指摘）と根拠
* 反復上限に達した、または発振ガードで離脱したスライドと、その未解決の対立点
* `BLOCKED` にしたスライドと理由
* `## Feedback carried forward` に追加した横断ルール
* 他スライドへの影響（**変更はせず報告のみ**）
* ユーザーに確認してほしい点

**報告後は停止し、ユーザーのレビューを待つ。**
エージェント自身の判断でスライドを `APPROVED` にしない。
