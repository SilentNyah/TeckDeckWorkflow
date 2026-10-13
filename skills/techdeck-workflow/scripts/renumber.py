# -*- coding: utf-8 -*-
"""renumber — shift slide numbers after a split or insertion, in one pass, across the
Markdown state files of a techdeck-workflow project.

    python renumber.py --insert-after 12                 # dry run: one new slide after 12
    python renumber.py --insert-after 35:2 --insert-after 39:2   # several splits at once
    python renumber.py --map 12:13,13:14                 # explicit old:new pairs
    python renumber.py --insert-after 12 --pages         # also rewrite p.N deck page refs
    python renumber.py --insert-after 12 --rename-reviews --apply

Default is a DRY RUN that prints every change as  file:line  old → new , the tokens it
deliberately did not touch (旧 N, N枚目, スライドN, p.N without --pages) for a human to check,
and — separately — every hit on an APPROVED slide, so the user can be asked once.
Nothing is written without --apply.

What is rewritten (all numbers are mapped from the ORIGINAL numbering, simultaneously):

* `## Slide NNN:` headings and every `Slide NNN` / `Slides 008–015` / `Slide 011・013` token
  (padding follows the original token: 003 → 004, 7 → 8);
* `Previous slide: 002 ／ Next slide: 004` bare numbers;
* table cells under a column whose header is `Slide…`, `#`, `スライド`, `範囲` or `Slides`
  (`27`, `~~41~~`, `1–15`, `3・5`), i.e. the Progress and batch-ledger tables of
  review_state.md and the chapter / slide tables of outline.md;
* carried-forward origins `【b003 / Slide 031 由来 / …】` (covered by the Slide token rule);
* the `* 章: はじめに 1–4／第1章 5–12` and `* バッチ: b001 1–12／…` lines of the Deck
  structure note, and the `（… 3–4）` range in `### バッチ bNNN（…）` headings;
* with --pages, `p.N` / `p.28–29` in storyboard / outline / review_state / glossary only —
  never in source_index.md, where `p.N` is a PDF page.

What is NOT rewritten: `旧 NN` (history), `N枚目`, `スライドN`, dates, `SRC-/DEC-/OQ-/FINDING-/
CF-/R6-` ids, `第N章`, `bNNN`, anything in notes/decisions.md or slides/reviews/*.md contents
(records keep the numbering of their time; the Deck structure note says so). The deck itself is
never edited — `--scan-deck` lists the text it would need the builder to change.

Default files: slides/storyboard.md, slides/outline.md, slides/review_state.md, notes/glossary.md.
`--include-index` adds sources/source_index.md (Slide tokens only). Line endings are preserved
per file.
"""
import argparse
import io
import os
import re
import sys
from dataclasses import dataclass, field

DECK_FILES = ['slides/storyboard.md', 'slides/outline.md', 'slides/review_state.md',
              'notes/glossary.md']
INDEX_FILE = 'sources/source_index.md'


# --------------------------------------------------------------------------- mapping

def build_map(inserts, explicit=None):
    """inserts: [(after_old_number, count), ...]; explicit: {old: new} used exclusively."""
    if explicit:
        return lambda old: explicit.get(old, old)
    ins = sorted(inserts)

    def m(old):
        return old + sum(c for a, c in ins if old > a)
    return m


def fmt_like(tok, new):
    """Format `new` with the width of the original token (zero padding preserved)."""
    return '%0*d' % (len(tok), new)


# --------------------------------------------------------------------------- rewriting

R_SLIDE = re.compile(r'(?<![A-Za-z])(Slides?)(\s*)(\d{1,3})((?:\s*[–\-〜~]\s*\d{1,3})?)((?:・\d{1,3})*)(?!\d)')
R_PREVNEXT = re.compile(r'((?:Previous|Next) slide\s*[:：]\s*)(\d{1,3})(?!\d)')
R_PAGE = re.compile(r'(?<![A-Za-z0-9])(p\.\s?)(\d{1,3})((?:\s*[–\-]\s*\d{1,3})?)(?!\d)')
R_NUM = re.compile(r'\d{1,3}')
# bare range / single tokens on structure-note lines; en dash only (ASCII hyphen = dates)
R_BARE = re.compile(r'(?<![\d第bBrR\-/.])(\d{1,3})(\s*[–〜]\s*)?(?(2)(\d{1,3})?)(?![\d章枚\-/.])')
R_RANGE_ONLY = re.compile(r'(?<![\d第bBrR\-/.])(\d{1,3})(\s*[–〜]\s*)(\d{1,3})?(?![\d章枚\-/.])')
SLIDE_COL = re.compile(r'^\s*(Slide\b.*|#|No\.?|スライド.*|範囲|Slides|Page|ページ)\s*$', re.I)
STRUCT_LINE = re.compile(r'^\s*[\*\-]\s*(章|バッチ)\s*[:：]')
BATCH_HEAD = re.compile(r'^#{2,4}\s+バッチ\s+b\d+')
REVIEW_PATTERNS = [
    (re.compile(r'旧\s*\d{1,3}(?!\d)'), '旧番号（履歴。書き換えない）'),
    (re.compile(r'\d{1,3}\s*枚目'), 'N枚目（順序か枚数か判別できない）'),
    (re.compile(r'スライド\s*\d{1,3}(?!\d)'), 'スライドN（手で確認）'),
]
R_SEP_ROW = re.compile(r'^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$')


def _map_numbers(s, m):
    return R_NUM.sub(lambda x: fmt_like(x.group(0), m(int(x.group(0)))), s)


def _sub_slide(m):
    def f(x):
        word, sp, first, rng, lst = x.groups()
        return word + sp + fmt_like(first, m(int(first))) + _map_numbers(rng, m) + _map_numbers(lst, m)
    return f


def _sub_page(m):
    def f(x):
        p, first, rng = x.groups()
        return p + fmt_like(first, m(int(first))) + _map_numbers(rng, m)
    return f


def _sub_bare(m):
    def f(x):
        first, dash, second = x.group(1), x.group(2), x.group(3)
        out = fmt_like(first, m(int(first)))
        if dash:
            out += dash
            if second:
                out += fmt_like(second, m(int(second)))
        return out
    return f


def _rewrite_cell(cell, m):
    s = cell
    if re.fullmatch(r'\s*~~\d{1,3}~~\s*', s) or re.fullmatch(r'\s*\d{1,3}\s*', s):
        return _map_numbers(s, m)
    if re.fullmatch(r'\s*\d{1,3}\s*[–〜\-]\s*(\d{1,3})?\s*', s):
        return _map_numbers(s, m)
    if re.fullmatch(r'\s*\d{1,3}(\s*[・,、]\s*\d{1,3})+\s*', s):
        return _map_numbers(s, m)
    return s


def rewrite_text(text, m, pages=False, kind='deck'):
    """Return (new_text, changes, review).

    changes: [(line_no, old_line, new_line)]; review: [(line_no, snippet, reason)].
    kind: 'deck' (storyboard/outline/review_state/glossary) or 'index' (source_index).
    """
    lines = text.split('\n')
    out, changes, review = [], [], []
    header_cols = None          # slide-ish column indexes of the table we are inside
    for i, ln in enumerate(lines):
        new = ln
        # tables: remember slide-ish columns from the header row
        if ln.lstrip().startswith('|'):
            if header_cols is None and i + 1 < len(lines) and R_SEP_ROW.match(lines[i + 1]):
                hdr = _cells(ln)
                header_cols = [k for k, h in enumerate(hdr) if SLIDE_COL.match(h)]
                header_cols = header_cols or []
                is_header = True
            else:
                is_header = False
            if header_cols and not is_header and not R_SEP_ROW.match(ln):
                parts = ln.split('|')
                # parts[0] is text before the first |, cells are parts[1:-1] when line ends with |
                for k in header_cols:
                    j = k + 1
                    if j < len(parts) - 1 or (j < len(parts) and not ln.rstrip().endswith('|')):
                        parts[j] = _rewrite_cell(parts[j], m)
                new = '|'.join(parts)
        else:
            header_cols = None
        # Slide tokens everywhere (headings, prose, CF origins, cells)
        new = R_SLIDE.sub(_sub_slide(m), new)
        new = R_PREVNEXT.sub(lambda x: x.group(1) + fmt_like(x.group(2), m(int(x.group(2)))), new)
        if kind == 'deck':
            if STRUCT_LINE.match(new):
                head, sep, rest = new.partition(':') if ':' in new.split('／')[0] else new.partition('：')
                new = head + sep + R_BARE.sub(_sub_bare(m), rest)
            elif BATCH_HEAD.match(new):
                new = R_RANGE_ONLY.sub(_sub_bare(m), new)
            if pages:
                new = R_PAGE.sub(_sub_page(m), new)
            elif R_PAGE.search(new):
                review.append((i + 1, R_PAGE.search(new).group(0), 'p.N（--pages で書き換え。PDF のページなら触らない）'))
        for rx, why in REVIEW_PATTERNS:
            mm = rx.search(new)
            if mm:
                review.append((i + 1, mm.group(0), why))
        if new != ln:
            changes.append((i + 1, ln, new))
        out.append(new)
    return '\n'.join(out), changes, review


def _cells(ln):
    s = ln.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


# --------------------------------------------------------------------------- planning

@dataclass
class Hit:
    path: str
    line: int
    slide: int
    old: str
    new: str


@dataclass
class FileChange:
    path: str
    eol: str
    old_text: str
    new_text: str
    changes: list
    review: list


@dataclass
class Plan:
    root: str
    mapping: object
    files: list = field(default_factory=list)
    approved_slides: set = field(default_factory=set)
    approved_hits: list = field(default_factory=list)
    approved_renumbered: list = field(default_factory=list)
    renames: list = field(default_factory=list)
    deck_hits: list = field(default_factory=list)


def _read(path):
    with io.open(path, encoding='utf-8', newline='') as f:
        raw = f.read()
    eol = '\r\n' if '\r\n' in raw else '\n'
    return raw.replace('\r\n', '\n'), eol


def approved_from_review_state(text):
    """Slide numbers whose Status is APPROVED in the ## Progress table."""
    lines = text.split('\n')
    approved = set()
    inside = False
    cols = None
    for i, ln in enumerate(lines):
        if ln.startswith('## '):
            inside = ln.strip() == '## Progress'
            cols = None
            continue
        if not inside or not ln.lstrip().startswith('|'):
            if inside and not ln.lstrip().startswith('|'):
                cols = None
            continue
        if cols is None:
            if i + 1 < len(lines) and R_SEP_ROW.match(lines[i + 1]):
                hdr = _cells(ln)
                try:
                    cols = (0, [k for k, h in enumerate(hdr) if h.strip().startswith('Status')][0])
                except IndexError:
                    cols = None
            continue
        if R_SEP_ROW.match(ln):
            continue
        cells = _cells(ln)
        if len(cells) <= cols[1]:
            continue
        key = re.sub(r'^~~(.*?)~~$', r'\1', cells[0].strip()).strip('`').strip()
        if 'APPROVED' in cells[cols[1]] and re.fullmatch(r'\d{1,3}', key):
            approved.add(int(key))
    return approved


def _slide_of_line(storyboard_lines):
    """For each line index, the ORIGINAL slide number of the enclosing ## Slide section."""
    cur = None
    out = []
    for ln in storyboard_lines:
        mm = re.match(r'^## Slide\s+(\d{1,3})\s*[:：]', ln)
        if mm:
            cur = int(mm.group(1))
        out.append(cur)
    return out


def plan(root, inserts, pages=False, explicit=None, rename_reviews=False, include_index=False,
         files=None, scan_deck=None):
    m = build_map(inserts, explicit)
    p = Plan(root=root, mapping=m)
    targets = list(files) if files else list(DECK_FILES)
    if include_index:
        targets.append(INDEX_FILE)
    rs_path = os.path.join(root, 'slides', 'review_state.md')
    if os.path.exists(rs_path):
        p.approved_slides = approved_from_review_state(_read(rs_path)[0])
    p.approved_renumbered = [(s, m(s)) for s in sorted(p.approved_slides) if m(s) != s]

    for rel in targets:
        path = os.path.join(root, rel.replace('/', os.sep))
        if not os.path.exists(path):
            continue
        text, eol = _read(path)
        kind = 'index' if rel == INDEX_FILE else 'deck'
        new, changes, review = rewrite_text(text, m, pages=pages, kind=kind)
        p.files.append(FileChange(path, eol, text, new, changes, review))
        if not changes:
            continue
        if rel.endswith('storyboard.md'):
            owner = _slide_of_line(text.split('\n'))
            for (ln, old, nw) in changes:
                s = owner[ln - 1]
                if s in p.approved_slides:
                    p.approved_hits.append(Hit(path, ln, s, old.strip(), nw.strip()))
        elif rel.endswith('review_state.md'):
            for (ln, old, nw) in changes:
                if old.lstrip().startswith('|'):
                    key = re.sub(r'^~~(.*?)~~$', r'\1', _cells(old)[0]).strip('`').strip()
                    if re.fullmatch(r'\d{1,3}', key) and int(key) in p.approved_slides:
                        p.approved_hits.append(Hit(path, ln, int(key), old.strip(), nw.strip()))

    if rename_reviews:
        rdir = os.path.join(root, 'slides', 'reviews')
        if os.path.isdir(rdir):
            for fn in os.listdir(rdir):
                mm = re.match(r'^slide-(\d{3})(\..+)$', fn)
                if mm and m(int(mm.group(1))) != int(mm.group(1)):
                    dst = 'slide-%03d%s' % (m(int(mm.group(1))), mm.group(2))
                    p.renames.append((os.path.join(rdir, fn), os.path.join(rdir, dst)))
    if scan_deck:
        p.deck_hits = scan_deck_text(scan_deck, m, pages)
    return p


def scan_deck_text(pptx_path, m, pages=False):
    """[(slide_no, shape_name, text_snippet, suggested)] — read-only, needs python-pptx."""
    try:
        from pptx import Presentation
    except ImportError:
        return [(0, '', 'python-pptx not installed; cannot scan the deck', '')]
    prs = Presentation(pptx_path)
    hits = []

    def texts(shape):
        if shape.shape_type == 6 and hasattr(shape, 'shapes'):   # group
            for s in shape.shapes:
                yield from texts(s)
            return
        if getattr(shape, 'has_text_frame', False) and shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                t = ''.join(r.text for r in para.runs)
                if t:
                    yield t
        if getattr(shape, 'has_table', False) and shape.has_table:
            for row in shape.table.rows:
                for cell in row.cells:
                    if cell.text:
                        yield cell.text

    for idx, slide in enumerate(prs.slides, 1):
        for shape in slide.shapes:
            for t in texts(shape):
                nt = R_SLIDE.sub(_sub_slide(m), t)
                if pages:
                    nt = R_PAGE.sub(_sub_page(m), nt)
                if nt != t:
                    hits.append((idx, shape.name, t[:80], nt[:80]))
    return hits


# --------------------------------------------------------------------------- output

def _rel(root, path):
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path


def report(p, out=None):
    out = out or sys.stdout
    w = out.write
    total = sum(len(f.changes) for f in p.files)
    w('renumber plan — %d change(s) in %d file(s)\n' % (total, sum(1 for f in p.files if f.changes)))
    for f in p.files:
        if not f.changes:
            continue
        w('\n== %s (%d, eol=%s)\n' % (_rel(p.root, f.path), len(f.changes), 'CRLF' if f.eol == '\r\n' else 'LF'))
        for ln, old, new in f.changes:
            w('  %5d: %s\n         → %s\n' % (ln, old.strip()[:110], new.strip()[:110]))
    rev = [(f.path, r) for f in p.files for r in f.review]
    if rev:
        w('\n-- not rewritten, check by hand (%d)\n' % len(rev))
        for path, (ln, snip, why) in rev:
            w('  %s:%d  %r  %s\n' % (_rel(p.root, path), ln, snip, why))
    w('\n-- APPROVED slides: %s\n' % (', '.join(str(s) for s in sorted(p.approved_slides)) or 'none'))
    if p.approved_renumbered:
        w('   whose own number changes (page-number-only re-approval needed): %s\n'
          % ', '.join('%d→%d' % x for x in p.approved_renumbered))
    if p.approved_hits:
        w('   references INSIDE approved slides that change (%d) — ask before applying:\n' % len(p.approved_hits))
        for h in p.approved_hits:
            w('     Slide %03d  %s:%d  %s\n' % (h.slide, _rel(p.root, h.path), h.line, h.new[:100]))
    if p.renames:
        w('\n-- review record renames (%d)\n' % len(p.renames))
        for s, d in p.renames:
            w('  %s → %s\n' % (os.path.basename(s), os.path.basename(d)))
    if p.deck_hits:
        w('\n-- deck text the BUILDER must change (%d; renumber.py never edits the pptx)\n' % len(p.deck_hits))
        for idx, name, t, nt in p.deck_hits:
            w('  slide %d  %s  %r → %r\n' % (idx, name, t, nt))


def apply(p):
    for f in p.files:
        if f.new_text != f.old_text:
            with io.open(f.path, 'w', encoding='utf-8', newline='') as fh:
                fh.write(f.new_text.replace('\n', f.eol))
    # two-phase rename so that 003→004 never clobbers an existing 004
    tmp = []
    for s, d in p.renames:
        t = s + '.renumber-tmp'
        os.rename(s, t)
        tmp.append((t, d))
    for t, d in tmp:
        if os.path.exists(d):
            raise RuntimeError('rename target exists: %s' % d)
        os.rename(t, d)


# --------------------------------------------------------------------------- CLI

def _parse_inserts(values):
    out = []
    for v in values or []:
        if ':' in v:
            a, c = v.split(':', 1)
            out.append((int(a), int(c)))
        else:
            out.append((int(v), 1))
    return out


def _parse_map(v):
    if not v:
        return None
    out = {}
    for pair in v.split(','):
        a, b = pair.split(':')
        out[int(a)] = int(b)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', default='.')
    ap.add_argument('--insert-after', action='append', metavar='N[:COUNT]',
                    help='insert COUNT (default 1) new slides after OLD slide N; repeatable')
    ap.add_argument('--map', help='explicit old:new pairs, comma separated (used instead of --insert-after)')
    ap.add_argument('--pages', action='store_true', help='also rewrite p.N deck page references (never in source_index)')
    ap.add_argument('--include-index', action='store_true', help='also rewrite Slide tokens in sources/source_index.md')
    ap.add_argument('--files', help='comma-separated project-relative files instead of the defaults')
    ap.add_argument('--rename-reviews', action='store_true', help='rename slides/reviews/slide-NNN.* accordingly')
    ap.add_argument('--scan-deck', metavar='PPTX', help='list deck text that references slide numbers (read-only)')
    ap.add_argument('--apply', action='store_true', help='write the changes (default: dry run)')
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    inserts = _parse_inserts(a.insert_after)
    explicit = _parse_map(a.map)
    if not inserts and not explicit:
        ap.error('give --insert-after N or --map old:new')
    files = a.files.split(',') if a.files else None
    p = plan(os.path.abspath(a.root), inserts, pages=a.pages, explicit=explicit,
             rename_reviews=a.rename_reviews, include_index=a.include_index, files=files,
             scan_deck=a.scan_deck)
    report(p)
    if a.apply:
        apply(p)
        print('\napplied.')
    else:
        print('\ndry run — nothing written. Re-run with --apply.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
