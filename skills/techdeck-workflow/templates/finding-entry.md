# Finding Entry Template

<!--
使用方法:
- このテンプレートを複製し、notes/findings.md に追記する。
- 情報源ごとの要約ではなく、技術項目ごとに複数の出典を統合する。
- 確認済みの事実、推論、未確認事項を明確に区別する。
-->

## FINDING-XXX: 調査項目名

### Status

`CONFIRMED` / `PARTIALLY_CONFIRMED` / `DISPUTED` / `DRAFT`

### Conclusion

この調査から確認できた結論を、最初に簡潔に記載する。

結論には、必要に応じて次を含める。

* 何が起きるか
* どの条件で成立するか
* 何に依存するか
* どの範囲まで確認済みか

### Scope

この調査結果が扱う範囲を記載する。

* 対象製品:
* 対象機能:
* 対象環境:
* 対象バージョン:
* 対象実装:
* 対象外:

### Background

この技術が必要になった背景、解決する問題、導入理由を記載する。

### Terminology

この調査項目を理解するために必要な用語を記載する。

| Term | Definition | Related glossary entry |
| ---- | ---------- | ---------------------- |
|      |            |                        |

### Technical details

技術的な仕組みを十分な説明で記載する。

必要に応じて、次の観点を含める。

* 構成要素
* 責務
* データ構造
* 呼び出し関係
* 状態管理
* 並行性モデル（スレッド / イベントループ / 非同期タスク等）
* ライフサイクル
* 入力と出力
* 失敗時の動作

### Components

| Component | Type | Responsibility | Lifetime | Notes |
| --------- | ---- | -------------- | -------- | ----- |
|           |      |                |          |       |

### Processing flow

処理の開始から終了までを順序立てて記載する。

1.
2.
3.

必要に応じて、分岐を記載する。

```text
開始
  ↓
条件A
  ├─ 成立 → 処理B
  └─ 不成立 → 処理C
```

### Inputs and outputs

| Item | Input / Output | Type | Description |
| ---- | -------------- | ---- | ----------- |
|      |                |      |             |

### State and lifecycle

状態を持つ技術の場合に記載する。

| State | Meaning | Entry condition | Exit condition |
| ----- | ------- | --------------- | -------------- |
|       |         |                 |                |

### Preconditions

この仕組みが成立するための前提条件を記載する。

*
*
*

### Normal behavior

正常系の動作を記載する。

*
*
*

### Constraints

技術上または仕様上の制約を記載する。

*
*
*

### Exceptions and failure behavior

例外条件、失敗条件、エラー処理を記載する。

| Condition | Behavior | Recovery | Notes |
| --------- | -------- | -------- | ----- |
|           |          |          |       |

### Version differences

| Version | Behavior | Source    | Notes |
| ------- | -------- | --------- | ----- |
|         |          | `SRC-XXX` |       |

### Implementation-dependent behavior

特定の製品、ライブラリ、プラットフォーム、実装に依存する内容を記載する。

#### General behavior

一般仕様として確認できる内容を記載する。

#### Specific implementation

特定実装でのみ確認できる内容を記載する。

#### Boundary

一般仕様と実装依存の境界を記載する。

### Similar concepts

| Concept | Similarity | Difference | When to use |
| ------- | ---------- | ---------- | ----------- |
|         |            |            |             |

### Common misunderstandings

読者が誤解しやすい内容を記載する。

| Misunderstanding | Correct explanation |
| ---------------- | ------------------- |
|                  |                     |

### Evidence

この結論の根拠を記載する。

| Source ID | Evidence | Reliability         |
| --------- | -------- | ------------------- |
| `SRC-XXX` |          | High / Medium / Low |
|           |          |                     |

### Inference

出典に直接記載されておらず、複数の事実から導いた推論がある場合に記載する。

#### Inferred conclusion

*

#### Supporting evidence

* `SRC-XXX`
* `SRC-YYY`

#### Confidence

`High` / `Medium` / `Low`

推論がない場合:

`なし`

### Code and verification

#### Related sample

* Sample name:
* Path:
* Purpose:

#### Verification environment

* OS:
* Runtime:
* Language version:
* Library version:
* Build tool:
* Other conditions:

#### Execution command

```bash
# 実行コマンド
```

#### Expected result

```text
期待する結果
```

#### Actual result

```text
実際の結果
```

#### Verification conclusion

検証によって何を確認できたかを記載する。

#### Unverified areas

*
*

### Diagram candidates

#### Diagram 1

* Type:
* Purpose:
* Scope:
* Elements:
* Relationships:
* Reading order:
* Simplifications:
* Source IDs:
* Proposed file:

  * `assets/diagrams/<name>.puml`
  * `assets/diagrams/<name>.svg`

必要に応じて追加する。

### Slide candidates

#### Candidate slide 1

* Technical topic:
* Main conclusion:
* Required explanation:
* Diagram:
* Code:
* Constraints:
* Sources:

### Impact on document structure

この調査結果が資料構成に与える影響を記載する。

* 新しいスライドが必要
* 既存スライドへ追記
* 既存構成の分割が必要
* 付録へ配置
* 資料対象外
* 追加調査後に判断

### Open questions

関連する未確認事項を記載する。

* `OQ-XXX`:
*

### Related decisions

* `DEC-XXX`

### Related findings

* `FINDING-XXX`

### Change history

| Date       | Change | Related source |
| ---------- | ------ | -------------- |
| YYYY-MM-DD | 初回登録   | `SRC-XXX`      |
