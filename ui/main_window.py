import os
from typing import Optional, List, Tuple
from PySide6 import QtCore, QtGui, QtWidgets
from core.utils import human_size, unzip_first
from core.device_manager import list_devices, system_disk_path, Device
from core.imaging import ImageWriter
from ui.styles import dark_qss
from ui.widgets import DropZone, Badge

Signal = QtCore.Signal

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BitBurner")
        self.resize(1100, 720)
        self.setMinimumSize(940, 620)
        self.src_path = ""
        self.src_size = 0
        self.src_tmp = ""
        self.devices: List[Device] = []
        self.selected: Optional[Device] = None
        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)
        self._build_select_page()
        self._build_devices_page()
        self._build_burn_page()
        self.stack.setCurrentWidget(self.pg_select)
        self.setStyleSheet(dark_qss())

    def _card(self, title: str, sub: str) -> Tuple[QtWidgets.QWidget, QtWidgets.QVBoxLayout]:
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(w)
        lay.setContentsMargins(16,16,16,16)
        lay.setSpacing(12)
        header = QtWidgets.QHBoxLayout()
        h1 = QtWidgets.QLabel(title)
        h1.setObjectName("h1")
        h1.setProperty("class","h1")
        subl = QtWidgets.QLabel(sub)
        subl.setProperty("class","muted")
        header.addWidget(h1, 0, QtCore.Qt.AlignVCenter)
        header.addStretch(1)
        header.addWidget(subl, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        frame = QtWidgets.QFrame()
        frame.setObjectName("card")
        inner = QtWidgets.QVBoxLayout(frame)
        inner.setContentsMargins(16,16,16,16)
        inner.setSpacing(10)
        lay.addLayout(header)
        lay.addWidget(frame, 1)
        return w, inner

    def _build_select_page(self):
        self.pg_select, box = self._card("1) Select Image", "ISO/IMG or ZIP — drag & drop or choose via dialog")
        self.drop = DropZone()
        self.drop.setToolTip("*.img, *.iso, *.zip")
        self.drop.fileDropped.connect(self._set_image_path)
        self.drop.clicked.connect(self._open_file_dialog)
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_dialog = QtWidgets.QPushButton("Select File…")
        self.btn_dialog.setProperty("secondary","true")
        self.btn_next1  = QtWidgets.QPushButton("Next →")
        self.btn_next1.setEnabled(False)
        btn_row.addWidget(self.btn_dialog)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_next1)
        self.lbl_sel = QtWidgets.QLabel("No file selected")
        self.lbl_sel.setProperty("class","muted")
        box.addWidget(self.drop)
        box.addWidget(self.lbl_sel)
        box.addLayout(btn_row)
        self.btn_dialog.clicked.connect(self._open_file_dialog)
        self.btn_next1.clicked.connect(lambda: (self._refresh_devices(), self.stack.setCurrentWidget(self.pg_devices)))
        self.stack.addWidget(self.pg_select)

    def _open_file_dialog(self):
        dlg = QtWidgets.QFileDialog(self, "Choose image (.img/.iso/.zip)")
        dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        dlg.setNameFilter("Image Files (*.img *.iso *.zip)")
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if dlg.exec():
            files = dlg.selectedFiles()
            if files:
                self._set_image_path(files[0])

    def _set_image_path(self, path: str):
        if self.src_tmp and os.path.exists(self.src_tmp):
            try:
                os.remove(self.src_tmp)
            except Exception:
                pass
        self.src_tmp = ""
        try:
            if path.lower().endswith(".zip"):
                tmp, size, inner = unzip_first(path)
                if not tmp:
                    QtWidgets.QMessageBox.critical(self, "ZIP", "Failed to extract inner file from ZIP.")
                    return
                self.src_path, self.src_size, self.src_tmp = tmp, size, tmp
                shown = f"{os.path.basename(path)} → {inner} ({human_size(size)})"
            else:
                self.src_path = path
                self.src_size = os.path.getsize(path)
                shown = f"{os.path.basename(path)} ({human_size(self.src_size)})"
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "File", f"Failed to process file: {e}")
            return
        self.lbl_sel.setText(f"Selected: <b>{shown}</b>")
        self.btn_next1.setEnabled(True)
        eff = QtWidgets.QGraphicsColorizeEffect(self.drop)
        eff.setColor(QtGui.QColor(80,160,255))
        self.drop.setGraphicsEffect(eff)
        anim = QtCore.QPropertyAnimation(eff, b"strength", self)
        anim.setDuration(520)
        anim.setStartValue(0.9)
        anim.setEndValue(0.0)
        anim.finished.connect(lambda: self.drop.setGraphicsEffect(None))
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def _build_devices_page(self):
        self.pg_devices, box = self._card("2) Select Target Device", "System disk is protected")
        self.tbl = QtWidgets.QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(["Device", "Path", "Size", "Status"])
        hh = self.tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl.setShowGrid(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setSortingEnabled(False)
        self.tbl.setIconSize(QtCore.QSize(18,18))
        info = QtWidgets.QHBoxLayout()
        info.addWidget(Badge("SYSTEM LOCKED", "#ffbdad"))
        info.addWidget(Badge("USB/SD", "#b6f3c6"))
        info.addStretch(1)
        btns = QtWidgets.QHBoxLayout()
        self.btn_refresh = QtWidgets.QPushButton("Refresh")
        self.btn_refresh.setProperty("secondary","true")
        self.btn_next2 = QtWidgets.QPushButton("Proceed →")
        self.btn_next2.setEnabled(False)
        btns.addWidget(self.btn_refresh)
        btns.addStretch(1)
        btns.addWidget(self.btn_next2)
        self.lbl_sel_dev = QtWidgets.QLabel("No device selected")
        self.lbl_sel_dev.setProperty("class","muted")
        box.addLayout(info)
        box.addWidget(self.tbl, 1)
        box.addWidget(self.lbl_sel_dev)
        box.addLayout(btns)
        self.btn_refresh.clicked.connect(self._refresh_devices)
        self.btn_next2.clicked.connect(lambda: self.stack.setCurrentWidget(self.pg_burn))
        self.tbl.cellClicked.connect(self._on_table_clicked)
        self.stack.addWidget(self.pg_devices)

    def _refresh_devices(self):
        self.devices = list_devices()
        self.tbl.setRowCount(len(self.devices))
        lock_icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        drive_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DriveHDIcon)
        usb_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DriveFDIcon)
        for i, d in enumerate(self.devices):
            name = d.name or os.path.basename(d.path)
            it0 = QtWidgets.QTableWidgetItem(name)
            it1 = QtWidgets.QTableWidgetItem(d.path)
            it2 = QtWidgets.QTableWidgetItem(human_size(d.size))
            status = "SYSTEM (LOCKED)" if d.protected else "Available"
            it3 = QtWidgets.QTableWidgetItem(status)
            it0.setIcon(lock_icon if d.protected else (usb_icon if "usb" in name.lower() else drive_icon))
            f = it0.font()
            f.setBold(True)
            it0.setFont(f)
            if d.protected:
                col = QtGui.QColor("#ff8b8b")
                for it in (it0,it1,it2,it3):
                    it.setForeground(col)
            else:
                it3.setForeground(QtGui.QBrush(QtGui.QColor("#9fe1b4")))
            self.tbl.setItem(i,0,it0)
            self.tbl.setItem(i,1,it1)
            self.tbl.setItem(i,2,it2)
            self.tbl.setItem(i,3,it3)
            self.tbl.setRowHeight(i, 34)
        self.selected = None
        self.lbl_sel_dev.setText("No device selected")
        self.btn_next2.setEnabled(False)

    def _on_table_clicked(self, row, col):
        d = self.devices[row]
        if d.protected:
            QtWidgets.QMessageBox.warning(self, "Locked", "This appears to be the system disk and is not selectable.")
            self.tbl.clearSelection()
            self.selected = None
            self.btn_next2.setEnabled(False)
            self.lbl_sel_dev.setText("No device selected")
            return
        self.selected = d
        self.lbl_sel_dev.setText(f"Selected: <b>{d.name}</b> — {d.path} ({human_size(d.size)})")
        self.btn_next2.setEnabled(True)

    def _build_burn_page(self):
        self.pg_burn, box = self._card("3) Write Image", "Do not remove the device during writing")
        top = QtWidgets.QHBoxLayout()
        self.btn_start = QtWidgets.QPushButton("Write")
        self.btn_cancel = QtWidgets.QPushButton("Stop")
        self.btn_cancel.setProperty("secondary","true")
        self.btn_cancel.setEnabled(False)
        top.addWidget(self.btn_start)
        top.addWidget(self.btn_cancel)
        top.addStretch(1)
        self.p_write = QtWidgets.QProgressBar()
        self.p_write.setRange(0,100)
        self.l_speed = QtWidgets.QLabel("Speed: —/s")
        self.l_speed.setProperty("class","muted")
        self.l_eta   = QtWidgets.QLabel("ETA: —")
        self.l_eta.setProperty("class","muted")
        box.addLayout(top)
        box.addWidget(QtWidgets.QLabel("<b>Progress</b>"))
        box.addWidget(self.p_write)
        box.addWidget(self.l_speed)
        box.addWidget(self.l_eta)
        self.btn_start.clicked.connect(self._start_burn)
        self.btn_cancel.clicked.connect(self._cancel_burn)
        self.stack.addWidget(self.pg_burn)

    def _start_burn(self):
        if not self.src_path:
            QtWidgets.QMessageBox.warning(self, "Missing", "Choose an image first.")
            return
        if not self.selected:
            QtWidgets.QMessageBox.warning(self, "Missing", "Choose a target device.")
            return
        if self.selected.protected:
            QtWidgets.QMessageBox.warning(self, "Locked", "System disk is protected.")
            return
        if self.selected.size and self.src_size and self.src_size > self.selected.size:
            QtWidgets.QMessageBox.critical(self, "Size Mismatch", f"Image size ({human_size(self.src_size)}) is larger than device ({human_size(self.selected.size)}).")
            return
        self.p_write.setValue(0)
        self.l_speed.setText("Speed: —/s")
        self.l_eta.setText("ETA: —")
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.writer = ImageWriter()
        self.writer.on_progress = self._on_progress
        self.writer.on_error = self._on_error
        self.writer.on_finished = self._on_finished
        self.writer.on_canceled = self._on_canceled
        self.writer.start(self.src_path, self.selected.path)

    def _cancel_burn(self):
        if hasattr(self, "writer") and self.writer:
            self.writer.cancel()

    def _on_progress(self, ratio, done, total, bps, eta):
        self.p_write.setValue(int(ratio*100))
        self.l_speed.setText(f"Speed: {human_size(int(bps))}/s")
        self.l_eta.setText("ETA: calculating…" if eta < 0 else f"ETA: {eta}s")

    def _on_error(self, msg):
        self.btn_cancel.setEnabled(False)
        self.btn_start.setEnabled(True)
        QtWidgets.QMessageBox.critical(self, "Write Error", msg)

    def _on_canceled(self):
        self._reset_to_home("Writing canceled.")

    def _on_finished(self):
        self.btn_cancel.setEnabled(False)
        self.p_write.setValue(100)
        QtWidgets.QMessageBox.information(self, "Done", "Image has been written successfully.")
        self._reset_to_home(None)

    def _reset_common(self):
        if self.src_tmp and os.path.exists(self.src_tmp):
            try:
                os.remove(self.src_tmp)
            except Exception:
                pass
        self.src_path = ""
        self.src_size = 0
        self.src_tmp = ""
        self.selected = None

    def _reset_to_home(self, info_text: Optional[str]):
        self._reset_common()
        self._refresh_devices()
        self.lbl_sel.setText("No file selected")
        self.btn_next1.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.btn_start.setEnabled(True)
        self.p_write.setValue(0)
        self.l_speed.setText("Speed: —/s")
        self.l_eta.setText("ETA: —")
        self.stack.setCurrentWidget(self.pg_select)
        if info_text:
            QtWidgets.QMessageBox.information(self, "Info", info_text)
