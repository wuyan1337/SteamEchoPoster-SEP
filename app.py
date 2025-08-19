# app.py
# -*- coding: utf-8 -*-
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6 import QtWidgets

from ui.main_window import MainWindow

def main():
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
