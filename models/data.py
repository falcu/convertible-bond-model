from models.convertible_bond_tree import Feature, FeatureSchedule, ConvertibleBondModelInput, ConvertibleBondType
from models.risk_free_tree import RiskFreeModelInput
from models.default_tree import DefaultTreeModelInput
from models.stock_tree import StockTreeModelInput


def chambersPaperRealExampleRiskFreeInput( faceValue = 100.0 ):
    zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
    volatility = 0.1
    deltaTime = 1.0
    t = 6
    return RiskFreeModelInput.makeModelInput(zeroCouponRates, volatility, faceValue, deltaTime, t)

def chambersPaperRealExampleDefaultTreeInput( faceValue = 100.0 ):
    riskfreeInput = chambersPaperRealExampleRiskFreeInput(faceValue)
    riskyZeroCoupons = [0.0611, 0.0646, 0.0663, 0.0678, 0.0683, 0.06894]
    recovery = 0.32
    deltaTime = 1.0
    t = 6
    return DefaultTreeModelInput.makeModelInput(riskfreeInput, riskyZeroCoupons, recovery, deltaTime, t)

def chambersPaperRealExampleStockTreeInput(stockPrice=15.006):
    volatility = 0.353836
    deltaTime = 1
    time = 6

    return StockTreeModelInput.makeModelInput(stockPrice, volatility, deltaTime, time)

def chambersPaperRealExampleInput( irStockCorrelation=-0.1, stockPrice=15.006, conversionFactor=5.07524,
                                   bondType=ConvertibleBondType.CLASSIC):
    riskFreeRateModelInput = chambersPaperRealExampleRiskFreeInput()
    defaultModelInput = chambersPaperRealExampleDefaultTreeInput()
    stockModelInput = chambersPaperRealExampleStockTreeInput(stockPrice=stockPrice)
    irStockCorrelation = irStockCorrelation
    conversionFactor = conversionFactor
    deltaTime = 1.0
    time = 6
    featureSchedule = FeatureSchedule()
    featureSchedule.addFeatures(
        {3: Feature(callValue=94.205), 4: Feature(callValue=96.098), 5: Feature(callValue=98.030)})

    return ConvertibleBondModelInput.makeModelInput(riskFreeRateModelInput, defaultModelInput, stockModelInput,
                                                    irStockCorrelation, conversionFactor, featureSchedule, deltaTime, time, bondType=bondType)

def chambersPaperSimpleExampleRiskFreeInput( faceValue=100.0 ):
    zeroCouponRates = [0.1, 0.1, 0.1]
    volatility = 0.1
    deltaTime = 1.0
    t = 3
    return RiskFreeModelInput.makeModelInput(zeroCouponRates, volatility, faceValue, deltaTime, t)

def chambersPaperSimpleExampleDefaultTreeInput( faceValue=100.0 ):
    riskFreeInput = chambersPaperSimpleExampleRiskFreeInput()
    riskyZeroCoupons = [0.15, 0.15, 0.15]
    recovery = 0.32
    deltaTime = 1.0
    t = 3
    return DefaultTreeModelInput.makeModelInput(riskFreeInput, riskyZeroCoupons, recovery, deltaTime, t)

def chambersPaperSimpleExampleStockTreeInput(  ):
    stockPrice = 30.0
    stockVolatility = 0.23
    deltaTime = 1.0
    t = 3
    return StockTreeModelInput.makeModelInput(stockPrice, stockVolatility, deltaTime, t)


def chambersPaperSimpleExampleInput():

    riskFreeModelInput = chambersPaperSimpleExampleRiskFreeInput()
    defaultModelInput = chambersPaperSimpleExampleDefaultTreeInput()
    stockModelInput = chambersPaperSimpleExampleStockTreeInput()
    irStockCorrelation = -0.1
    conversionFactor = 3.0
    featureSchedule = FeatureSchedule()
    featureSchedule.addFeatures({ 1: Feature(callValue=105.0),2: Feature(callValue=105.0), 3: Feature(callValue=105.0) } )
    deltaTime = 1.0
    t = 3

    return ConvertibleBondModelInput(riskFreeModelInput, defaultModelInput, stockModelInput, irStockCorrelation,
                                     conversionFactor, featureSchedule, deltaTime, t)