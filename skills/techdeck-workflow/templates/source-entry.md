# Source Entry Template

<!--
使用方法:
- このテンプレートを複製し、sources/source_index.md に追記する。
- 同じURLがすでに登録されていないことを確認する（`scripts/statekit.py dupes sources/source_index.md`）。
- Source IDは既存の最大番号に続く連番とする。**採番の前に、その番号が未使用であることを
  grep で確かめる**（`scripts/statekit.py next-id SRC`）。二重採番の実例がある。
- 不明な項目を推測で埋めず、「未確認」と記載する。
- 逐語（`### Verbatim quotes`）は、生の HTML・PDF の原本画像・ソースコードで照合したものだけを
  載せる。WebFetch は言い換えることがある。要約と逐語を同じ節に混ぜない。
-->

## SRC-XXX: 情報源のタイトル

### Basic information

| Item           | Value                     |
| -------------- | ------------------------- |
| Source ID      | `SRC-XXX`                 |
| Title          |                           |
| URL / Path     |                           |
| Provider       |                           |
| Author         |                           |
| Source type    |                           |
| Published      |                           |
| Updated        |                           |
| Checked        | YYYY-MM-DD                |
| Target product |                           |
| Target version |                           |
| Language       |                           |
| Reliability    | `High` / `Medium` / `Low` |

### Source type

該当するものを記載する。

* 公式仕様書
* 標準文書
* 公式ドキュメント
* 公式APIリファレンス
* 公式ソースコード
* 公式ブログ
* リリースノート
* 論文
* 書籍
* 技術記事
* Q&A
* 検証結果
* その他

### Summary

この情報源の目的と、扱っている技術テーマを要約する。

外部ページの文章をそのまま転載せず、情報源の位置づけが分かるように記載する。

### Key technical points

この情報源から確認できる重要な技術的事実を記載する。

**ここは要約である。** 逐語は下の `### Verbatim quotes` に分ける。逐語に見える要約
（「5秒の意味は『…』」）を書かない ─ 索引に「ページに無い文」が逐語の顔で入り、
キーメッセージがそれに乗った実例がある。grep は索引の誤りを通す。

*
*
*

### Verbatim quotes

**スライドがこの出典の文言に依拠する場合は必須。** 原文のまま（翻訳しない。省略は `…` で示す）。
`確認方法` は 生HTML（curl） / PDF原本画像（ページ） / ソースコード（tag・行） のいずれか。
WebFetch の出力・検索結果の抜粋・自分の記憶は確認方法にならない。

| # | 逐語（原文のまま） | 位置（見出し／ページ／行） | 確認方法 | 確認日 |
| - | ------------------ | -------------------------- | -------- | ---------- |
| 1 |                    |                            |          | YYYY-MM-DD |

画像 PDF（通達・様式）は、該当ページを描画して**段落を全部**転記してから抜粋する。
段落の一部だけを写した要約が `CRITICAL` の原因になった。

### Absence claims

「この出典には〜が書かれていない」を根拠に使う場合に記載する。不在は逐語で示せないので、
**探した範囲と時点**が根拠になる（`editorial-rules.md`、ルーブリック `R1-A-6`）。

| 主張（〜が無い） | 探した範囲（位置） | 確認日 | 代わりの根拠（機構での説明など） |
| ---------------- | ------------------ | ---------- | -------------------------------- |
|                  |                    | YYYY-MM-DD |                                  |

### Verification record

Source type が **検証結果**（この PC での実測・再現実験）の場合に記載する。
レビュー担当や作成担当の実測を根拠にするときは、オーケストレータが**取り直して**ここに残してから
storyboard に書く。

* 環境（OS / 製品と版 / シェル）:
* 日付:
* 手順（再現コマンド）:
* 結果（出力・観測）:
* 取得者:

### Preconditions

この情報源の説明が成立する前提条件を記載する。

* 対象環境:
* 必要な設定:
* 必要な依存関係:
* その他:

### Constraints and exceptions

情報源に記載されている制約、例外、未対応条件を記載する。

*
*
*

### Version-specific behavior

バージョンによって挙動が異なる場合に記載する。

| Version | Behavior | Notes |
| ------- | -------- | ----- |
|         |          |       |

該当しない場合:

`特に確認されていない`

### General specification or implementation-specific

この情報が次のどれに該当するかを記載する。

* 一般仕様
* 特定実装
* 特定製品
* 特定バージョン
* 検証環境固有
* 判別不能

#### Details

一般仕様と実装依存を区別するための補足を記載する。

### Evidence locations

情報源内の具体的な確認位置を記載する。

| Location               | Confirmed content |
| ---------------------- | ----------------- |
| セクション名、見出し、行番号、ページ番号など |                   |
|                        |                   |

画像 PDF は「p.N の第2段」のように段落まで位置を書く。文字 PDF と違い grep できないので、
位置が無いと再確認できない。

### Code, diagrams, and tables

#### Code

* 対象コード:
* 読み取れる内容:
* 注意点:

#### Diagrams

* 図番号または名称:
* 読み取れる内容:
* 本文との関係:

#### Tables

* 表番号または名称:
* 読み取れる内容:
* 適用条件:

### Applicable technical topics

この情報源を、資料内のどの技術項目に使用できるかを記載する。

*
*
*

### Slide candidates

この情報源から作成できそうなスライド要素を記載する。

* 説明候補:
* 比較表候補:
* コード候補:
* UML図候補:
* その他の技術図候補:

### Related sources

| Source ID | Relationship      |
| --------- | ----------------- |
| `SRC-XXX` | 補足、整合、矛盾、旧バージョンなど |
|           |                   |

### Conflicts

他の情報源と矛盾する場合に記載する。

#### Conflicting content

*

#### Possible reason

* バージョン差
* 一般仕様と実装差
* 誤記
* 適用条件の違い
* 未確認

#### Required investigation

*

### Reliability assessment

この情報源の信頼度を評価した理由を記載する。

#### Positive factors

*
*

#### Limitations

*
*

### Caveats

資料で使用する際の注意点を記載する。

* 情報の古さ:
* バージョン依存:
* 実装依存:
* 検証不足:
* その他:

### Open questions

この情報源だけでは確認できない内容を記載する。

*
*
*

関連するOpen Question:

* `OQ-XXX`

### Usage policy

この情報源を資料でどのように扱うかを記載する。

* 主要な根拠として使用する
* 補足情報として使用する
* 実装例として使用する
* 比較対象として使用する
* 古い仕様の説明として使用する
* 未確認のため現時点では使用しない

### Update history

| Date       | Change | Reason |
| ---------- | ------ | ------ |
| YYYY-MM-DD | 初回登録   |        |
