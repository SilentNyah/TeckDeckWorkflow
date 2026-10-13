# -*- coding: utf-8 -*-
"""Monochrome pictograms composed from PowerPoint preset geometries.

Why not an icon font or an SVG set: an icon has to take its colour from the
deck's palette to look like it belongs, it has to survive a machine that has
never heard of your font, and it must not drag a licence into the project.
Shapes drawn from prstGeom satisfy all three -- they are vector, recolourable,
and made of nothing but the file itself.

    import sys
    sys.path.insert(0, r'<pptx-toolkit>/scripts')
    from pictogram import draw, CATALOG, contact_sheet

    draw(slide, 'warning', 1.0, 2.0, size=0.55, color=PAL['accent_red'], bg=PAL['bg'])

`bg` is the knock-out colour -- the '!' inside a filled triangle, the windows in
a building. Pass the colour the icon actually sits on, not always palette.bg.

`size` is the COMPOSITION box, not the drawn extent. Most glyphs inset their strokes
(`cross` keeps 4% inside), so draw(..., 0.628, y, size=0.184) does not give you a
0.184-in glyph at x=0.628 -- it lands at 0.635 / 0.169. Decide the drawn box you want,
call draw() once, read the real xfrm back with `inspect_deck.py --slide N`, and derive
the arguments from that (for `cross`: draw(..., 0.620, y, size=0.200)). Put the CALL
ARGUMENTS in the storyboard, never the measured box; six slides re-derived this.

Run this file directly to write a labelled contact sheet of every pictogram:

    python pictogram.py out.pptx --profile slides/deck-profile.json
"""
import deckkit as _dk

# Each op is one shape drawn in a 0..1 box:
#   prst  : preset geometry name                      (or)
#   text  : a character to centre, em = size fraction
#   role  : 'fg'      solid fill in `color`
#           'out'     no fill, outline in `color`
#           'knock'   solid fill in `bg`   (holes punched in an fg shape)
#           'fgtext'  text in `color`
#           'bgtext'  text in `bg`
#   x,y,w,h are fractions of the icon box; rot is degrees.

CATALOG = {
    # ---- status -----------------------------------------------------------
    'warning': [
        dict(prst='triangle', x=.00, y=.04, w=1., h=.94, role='fg', adj=None),
        dict(text='!', x=.00, y=.30, w=1., h=.60, em=.46, role='bgtext', b=True),
    ],
    'prohibited': [
        dict(prst='noSmoking', x=.02, y=.02, w=.96, h=.96, role='fg'),
    ],
    'check': [
        dict(prst='rect', x=.06, y=.55, w=.40, h=.155, role='fg', rot=45),
        dict(prst='rect', x=.24, y=.42, w=.78, h=.155, role='fg', rot=-49),
    ],
    'cross': [
        dict(prst='mathMultiply', x=.04, y=.04, w=.92, h=.92, role='fg',
             adj={'adj1': 25000}),
    ],
    'check-circle': [
        dict(prst='ellipse', x=.00, y=.00, w=1., h=1., role='fg'),
        dict(prst='rect', x=.20, y=.53, w=.28, h=.115, role='knock', rot=45),
        dict(prst='rect', x=.33, y=.44, w=.54, h=.115, role='knock', rot=-49),
    ],
    'cross-circle': [
        dict(prst='ellipse', x=.00, y=.00, w=1., h=1., role='fg'),
        dict(prst='mathMultiply', x=.22, y=.22, w=.56, h=.56, role='knock',
             adj={'adj1': 30000}),
    ],
    'question': [
        dict(prst='ellipse', x=.00, y=.00, w=1., h=1., role='fg'),
        dict(text='?', x=.00, y=.06, w=1., h=.88, em=.58, role='bgtext', b=True),
    ],
    'flag': [
        dict(prst='rect', x=.13, y=.02, w=.095, h=.96, role='fg'),
        dict(prst='homePlate', x=.225, y=.06, w=.71, h=.46, role='fg',
             flipH=True, adj=26000),
    ],
    'star': [
        dict(prst='star5', x=.00, y=.02, w=1., h=.96, role='fg'),
    ],
    'lightning': [
        dict(prst='lightningBolt', x=.14, y=.00, w=.72, h=1., role='fg'),
    ],

    # ---- people / organisation -------------------------------------------
    'person': [
        dict(prst='ellipse', x=.30, y=.02, w=.40, h=.40, role='fg'),
        dict(prst='flowChartManualOperation', x=.07, y=.50, w=.86, h=.46,
             role='fg', flipV=True),
    ],
    # Two figures, back-then-front. Every head is centred on ITS OWN body
    # (head cx == body cx) and both figures reach the same bottom edge -- get
    # either wrong and the icon reads as heads floating beside the shoulders.
    'people': [
        dict(prst='ellipse', x=.61, y=.06, w=.28, h=.28, role='fg'),   # cx .75
        dict(prst='flowChartManualOperation', x=.50, y=.42, w=.50, h=.54,
             role='fg', flipV=True),                                   # cx .75
        # halo: the front body grown ~.045, punched out of the back one so the
        # two do not fuse into one blob. Nothing else sits under it.
        dict(prst='flowChartManualOperation', x=.005, y=.48, w=.71, h=.50,
             role='knock', flipV=True),
        dict(prst='ellipse', x=.195, y=.10, w=.34, h=.34, role='fg'),  # cx .365
        dict(prst='flowChartManualOperation', x=.055, y=.525, w=.62, h=.435,
             role='fg', flipV=True),                                   # cx .365
    ],
    'building': [
        dict(prst='rect', x=.10, y=.08, w=.80, h=.92, role='fg'),
        dict(prst='rect', x=.22, y=.22, w=.18, h=.15, role='knock'),
        dict(prst='rect', x=.60, y=.22, w=.18, h=.15, role='knock'),
        dict(prst='rect', x=.22, y=.46, w=.18, h=.15, role='knock'),
        dict(prst='rect', x=.60, y=.46, w=.18, h=.15, role='knock'),
        dict(prst='rect', x=.38, y=.72, w=.24, h=.28, role='knock'),
    ],

    # ---- documents / law --------------------------------------------------
    'document': [
        dict(prst='flowChartDocument', x=.10, y=.06, w=.80, h=.88, role='fg'),
    ],
    'contract': [
        dict(prst='flowChartDocument', x=.10, y=.06, w=.80, h=.88, role='fg'),
        dict(prst='rect', x=.24, y=.24, w=.52, h=.075, role='knock'),
        dict(prst='rect', x=.24, y=.40, w=.52, h=.075, role='knock'),
        dict(prst='rect', x=.24, y=.56, w=.32, h=.075, role='knock'),
    ],
    'scale': [
        dict(prst='rect', x=.46, y=.12, w=.08, h=.56, role='fg'),
        dict(prst='rect', x=.04, y=.22, w=.92, h=.07, role='fg'),
        dict(prst='rect', x=.16, y=.29, w=.035, h=.14, role='fg'),
        dict(prst='rect', x=.805, y=.29, w=.035, h=.14, role='fg'),
        dict(prst='flowChartManualOperation', x=.00, y=.41, w=.36, h=.19,
             role='fg'),
        dict(prst='flowChartManualOperation', x=.64, y=.41, w=.36, h=.19,
             role='fg'),
        dict(prst='triangle', x=.30, y=.64, w=.40, h=.30, role='fg'),
        dict(prst='rect', x=.22, y=.92, w=.56, h=.07, role='fg'),
    ],
    'gavel': [
        dict(prst='rect', x=.10, y=.60, w=.66, h=.115, role='fg', rot=-38),
        dict(prst='roundRect', x=.52, y=.06, w=.44, h=.30, role='fg',
             rot=52, adj=20000),
        dict(prst='rect', x=.06, y=.92, w=.60, h=.08, role='fg'),
    ],
    'money': [
        dict(prst='ellipse', x=.02, y=.02, w=.96, h=.96, role='fg'),
        dict(text='\u00a5', x=.02, y=.06, w=.96, h=.88, em=.60,
             role='bgtext', b=True),
    ],

    # ---- process / structure ---------------------------------------------
    'arrow-right': [
        dict(prst='rightArrow', x=.00, y=.26, w=1., h=.48, role='fg',
             adj=[50000, 48000]),
    ],
    'arrow-cycle': [
        dict(prst='ellipse', x=.09, y=.14, w=.82, h=.82, role='out', lw=3.4),
        dict(prst='rect', x=.48, y=.02, w=.58, h=.30, role='knock'),
        dict(prst='triangle', x=.60, y=.06, w=.34, h=.30, role='fg', rot=118),
    ],
    'link': [
        dict(prst='roundRect', x=.01, y=.32, w=.60, h=.34, role='out', lw=3,
             adj=50000, rot=-28),
        dict(prst='roundRect', x=.39, y=.32, w=.60, h=.34, role='out', lw=3,
             adj=50000, rot=-28),
    ],
    'broken-link': [
        dict(prst='roundRect', x=-.10, y=.34, w=.54, h=.32, role='out', lw=3,
             adj=50000, rot=-28),
        dict(prst='roundRect', x=.56, y=.34, w=.54, h=.32, role='out', lw=3,
             adj=50000, rot=-28),
        dict(prst='rect', x=.42, y=.06, w=.05, h=.22, role='fg', rot=-28),
        dict(prst='rect', x=.55, y=.72, w=.05, h=.22, role='fg', rot=-28),
    ],
    'clock': [
        dict(prst='ellipse', x=.03, y=.03, w=.94, h=.94, role='out', lw=3),
        dict(prst='rect', x=.47, y=.20, w=.065, h=.33, role='fg'),
        dict(prst='rect', x=.47, y=.46, w=.28, h=.065, role='fg'),
    ],
    'search': [
        dict(prst='ellipse', x=.02, y=.02, w=.68, h=.68, role='out', lw=3),
        dict(prst='rect', x=.54, y=.72, w=.44, h=.11, role='fg', rot=45),
    ],
    'shield': [
        dict(prst='rect', x=.10, y=.04, w=.80, h=.44, role='fg'),
        dict(prst='triangle', x=.10, y=.46, w=.80, h=.50, role='fg',
             flipV=True),
    ],
    'shield-check': [
        dict(prst='rect', x=.10, y=.04, w=.80, h=.44, role='fg'),
        dict(prst='triangle', x=.10, y=.46, w=.80, h=.50, role='fg',
             flipV=True),
        dict(prst='rect', x=.22, y=.43, w=.26, h=.10, role='knock', rot=45),
        dict(prst='rect', x=.34, y=.34, w=.50, h=.10, role='knock', rot=-49),
    ],

    # ---- systems ----------------------------------------------------------
    'database': [
        dict(prst='can', x=.14, y=.04, w=.72, h=.92, role='fg', adj=22000),
    ],
    'server': [
        dict(prst='rect', x=.06, y=.06, w=.88, h=.24, role='fg'),
        dict(prst='rect', x=.06, y=.38, w=.88, h=.24, role='fg'),
        dict(prst='rect', x=.06, y=.70, w=.88, h=.24, role='fg'),
        dict(prst='ellipse', x=.14, y=.14, w=.09, h=.09, role='knock'),
        dict(prst='ellipse', x=.14, y=.46, w=.09, h=.09, role='knock'),
        dict(prst='ellipse', x=.14, y=.78, w=.09, h=.09, role='knock'),
    ],
    'code': [
        dict(text='</>', x=.00, y=.00, w=1., h=1., em=.50, role='fgtext',
             b=True, mono=True),
    ],
    'bug': [
        dict(prst='ellipse', x=.34, y=.02, w=.32, h=.26, role='fg'),
        dict(prst='ellipse', x=.24, y=.24, w=.52, h=.72, role='fg'),
        dict(prst='rect', x=.02, y=.36, w=.24, h=.065, role='fg', rot=-18),
        dict(prst='rect', x=.02, y=.58, w=.24, h=.065, role='fg'),
        dict(prst='rect', x=.02, y=.78, w=.24, h=.065, role='fg', rot=18),
        dict(prst='rect', x=.74, y=.36, w=.24, h=.065, role='fg', rot=18),
        dict(prst='rect', x=.74, y=.58, w=.24, h=.065, role='fg'),
        dict(prst='rect', x=.74, y=.78, w=.24, h=.065, role='fg', rot=-18),
    ],
    'idea': [
        dict(prst='ellipse', x=.20, y=.02, w=.60, h=.62, role='fg'),
        dict(prst='rect', x=.36, y=.62, w=.28, h=.16, role='fg'),
        dict(prst='rect', x=.34, y=.82, w=.32, h=.10, role='fg'),
    ],
    'chart': [
        dict(prst='rect', x=.06, y=.58, w=.22, h=.40, role='fg'),
        dict(prst='rect', x=.39, y=.30, w=.22, h=.68, role='fg'),
        dict(prst='rect', x=.72, y=.06, w=.22, h=.92, role='fg'),
    ],
    'lock': [
        dict(prst='ellipse', x=.25, y=.04, w=.50, h=.62, role='out', lw=3.4),
        dict(prst='roundRect', x=.06, y=.42, w=.88, h=.56, role='fg',
             adj=16000),
        dict(prst='ellipse', x=.43, y=.60, w=.14, h=.14, role='knock'),
    ],
}


def draw(slide, name, x, y, size=0.5, color=None, bg=None, aspect=1.0,
         lw_pt=None):
    """Draw one pictogram. Returns the list of created elements.

    x, y   top-left in inches
    size   height in inches (width = size * aspect)
    color  the ink; bg the knock-out colour it sits on
    """
    try:
        ops = CATALOG[name]
    except KeyError:
        raise KeyError('unknown pictogram %r. Known: %s'
                       % (name, ', '.join(sorted(CATALOG))))
    color = color or _dk.DEFAULTS['text']
    bg = bg or 'FFFFFF'
    w_box, h_box = size * aspect, size
    out = []
    for op in ops:
        ox = x + op.get('x', 0) * w_box
        oy = y + op.get('y', 0) * h_box
        ow = op.get('w', 1) * w_box
        oh = op.get('h', 1) * h_box
        role = op.get('role', 'fg')
        if 'text' in op:
            font = _dk.DEFAULTS['font']
            if op.get('mono'):
                font = 'Consolas'
            run = _dk.R(op['text'], op.get('em', .5) * h_box * 72,
                        bg if role == 'bgtext' else color, font,
                        b=op.get('b', False))
            out.append(_dk.shape(slide, 'rect', ox, oy, ow, oh, fill=None,
                                 line=None, runs=[run], algn='ctr',
                                 anchor='ctr', ins=0, style=False,
                                 name='Pictogram'))
            continue
        kw = dict(adj=op.get('adj'), rot=op.get('rot'),
                  flipH=op.get('flipH', False), flipV=op.get('flipV', False),
                  style=False, name='Pictogram')
        if role == 'out':
            kw.update(fill=None, line=color,
                      lw=int((lw_pt or op.get('lw', 2)) * 12700))
        elif role == 'knock':
            kw.update(fill=bg, line=None)
        else:
            kw.update(fill=color, line=None)
        out.append(_dk.shape(slide, op['prst'], ox, oy, ow, oh, **kw))
    return out


def names():
    return sorted(CATALOG)


def contact_sheet(out_path, profile=None, cols=None, size=0.62):
    """Write a deck with every pictogram, labelled, paginated to fit the
    profile's slide size. Render it and LOOK at it -- a preset geometry that
    does not compose the way you expected is invisible until you do.

    The grid is DERIVED from geometry, not fixed at 8 columns: on a 10in deck a
    fixed 8x1.58in grid runs 2.6in off the right edge and the rows spill off the
    bottom, so the icons you most want to check are the ones you cannot see.
    """
    import json
    from pptx import Presentation                      # noqa: F401
    pal = {'bg': 'FDFBF8', 'text': '554031', 'accent_red': 'C00000'}
    fonts = {'sans': 'Calibri', 'cjk': 'Calibri'}
    geom = {'width_in': 13.333, 'height_in': 7.5}
    if profile:
        prof = json.load(open(profile, encoding='utf-8'))
        pal.update(prof.get('palette') or {})
        fonts.update(prof.get('fonts') or {})
        geom.update(prof.get('geometry') or {})
    W, H = float(geom['width_in']), float(geom['height_in'])
    _dk.use_defaults(text=pal['text'], rule=pal.get('rule', pal['text']),
                     font=fonts.get('cjk') or fonts['sans'])

    margin, top = .5, .95
    cell_w, dy = max(size + .5, 1.30), size + .62
    cols = cols or max(1, int((W - 2 * margin) // cell_w))
    rows = max(1, int((H - top - .25) // dy))
    per_slide = cols * rows
    dx = (W - 2 * margin) / cols
    ink = pal.get('accent_red', pal['text'])
    muted = pal.get('muted', pal['text'])

    prs = _dk.new_presentation(W, H)
    allnames = names()
    pages = (len(allnames) + per_slide - 1) // per_slide
    for page in range(pages):
        s = _dk.add_slide(prs, bg=pal['bg'])
        head = 'pictogram.py contact sheet'
        if pages > 1:
            head += '  (%d/%d)' % (page + 1, pages)
        _dk.textbox(s, margin, .25, W - 2 * margin, .4,
                    [[_dk.R(head, 18, pal['text'], fonts['sans'], b=True)]],
                    algn='l')
        for i, nm in enumerate(allnames[page * per_slide:(page + 1) * per_slide]):
            cx = margin + (i % cols) * dx
            cy = top + (i // cols) * dy
            draw(s, nm, cx + (dx - size) / 2, cy, size=size,
                 color=ink, bg=pal['bg'])
            _dk.textbox(s, cx, cy + size + .04, dx, .24,
                        [[_dk.R(nm, 8.5, muted, fonts['sans'])]], algn='ctr')
    prs.save(out_path)
    return out_path


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('out')
    ap.add_argument('--profile')
    a = ap.parse_args()
    print(contact_sheet(a.out, a.profile))
