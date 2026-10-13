# -*- coding: utf-8 -*-
"""Static lint for a .pptx. Does NOT launch PowerPoint.

Catches the two failure modes that otherwise cost a full render cycle to discover:
  * corrupt spTree      -> PowerPoint refuses the file, python-pptx opens it fine
  * endParaRPr misorder -> paragraph renders BLANK though the XML looks right

    python check_deck.py <deck.pptx>
    python check_deck.py <deck.pptx> --profile slides/deck-profile.json
    python check_deck.py <deck.pptx> --slide 39
    python check_deck.py <deck.pptx> --infer-profile > slides/deck-profile.json

Exit code 0 = clean, 1 = findings, 2 = could not read the deck.
"""
import argparse
import collections
import json
import sys

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
SHAPE_TAGS = {'sp', 'cxnSp', 'pic', 'graphicFrame', 'grpSp'}


def q(ns, tag):
    return '{%s}%s' % (ns, tag)


# --------------------------------------------------------------------------
# background resolution + WCAG contrast
#
# This is the only check in the toolchain that catches white-on-white BEFORE a
# render cycle. deckkit's default text colour is near-white, so a deck built
# without a background renders invisible text while every other check passes.
# --------------------------------------------------------------------------

def _bg_of(part):
    """The explicit solid <p:bg> colour of a slide/layout/master, or None."""
    el = getattr(part, '_element', None)
    if el is None:
        return None
    cSld = el.find(q(P, 'cSld'))
    if cSld is None:
        return None
    bg = cSld.find(q(P, 'bg'))
    if bg is None:
        return None
    clr = bg.find('.//' + q(A, 'srgbClr'))
    return clr.get('val').upper() if clr is not None and clr.get('val') else None


def effective_bg(slide):
    """Resolve slide -> layout -> master. None means the theme decides (white)."""
    for part in (slide, slide.slide_layout, slide.slide_layout.slide_master):
        try:
            val = _bg_of(part)
        except Exception:
            val = None
        if val:
            return val
    return None


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hexstr):
    r, g, b = (int(hexstr[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    """WCAG contrast ratio between two RRGGBB strings. 1.0 = identical."""
    try:
        la, lb = luminance(a), luminance(b)
    except Exception:
        return None
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def check_slide(prs, idx, slide, profile, findings, contrast_check=False,
                visual=True):
    from lxml import etree
    from pptx.util import Emu

    where = 'slide %d' % idx
    tree = slide.shapes._spTree

    # --- structural: nvGrpSpPr must be present and first ---
    kids = [etree.QName(el).localname for el in tree]
    if 'nvGrpSpPr' not in kids:
        findings.append((where, 'CRITICAL', 'spTree is missing <p:nvGrpSpPr> -- '
                                            'PowerPoint will refuse to open this file'))
    elif kids[0] != 'nvGrpSpPr':
        findings.append((where, 'CRITICAL', '<p:nvGrpSpPr> is not the first spTree child '
                                            '(found %r)' % kids[0]))
    if 'grpSpPr' not in kids:
        findings.append((where, 'HIGH', 'spTree is missing <p:grpSpPr>'))

    # --- shape ids: duplicates break addressing ---
    ids = collections.Counter()
    for el in tree:
        if etree.QName(el).localname not in SHAPE_TAGS:
            continue
        cnv = el.find('.//' + q(P, 'cNvPr'))
        if cnv is None:
            findings.append((where, 'HIGH', 'shape element without <p:cNvPr>'))
            continue
        ids[cnv.get('id')] += 1
    for sid, n in ids.items():
        if n > 1:
            findings.append((where, 'HIGH', 'duplicate shape id %s (x%d)' % (sid, n)))

    # --- paragraphs: endParaRPr must be last; flag run-less paragraphs ---
    for el in tree:
        if etree.QName(el).localname not in SHAPE_TAGS:
            continue
        cnv = el.find('.//' + q(P, 'cNvPr'))
        sid = cnv.get('id') if cnv is not None else '?'
        for p_el in el.iter(q(A, 'p')):
            children = [etree.QName(c).localname for c in p_el]
            if 'endParaRPr' in children:
                if children[-1] != 'endParaRPr':
                    findings.append((where, 'CRITICAL',
                                     'shape %s: <a:endParaRPr> is not the last child '
                                     '(order %s) -- paragraph will render BLANK'
                                     % (sid, '/'.join(children))))
            if 'r' not in children and 'fld' not in children and 'br' not in children:
                has_text = any(c == 'endParaRPr' for c in children)
                if not has_text and children:
                    findings.append((where, 'LOW',
                                     'shape %s: paragraph with no runs' % sid))

    # --- geometry: shapes outside the canvas ---
    W = Emu(prs.slide_width).inches
    H = Emu(prs.slide_height).inches
    tol = 0.02
    for sh in slide.shapes:
        if sh.left is None or sh.top is None or sh.width is None or sh.height is None:
            continue
        x, y = Emu(sh.left).inches, Emu(sh.top).inches
        w, h = Emu(sh.width).inches, Emu(sh.height).inches
        if x < -tol or y < -tol or x + w > W + tol or y + h > H + tol:
            findings.append((where, 'MEDIUM',
                             'shape %s (%s) outside canvas: x=%.2f y=%.2f w=%.2f h=%.2f '
                             '(canvas %.2fx%.2f)' % (sh.shape_id, sh.name, x, y, w, h, W, H)))

    # --- background: deterministic, always on ---
    bg = effective_bg(slide)
    if bg is None and profile and (profile.get('palette') or {}).get('bg'):
        findings.append((where, 'HIGH',
                         'no explicit background on slide, layout or master -- '
                         'PowerPoint renders this WHITE, and this profile\'s text '
                         'colour would be invisible on white'))

    # --- text contrast: opt-in, advisory ---
    #
    # Deliberately NOT part of the default run. Text frequently sits on top of a
    # SEPARATE filled shape (badge chips, panels), which cannot be resolved
    # without z-order + geometry analysis, so a naive slide-background
    # comparison produces heavy false positives on well-built decks. Oversized
    # decorative numerals are also intentionally near-invisible.
    #
    # What it IS good for: a freshly generated deck, where every shape is known
    # and nothing overlaps yet. That is the white-on-white case worth catching.
    if contrast_check:
        bg_ref = bg or 'FFFFFF'
        seen = set()
        for el in tree:
            if etree.QName(el).localname not in SHAPE_TAGS:
                continue
            cnv = el.find('.//' + q(P, 'cNvPr'))
            sid = cnv.get('id') if cnv is not None else '?'
            # a shape's own solid fill is the backdrop for its own text
            spPr = el.find(q(P, 'spPr'))
            own = None
            if spPr is not None:
                f = spPr.find(q(A, 'solidFill'))
                if f is not None:
                    c = f.find(q(A, 'srgbClr'))
                    if c is not None and c.get('val'):
                        own = c.get('val').upper()
            backdrop = own or bg_ref
            for rPr in el.iter(q(A, 'rPr')):
                fill = rPr.find(q(A, 'solidFill'))
                if fill is None:
                    continue
                clr = fill.find(q(A, 'srgbClr'))
                if clr is None or not clr.get('val'):
                    continue
                fg = clr.get('val').upper()
                try:
                    pt = int(rPr.get('sz') or 0) / 100.0
                except ValueError:
                    pt = 0
                if pt >= 40:          # decorative oversized type
                    continue
                key = (fg, backdrop)
                if key in seen:
                    continue
                seen.add(key)
                ratio = contrast(fg, backdrop)
                # Lenient: de-emphasised text is a real design choice --
                # this deck's `dim` sits at 3.6:1 by intent.
                if ratio is not None and ratio < 2.0:
                    findings.append((where, 'MEDIUM',
                                     'shape %s: text %s on %s is %.2f:1%s'
                                     % (sid, fg, backdrop, ratio,
                                        '' if own else ' (slide bg; may sit on another shape)')))

    # --- palette / fonts, only when a profile is supplied ---
    if profile:
        # code_palette holds syntax-highlight colours; both groups are legitimate.
        palette = {v.upper() for v in (profile.get('palette') or {}).values()}
        palette |= {v.upper() for v in (profile.get('code_palette') or {}).values()}
        fonts = {v for v in (profile.get('fonts') or {}).values()}
        if palette:
            seen = set()
            for el in tree:
                for c in el.iter(q(A, 'srgbClr')):
                    val = (c.get('val') or '').upper()
                    if val and val not in palette:
                        seen.add(val)
            for val in sorted(seen):
                findings.append((where, 'LOW', 'colour %s not in profile palette' % val))
        if fonts:
            seen = set()
            for el in tree:
                for t in el.iter(q(A, 'latin')):
                    tf = t.get('typeface')
                    if tf and tf not in fonts:
                        seen.add(tf)
            for tf in sorted(seen):
                findings.append((where, 'LOW', 'font %r not in profile fonts' % tf))


    # --- visual: overflow / emphasis / text budget ---
    if visual:
        visual_checks(prs, idx, slide, profile, findings)



# --------------------------------------------------------------------------
# visual checks -- L1 overflow, L2 emphasis, L3 text budget
#
# The rubric has always said text overflowing its OWN shape is invisible to a
# static check and can only be found in the PNG. That was true while nothing
# measured text. L1 estimates it. It is deliberately MEDIUM and deliberately
# generous: it is a pre-filter that saves a render cycle, not a replacement for
# looking at the render.
# --------------------------------------------------------------------------

VISUAL_DEFAULTS = {
    'key_message_max_lines': 2,
    'key_message_max_chars': 30,
    'body_char_budget': 450,
    'emphasis_budget': 3,
    # shape-name prefixes whose text is NOT body text (visual-design.md §5):
    # titles, chapter labels, navigation, source lines, diagram part labels,
    # table reference columns, legend headers, pictogram glyphs
    'uncounted': ['title:', 'chapter:', 'nav:', 'src:', 'label:', 'ref:', 'legend:',
                  'Pictogram'],
}
_CJK_PUNCT_END = '。、．，！？」』）】・:：'
_CJK_PUNCT_START = '（「『【・'
_PAREN_OPEN = '（(【'
_PAREN_CLOSE = '）)】'


def _is_hira(c):
    return '\u3041' <= c <= '\u309f'


def _is_kata(c):
    return ('\u30a1' <= c <= '\u30ff') or c == 'ー'


def _is_cjk_letter(c):
    return _is_hira(c) or _is_kata(c) or ('\u4e00' <= c <= '\u9fff')


def phrase_break_defect(a, b, phrase_breaks):
    """Why the paragraph break between a and b looks like a break INSIDE a word/phrase,
    or None. Deliberately narrow: two unrelated lines in one text box (list items, a label
    and its sub-label) must not fire -- on real decks a naive BudouX comparison flagged 28
    of 37 slides. The three shapes it does catch are the ones reviewers actually raised:

      1. 「指示して／いるのは」   b starts with hiragana (okurigana / particle continues a)
      2. 「システムエン／ジニアリング」   katakana word split across lines
      3. 「（SES＝／準委任契約の呼び名）」   a short parenthetical broken open

    Shapes 1 and 2 additionally require BudouX to find NO phrase boundary at the break.
    """
    a, b = a.strip(), b.strip()
    if not a or not b or a[-1] in _CJK_PUNCT_END or b[0] in _CJK_PUNCT_START:
        return None
    if not any(_is_cjk_letter(c) for c in a + b):
        return None                      # Latin-only text (code, URLs) is not 文節 territory
    # 3. a short parenthetical (<= 24 chars) left open at the line end
    for o, c in zip(_PAREN_OPEN, _PAREN_CLOSE):
        i = a.rfind(o)
        if i != -1 and c not in a[i:]:
            j = b.find(c)
            if j != -1 and (len(a) - i) + j + 1 <= 24:
                return 'parenthetical %r broken open' % (a[i:] + '／' + b[:j + 1])
    if not _is_cjk_letter(a[-1]) or not _is_cjk_letter(b[0]):
        return None
    hira_cont = _is_hira(b[0])
    kata_split = _is_kata(a[-1]) and _is_kata(b[0])
    if not (hira_cont or kata_split):
        return None
    if phrase_breaks is None:
        return None
    phrases = phrase_breaks(a + b) or []
    cuts, pos = set(), 0
    for ph in phrases:
        pos += len(ph)
        cuts.add(pos)
    if len(a) in cuts:
        return None
    return 'hiragana continuation' if hira_cont else 'katakana word split'
_EMU_IN = 914400.0
_DEF_INS = {'lIns': 91440, 'tIns': 45720, 'rIns': 91440, 'bIns': 45720}


def _visual_cfg(profile):
    cfg = dict(VISUAL_DEFAULTS)
    cfg.update((profile or {}).get('visual') or {})
    return cfg


def _runs_of(p_el, etree):
    """[(text, pt, font, bold, colour, highlighted)] for one <a:p>."""
    out = []
    for r in p_el.findall(q(A, 'r')):
        t = r.find(q(A, 't'))
        if t is None or not t.text:
            continue
        rPr = r.find(q(A, 'rPr'))
        pt, font, bold, colour, hl = 18.0, '', False, None, False
        if rPr is not None:
            try:
                pt = int(rPr.get('sz')) / 100.0 if rPr.get('sz') else 18.0
            except ValueError:
                pt = 18.0
            bold = rPr.get('b') == '1'
            lat = rPr.find(q(A, 'latin'))
            font = lat.get('typeface') if lat is not None else ''
            fill = rPr.find(q(A, 'solidFill'))
            if fill is not None:
                c = fill.find(q(A, 'srgbClr'))
                if c is not None and c.get('val'):
                    colour = c.get('val').upper()
            hl = rPr.find(q(A, 'highlight')) is not None
        out.append((t.text, pt, font or '', bold, colour, hl))
    return out


def visual_checks(prs, idx, slide, profile, findings):
    from lxml import etree
    from pptx.util import Emu
    try:
        from deckkit import _em, is_fullwidth
    except Exception:
        return                                    # measurement unavailable
    try:
        from deckkit import phrase_breaks         # None at call time without budoux
    except Exception:
        phrase_breaks = None
    where = 'slide %d' % idx
    cfg = _visual_cfg(profile)
    uncounted_prefixes = tuple(cfg.get('uncounted') or ())
    pal = (profile or {}).get('palette') or {}
    accents = {v.upper() for k, v in pal.items() if k.startswith('accent')}
    bright = {v.upper() for k, v in pal.items()
              if k in ('text_bright', 'bg_alt')}

    total_chars = 0
    uncounted_chars = 0   # text in shapes named with a visual.uncounted prefix
    emphasis = 0          # emphasis spans INSIDE a sentence
    any_mark = 0          # any bold / accent / highlight run at all
    for el in slide.shapes._spTree:
        if etree.QName(el).localname != 'sp':
            continue
        body = el.find(q(P, 'txBody'))
        xfrm = el.find('.//' + q(A, 'xfrm'))
        if body is None or xfrm is None:
            continue
        # A shape with no text cannot overflow. Decorative geometry -- pictogram
        # strokes, rules, panels -- is thinner than the default text insets, so
        # measuring it yields a NEGATIVE available height and a false positive.
        if not any((t.text or '').strip() for t in body.iter(q(A, 't'))):
            continue
        cnv = el.find('.//' + q(P, 'cNvPr'))
        sid = cnv.get('id') if cnv is not None else '?'
        sname = (cnv.get('name') or '') if cnv is not None else ''
        exempt = sname.startswith(uncounted_prefixes) if uncounted_prefixes else False
        ext = xfrm.find(q(A, 'ext'))
        if ext is None:
            continue
        w_in = int(ext.get('cx')) / _EMU_IN
        h_in = int(ext.get('cy')) / _EMU_IN

        bodyPr = body.find(q(A, 'bodyPr'))
        ins = dict(_DEF_INS)
        wrap, autofit = 'square', False
        if bodyPr is not None:
            for k in ins:
                if bodyPr.get(k) is not None:
                    ins[k] = int(bodyPr.get(k))
            wrap = bodyPr.get('wrap') or 'square'
            autofit = bodyPr.find(q(A, 'normAutofit')) is not None
        avail_w = w_in - (ins['lIns'] + ins['rIns']) / _EMU_IN
        avail_h = h_in - (ins['tIns'] + ins['bIns']) / _EMU_IN
        if avail_w <= 0.05:
            continue

        used_h, worst = 0.0, None
        ptexts = []
        for p_el in body.findall(q(A, 'p')):
            runs = _runs_of(p_el, etree)
            if not runs:
                continue          # an empty paragraph draws nothing
            ptexts.append((''.join(r[0] for r in runs),
                           all(r[2] in ('Courier New', 'Consolas', 'MS Gothic') for r in runs)))
            width = 0.0
            marked = [bool(b or h or (c in accents) or (c in bright))
                      for _, _, _, b, c, h in runs]
            # A paragraph where EVERY run is marked is a heading or a table
            # header, not emphasis. Emphasis is a span that stands out from
            # ordinary text beside it -- so only count marks in mixed paragraphs.
            mixed = any(marked) and not all(marked)
            any_mark += sum(marked)
            if mixed:
                emphasis += sum(marked)
            for text, pt, font, bold, colour, hl in runs:
                if exempt:
                    uncounted_chars += len(text.strip())
                else:
                    total_chars += len(text.strip())
                mono = font in ('Courier New', 'Consolas', 'MS Gothic')
                for ch in text:
                    width += (pt / 72.0) * _em(ch, mono)
            max_pt = max(r[1] for r in runs)
            spc = 1.0
            pPr = p_el.find(q(A, 'pPr'))
            if pPr is not None:
                ln = pPr.find(q(A, 'lnSpc'))
                if ln is not None:
                    pct = ln.find(q(A, 'spcPct'))
                    if pct is not None and pct.get('val'):
                        spc = int(pct.get('val')) / 100000.0
            if wrap == 'none':
                lines = 1
                if width > avail_w * 1.02 and (worst is None or width > worst[0]):
                    worst = (width, ''.join(r[0] for r in runs)[:34])
            else:
                lines = max(1, int(width / avail_w) + (1 if width % avail_w else 0))
                if lines > 1 and width > avail_w * 1.02 and worst is None:
                    worst = (width, ''.join(r[0] for r in runs)[:34])
            used_h += lines * (max_pt / 72.0) * 1.21 * spc

        # A 0.14in label "needing" 0.16in is line-height rounding, not overflow.
        # Require BOTH a relative and an absolute overshoot before speaking up.
        if not autofit and used_h > avail_h * 1.10 + 0.03:
            findings.append((where, 'MEDIUM',
                             'shape %s: text needs about %.2fin but the shape is '
                             '%.2fin tall -- likely OVERFLOWS (estimate; confirm in '
                             'the PNG)' % (sid, used_h, avail_h)))
        elif wrap == 'none' and worst:
            findings.append((where, 'MEDIUM',
                             'shape %s: wrap="none" line is about %.2fin wide in a '
                             '%.2fin box -- %r will be clipped'
                             % (sid, worst[0], avail_w, worst[1])))

        # R8-2: a hand-written line break inside a word / short parenthetical.
        # Needs budoux for shapes 1-2; silent without it. See phrase_break_defect().
        if not exempt and len(ptexts) >= 2:
            for (a_txt, a_code), (b_txt, b_code) in zip(ptexts, ptexts[1:]):
                if a_code or b_code:
                    continue                 # code lines break where the code breaks
                why = phrase_break_defect(a_txt, b_txt, phrase_breaks)
                if why:
                    findings.append((where, 'LOW',
                                     'shape %s: line break inside a phrase (%s) -- %r / %r '
                                     '(estimate; break at a 文節 boundary) [R8-2]'
                                     % (sid, why, a_txt.strip()[-8:], b_txt.strip()[:8])))
                    break

    if total_chars:
        if any_mark == 0:
            findings.append((where, 'LOW',
                             'no emphasised run on this slide (no bold, no accent '
                             'colour, no highlight) -- nothing tells the reader '
                             'where to look first [R8-4]'))
        elif emphasis == 0 and total_chars > 150:
            # Bold headings alone do not guide a reader THROUGH a sentence. This
            # is the shape a text-heavy deck takes when every emphasis decision
            # was made at the label level and none inside the prose.
            findings.append((where, 'LOW',
                             'every marked run is a whole label; no keyword is '
                             'emphasised INSIDE a sentence [R8-4]'))
        elif emphasis > cfg['emphasis_budget'] * 2:
            findings.append((where, 'LOW',
                             '%d in-sentence emphasis spans, budget is about %d -- '
                             'emphasis everywhere reads as emphasis nowhere [R8-5]'
                             % (emphasis, cfg['emphasis_budget'])))
        if total_chars > cfg['body_char_budget']:
            findings.append((where, 'LOW',
                             '%d characters of body text%s, budget %d -- over by %d. '
                             'Plan a split or move content; replacing prose with a '
                             'diagram rarely lowers the count (labels are characters). '
                             'Unnamed labels/sources/nav? name them with a visual.uncounted '
                             'prefix [R8-7]'
                             % (total_chars,
                                ' (+%d in uncounted shapes)' % uncounted_chars if uncounted_chars else '',
                                cfg['body_char_budget'],
                                total_chars - cfg['body_char_budget'])))


def infer_profile(prs):
    from lxml import etree
    from pptx.util import Emu
    colors = collections.Counter()
    fonts = collections.Counter()
    for slide in prs.slides:
        for el in slide.shapes._spTree:
            for c in el.iter(q(A, 'srgbClr')):
                if c.get('val'):
                    colors[c.get('val').upper()] += 1
            for t in el.iter(q(A, 'latin')):
                if t.get('typeface'):
                    fonts[t.get('typeface')] += 1
    top_fonts = [f for f, _ in fonts.most_common(3)]
    return {
        'language': 'ja',
        'geometry': {'width_in': round(Emu(prs.slide_width).inches, 3),
                     'height_in': round(Emu(prs.slide_height).inches, 3)},
        'fonts': {'sans': top_fonts[0] if top_fonts else 'Calibri',
                  'mono': next((f for f in top_fonts if 'Courier' in f or 'Mono' in f),
                               'Courier New'),
                  'cjk': next((f for f in top_fonts if 'Gothic' in f or 'Mincho' in f),
                              'Yu Gothic')},
        'palette': {('c%02d' % i): c for i, (c, _) in enumerate(colors.most_common(12))},
        'conventions': [],
        'source_notation': 'SRC-NNN',
        'id_prefixes': {'finding': 'FINDING', 'source': 'SRC', 'decision': 'DEC',
                        'question': 'OQ', 'comment': 'CMT'},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('deck')
    ap.add_argument('--profile')
    ap.add_argument('--slide', type=int, help='check only this 1-based slide')
    ap.add_argument('--infer-profile', action='store_true')
    ap.add_argument('--quiet', action='store_true', help='only CRITICAL/HIGH')
    ap.add_argument('--no-visual', dest='visual', action='store_false',
                    help='skip the overflow / emphasis / text-budget estimates')
    ap.add_argument('--contrast', action='store_true',
                    help='also check text/background contrast. Advisory: text often '
                         'sits on a separate filled shape, so expect false positives '
                         'on mature decks. Best on a freshly generated deck.')
    a = ap.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    try:
        from pptx import Presentation
        prs = Presentation(a.deck)
    except Exception as e:
        print('cannot read deck: %s' % e)
        return 2

    if a.infer_profile:
        print(json.dumps(infer_profile(prs), ensure_ascii=False, indent=2))
        return 0

    profile = None
    if a.profile:
        try:
            with open(a.profile, encoding='utf-8') as f:
                profile = json.load(f)
        except Exception as e:
            print('cannot read profile: %s' % e)
            return 2

    findings = []
    targets = [a.slide] if a.slide else range(1, len(prs.slides) + 1)
    for i in targets:
        check_slide(prs, i, prs.slides[i - 1], profile, findings, a.contrast,
                    a.visual)

    order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
    if a.quiet:
        findings = [f for f in findings if f[1] in ('CRITICAL', 'HIGH')]
    findings.sort(key=lambda f: order.get(f[1], 9))

    if not findings:
        print('%s: %d slides, no findings' % (a.deck, len(prs.slides)))
        return 0

    counts = collections.Counter(f[1] for f in findings)
    print('%s: %d slides, %d findings (%s)'
          % (a.deck, len(prs.slides), len(findings),
             ', '.join('%s=%d' % (k, counts[k]) for k in
                       ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] if counts[k])))
    for where, sev, msg in findings:
        print('  [%-8s] %-9s %s' % (sev, where, msg))
    return 1 if any(f[1] in ('CRITICAL', 'HIGH') for f in findings) else 0


if __name__ == '__main__':
    sys.exit(main())
