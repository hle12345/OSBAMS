"""Minimal KiCad s-expression reader/writer that preserves which atoms were quoted."""
import re


class Str(str):
    """A quoted string atom."""


_TOK = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()"]+')


def parse(text):
    stack = [[]]
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            l = stack.pop(); stack[-1].append(l)
        elif t[0] == '"':
            s = t[1:-1].replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
            stack[-1].append(Str(s))
        else:
            stack[-1].append(t)
    return stack[0][0]


def _atom(a):
    if isinstance(a, Str):
        return '"' + a.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(a, bool):
        return 'yes' if a else 'no'
    if isinstance(a, float):
        s = f"{a:.6f}".rstrip('0').rstrip('.')
        return s if s not in ('-0', '') else '0'
    return str(a)


def dump(node, indent=0, width=100):
    if not isinstance(node, list):
        return _atom(node)
    flat = _flat(node)
    if len(flat) + indent * 2 <= width:
        return flat
    head = []
    i = 0
    while i < len(node) and not isinstance(node[i], list):
        head.append(node[i]); i += 1
    s = '(' + ' '.join(_atom(c) for c in head)
    for k in node[i:]:
        s += '\n' + '  ' * (indent + 1) + (dump(k, indent + 1, width) if isinstance(k, list) else _atom(k))
    return s + '\n' + '  ' * indent + ')'


def _flat(node):
    return '(' + ' '.join(_flat(c) if isinstance(c, list) else _atom(c) for c in node) + ')'


def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def find1(node, name):
    r = find(node, name)
    return r[0] if r else None


def prop(node, name):
    for c in find(node, 'property'):
        if c[1] == name:
            return str(c[2])
    return None
