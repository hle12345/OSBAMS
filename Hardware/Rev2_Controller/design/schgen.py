"""KiCad 7 schematic generator (hierarchical, label-based) driven by rev2_design.py."""
import os, uuid, math, copy
from collections import OrderedDict, defaultdict
from . import kisx, kilib
from .kisx import Str

CW = 1.15           # estimated mm per character of label text
STUB = 5.08
GAP = 10.16


def U():
    return str(uuid.uuid4())


def fx(size=1.27, hide=False, justify=None, bold=False):
    e = ['effects', ['font', ['size', size, size]] + (['bold'] if bold else [])]
    if justify:
        e.append(['justify'] + justify.split())
    if hide:
        e.append('hide')
    return e


class SymInfo:
    def __init__(self, lib_id, custom=None):
        self.lib_id = lib_id
        if custom is not None:
            self.node = custom
            self.pins = []
            for sub in kisx.find(custom, 'symbol'):
                for p in kisx.find(sub, 'pin'):
                    at = kisx.find1(p, 'at')
                    self.pins.append(dict(number=str(kisx.find1(p, 'number')[1]), name=str(kisx.find1(p, 'name')[1]), type=str(p[1]), x=float(at[1]), y=float(at[2]),
                                          angle=int(float(at[3])), length=5.08, unit=1, hidden=False))
        else:
            self.node = kilib.flat_symbol(lib_id)
            self.pins = kilib.pins(lib_id)


def outward(angle):
    """schematic-space unit vector pointing away from the symbol body for a pin of library angle."""
    a = math.radians((angle + 180) % 360)
    return (round(math.cos(a)), -round(math.sin(a)))


def snap(v, g=1.27):
    return round(round(v / g) * g, 4)


class Sheet:
    def __init__(self, name, title):
        self.name, self.title = name, title
        self.items = []        # raw s-expr nodes
        self.uuid = U()
        self.file = name + ".kicad_sch"
        self.paper = "A3"
        self.notes = []
        self.symbols = []      # symbol instance nodes (for page assembly)


class SchGen:
    def __init__(self, design, outdir, project):
        self.d = design
        self.out = outdir
        self.project = project
        self.root_uuid = U()
        self.syminfo = {}
        self.pwr_n = 0
        self.errors = []
        net_sheets = defaultdict(set)
        for ref, c in design.COMPS.items():
            for n in c['nets'].values():
                net_sheets[n].add(c['sheet'])
        for n in design.PWR_FLAGS:
            net_sheets[n].add("__flag__")
        self.global_nets = {n for n, s in net_sheets.items() if len(s) > 1 and n not in design.POWER_SYMS}

    # ------------------------------------------------------------------ symbols
    def sym(self, lib_id):
        if lib_id not in self.syminfo:
            if lib_id.startswith("OSBAMS_Rev2:"):
                name = lib_id.split(':')[1]
                c = self.d.CUSTOM[name]
                node = kilib.custom_symbol(lib_id, c['ref'], c['value'], c['fp'], c['pins'], desc=c['desc'])
                self.syminfo[lib_id] = SymInfo(lib_id, node)
            else:
                self.syminfo[lib_id] = SymInfo(lib_id)
        return self.syminfo[lib_id]

    def resolve(self, comp):
        """-> list of (pin dict, net or None)"""
        si = self.sym(comp['lib'])
        m = {str(k): v for k, v in comp['nets'].items()}
        res = []
        used = set()
        for p in si.pins:
            net = None
            if p['number'] in m:
                net = m[p['number']]; used.add(p['number'])
            elif p['name'] in m and p['name'] != '~':
                net = m[p['name']]; used.add(p['name'])
            res.append((p, net))
        for k in m:
            if k not in used:
                self.errors.append(f"{comp['ref']}: pin key '{k}' not found on {comp['lib']}")
        return res

    # ------------------------------------------------------------------ geometry
    def extents(self, comp):
        """bounding box (l, r, u, d) in schematic mm relative to the symbol origin including stubs and labels."""
        pins = self.resolve(comp)
        l = r = u = d = 0.0
        seen = set()
        for p, net in pins:
            px, py = p['x'], -p['y']
            ox, oy = outward(p['angle'])
            if (px, py) in seen:
                continue
            seen.add((px, py))
            lab = len(net or "") * CW + 2 if net else 0
            ex, ey = px + ox * STUB, py + oy * STUB
            for x, y in ((px, py), (ex, ey), (ex + ox * lab if oy == 0 else ex, ey + oy * lab if ox == 0 else ey)):
                l, r, u, d = min(l, x), max(r, x), min(u, y), max(d, y)
        return l, r, u, d

    # ------------------------------------------------------------------ writing one symbol instance
    def place(self, sheet, comp, X, Y):
        si = self.sym(comp['lib'])
        ref = comp['ref']
        props = [
            ['property', Str('Reference'), Str(ref), ['at', X + 2.54, Y - 3.81, 0], fx(justify='left')],
            ['property', Str('Value'), Str(str(comp['value'])), ['at', X + 2.54, Y - 1.27, 0], fx(justify='left')],
            ['property', Str('Footprint'), Str(comp['fp']), ['at', X, Y, 0], fx(hide=True)],
            ['property', Str('Datasheet'), Str(""), ['at', X, Y, 0], fx(hide=True)],
        ]
        extra = [("Manufacturer", comp.get('mfr', '')), ("MPN", comp.get('mpn', '')), ("Evidence", comp.get('evid', '')), ("Lifecycle", comp.get('life', '')),
                 ("Source", comp.get('src', '')), ("Alternate", comp.get('alt', '')), ("Description", comp.get('desc', '')), ("Note", comp.get('note', ''))]
        for k, v in extra:
            props.append(['property', Str(k), Str(str(v)), ['at', X, Y, 0], fx(hide=True)])
        pin_nodes = []
        seen_num = set()
        for p, net in self.resolve(comp):
            if p['number'] not in seen_num:
                pin_nodes.append(['pin', Str(p['number']), ['uuid', Str(U())]]); seen_num.add(p['number'])
        node = ['symbol', ['lib_id', Str(comp['lib'])], ['at', X, Y, 0], ['unit', 1], ['in_bom', 'yes' if comp['key'] not in ('TP', 'MH', 'FID') else 'no'],
                ['on_board', 'yes'], ['dnp', 'yes' if comp.get('dnp') else 'no'], ['fields_autoplaced'], ['uuid', Str(U())]] + props + pin_nodes + [
            ['instances', ['project', Str(self.project), ['path', Str(f"/{self.root_uuid}/{sheet.uuid}"), ['reference', Str(ref)], ['unit', 1]]]]]
        sheet.items.append(node)
        # stubs, labels, no-connects
        done = {}
        # stagger stub lengths of vertical pins that are packed together (e.g. MCU supply pins)
        vert = sorted({(round(p['x'], 2), round(p['y'], 2)) for p, n in self.resolve(comp) if outward(p['angle'])[0] == 0})
        stag = {}
        if len(vert) > 3:
            for i, key in enumerate(vert):
                stag[key] = STUB + 2.54 * (i % 3)
        for p, net in self.resolve(comp):
            px, py = X + p['x'], Y - p['y']
            key = (round(px, 3), round(py, 3))
            if key in done:
                if done[key] != net:
                    self.errors.append(f"{ref}: stacked pins at {key} have different nets {done[key]} vs {net}")
                continue
            done[key] = net
            if net is None:
                if p['type'] != 'power_out' or True:
                    sheet.items.append(['no_connect', ['at', px, py], ['uuid', Str(U())]])
                continue
            self.stub(sheet, px, py, outward(p['angle']), net, stag.get((round(p['x'], 2), round(p['y'], 2))))

    def stub(self, sheet, px, py, vec, net, length=None):
        ox, oy = vec
        L = length or STUB
        ex, ey = px + ox * L, py + oy * L
        sheet.items.append(['wire', ['pts', ['xy', px, py], ['xy', ex, ey]], ['stroke', ['width', 0], ['type', 'default']], ['uuid', Str(U())]])
        if net in self.d.POWER_SYMS:
            self.power(sheet, net, ex, ey, vec)
        else:
            ang = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[(ox, oy)]
            just = 'left bottom' if ang in (0, 90) else 'right bottom'
            if net in self.global_nets:
                sheet.items.append(['global_label', Str(net), ['shape', 'bidirectional'], ['at', ex, ey, ang], fx(justify=just), ['uuid', Str(U())],
                                    ['property', Str('Intersheetrefs'), Str('${INTERSHEET_REFS}'), ['at', ex, ey, 0], fx(hide=True)]])
            else:
                sheet.items.append(['label', Str(net), ['at', ex, ey, ang], fx(justify=just), ['uuid', Str(U())]])

    def power(self, sheet, net, x, y, vec):
        lib = self.d.POWER_SYMS[net]
        self.pwr_n += 1
        base = 270 if net == 'GND' else 90          # direction of the symbol body (CCW degrees)
        want = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[vec]
        rot = (want - base) % 360
        self._power_node(sheet, lib, net, x, y, rot)

    def _power_node(self, sheet, lib, value, x, y, rot, flag=False):
        self.sym(lib)
        ref = f"#FLG{self.pwr_n:03d}" if flag else f"#PWR{self.pwr_n:03d}"
        node = ['symbol', ['lib_id', Str(lib)], ['at', x, y, rot], ['unit', 1], ['in_bom', 'no'], ['on_board', 'no'], ['dnp', 'no'], ['fields_autoplaced'], ['uuid', Str(U())],
                ['property', Str('Reference'), Str(ref), ['at', x, y, 0], fx(hide=True)],
                ['property', Str('Value'), Str(value), ['at', x + 2, y - 2, 0], fx(justify='left')],
                ['property', Str('Footprint'), Str(""), ['at', x, y, 0], fx(hide=True)],
                ['property', Str('Datasheet'), Str(""), ['at', x, y, 0], fx(hide=True)],
                ['pin', Str('1'), ['uuid', Str(U())]],
                ['instances', ['project', Str(self.project), ['path', Str(f"/{self.root_uuid}/{sheet.uuid}"), ['reference', Str(ref)], ['unit', 1]]]]]
        sheet.items.append(node)

    # ------------------------------------------------------------------ sheet layout
    def build_sheet(self, sheet, notes):
        comps = [c for c in self.d.COMPS.values() if c['sheet'] == sheet.name]
        maxw = 380.0
        x0, y0 = 25.4, 40.64
        cx, cy, rowh = x0, y0, 0.0
        placed = []
        # big ICs first on their own row
        comps.sort(key=lambda c: (0 if len(self.sym(c['lib']).pins) > 12 else 1))
        for c in comps:
            if c['key'] in ('TP',):
                continue
            l, r, u, d = self.extents(c)
            w, h = r - l, d - u
            if cx + w > maxw or (placed and len(self.sym(c['lib']).pins) > 12 and cx > x0 and False):
                cx = x0; cy += rowh + GAP * 2; rowh = 0
            X = snap(cx - l + 5.08, 2.54); Y = snap(cy - u + 5.08, 2.54)
            self.place(sheet, c, X, Y)
            placed.append((c, X + l, Y + u, X + r, Y + d))
            cx += w + GAP * 1.5
            rowh = max(rowh, h)
        # test points laid out in a row
        tps = [c for c in comps if c['key'] == 'TP']
        if tps:
            cy2 = cy + rowh + GAP * 2 if placed else y0
            cx2 = x0
            for c in tps:
                l, r, u, d = self.extents(c)
                self.place(sheet, c, snap(cx2 - l + 5.08, 2.54), snap(cy2 - u + 5.08, 2.54))
                cx2 += (r - l) + GAP
                if cx2 > maxw:
                    cx2 = x0; cy2 += 40
            cy = cy2; rowh = 30
        # PWR_FLAGs for nets that belong to this sheet's first comp occurrence
        flags = [n for n in self.d.PWR_FLAGS if any(c['sheet'] == sheet.name and n in c['nets'].values() for c in self.d.COMPS.values())
                 and self.flag_sheet(n) == sheet.name]
        fy = cy + rowh + GAP * 2
        for i, n in enumerate(flags):
            fx_ = x0 + i * 40.64
            self.pwr_n += 1
            self._power_node(sheet, "power:PWR_FLAG", "PWR_FLAG", snap(fx_, 2.54), snap(fy, 2.54), 0, flag=True)
            # wire up from the flag pin and label the net
            px, py = snap(fx_, 2.54), snap(fy, 2.54)
            self.stub(sheet, px, py, (0, -1), n)
        # notes
        ny = 12.7
        sheet.items.append(['text', Str(f"{sheet.title}"), ['at', 25.4, 12.7, 0], fx(3.0, bold=True, justify='left'), ['uuid', Str(U())]])
        sheet.items.append(['text', Str("OSBAMS Rev.2 Controller RC1 - REVIEW CANDIDATE, NOT FOR FABRICATION. Evidence: VERIFIED_LOCAL / USER_RELAYED_MANUFACTURER / UNVERIFIED (see evidence register)."),
                            ['at', 25.4, 19.05, 0], fx(1.5, justify='left'), ['uuid', Str(U())]])
        yy = 25.4
        for line in notes:
            sheet.items.append(['text', Str(line), ['at', 25.4, yy, 0], fx(1.27, justify='left'), ['uuid', Str(U())]])
            yy += 3.5
        # choose paper
        maxx = max([p[3] for p in placed] + [x0]) + 30
        maxy = max(fy + 30, cy + rowh + 40)
        for name, w, h in (("A4", 297, 210), ("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594)):
            if maxx <= w - 10 and maxy <= h - 10:
                sheet.paper = name; break
        else:
            sheet.paper = "A1"

    def flag_sheet(self, net):
        for c in self.d.COMPS.values():
            if net in c['nets'].values():
                return c['sheet']

    # ------------------------------------------------------------------ files
    def lib_symbols_node(self):
        out = ['lib_symbols']
        for lid, si in self.syminfo.items():
            out.append(si.node)
        return out

    def sheet_file(self, sheet):
        n = ['kicad_sch', ['version', 20230121], ['generator', 'osbams_schgen'], ['uuid', Str(sheet.uuid)], ['paper', Str(sheet.paper)],
             ['title_block', ['title', Str(sheet.title)], ['date', Str("2026-10-01")], ['rev', Str("RC1")], ['company', Str("OSBAMS Rev.2 Controller")],
              ['comment', 1, Str("RELEASE CANDIDATE 1 - NOT FOR FABRICATION")], ['comment', 2, Str("Manufacturer-document verification is a fabrication gate")]],
             self.lib_symbols_node()] + sheet.items + [['sheet_instances', ['path', Str("/"), ['page', Str("1")]]]]
        return n

    def write_all(self, notes):
        os.makedirs(self.out, exist_ok=True)
        sheets = []
        for name, title in self.d.SHEETS.items():
            sh = Sheet(name, title)
            self.build_sheet(sh, notes.get(name, []))
            sheets.append(sh)
        # symbol lib must be complete before serialising child files
        for sh in sheets:
            txt = kisx.dump(self.sheet_file(sh))
            open(os.path.join(self.out, sh.file), 'w').write(txt + "\n")
        # root
        items = []
        y = 30.0
        for i, sh in enumerate(sheets):
            col, row = i % 2, i // 2
            x, yy = 30 + col * 130, 40 + row * 30
            items.append(['sheet', ['at', x, yy], ['size', 90, 15], ['fields_autoplaced'], ['stroke', ['width', 0.1524], ['type', 'solid']], ['fill', ['color', 0, 0, 0, 0.0]], ['uuid', Str(sh.uuid)],
                          ['property', Str('Sheetname'), Str(sh.name), ['at', x, yy - 0.7, 0], fx(justify='left bottom')],
                          ['property', Str('Sheetfile'), Str(sh.file), ['at', x, yy + 15.7, 0], fx(justify='left top')],
                          ['instances', ['project', Str(self.project), ['path', Str(f"/{self.root_uuid}"), ['page', Str(str(i + 2))]]]]])
        items.append(['text', Str("OSBAMS Rev.2 Controller - RELEASE CANDIDATE 1 (review only; NOT FOR FABRICATION)"), ['at', 30, 15, 0], fx(4, bold=True, justify='left'), ['uuid', Str(U())]])
        items.append(['text', Str("Battery discharge current never enters this PCB. 44 V / 10 A MAX. Hierarchical sheets use global labels for cross-sheet nets."), ['at', 30, 23, 0], fx(2, justify='left'), ['uuid', Str(U())]])
        root = ['kicad_sch', ['version', 20230121], ['generator', 'osbams_schgen'], ['uuid', Str(self.root_uuid)], ['paper', Str("A3")],
                ['title_block', ['title', Str("OSBAMS Rev.2 Controller")], ['date', Str("2026-10-01")], ['rev', Str("RC1")], ['company', Str("OSBAMS")],
                 ['comment', 1, Str("RELEASE CANDIDATE 1 - NOT FOR FABRICATION")]],
                ['lib_symbols']] + items + [['sheet_instances', ['path', Str("/"), ['page', Str("1")]]] + [['path', Str(f"/{sh.uuid}"), ['page', Str(str(i + 2))]] for i, sh in enumerate(sheets)]]
        # KiCad 7 sheet_instances is a list of (path ...) children
        root[-1] = ['sheet_instances', ['path', Str("/"), ['page', Str("1")]]] + [['path', Str(f"/{sh.uuid}"), ['page', Str(str(i + 2))]] for i, sh in enumerate(sheets)]
        open(os.path.join(self.out, self.project + ".kicad_sch"), 'w').write(kisx.dump(root) + "\n")
        return sheets
