from PySide6 import QtCore, QtGui, QtWidgets

Signal = QtCore.Signal

class DropZone(QtWidgets.QFrame):
    fileDropped = Signal(str)
    clicked = Signal()
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("dropzone")
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self._hover = False
        self.setMinimumHeight(180)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect().adjusted(10,10,-10,-10)
        bg = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg.setColorAt(0, QtGui.QColor(20,24,36))
        bg.setColorAt(1, QtGui.QColor(18,22,32))
        p.fillRect(rect, bg)
        pen = QtGui.QPen(QtGui.QColor(80,130,255, 220 if self._hover else 140), 2, QtCore.Qt.DashLine)
        p.setPen(pen)
        p.drawRoundedRect(rect, 16, 16)
        cx, cy = rect.center().x(), rect.center().y() - 6
        plus_len = 30
        pen2 = QtGui.QPen(QtGui.QColor(140, 180, 255), 4)
        p.setPen(pen2)
        p.drawLine(cx - plus_len, cy, cx + plus_len, cy)
        p.drawLine(cx, cy - plus_len, cx, cy + plus_len)
        f = self.font()
        f.setPointSize(12)
        p.setFont(f)
        text = " "
        p.setPen(QtGui.QColor("#cbd5e1"))
        p.drawText(rect.adjusted(0, plus_len+18, 0, 0), QtCore.Qt.AlignHCenter, text)

    def enterEvent(self, e):
        self._hover=True
        self.update()

    def leaveEvent(self, e):
        self._hover=False
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            for u in e.mimeData().urls():
                if u.toLocalFile().lower().endswith((".img",".iso",".zip")):
                    e.acceptProposedAction()
                    return
        e.ignore()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            p = u.toLocalFile()
            if p.lower().endswith((".img",".iso",".zip")):
                self.fileDropped.emit(p)
                break

class Badge(QtWidgets.QLabel):
    def __init__(self, text, color="#2f76ff"):
        super().__init__(text)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet(f"QLabel {{ background:{color}; color:#0c0e12; padding:2px 8px; border-radius:10px; font-weight:700; font-size:11px; }}")
