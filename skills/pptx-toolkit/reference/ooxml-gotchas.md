# OOXML / python-pptx の落とし穴

各項目は実際にデバッグ時間を消費したもの。**症状が原因から遠い**ものばかりなので、
症状から引けるようにしてある。

---

## 症状から引く

| 症状 | 原因 |
| --- | --- |
| `'_Element' object has no attribute 'has_ph_elm'` | (1) 素の lxml で XML を作った |
| PowerPoint「ファイルを開けません」。python-pptx では開ける | (2) `nvGrpSpPr` を消した |
| 段落が空白で描画される。XML には文字がある | (3) `endParaRPr` の位置 |
| スライドを消したら他のスライドも壊れた | (4) `drop_rel` を呼んでいない |
| `soffice` が無い / 変換できない | (5) LibreOffice 未導入 |
| 図形は動いたが枠線が元の位置に残る | (6) 枠と文字が別シェイプ |
| 色を変えたのに反映されない | (7) `<p:style>` のテーマ色が勝っている |
| 新規デッキが 4:3 のまま / 文字が見えない | (8) `sldSz @type` と背景の未設定 |
| PowerPoint「ファイルを開けません」。`check_deck.py` は通る | (9) その図形に無い調整値名を書いた |
| 段落が全部 1 行に重なって描画される | (10) `spc_pct` の単位を比率と取り違えた |
| 概念図の矢印が本文と逆を向く。エラーは出ない | (11) `head=` は**始点**側の装飾 |

---

## (1) XML 構築は `pptx.oxml.parse_xml`

**やってはいけない:**

```python
from lxml import etree
el = etree.fromstring('<p:sp .../>')      # ← python-pptx のクラスが付かない
slide.shapes._spTree.append(el)
```

次に `for sh in slide.shapes:` を回した瞬間、python-pptx の内部ファクトリが
`shape_elm.has_ph_elm` を呼び、素の `_Element` には無いので `AttributeError`。
**XML を足した箇所ではなく、後から無関係な反復処理で落ちる**ため原因が見えにくい。

**正しい:**

```python
from pptx.oxml import parse_xml
wrapper = '<root xmlns:a="..." xmlns:p="..." xmlns:r="...">%s</root>' % xml
elements = list(parse_xml(wrapper))
```

`deckkit.frag()` がこれを行う。名前空間宣言をラッパに付けるのが要点。

---

## (2) `nvGrpSpPr` を消さない

`spTree` の子は shape だけではない:

```xml
<p:spTree>
  <p:nvGrpSpPr>...<p:cNvPr id="1" name=""/>...</p:nvGrpSpPr>   ← shape ではない
  <p:grpSpPr>...</p:grpSpPr>                                    ← shape ではない
  <p:sp>...<p:cNvPr id="2" .../></p:sp>                         ← shape
</p:spTree>
```

`cNvPr` を持つからといって `nvGrpSpPr` を消すと spTree が壊れる。
**python-pptx は壊れたファイルを平然と開き、スライド数も shape も正しく報告する。**
PowerPoint だけが拒否する。この非対称のせいで、原因究明が数ステップ遅れる。

**正しい:**

```python
SHAPE_TAGS = {'sp', 'cxnSp', 'pic', 'graphicFrame', 'grpSp'}
for el in list(spTree):
    if etree.QName(el).localname not in SHAPE_TAGS:
        continue
    ...
```

`deckkit.delete_ids()` / `delete_range()` / `shape_elements()` が対応済み。
`check_deck.py` は `nvGrpSpPr` の欠落を `CRITICAL` として検出する。

**復旧方法:** 他スライドから `nvGrpSpPr` を `copy.deepcopy` して先頭に挿入すれば直る。

---

## (3) `endParaRPr` は段落の最後の子

`CT_TextParagraph` の子の順序は決まっている: `pPr?` → (`r` | `br` | `fld`)* → `endParaRPr?`

段落の run を作り直すとき、既存の `endParaRPr` を残したまま後ろに run を足すと
**順序違反**になる。すると:

* XML を目で見ても正しく見える
* python-pptx の `paragraph.runs` でも読める
* **PowerPoint だけがその段落を描画しない（空白になる）**

**正しい:**

```python
epr = p_el.find(qn('a:endParaRPr'))
for r in new_runs:
    node = frag(run_xml(r))[0]
    if epr is not None:
        epr.addprevious(node)     # endParaRPr の前に差す
    else:
        p_el.append(node)
```

`deckkit.set_para()` が対応済み。`check_deck.py` が `CRITICAL` として検出する。

---

## (4) スライド削除は drop_rel が要る

`sldIdLst` から要素を消すだけでは、`presentation.xml.rels` に関係が残り、
パッケージが不整合になる。

```python
from pptx.oxml.ns import qn
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
for pos in sorted(positions, reverse=True):      # 必ず降順
    sldId = ids[pos - 1]
    prs.part.drop_rel(sldId.get(qn('r:id')))     # 関係を落とす
    sldIdLst.remove(sldId)                       # 一覧から外す
```

* **降順で消す。** 昇順だと2枚目以降のインデックスがずれる。
* そのスライドに紐づく **modern comment も一緒に落ちる**（意図どおりだが、
  コメント記録を先に書き出しておくこと）。
* 他スライドがテキストで「Slide 41 参照」と書いていても**自動では直らない**。
  削除後に全スライドを grep して参照を潰す。

`deckkit.delete_slides()` が対応済み。削除前に `slide_titles(prs)` で対象を確認する。

---

## (5) レンダリングは PowerPoint COM のみ

このマシンに LibreOffice は**入っていない**。`soffice --convert-to` は使えない。

```powershell
$app  = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($path, $true, $false, $false)  # ReadOnly, ¬Untitled, ¬WithWindow
$pres.Slides($i).Export($png, "PNG", 1600, 900)
$pres.SaveAs($pdf, 32)                                          # 32 = ppSaveAsPDF
$pres.Close(); $app.Quit()
```

* `Presentations.Open` が失敗する ＝ **ファイルが壊れている**強いサイン（症状(2)）。
* COM プロセスが残ると次回の Open が失敗する。`finally` で必ず `Close`/`Quit`。
* PDF を画像で確認したいだけなら pypdfium2 が速く、PowerPoint も要らない
  （`render_deck.py --from-pdf`）。

---

## (6) 枠と文字が別シェイプのことがある

このデッキの生成物では、角丸長方形（`rrect`）と、その上に載るテキストボックス（`textbox`）が
**別々のシェイプ**。片方だけ `set_xfrm` で動かすと、枠だけ元の位置に取り残される。

シェイプを動かすときは、`inspect_deck.py` で**同じ座標に重なっている別 id が無いか**を
必ず確認する。左右を入れ替えるような編集では特に起きやすい。

---

## (7) `<p:style>` のテーマ色が明示色に勝つことがある

python-pptx の `shape.fill.fore_color.rgb` で色を設定しても、シェイプに
`<p:style><a:fillRef idx="3"><a:schemeClr val="accent1"/></a:fillRef></p:style>`
が付いていると、環境によってテーマ色が優先されることがある。

確実に効かせるには `spPr` に直接 `<a:solidFill><a:srgbClr val="..."/></a:solidFill>` を書く
（`deckkit.rrect()` はそうしている）。既存シェイプの色を変える場合は、
`el.find('.//a:solidFill/a:srgbClr').set('val', ...)` のように**生の要素を触る**のが安全。

---

## (8) 新規デッキ: `sldSz @type` は古いまま残り、背景は白のまま

素の `Presentation()` は **10 × 7.5 in（4:3）** で、canvas は**白**。
ここに2つの罠がある。

**罠A ─ 寸法を変えても `type` が残る。** 検証済み:

```python
p = Presentation()                    # 10 x 7.5, type="screen4x3"
p.slide_height = Emu(5143500)         # 10 x 5.625 になるが…
# <p:sldSz cx="9144000" cy="5143500" type="screen4x3"/>   ← type が古いまま
```

PowerPoint の「デザイン > スライドのサイズ」が誤ったプリセットを表示する。
`deckkit.set_deck_size()` は `type` も一緒に設定する。

**罠B ─ 背景が白のまま＝文字が消える。** マスターもレイアウトも
`bgRef idx="1001" → schemeClr bg1 → lt1 → FFFFFF` に解決される。
一方 `deckkit.R()` の既定文字色はほぼ白（`ECEAF7`）。
**結果は白地に白文字で、何も見えないデッキ**が「正常に」生成される。
python-pptx も `check_deck` の他のルールも異常を報告しない。

対策（`new_deck.py` が実施している）:

```python
set_bg(prs.slide_masters[0], palette['bg'])   # マスターに背景
for lay in prs.slide_layouts:
    clear_bg(lay)                              # レイアウトからは外して継承させる
```

マスターに置くと、**人間が PowerPoint で「新しいスライド」を押した場合**も暗い canvas になる。
`check_deck.py` は「slide / layout / master のどこにも `<p:bg>` が無い」を `HIGH` で検出する。

なお `<p:bg>` は `<p:cSld>` の**第1子**でなければならない（schema 順序 `bg?, spTree, ...`）。

---

## (9) `<a:avLst>` にその図形が持たない調整値名を書くと開けなくなる

**(2) と同じ非対称性**。python-pptx も `check_deck.py` も何も言わないが、
PowerPoint は `Presentations.Open` の時点でファイルを拒否する。

```python
# ダメ: mathMultiply の調整値は adj1 であって adj ではない
shape(s, 'mathMultiply', ..., adj=25000)          # -> <a:gd name="adj" .../>

# ダメ: flowChartManualOperation は調整値を1つも持たない
shape(s, 'flowChartManualOperation', ..., adj=22000)
```

```python
# 正しい
shape(s, 'mathMultiply', ..., adj={'adj1': 25000})
shape(s, 'flowChartManualOperation', ...)          # adj を渡さない
```

`deckkit.shape()` の `adj` は、**int を渡すと `name="adj"` になる**。
`adj` という名前の調整値を持つ図形（`roundRect` `triangle` `donut` `can`
`homePlate` `star5` `noSmoking` など）ではそれで正しいが、
`adj1`/`adj2` 系の図形（`rightArrow` `wedgeRectCallout` `blockArc`
`circularArrow` `mathMultiply` など）には **list か dict で渡す**。

迷ったら **`adj` を渡さない**（`<a:avLst/>` になり、PowerPoint が既定値を使う）。
見た目が気に入らなければそこから調整する。**開けないファイルを作るよりはるかに安い。**

新しい `prst` を使ったら、**必ず一度レンダリングして開けることを確認する。**
`pictogram.py` の `contact_sheet()` はそのためにある。

---

## (10) `spc_pct` は「パーセント」であって「倍率」ではない

`textbox(..., spc_pct=1.25)` と書くと、行間が **1.25%** になり、
**段落が全部同じ位置に重なって描画される**。1文字も欠けないので XML を見ても気づけない。

```python
textbox(..., spc_pct=125)    # 125% = 1.25倍。これが正しい
textbox(..., spc_pct=104)    # 既存スクリプトの実績値
```

OOXML の `<a:spcPct val="...">` は 100000 が 100%。`deckkit` は渡された値を
1000倍して書くので、**引数はパーセント**である。

---

## (11) `head=` は「矢が指す先」ではない。矢印は `arrow()` で描く

`connector(..., head='triangle')` と書くと、矢じりは**線の始点側**に出る。
「head = 矢の先端」という読み方は通じない。OOXML の `<a:headEnd>` は
**線の始点の装飾**、`<a:tailEnd>` が終点の装飾で、`deckkit` はそれを素通ししている。

実測（横線。左端がボックス原点）:

| 指定 | 矢じりの位置 |
| --- | --- |
| `head='triangle'` | 左端（＝始点） |
| `tail='triangle'` | 右端（＝終点） |
| `head='triangle', flipH=True` | 右端（flip で始点が右に移る） |

**この落とし穴が厄介なのは、何もエラーにならないこと。** ファイルは開けるし、
`check_deck.py` も通るし、線もちゃんと引かれている。ただ図が**本文と逆のことを
言っている**だけで、レンダリングした PNG を人間が読むまで誰も気づかない。

しかも名前を覚えるだけでは足りない。`connector()` は 2点ではなく
**バウンディングボックス + flipH/flipV** を取るので、どの角が始点かは flip で
入れ替わる。flip が絡んだ瞬間にまた間違える。

**矢印は `arrow()` で描く。** 始点→終点をそのまま座標で渡すだけで、矢じりは必ず
第2点に出る。ボックスも flip も内部で計算する。

```python
arrow(s, 3.0, 2.0, 6.5, 2.0)              # --> 矢じりは (6.5, 2.0)
arrow(s, 6.5, 2.0, 3.0, 2.0)              # <-- 矢じりは (3.0, 2.0)
arrow(s, 4.0, 5.0, 4.0, 2.0)              # 上向き。矢じりは上端
arrow(s, 3.0, 2.0, 6.5, 4.0, both=True)   # <-> 両端に矢じり
arrow(s, 3.0, 2.0, 6.5, 2.0, tip=None, dash='dash')   # 矢じり無しの破線
```

座標は**意味が流れる向き**に書く。「B社がC社に労働者を供給する」なら B社の辺を先、
C社の辺を後に渡す。そうすれば図と本文が食い違いようがない。

`connector()` の `head=`/`tail=` は既存バッチスクリプト互換のため素通しのまま
残してあるが、**新規コードでは使わない**。どうしても `connector()` を直接呼ぶなら、
意味の明示された別名を使う:

```python
connector(s, x, y, w, h, start='triangle')   # 始点側（= head=）
connector(s, x, y, w, h, end='triangle')     # 終点側（= tail=）
```

---

## 参考: このデッキの構造メモ

* 寸法 10 × 5.625 in（16:9）。EMU 換算は 914400/in。
* 本文フォント `Calibri`、等幅 `Courier New`、和文 `Yu Gothic`。
* CJK を含む run は `<a:ea typeface="...">` も設定しないと和文が別フォントになる
  （`deckkit._run_xml` は `latin`/`ea`/`cs` の3つを揃えて出力する）。
* コード断片は VSCode Dark+ 相当: キーワード `569CD6` / 関数 `DCDCAA` / 文字列 `CE9178` /
  型 `4EC9B0` / 数値 `B5CEA8` / 既定 `D4D4D4` / コメント `6A9955` 系。
