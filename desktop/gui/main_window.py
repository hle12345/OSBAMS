"""
main_window.py — OSBAMS v8  (Lifecycle Platform)

Tabs:
  1. 🔋 Battery Registration
  2. ⚡ Dashboard
  3. 📊 Health Estimation
  4. 📋 Registry
  5. 🏭 Fleet Overview      ← NEW

Window title and status bar now reflect the lifecycle platform framing.
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from PySide6.QtCore import Slot

from gui.tabs.intake_tab    import IntakeTab
from gui.tabs.dashboard_tab import DashboardTab
from gui.tabs.ai_tab        import AITab
from gui.tabs.registry_tab  import RegistryTab
from gui.tabs.analytics_tab import AnalyticsTab
from db.database import init_db
from db.migrations import migrate
from config import APP_NAME, APP_FULL, VISION, APP_VERSION


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        migrate()

        self.setWindowTitle(
            f"OSBAMS v{APP_VERSION}  —  Open Battery Engineering Platform")
        self.resize(1340, 880)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setStyleSheet(
            "QTabBar::tab { padding: 8px 18px; font-size:13px; }")
        self.setCentralWidget(self.tabs)

        self.intake_tab  = IntakeTab()
        self.dash_tab    = DashboardTab()
        self.ai_tab      = AITab()
        self.registry_tab= RegistryTab()
        self.analytics_tab = AnalyticsTab()

        self.tabs.addTab(self.intake_tab,   "🔋  Battery Registration")
        self.tabs.addTab(self.dash_tab,     "⚡  Dashboard")
        self.tabs.addTab(self.ai_tab,       "📊  Health Estimation")
        self.tabs.addTab(self.registry_tab, "📋  Registry")
        self.tabs.addTab(self.analytics_tab, "📊  Analytics")

        self.intake_tab.battery_saved.connect(self._on_battery_saved)
        self.registry_tab.battery_selected.connect(self._on_battery_selected)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(
            "OSBAMS — Register a battery asset to begin, or open Analytics to view fleet status.")

    @Slot(int, str)
    def _on_battery_saved(self, battery_id: int, label: str):
        self.dash_tab.set_battery(battery_id, label)
        self.ai_tab.set_battery(battery_id)
        self.registry_tab.load()
        self.analytics_tab.refresh()
        self.tabs.setCurrentIndex(1)
        self.status.showMessage(
            f"{label} registered ✓  —  Select a port and press Start Test.")

    @Slot(int, str)
    def _on_battery_selected(self, battery_id: int, label: str):
        self.dash_tab.set_battery(battery_id, label)
        self.ai_tab.set_battery(battery_id)
        self.tabs.setCurrentIndex(1)
        self.status.showMessage(
            f"Loaded {label}  —  Select a port and press Start Test.")
