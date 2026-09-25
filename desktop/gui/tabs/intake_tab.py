"""
intake_tab.py — Battery Registration tab (renamed from Intake)

New features:
  - OSB-XXXX auto ID displayed after save
  - QR code generated and shown
  - Photo capture (file import or webcam placeholder)
  - OEM barcode / serial number / fleet ID fields
"""

import os
import shutil
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QPushButton, QMessageBox, QGroupBox,
    QFileDialog, QFrame
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QImage

from db.database import create_battery

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "db", "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)


def _make_qr_pixmap(text: str, size: int = 180) -> QPixmap:
    """Generate a QR code pixmap for the given text."""
    try:
        import qrcode
        from PIL import Image
        import io
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        qi = QImage.fromData(buf.read())
        return QPixmap.fromImage(qi).scaled(size, size, Qt.KeepAspectRatio,
                                            Qt.SmoothTransformation)
    except ImportError:
        # qrcode not installed — return blank pixmap
        px = QPixmap(size, size)
        px.fill()
        return px


class IntakeTab(QWidget):
    battery_saved = Signal(int, str)   # (battery_id, osbams_id label)

    def __init__(self):
        super().__init__()
        self._photo_path: str | None = None
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setSpacing(16)

        # ── LEFT COLUMN: form ──────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(10)

        title = QLabel("🔋  Battery Registration")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        left.addWidget(title)

        # Source
        src_box = QGroupBox("Source")
        sf = QFormLayout(src_box)
        self.source_combo = QComboBox()
        self.source_combo.addItems(["fleet", "consumer_retail", "unknown"])
        sf.addRow("Source type:", self.source_combo)
        self.brand_edit = QLineEdit()
        self.brand_edit.setPlaceholderText("e.g. Spin, Lime, Gotrax, Ninebot")
        sf.addRow("Brand:", self.brand_edit)
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g. ES200, Max G2, G4 Pro")
        sf.addRow("Model:", self.model_edit)
        left.addWidget(src_box)

        # OEM IDs
        id_box = QGroupBox("OEM Identification (optional)")
        idf = QFormLayout(id_box)
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("Scan or type OEM serial number")
        idf.addRow("Serial number:", self.serial_edit)
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText("Barcode / QR from label")
        idf.addRow("Barcode:", self.barcode_edit)
        self.fleet_edit = QLineEdit()
        self.fleet_edit.setPlaceholderText("Fleet asset tag (if any)")
        idf.addRow("Fleet ID:", self.fleet_edit)
        left.addWidget(id_box)

        # Electrical specs
        elec_box = QGroupBox("Electrical Specs (leave 0 if unknown)")
        ef = QFormLayout(elec_box)
        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(0, 120); self.voltage_spin.setSuffix(" V")
        self.voltage_spin.setDecimals(1)
        ef.addRow("Nominal voltage:", self.voltage_spin)
        self.chemistry_combo = QComboBox()
        self.chemistry_combo.addItems(["unknown", "NMC", "NCA", "LFP"])
        ef.addRow("Chemistry:", self.chemistry_combo)
        self.cells_spin = QSpinBox()
        self.cells_spin.setRange(0, 30)
        ef.addRow("Cell count:", self.cells_spin)
        self.cap_spin = QDoubleSpinBox()
        self.cap_spin.setRange(0, 200); self.cap_spin.setSuffix(" Ah")
        self.cap_spin.setDecimals(1)
        ef.addRow("Rated capacity:", self.cap_spin)
        self.wh_spin = QDoubleSpinBox()
        self.wh_spin.setRange(0, 10000); self.wh_spin.setSuffix(" Wh")
        self.wh_spin.setDecimals(0)
        ef.addRow("Rated energy:", self.wh_spin)
        left.addWidget(elec_box)

        # Physical
        phys_box = QGroupBox("Physical Condition")
        pf = QFormLayout(phys_box)
        self.phys_spin = QSpinBox()
        self.phys_spin.setRange(0, 10); self.phys_spin.setValue(8)
        pf.addRow("Condition (0=poor, 10=perfect):", self.phys_spin)
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(70)
        self.notes_edit.setPlaceholderText(
            "Swelling, corrosion, dents, unusual smell, damaged leads...")
        pf.addRow("Notes:", self.notes_edit)
        left.addWidget(phys_box)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("💾  Register Battery")
        self.save_btn.setFixedHeight(38)
        self.save_btn.setStyleSheet(
            "background:#2563eb; color:white; font-weight:bold; border-radius:6px;")
        self.save_btn.clicked.connect(self._save)
        btn_row.addWidget(self.save_btn)
        left.addLayout(btn_row)
        left.addStretch()

        root.addLayout(left, 3)

        # ── RIGHT COLUMN: photo + QR ───────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(12)

        # Photo panel
        photo_box = QGroupBox("Battery Photo")
        photo_layout = QVBoxLayout(photo_box)

        self.photo_label = QLabel()
        self.photo_label.setFixedSize(220, 180)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet(
            "border: 2px dashed #aaa; border-radius:8px; background:#f5f5f5;")
        self.photo_label.setText("No photo\n📷")
        photo_layout.addWidget(self.photo_label, alignment=Qt.AlignCenter)

        photo_btns = QHBoxLayout()
        self.import_btn = QPushButton("📁 Import Photo")
        self.import_btn.clicked.connect(self._import_photo)
        photo_btns.addWidget(self.import_btn)
        # Webcam placeholder — requires opencv, skip for now
        self.cam_btn = QPushButton("📷 Camera")
        self.cam_btn.setToolTip("Requires OpenCV (pip install opencv-python)")
        self.cam_btn.clicked.connect(self._camera_photo)
        photo_btns.addWidget(self.cam_btn)
        photo_layout.addLayout(photo_btns)
        right.addWidget(photo_box)

        # QR panel
        qr_box = QGroupBox("Battery QR Code")
        qr_layout = QVBoxLayout(qr_box)

        self.qr_label = QLabel()
        self.qr_label.setFixedSize(190, 190)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setStyleSheet("background:#fff;")
        self.qr_label.setText("Save battery\nto generate QR")
        qr_layout.addWidget(self.qr_label, alignment=Qt.AlignCenter)

        self.osbams_id_label = QLabel("—")
        self.osbams_id_label.setAlignment(Qt.AlignCenter)
        self.osbams_id_label.setStyleSheet(
            "font-size:22px; font-weight:bold; color:#2563eb; letter-spacing:2px;")
        qr_layout.addWidget(self.osbams_id_label)

        self.print_qr_btn = QPushButton("🖨  Save QR as PNG")
        self.print_qr_btn.setEnabled(False)
        self.print_qr_btn.clicked.connect(self._save_qr)
        qr_layout.addWidget(self.print_qr_btn)

        right.addWidget(qr_box)
        right.addStretch()

        root.addLayout(right, 2)

        self._last_qr_pixmap: QPixmap | None = None
        self._last_osbams_id: str | None = None

    # ── Photo handling ────────────────────────────────────────────────

    def _import_photo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Battery Photo", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if path:
            self._photo_path = path
            px = QPixmap(path).scaled(220, 180, Qt.KeepAspectRatio,
                                       Qt.SmoothTransformation)
            self.photo_label.setPixmap(px)
            self.photo_label.setText("")

    def _camera_photo(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if not ret:
                QMessageBox.warning(self, "Camera", "Could not capture from camera.")
                return
            tmp = os.path.join(PHOTOS_DIR, "_cam_tmp.jpg")
            cv2.imwrite(tmp, frame)
            self._photo_path = tmp
            px = QPixmap(tmp).scaled(220, 180, Qt.KeepAspectRatio,
                                      Qt.SmoothTransformation)
            self.photo_label.setPixmap(px)
            self.photo_label.setText("")
        except ImportError:
            QMessageBox.information(self, "Camera",
                "Install opencv-python to use camera:\npip install opencv-python")

    # ── Save ──────────────────────────────────────────────────────────

    def _save(self):
        source = self.source_combo.currentText()
        chem   = self.chemistry_combo.currentText()
        if chem == "unknown": chem = None
        v   = self.voltage_spin.value() or None
        cap = self.cap_spin.value()      or None
        wh  = self.wh_spin.value()       or None
        cells = self.cells_spin.value()  or None

        # Copy photo to permanent location after we know battery_id
        photo_dest = None

        battery_id, osbams_id = create_battery(
            source_type       = source,
            brand             = self.brand_edit.text().strip() or None,
            model             = self.model_edit.text().strip() or None,
            nominal_voltage   = v,
            chemistry         = chem,
            cell_count        = cells,
            capacity_rated_ah = cap,
            energy_rated_wh   = wh,
            physical_notes    = self.notes_edit.toPlainText().strip() or None,
            physical_score    = self.phys_spin.value(),
            serial_number     = self.serial_edit.text().strip() or None,
            fleet_id          = self.fleet_edit.text().strip() or None,
            barcode           = self.barcode_edit.text().strip() or None,
            photo_path        = None,   # update after copy
        )

        # Copy photo to db/photos/<osbams_id>.jpg
        if self._photo_path and os.path.exists(self._photo_path):
            ext = os.path.splitext(self._photo_path)[1]
            photo_dest = os.path.join(PHOTOS_DIR, f"{osbams_id}{ext}")
            shutil.copy2(self._photo_path, photo_dest)
            from db.database import update_battery_photo
            update_battery_photo(battery_id, photo_dest)

        # Generate QR
        qr_text = f"OSBAMS:{osbams_id}"
        px = _make_qr_pixmap(qr_text, 180)
        self._last_qr_pixmap = px
        self._last_osbams_id = osbams_id
        self.qr_label.setPixmap(px)
        self.qr_label.setText("")
        self.osbams_id_label.setText(osbams_id)
        self.print_qr_btn.setEnabled(True)

        label = f"{osbams_id} — {self.brand_edit.text().strip() or source}"
        QMessageBox.information(self, "Registered",
            f"Battery registered as {osbams_id}")
        self.battery_saved.emit(battery_id, label)

    def _save_qr(self):
        if not self._last_qr_pixmap:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save QR Code",
            f"{self._last_osbams_id}_QR.png", "PNG (*.png)")
        if path:
            self._last_qr_pixmap.save(path)
            QMessageBox.information(self, "Saved", f"QR saved to {path}")
