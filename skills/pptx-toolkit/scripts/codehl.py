# -*- coding: utf-8 -*-
"""Syntax highlighting for code fragments on a slide.

deck-profile.json has carried a `code_palette` since the beginning and
check_deck.py has always accepted those colours -- but nothing ever APPLIED
them, so every code fragment came out one flat colour and the reader had no way
to see structure. This module closes that gap.

    import sys
    sys.path.insert(0, r'<pptx-toolkit>/scripts')
    from codehl import highlight, code_block

    paras = highlight(src, 'python', prof['code_palette'], sz=10.5,
                      font=prof['fonts']['mono'], line_numbers=True,
                      mark_lines=[7, 8], focus=True)
    textbox(slide, 1.0, 2.0, 7.0, 3.0, paras, algn='l', anchor='t')

    # or, panel + code in one call:
    code_block(slide, 1.0, 2.0, 7.0, 3.0, src, 'python', prof, mark_lines=[7])

`mark_lines` is the point of R4-8 "注目箇所が明確である": marked lines keep full
strength and get a highlighter band; with `focus=True` every other line is
pushed back by OPACITY, keeping its syntax colours. A reader's eye lands on the
marked lines first, which is the whole reason the fragment is on the slide --
but the rest of the fragment is still highlighted code, not a grey wall.

No external dependency. pygments is not installed on this machine and adding it
would make every deck build depend on it.

Unknown language -> `text`, i.e. no colour at all. A WRONG highlight is worse
than none: it asserts a structure the code does not have.
"""

# --------------------------------------------------------------------------
# language definitions
# --------------------------------------------------------------------------

_PY_KW = set("""and as assert async await break class continue def del elif else
except finally for from global if import in is lambda nonlocal not or pass raise
return try while with yield match case""".split())
_PY_CTL = set('if elif else for while try except finally return yield break continue raise with match case'.split())
_PY_TYPE = set("""int float str bytes bool list dict set tuple frozenset object type
None True False self cls Exception ValueError TypeError KeyError IndexError
RuntimeError NotImplementedError StopIteration Optional List Dict Set Tuple Any
Callable Iterable Iterator Union""".split())

_JAVA_KW = set("""abstract assert boolean break byte case catch char class const
continue default do double else enum extends final finally float for goto if
implements import instanceof int interface long native new package private
protected public return short static strictfp super switch synchronized this
throw throws transient try void volatile while var record sealed permits
yield""".split())
_JAVA_CTL = set('if else for while do switch case default break continue return throw try catch finally yield'.split())
_JAVA_TYPE = set("""String Integer Long Double Float Boolean Character Byte Short
Object List Map Set Collection Optional Stream ArrayList HashMap HashSet
Exception RuntimeException Override Deprecated true false null""".split())

_KT_KW = set("""actual abstract annotation as break by catch class companion const
constructor continue crossinline data delegate do dynamic else enum expect
external false final finally for fun get if import in infix init inline inner
interface internal is lateinit noinline null object open operator out override
package private protected public reified return sealed set super suspend tailrec
this throw true try typealias typeof val var vararg when where while""".split())
_KT_CTL = set('if else for while do when try catch finally return break continue throw'.split())
_KT_TYPE = set("""Any Unit Nothing String Int Long Short Byte Double Float Boolean
Char Array List MutableList Map MutableMap Set MutableSet Pair Triple Sequence
Flow Job Deferred CoroutineScope Exception""".split())

_CS_KW = set("""abstract as async await base bool break byte case catch char
checked class const continue decimal default delegate do double else enum event
explicit extern false finally fixed float for foreach goto if implicit in int
interface internal is lock long namespace new null object operator out override
params private protected public readonly ref return sbyte sealed short sizeof
stackalloc static string struct switch this throw true try typeof uint ulong
unchecked unsafe ushort using var virtual void volatile while record init
with""".split())
_CS_CTL = set('if else for foreach while do switch case default break continue return throw try catch finally yield'.split())
_CS_TYPE = set("""String Int32 Int64 Boolean Double Decimal Object List
Dictionary IEnumerable IList IDictionary Task Exception Nullable Span""".split())

_TS_KW = set("""abstract any as async await break case catch class const constructor
continue declare default delete do else enum export extends false finally for
from function get if implements import in instanceof interface keyof let new
null of package private protected public readonly return satisfies set static
super switch this throw true try type typeof var void while yield""".split())
_TS_CTL = set('if else for while do switch case default break continue return throw try catch finally yield await'.split())
_TS_TYPE = set("""string number boolean object symbol bigint unknown never
undefined Array Promise Record Partial Readonly Pick Omit Map Set Date RegExp
Error JSON Math console""".split())

_SQL_KW = set("""select from where group by having order limit offset insert into
values update set delete create table alter drop index view join inner left
right full outer on as distinct union all exists in between like is null not and
or case when then else end primary key foreign references constraint default
begin commit rollback transaction with returning""".split())
_SQL_CTL = set('select insert update delete create alter drop begin commit rollback'.split())
_SQL_TYPE = set("""int integer bigint smallint decimal numeric float real double
precision char varchar text date time timestamp boolean blob json jsonb uuid
serial""".split())

_SH_KW = set("""if then else elif fi for while until do done case esac function
return break continue in select time coproc local export readonly declare
unset""".split())
_SH_CTL = set('if then else elif fi for while until do done case esac return break continue'.split())
_SH_TYPE = set('echo cd ls cp mv rm mkdir cat grep sed awk find export source printf test'.split())

_C_STRINGS = [('"', '"'), ("'", "'")]

LANGS = {
    'python': dict(line=['#'], block=[], strings=[('"""', '"""'), ("'''", "'''"),
                                                  ('"', '"'), ("'", "'")],
                   kw=_PY_KW, ctl=_PY_CTL, ty=_PY_TYPE, decorator=True),
    'java': dict(line=['//'], block=[('/*', '*/')], strings=_C_STRINGS,
                 kw=_JAVA_KW, ctl=_JAVA_CTL, ty=_JAVA_TYPE, decorator=True),
    'kotlin': dict(line=['//'], block=[('/*', '*/')],
                   strings=[('"""', '"""')] + _C_STRINGS,
                   kw=_KT_KW, ctl=_KT_CTL, ty=_KT_TYPE, decorator=True),
    'csharp': dict(line=['//'], block=[('/*', '*/')], strings=_C_STRINGS,
                   kw=_CS_KW, ctl=_CS_CTL, ty=_CS_TYPE),
    'typescript': dict(line=['//'], block=[('/*', '*/')],
                       strings=_C_STRINGS + [('`', '`')],
                       kw=_TS_KW, ctl=_TS_CTL, ty=_TS_TYPE, decorator=True),
    'sql': dict(line=['--'], block=[('/*', '*/')], strings=[("'", "'")],
                kw=_SQL_KW, ctl=_SQL_CTL, ty=_SQL_TYPE, fold=True),
    'json': dict(line=[], block=[], strings=[('"', '"')],
                 kw={'true', 'false', 'null'}, ctl=set(), ty=set(), json=True),
    'bash': dict(line=['#'], block=[], strings=_C_STRINGS,
                 kw=_SH_KW, ctl=_SH_CTL, ty=_SH_TYPE, dollar=True),
    'text': dict(line=[], block=[], strings=[], kw=set(), ctl=set(), ty=set()),
}
LANGS['js'] = LANGS['javascript'] = LANGS['typescript']
LANGS['ts'] = LANGS['tsx'] = LANGS['jsx'] = LANGS['typescript']
LANGS['py'] = LANGS['python']
LANGS['kt'] = LANGS['kotlin']
LANGS['cs'] = LANGS['c#'] = LANGS['csharp']
LANGS['sh'] = LANGS['shell'] = LANGS['console'] = LANGS['bash']
LANGS['c'] = LANGS['cpp'] = LANGS['c++'] = LANGS['go'] = LANGS['java']
LANGS['plain'] = LANGS['none'] = LANGS['text']

_NAME_START = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$')
_NAME_CHAR = _NAME_START | set('0123456789')
_DIGITS = set('0123456789')


# --------------------------------------------------------------------------
# tokenizers -- each yields (kind, text); '\n' is its own token
# --------------------------------------------------------------------------

def _tok_generic(code, spec):
    n, i = len(code), 0
    line_c = spec.get('line') or []
    block_c = spec.get('block') or []
    strings = sorted(spec.get('strings') or [], key=lambda p: -len(p[0]))
    kw, ctl, ty = spec['kw'], spec['ctl'], spec['ty']
    fold = spec.get('fold', False)
    while i < n:
        ch = code[i]
        if ch == '\n':
            yield ('nl', '\n')
            i += 1
            continue
        if ch in ' \t':
            j = i
            while j < n and code[j] in ' \t':
                j += 1
            yield ('default', code[i:j])
            i = j
            continue
        # block comment
        hit = next((p for p in block_c if code.startswith(p[0], i)), None)
        if hit:
            end = code.find(hit[1], i + len(hit[0]))
            end = n if end == -1 else end + len(hit[1])
            for k, part in enumerate(code[i:end].split('\n')):
                if k:
                    yield ('nl', '\n')
                if part:
                    yield ('comment', part)
            i = end
            continue
        # line comment
        if any(code.startswith(c, i) for c in line_c):
            end = code.find('\n', i)
            end = n if end == -1 else end
            yield ('comment', code[i:end])
            i = end
            continue
        # decorator / annotation
        if spec.get('decorator') and ch == '@' and i + 1 < n and code[i + 1] in _NAME_START:
            j = i + 1
            while j < n and (code[j] in _NAME_CHAR or code[j] == '.'):
                j += 1
            yield ('function', code[i:j])
            i = j
            continue
        # shell variable
        if spec.get('dollar') and ch == '$':
            j = i + 1
            if j < n and code[j] == '{':
                j = code.find('}', j)
                j = n if j == -1 else j + 1
            else:
                while j < n and code[j] in _NAME_CHAR:
                    j += 1
            yield ('variable', code[i:j])
            i = j
            continue
        # string
        sd = next((p for p in strings if code.startswith(p[0], i)), None)
        if sd:
            op, cl = sd
            j = i + len(op)
            while j < n:
                if code[j] == '\\' and len(op) == 1:
                    j += 2
                    continue
                if code.startswith(cl, j):
                    j += len(cl)
                    break
                if code[j] == '\n' and len(op) == 1:
                    break                       # unterminated: stop at EOL
                j += 1
            for k, part in enumerate(code[i:j].split('\n')):
                if k:
                    yield ('nl', '\n')
                if part:
                    yield ('string', part)
            i = j
            continue
        # number
        if ch in _DIGITS or (ch == '.' and i + 1 < n and code[i + 1] in _DIGITS):
            j = i
            while j < n and (code[j] in _DIGITS or code[j] in '.xXbBoOeE_aAcCdDfFlLuU'
                             or (code[j] in '+-' and code[j - 1] in 'eE')):
                j += 1
            yield ('number', code[i:j])
            i = j
            continue
        # name
        if ch in _NAME_START:
            j = i
            while j < n and code[j] in _NAME_CHAR:
                j += 1
            word = code[i:j]
            probe = word.lower() if fold else word
            k = j
            while k < n and code[k] in ' \t':
                k += 1
            if probe in ctl:
                kind = 'control'
            elif probe in ty:
                kind = 'type'
            elif probe in kw:
                kind = 'keyword'
            elif k < n and code[k] == '(':
                kind = 'function'
            elif word[0].isupper():
                kind = 'type'
            else:
                kind = 'default'
            yield (kind, word)
            i = j
            continue
        yield ('default', ch)
        i += 1


def _tok_json(code, spec):
    """Same as generic, but a string in key position is a key, not a value."""
    pending = []
    for kind, text in _tok_generic(code, spec):
        if kind == 'string':
            pending.append((kind, text))
            continue
        if pending:
            is_key = text.lstrip().startswith(':')
            for k, t in pending:
                yield ('variable' if is_key else k, t)
            pending = []
        yield (kind, text)
    for k, t in pending:
        yield (k, t)


def _tok_yaml(code, spec):
    for li, line in enumerate(code.split('\n')):
        if li:
            yield ('nl', '\n')
        stripped = line.lstrip()
        if stripped.startswith('#'):
            yield ('comment', line)
            continue
        indent = line[:len(line) - len(stripped)]
        if indent:
            yield ('default', indent)
        if stripped.startswith('- '):
            yield ('control', '- ')
            stripped = stripped[2:]
        if ':' in stripped:
            key, _, rest = stripped.partition(':')
            if '#' in key or ' ' in key.strip() and not key.strip():
                yield ('default', stripped)
                continue
            yield ('variable', key)
            yield ('default', ':')
            cmt = rest.find(' #')
            if cmt != -1:
                val, com = rest[:cmt], rest[cmt:]
            else:
                val, com = rest, ''
            if val.strip():
                v = val.strip()
                kind = ('number' if v.replace('.', '', 1).lstrip('-').isdigit()
                        else 'keyword' if v in ('true', 'false', 'null', '~')
                        else 'string')
                yield (kind, val)
            elif val:
                yield ('default', val)
            if com:
                yield ('comment', com)
        else:
            yield ('string' if stripped else 'default', stripped or line)


def _tok_xml(code, spec):
    n, i = len(code), 0
    while i < n:
        ch = code[i]
        if ch == '\n':
            yield ('nl', '\n')
            i += 1
        elif code.startswith('<!--', i):
            end = code.find('-->', i)
            end = n if end == -1 else end + 3
            for k, part in enumerate(code[i:end].split('\n')):
                if k:
                    yield ('nl', '\n')
                if part:
                    yield ('comment', part)
            i = end
        elif ch == '<':
            j = i + 1
            while j < n and code[j] not in ' \t\n>/':
                j += 1
            yield ('keyword', code[i:j])
            i = j
        elif ch in '>/' and i and code[i - 1] not in '=' :
            yield ('keyword', ch)
            i += 1
        elif ch == '"' or ch == "'":
            j = code.find(ch, i + 1)
            j = n if j == -1 else j + 1
            yield ('string', code[i:j])
            i = j
        elif ch in _NAME_START:
            j = i
            while j < n and (code[j] in _NAME_CHAR or code[j] in '-:'):
                j += 1
            k = j
            while k < n and code[k] in ' \t':
                k += 1
            yield ('variable' if k < n and code[k] == '=' else 'default', code[i:j])
            i = j
        else:
            yield ('default', ch)
            i += 1


def _tok_diff(code, spec):
    for li, line in enumerate(code.split('\n')):
        if li:
            yield ('nl', '\n')
        if line.startswith('@@'):
            yield ('type', line)
        elif line.startswith('+++') or line.startswith('---'):
            yield ('keyword', line)
        elif line.startswith('+'):
            yield ('number', line)
        elif line.startswith('-'):
            yield ('highlight', line)
        else:
            yield ('default', line)


_SPECIAL = {'json': _tok_json, 'yaml': _tok_yaml, 'yml': _tok_yaml,
            'xml': _tok_xml, 'html': _tok_xml, 'svg': _tok_xml,
            'diff': _tok_diff, 'patch': _tok_diff}


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------

def tokenize(code, lang):
    """[(kind, text)] with '\\n' as its own token. kind is a code_palette key."""
    lang = (lang or 'text').lower().lstrip('.')
    spec = LANGS.get(lang, LANGS['text'])
    fn = _SPECIAL.get(lang, _tok_generic)
    return list(fn(code, spec))


def highlight(code, lang, palette, sz=9.0, font='Courier New',
              line_numbers=False, start_line=1, mark_lines=(),
              mark_hl=None, focus=False, dim_color=None, gutter_color=None,
              tab=4, dim_alpha=0.55):
    """Tokenize `code` and return paragraphs (a list of list-of-R) ready for
    textbox()/set_runs().

    palette      a deck-profile `code_palette` dict
    mark_lines   1-based line numbers to draw attention to
    mark_hl      highlighter colour painted behind marked lines
    focus        push every UNmarked line BACK so the marked lines pop
    dim_alpha    how far back focus pushes them: opacity 0.0-1.0

    focus dims by OPACITY, not by recolouring. Repainting the unmarked lines a
    single flat grey -- what this used to do -- deletes the syntax highlight
    from nearly the whole fragment: on a typical slide two lines are marked and
    twenty are not, so the reader sees a grey wall with two coloured lines in
    it, and R4-7 (syntax highlighting applied) loses to R4-8 (marked lines
    visible). Alpha keeps every token its own colour AND still ranks the lines.
    It also keeps the colour VALUE in the file a profile colour, so
    check_deck.py's palette check stays quiet.

    0.55 is where the weakest token in both shipped presets still clears
    check_deck's 2.0:1 floor (dark comment 2.45:1, light type 2.07:1) while
    `default` lands around 4.5:1 -- dimmed lines stay readable when the reader
    chooses to read them, which is the difference between context and noise.

    Pass `dim_color` to get the old flat-recolour behaviour back.
    """
    from deckkit import R
    pal = dict(palette or {})
    pal.setdefault('default', '000000')
    marks = set(mark_lines or ())
    code = code.replace('\t', ' ' * tab).rstrip('\n')

    lines, cur = [], []
    for kind, text in tokenize(code, lang):
        if kind == 'nl':
            lines.append(cur)
            cur = []
        else:
            cur.append((kind, text))
    lines.append(cur)

    if focus and marks and not marks & set(range(start_line,
                                                 start_line + len(lines))):
        # Every line would be dimmed and none marked -- a flat wall with
        # nothing to look at. Usually a stale mark_lines left behind after the
        # snippet was re-cut. Fail loud rather than ship the wall.
        import warnings
        warnings.warn('codehl: mark_lines %s fall outside lines %d-%d of this '
                      'fragment; ignoring focus'
                      % (sorted(marks), start_line, start_line + len(lines) - 1),
                      stacklevel=2)
        focus = False

    width = len(str(start_line + len(lines) - 1))
    paras = []
    for idx, toks in enumerate(lines):
        no = start_line + idx
        marked = no in marks
        runs = []
        if line_numbers:
            runs.append(R('%*d  ' % (width, no), sz,
                          gutter_color or pal['default'], font,
                          a=None if gutter_color else dim_alpha))
        merged = []
        for kind, text in toks:
            if merged and merged[-1][0] == kind:
                merged[-1][1] += text
            else:
                merged.append([kind, text])
        for kind, text in merged:
            color, alpha = pal.get(kind, pal['default']), None
            if focus and marks and not marked:
                if dim_color:
                    color = dim_color            # explicit opt-in to flat dim
                else:
                    alpha = dim_alpha
            runs.append(R(text, sz, color, font, b=marked and not focus,
                          hl=mark_hl if marked else None, a=alpha))
        if not runs:
            runs = [R(' ', sz, pal['default'], font)]
        paras.append(runs)
    return paras


def code_block(slide, x, y, w, h, code, lang, profile, sz=None, panel=None,
               line_numbers=False, start_line=1, mark_lines=(), mark_hl=None,
               focus=False, pad=0.16, radius=6000, dim_color=None,
               dim_alpha=0.55):
    """Panel + highlighted code in one call. Returns (panel_el, text_el).

    `profile` is a loaded deck-profile.json dict (needs fonts.mono and
    code_palette; palette.deep / palette.card is used for the panel).
    """
    from deckkit import rrect, textbox
    pal = profile.get('palette') or {}
    cpal = profile.get('code_palette') or {}
    font = (profile.get('fonts') or {}).get('mono', 'Courier New')
    sz = sz or 10.0
    panel = panel or pal.get('deep') or pal.get('card') or pal.get('bg_alt')
    bg_el = rrect(slide, x, y, w, h, fill=panel,
                  line=pal.get('rule'), lw=9525, adj=radius)
    # The gutter is chrome, not code: it takes a NEUTRAL colour from the deck
    # palette. The code itself keeps its code_palette colours even under focus
    # -- dimming is opacity (see highlight). Passing dim_color here restores
    # the old flat recolour.
    gutter = pal.get('dim') or pal.get('muted')
    paras = highlight(code, lang, cpal, sz=sz, font=font,
                      line_numbers=line_numbers, start_line=start_line,
                      mark_lines=mark_lines, mark_hl=mark_hl, focus=focus,
                      dim_color=dim_color, gutter_color=gutter,
                      dim_alpha=dim_alpha)
    tx_el = textbox(slide, x + pad, y + pad, w - 2 * pad, h - 2 * pad, paras,
                    algn='l', anchor='t', spc_pct=125)
    return bg_el, tx_el
