"""
gui/limit_panel.py — shows the permitted-current breakdown (Rev.2).

Displays: battery voltage, profile limit, OSBAMS hardware limit, 6060B current
limit, 6060B power-derived limit and FINAL PERMITTED CURRENT. All numbers come
from equipment.capability — the same function the drivers enforce.
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
                self._labels[label] = w
                self._form.addRow(label + ":", w)
            self._labels[label].setText(value)
            if label.startswith("FINAL"):
                self._labels[label].setStyleSheet("font-weight:bold")
        if lim.blocked:
            self._labels["FINAL PERMITTED CURRENT"].setText(f"BLOCKED — {lim.blocked_reason}")
