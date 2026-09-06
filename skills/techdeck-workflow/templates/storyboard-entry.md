# Storyboard Entry Template

<!--
使用方法:
- このセクションを複製し、slides/storyboard.md に追記する。
- Phase 3で追加判断をせずにスライドを作成できる程度まで具体化する。
- スライド本文に必要な説明を、単語だけで済ませない。
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
* 想定文字数（予算 `visual.body_char_budget`、既定450字）:

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

### Screenshot

スクリーンショットを使用する場合に記載する。

* Purpose:
* Source file:
* Target area:
* Annotation:
* Masking required:
* Version:

### Sources

| Source ID | Used for |
| --------- | -------- |
| `SRC-XXX` |          |
|           |          |

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
* Content retained on this slide:
* Content moved to new slide:
* Impact on following slides:

### Approval record

* Approved by:
* Approved date:
* Approval comment:

