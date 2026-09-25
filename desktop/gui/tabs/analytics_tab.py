"""
gui/tabs/analytics_tab.py — Analytics Tab (replaces Fleet Overview)

Sections:
  1. Fleet summary cards (total, healthy, repair, recycle, quarantine)
  2. Grade distribution bar chart
  3. SOH histogram  
  4. Chemistry distribution
  5. Brand / manufacturer breakdown
  6. Research mode: filter → export CSV / statistics
  7. Recent activity feed

Renamed from "Fleet" to "Analytics" per recommendation:
  "Fleet / Statistics / Research / Knowledge / Comparison — much broader"
"""

import csv
import io
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QFileDialog,
    QComboBox, QMessageBox, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
import pyqtgraph as pg

from services.lifecycle import compute_fleet_stats, get_recent_events, FleetStats
from db.database import get_all_batteries, get_tests_for_battery
from config import VISION, FIVE_QUESTIONS


class StatCard(QFrame):
    def __init__(self, title, value="—", color="#2563eb", subtitle=""):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1px solid #e5e7eb;
                border-left: 4px solid {color};
                border-radius: 8px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(1)
        self._t = QLabel(title)
        self._t.setStyleSheet("font-size:9px; color:#6b7280; font-weight:bold;")
        lay.addWidget(self._t)
        self._v = QLabel(value)
        self._v.setStyleSheet(f"font-size:28px; font-weight:bold; color:{color};")
        lay.addWidget(self._v)
        if subtitle:
            self._s = QLabel(subtitle)
            self._s.setStyleSheet("font-size:9px; color:#9ca3af;")
            lay.addWidget(self._s)

    def set_value(self, v): self._v.setText(v)
    def set_sub(self, s):
        if hasattr(self, '_s'): self._s.setText(s)


class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self._all_data = []   # cache for research mode
        self._build_ui()
        self._refresh()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(60_000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 10, 10, 10)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("📊  Analytics")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        hdr.addWidget(title)
        hdr.addStretch()
        ref_btn = QPushButton("🔄 Refresh")
        ref_btn.clicked.connect(self._refresh)
        hdr.addWidget(ref_btn)
        export_btn = QPushButton("📤 Export All Data")
        export_btn.clicked.connect(self._export_all)
        hdr.addWidget(export_btn)
        root.addLayout(hdr)

        # Summary cards
        cards = QHBoxLayout(); cards.setSpacing(6)
        self._c_total   = StatCard("BATTERY ASSETS",  "—", "#1F3864")
        self._c_healthy = StatCard("HEALTHY  (A+B)",  "—", "#16a34a", "Grade A or B")
        self._c_repair  = StatCard("REVIEW  (C+D)",   "—", "#d97706", "Grade C or D")
        self._c_recycle = StatCard("RECYCLE  (F)",    "—", "#dc2626", "Grade F")
        self._c_quar    = StatCard("QUARANTINE",      "—", "#7f1d1d", "Safety hold")
        self._c_tests   = StatCard("TOTAL TESTS",     "—", "#7c3aed")
        for c in [self._c_total, self._c_healthy, self._c_repair,
                  self._c_recycle, self._c_quar, self._c_tests]:
            cards.addWidget(c)
        root.addLayout(cards)

        # Avg row
        avgs = QHBoxLayout(); avgs.setSpacing(6)
        self._c_soh   = StatCard("AVG ESTIMATED SOH", "—", "#0891b2", "tested batteries")
        self._c_cap   = StatCard("AVG CAPACITY",      "—", "#0891b2", "Ah")
        self._c_score = StatCard("AVG SCORE",         "—", "#6d28d9", "/ 100")
        self._c_nt    = StatCard("NOT YET TESTED",    "—", "#6b7280")
        for c in [self._c_soh, self._c_cap, self._c_score, self._c_nt]:
            avgs.addWidget(c)
        root.addLayout(avgs)

        # Charts row
        pg.setConfigOption("background", "#fafafa")
        pg.setConfigOption("foreground", "#222")

        charts = QHBoxLayout(); charts.setSpacing(8)

        # Grade distribution
        grade_box = QGroupBox("Grade distribution")
        gl = QVBoxLayout(grade_box)
        self._grade_plot = pg.PlotWidget()
        self._grade_plot.setMinimumHeight(180); self._grade_plot.setMaximumHeight(220)
        self._grade_plot.showGrid(x=False, y=True, alpha=0.3)
        self._grade_plot.setLabel("left", "Count")
        self._grade_plot.getAxis("bottom").setTicks(
            [[(i, g) for i, g in enumerate(["A","B","C","D","F","No test"])]])
        gl.addWidget(self._grade_plot)
        charts.addWidget(grade_box, 2)

        # SOH histogram
        soh_box = QGroupBox("SOH distribution (%)")
        sl = QVBoxLayout(soh_box)
        self._soh_plot = pg.PlotWidget()
        self._soh_plot.setMinimumHeight(180); self._soh_plot.setMaximumHeight(220)
        self._soh_plot.showGrid(x=False, y=True, alpha=0.3)
        self._soh_plot.setLabel("left", "Count"); self._soh_plot.setLabel("bottom", "SOH %")
        sl.addWidget(self._soh_plot)
        charts.addWidget(soh_box, 2)

        # Brand/Manufacturer bar
        brand_box = QGroupBox("Battery assets by manufacturer")
        bl = QVBoxLayout(brand_box)
        self._brand_plot = pg.PlotWidget()
        self._brand_plot.setMinimumHeight(180); self._brand_plot.setMaximumHeight(220)
        self._brand_plot.showGrid(x=False, y=True, alpha=0.3)
        self._brand_plot.setLabel("left", "Count")
        bl.addWidget(self._brand_plot)
        charts.addWidget(brand_box, 2)

        root.addLayout(charts)

        # Research mode + activity feed
        bottom = QHBoxLayout(); bottom.setSpacing(8)

        # Research mode
        research_box = QGroupBox("Research Mode — Filter and Export")
        rl = QVBoxLayout(research_box)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Grade:"))
        self._grade_filter = QComboBox()
        self._grade_filter.addItems(["All","A","B","C","D","F","Not tested"])
        filter_row.addWidget(self._grade_filter)
        filter_row.addWidget(QLabel("Safety:"))
        self._safety_filter = QComboBox()
        self._safety_filter.addItems(["All","OK","Pending","Hold","Quarantine"])
        filter_row.addWidget(self._safety_filter)
        filter_btn = QPushButton("Apply Filter")
        filter_btn.clicked.connect(self._apply_filter)
        filter_row.addWidget(filter_btn)
        stats_btn = QPushButton("Compute Stats")
        stats_btn.clicked.connect(self._compute_stats)
        filter_row.addWidget(stats_btn)
        rl.addLayout(filter_row)

        self._research_table = QTableWidget(0, 7)
        self._research_table.setHorizontalHeaderLabels(
            ["ID", "Manufacturer", "Model", "Chemistry", "SOH%", "Score", "Grade"])
        self._research_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._research_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._research_table.setStyleSheet("font-size:11px;")
        self._research_table.setMaximumHeight(200)
        rl.addWidget(self._research_table)

        export_row = QHBoxLayout()
        csv_btn = QPushButton("💾 Export filtered CSV")
        csv_btn.clicked.connect(self._export_filtered_csv)
        export_row.addWidget(csv_btn)
        self._stats_lbl = QLabel("")
        self._stats_lbl.setStyleSheet("font-size:10px; color:#6b7280;")
        self._stats_lbl.setWordWrap(True)
        export_row.addWidget(self._stats_lbl, 1)
        rl.addLayout(export_row)

        bottom.addWidget(research_box, 3)

        # Activity feed
        feed_box = QGroupBox("Recent activity")
        fl = QVBoxLayout(feed_box)
        self._feed_table = QTableWidget(0, 4)
        self._feed_table.setHorizontalHeaderLabels(["ID","Date","Event","Description"])
        self._feed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._feed_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._feed_table.setAlternatingRowColors(True)
        self._feed_table.setStyleSheet("font-size:11px;")
        fl.addWidget(self._feed_table)
        bottom.addWidget(feed_box, 2)

        root.addLayout(bottom)

        # Vision footer
        v_lbl = QLabel(VISION[:140] + "...")
        v_lbl.setWordWrap(True)
        v_lbl.setStyleSheet("color:#9ca3af; font-size:9px; font-style:italic; padding:2px 0;")
        root.addWidget(v_lbl)

    # ── Data ─────────────────────────────────────────────────────────

    def _load_all(self):
        rows = []
        for b in get_all_batteries():
            if not b.get("model") and not b.get("manufacturer"):
                continue
            tests = [t for t in get_tests_for_battery(b["battery_id"])
                     if t.get("ended_at")]
            latest = tests[0] if tests else {}
            rows.append({
                "osbams_id":    b.get("osbams_id") or f"#{b['battery_id']}",
                "manufacturer": b.get("manufacturer") or b.get("brand") or "Unknown",
                "model":        b.get("model") or "—",
                "chemistry":    b.get("chemistry") or "?",
                "safety_status":b.get("safety_status") or "Pending",
                "soh":          latest.get("soh_percent"),
                "score":        latest.get("reliability_score"),
                "grade":        latest.get("grade") or "—",
                "tested":       bool(tests),
            })
        self._all_data = rows
        return rows

    def _refresh(self):
        try:
            stats = compute_fleet_stats()
            data  = self._load_all()
            self._update_cards(stats)
            self._update_grade_chart(stats)
            self._update_soh_histogram(data)
            self._update_brand_chart(data)
            self._update_feed()
            self._apply_filter()
        except Exception as e:
            print(f"[AnalyticsTab] {e}")

    def _update_cards(self, s: FleetStats):
        self._c_total.set_value(str(s.total_batteries))
        self._c_healthy.set_value(str(s.healthy_count))
        self._c_repair.set_value(str(s.repair_count))
        self._c_recycle.set_value(str(s.recycle_count))
        self._c_quar.set_value(str(s.quarantine_count))
        self._c_tests.set_value(str(s.total_tests))
        self._c_soh.set_value(f"{s.avg_soh_pct:.1f}%" if s.avg_soh_pct else "—")
        self._c_cap.set_value(f"{s.avg_capacity_ah:.2f}" if s.avg_capacity_ah else "—")
        self._c_score.set_value(str(int(s.avg_score)) if s.avg_score else "—")
        self._c_nt.set_value(str(s.not_tested))
        if s.most_common_issue != "—":
            self._c_nt.set_sub(f"Common: {s.most_common_issue}")

    def _update_grade_chart(self, s: FleetStats):
        self._grade_plot.clear()
        vals   = [s.grade_a, s.grade_b, s.grade_c, s.grade_d, s.grade_f, s.not_tested]
        colors = ["#16a34a","#2563eb","#d97706","#dc2626","#7f1d1d","#9ca3af"]
        for i,(v,c) in enumerate(zip(vals, colors)):
            self._grade_plot.addItem(pg.BarGraphItem(x=[i], height=[v],
                                                     width=0.6, brush=c, pen="#fff"))
        self._grade_plot.setXRange(-0.5, 5.5)
        self._grade_plot.setYRange(0, max(vals or [1]) * 1.3)

    def _update_soh_histogram(self, data):
        self._soh_plot.clear()
        sohs = [r["soh"] for r in data if r["soh"] is not None]
        if not sohs:
            return
        import math
        bins = [0]*10  # 0-9, 10-19, ..., 90-99, 100
        for s in sohs:
            idx = min(int(s // 10), 9)
            bins[idx] += 1
        xs = [i * 10 + 5 for i in range(10)]
        self._soh_plot.addItem(pg.BarGraphItem(x=xs, height=bins, width=9,
                                                brush="#2563eb", pen="#fff"))
        self._soh_plot.setXRange(0, 105)
        self._soh_plot.setYRange(0, max(bins or [1]) * 1.3)

    def _update_brand_chart(self, data):
        self._brand_plot.clear()
        counts = {}
        for r in data:
            m = r["manufacturer"].split("/")[0].split("(")[0].strip()
            counts[m] = counts.get(m, 0) + 1
        if not counts:
            return
        sorted_brands = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [b[0][:12] for b in sorted_brands]
        vals   = [b[1] for b in sorted_brands]
        colors = ["#2563eb","#7c3aed","#16a34a","#d97706","#dc2626",
                  "#0891b2","#6b7280","#9ca3af"]
        for i,(v,c) in enumerate(zip(vals, colors)):
            self._brand_plot.addItem(pg.BarGraphItem(x=[i], height=[v],
                                                     width=0.6, brush=c, pen="#fff"))
        self._brand_plot.getAxis("bottom").setTicks(
            [[(i, l) for i, l in enumerate(labels)]])
        self._brand_plot.setXRange(-0.5, len(labels) - 0.5)
        self._brand_plot.setYRange(0, max(vals) * 1.3)

    def _update_feed(self):
        events = get_recent_events(12)
        self._feed_table.setRowCount(len(events))
        for r, e in enumerate(events):
            for c, v in enumerate([e.osbams_id, e.date_str,
                                    f"{e.icon} {e.label}", e.description]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter if c < 3 else Qt.AlignLeft)
                self._feed_table.setItem(r, c, item)

    # ── Research mode ─────────────────────────────────────────────────

    def _filtered_data(self):
        gf = self._grade_filter.currentText()
        sf = self._safety_filter.currentText()
        out = []
        for r in self._all_data:
            if gf != "All":
                if gf == "Not tested" and r["tested"]: continue
                if gf != "Not tested" and r["grade"] != gf: continue
            if sf != "All":
                if sf.lower() not in (r["safety_status"] or "").lower(): continue
            out.append(r)
        return out

    def _apply_filter(self):
        rows = self._filtered_data()
        self._research_table.setRowCount(len(rows))
        GRADE_BG = {"A":"#d4edda","B":"#d1ecf1","C":"#fff3cd","D":"#fdefd3","F":"#f8d7da"}
        for r, d in enumerate(rows):
            soh   = f"{d['soh']:.0f}%" if d["soh"] else "—"
            score = str(d["score"]) if d["score"] else "—"
            grade = d["grade"]
            for c, v in enumerate([d["osbams_id"], d["manufacturer"],
                                    d["model"], d["chemistry"], soh, score, grade]):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignCenter)
                if c == 6 and grade in GRADE_BG:
                    item.setBackground(QColor(GRADE_BG[grade]))
                self._research_table.setItem(r, c, item)

    def _compute_stats(self):
        rows = self._filtered_data()
        sohs   = [r["soh"]   for r in rows if r["soh"]   is not None]
        scores = [r["score"] for r in rows if r["score"] is not None]
        if not rows:
            self._stats_lbl.setText("No data matching filter.")
            return
        n = len(rows)
        avg_soh   = sum(sohs)   / len(sohs)   if sohs   else 0
        avg_score = sum(scores) / len(scores) if scores else 0
        min_soh   = min(sohs)   if sohs else 0
        max_soh   = max(sohs)   if sohs else 0
        import math
        std_soh = math.sqrt(sum((s - avg_soh)**2 for s in sohs) / len(sohs)) if len(sohs) > 1 else 0
        self._stats_lbl.setText(
            f"n={n}  |  SOH: avg={avg_soh:.1f}%  min={min_soh:.1f}%  "
            f"max={max_soh:.1f}%  σ={std_soh:.1f}%  |  Avg score={avg_score:.0f}")

    # ── Exports ───────────────────────────────────────────────────────

    def _export_filtered_csv(self):
        rows = self._filtered_data()
        if not rows:
            QMessageBox.information(self, "No Data", "No rows match the current filter.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Filtered Data", "osbams_export.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(rows)
        QMessageBox.information(self, "Exported", f"Saved {len(rows)} rows to {path}")

    def _export_all(self):
        if not self._all_data:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export All Battery Data", "osbams_all_batteries.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self._all_data[0].keys())
            w.writeheader(); w.writerows(self._all_data)
        QMessageBox.information(self, "Exported",
                                f"Exported {len(self._all_data)} battery records to {path}")

    def refresh(self):
        self._refresh()
