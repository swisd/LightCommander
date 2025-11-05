# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import QFile, QTextStream
from ui_lightcmdr import *
import qdarktheme
from modules import *
import time

start = time.time()

def gtime():
    return round(time.time() - start, 2)


app = QApplication(sys.argv)
#app.setStyleSheet(qdarktheme.load_stylesheet())
term(gtime(), "Loading Stylesheet 'stylesheet.qss'")
try:
    file = QFile("stylesheet.qss")
    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    term(gtime(), "Stylesheet Loaded")
    app.setStyleSheet(stream.readAll())
    term(gtime(), "Stylesheet Applied")
except Exception as e:
    term(gtime(), "Stylesheet Error: " + str(e))

window = QMainWindow()
term(gtime(), "window ok")

term(gtime(), "start ok")


window.condition = "Ready"
window.frameref = 0


term(gtime(), "vset ok")
try:
    form = Ui_MainWindow()
    term(gtime(), "form ok")
except Exception as e:
    term(gtime(), "form error: " + str(e))


#form.setDocumentMode(True)
term(gtime(), "setting up...")

try:
    form.setupUi(window)
    term(gtime(), "setup ok")
except Exception as e:
    term(gtime(), "setup error: " + str(e))

try:
    form.retranslateUi(window)
    term(gtime(), "retranslate ok")
except Exception as e:
    term(gtime(), "retranslate error: " + str(e))


window.show()

term(gtime(), "starting window..")


setTitle(window, "REGISTERED", "No Project Selected", "V1.0.2", "OK")
statusMessage(window, "GENERAL", "OK  (User interaction pending)")

term(gtime(), "Awaiting user input")


sys.exit(app.exec_())