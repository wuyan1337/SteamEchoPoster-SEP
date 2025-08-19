# widgets/logger.py
# -*- coding: utf-8 -*-
from PyQt6 import QtCore, QtWidgets

class UiLogger(QtCore.QObject):
    message = QtCore.pyqtSignal(str)

    def __init__(self, widget: QtWidgets.QPlainTextEdit):
        super().__init__()
        self.widget = widget
        self.message.connect(self._append)

    @QtCore.pyqtSlot(str)
    def _append(self, text: str):
        self.widget.appendPlainText(text)
        sb = self.widget.verticalScrollBar()
        sb.setValue(sb.maximum())
