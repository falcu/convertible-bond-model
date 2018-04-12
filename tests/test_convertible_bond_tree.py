from tests.test_base import TestBase
import models.convertible_bond_tree as underTest
import models.data as model_data
from parameterized import parameterized

class TestConvertibleBondTree(TestBase):
    def test_priceBond_ChambersPaperRealExample(self):
        modelInput = model_data.chambersPaperRealExampleInput()

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 90.83511, convertibleBondModel.priceBond(), delta=0.0001)

    @parameterized.expand([
                    (-0.15,90.76877), (-0.1, 90.83511), (-0.05, 90.90137),
                    (0, 90.96755), (0.05, 91.03367), (0.10, 91.09971), (0.15, 91.16569)])
    def test_priceBond_ChambersPaperRealExample_WithDifferentCorrelations(self, irStockCorrelation, expectedPrice):
        modelInput = model_data.chambersPaperRealExampleInput(irStockCorrelation=irStockCorrelation)

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( expectedPrice, convertibleBondModel.priceBond(), delta=0.0001)

    def test_priceBond_ChambersPaperSimpleExample(self):
        modelInput = model_data.chambersPaperSimpleExampleInput()

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 93.15353, convertibleBondModel.priceBond(), delta=0.005)

    def test_priceBond_bondPriceConvergesToStockPriceForHighStockPrice(self):
        modelInput = model_data.chambersPaperRealExampleInput(stockPrice=10000000, conversionFactor=1.0)

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 10000000, convertibleBondModel.priceBond(), delta=0.5)

    def test_priceBond_bondPriceConvergesToBondNonConvertiblePriceWhenStockIsLow(self):
        modelInput = model_data.chambersPaperRealExampleInput(stockPrice=5, conversionFactor=2)
        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )
        noConvesionBond = convertibleBondModel.clone()
        noConvesionBond.modelInput.bondType = underTest.ConvertibleBondType.NO_CONVERSION

        self.assertAlmostEqual( noConvesionBond.priceBond(), convertibleBondModel.priceBond(), delta=0.001)

    def test_impliedVolatility_chambersPaper(self):
        modelInput = model_data.chambersPaperRealExampleInput()
        marketPrice = 88.7060
        expectedImpliedVolatiltiy = 0.315995

        convertibleBondModel = underTest.ConvertibleBondTree(modelInput)

        self.assertAlmostEqual( expectedImpliedVolatiltiy, convertibleBondModel.impliedVolatility(marketPrice), delta=0.00001)

    def test_chambersPaperBond_ForcedTypeConvertibleBond(self):
        modelInput = model_data.chambersPaperRealExampleInput( bondType=underTest.ConvertibleBondType.FORCED)

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 76.698661, convertibleBondModel.priceBond(), delta=0.0001)

    def test_chambersPaperBond_CocoTypeConvertibleBond(self):
        modelInput = model_data.chambersPaperRealExampleInput( bondType=underTest.ConvertibleBondType.COCO)

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 46.9815, convertibleBondModel.priceBond(), delta=0.0001)

    def test_chambersPaperBond_cocoBondConvergesToNonConvertiblePriceWhenStockIsHigh(self):
        modelInput = model_data.chambersPaperRealExampleInput( bondType=underTest.ConvertibleBondType.COCO, stockPrice=1000.0)
        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )
        noConvesionBond = convertibleBondModel.clone()
        noConvesionBond.modelInput.bondType = underTest.ConvertibleBondType.NO_CONVERSION

        self.assertAlmostEqual( noConvesionBond.priceBond(), convertibleBondModel.priceBond(), delta=0.0001)

    def test_chambersPaperBond_noConversionOptionBond(self):
        modelInput = model_data.chambersPaperRealExampleInput( bondType=underTest.ConvertibleBondType.NO_CONVERSION )

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual(  66.123511 , convertibleBondModel.priceBond(), delta=0.0001)