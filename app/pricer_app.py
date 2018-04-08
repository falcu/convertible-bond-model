import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QTabWidget, QLabel, QComboBox, QPushButton, QGridLayout,
    QLineEdit, QApplication, QVBoxLayout, QHBoxLayout, QListWidget, QCheckBox)

from PyQt5.QtGui import QDoubleValidator
from viewmodels.viewmodels import ConvertibleBondViewModel, SensitivityAnalyzerViewModel
import models.data as model_data
import PyQt5.QtCore as qtCore

class App(QMainWindow):
    def __init__(self, convertibleBondViewModel, analyzerViewModel):
        super().__init__()
        self.title = 'Pricer Bono Convertible'
        self.left = 100
        self.top = 100
        self.width = 300
        self.height = 200
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.pricerWidget = PricerWidget(self, convertibleBondViewModel, analyzerViewModel)
        self.setCentralWidget(self.pricerWidget)

        self.show()

class PricerWidget(QWidget):

    def __init__(self, parent, convertibleBondViewModel, analyzerViewModel):
        super().__init__( parent )
        self.convertibleBondViewModel = convertibleBondViewModel
        self.analyzerViewModel = analyzerViewModel
        self.initUI()

    def initUI(self):
        self._createTabs()
        self._setPricerTab()
        self._setAnalyzeTab()

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
        layout = QGridLayout(self.tabModel)
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

    def _makeComboBoxWidget(self, viewModel):
        comboBoxWidget = QComboBox(self)
        comboBoxWidget.currentIndexChanged[int].connect(lambda : viewModel.onOptionSelected())
        viewModel.optionsProvider = comboBoxWidget
        return comboBoxWidget

    def _setAnalyzeTab(self):
        layout = QVBoxLayout(self.tabAnalyze)
        layout.setAlignment( qtCore.Qt.AlignTop )
        inputWidget = QWidget( self.tabAnalyze )
        horizontalLayout = QHBoxLayout()
        inputWidget.setLayout( horizontalLayout )
        self.tabAnalyze.setLayout(layout)
        analyzeButton = QPushButton('Graficar')
        analyzeButton.clicked[bool].connect(lambda: self.analyzerViewModel.onAnalyzeClicked())
        includeNoConversionCheckBox = QCheckBox('Incluir precio sin conversion', self.tabAnalyze)
        includeNoConversionCheckBox.setTristate(False)
        useNewGraphCheckBox = QCheckBox('En nuevo grafico', self.tabAnalyze)
        useNewGraphCheckBox.setTristate(False)
        self.analyzerViewModel.includeNoConversionViewModel.checkBox = includeNoConversionCheckBox
        self.analyzerViewModel.newGraphViewModel.checkBox = useNewGraphCheckBox
        horizontalLayout.addWidget(self._makeLineEditWidget(self.analyzerViewModel.fromViewModel, 'Desde'))
        horizontalLayout.addWidget(self._makeLineEditWidget(self.analyzerViewModel.toViewModel, 'Hasta'))
        horizontalLayout.addWidget(self._makeLineEditWidget(self.analyzerViewModel.numberOfPointsViewModel, 'Cantidad Puntos'))
        layout.addWidget(self._makeComboBoxWidget(self.analyzerViewModel.optionsViewModel) )
        layout.addWidget(inputWidget)
        layout.addWidget(includeNoConversionCheckBox)
        layout.addWidget(useNewGraphCheckBox)
        layout.addWidget(analyzeButton)




if __name__ == '__main__':
    convertibleBondViewModel = ConvertibleBondViewModel()
    analyzerViewModel = SensitivityAnalyzerViewModel( convertibleBondViewModel )
    app = QApplication(sys.argv)
    ex = App(convertibleBondViewModel, analyzerViewModel)
    convertibleBondViewModel.update( model_data.chambersPaperRealExampleInput())
    analyzerViewModel.update({'options':['initialStockPrice','irVolatility','recovery','stockVolatility','irStockCorrelation','conversionFactor'], 'from':0.0, 'to':30.0, 'points':10})
    sys.exit(app.exec_())