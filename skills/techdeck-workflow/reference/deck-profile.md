# デッキプロファイル（deck-profile.json）

案件ごとの**見た目と言語の設定**を1ファイルに集約する。
スキル本体は案件に依存しない。案件固有の値はすべてここに置く。

配置: `slides/deck-profile.json`（案件側。スキル側ではない）

## スキーマ

```json
{
  "language": "ja",
  "geometry": { "width_in": 10, "height_in": 5.625 },
  "fonts": { "sans": "Calibri", "mono": "Courier New", "cjk": "Yu Gothic" },
  "palette": {
    "bg": "151124", "card": "1E1838", "rule": "3C3463",
    "text": "ECEAF7", "muted": "9C95BC", "dim": "6E6A8A",
    "accent_green": "34E2B0", "accent_amber": "FFB454",
    "accent_purple": "B89CFF", "accent_pink": "FF7597",
    "highlight": "4A3A12"
  },
  "code_theme": "vscode-dark-plus",
  "conventions": [
    "バッジ: 要点=amber / 注意=pink / 次章=green",
    "出典はスライド下部に SRC-NNN で表示する",
    "コード断片は mono。本文中の識別子も mono"
  ],
  "source_notation": "SRC-NNN",
  "id_prefixes": {
    "finding": "FINDING", "source": "SRC",
    "decision": "DEC", "question": "OQ", "comment": "CMT"
  }
}
```

## 各項目

| キー | 用途 | 消費者 |
| --- | --- | --- |
| `language` | デッキ本文・状態ファイル・レビュー記録の言語 | エージェント |
| `geometry` | スライド寸法（インチ）。座標計算の基準 | `deckkit` / `new_deck.py` / `check_deck.py` |
| `fonts` | 欧文 sans / 等幅 / 和文 / 見出し。CJK を含むテキストは `cjk` を使う | エージェント / `check_deck.py` |
| `palette` | 配色。**ここに無い色を使わない**。`bg` と `text` は必須 | `new_deck.py` / `check_deck.py` が検査 |
| `palette.highlight` | 蛍光ペンの色（`R(..., hl=...)`）。**背景側**なので、その上に載る文字色とのコントラストで選ぶ。dark と light で明暗が逆になる | エージェント |
| `code_palette` | コード断片のトークン色（keyword / function / type / string / number / comment 等） | **`codehl.highlight()` が適用**、`check_deck.py` が `palette` と合わせて検査 |
| `code_theme` | コード断片のハイライト方針の名前 | エージェント |
| `visual` | 視覚設計の数値（下記） | エージェント / `check_deck.py` |
| `conventions` | 機械検査できない約束事。散文でよい | エージェント |
| `source_notation` | スライド上の出典表記 | エージェント |
| `id_prefixes` | ID 体系の接頭辞 | エージェント |

### 任意キー `visual`

視覚設計の数値。省略時は下記の既定値。規定そのものは `reference/visual-design.md`。

```json
"visual": {
  "key_message_max_lines": 2,
  "key_message_max_chars": 30,
  "body_char_budget": 450,
  "emphasis_budget": 3,
  "size_ladder": { "key": 24, "heading": 18, "body": 12, "note": 10, "source": 9 }
}
```

| キー | 既定 | 意味 | 消費者 |
| --- | --- | --- | --- |
| `key_message_max_lines` | `2` | キーメッセージの行数上限 | エージェント |
| `key_message_max_chars` | `30` | 1行の全角文字数の目安 | エージェント |
| `body_char_budget` | `450` | 1スライドの総文字数の目安 | `check_deck.py` |
| `emphasis_budget` | `3` | 1スライドの文中強調の箇所数 | `check_deck.py` |
| `size_ladder` | 上記 | 役割ごとのpt。**隣の段と1.25倍以上離す** | エージェント |

`size_ladder` の既定は **13.33×7.5in** 用。**10×5.625in では 0.72 倍**が目安
（key 18 / heading 14 / body 9 / note 8 / source 7）。
`geometry` を変えたらここも変える ─ **連動しない。**

`check_deck.py --profile` は `body_char_budget` と `emphasis_budget` を推定で検査し、
`MEDIUM`/`LOW` で報告する（終了コードは変えない）。`--no-visual` で切れる。

### 任意キー `batch`

Phase 3 のバッチ作成とレビューループの調整。省略時は下記の既定値。

```json
"batch": {
  "unit": "chapter",
  "max_slides_per_wave": 8,
  "max_iterations": 3,
  "review_concurrency": 4
}
```

| キー | 既定 | 意味 |
| --- | --- | --- |
| `unit` | `chapter` | バッチの既定単位。`single` にすると常に単枚モード |
| `max_slides_per_wave` | `8` | 1波で作るスライド数。波の間に状態を保存する |
| `max_iterations` | `3` | スライドあたりの review 回数の上限 |
| `review_concurrency` | `4` | 並列に走らせる評価用エージェントの数 |

`max_slides_per_wave` はバッチではなく**波**の上限。14枚の章は1バッチ・2波になる。

`palette` と `code_palette` は**別グループだが同格**に扱われる。
`check_deck.py` はデッキ中の色がどちらかに含まれることを検査するので、
コードのトークン色を `palette` 側に混ぜる必要はない。

`check_deck.py --profile <path>` が `geometry` / `palette` / `fonts` を機械検査する。
`conventions` はエージェントが散文として読む。

## 新規案件での作り方

**Phase 0 が自動で行う。** `init_project.py --preset dark|light` が
`new_deck.py --write-profile` 経由で `slides/deck-profile.json` を書き出す。

手動で用意する場合:

1. `pptx-toolkit/templates/presets/dark.json`（または `light.json`）をコピーして値を差し替える。
2. 既存デッキから起こす場合は `check_deck.py <deck.pptx> --infer-profile` で雛形を生成し、
   最頻出の色・フォント・寸法から出発する（**既存デッキが必要**）。

## プリセット

| プリセット | bg | text | highlight | 想定 |
| --- | --- | --- | --- | --- |
| `dark`（既定） | `151124` | `ECEAF7` | `4A3A12` (9.3:1) | 画面閲覧。コード断片の多い技術資料 |
| `light` | `FBFAFD` | `1B1524` | `FFEFA8` (15.4:1) | 印刷・明るい環境 |

**`highlight` は accent と同じく共有できない。** ライトテーマの淡い黄色を
ダークテーマに持ち込むと、その上の淡色文字が読めなくなる。ダークでは
「暗いマーカー」になる ─ 直感に反するが、文字とのコントラストが基準である。

**accent はプリセット間で共有できない。** `34E2B0` は dark の bg 上で 11:1 だが、
白地では約 1.5:1 で読めない。各プリセットは自分の背景に対して検証した値を持つ。

`card` と `bg` の明暗関係も**反転する**（dark では card が明るい、light では暗い）。
自前のプリセットを作る場合はここを間違えやすい。

## `dark` プリセットの実値

上のスキーマ例がそのまま `dark` の値。10×5.625in、和文 Yu Gothic。
バッジは 要点=amber / 注意=pink / 次章=green。
コードは VSCode Dark+ 相当（キーワード `569CD6` / 関数 `DCDCAA` / 文字列 `CE9178` /
型 `4EC9B0` / 数値 `B5CEA8` / 既定文字 `D4D4D4`）。
