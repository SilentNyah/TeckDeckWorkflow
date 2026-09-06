# -*- coding: utf-8 -*-
"""CMT-r001-002 : rebuild the slide 20 sequence diagram from scratch."""
import sys
sys.path.insert(0, r'<pptx-toolkit>/scripts')
from pptx import Presentation
from lxml import etree
from deckkit import R, set_runs, shape_by_id, rrect, textbox, connector, spTree, _q

DECK = r'<project>\slides\deck.pptx'
prs = Presentation(DECK)
s = prs.slides[19]

MONO, SANS = 'Courier New', 'Calibri'
GREEN, AMBER, PURPLE, PINK = '34E2B0', 'FFB454', 'B89CFF', 'FF7597'
MUTED, DIM, LIGHT = '9C95BC', '6E6A8A', 'ECEAF7'
CARD, RULE, BG = '1E1838', '3C3463', '151124'

# 図の構成要素をすべて撤去（kicker=2 / title=3 / lead=4 / footer=47,48 は残す）
# spTree の先頭 2 要素は nvGrpSpPr / grpSpPr。nvGrpSpPr も cNvPr を持つので、
# 図形要素だけを対象にしないとツリーごと壊れる。
SHAPE_TAGS = {'sp', 'cxnSp', 'pic', 'graphicFrame', 'grpSp'}
KEEP = {'2', '3', '4', '47', '48'}
for el in list(spTree(s)):
    if etree.QName(el).localname not in SHAPE_TAGS:
        continue
    cnv = el.find('.//' + _q('p:cNvPr'))
    if cnv is not None and cnv.get('id') not in KEEP:
        el.getparent().remove(el)


def text_w(runs):
    """Rough rendered width (inches) of a run list."""
    w = 0.0
    for r in runs:
        pt = r['sz'] / 72.0
        for ch in r['text']:
            w += pt * (1.0 if ord(ch) > 0x2000 else (0.6 if r['font'] == MONO else 0.48))
    return w


def plate(x, y, w, h):
    """Opaque backing so a label is not crossed by lifelines."""
    return rrect(s, x, y, w, h, fill=BG, line=None, adj=0)


def label(cx, y, h, runs, algn='ctr', pad=0.07):
    """Centred label with a background plate."""
    w = text_w(runs) + 2 * pad
    plate(cx - w / 2, y, w, h)
    return textbox(s, cx - w / 2, y, w, h, [runs], algn=algn)


# --------------------------------------------------------------- lead 文
set_runs(shape_by_id(s, 4), [[
    R('初回実行も再開も、', 11.0, MUTED, SANS),
    R('DispatchedContinuation', 11.0, LIGHT, MONO),
    R(' → ', 11.0, MUTED, SANS),
    R('Dispatcher', 11.0, AMBER, MONO),
    R(' を通ってから状態マシンへ戻る。', 11.0, MUTED, SANS),
]])

# ------------------------------------------------------------ participants
TOP, HDR_H, BOT = 1.32, 0.46, 5.06
P = [
    # (x, w, 役割, 型名, 色)
    (0.50, 1.42, '呼び元 (caller)', 'launch / 完了側',        GREEN),
    (2.04, 2.02, 'intercept 済み',  'DispatchedContinuation', PURPLE),
    (4.18, 1.76, '実行方針',         'CoroutineDispatcher',    AMBER),
    (6.06, 1.58, '実行基盤',         'Executor/Scheduler',     MUTED),
    (7.76, 1.74, '状態マシン',       'BaseContinuationImpl',   PINK),
]
CX = [x + w / 2 for x, w, _, _, _ in P]

for x, w, role, name, color in P:
    rrect(s, x, TOP, w, HDR_H, fill=CARD, line=color, lw=15240, adj=14000, shadow=True)
    textbox(s, x, TOP, w, HDR_H,
            [[R(role, 7.5, MUTED, SANS)], [R(name, 8.5, color, MONO, b=True)]], algn='ctr')
for cx in CX:
    connector(s, cx, TOP + HDR_H, 0, BOT - (TOP + HDR_H), color=RULE, lw=9525, dash='dash')


def msg(n, src, dst, runs, y, color, dash=None):
    x1, x2 = CX[src], CX[dst]
    left, right = min(x1, x2), max(x1, x2)
    connector(s, left, y, right - left, 0, color=color, lw=19050,
              dash=dash, tail='triangle', flipH=(x2 < x1))
    label((left + right) / 2, y - 0.19, 0.17,
          [R('%s ' % n, 8.5, MUTED, SANS, b=True)] + runs)


# ① 呼び元 → DispatchedContinuation
msg('①', 0, 1, [R('resumeWith(result)', 8.5, LIGHT, MONO, b=True)], 2.06, GREEN)
n1 = [R('初回実行 = builder.start 由来（resumeCancellableWith）', 7.0, MUTED, SANS)]
n2 = [R('再開 = タイマ / コールバック / 完了 coroutine が呼ぶ', 7.0, MUTED, SANS)]
w1 = max(text_w(n1), text_w(n2)) + 0.14
plate(0.55, 2.09, w1, 0.26)
textbox(s, 0.62, 2.09, w1, 0.26, [n1, n2], algn='l')

# ② DispatchedContinuation → CoroutineDispatcher
msg('②', 1, 2, [R('isDispatchNeeded(context)', 8.5, LIGHT, MONO, b=True)], 2.62, PURPLE)

# ------------------------------------------------------------------ alt フレーム
ALT_Y, ALT_X, ALT_R = 2.74, 2.68, 9.50
rrect(s, ALT_X, ALT_Y, ALT_R - ALT_X, BOT - ALT_Y, fill=None, line=PURPLE, lw=9525, adj=2000)
rrect(s, ALT_X, ALT_Y, 0.50, 0.21, fill=PURPLE, line=None, adj=10000)
textbox(s, ALT_X, ALT_Y, 0.50, 0.21, [[R('alt', 8.0, '100B21', SANS, b=True)]], algn='ctr')

gA = [R('[ isDispatchNeeded == true', 7.5, AMBER, MONO, b=True),
      R(' ─ 別 thread へ渡して続行 ]', 7.5, AMBER, SANS, b=True)]
plate(ALT_X + 0.58, ALT_Y + 0.02, text_w(gA) + 0.16, 0.17)
textbox(s, ALT_X + 0.64, ALT_Y + 0.03, text_w(gA) + 0.16, 0.16, [gA], algn='l')

# ③ DispatchedContinuation → CoroutineDispatcher
msg('③', 1, 2, [R('dispatch(context, block = this)', 8.5, LIGHT, MONO, b=True)], 3.16, PURPLE)
# ④ CoroutineDispatcher → 実行基盤
msg('④', 2, 3, [R('enqueue(task)', 8.5, LIGHT, MONO, b=True)], 3.46, AMBER)
label(5.955, 3.49, 0.15,
      [R('task = DispatchedContinuation 自身（Runnable）', 7.0, DIM, SANS)])
# ⑤ 実行基盤 → DispatchedContinuation（worker が task を走らせる）
msg('⑤', 3, 1, [R('run()', 8.5, LIGHT, MONO, b=True)], 3.86, MUTED, dash='dash')
label(4.95, 3.89, 0.15, [R('※ ここから worker thread 上', 7.0, GREEN, SANS, b=True)])
# ⑥ DispatchedContinuation → BaseContinuationImpl
msg('⑥', 1, 4, [R('resumeWith(result)', 8.5, LIGHT, MONO, b=True)], 4.26, PURPLE)
# ⑦ BaseContinuationImpl の自己呼び出し
lx, ly, lh, lw2 = CX[4], 4.36, 0.16, 0.34
connector(s, lx, ly, lw2, 0, color=PINK, lw=19050)
connector(s, lx + lw2, ly, 0, lh, color=PINK, lw=19050)
connector(s, lx, ly + lh, lw2, 0, color=PINK, lw=19050, tail='triangle', flipH=True)
r7 = [R('⑦ ', 8.5, MUTED, SANS, b=True),
      R('invokeSuspend()', 8.5, LIGHT, MONO, b=True),
      R('（次 label へ）', 7.5, MUTED, SANS)]
w7 = text_w(r7) + 0.14
plate(lx - 0.06 - w7, ly - 0.01, w7, 0.19)
textbox(s, lx - 0.12 - w7, ly - 0.01, w7, 0.19, [r7], algn='r')

# ------------------------------------------------------------------ else 分岐
connector(s, ALT_X, 4.60, ALT_R - ALT_X, 0, color=PURPLE, lw=9525, dash='dash')
gB = [R('[ isDispatchNeeded == false', 7.5, GREEN, MONO, b=True),
      R(' ─ 呼び出し元 thread のまま続行（再 dispatch なし）]', 7.5, GREEN, SANS, b=True)]
plate(ALT_X + 0.58, 4.63, text_w(gB) + 0.16, 0.17)
textbox(s, ALT_X + 0.64, 4.64, text_w(gB) + 0.16, 0.16, [gB], algn='l')
# ⑧ DispatchedContinuation → BaseContinuationImpl（再 dispatch なし）
msg('⑧', 1, 4, [R('resumeWith(result)', 8.5, LIGHT, MONO, b=True)], 4.95, PURPLE)

# -------------------------------------------------------------- 例外ケースの注
textbox(s, 0.55, 5.14, 8.95, 0.18, [[
    R('注: ', 7.5, PINK, SANS, b=True),
    R('CoroutineStart.UNDISPATCHED', 7.5, PINK, MONO, b=True),
    R(' は intercept / dispatch を経ず、呼び出し元 thread で最初の suspension まで直接 '
      'invokeSuspend する（初回 dispatch の例外）。', 7.5, MUTED, SANS),
]], algn='l')

prs.save(DECK)
print('saved')
