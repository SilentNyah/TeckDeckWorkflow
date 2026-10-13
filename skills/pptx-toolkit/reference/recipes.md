# バッチ編集のレシピ

編集は使い捨てスクリプトに書く。1ラウンド＝1〜数本。
実例は `history/`（実プロジェクトで実際に走らせたスクリプト。パスは匿名化してある）。

## 新規デッキ / 新規スライド

デッキ自体を作るのは CLI の仕事。**素の `Presentation()` を書かない**（gotcha 8）。

```text
python new_deck.py slides/deck.pptx --preset dark --write-profile slides/deck-profile.json
```

既存デッキにスライドを足す場合:

```python
from deckkit import load_profile, use_defaults, add_slide, textbox, rrect, arrow, R

PROF = load_profile(r'...\slides\deck-profile.json')
PAL = PROF['palette']
use_defaults(text=PAL['text'], rule=PAL['rule'])   # ← light プリセットでは必須
BG, CARD, RULE = PAL['bg'], PAL['card'], PAL['rule']

s = add_slide(prs, bg=BG)
```

`use_defaults` を呼ばないと、色を省略した `R()` は**ダークテーマ既定の白**を返す。
light プリセットではそれが白地に白文字になる。

---

## 骨格

```python
# -*- coding: utf-8 -*-
"""rNNN Batch A: slides 16, 20, 22 -- 何をするか1行で。"""
import sys
sys.path.insert(0, r'<pptx-toolkit>/scripts')
from pptx import Presentation
from deckkit import (R, set_runs, set_para, shape_by_id, el_by_id, set_xfrm,
                     rrect, textbox, arrow, connector, move_before, save_backup,
                     load_profile, use_defaults,
                     slide_fingerprints, assert_untouched, save_replace)

DECK = r'<project>\slides\deck.pptx'
TARGET = {16, 20, 22}                 # このスクリプトが触ってよい位置（1-based）
save_backup(DECK)                     # ← 最初に必ず
BEFORE = slide_fingerprints(DECK)     # ← 守り 4 の「前」
prs = Presentation(DECK)
def S(n):                             # 1-based。対象外なら止まる（守り 1）
    assert n in TARGET, 'slide %d is outside TARGET' % n
    return prs.slides[n - 1]

PAL = load_profile(r'<project>\slides\deck-profile.json')['palette']
use_defaults(text=PAL['text'], rule=PAL['rule'])

MONO, SANS = 'Courier New', 'Calibri'
LIGHT, MUTED, DIM = PAL['text'], PAL['muted'], PAL['dim']
GREEN, AMBER = PAL['accent_green'], PAL['accent_amber']
PURPLE, PINK = PAL['accent_purple'], PAL['accent_pink']

# ---------------- slide 22 : CMT-rNNN-003 ----------------
set_runs(shape_by_id(S(22), 44), [[
    R('一般のアプリコードでは使わない。', 7.6, PINK, SANS, b=True),
]])

save_replace(prs, DECK)                                   # 一時ファイル → 置き換え（守り 3）
assert_untouched(BEFORE, slide_fingerprints(DECK), TARGET)  # 対象外は XML まで同一（守り 4）
print('Batch A saved')
```

規約:

* **1スクリプト = 1バッチ**。スライド番号とコメントIDをコメントに書く。あとで追跡できる。
* **4 つの守りを省かない**（対象外を拒む／枚数とタイトルを確かめる／一時ファイルから置き換える／
  対象外が XML まで同一か確かめる）。雛形は `templates/edit-script.py`。守りがあると、
  API の上限で途中で止まっても保存の状態が確かで、続きから終えられる。
* **編集は 1 件ずつ関数にして順に実行し、進み具合をファイルに書く。** 途中で落ちたら、
  再実行ではなく「何を書くはずだったか」の一覧（`EDITS`）から再開する。
  5 件まとめた置換の 4 件目で例外 → 再実行で 1 件入れ忘れ、という実例がある。
* 字数の予算に入れない文字（タイトル・章ラベル・出典行・ナビ・図の名札・参照列・凡例の頭）は
  `textbox(..., name='label:…')` / `shape(..., name='src:…')` のように**役割名を付ける**。
  `check_deck.py` はその接頭辞（`visual.uncounted`）の図形を数えない。
* 実行後は必ず `render_deck.py` で目視確認。`check_deck.py` はその前に。
* 失敗したら `save_backup` の戻り値から戻す。
* **Markdown の状態ファイル（storyboard / review_state / source_index）は、この骨格で触らない。**
  `str.replace` を連ねて末尾で書き込む形は、1 件目の成功を見せたまま 2 件目で落ち、
  何も書かれない。`techdeck-workflow/scripts/statekit.py` を使う（節の境界・1 回一致・
  改行コードを機械が守る）。

---

## よく使う操作

### テキストの一部だけ差し替える

```python
for pa in shape_by_id(S(34), 22).text_frame.paragraphs:
    for r in pa.runs:
        if r.text == '// リンク切断':
            from pptx.dml.color import RGBColor
            r.font.color.rgb = RGBColor.from_string(GREEN)
```

`set_runs` は書式ごと作り直す。**既存の書式を保ちたいときは run を直接触る。**

### 段落単位の入れ替え（コードブロックの1行だけ直す等）

```python
set_para(shape_by_id(S(31), 6), 9, [
    R('isActive', 9.5, GREEN, MONO),
    R(' ＝ ', 9.0, MUTED, SANS),
    R('coroutineContext[Job]?.isActive', 7.6, GREEN, MONO),
    R(' の短縮', 9.0, MUTED, SANS),
])
```

`endParaRPr` を壊さない（gotcha 3）。段落番号は `inspect_deck.py --runs` で確認する。

### 図の左右を入れ替える

```python
set_xfrm(el_by_id(s, 15), x=0.80)     # 文字
set_xfrm(el_by_id(s, 14), x=0.80)     # ← 枠も忘れずに（gotcha 6）
```

枠とテキストが別シェイプなので**両方**動かす。`inspect_deck.py` で同座標の id を確認。

### 矢印を引く

```python
arrow(s, 3.0, 2.4, 6.5, 2.4)                    # --> 矢じりは (6.5, 2.4)
arrow(s, 6.5, 3.2, 3.0, 3.2, color=PINK)        # <-- 矢じりは (3.0, 3.2)
arrow(s, 4.0, 5.0, 4.0, 2.0)                    # 上向き
arrow(s, 3.0, 2.0, 6.5, 4.0, both=True)         # <-> 両端
arrow(s, 3.0, 2.0, 6.5, 2.0, tip=None, dash='dash')   # 矢じり無しの破線
```

**座標は意味が流れる向きに書く。** 「B社がC社に労働者を供給する」なら B社の辺を先、
C社の辺を後。矢じりは必ず第2点に出るので、図が本文と逆を向くことがない。

`connector()` を直接呼んで `head=` を使ってはいけない。`head=` は OOXML の
`<a:headEnd>` 素通しで、矢じりは**始点側**に出る（gotcha 11）。何もエラーにならず、
`check_deck.py` も通り、レンダリングを人間が見るまで誤りに気づけない。

### 図をまるごと作り直す

```python
from deckkit import delete_range
delete_range(s, 5, 46, keep=())        # 図の id 範囲だけ消す。title/footer は範囲外に
# ... rrect / textbox / arrow で組み直す
```

`delete_range` は非シェイプ要素を自動でスキップする（gotcha 2）。

### 背面に帯を敷く

```python
band = rrect(s, 0.78, top, 4.16, h, fill=PURPLE, fill_alpha=13,
             line=PURPLE, lw=9525, adj=6000)
move_before(s, band, el_by_id(s, 7))   # コードブロックより背面へ
```

新規シェイプは末尾（最前面）に追加されるので、`move_before` で z 順を下げる。

### ラベルが線に重なるのを防ぐ

```python
def plate(x, y, w, h):
    """背景色で塗った矩形。ラベルの下に敷いて lifeline を隠す。"""
    return rrect(s, x, y, w, h, fill='151124', line=None, adj=0)
```

シーケンス図で lifeline がラベルを貫くときに使う。

### スライドを消す

```python
from deckkit import slide_titles, delete_slides
print(slide_titles(prs))               # ← 消す前に必ず確認
delete_slides(prs, [41, 42])           # 降順処理は内部でやる
```

削除後、**他スライドの「Slide 41 参照」を grep して潰す**（自動では直らない）。

---

## メリハリを付ける

### キーメッセージ ─ 行は自分で決める

自動折り返しに任せると「行為者個人／・法人」のような位置で切れる。
**storyboard に書かれた行を、そのまま1段落ずつ描く。**

```python
KEY = [                                   # storyboard の ### Key message から
    [R('二重派遣は', 24, TEXT, CJK, b=True),
     R('職業安定法44条違反', 24, RED, CJK, b=True),
     R('。', 24, TEXT, CJK, b=True)],
    [R('罰則は', 24, TEXT, CJK, b=True),
     R('行為者個人にも', 24, RED, CJK, b=True, hl='FFF0A8'),
     R('及ぶ。', 24, TEXT, CJK, b=True)],
]
card = rrect(s, 0.70, 0.85, 11.93, 1.30, fill=CARD, line=RULE, adj=6000)
textbox(s, 1.00, 0.85, 11.33, 1.30, KEY, algn='l', spc_pct=118)

for line in KEY:                          # 収まるか、描く前に確かめる
    assert fits(line, 11.33), ''.join(r['text'] for r in line)
```

強調は**1〜3語**。`b=True` だけの行は見出しであって強調ではない。

### ピクトグラムを本文の代わりに使う

```python
from pictogram import draw
for i, (icon, label) in enumerate([('contract', '契約書'),
                                   ('people', '指揮命令'),
                                   ('gavel', '罰則')]):
    x = 1.2 + i * 3.9
    draw(s, icon, x, 2.4, size=0.9, color=RED, bg=BG)
    textbox(s, x - 0.7, 3.5, 2.3, 0.3, [[R(label, 13, TEXT, CJK, b=True)]],
            algn='ctr')
```

`bg` は**そのアイコンが実際に載っている色**。カードの上なら `CARD` を渡す。

### コードを載せる

```python
from codehl import code_block
code_block(s, 0.70, 2.10, 6.20, 4.20, src, 'kotlin', PROF,
           sz=10.5, line_numbers=True, mark_lines=[12, 13],
           mark_hl=PAL['highlight'], focus=True)
```

`mark_lines` を指定しないコード断片は、**なぜそれが載っているのかを読者に投げている**。

`focus=True` は注目行以外を**不透明度で後ろに下げる**（`dim_alpha`、既定 0.55）。
色は `code_palette` のまま残るので、注目行以外もコードとして読める。
`mark_hl` にはプロファイルの `palette.highlight` を渡す（ハードコードした
淡黄色はダークデッキで見えない）。

### UML図の部品

`shape()` があるので専用の関数は要らない。

```python
shape(s, 'flowChartDecision', 5.0, 2.0, 1.8, 1.0, fill=CARD, line=RULE,
      runs=[R('派遣か？', 11, TEXT, CJK)])          # 判断（アクティビティ図）
shape(s, 'ellipse', 1.0, 2.2, 0.28, 0.28, fill=TEXT)  # 開始（状態遷移図）
shape(s, 'can', 9.0, 2.0, 1.2, 1.4, fill=CARD, line=RULE)   # データストア
shape(s, 'wedgeRectCallout', 7.0, 1.0, 2.4, 0.9, fill=DEEP, line=RULE,
      adj={'adj1': -20000, 'adj2': 60000}, runs=[R('注記', 10, MUTED, CJK)])
```

**新しい `prst` を使ったら必ず一度レンダリングする。** 図形が持たない調整値名を書くと、
`check_deck.py` は通るのに PowerPoint がファイルを開けなくなる（gotcha 9）。

---

## 文字幅の見積もり

はみ出しを事前に避けたいとき。厳密ではないが実用になる。

`deckkit` に入った。手書きしない。

```python
from deckkit import measure, fits, wrap_ja

measure(runs)                    # 描画幅の概算（インチ）
fits(runs, 11.33)                # 1行に収まるか
wrap_ja(text, 11.33, 20.0, CJK)  # 禁則処理つきで行に割る
```

`check_deck.py --profile` は同じ推定で「自分の枠からはみ出しそうな段落」を報告する。

**それでも確実なのは `render_deck.py` して見ること。** 見積もりはレンダリング回数を
減らすためのもので、レンダリングの代わりではない。

---

## 履歴

`history/` に、実プロジェクトで走らせたスクリプトをそのまま置いてある。
デッキパスと `sys.path` は `<project>` / `<pptx-toolkit>` に置き換えてあるので、
コピーして使う場合はそこを実パスに直すこと。

| ファイル | 内容 |
| --- | --- |
| `fix_simple.py` | r001: テキスト差し替え中心（複数スライド） |
| `fix_20.py` | r001: シーケンス図の全面再構成（delete → 組み直し） |
| `fix_25.py` | r001: コード行の背面に context 帯を敷く。座標の詰め方の例 |
| `r2_batchA.py` | r002: ラベル・文言の修正 |
| `r2_batchB.py` | r002: 矢印の引き直し、表のハイライト行追加 |
| `r2_batchC.py` | r002: 図の左右入れ替え、色の対応付け |
| `r2_batchD.py` | r002: フローチャートを削除してコードカード3枚に再構成 |
