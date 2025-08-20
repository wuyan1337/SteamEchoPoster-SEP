# ui/styles.py
# -*- coding: utf-8 -*-
from PyQt6 import QtCore

def apply_modern_style(widget):
    widget.setStyleSheet("""
        * { font-family: "Segoe UI", "Microsoft YaHei", "Inter", sans-serif; }
        QWidget { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                  stop:0 #f5f7fb, stop:1 #eef1f6); }
        #Card {
            background: rgba(255,255,255,0.72);
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.65);
        }
        QLabel { color: #111; font-size: 13px; }
        QLineEdit, QPlainTextEdit, QDoubleSpinBox {
            background: rgba(255,255,255,0.78);
            border: 1px solid rgba(0,0,0,0.12);
            border-radius: 12px;
            padding: 8px 10px;
            selection-background-color: #d0e1ff;
        }
        QPlainTextEdit { min-height: 100px; }
        QPushButton {
            background: rgba(255,255,255,0.70);
            border: 1px solid rgba(0,0,0,0.12);
            border-radius: 12px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:hover { background: rgba(255,255,255,0.90); }
        QPushButton:pressed { background: rgba(245,245,245,1.0); }
        QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
        QScrollBar::handle:vertical { background: rgba(0,0,0,0.25); border-radius: 5px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }

        QComboBox {
            background: rgba(255, 255, 255, 0.85);  
            color: #000;                           
            border: 1px solid rgba(0, 0, 0, 0.2);
            border-radius: 6px;
            padding: 4px 8px;
            min-height: 28px;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid rgba(0, 0, 0, 0.2);
        }
        QComboBox QAbstractItemView {
            background: #fff;   
            color: #000;        
            selection-background-color: #0078d7; 
            selection-color: #fff;               
        }

    """)

def fade_in(widget):
    widget.setWindowOpacity(0.0)
    anim = QtCore.QPropertyAnimation(widget, b"windowOpacity", widget)
    anim.setDuration(280)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
    anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
