# Storyboard Entry Template

<!--
使用方法:
- このセクションを複製し、slides/storyboard.md に追記する。
- Phase 3で追加判断をせずにスライドを作成できる程度まで具体化する。
- スライド本文に必要な説明を、単語だけで済ませない。
- 節は「今の仕様 1 つ」に保つ。レビュー後の変更は `### Spec changes` に書き、本文の欄は
  **書き換える**（新しい欄を上に積んで古い欄を残さない）。無効になった欄は消す。
  スライドが `AWAITING_REVIEW` になったら節を畳み直し、変更の履歴はレビュー記録へ移す。
- 座標・寸法は生成器の入力（関数と引数）で書く。丸めた派生値を書かない。
-->

## Slide NNN: スライドタイトル

### Status

`NOT_STARTED`

使用可能な状態:

* `NOT_STARTED`
* `DRAFTING`
* `AWAITING_REVIEW`
* `REVISION_REQUIRED`
* `APPROVED`
* `BLOCKED`

### Current spec

この節の**今の仕様**を 5 行以内で要約する（キーメッセージ／支配的要素／図の種類／出典／字数の余裕）。
変更の欄が 2 つ以上になったら必須。作成担当とレビュー担当はまずここを読む。

*

### Section

* Section name:
* Position in section:
* Previous slide:
* Next slide:

### Technical purpose

このスライドで読者に理解させる技術内容を記載する。

### Reader outcome

このスライドを読み終えた読者が、何を説明または判断できるようになるかを記載する。

### Reader prerequisites

このスライドを理解するために必要な前提知識を記載する。

*
*
*

### Main conclusion

このスライドから読み取るべき最も重要な技術的結論を記載する。
**長さの制限はない。** これは設計上の結論であって、スライドに載せる文ではない。

### Key message

**スライド上端に実際に載せる文。** `Main conclusion` とは別物である
（両者を混同すると、89字の技術的結論がそのままスライドに載り、
PowerPoint が中途半端な位置で折り返す ─ 実際に起きた）。

規定は `reference/visual-design.md` §3。既定は **2行以内・1行あたり全角30字以内**。

**実際の改行位置で行を分けて書く。** builder はこの行を1行=1段落として描き、
自動折り返しに任せない。強調する語を `**` で囲む（**1〜3語**）。

```text
行1: 二重派遣のリスクは **刑事・行政・民事** の3軸。
行2: 罰則は **行為者個人にも** 及ぶ。
```

* 強調語と、使う色（`deck-profile.json` の `conventions` に従うこと）:

| 強調語 | 色 | 理由 |
| --- | --- | --- |
| 刑事・行政・民事 | `text_bright` | 中立の列挙。法的状態を表さない |
| 行為者個人にも | `accent_red` | 違法・重大リスクを示す |

### Scope

#### Included

*
*

#### Excluded

*
*

### Target environment

* Product:
* Platform:
* Language:
* Library:
* Version:
* Implementation:

### Body content

スライド本文に記載する説明を、実際に作成可能な粒度で整理する。

#### Definition

必要な用語や概念の定義を記載する。

#### Background

この技術が必要な理由や、解決する問題を記載する。

#### Mechanism

技術的な仕組みを記載する。

#### Processing flow

1.
2.
3.

#### Preconditions

*
*

#### Constraints

*
*

#### Exceptions

*
*

#### Practical implications

実務でどのような判断や注意につながるかを記載する。

### Visual hierarchy

`reference/visual-design.md` §1・§2・§5 に従って記載する。

* 支配的要素（この1つが最も目を引く）: キーメッセージ / 図 / 表 / コード
* 3秒で読者が持ち帰る1点:
* 本文に書かず**図・ピクトグラムで表す**内容:
* 使用するピクトグラム（`pictogram.names()` の名前で）:
* 想定文字数（`visual-design.md` §5 の数え方。本文のみ）:
* 余裕（字）: 予算 − 想定文字数。**計画は上限の 70〜75%**（450字なら 315〜340字）。
  レビューの直しは文を足す方向に働くので、残りはそのために取っておく
* 余裕（in）: 本文領域の高さ − 試し組みの実測（Phase 3 の試し組み後に埋める）
* 数えないもの（名札・出典行・ナビ・参照列。`visual.uncounted` の接頭辞で名前を付ける）:

### Layout concept

* Layout type:
* Main area:
* Secondary area:
* Footer:
* Reading order:

例:

```text
┌─────────────────────────────────────┐
│ タイトル                              │
├──────────────────┬──────────────────┤
│ 技術説明          │ UMLシーケンス図   │
│                  │                  │
├──────────────────┴──────────────────┤
│ 注意点・出典                          │
└─────────────────────────────────────┘
```

### Diagram

#### Diagram type

次のいずれか、または適切な技術図を指定する。

* UMLクラス図
* UMLシーケンス図
* UML状態遷移図
* UMLアクティビティ図
* UMLコンポーネント図
* UML配置図
* ER図
* C4モデル
* データフロー図
* タイミング図
* 比較表
* 概念図
* なし

#### Purpose

この図で何を理解させるかを記載する。

#### Scope

図が表す範囲を記載する。

#### Elements

| Element | Type | Description |
| ------- | ---- | ----------- |
|         |      |             |

#### Relationships or messages

| From | To | Relationship / Message | Condition |
| ---- | -- | ---------------------- | --------- |
|      |    |                        |           |

#### Reading order

図をどの順番で読むかを記載する。

1.
2.
3.

#### Simplifications

図で省略する要素と、省略してよい理由を記載する。

*
*

#### UML notes

* 使用するUML記法:
* 同期・非同期の区別:
* 戻り値の表現:
* 分岐:
* ループ:
* 並行処理:
* 状態・イベント・ガード:

#### Source files

* Editable source:

  * `assets/diagrams/<diagram-name>.puml`
* Rendered asset:

  * `assets/diagrams/<diagram-name>.svg`
* 生成器と入力（Python で描く図の場合）:

  * `assets/diagrams/<module>.py` の `draw_<name>(slide, prof, variant=...)`。
    **位置と寸法は生成器の入力で書く**（`h=2.30`）。丸めた派生値（`y=2.540`）を書くと、
    書いたとおりに描いた図が承認済みの図とずれる。派生値を書くなら EMU で。
    複数スライドで共有する図は、座標引数も pt 引数も取らないモジュールにする
    （呼び出し側に上書きの余地が無いことが、画素一致の保証になる）。

### Code

#### Purpose

コードを掲載する理由を記載する。

#### Related sample

* Sample name:
* File:
* Symbol:
* Related test:

#### Included range

掲載するクラス、関数、行、処理範囲を記載する。

#### Omitted range

省略する部分と、その内容を記載する。

#### Focus points

読者に注目させる箇所を記載する。**行番号で指定する**（`codehl` の `mark_lines`）。

* Language (`codehl` の言語名):
* mark_lines:
* 注目させる理由:

1.
2.
3.

#### Conclusion from code

コードから何が読み取れるかを記載する。

### Table

表を使用する場合に記載する。

* Purpose:
* Rows:
* Columns:
* Comparison axes:
* Source:

用語集・根拠の表は **用語｜定義｜根拠・参照（9pt）** の 3 列を既定とする。
参照列は文字数予算の外（`visual-design.md` §5）。定義の文の中に条番号・参照を埋め込まない。

### Screenshot

スクリーンショットを使用する場合に記載する。

* Purpose:
* Source file:
* Target area:
* Annotation:
* Masking required:
* Version:

### Sources

| Source ID | Used for | 依拠する逐語（`### Verbatim quotes` の #） |
| --------- | -------- | ------------------------------------------ |
| `SRC-XXX` |          |                                            |
|           |          |                                            |

発注文はこの表を**参照させる**（「storyboard の `### Sources` に従うこと」）。出典の本文や
`SRC-NNN` の一覧を発注文に転記しない ─ この表を直した直後の発注文に古い番号を書いた実例がある。

### Source notation on slide

スライド上での出典表記方法を記載する。

* フッターにSource IDを記載
* 付録の出典一覧へリンク
* URLを記載
* その他:

### Previous slide relationship

前のスライドから何を引き継ぐかを記載する。

### Next slide relationship

次のスライドへ何を引き渡すかを記載する。

### Speaker notes

発表者向けの補助情報のみを記載する。

技術理解に必要な説明は、原則としてスライド本文へ含める。

### Accessibility and readability

* 色だけで意味を表していない:
* 図中の文字サイズ:
* コードの文字サイズ:
* 読み順:
* コントラスト:
* その他:

### Review focus

ユーザーに特に確認してほしい点を記載する。

* 技術的な正確性
* 説明の深さ
* 図の種類
* UML記法
* 図の抽象度
* コード掲載範囲
* 情報量
* レイアウト
* 前後スライドとのつながり

### Spec changes

レビューの指摘や判断を受けて**オーケストレータが書き足す・書き換える文**は、新しい内容として
扱い、ここに 1 件ずつ記録してから本文の欄を書き換える。急いで書いた直しの文が次の `HIGH` を
作った実例が 1 バッチで 7 件ある。6 点検をすべて埋められない文は書かない。

#### Change 1（iter N / FINDING-NNN への対応）

* 変更した欄:
* 新しい文: 「」
* 元の文（あれば）: 「」
* 点検:
  - [ ] (1) 主張を一次資料で確かめた（`SRC-NNN` の `### Verbatim quotes` #、またはコードの行）
  - [ ] (2) 言い換えが原文の意味を保っている（原文: 「」）
  - [ ] (3) 設定・既定に触れる文は、オンとオフの両方で成り立つ
  - [ ] (4) 新しい語に、同じページの説明か参照がある
  - [ ] (5) 同じスライドの例・図・コードと食い違わない
  - [ ] (6) スライドの実物（PNG・run）を見て書いた
* レビュー担当の文例を採った場合: 文例は「直し方の一案」であり検証済みの文言ではない。
  (1)〜(6) と横断ルールに照らしてから採る。照らした結果:

### Derived from

派生資料（発表版・要約版）のスライドで、元の資料の文を短くしたときに記載する。
短くするたびに限定語（「〜事業を」「〜の人に」「自分の」）が落ちて `HIGH` になった実例が 3 回ある。

| 元の文（詳細版 Slide NN） | この資料の文 | 条件・主体・対象の照合 |
| ------------------------- | ------------ | ---------------------- |
|                           |              | ✔ / 落ちた語:          |

### Known risks

*
*

### Open questions

* `OQ-XXX`
*

### Related decisions

* `DEC-XXX`

### Split proposal

1枚に収まらない可能性がある場合に記載する。

* Split required: Yes / No / Undecided
* Reason:
* 余裕（字 / in、試し組みの実測）:
* 同じバッチで上限に近い他のスライド（分割・移動は**まとめて**決め、番号の付け替えを 1 回にする）:
* Content retained on this slide:
* Content moved to new slide:
* Impact on following slides:
* 承認済みスライドのページ番号への影響:

### Approval record

* Approved by:
* Approved date:
* Approval comment:

