# Phase 3: PPTX Comment Review Workflow

## Purpose

PowerPointのコメントを含むPPTXを読み取り、コメントが付いているすべてのスライドをレビュー・修正します。

レビュー入力ファイルは証跡として保持し、直接編集しません。

---

## Inputs

* 作業中PPTX: `slides/deck.pptx`
* コメント付きPPTX:

```text
slides/review-input/deck-review-rNNN.pptx
```

### 入力の2モード

コメントの届き方は2通りある。**どちらかを判別してから作業を始めること。**

**モード A — 別ファイル**

`slides/review-input/` に新しいコメント付きPPTXが置かれている。そのまま入力として使う。

**モード B — 作業中PPTXに直接付与**

ユーザーが `slides/deck.pptx` に直接コメントを付けた。実運用ではこちらが多い。

この場合、**編集を始める前に最初の操作として**、作業中PPTXを証跡へ複製する。

```text
cp slides/deck.pptx slides/review-input/deck-review-rNNN.pptx
```

複製前に1文字でも編集してはならない。複製後は、その証跡ファイルを読み取り専用として扱う。

どちらのモードだったかを `slides/reviews/comment-import-rNNN.md` の `## Source` に記録する。

* 関連ファイル:

  * `slides/storyboard.md`
  * `slides/review_state.md`
  * `sources/`
  * `notes/`
  * `examples/`
  * `assets/diagrams/`

`rNNN` はレビューラウンド番号です。

---

## Scope

1回の作業で、レビュー入力PPTX内にコメントが存在するすべてのスライドを対象とします。

* 同じスライドの複数コメントは、まとめて処理する。
* コメントのないスライドは原則として変更しない。
* 承認済みスライドでも、コメントが付いている場合は修正対象とする（コメントが変更許可である）。
  コメントの無い承認済みスライドへの波及は、修正せず `## Approved slide change requests` に積む。
* コメントによる影響が他スライドへ及ぶ場合は、影響を報告する。
* コメントのない関連スライドを変更する場合は、ユーザーの明示的な指示を得る。

---

## Comment conventions

任意で、コメント先頭に分類を付けられます。

```text
[TECH] 技術的な正確性
[EXPLAIN] 説明不足
[DIAGRAM] 図
[CODE] コード
[SOURCE] 出典
[CONSISTENCY] 整合性
[LAYOUT] レイアウト
```

重要度も任意で指定できます。

```text
[TECH][HIGH] この説明には成立条件が不足しています。
```

接頭辞がない場合は、コメント内容から分類してください。

---

## Procedure

### 1. コメント抽出

レビュー入力PPTXから、すべてのコメントを抽出します。

各コメントについて次を記録してください。

* コメントID
* スライド番号
* スライドタイトル
* 作成者
* コメント本文
* コメント位置
* 推定対象
* 分類
* 重要度
* 状態

コメントID:

```text
CMT-rNNN-NNN
```

抽出結果:

```text
slides/reviews/comment-import-rNNN.md
```

コメント本文は、原文を保持してください。要約・整形・誤字修正をしないでください。

抽出には `pptx-toolkit` スキルを使います。雛形が生成されるので、
分類・重要度・状態・対応の各欄をエージェントが埋めます。

```text
python extract_comments.py <deck.pptx> --dry-run          # 件数と対応スライドの確認
python extract_comments.py <deck.pptx> --round rNNN --out slides/reviews/comment-import-rNNN.md
```

書式は `templates/comment-import.md` に従います。

### 2. コメント整理

コメントをスライド単位でグループ化します。

対象や意図が不明なコメントは、次の状態にしてください。

```text
NEEDS_CLARIFICATION
```

意図を推測して修正しないでください。

### 3. 技術確認

コメントをそのまま反映する前に、必要に応じて次を確認します。

* 公式仕様や一次情報
* 対象バージョン
* 一般仕様と実装依存の違い
* Storyboardとの整合性
* UML記法
* サンプルコード
* 他スライドとの関係

技術的に誤ったコメントは反映せず、理由と根拠を記録してください。

コメントに答えて**オーケストレータが新しい文を書く**ときは、`phase3-batch-build.md` の
「指摘の反映」に従います（storyboard の `### Spec changes` に 6 点検つきで起こしてから書く）。

### 4. スライド修正

コメントが付いているすべてのスライドを修正します。

* 技術的な正確性を見栄えより優先する。
* 言葉足らずな説明を補う。
* 図を修正した場合は、編集可能なソースも更新する。
* コードを修正した場合は、`examples/` の完全版との整合性を確認する。
* 内容が1枚に収まらない場合は、削除ではなく分割を提案する。
* レビュー入力PPTX内のコメントは削除・変更しない。

### 5. レンダリング確認

修正したすべてのスライドをレンダリングし、**PNG を実際に見て**確認します。

確認項目は `reference/review-rubric.md` の **§R5 表示・レンダリング** が唯一の正です
（この節に項目を再掲しません）。

複数スライドのレンダリングは**1回の COM セッションにまとめます**。

```text
python <pptx-toolkit>/scripts/render_deck.py slides/deck.pptx --slides 20,22-25 --png-dir <out>
```

### 5.5. 評価パス

状態を更新する前に、修正した各スライドを `reference/review-rubric.md` に照らして採点します。

* 未解決の `CRITICAL` / `HIGH` があれば修正し、再レンダリングして再採点します
* 反復上限・離脱条件・発振ガードは `phase3-batch-build.md` と共通です
* ユーザーのコメント対応そのものは `## コメント` の記録が正で、
  評価パスはそれに**加えて**ルーブリック違反を拾うためのものです

コメント対応で新たに壊れた箇所（隣接要素との重なり、はみ出し、出典の消失）は
ここで捕まえます。

### 6. 状態更新

修正したスライドは、次の状態にします。

```text
AWAITING_REVIEW
```

エージェント自身の判断で `APPROVED` にしないでください。

コメントの状態は次から選びます。

| Status                | Meaning      |
| --------------------- | ------------ |
| `OPEN`                | 未対応          |
| `APPLIED`             | 修正を反映済み      |
| `VERIFIED`            | 修正後の確認済み     |
| `NEEDS_CLARIFICATION` | 意図や対象が不明     |
| `REJECTED`            | 根拠があり反映しなかった |
| `CLOSED`              | ユーザーが対応完了を確認 |

エージェント自身の判断で `CLOSED` にしないでください。

---

## Outputs

作業中PPTX:

```text
slides/deck.pptx
```

レビュー用修正版:

```text
slides/review-output/deck-revised-rNNN.pptx
```

レビュー記録:

```text
slides/reviews/comment-import-rNNN.md
slides/review_state.md
```

レビュー用PDF:

```text
output/pdf/deck-revised-rNNN.pdf
```

必要に応じて、スライド単位のレビュー記録も更新します。

```text
slides/reviews/slide-NNN.md
```

---

## Review input protection

`slides/review-input/` 配下のPPTXは読み取り専用として扱います。

次を行わないでください。

* 上書き
* コメントの削除や変更
* スライド内容の変更
* 同じレビューラウンド番号の再利用

新しいレビューでは、番号を増やしてください。

```text
deck-review-r001.pptx
deck-review-r002.pptx
```

---

## Completion

作業完了時は、次を報告してください。

* レビュー入力ファイル
* レビューラウンド
* 抽出したコメント数
* 修正したスライド一覧
* 対応したコメントID
* 主な修正内容
* `NEEDS_CLARIFICATION` のコメント
* `REJECTED` のコメントと理由
* 他スライドへの影響
* 更新した図やコード
* 修正版PPTXとPDF
* ユーザーに再確認してほしい点

報告後は停止し、再レビューを待ってください。
