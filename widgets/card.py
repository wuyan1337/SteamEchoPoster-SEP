# widgets/card.py
# -*- coding: utf-8 -*-
from PyQt6 import QtWidgets, QtGui

class Card(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setGraphicsEffect(self._make_shadow())

    def _make_shadow(self):
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 12)
        shadow.setColor(QtGui.QColor(0, 0, 0, 40))
        return shadow
