from tests.test_base import TestBase
import models.convertible_bond_tree as underTest
from models.convertible_bond_tree import Feature, FeatureSchedule, ConvertibleBondModelInput
from parameterized import parameterized

class TestConvertibleBondTree(TestBase):
    def test_priceBond_ChambersPaperRealExample(self):
        modelInput = self.chambersPaperRealExampleInput()

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 90.83511, convertibleBondModel.priceBond(), delta=0.0001)

    @parameterized.expand([
                    (-0.15,90.76877), (-0.1, 90.83511), (-0.05, 90.90137),
                    (0, 90.96755), (0.05, 91.03367), (0.10, 91.09971), (0.15, 91.16569)])
    def test_priceBond_ChambersPaperRealExample_WithDifferentCorrelations(self, irStockCorrelation, expectedPrice):
        modelInput = self.chambersPaperRealExampleInput(irStockCorrelation=irStockCorrelation)

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( expectedPrice, convertibleBondModel.priceBond(), delta=0.0001)

    def test_priceBond_ChambersPaperSimpleExample(self):
        modelInput = self.chambersPaperSimpleExampleInput()

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 93.15353, convertibleBondModel.priceBond(), delta=0.005)

    def test_priceBond_bondPriceConvergesToStockPriceForHighStockPrice(self):
        modelInput = self.chambersPaperRealExampleInput(stockPrice=10000000, conversionFactor=1.0)

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 10000000, convertibleBondModel.priceBond(), delta=0.5)

    def test_priceBond_bondPriceConvergesToBondNonConvertiblePriceWhenStockIsLow(self):
        modelInputNonConvertible = self.chambersPaperRealExampleInput(stockPrice=1, conversionFactor=0)
        modelInput = self.chambersPaperRealExampleInput(stockPrice=5, conversionFactor=2)
        nonConvertiblePrice = underTest.ConvertibleBondTree( modelInputNonConvertible ).priceBond()

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( nonConvertiblePrice, convertibleBondModel.priceBond(), delta=0.001)

    def test_impliedVolatility_chambersPaper(self):
        modelInput = self.chambersPaperRealExampleInput()
        marketPrice = 88.7060
        expectedImpliedVolatiltiy = 0.315995

        convertibleBondModel = underTest.ConvertibleBondTree(modelInput)

        self.assertAlmostEqual( expectedImpliedVolatiltiy, convertibleBondModel.impliedVolatility(marketPrice), delta=0.00001)

    def chambersPaperRealExampleInput(self, irStockCorrelation=-0.1, stockPrice=15.006, conversionFactor=5.07524):
        zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
        irVolatility = 0.1
        deltaTime = 1.0
        faceValue = 100.0
        riskyZeroCoupons = [0.0611, 0.0646, 0.0663, 0.0678, 0.0683, 0.06894]
        recovery = 0.32
        initialStockPrice = stockPrice
        stockVolatility = 0.353836
        irStockCorrelation = irStockCorrelation
        conversionFactor = conversionFactor
        time = 6
        featureSchedule = FeatureSchedule()
        featureSchedule.addFeatures(
            {3: Feature(callValue=94.205), 4: Feature(callValue=96.098), 5: Feature(callValue=98.030)})

        return ConvertibleBondModelInput(zeroCouponRates, irVolatility, deltaTime, faceValue, riskyZeroCoupons,
                                               recovery,
                                               initialStockPrice, stockVolatility, irStockCorrelation, conversionFactor,
                                               featureSchedule, time)


    def chambersPaperSimpleExampleInput(self):
        zeroCouponRates = [0.1, 0.1, 0.1]
        irVolatility = 0.1
        deltaTime = 1.0
        faceValue = 100.0
        riskyZeroCoupons = [0.15, 0.15, 0.15]
        recovery = 0.32
        initialStockPrice = 30.0
        stockVolatility = 0.23
        irStockCorrelation = -0.1
        conversionFactor = 3.0
        time = 3
        featureSchedule = FeatureSchedule()
        featureSchedule.addFeatures({ 1: Feature(callValue=105.0),2: Feature(callValue=105.0), 3: Feature(callValue=105.0) } )

        return ConvertibleBondModelInput(zeroCouponRates, irVolatility, deltaTime, faceValue, riskyZeroCoupons,
                                               recovery,
                                               initialStockPrice, stockVolatility, irStockCorrelation, conversionFactor,
                                               featureSchedule, time)