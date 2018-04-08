import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QTabWidget, QLabel, QComboBox, QPushButton, QGridLayout,
    QLineEdit, QApplication, QVBoxLayout, QHBoxLayout, QListWidget)

from PyQt5.QtGui import QDoubleValidator
from viewmodels.viewmodels import ListViewModel, TextViewModel, ConvertibleBondViewModel
import models.data as model_data

class App(QMainWindow):
    def __init__(self, viewModel):
        super().__init__()
        self.title = 'Pricer Bono Convertible'
        self.left = 100
        self.top = 100
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.pricerWidget = PricerWidget(self, viewModel)
        self.setCentralWidget(self.pricerWidget)

        self.show()

class PricerWidget(QWidget):

    def __init__(self, parent, viewModel):
        super().__init__( parent )
        self.convertibleBondViewModel = viewModel
        self.initUI()

    def initUI(self):
        self._createTabs()
        self._setPricerTab()

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

    def _setPricerTab(self):
        layout = QGridLayout()
        self.tabModel.setLayout(layout)

        inputs = [self._makeLineEditWidget(self.convertibleBondViewModel.bondPriceViewModel, 'Precio Bono:', readOnly=True),
                  self._makeLineEditWidget(self.convertibleBondViewModel.timeViewModel, 'Periodos'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.deltaTimeViewModel, 'Delta T'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.irVolatilityViewModel,'Volatilidad Tasa de Interes'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.faceValueViewModel, 'Face value'),
                  self._makeEditableListWidget(self.convertibleBondViewModel.riskFreeViewModel,
                                               'Zero coupons libre de riesgo'),
                  self._makeEditableListWidget(self.convertibleBondViewModel.riskyZeroCouponsViewModel,
                                               'Zero coupons con riesgo'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.recoveryViewModel, 'Recovery'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.initialStockPriceViewModel, 'Precio Stock'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.stockVolatilityViewModel, 'Volatilidad Stock'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.irStockCorrelationViewModel, 'Correlacion Tasa-Stock'),
                  self._makeLineEditWidget(self.convertibleBondViewModel.conversionFactorViewModel,
                                           'Factor Conversion'),
                  self._makeEditableListWidget(self.convertibleBondViewModel.featureScheduleViewModel,
                                               'Periodo,Valor Call,Valor Put')]

        for i in range(len(inputs)):
            layout.addWidget( inputs[i], i, 0)

        bondPriceButton = QPushButton(text='Valuar')
        bondPriceButton.clicked[bool].connect(lambda: self.convertibleBondViewModel.onPriceBondClicked())
        layout.addWidget(bondPriceButton, 0, 1)

    def _makeEditableListWidget(self, viewModel, title='' ):
        parentWidget = QWidget(self)
        parentLayout = QVBoxLayout()
        parentWidget.setLayout( parentLayout )

        mainWidget = QWidget(self)
        layout = QHBoxLayout()
        listWidget      = QListWidget()
        listWidget.setSelectionMode( QListWidget.MultiSelection)
        addItemLabel    = QLabel( text='Ingrese valor')
        addItemLineEdit = QLineEdit(text='' )
        addItemLineEdit.setValidator( QDoubleValidator() )
        addItemButton   = QPushButton(text='Agregar')
        removeItemsButton = QPushButton(text='Remover')
        removeAllItemsButton = QPushButton(text='Remover Todos')
        viewModel.listView = listWidget
        viewModel.newItemInput = addItemLineEdit
        addItemButton.clicked[bool].connect(lambda : viewModel.onAddNewItem())
        removeItemsButton.clicked[bool].connect(lambda : viewModel.onRemoveSelectedItems())
        removeAllItemsButton.clicked[bool].connect(lambda : viewModel.onRemoveAllItems())
        layout.addWidget(listWidget)
        layout.addWidget(addItemLabel)
        layout.addWidget(addItemLineEdit)
        layout.addWidget(addItemButton)
        layout.addWidget(removeItemsButton)
        layout.addWidget(removeAllItemsButton)
        mainWidget.setLayout( layout )

        parentLayout.addWidget( QLabel(text=title))
        parentLayout.addWidget( mainWidget )
        return parentWidget

    def _makeLineEditWidget(self, viewModel, title='', readOnly=False):
        parentLayout = QHBoxLayout()
        mainWidget = QWidget(self)
        label = QLabel(text=title)
        textLineEdit = QLineEdit(text='')
        textLineEdit.setValidator(QDoubleValidator())
        textLineEdit.setDisabled(readOnly)
        textLineEdit.textChanged.connect( viewModel.onTextChanged )
        parentLayout.addWidget( label )
        parentLayout.addWidget( textLineEdit )
        viewModel.inputText = textLineEdit
        mainWidget.setLayout( parentLayout )

        return mainWidget




if __name__ == '__main__':
    viewModel = ConvertibleBondViewModel()
    app = QApplication(sys.argv)
    ex = App(viewModel)
    viewModel.update( model_data.chambersPaperRealExampleInput())
    sys.exit(app.exec_())