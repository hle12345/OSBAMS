"""Symbol library access (KiCad 7 stock libraries): flatten 'extends', list pins, build lib_symbols entries."""
import os, copy, functools
from . import kisx
from .kisx import Str

SYM_DIR = "/usr/share/kicad/symbols"
FP_DIR = "/usr/share/kicad/footprints"


@functools.lru_cache(maxsize=None)
def _lib(name):
    return kisx.parse(open(os.path.join(SYM_DIR, name + ".kicad_sym")).read())


def _raw(libname, sym):
    for e in _lib(libname)[1:]:
        if isinstance(e, list) and e and e[0] == 'symbol' and e[1] == sym:
            return e
    raise KeyError(f"{libname}:{sym}")


def flat_symbol(lib_id):
    """Return a flattened copy of the symbol, top-level renamed to lib_id (sub-symbols keep the bare name)."""
    libname, sym = lib_id.split(':', 1)
    node = copy.deepcopy(_raw(libname, sym))
    ext = kisx.find1(node, 'extends')
    if ext:
        base = copy.deepcopy(_raw(libname, ext[1]))
        base_name = str(ext[1])
        props = {str(p[1]): p for p in kisx.find(node, 'property')}
        out = [base[0], Str(sym)]
        for c in base[2:]:
            if isinstance(c, list) and c[0] == 'property':
                out.append(props.get(str(c[1]), c))
            elif isinstance(c, list) and c[0] == 'symbol':
                c[1] = Str(str(c[1]).replace(base_name, sym, 1))
                out.append(c)
            else:
                out.append(c)
        for k, p in props.items():
            if not any(isinstance(c, list) and c[0] == 'property' and str(c[1]) == k for c in out):
                out.append(p)
        node = out
    node[1] = Str(lib_id)
    return node


def pins(lib_id, unit=None):
    """List of dict(number,name,type,x,y,angle,length,unit,hidden) in symbol coordinates (y up)."""
    node = flat_symbol(lib_id)
    res = []
    for sub in kisx.find(node, 'symbol'):
        nm = str(sub[1])
        parts = nm.rsplit('_', 2)
        u = int(parts[-2]) if len(parts) == 3 and parts[-2].isdigit() else 0
        for p in kisx.find(sub, 'pin'):
            at = kisx.find1(p, 'at')
            res.append(dict(number=str(kisx.find1(p, 'number')[1]), name=str(kisx.find1(p, 'name')[1]), type=str(p[1]),
                            x=float(at[1]), y=float(at[2]), angle=int(float(at[3])), length=float(kisx.find1(p, 'length')[1]),
                            unit=u, hidden=('hide' in p) or any(isinstance(c, list) and c[0] == 'hide' for c in p)))
    if unit is not None:
        res = [p for p in res if p['unit'] in (0, unit)]
    return res


def custom_symbol(lib_id, ref_prefix, value, footprint, pinlist, datasheet="", width=None, desc=""):
    """Build a simple rectangular symbol. pinlist: [(number, name, type, side('L'/'R'), slot_index)]"""
    left = [p for p in pinlist if p[3] == 'L']; right = [p for p in pinlist if p[3] == 'R']
    n = max(len(left), len(right), 1)
    w = width or 17.78
    h = 2.54 * (n + 1)
    top = h / 2
    def pin_node(num, name, typ, side, idx):
        y = top - 2.54 * (idx + 1)
        if side == 'L':
            x, ang = -w / 2 - 5.08, 0
        else:
            x, ang = w / 2 + 5.08, 180
        return ['pin', typ, 'line', ['at', x, y, ang], ['length', 5.08], ['name', Str(name), ['effects', ['font', ['size', 1.27, 1.27]]]],
                ['number', Str(num), ['effects', ['font', ['size', 1.27, 1.27]]]]]
    fx = ['effects', ['font', ['size', 1.27, 1.27]]]
    def pr(k, v, y, hide=False):
        e = ['effects', ['font', ['size', 1.27, 1.27]]] + (['hide'] if hide else [])
        return ['property', Str(k), Str(v), ['at', 0, y, 0], e]
    body = ['symbol', Str(lib_id.split(':')[-1] + '_0_1'),
            ['rectangle', ['start', -w / 2, top], ['end', w / 2, -top], ['stroke', ['width', 0.254], ['type', 'default']], ['fill', ['type', 'background']]]]
    pins_n = ['symbol', Str(lib_id.split(':')[-1] + '_1_1')] + [pin_node(*p) for p in pinlist]
    return ['symbol', Str(lib_id), ['pin_names', ['offset', 1.016]], ['in_bom', 'yes'], ['on_board', 'yes'],
            pr('Reference', ref_prefix, top + 1.27), pr('Value', value, -top - 1.27), pr('Footprint', footprint, 0, True),
            pr('Datasheet', datasheet, 0, True), pr('ki_description', desc, 0, True), body, pins_n]


def fp_path(fp_id):
    lib, name = fp_id.split(':', 1)
    return os.path.join(FP_DIR, lib + ".pretty", name + ".kicad_mod")
