# -*- coding: utf-8 -*-
"""statekit — write techdeck-workflow state files without the hand-written-script failures.

Every write here guards against a failure that actually happened when state files were
edited with one-off scripts:

* an appended block landing in the NEXT section because the named sub-section did not
  exist in the intended one (`grep -c` still passed);
* a "table row added" that was written outside the table;
* CRLF files silently rewritten as LF;
* a headline inside a fenced code block mistaken for a real heading;
* an ID assigned twice because nobody grepped before numbering.

Rules: every operation resolves its target to EXACTLY one place or refuses (exit 2, nothing
written); the file's line endings are preserved; the line number where the write landed is
printed so the placement can be verified, not just the existence.

    python statekit.py next-id SRC [--root .]
    python statekit.py check-id SRC-024 [--root .]
    python statekit.py dupes sources/source_index.md
    python statekit.py ledger-set slides/review_state.md --batch b003 --slide 33 \
        --set "Exit verdict=\\`PASS\\`" --set "Review iter=2" --set "状態=\\`AWAITING_REVIEW\\`"
    python statekit.py progress-set slides/review_state.md --slide 33 --status AWAITING_REVIEW \
        --date 2026-10-13 --append-notes "iter2 PASS"
    python statekit.py storyboard-set slides/storyboard.md --slide 033 --section "Current spec" \
        --text "* キーメッセージ: …"          [--append] [--before "Known risks"]
    python statekit.py sources-row slides/storyboard.md --slide 033 --row "| \\`SRC-041\\` | 根拠 | #3 |"
    python statekit.py src-append sources/source_index.md --src SRC-041 --section "Update history" \
        --text "| 2026-10-13 | 逐語を追記 | C-2 |"
    python statekit.py review-append slides/reviews/slide-033.md --section "R6 notes" --text "* …"
    python statekit.py asc-add slides/review_state.md --slide 7 --source "b003 R6" \
        --content "限定語を追加" --impact "字数 +8" --when "Phase 4"

Text for --text may contain literal "\\n" to mean a newline, or be read from a file with @path.
"""
import argparse
import io
import os
import re
import sys
from dataclasses import dataclass


class StateError(Exception):
    """The target could not be resolved to exactly one place. Nothing was written."""


# --------------------------------------------------------------------------- documents

class Doc:
    """UTF-8 text with its original line endings remembered."""

    def __init__(self, path):
        self.path = path
        with io.open(path, encoding='utf-8', newline='') as f:
            raw = f.read()
        self.eol = '\r\n' if '\r\n' in raw else '\n'
        self.text = raw.replace('\r\n', '\n')

    def save(self, text):
        with io.open(self.path, 'w', encoding='utf-8', newline='') as f:
            f.write(text.replace('\n', self.eol))


def _apply(path, fn):
    """Load, transform with fn(text) -> (new_text, line), save with the same EOL."""
    d = Doc(path)
    new, line = fn(d.text)
    d.save(new)
    return line


# --------------------------------------------------------------------------- structure

@dataclass
class Section:
    start: int      # index of the heading line
    end: int        # exclusive: index of the next heading of level <= this, or bound
    level: int
    title: str


_FENCE = re.compile(r'^\s*(```|~~~)')
_HEAD = re.compile(r'^(#{1,6})\s+(.*?)\s*$')


def fence_mask(lines):
    """True for every line that is inside a fenced code block (fence lines included)."""
    mask, inside, marker = [], False, None
    for ln in lines:
        m = _FENCE.match(ln)
        if m and not inside:
            inside, marker = True, m.group(1)
            mask.append(True)
            continue
        if m and inside and ln.strip().startswith(marker):
            inside = False
            mask.append(True)
            continue
        mask.append(inside)
    return mask


def headings(lines):
    mask = fence_mask(lines)
    out = []
    for i, ln in enumerate(lines):
        if mask[i]:
            continue
        m = _HEAD.match(ln)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def find_section(lines, pattern, level, within=None, allow_missing=False, what='section'):
    """Exactly one heading of `level` whose title matches `pattern` (regex, search)."""
    lo = within.start + 1 if within else 0
    hi = within.end if within else len(lines)
    heads = headings(lines)
    cands = [h for h in heads if h[1] == level and lo <= h[0] < hi and re.search(pattern, h[2])]
    if not cands:
        if allow_missing:
            return None
        raise StateError('%s not found: level %d heading matching %r%s'
                         % (what, level, pattern, ' within %r' % within.title if within else ''))
    if len(cands) > 1:
        raise StateError('%s is ambiguous: %d level-%d headings match %r (lines %s)'
                         % (what, len(cands), level, pattern, ', '.join(str(c[0] + 1) for c in cands)))
    start, lvl, title = cands[0]
    end = hi
    for h in heads:
        if h[0] > start and h[1] <= lvl and h[0] < hi:
            end = h[0]
            break
    return Section(start, end, lvl, title)


def _split_block(block):
    if isinstance(block, str):
        return block.replace('\r\n', '\n').rstrip('\n').split('\n')
    return list(block)


def insert_at_section_end(lines, sec, block):
    """Insert block before the section's trailing blank lines / `---` separator.

    Returns the 0-based index of the block's first line. Exactly one blank line is kept
    between the previous content and the block, and between the block and what follows.
    """
    block = _split_block(block)
    e = sec.end
    i = e
    while i > sec.start + 1 and lines[i - 1].strip() == '':
        i -= 1
    sep = None
    if i > sec.start + 1 and lines[i - 1].strip() == '---':
        sep = i - 1
        i = sep
        while i > sec.start + 1 and lines[i - 1].strip() == '':
            i -= 1
    # i = just past the last content line of the section (heading counts as content)
    tail_start = sep if sep is not None else e
    del lines[i:tail_start]              # drop the blank run; we re-add exactly one
    new = [''] + block + ['']
    lines[i:i] = new
    return i + 1


def replace_section_body(lines, sec, block):
    """Replace everything after the heading line up to sec.end with block."""
    block = _split_block(block)
    new = [''] + block + ['']
    lines[sec.start + 1:sec.end] = new
    return sec.start + 2


# --------------------------------------------------------------------------- tables

_SEP_ROW = re.compile(r'^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$')


def _is_table_row(ln):
    return ln.lstrip().startswith('|')


def _cells(ln):
    s = ln.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def _row(cells):
    return '| ' + ' | '.join(cells) + ' |'


def find_table(lines, within, header_pattern, what='table'):
    """First table inside `within` whose header row matches header_pattern.

    Returns (header_idx, header_cells, first_row_idx, end_idx_exclusive).
    """
    for i in range(within.start + 1, within.end - 1):
        if _is_table_row(lines[i]) and _SEP_ROW.match(lines[i + 1] if i + 1 < len(lines) else ''):
            if re.search(header_pattern, lines[i]):
                j = i + 2
                while j < within.end and _is_table_row(lines[j]):
                    j += 1
                return i, _cells(lines[i]), i + 2, j
    raise StateError('%s not found: no table whose header matches %r within %r'
                     % (what, header_pattern, within.title))


def _norm_key(cell):
    c = cell.strip().strip('`').strip()
    c = re.sub(r'^~~(.*?)~~$', r'\1', c).strip()
    return c


def find_row(lines, first, end, key, what='row'):
    key = str(key)
    hits = [i for i in range(first, end) if _norm_key(_cells(lines[i])[0]) == key]
    if not hits:
        raise StateError('%s not found: no row whose first cell is %r' % (what, key))
    if len(hits) > 1:
        raise StateError('%s is ambiguous: %d rows have first cell %r' % (what, len(hits), key))
    return hits[0]


def _col_index(header, name):
    exact = [i for i, h in enumerate(header) if h == name]
    if len(exact) == 1:
        return exact[0]
    loose = [i for i, h in enumerate(header) if h.startswith(name)]
    if len(loose) == 1:
        return loose[0]
    raise StateError('column %r not found in header %r' % (name, header))


def set_cells(lines, row_idx, header, sets):
    cells = _cells(lines[row_idx])
    while len(cells) < len(header):
        cells.append('')
    for name, value in sets.items():
        cells[_col_index(header, name)] = value
    lines[row_idx] = _row(cells)


# --------------------------------------------------------------------------- ids

_SKIP_DIRS = {'.git', 'output', '__pycache__', 'node_modules', 'review-input', 'review-output'}


def _md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fn in filenames:
            if fn.lower().endswith('.md'):
                yield os.path.join(dirpath, fn)


def next_id(root, prefix, width=3):
    """`PREFIX-NNN` one past the largest number mentioned anywhere under root.

    References count, not only definitions: a DEC that already cites SRC-040 means
    SRC-040 is taken even if its index entry has not been written yet.
    """
    rx = re.compile(r'(?<![A-Za-z0-9])%s-(\d{%d,4})(?!\d)' % (re.escape(prefix), width))
    mx = 0
    for p in _md_files(root):
        try:
            with io.open(p, encoding='utf-8', errors='replace') as f:
                s = f.read()
        except OSError:
            continue
        for m in rx.finditer(s):
            mx = max(mx, int(m.group(1)))
    return '%s-%0*d' % (prefix, width, mx + 1)


def check_id(root, ident):
    """(definitions, references) of an ID. definitions = headings or table-first-cells."""
    rx_def = re.compile(r'^(?:#{1,6}\s+%s(?!\d)|\|\s*%s\s*\|)' % (re.escape(ident), re.escape(ident)), re.M)
    rx_any = re.compile(r'(?<![A-Za-z0-9])%s(?!\d)' % re.escape(ident))
    defs = refs = 0
    for p in _md_files(root):
        with io.open(p, encoding='utf-8', errors='replace') as f:
            s = f.read()
        d = len(rx_def.findall(s))
        defs += d
        refs += len(rx_any.findall(s)) - d
    return defs, refs


_URL_LINE = re.compile(r'^\s*(?:\*\s*URL[^:：]*[:：]|\|\s*URL[^|]*\|)\s*(\S+)', re.M)


_URL_LIKE = re.compile(r'^(?:[A-Za-z][A-Za-z0-9+.-]*://|www\.|/|\./|~/|[A-Za-z]:[\\/])')


def _norm_url(u):
    """Normalised URL/path key, or '' when the value is not a URL (「未確認」, '*', a note)."""
    u = u.strip().strip('`').rstrip('）),;、。')
    if not _URL_LIKE.match(u):
        return ''
    u = u.split('#', 1)[0]
    m = re.match(r'^([A-Za-z][A-Za-z0-9+.-]*://)([^/]+)(.*)$', u)
    if m:
        u = m.group(1).lower() + m.group(2).lower() + m.group(3)
    return u.rstrip('/')


def find_dupes(index_text):
    """[(normalised_url, [SRC ids...]), ...] for URLs registered under more than one ID."""
    lines = index_text.replace('\r\n', '\n').split('\n')
    by_url = {}
    for h in headings(lines):
        if h[1] != 2:
            continue
        m = re.match(r'(SRC-\d+)', h[2])
        if not m:
            continue
        sec = Section(h[0], len(lines), 2, h[2])
        for h2 in headings(lines):
            if h2[0] > h[0] and h2[1] <= 2:
                sec.end = h2[0]
                break
        body = '\n'.join(lines[sec.start:sec.end])
        for um in _URL_LINE.finditer(body):
            key = _norm_url(um.group(1))
            if key:
                by_url.setdefault(key, [])
                if m.group(1) not in by_url[key]:
                    by_url[key].append(m.group(1))
    return [(u, ids) for u, ids in by_url.items() if len(ids) > 1]


# --------------------------------------------------------------------------- operations
# Each returns (new_text, line_number_1_based) and raises StateError without side effects.

def _lines(text):
    return text.replace('\r\n', '\n').split('\n')


def _join(lines):
    return '\n'.join(lines)


def src_append(text, src, block, section=None):
    lines = _lines(text)
    sec = find_section(lines, r'^%s(?!\d)' % re.escape(src), 2, what='source %s' % src)
    if section:
        sub = find_section(lines, r'^%s$' % re.escape(section), 3, within=sec, allow_missing=True)
        if sub is None:
            idx = insert_at_section_end(lines, sec, ['### ' + section, ''] + _split_block(block))
            idx += 2
        else:
            idx = insert_at_section_end(lines, sub, block)
    else:
        idx = insert_at_section_end(lines, sec, block)
    _assert_inside(lines, idx, sec_pattern=r'^%s(?!\d)' % re.escape(src), level=2)
    return _join(lines), idx + 1


def _assert_inside(lines, idx, sec_pattern, level):
    """Placement check: the written line must sit inside the intended section."""
    sec = find_section(lines, sec_pattern, level)
    if not (sec.start < idx < sec.end):
        raise StateError('placement check failed: line %d is not inside %r (%d..%d)'
                         % (idx + 1, sec.title, sec.start + 1, sec.end))


def _slide_section(lines, slide):
    n = int(str(slide).strip())
    return find_section(lines, r'^Slide\s+0*%d\s*[:：]' % n, 2, what='Slide %s' % slide)


def storyboard_set(text, slide, section, body, append=False, before=None):
    lines = _lines(text)
    sec = _slide_section(lines, slide)
    sub = find_section(lines, r'^%s$' % re.escape(section), 3, within=sec, allow_missing=True)
    if sub is None:
        block = ['### ' + section, ''] + _split_block(body)
        anchor = None
        if before:
            anchor = find_section(lines, r'^%s$' % re.escape(before), 3, within=sec, allow_missing=True)
        if anchor is not None:
            lines[anchor.start:anchor.start] = block + ['']
            idx = anchor.start + 2
        else:
            idx = insert_at_section_end(lines, sec, block) + 2
    elif append:
        idx = insert_at_section_end(lines, sub, body)
    else:
        idx = replace_section_body(lines, sub, body)
    _assert_inside(lines, idx, r'^Slide\s+0*%d\s*[:：]' % int(slide), 2)
    return _join(lines), idx + 1


def sources_row(text, slide, row):
    lines = _lines(text)
    sec = _slide_section(lines, slide)
    sub = find_section(lines, r'^Sources$', 3, within=sec, what='### Sources of Slide %s' % slide)
    _, header, first, end = find_table(lines, sub, r'.', what='Sources table of Slide %s' % slide)
    row = row.strip()
    if not row.startswith('|'):
        raise StateError('row must be a markdown table row starting with |: %r' % row)
    if len(_cells(row)) != len(header):
        raise StateError('row has %d cells, table has %d columns %r' % (len(_cells(row)), len(header), header))
    lines[end:end] = [row]
    return _join(lines), end + 1


def ledger_set(text, batch, slide, sets):
    lines = _lines(text)
    sec = find_section(lines, r'^バッチ\s+%s(?!\d)' % re.escape(batch), 3, what='ledger of %s' % batch)
    _, header, first, end = find_table(lines, sec, r'^\|\s*Slide\s*\|', what='ledger table of %s' % batch)
    r = find_row(lines, first, end, slide, what='ledger row for slide %s' % slide)
    set_cells(lines, r, header, sets)
    return _join(lines), r + 1


def progress_set(text, slide, status=None, date=None, notes=None, append_notes=None):
    lines = _lines(text)
    sec = find_section(lines, r'^Progress$', 2, what='## Progress')
    _, header, first, end = find_table(lines, sec, r'^\|\s*Slide', what='Progress table')
    r = find_row(lines, first, end, slide, what='Progress row for slide %s' % slide)
    sets = {}
    if status is not None:
        s = status.strip()
        sets['Status'] = s if s.startswith('`') else '`%s`' % s
    if date is not None:
        sets['Last updated'] = date
    if notes is not None:
        sets['Notes'] = notes
    if append_notes:
        cur = _cells(lines[r])[_col_index(header, 'Notes')]
        if cur and not cur.endswith(('。', '.', '、')):
            cur += '。'
        sets['Notes'] = cur + append_notes
    if not sets:
        raise StateError('nothing to set')
    set_cells(lines, r, header, sets)
    return _join(lines), r + 1


def asc_add(text, slide, source, content, impact, when, status='OPEN'):
    lines = _lines(text)
    sec = find_section(lines, r'^Approved slide change requests$', 2, what='## Approved slide change requests')
    mx = 0
    for m in re.finditer(r'(?<![A-Za-z0-9])ASC-(\d{3,4})(?!\d)', _join(lines)):
        mx = max(mx, int(m.group(1)))
    ident = 'ASC-%03d' % (mx + 1)
    row = _row([ident, str(slide), source, content, impact, when, '`%s`' % status])
    try:
        _, header, first, end = find_table(lines, sec, r'^\|\s*ID\s*\|', what='ASC table')
        lines[end:end] = [row]
        idx = end
    except StateError:
        block = ['| ID | Slide | 出所 | 内容 | 影響 | 処理時期 | 状態 |',
                 '| --- | ---: | --- | --- | --- | --- | --- |', row]
        idx = insert_at_section_end(lines, sec, block) + 2
    return _join(lines), idx + 1


def review_append(text, section, block):
    lines = _lines(text)
    sec = find_section(lines, r'^%s$' % re.escape(section), 2, allow_missing=True)
    if sec is None:
        while lines and lines[-1].strip() == '':
            lines.pop()
        lines += ['', '## ' + section, ''] + _split_block(block)
        return _join(lines) + '\n', len(lines) - len(_split_block(block)) + 1
    idx = insert_at_section_end(lines, sec, block)
    return _join(lines), idx + 1


# file-level wrappers ------------------------------------------------------------------

def src_append_file(path, src, block, section=None):
    return _apply(path, lambda t: src_append(t, src, block, section))


def storyboard_set_file(path, slide, section, body, append=False, before=None):
    return _apply(path, lambda t: storyboard_set(t, slide, section, body, append, before))


def sources_row_file(path, slide, row):
    return _apply(path, lambda t: sources_row(t, slide, row))


def ledger_set_file(path, batch, slide, sets):
    return _apply(path, lambda t: ledger_set(t, batch, slide, sets))


def progress_set_file(path, slide, **kw):
    return _apply(path, lambda t: progress_set(t, slide, **kw))


def asc_add_file(path, **kw):
    return _apply(path, lambda t: asc_add(t, **kw))


def review_append_file(path, section, block):
    return _apply(path, lambda t: review_append(t, section, block))


# --------------------------------------------------------------------------- CLI

def _text_arg(v):
    if v is None:
        return None
    if v.startswith('@'):
        with io.open(v[1:], encoding='utf-8') as f:
            return f.read().replace('\r\n', '\n').rstrip('\n')
    return v.replace('\\n', '\n')


def _kv(items):
    out = {}
    for it in items or []:
        if '=' not in it:
            raise StateError('--set expects Column=value, got %r' % it)
        k, v = it.split('=', 1)
        out[k.strip()] = v
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('next-id', help='print PREFIX-NNN one past the largest number mentioned under --root')
    p.add_argument('prefix')
    p.add_argument('--root', default='.')

    p = sub.add_parser('check-id', help='count definitions and references of an ID; exit 1 if it exists')
    p.add_argument('ident')
    p.add_argument('--root', default='.')

    p = sub.add_parser('dupes', help='list URLs registered under more than one SRC id; exit 1 if any')
    p.add_argument('index')

    p = sub.add_parser('ledger-set', help='set cells of a batch ledger row in review_state.md')
    p.add_argument('path'); p.add_argument('--batch', required=True); p.add_argument('--slide', required=True)
    p.add_argument('--set', action='append', required=True, metavar='COL=VALUE')

    p = sub.add_parser('progress-set', help='set Status / Last updated / Notes of a Progress row')
    p.add_argument('path'); p.add_argument('--slide', required=True)
    p.add_argument('--status'); p.add_argument('--date'); p.add_argument('--notes'); p.add_argument('--append-notes')

    p = sub.add_parser('storyboard-set', help='replace / append / create a ### section of a slide entry')
    p.add_argument('path'); p.add_argument('--slide', required=True); p.add_argument('--section', required=True)
    p.add_argument('--text', required=True); p.add_argument('--append', action='store_true')
    p.add_argument('--before', help='when creating, insert before this existing ### section')

    p = sub.add_parser('sources-row', help='append a row to the ### Sources table of a slide entry')
    p.add_argument('path'); p.add_argument('--slide', required=True); p.add_argument('--row', required=True)

    p = sub.add_parser('src-append', help='append a block at the end of a ## SRC-NNN entry (or its ### sub-section)')
    p.add_argument('path'); p.add_argument('--src', required=True); p.add_argument('--text', required=True)
    p.add_argument('--section')

    p = sub.add_parser('review-append', help='append a block under a ## heading of a review record (created if missing)')
    p.add_argument('path'); p.add_argument('--section', required=True); p.add_argument('--text', required=True)

    p = sub.add_parser('asc-add', help='append an ASC-NNN row to ## Approved slide change requests')
    p.add_argument('path'); p.add_argument('--slide', required=True); p.add_argument('--source', required=True)
    p.add_argument('--content', required=True); p.add_argument('--impact', default='')
    p.add_argument('--when', default='Phase 4')

    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    try:
        if a.cmd == 'next-id':
            print(next_id(a.root, a.prefix))
            return 0
        if a.cmd == 'check-id':
            d, r = check_id(a.root, a.ident)
            print('%s: definitions=%d references=%d' % (a.ident, d, r))
            return 1 if (d or r) else 0
        if a.cmd == 'dupes':
            with io.open(a.index, encoding='utf-8') as f:
                groups = find_dupes(f.read())
            for url, ids in groups:
                print('%s  <-  %s' % (', '.join(ids), url))
            print('%d duplicate URL group(s)' % len(groups))
            return 1 if groups else 0
        if a.cmd == 'ledger-set':
            line = ledger_set_file(a.path, a.batch, a.slide, _kv(a.set))
        elif a.cmd == 'progress-set':
            line = progress_set_file(a.path, a.slide, status=a.status, date=a.date,
                                     notes=_text_arg(a.notes), append_notes=_text_arg(a.append_notes))
        elif a.cmd == 'storyboard-set':
            line = storyboard_set_file(a.path, a.slide, a.section, _text_arg(a.text), a.append, a.before)
        elif a.cmd == 'sources-row':
            line = sources_row_file(a.path, a.slide, a.row)
        elif a.cmd == 'src-append':
            line = src_append_file(a.path, a.src, _text_arg(a.text), a.section)
        elif a.cmd == 'review-append':
            line = review_append_file(a.path, a.section, _text_arg(a.text))
        elif a.cmd == 'asc-add':
            line = asc_add_file(a.path, slide=a.slide, source=a.source, content=a.content,
                                impact=a.impact, when=a.when)
        else:
            ap.error('unknown command')
        print('wrote %s:%d' % (a.path, line))
        return 0
    except StateError as e:
        print('statekit: refused — %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
