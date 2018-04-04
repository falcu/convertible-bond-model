from tests.test_base import TestBase
import models.convertible_bond_tree as underTest
from models.convertible_bond_tree import Feature, FeatureSchedule, ConvertibleBondModelInput

class TestConvertibleBondTree(TestBase):
    def test_priceBond_ChambersPaperRealExample(self):
        modelInput = self.chambersPaperRealExampleInput()

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 90.83511, convertibleBondModel.priceBond(), delta=0.0001)

    def test_priceBond_ChambersPaperSimpleExample(self):
        modelInput = self.chambersPaperSimpleExampleInput()

        convertibleBondModel = underTest.ConvertibleBondTree( modelInput )

        self.assertAlmostEqual( 93.15353, convertibleBondModel.priceBond(), delta=0.005)

    def chambersPaperRealExampleInput(self):
        zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
        irVolatility = 0.1
        deltaTime = 1.0
        faceValue = 100.0
        riskyZeroCoupons = [0.0611, 0.0646, 0.0663, 0.0678, 0.0683, 0.06894]
        recovery = 0.32
        initialStockPrice = 15.006
        stockVolatility = 0.353836
        irStockCorrelation = -0.1
        conversionFactor = 5.07524
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