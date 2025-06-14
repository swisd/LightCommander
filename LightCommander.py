# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import QFile, QTextStream
from ui_lightcmdr import *
import qdarktheme
app = QApplication(sys.argv)
#app.setStyleSheet(qdarktheme.load_stylesheet())
file = QFile("stylesheet.qss")
file.open(QFile.ReadOnly | QFile.Text)
stream = QTextStream(file)
app.setStyleSheet(stream.readAll())
window = QMainWindow()
form = Ui_MainWindow()
#form.setDocumentMode(True)
form.setupUi(window)
window.show()
sys.exit(app.exec_())