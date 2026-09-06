# -*- coding: utf-8 -*-
"""Create a new .pptx with the right size, background and palette.

python-pptx's bare Presentation() is 10x7.5in (4:3) with a WHITE canvas, and
deckkit's default text colour is near-white -- so a naive new deck renders
white-on-white and every storyboard y-coordinate is wrong. This script exists
so that never happens.

    python new_deck.py slides/deck.pptx
    python new_deck.py slides/deck.pptx --preset light
    python new_deck.py slides/deck.pptx --profile slides/deck-profile.json
    python new_deck.py slides/deck.pptx --slides 0 --no-theme
    python new_deck.py out.pptx --preset dark --write-profile slides/deck-profile.json

Exit: 0 created · 1 bad arguments / unreadable profile · 2 target exists.
"""
import argparse
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRESET_DIR = os.path.join(os.path.dirname(HERE), 'templates', 'presets')
sys.path.insert(0, HERE)


def resolve_profile(preset, profile_path):
    """-> (profile dict, human-readable source)."""
    if profile_path:
        if not os.path.exists(profile_path):
            sys.exit('no such profile: %s' % profile_path)
        with open(profile_path, encoding='utf-8') as f:
            return json.load(f), profile_path
    path = os.path.join(PRESET_DIR, '%s.json' % preset)
    if not os.path.exists(path):
        avail = sorted(f[:-5] for f in os.listdir(PRESET_DIR)
                       if f.endswith('.json')) if os.path.isdir(PRESET_DIR) else []
        sys.exit('unknown preset %r. available: %s' % (preset, ', '.join(avail) or '(none)'))
    with open(path, encoding='utf-8') as f:
        return json.load(f), 'preset:%s' % preset


def derive_sz_type(w, h, explicit):
    if explicit:
        return None if explicit == 'none' else explicit
    ratio = w / h if h else 0
    if abs(ratio - 16 / 9.0) < 0.01:
        return 'screen16x9'
    if abs(ratio - 4 / 3.0) < 0.01:
        return 'screen4x3'
    return None


def title_slide(prs, pal, fonts, title, subtitle, w, h):
    """A placeholder title slide, drawn with the same primitives Phase 3 uses.

    Its real job is proof: if this renders legibly, then background, text and
    rule colours are mutually visible in this palette.
    """
    from deckkit import add_slide, textbox, connector, R
    s = add_slide(prs, bg=pal['bg'])
    sans = fonts.get('cjk') or fonts.get('sans', 'Calibri')
    mono = fonts.get('mono', 'Courier New')
    left, right = 0.9, w - 0.9
    textbox(s, left, h * 0.34, right - left, 0.62,
            [[R(title, 30, pal['text'], sans, b=True)]], algn='l')
    connector(s, left, h * 0.50, right - left, 0, color=pal['rule'], lw=12700)
    textbox(s, left, h * 0.53, right - left, 0.30,
            [[R(subtitle, 12, pal.get('muted', pal['text']), sans)]], algn='l')
    textbox(s, left, h - 0.55, right - left, 0.20,
            [[R('Phase 0 が置いた仮スライド ─ Phase 3 で storyboard に基づき作り直す',
                8, pal.get('dim', pal['text']), mono, i=True)]], algn='l')
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('out')
    ap.add_argument('--preset', default='dark')
    ap.add_argument('--profile')
    ap.add_argument('--write-profile', nargs='?', const='__auto__',
                    help='also write the resolved profile (default: alongside the deck)')
    ap.add_argument('--width', type=float)
    ap.add_argument('--height', type=float)
    ap.add_argument('--sz-type', choices=['screen16x9', 'screen4x3', 'custom', 'none'])
    ap.add_argument('--slides', type=int, default=1)
    ap.add_argument('--title')
    ap.add_argument('--subtitle')
    ap.add_argument('--no-theme', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')

    if os.path.exists(a.out) and not a.force:
        print('refusing to overwrite existing %s\n'
              'pass --force to replace it (a timestamped backup is made first)' % a.out)
        return 2

    profile, src = resolve_profile(a.preset, a.profile)
    pal = profile.get('palette') or {}
    if 'bg' not in pal or 'text' not in pal:
        sys.exit('profile needs at least palette.bg and palette.text')
    fonts = profile.get('fonts') or {}
    geo = profile.get('geometry') or {}
    w = a.width or geo.get('width_in', 10.0)
    h = a.height or geo.get('height_in', 5.625)
    sz_type = derive_sz_type(w, h, a.sz_type)

    from deckkit import (new_presentation, set_bg, clear_bg, blank_layout,
                         set_theme_colors, use_defaults, save_backup)

    # so any later batch script that omits a colour still gets this palette
    use_defaults(text=pal['text'], rule=pal.get('rule'),
                 font=fonts.get('sans'))

    prs = new_presentation(w, h, sz_type)

    # Background on the MASTER, cleared on every layout: a slide that forgets
    # its own <p:bg> still inherits the right canvas -- including a slide a
    # human adds by hand in PowerPoint.
    set_bg(prs.slide_masters[0], pal['bg'])
    for lay in prs.slide_layouts:
        clear_bg(lay)

    themed = []
    if not a.no_theme:
        themed = set_theme_colors(prs, {
            'accent1': pal.get('accent_green'), 'accent2': pal.get('accent_amber'),
            'accent3': pal.get('accent_purple'), 'accent4': pal.get('accent_pink'),
            'accent5': pal.get('muted'), 'accent6': pal.get('dim'),
        })

    stem = os.path.splitext(os.path.basename(a.out))[0]
    title = a.title or stem
    subtitle = a.subtitle or datetime.date.today().isoformat()
    for i in range(max(0, a.slides)):
        if i == 0:
            title_slide(prs, pal, fonts, title, subtitle, w, h)
        else:
            from deckkit import add_slide
            add_slide(prs, bg=pal['bg'])

    backup = None
    if os.path.exists(a.out) and a.force:
        backup = save_backup(a.out)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    prs.save(a.out)

    wrote_profile = None
    if a.write_profile:
        p = a.write_profile
        if p == '__auto__':
            p = os.path.join(os.path.dirname(os.path.abspath(a.out)), 'deck-profile.json')
        if not os.path.exists(p):
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
                f.write('\n')
            wrote_profile = p

    info = {
        'deck': a.out, 'profile_source': src, 'size_in': [w, h], 'sz_type': sz_type,
        'bg': pal['bg'], 'slides': max(0, a.slides), 'layout': blank_layout(prs).name,
        'theme_accents': themed, 'wrote_profile': wrote_profile, 'backup': backup,
    }
    if a.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0

    print('%s: created' % a.out)
    print('  size      %.3f x %.3f in, sldSz type=%s' % (w, h, sz_type))
    print('  layout    %r (placeholder-free) of %d' % (info['layout'], len(prs.slide_layouts)))
    print('  bg        %s  (master + every slide)' % pal['bg'])
    print('  theme     %s' % (', '.join(themed) + ' <- palette' if themed else 'untouched'))
    print('  slides    %d%s' % (info['slides'],
                                ' (placeholder title slide)' if info['slides'] else ''))
    print('  profile   %s' % (wrote_profile or '%s (not written)' % src))
    if backup:
        print('  backup    %s' % backup)
    print('next: python check_deck.py %s --profile %s'
          % (a.out, wrote_profile or '<profile.json>'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
