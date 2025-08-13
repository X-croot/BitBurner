#!/usr/bin/env python3
import sys
import os
from PySide6 import QtCore, QtGui, QtWidgets
from ui.main_window import MainWindow
def main():
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()
