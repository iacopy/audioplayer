#!/usr/bin/python

import sys
from PyQt5.QtWidgets import QMainWindow, QApplication


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(350, 250)
        self.setWindowTitle('MainWindow')

        self.statusBar().showMessage('This is a message')

app = QApplication(sys.argv)
main = MainWindow()
main.show()
sys.exit(app.exec_())

