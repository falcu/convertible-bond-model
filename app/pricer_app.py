import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QTabWidget, QLabel, QComboBox, QPushButton, QGridLayout,
    QLineEdit, QApplication, QVBoxLayout, QHBoxLayout, QListWidget, QCheckBox, QScrollBar)

from PyQt5.QtGui import QDoubleValidator
from viewmodels.viewmodels import ConvertibleBondViewModel, SensitivityAnalyzerViewModel
import models.data as model_data
import PyQt5.QtCore as qtCore

class App(QMainWindow):
    def __init__(self, convertibleBondViewModel, analyzerViewModel):
        super().__init__()
        self.title = 'Pricer Bono Convertible - Matematica Financiera'
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

    def updateToChambersInput(self):
        self.convertibleBondViewModel.update(model_data.chambersPaperRealExampleInput())

    def initUI(self):
        self._createTabs()
        self._setPricerTab()
        self._setInputTab()
        self._setAnalyzeTab()

    def _createTabs(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabPricer = QWidget()
        self.tabInput= QWidget()
        self.tabAnalyze = QWidget()
        self.tabs.resize(300, 200)
        self.tabs.addTab(self.tabPricer, "Pricer")
        self.tabs.addTab(self.tabInput, "Input")
        self.tabs.addTab(self.tabAnalyze, "Analizador")
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def _setPricerTab(self):
        childWidgets = [self._makePriceBondWidget(), self._makeImpliedVolatilityWidget()]
        parentWidget = self._makeContainerWidget(QVBoxLayout, childWidgets, alignment=qtCore.Qt.AlignTop, parent=self.tabPricer)
        layout = QGridLayout(self.tabPricer)
        self.tabPricer.setLayout(layout)
        layout.addWidget(parentWidget)

    def _setInputTab(self):
        layout = QGridLayout(self.tabInput)
        self.tabInput.setLayout(layout)

        inputs = [self._updateToChambersInputWidget(),
                  self._makeComboBoxWidget(self.convertibleBondViewModel.bondTypeViewModel),
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

    def _makePriceBondWidget(self ):
        priceBondResultWidget = self._makeLineEditWidget(self.convertibleBondViewModel.bondPriceViewModel, 'Precio Bono:',
                                                   readOnly=True)
        bondPriceButton = QPushButton(text='Valuar')
        bondPriceButton.clicked[bool].connect(lambda: self.convertibleBondViewModel.onPriceBondClicked())

        return self._makeContainerWidget(QHBoxLayout, [priceBondResultWidget,bondPriceButton], alignment=qtCore.Qt.AlignLeft)

    def _makeImpliedVolatilityWidget(self):
        inputMarketPriceWidget = self._makeLineEditWidget(self.convertibleBondViewModel.impliedVolatilityViewodel.marketPriceViewModel,
                               'Precio Mercado:')
        showImpliedVolatilityWidget = self._makeLineEditWidget(self.convertibleBondViewModel.impliedVolatilityViewodel.outputViewModel,
                               'Volatilidad Implicita:', readOnly=True)
        computeImpliedVolatilityButton = QPushButton(text='Calcular')
        computeImpliedVolatilityButton.clicked[bool].connect(lambda: self.convertibleBondViewModel.onImpliedVolatilityClicked())

        return self._makeContainerWidget(QHBoxLayout,
                      [inputMarketPriceWidget,showImpliedVolatilityWidget,computeImpliedVolatilityButton], alignment=qtCore.Qt.AlignLeft)

    def _updateToChambersInputWidget(self):
        updateToChambersInput = QPushButton(text='Chamber Input')
        updateToChambersInput.clicked[bool].connect(
            lambda: self.updateToChambersInput())

        return updateToChambersInput

    def _makeContainerWidget(self, LayoutClass, childWidgets,alignment=None, parent=None, containerWidget=None):
        containerWidget = containerWidget or QWidget( parent or self )
        containerLayout = LayoutClass(containerWidget)
        containerWidget.setLayout(containerLayout)
        if alignment:
            containerLayout.setAlignment(alignment)
        for widget in childWidgets:
            containerLayout.addWidget( widget )

        return containerWidget


    def _makeEditableListWidget(self, viewModel, title='' ):
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
        childWidgets = [listWidget, addItemLabel, addItemLineEdit, addItemButton, removeItemsButton, removeAllItemsButton]
        mainWidget = self._makeContainerWidget(QHBoxLayout, childWidgets)

        return self._makeContainerWidget(QVBoxLayout, [QLabel(text=title), mainWidget])

    def _makeLineEditWidget(self, viewModel, title='', readOnly=False):
        label = QLabel(text=title)
        textLineEdit = QLineEdit(text='')
        textLineEdit.setValidator(QDoubleValidator())
        textLineEdit.setDisabled(readOnly)
        textLineEdit.textChanged.connect( viewModel.onTextChanged )
        viewModel.inputText = textLineEdit

        return self._makeContainerWidget(QHBoxLayout, [label,textLineEdit] )

    def _makeComboBoxWidget(self, viewModel):
        comboBoxWidget = QComboBox(self)
        comboBoxWidget.currentIndexChanged[int].connect(lambda : viewModel.onOptionSelected())
        viewModel.optionsProvider = comboBoxWidget
        return comboBoxWidget

    def _setAnalyzeTab(self):
        analyzeButton = QPushButton('Graficar')
        analyzeButton.clicked[bool].connect(lambda: self.analyzerViewModel.onAnalyzeClicked())
        includeConversionValueCheckBox = QCheckBox('Incluir valor conversion', self.tabAnalyze)
        includeConversionValueCheckBox.setTristate(False)
        useNewGraphCheckBox = QCheckBox('En nuevo grafico', self.tabAnalyze)
        useNewGraphCheckBox.setTristate(False)
        self.analyzerViewModel.includeConversionValueViewModel.checkBox = includeConversionValueCheckBox
        self.analyzerViewModel.newGraphViewModel.checkBox = useNewGraphCheckBox
        inputWidget = self._makeContainerWidget(QHBoxLayout,
                                    [self._makeLineEditWidget(self.analyzerViewModel.fromViewModel, 'Desde'),
                                    self._makeLineEditWidget(self.analyzerViewModel.toViewModel, 'Hasta'),
                                     self._makeLineEditWidget(self.analyzerViewModel.numberOfPointsViewModel,
                                                                  'Cantidad Puntos')          ], parent=self.tabAnalyze)
        analyzeOptionsComboBox = self._makeComboBoxWidget(self.analyzerViewModel.optionsViewModel)
        childWidgets = [analyzeOptionsComboBox, inputWidget, includeConversionValueCheckBox, useNewGraphCheckBox, analyzeButton]

        self._makeContainerWidget(QVBoxLayout,childWidgets,alignment=qtCore.Qt.AlignTop, containerWidget=self.tabAnalyze)

if __name__ == '__main__':
    convertibleBondViewModel = ConvertibleBondViewModel()
    analyzerViewModel = SensitivityAnalyzerViewModel( convertibleBondViewModel )
    app = QApplication(sys.argv)
    ex = App(convertibleBondViewModel, analyzerViewModel)
    ex.pricerWidget.updateToChambersInput()
    analyzerViewModel.update({'options':['stockTreeModelInput.initialStockPrice','riskFreeModelInput.volatility',
                     'defaultTreeModelInput.recovery','stockTreeModelInput.volatility','irStockCorrelation',
                                         'conversionFactor','riskFreeModelInput.rateMovement&defaultTreeModelInput.rateMovement'],
                              'from':0.0, 'to':30.0, 'points':10})
    sys.exit(app.exec_())