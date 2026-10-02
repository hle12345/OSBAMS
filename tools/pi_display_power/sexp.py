"""Netlist reader for kicad-cli 'export netlist --format kicadsexpr' (KiCad 7 single-line and KiCad 10 multi-line forms)."""
import re
def tokens(t):
    for m in re.finditer(r'\(|\)|"((?:[^"\\]|\\.)*)"|[^\s()"]+', t):
        yield m.group(0) if m.group(1) is None else ("S", m.group(1))
def parse(t):
    st = [[]]
    for tok in tokens(t):
        if tok == "(": st.append([])
        elif tok == ")": x = st.pop(); st[-1].append(x)
        else: st[-1].append(tok[1] if isinstance(tok, tuple) else tok)
    return st[0][0]
def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]
def read_netlist(text):
    """-> {net name (leading '/' kept): [(ref, pin, pintype), ...]}"""
    root = parse(text); nets = {}
    for ns in find(root, "nets"):
        for n in find(ns, "net"):
            nm = find(n, "name")[0][1]; nodes = []
            for nd in find(n, "node"):
                g = lambda k: (find(nd, k) or [[None, None]])[0][1]
                nodes.append((g("ref"), g("pin"), g("pintype")))
            nets[nm] = nodes
    return nets
