import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QTabWidget, QLabel, QComboBox, QPushButton, QGridLayout,
    QLineEdit, QApplication, QVBoxLayout)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Pricer Bono Convertible'
        self.left = 100
        self.top = 100
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = PricerApp(self)
        self.setCentralWidget(self.table_widget)

        self.show()

class PricerApp(QWidget):

    def __init__(self, parent):
        super().__init__( parent )
        self.initUI()

    def initUI(self):
        self._createTabs()

    def _createTabs(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabModel= QWidget()
        self.tabAnalyze = QWidget()
        self.tabs.resize(300, 200)
        self.tabs.addTab(self.tabModel, "Pricer")
        self.tabs.addTab(self.tabAnalyze, "Analizador")
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())