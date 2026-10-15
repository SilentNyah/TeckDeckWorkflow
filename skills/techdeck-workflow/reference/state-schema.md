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
* 【b003 / Slide 031 由来 / R3-6 / 対象: 図】矢印ラベルには必ず動作主体を書く
  （「join」ではなく「親が子を join」）。
* 【b003 / Slide 033 由来 / R1-C-4 / 対象: 用語】`CoroutineScope` は常にコードフォントで表記し、
  和文と混ぜない。
* 【r002 / ユーザー指示 / 対象: 本文】章内マップの「実務」項目は削除済み。以降のスライドで参照しない。
* 【b002 / Slide 012 由来 / R6-3 / 対象: 色】→ `conventions` #7 に吸収済み。ここでは参照のみ。
```

書式は `【出所 / 由来スライド / rubric項目 / 対象】ルール`。**命令形の一文**で書く
（ビルダーが指摘本文を読み返さずに従える粒度）。

* **対象**は次のいずれか: `キーメッセージ` `本文` `最下段` `コード` `図` `出典` `用語` `配置` `色`。
  同じ対象の規則をまとめて読めるように、節内は対象ごとに並べる。
* **由来**は `bNNN` と**その時点の**スライド番号で書く。番号を振り直したら、
  `scripts/renumber.py` が由来の番号を現番号に書き換える（手で「旧008＝現9」の読み替え注記を
  足さない。旧番号との対応表は `## Deck structure note` の「番号の振り直しの履歴」に残す）。
  番号に依存させたくない規則はスライドタイトルを併記する。

#### 横断ルールを足すときの 4 点検

規則は書いた瞬間ではなく、次に誰かがそれに従って作るときに効く。足す前に確かめる。

1. **同じ対象の既存規則と矛盾しないか。** 対象タグで節を読み、ぶつかる規則（例:「中身は muted」
   と「枠の中のラベルは muted」）が無いか見る。2 つの規則が両立しないときは、絶対値を固定するのを
   やめて**相対距離だけを固定**し、絶対位置は直下の要素に従わせる。
2. **位置を決めたら大きさも決めたか。** 「この型で次に作る人が、まだ選べる自由度は何か」を数える。
   幅を決めない脚注箱は 3 通りに割れ、下限だけ決めた左端は章ごとに割れた。
3. **この規則を守れる実装が実在するか。** 1 例で確かめる。「テキスト側で層色を使わない」は、
   残る色が全部層色だったので守れなかった。
4. **足したら、作成済みのスライドを全文検索する。** 同じ語・同じ要素を持つスライドを列挙し、
   `### R6 notes` のキューに積む。**再ループはしない**（整合パスで扱う）。

#### 統廃合 ─ CF は暫定規則の置き場であり、恒久の規約置き場ではない

バッチの末尾（`phase3-batch-build.md` §7）に、`deck-profile.json` の `conventions` か
`slides/outline.md` の視覚規約へ**吸収できる規則を移し**、CF では参照だけ残す（上の 4 行目の形）。
吸収したら、以降の発注文はその規約を参照する。規則の件数ではなく**執行経路の有無**が問題なので、
「発注文に毎回書かれ、レビューで毎回照合される」場所に置く。

オーケストレータは `scripts/statekit.py show-cf slides/review_state.md --for-slide N --storyboard slides/storyboard.md`
の出力（規則 1 件 1 行。図・コードの無いスライドではそのタグの規則を省いた**全件**）を
build 指示・review 指示に渡す。**節の全文は渡さない** ─ 100 件・118KB になった実例で、全文を
読んだ agent は居なかった（説明段落は規則の根拠であって、従うべき文ではない）。
バッチ整合パス（R6）だけは無指定の `show-cf` で全件を渡す。

**完成済みスライドを、新しい横断ルールが増えるたびに再ループさせてはならない。**
それは発散する。既存スライドへの遡及適用は、バッチ末尾の整合パス（R6）1回で行う。

### `## Current review request`

ラウンドごとに `### PPTXコメント rNNN 対応（日付 ─ 概要）` を**新しい順に**積む。各節に:

* Review input / Comment import / Review output / Revised（日付）へのパス
* 対応の要約表（Slide / コメントID / 主な修正）
* `Points to review` — ユーザーに特に見てほしい判断

### `## Approved slide change requests` ─ 書式

承認済みスライドに対する是正要求の**キュー**。承認後に見つかった不整合（後続スライドで決まった
横断ルール、R6 の指摘、用語の統一、限定語の追加）をここに積み、**承認済みスライドは触らない。**

```markdown
| ID | Slide | 出所 | 内容 | 影響 | 処理時期 | 状態 |
| --- | ---: | --- | --- | --- | --- | --- |
| ASC-001 | 007 | b003 R6 / FINDING-012 | 限定語「〜に限る」を追加 | 字数 +8（余裕内）、図は不変 | Phase 4 | `OPEN` |
| ASC-002 | 013 | ユーザー指摘 2026-09-08 | 凡例の「実線＝取得」を追加 | 凡例の高さ +0.2in | 前倒し（b005 と同時） | `RESOLVED` |
```

* 状態は (5) レビュー指摘の状態（`OPEN` / `RESOLVED` / `DEFERRED` / `REJECTED`）を使う。
* **既定の処理時期は Phase 4。** 各バッチの Completion 報告に件数と一覧を出し、ユーザーが
  「今直す」と指示した分だけ前倒しする。**その指示が、承認済みスライドへの変更許可である。**
* 処理したスライドは `AWAITING_REVIEW` に戻し、再承認を得るまで `APPROVED` に戻さない。
* 分割による**ページ番号だけの付け替え**はこのキューに載せず、`scripts/renumber.py` の変更一覧で
  まとめてユーザーに諮る（`phase3-batch-build.md` の「分割の判断」）。

### statekit の使い方（1 画面。ソースは読まない）

読む（何も書かない。Phase 3 の 1 ターンは `show-turn` 1 回で足りる）:

| コマンド | 出すもの |
| --- | --- |
| `statekit.py show-turn slides/review_state.md slides/storyboard.md --slide N [--sections "Current spec,Sources"]` | `## Rules`・Progress 行・台帳行・圧縮した CF（図／コードの無いスライドはそのタグを省く）・storyboard の節 |
| `statekit.py show-slide slides/storyboard.md --slide N [--sections …]` | storyboard の節（または指定した `###` だけ） |
| `statekit.py show-cf slides/review_state.md [--for-slide N --storyboard …] [--exclude-tags 図,コード]` | CF を 1 件 1 行で。先頭行に「kept of total」 |
| `statekit.py show-ledger slides/review_state.md [--slide N] [--batch bNNN]` | `## Current target` の台帳行 |
| `statekit.py show-progress slides/review_state.md --slide N` | Progress の 1 行 |
| `statekit.py show-rules slides/review_state.md` | `## Rules` |

書く（置き場を機械が守り、書いた行番号を返す）:

| コマンド | 書く先 |
| --- | --- |
| `progress-set … --slide N --status S --date D [--append-notes …]` | Progress 行 |
| `ledger-set … --batch bNNN --slide N --set "列=値"` | 台帳行 |
| `storyboard-set … --slide N --section "名前" --text … [--append] [--before …]` | storyboard の `###` 節（無ければ作る） |
| `sources-row … --slide N --row "\| … \|"` | `### Sources` の表 |
| `src-append … --src SRC-NNN --text … [--section …]` | 索引の節末 |
| `review-append slides/reviews/slide-NNN.md --section "R6 notes" --text …` | レビュー記録（ファイルも見出しも無ければ作る） |
| `asc-add … --slide N --source … --content … [--impact …] [--when …]` | ASC キュー（採番は表の ID 列だけから。注記で先に番号を引用しない） |
| `next-id SRC` / `check-id SRC-024` / `dupes sources/source_index.md` | 採番・重複の検査 |

`--text` は `\n` で改行、`@path` でファイルから。`--help` は UTF-8 で出る（cp932 の端末でも落ちない）。
**`statekit.py` のソースを読んで使い方を調べない** ─ 1 ターンで 6〜14 回読まれた実例がある。

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
| `### Relocation check` | **内容を他スライドへ移す・案内する決定では必須** | 下記 |
| `### Related files` | ✔ | 変更したファイル |

`### Relocation check` は、「この内容は Slide NN に移した／Slide NN を参照」と書く決定で必ず埋める。
「移した」と書いたのに移す先に無かった、移す先の例が別の主語・別の違反だった、の 2 つの事故を防ぐ。

```markdown
### Relocation check
* 移す先 / 案内先: Slide 019
* そこにある該当の文言（逐語。storyboard の要約ではなく PNG か原本で確認）: 「…」
* 案内元の主語・違反 → 案内先の主語・違反の対応: 指示した側（44条後半）→ 指示した側（44条後半）✔
* 確認方法: deck.pptx 全文検索（`inspect_deck.py`）で「勧告」が Slide 019 に 1 件
```

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

**スライドが逐語に依拠する出典では `### Verbatim quotes` が必須**（`templates/source-entry.md`）。
逐語は、生の HTML・PDF の原本画像・ソースコードで照合したものだけを載せ、要約と同じ節に混ぜない。
索引の誤りは grep では防げず、原文に当たるしかない（索引に「ページに無い文」が逐語の顔で入り、
キーメッセージがそれに乗った実例がある）。否定の主張の根拠は `### Absence claims` に、
位置と確認日つきで書く。

**同じURLを再調査した場合は新規IDを作らず、既存項目の `### Update history` に追記する。**

* **採番の前に未使用を確かめる**: `grep -c "^## SRC-0NN" sources/source_index.md` が 0、または
  `scripts/statekit.py next-id SRC`。採番の重複（同じ ID に 2 文書）は読者が出典を一意に引けなくする。
* 並行調査では ID の範囲を分けても同じ文書の重複登録は防げない。マージ時に
  `scripts/statekit.py dupes sources/source_index.md` で URL の重複を検出する。
* 実測・実験の結果（この PC で再現した挙動）も `SRC-NNN`（Source type: 検証結果）で登録する。
  環境・日付・手順・結果を書く。別の ID 系列は作らない。

詳細な項目定義は `templates/source-entry.md`。

---

## `notes/glossary.md`

5列の表1つ＋ `## Writing rules`。

```markdown
| Term | Full name | Definition | Related terms | Source |
```

`## Writing rules` には、標準の用語を採るときに現場の語を初出で併記する方針を書く
（`editorial-rules.md`）。スライド上の用語集は 用語｜定義｜根拠・参照（9pt）の 3 列
（`visual-design.md` §5）。

---

## `notes/findings.md`

`templates/finding-entry.md` の `FINDING-NNN` 形式が正式。
ただし調査量が多い場合は**技術トピック単位の見出し**で構成し、
見出しに根拠の `SRC-NNN` を併記する運用でもよい（実運用ではこちらが多い）。
どちらの形式でも、**確認済みの事実 / 推論 / 未確認**の区別は必ず明示する。
