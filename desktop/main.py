"""
main.py — OSBAMS application entry point

OSBAMS — Open Second-Life Battery Assessment & Management System
An open, modular engineering platform for the assessment, lifecycle tracking,
and engineering decision support of second-life lithium battery assets.

ENGR 696 / 697GW Senior Capstone — Joe Le, SFSU

Usage:
    python main.py
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _fatal(title: str, detail: str) -> int:
    """Report a startup failure on stderr and, if possible, in a dialog."""
    msg = f"{title}\n\n{detail}"
    print(f"\nOSBAMS startup failed\n{'=' * 60}\n{msg}\n", file=sys.stderr)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "OSBAMS — Startup Failed", msg)
    except Exception:
        pass   # no GUI available; stderr message already printed
    return 1


def main() -> int:
    # ── 1. Dependencies ──────────────────────────────────────────────
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as e:
        return _fatal(
            "PySide6 is not installed.",
            f"{e}\n\nInstall with:\n"
            "  conda install -c conda-forge pyside6 -y\n"
            "or\n  pip install -r requirements.txt")

    missing = []
    for mod, pkg in [("serial", "pyserial"), ("pyqtgraph", "pyqtgraph"),
                     ("sklearn", "scikit-learn"), ("numpy", "numpy"),
                     ("reportlab", "reportlab")]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        return _fatal(
            "Required packages are missing.",
            "Missing: " + ", ".join(missing) +
            "\n\nInstall with:\n  conda install -c conda-forge " +
            " ".join(missing) + " -y")

    # ── 2. Configuration and directories ─────────────────────────────
    try:
        import config
        config.ensure_directories()
    except Exception as e:
        return _fatal("Configuration failed to load.",
                      f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}")

    # ── 3. Database ──────────────────────────────────────────────────
    try:
        from db.database import init_db
        from db.migrations import migrate
        init_db()
        added = migrate()
        if added:
            print(f"Database migrated: {len(added)} column(s) added")
    except Exception as e:
        return _fatal(
            "Database initialisation failed.",
            f"{type(e).__name__}: {e}\n\n"
            f"Database path: {getattr(config, 'DB_PATH', 'unknown')}\n\n"
            f"{traceback.format_exc()}")

    # ── 4. Application ───────────────────────────────────────────────
    try:
        app = QApplication(sys.argv)
        app.setApplicationName(config.APP_NAME)
        app.setApplicationDisplayName(config.APP_FULL)
        app.setApplicationVersion(config.APP_VERSION)
        app.setStyle("Fusion")
    except Exception as e:
        return _fatal("Qt application failed to start.",
                      f"{type(e).__name__}: {e}")

    # ── 5. Main window ───────────────────────────────────────────────
    try:
        from gui.main_window import MainWindow
        window = MainWindow()
        window.show()
    except Exception as e:
        return _fatal("Main window failed to load.",
                      f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}")

    print(f"OSBAMS {config.APP_VERSION} — firmware target {config.FIRMWARE_VERSION}, "
          f"protocol v{config.PROTOCOL_VERSION}, schema {config.SCHEMA_VERSION}")

    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as e:
        sys.exit(_fatal("Unhandled exception.",
                        f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"))
