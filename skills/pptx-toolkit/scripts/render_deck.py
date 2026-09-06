# -*- coding: utf-8 -*-
"""Render slides to PNG / PDF via PowerPoint COM. LibreOffice is NOT available.

Rendering is the only way to catch overflow, overlap and blank paragraphs --
python-pptx will happily report text that PowerPoint refuses to draw.

    python render_deck.py <deck.pptx> --slides 39 --png-dir out/
    python render_deck.py <deck.pptx> --slides 20,22-25 --png-dir out/
    python render_deck.py <deck.pptx> --pdf output/pdf/deck.pdf
    python render_deck.py <deck.pptx> --from-pdf output/pdf/deck.pdf --pages 39 --png-dir out/

Requires pywin32 and a local PowerPoint install for PNG/PDF export.
--from-pdf uses pypdfium2 instead and needs neither.
"""
import argparse
import os
import sys


def parse_slides(spec):
    out = []
    for part in str(spec).split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            lo, hi = part.split('-', 1)
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def render_com(deck, slides, png_dir, pdf, width, height, prefix):
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        sys.exit('pywin32 not installed. pip install pywin32\n'
                 '(LibreOffice is not available on this machine.)')
    import win32com.client
    deck = os.path.abspath(deck)
    if not os.path.exists(deck):
        sys.exit('no such deck: %s' % deck)

    app = None
    pres = None
    try:
        app = win32com.client.Dispatch('PowerPoint.Application')
        # ReadOnly=True, Untitled=False, WithWindow=False
        pres = app.Presentations.Open(deck, True, False, False)
    except Exception as e:
        if pres is not None:
            pres.Close()
        if app is not None:
            app.Quit()
        sys.exit('could not open via PowerPoint COM: %s\n'
                 'Is PowerPoint installed and the file valid? A corrupt spTree makes '
                 'PowerPoint refuse a file that python-pptx still opens.' % e)

    made = []
    try:
        total = pres.Slides.Count
        if png_dir:
            os.makedirs(png_dir, exist_ok=True)
            targets = slides or range(1, total + 1)
            for i in targets:
                if not (1 <= i <= total):
                    print('  skip slide %d (deck has %d)' % (i, total))
                    continue
                path = os.path.abspath(os.path.join(png_dir, '%s%d.png' % (prefix, i)))
                pres.Slides(i).Export(path, 'PNG', width, height)
                made.append(path)
                print('  %s' % path)
        if pdf:
            pdf = os.path.abspath(pdf)
            os.makedirs(os.path.dirname(pdf) or '.', exist_ok=True)
            pres.SaveAs(pdf, 32)   # 32 = ppSaveAsPDF
            made.append(pdf)
            print('  %s' % pdf)
    finally:
        try:
            pres.Close()
        except Exception:
            pass
        try:
            app.Quit()
        except Exception:
            pass
    return made


def render_from_pdf(pdf, pages, png_dir, scale, prefix):
    try:
        import pypdfium2 as pdfium
    except ImportError:
        sys.exit('pypdfium2 not installed. pip install pypdfium2')
    os.makedirs(png_dir, exist_ok=True)
    doc = pdfium.PdfDocument(pdf)
    targets = pages or range(1, len(doc) + 1)
    made = []
    for i in targets:
        if not (1 <= i <= len(doc)):
            print('  skip page %d (pdf has %d)' % (i, len(doc)))
            continue
        path = os.path.abspath(os.path.join(png_dir, '%spdf-%d.png' % (prefix, i)))
        doc[i - 1].render(scale=scale / 72.0).to_pil().save(path)
        made.append(path)
        print('  %s' % path)
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('deck', nargs='?')
    ap.add_argument('--slides', help='1-based; "39", "20,22-25". default: all')
    ap.add_argument('--png-dir')
    ap.add_argument('--pdf', help='export whole deck to this PDF')
    ap.add_argument('--width', type=int, default=1600)
    ap.add_argument('--height', type=int, default=900)
    ap.add_argument('--prefix', default='slide-')
    ap.add_argument('--from-pdf', help='raster an existing PDF instead (no PowerPoint)')
    ap.add_argument('--pages', help='with --from-pdf; 1-based page numbers')
    ap.add_argument('--scale', type=float, default=150.0, help='with --from-pdf, DPI')
    a = ap.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    if a.from_pdf:
        if not a.png_dir:
            sys.exit('--from-pdf requires --png-dir')
        render_from_pdf(a.from_pdf, parse_slides(a.pages) if a.pages else None,
                        a.png_dir, a.scale, a.prefix)
        return

    if not a.deck:
        sys.exit('deck path required (or use --from-pdf)')
    if not a.png_dir and not a.pdf:
        sys.exit('nothing to do: pass --png-dir and/or --pdf')

    render_com(a.deck, parse_slides(a.slides) if a.slides else None,
               a.png_dir, a.pdf, a.width, a.height, a.prefix)


if __name__ == '__main__':
    main()
