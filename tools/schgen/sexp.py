"""Minimal S-expression parser/serializer for KiCad files + symbol library helpers."""
import copy, math, re

class Sym(str):
    """Unquoted atom."""
    pass

def parse(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack = [[]]
    for t in tokens:
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        elif t.startswith('"'):
            stack[-1].append(t[1:-1].replace('\\"', '"').replace('\\\\', '\\'))
        else:
            stack[-1].append(Sym(t))
    return stack[0][0]

def dump(x, ind=0):
    if isinstance(x, list):
        if not x:
            return '()'
        simple = all(not isinstance(e, list) for e in x)
        if simple or len(x) <= 3 and all(not isinstance(e, list) or all(not isinstance(f, list) for f in e) for e in x):
            return '(' + ' '.join(dump(e) for e in x) + ')'
        head = []
        i = 0
        while i < len(x) and not isinstance(x[i], list):
            head.append(dump(x[i])); i += 1
        s = '(' + ' '.join(head)
        for e in x[i:]:
            s += '\n' + '  ' * (ind + 1) + dump(e, ind + 1)
        return s + '\n' + '  ' * ind + ')'
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return 'yes' if x else 'no'
    if isinstance(x, (int, float)):
        v = round(x, 4)
        return ('%d' % v) if v == int(v) else ('%g' % v)
    s = str(x).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return '"' + s + '"'

def find(x, key):
    return [e for e in x if isinstance(e, list) and e and e[0] == key]

def find1(x, key):
    r = find(x, key)
    return r[0] if r else None

_libcache = {}
def load_lib(name):
    if name not in _libcache:
        _libcache[name] = parse(open(f'/usr/share/kicad/symbols/{name}.kicad_sym').read())
    return _libcache[name]

def get_symbol(lib, name):
    """Return flattened symbol definition named 'lib:name'."""
    L = load_lib(lib)
    for s in find(L, 'symbol'):
        if s[1] == name:
            break
    else:
        raise KeyError(name)
    s = copy.deepcopy(s)
    ext = find1(s, 'extends')
    if ext:
        parent = get_symbol(lib, ext[1])  # already flattened
        pname = parent[1].split(':', 1)[1]
        # child's properties override parent's
        props = {p[1]: p for p in find(s, 'property')}
        new = [Sym('symbol'), f'{lib}:{name}']
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == 'property' and e[1] in props:
                new.append(props.pop(e[1]))
            elif isinstance(e, list) and e[0] == 'symbol':
                e = copy.deepcopy(e)
                e[1] = name + e[1][len(pname):]
                new.append(e)
            else:
                new.append(e)
        # insert remaining child props after the last property
        idx = max(i for i, e in enumerate(new) if isinstance(e, list) and e[0] == 'property') + 1
        for p in props.values():
            new.insert(idx, p); idx += 1
        return new
    s[1] = f'{lib}:{name}'
    return s

def symbol_pins(symdef, unit=1, convert=1):
    """List of dicts: number, name, x, y, angle (library coords, y up)."""
    pins = []
    base = symdef[1].split(':', 1)[-1]
    for sub in find(symdef, 'symbol'):
        m = re.match(r'.*_(\d+)_(\d+)$', sub[1])
        u, c = int(m.group(1)), int(m.group(2))
        if u not in (0, unit) or c not in (0, convert):
            continue
        for p in find(sub, 'pin'):
            at = find1(p, 'at')
            pins.append(dict(number=find1(p, 'number')[1], name=find1(p, 'name')[1],
                             x=float(at[1]), y=float(at[2]), angle=float(at[3]) if len(at) > 3 else 0.0,
                             etype=str(p[1])))
    return pins
