"""
registry_tab.py — Battery Registry (v3)
Shows all fields now in the database including safety status and OCV.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QHeaderView, QAbstractItemView,
    QDialog, QFormLayout, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg

from db.database import get_all_batteries, get_tests_for_battery, get_battery

GRADE_BG = {"A":"#d4edda","B":"#d1ecf1","C":"#fff3cd","F":"#f8d7da"}
GRADE_FG = {"A":"#155724","B":"#0c5460","C":"#856404","F":"#721c24"}
SAFETY_BG = {
    "OK":                "#d4edda",
    "Pending":           "#e2e3e5",
    "Pending - Inspect": "#fff3cd",
    "Hold - Verify":     "#ffeeba",
    "Quarantine":        "#f8d7da",
}
SAFETY_FG = {
    "OK":                "#155724",
    "Pending":           "#383d41",
    "Pending - Inspect": "#856404",
    "Hold - Verify":     "#856404",
    "Quarantine":        "#721c24",
}


class RegistryTab(QWidget):
    battery_selected = Signal(int, str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("📋  Battery Registry")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        hdr.addWidget(title)
        hdr.addStretch()

        for label, slot in [
            ("🔄 Refresh",          self.load),
            ("📈 History",          self._open_history),
            ("⚖ Compare",           self._open_compare),
            ("▶ Use for Test",      self._use_selected),
        ]:
            btn = QPushButton(label)
            if label == "▶ Use for Test":
                btn.setStyleSheet(
                    "background:#2563eb;color:white;font-weight:bold;"
                    "padding:4px 12px;border-radius:5px;")
            btn.clicked.connect(slot)
            hdr.addWidget(btn)

        root.addLayout(hdr)

        # Table columns
        COLS = [
            ("OSBAMS ID",    90),
            ("Model",       150),
            ("Manufacturer",150),
            ("Nom V",        60),
            ("Config",       70),
            ("Rated Ah",     70),
            ("OCV (V)",      70),
            ("OCV Date",     85),
            ("Safety Status",120),
            ("Tests",        45),
            ("Last Ah",      65),
            ("SOH%",         55),
            ("Grade",        50),
        ]
        self._col_names = [c[0] for c in COLS]

        self.table = QTableWidget(0, len(COLS))
        self.table.setHorizontalHeaderLabels(self._col_names)
        for i, (_, w) in enumerate(COLS):
            self.table.setColumnWidth(i, w)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setStyleSheet("QTableWidget { font-size:12px; }")
        self.table.doubleClicked.connect(self._open_history)
        root.addWidget(self.table)

        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet("color:#6b7280;font-size:11px;padding:2px;")
        root.addWidget(self.summary_lbl)

        self.load()

    def load(self):
        batteries = get_all_batteries()
        self.table.setRowCount(len(batteries))
        safety_counts = {}

        for r, b in enumerate(batteries):
            tests  = get_tests_for_battery(b["battery_id"])
            latest = tests[0] if tests else {}
            grade  = latest.get("grade") or "—"
            safety = b.get("safety_status") or "Pending"
            safety_counts[safety] = safety_counts.get(safety, 0) + 1

            ocv = b.get("initial_ocv_v")
            ocv_str = f"{ocv:.1f}" if ocv is not None else "—"

            vals = [
                b.get("osbams_id") or f"#{b['battery_id']}",
                b.get("model") or "—",
                b.get("manufacturer") or b.get("brand") or "—",
                f"{b['nominal_voltage']:.0f}V" if b.get("nominal_voltage") else "?",
                b.get("cell_config") or "?",
                f"{b['capacity_rated_ah']:.1f}" if b.get("capacity_rated_ah") else "?",
                ocv_str,
                b.get("ocv_date") or "—",
                safety,
                str(len(tests)),
                f"{latest['capacity_ah']:.2f}" if latest.get("capacity_ah") else "—",
                f"{latest['soh_percent']:.0f}%" if latest.get("soh_percent") else "—",
                grade,
            ]

            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, b["battery_id"])

                # Safety column coloring
                if c == 8:
                    bg = SAFETY_BG.get(safety, "#ffffff")
                    fg = SAFETY_FG.get(safety, "#000000")
                    item.setBackground(QColor(bg))
                    item.setForeground(QColor(fg))
                    f = QFont(); f.setBold(True); item.setFont(f)

                # Grade column coloring
                if c == 12 and grade in GRADE_BG:
                    item.setBackground(QColor(GRADE_BG[grade]))
                    item.setForeground(QColor(GRADE_FG[grade]))

                self.table.setItem(r, c, item)

        total = len(batteries)
        q = safety_counts.get("Quarantine", 0)
        h = safety_counts.get("Hold - Verify", 0)
        ok = safety_counts.get("OK", 0)
        self.summary_lbl.setText(
            f"{total} batteries  ·  "
            f"✅ OK: {ok}  ⏳ Pending: {safety_counts.get('Pending',0)}  "
            f"🔍 Inspect: {safety_counts.get('Pending - Inspect',0)}  "
            f"⚠ Hold: {h}  🚫 Quarantine: {q}")

    def _selected_battery_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _use_selected(self):
        bid = self._selected_battery_id()
        if not bid: return
        b = get_battery(bid)
        safety = b.get("safety_status","")
        if safety in ("Quarantine", "Hold - Verify"):
            QMessageBox.warning(self, "Safety Hold",
                f"{b['osbams_id']} is marked '{safety}'.\n\n"
                f"{b.get('physical_notes','')[:200]}\n\n"
                "Resolve the safety issue before connecting to test hardware.")
            return
        label = f"{b['osbams_id']} — {b.get('manufacturer','?')} {b.get('model','')}"
        self.battery_selected.emit(bid, label)

    def _open_history(self):
        bid = self._selected_battery_id()
        if not bid:
            QMessageBox.information(self,"Select Battery","Click a row first.")
            return
        HistoryDialog(bid, self).exec()

    def _open_compare(self):
        rows = list({i.row() for i in self.table.selectedItems()})
        if len(rows) < 2:
            QMessageBox.information(self,"Select 2",
                "Hold Shift and click two rows to compare.")
            return
        bid1 = self.table.item(rows[0],0).data(Qt.UserRole)
        bid2 = self.table.item(rows[1],0).data(Qt.UserRole)
        CompareDialog(bid1, bid2, self).exec()


# ── History Dialog ────────────────────────────────────────────────────────────
class HistoryDialog(QDialog):
    def __init__(self, battery_id, parent=None):
        super().__init__(parent)
        b = get_battery(battery_id)
        oid = b.get("osbams_id") or f"#{battery_id}"
        self.setWindowTitle(f"History — {oid}")
        self.resize(860, 600)
        layout = QVBoxLayout(self)

        # ── Identity card ─────────────────────────────────────────────
        info = QGroupBox(f"🔋  {oid}  —  {b.get('manufacturer','')} {b.get('model','')}")
        info.setStyleSheet("QGroupBox{font-size:14px;font-weight:bold;}")
        fl = QFormLayout(info)
        safety = b.get("safety_status","—")
        safety_color = SAFETY_FG.get(safety,"#000")
        for field, val in [
            ("Serial #",      b.get("serial_number") or "Unknown"),
            ("Chemistry",     b.get("chemistry") or "?"),
            ("Nominal V / Max V",
             f"{b.get('nominal_voltage','?')} V / {b.get('max_charge_voltage','?')} V"),
            ("Cell config",   b.get("cell_config") or "?"),
            ("Rated Ah / Wh",
             f"{b.get('capacity_rated_ah','?')} Ah / {b.get('energy_rated_wh','?')} Wh"),
            ("Initial OCV",   f"{b.get('initial_ocv_v','Not measured')} V  ({b.get('ocv_date','?')})"),
            ("Physical",      b.get("physical_condition") or "—"),
            ("BMS / LED",     b.get("bms_led_status") or "—"),
            ("Connector",     b.get("connector_condition") or "—"),
            ("Safety",        safety),
            ("Notes",         (b.get("physical_notes") or "—")[:120]),
        ]:
            v_lbl = QLabel(str(val))
            v_lbl.setWordWrap(True)
            if field == "Safety":
                v_lbl.setStyleSheet(
                    f"font-weight:bold; color:{safety_color};")
            fl.addRow(field + ":", v_lbl)
        layout.addWidget(info)

        # ── SOH trend ─────────────────────────────────────────────────
        tests = get_tests_for_battery(battery_id)
        pg.setConfigOption("background","#fafafa")
        pw = pg.PlotWidget(title="SOH % Trend")
        pw.setLabel("left","SOH %"); pw.setLabel("bottom","Test #")
        pw.showGrid(x=True,y=True,alpha=0.3); pw.setYRange(0,105)
        pw.addLegend()

        nums  = list(range(1, len(tests)+1))
        sohs  = [t.get("soh_percent") or 0 for t in reversed(tests)]
        scores= [t.get("reliability_score") or 0 for t in reversed(tests)]
        if nums:
            pw.plot(nums,sohs, pen=pg.mkPen("#2563eb",width=2),
                    symbol="o",symbolBrush="#2563eb",symbolSize=8,name="SOH %")
            pw.plot(nums,scores, pen=pg.mkPen("#16a34a",width=2,style=Qt.DashLine),
                    symbol="s",symbolBrush="#16a34a",symbolSize=7,name="Score")
        else:
            pw.setTitle("SOH % Trend — No tests yet")
        pw.setMaximumHeight(200)
        layout.addWidget(pw)

        # ── Test table ────────────────────────────────────────────────
        tbl = QTableWidget(len(tests),7)
        tbl.setHorizontalHeaderLabels(
            ["Test#","Date","Ah","Wh","SOH%","Score","Grade"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for r, t in enumerate(tests):
            for c, v in enumerate([
                str(len(tests)-r),
                (t.get("started_at") or "?")[:10],
                f"{t.get('capacity_ah',0):.2f}" if t.get("capacity_ah") else "—",
                f"{t.get('energy_wh',0):.1f}"   if t.get("energy_wh")   else "—",
                f"{t.get('soh_percent',0):.0f}%" if t.get("soh_percent") else "—",
                str(t.get("reliability_score") or "—"),
                t.get("grade") or "—",
            ]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                g = t.get("grade")
                if c == 6 and g in GRADE_BG:
                    item.setBackground(QColor(GRADE_BG[g]))
                tbl.setItem(r,c,item)
        tbl.setMaximumHeight(160)
        layout.addWidget(tbl)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignRight)


# ── Compare Dialog ────────────────────────────────────────────────────────────
class CompareDialog(QDialog):
    def __init__(self, bid1, bid2, parent=None):
        super().__init__(parent)
        b1 = get_battery(bid1); b2 = get_battery(bid2)
        id1 = b1.get("osbams_id") or f"#{bid1}"
        id2 = b2.get("osbams_id") or f"#{bid2}"
        self.setWindowTitle(f"Compare {id1} vs {id2}")
        self.resize(1000,580)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"<b>⚖  {id1}  vs  {id2}</b>")
                         .setParent(None) or
                         (lambda l: (l.setStyleSheet("font-size:15px;"), l)[1])(
                             QLabel(f"<b>⚖  {id1}  vs  {id2}</b>")))

        title_lbl = QLabel(f"⚖  {id1}  vs  {id2}")
        title_lbl.setStyleSheet("font-size:15px;font-weight:bold;")
        layout.addWidget(title_lbl)

        tests1 = get_tests_for_battery(bid1)
        tests2 = get_tests_for_battery(bid2)
        t1 = tests1[0] if tests1 else {}
        t2 = tests2[0] if tests2 else {}

        cols = QHBoxLayout()
        for batt, t, label in [(b1,t1,id1),(b2,t2,id2)]:
            box = QGroupBox(label)
            box.setStyleSheet("QGroupBox{font-size:13px;font-weight:bold;}")
            fl = QFormLayout(box)
            grade = t.get("grade") or "—"
            for field, val in [
                ("Model",         f"{batt.get('model','')}"),
                ("Mfr",           batt.get("manufacturer","—")),
                ("Config",        batt.get("cell_config","?") or "?"),
                ("Rated Ah",      f"{batt.get('capacity_rated_ah','?')} Ah"),
                ("Initial OCV",   f"{batt.get('initial_ocv_v','?')} V"),
                ("Safety",        batt.get("safety_status","?")),
                ("Measured Ah",   f"{t.get('capacity_ah','—')}"),
                ("SOH",           f"{t.get('soh_percent','—')}%"),
                ("Score",         str(t.get("reliability_score","—"))),
                ("Grade",         grade),
            ]:
                v_lbl = QLabel(str(val))
                if field == "Grade" and grade in GRADE_FG:
                    v_lbl.setStyleSheet(
                        f"font-weight:bold;color:{GRADE_FG[grade]};")
                fl.addRow(field+":", v_lbl)
            cols.addWidget(box)
        layout.addLayout(cols)

        pg.setConfigOption("background","#fafafa")
        pw = pg.PlotWidget(title="SOH % History")
        pw.setLabel("left","SOH %"); pw.setLabel("bottom","Test #")
        pw.showGrid(x=True,y=True,alpha=0.3); pw.addLegend()
        for i,(bid,batt,tests) in enumerate([(bid1,b1,tests1),(bid2,b2,tests2)]):
            oid = batt.get("osbams_id") or f"#{bid}"
            nums = list(range(1,len(tests)+1))
            sohs = [t.get("soh_percent") or 0 for t in reversed(tests)]
            if nums:
                pw.plot(nums,sohs,
                        pen=pg.mkPen(["#2563eb","#dc2626"][i],width=2),
                        symbol="o",symbolSize=7,name=oid)
        layout.addWidget(pw)

        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignRight)
