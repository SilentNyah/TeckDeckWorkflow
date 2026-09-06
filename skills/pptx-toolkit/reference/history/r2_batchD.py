# -*- coding: utf-8 -*-
"""r002 Batch D: slide 37 (pitfall sample code) + slide 39 (code-driven redesign)."""
import sys
sys.path.insert(0, r'<pptx-toolkit>/scripts')
from pptx import Presentation
from deckkit import (R, set_runs, shape_by_id, el_by_id, set_xfrm, spTree,
                     rrect, textbox, connector, _q)
from lxml import etree

DECK = r'<project>\slides\deck.pptx'
prs = Presentation(DECK)
S = lambda n: prs.slides[n - 1]
MONO, SANS = 'Courier New', 'Calibri'
LIGHT, MUTED, DIM = 'ECEAF7', '9C95BC', '6E6A8A'
GREEN, AMBER, PURPLE, PINK = '34E2B0', 'FFB454', 'B89CFF', 'FF7597'
CARD = '1E1838'
KW, FN, STR, TYPE, TXT, CMT = '569CD6', 'DCDCAA', 'CE9178', '4EC9B0', 'D4D4D4', '9C95BC'


# ================================================================ slide 37
# CMT-r002-017: put the pitfall into code inside the 落とし穴 box (keep concurrentSum happy path)
s37 = S(37)
set_xfrm(el_by_id(s37, 28), h=1.36)   # widen the 落とし穴 box a touch
set_runs(shape_by_id(s37, 30), [
    [R('coroutineScope {', 7.6, TXT, MONO)],
    [R('  ', 7.6, TXT, MONO), R('async', 7.6, FN, MONO), R(' { ', 7.6, TXT, MONO),
     R('throw', 7.6, KW, MONO), R(' E() }  ', 7.6, TXT, MONO), R('// await しない', 7.6, PINK, MONO)],
    [R('}  ', 7.6, TXT, MONO), R('// ← それでも親は cancel される', 7.6, PINK, MONO)],
    [R('非 supervisor 親では await 不要で親を巻き込む', 7.4, LIGHT, SANS, b=True)],
    [R('（supervisor / GlobalScope だけ Deferred 経由で観測）。', 7.2, MUTED, SANS)],
])

# ================================================================ slide 39
# CMT-r002-019: replace the dense flowchart with 3 code examples + a routing-rules panel
s39 = S(39)
# delete the whole flowchart (ids 5..49); keep kicker/title/subtitle(2,3,4) and 要点/source(50-53)
for el in list(spTree(s39)):
    if etree.QName(el).localname not in ('sp', 'cxnSp', 'pic', 'graphicFrame', 'grpSp'):
        continue
    cnv = el.find('.//' + _q('p:cNvPr'))
    if cnv is not None and 5 <= int(cnv.get('id')) <= 49:
        el.getparent().remove(el)

# subtitle: keep the essence
set_runs(shape_by_id(s39, 4), [[
    R('例外の行き先は3通り ─ ', 11.0, MUTED, SANS),
    R('自分で catch / launch は CEH へ / async は await() へ', 11.0, LIGHT, SANS, b=True),
    R('。CEH は root/scope 限定・回復不可。', 11.0, MUTED, SANS),
]])


def code_card(x, y, w, h, accent, title_runs, code_lines, takeaway_runs):
    rrect(s39, x, y, w, h, fill=CARD, line=accent, lw=12700, adj=8000)
    textbox(s39, x + 0.16, y + 0.07, w - 0.30, 0.18, [title_runs], algn='l')
    paras = [[R(*a) if isinstance(a, tuple) else a for a in line] for line in code_lines]
    textbox(s39, x + 0.16, y + 0.27, w - 0.30, h - 0.46, paras, algn='l', spc_pct=104)
    textbox(s39, x + 0.16, y + h - 0.20, w - 0.30, 0.16, [takeaway_runs], algn='l')


LX, LW = 0.50, 5.02
# ① try/catch
code_card(LX, 1.58, LW, 0.92, GREEN,
          [R('① 自分で try/catch ─ 通常の例外処理', 8.6, GREEN, SANS, b=True)],
          [[R('try', 8.0, KW, MONO), R(' { risky() } ', 8.0, TXT, MONO),
            R('catch', 8.0, KW, MONO), R(' (e: ', 8.0, TXT, MONO),
            R('IOException', 8.0, TYPE, MONO), R(') { handle(e) }', 8.0, TXT, MONO)]],
          [R('捕まえれば CEH は不要（＝正常系。ほとんどの例外はここ）', 7.6, MUTED, SANS)])
# ② launch → CEH
code_card(LX, 2.60, LW, 1.00, AMBER,
          [R('② launch の未処理例外 → CoroutineExceptionHandler', 8.6, AMBER, SANS, b=True)],
          [[R('val', 8.0, KW, MONO), R(' h = ', 8.0, TXT, MONO),
            R('CoroutineExceptionHandler', 8.0, TYPE, MONO),
            R(' { _, e -> log(e) }', 8.0, TXT, MONO)],
           [R('CoroutineScope', 8.0, TYPE, MONO), R('(', 8.0, TXT, MONO),
            R('SupervisorJob', 8.0, FN, MONO), R('() + h).', 8.0, TXT, MONO),
            R('launch', 8.0, FN, MONO), R(' { ', 8.0, TXT, MONO),
            R('throw', 8.0, KW, MONO), R(' E() }', 8.0, TXT, MONO)]],
          [R('CEH は root / scope の Job に置いたときだけ効く（子に置くと無効）', 7.6, MUTED, SANS)])
# ③ async → await
code_card(LX, 3.70, LW, 0.92, PURPLE,
          [R('③ async の例外 → await() で受ける', 8.6, PURPLE, SANS, b=True)],
          [[R('val', 8.0, KW, MONO), R(' d = scope.', 8.0, TXT, MONO),
            R('async', 8.0, FN, MONO), R(' { ', 8.0, TXT, MONO),
            R('throw', 8.0, KW, MONO), R(' E() }', 8.0, TXT, MONO)],
           [R('try', 8.0, KW, MONO), R(' { d.', 8.0, TXT, MONO), R('await', 8.0, FN, MONO),
            R('() } ', 8.0, TXT, MONO), R('catch', 8.0, KW, MONO), R(' (e: E) { … }', 8.0, TXT, MONO)]],
          [R('async は CEH を通らない ─ 例外は await() が throw する', 7.6, MUTED, SANS)])

# right rules panel
RX, RY, RW = 5.72, 1.58, 3.78
rrect(s39, RX, RY, RW, 3.04, fill=CARD, line='3C3463', lw=9525, adj=4000)
textbox(s39, RX + 0.18, RY + 0.12, RW - 0.36, 0.22,
        [[R('ルーティングの要点', 9.5, LIGHT, SANS, b=True)]], algn='l')
bullets = [
    [R('CancellationException', 8.2, PINK, MONO), R(' は透過 ─ ハンドラに渡らない（＝ normal cancel）', 8.2, MUTED, SANS)],
    [R('CEH が効くのは ', 8.2, MUTED, SANS), R('root / scope', 8.2, LIGHT, SANS, b=True),
     R(' だけ ─ 子に置くと無効（親へ委譲）', 8.2, MUTED, SANS)],
    [R('CEH は回復用ではない', 8.2, LIGHT, SANS, b=True),
     R(' ─ ログ / 通知 / shutdown の最後の受け皿', 8.2, MUTED, SANS)],
    [R('launch', 8.2, GREEN, MONO), R(' → CEH（無ければ platform 既定）', 8.2, MUTED, SANS)],
    [R('async', 8.2, PURPLE, MONO), R(' → ', 8.2, MUTED, SANS), R('await()', 8.2, LIGHT, MONO),
     R(' で throw（CEH を経由しない）', 8.2, MUTED, SANS)],
]
yy = RY + 0.44
for b in bullets:
    textbox(s39, RX + 0.30, yy, RW - 0.48, 0.44, [b], algn='l', spc_pct=104)
    # bullet dot
    textbox(s39, RX + 0.16, yy, 0.14, 0.20, [[R('•', 8.2, DIM, SANS)]], algn='l')
    yy += 0.50

prs.save(DECK)
print('Batch D saved')
