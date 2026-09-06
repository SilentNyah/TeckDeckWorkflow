# 状態ファイルの構造（State schema）

各状態ファイルが持つべき節と書式を定める。値の意味は `status-vocabulary.md` を見ること。

---

## `slides/review_state.md`

スライドごとの進行状態を管理する中心ファイル。**Phase 3 の開始時に必ず読む。**

### 節構成

```markdown
# Slide Review State

## Rules                     ← 不変。下記の5行を必ず含む
## Deck structure note       ← デッキ全体の構成メモ・枚数・章の対応・番号の振り直し履歴
## Current target            ← 今のラウンドで何を対象にしているか
## Progress                  ← 全スライドの状態表（下記）
## Current review request    ← ラウンドごとのレビュー依頼。新しいものを上に積む
## Design decisions to confirm
## Feedback carried forward  ← 今後の全スライドに効く横断ルール
## Pending decisions
## Approved slide change requests
```

### `## Rules`（このまま書く）

```markdown
* 状態はスライド単位で管理する。
* エージェント自身の判断で `APPROVED` にしない。
* ユーザーから明示的な承認があった場合のみ `APPROVED` に変更する。
* レビュー用エージェントの判定（`PASS` / `PASS_WITH_MINOR_FIXES` 等）は承認ではない。
  build → review → fix ループの離脱先は常に `AWAITING_REVIEW` である。
* 新規スライドは既定でまとめて作成する。バッチの対象は `NOT_STARTED` のスライドのみ。
  `AWAITING_REVIEW` / `REVISION_REQUIRED` のスライドは、ユーザーの明示指示がない限り
  バッチに含めない。
* 承認済みスライドを無断で変更しない。
```

**ブロッキング規則をスコープ規則に置き換えている。**
旧版は「レビュー待ちがある間は次を作らない」だったが、これはバッチ作成では自己ブロックする
（5枚中2枚目が、1枚目が `AWAITING_REVIEW` になった時点で開始できなくなる）。
対象を `NOT_STARTED` に限定することで、**同じ保護をデッドロックなしで得る** ─
レビュー待ちのスライドは依然として勝手に触られない。

### 既存プロジェクトの移行

`## Rules` は各プロジェクトの `review_state.md` に**実体としてコピーされている**ため、
スキル側を直しても既存プロジェクトには反映されない。
しかも上記のとおり**Phase 3 の毎ターン冒頭で読まれる**ので、放置すると
古い規則が新しい手順と矛盾したまま参照され続ける。

バッチ作業の**最初の操作**として、対象プロジェクトの `## Rules` を確認する。
「`AWAITING_REVIEW` または `REVISION_REQUIRED` のスライドがある間は、次のスライドを
作成しない」に相当する行があれば旧版である。

> **文字列一致で判定しないこと。**
> 実プロジェクトでは主語が「Codex/Claude 自身の判断で」等に書き換えられている例がある。
> **意味で判定する**（`AWAITING_REVIEW` と「次のスライドを作成しない」が同じ箇条書きにあるか）。

移行手順:

1. 旧版を検出したことをユーザーに報告し、差し替えを**提案する**。**黙って書き換えない。**
2. 承認後、上記の新版へ置き換える。
3. `notes/decisions.md` に DEC を立てる。Context に「旧ルール（1枚ずつ）からの方針転換」、
   Consequences に「`AWAITING_REVIEW` のスライドが新規作成をブロックしなくなる。ただし
   バッチ対象は `NOT_STARTED` に限定されるため、既存の `AWAITING_REVIEW` スライドは
   変更されない」と明記する。

### `## Progress` の表（5列）

```markdown
| Slide (現位置) | Title | Status | Last updated | Notes |
| ----: | ----- | ----------- | ------------ | ------------ |
| 19 | サンプルで確認：… | `AWAITING_REVIEW` | 2026-07-23 | rev2。CMT-r001-001 適用済み。 |
| ~~41~~ | ~~内部実装 (1/2)~~ | `CUT` | 2026-07-24 | CMT-r002-021。DEC-025 で削除。storyboard に温存。 |
| 1–15 | Chapter 1 | `APPROVED` | — | 範囲行。個別管理しない範囲はまとめてよい。 |
```

規約:

* `CUT` の行は `~~取り消し線~~` を付け、削除後も**行を消さない**（履歴が追えなくなるため）。
* スライド番号が繰り上がった場合、Notes に「旧 NN」を残す。
* Notes には rev 番号と対応した `CMT-rNNN-NNN` を書き、対応の追跡を可能にする。

### `## Current target` ─ バッチ形式

バッチ作成中はここに台帳を置く。バッチIDは `bNNN`。
コメントラウンド用の散文形式と**併存できる**（別の `###` ブロックとして積む）。

```markdown
### バッチ b003（2026-08-19 ─ Chapter 3 本文 30–37）

* Batch ID: `b003`
* Unit: Chapter 3「Structured Concurrency」本文（outline.md §3）
* Slides: 30, 31, 32, 33, 34, 35, 36, 37（すべて `NOT_STARTED` から開始）
* Exit bar: 未解決の `CRITICAL` / `HIGH` が 0
* Max iterations: 3
* Waves: 1（30 パイロット）→ 2（31–37）
* Batch status: **完了 ─ 8枚すべてユーザーレビュー待ち**

| Slide | Wave | Build | Review iter | Exit verdict | Open CRIT/HIGH | Deferred | 状態 |
| ----: | ---: | ----- | ----------: | ------------ | -------------: | -------- | ---- |
| 30 | 1 | done | 2 | `PASS` | 0 | — | `AWAITING_REVIEW` |
| 31 | 2 | done | 1 | `PASS` | 0 | — | `AWAITING_REVIEW` |
| 33 | 2 | done | 3 | `PASS_WITH_MINOR_FIXES` | 0 | FINDING-004 (MEDIUM) | `AWAITING_REVIEW` |
| 36 | 2 | done | 3 | `REVISION_REQUIRED` | 1 (HIGH) | — | `AWAITING_REVIEW` ⚠ 反復上限 |
| 37 | 2 | done | 2 | `REVISION_REQUIRED` | 1 (CRITICAL) | — | `BLOCKED` ⚠ 要ユーザー判断 |
```

この表がループの台帳であり、反復をまたいだ進捗の記録でもある。
`## Progress` は従来どおり5列のまま、最終状態だけを反映する。

### `## Feedback carried forward` ─ 書式

バッチ内の後続スライドすべてに効く横断ルール。
評価用エージェントが `Carry forward: yes` を付けた指摘、ユーザーの指示、
根拠付きで受け入れられた反論が入る。

```markdown
* 【b003 / Slide 031 由来 / R3-6】矢印ラベルには必ず動作主体を書く
  （「join」ではなく「親が子を join」）。
* 【b003 / Slide 033 由来 / R1-C-4】`CoroutineScope` は常にコードフォントで表記し、
  和文と混ぜない。
* 【r002 / ユーザー指示】章内マップの「実務」項目は削除済み。以降のスライドで参照しない。
```

書式は `【出所 / 由来スライド / rubric項目】ルール`。**命令形の一文**で書く
（ビルダーが指摘本文を読み返さずに従える粒度）。

オーケストレータはこの節**全体**を、以降のすべての build 指示・review 指示・
バッチ整合パスに渡す。

**完成済みスライドを、新しい横断ルールが増えるたびに再ループさせてはならない。**
それは発散する。既存スライドへの遡及適用は、バッチ末尾の整合パス（R6）1回で行う。

### `## Current review request`

ラウンドごとに `### PPTXコメント rNNN 対応（日付 ─ 概要）` を**新しい順に**積む。各節に:

* Review input / Comment import / Review output / Revised（日付）へのパス
* 対応の要約表（Slide / コメントID / 主な修正）
* `Points to review` — ユーザーに特に見てほしい判断

---

## `slides/reviews/comment-import-rNNN.md`

書式は `templates/comment-import.md` に従う。`extract_comments.py` が雛形を生成する。

---

## `notes/decisions.md`

`## DEC-NNN: <タイトル>` を `---` で区切って積む。各エントリの節:

| 節 | 必須 | 内容 |
| --- | --- | --- |
| `### Date` | ✔ | 絶対日付（相対表現を使わない） |
| `### Status` | ✔ | `ACCEPTED` / `SUPERSEDED` / `REVERTED` |
| `### Context` | ✔ | なぜこの判断が必要になったか |
| `### Decision` | ✔ | 何を決めたか |
| `### Reason` | ✔ | なぜそう決めたか |
| `### Alternatives` | 任意 | `\| Alternative \| Reason not selected \|` の表 |
| `### Consequences` | ✔ | 波及。番号の振り直し・他ファイルへの影響を必ず書く |
| `### Source IDs` | 任意 | 根拠にした `SRC-NNN` |
| `### Related files` | ✔ | 変更したファイル |

**ユーザー指示で過去の方針を反転する場合**は、元の DEC を書き換えず新しい DEC を立て、
Context に「DEC-NNN の反転」と明記する。可逆性の担保（原本の保全先）も Consequences に書く。

---

## `notes/open_questions.md`

前段の自由記述（`## ユーザー判断が必要な点` / `## 追加調査候補`）のあと `---`、
以降 `## OQ-NNN: <問い>` を積む。各エントリの節:

`### Question` / `### Why it matters` / `### Current information` /
`### Required investigation` / `### Candidate sources`（任意） /
`### Status`（`OPEN` / `DEFERRED` / `RESOLVED`） / `### Resolution`（解決後に追記）

---

## `sources/source_index.md`

`## SRC-NNN: <タイトル>` を `---` で区切る。冒頭は箇条書きのメタ情報:

```markdown
## SRC-039: JobSupport.kt（公式ソース tag 1.11.0）

* URL: https://...
* Provider: ...
* Source type: 公式ソースコード（tag 固定）
* Checked: 2026-07-20
* Target version: ...
* Reliability: High for implementation / Low for stable public contract

### Key technical points        ← 全エントリ必須

* ...
```

任意の追加節: `### Summary` / `### Preconditions` / `### Constraints and exceptions` /
`### Applicable topics` / `### Diagram and code candidates` / `### Update history`

**同じURLを再調査した場合は新規IDを作らず、既存項目の `### Update history` に追記する。**

詳細な項目定義は `templates/source-entry.md`。

---

## `notes/glossary.md`

5列の表1つ＋ `## Writing rules`。

```markdown
| Term | Full name | Definition | Related terms | Source |
```

---

## `notes/findings.md`

`templates/finding-entry.md` の `FINDING-NNN` 形式が正式。
ただし調査量が多い場合は**技術トピック単位の見出し**で構成し、
見出しに根拠の `SRC-NNN` を併記する運用でもよい（実運用ではこちらが多い）。
どちらの形式でも、**確認済みの事実 / 推論 / 未確認**の区別は必ず明示する。
