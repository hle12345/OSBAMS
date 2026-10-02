"""
gui/limit_panel.py — live permitted-current panel (Rev.2).

    Battery:                    42.0 V
    6060B current rating:       60 A
    6060B power-derived limit:  7.14 A
    OSBAMS validated limit:     10 A
    Battery-profile limit:      X A
    FINAL PERMITTED:            min(...)
    Limiting factor:            ...

All numbers come from equipment.capability — the same function the drivers and
the orchestrator enforce. The voltage shown is the CONSERVATIVE pack voltage
(monotone: sag never lowers it during a run).
"""

from PySide6.QtWidgets import QGroupBox, QFormLayout, QLabel
from equipment import capability as cap


class LimitPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Permitted current (6060B envelope)", parent)
        self._form = QFormLayout(self)
        self._labels = {}
        self.update_limit(cap.compute_permitted_current(None))

    def update_limit(self, lim: cap.CurrentLimit) -> None:
        for label, value in lim.rows():
            if label not in self._labels:
                w = QLabel(value)
                w.setWordWrap(True)
                self._labels[label] = w
                self._form.addRow(label + ":", w)
            self._labels[label].setText(value)
            bold = label in ("FINAL PERMITTED", "Limiting factor")
            self._labels[label].setStyleSheet("font-weight:bold" if bold else "")
        if lim.blocked:
            self._labels["FINAL PERMITTED"].setStyleSheet("font-weight:bold;color:#dc2626")

    def update_live(self, run) -> None:
        """Refresh from a running orchestrator (conservative voltage, profile limit)."""
        v = run.vcons.volts
        if v is None:
            v = run.profile.maximum_voltage_v      # worst case until OCV is known
        self.update_limit(cap.compute_permitted_current(
            v, run.profile.maximum_osbams_test_current_a))
