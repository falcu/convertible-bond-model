from models.risk_free_tree import RiskFreeTree
from models.default_tree import DefaultTree
from models.stock_tree import  StockTree
from models.tree_base import BaseTree, Node
import numpy as np
from abc import abstractmethod
from collections import deque

class NodeId:
    def __init__(self, level, index):
        self.level = level
        self.index = index

class BaseNode(Node):
    def __init__(self, modelInput, stockPrice=0 ):
        self.modelInput = modelInput
        self._stockPrice = stockPrice

    def stockPrice(self):
        return self._stockPrice

    def isSolved(self):
        return True

    def _conversionValue(self):
        return self.modelInput.conversionFactor * self.stockPrice()

    def _bondFaceValue(self):
        return self.modelInput.faceValue

class PathProbabilityProviderIntermediate:

    def __init__(self, node):
        self.node = node

    def pathsProbabilities(self):
        pathProbs =[]
        p = self.node._pProbability()
        defaultProbability = self.node._lambdaProbability()
        modelInput = self.node.modelInput
        pathProbs.append(0.5*(1.0- p + (np.sqrt(p*(1.0-p))*modelInput.irStockCorrelation))*(1-defaultProbability))
        pathProbs.append(0.5*(1.0- p -  (np.sqrt(p*(1.0-p))*modelInput.irStockCorrelation))*(1-defaultProbability))
        pathProbs.append(0.5*(p -  (np.sqrt(p*(1.0-p))*modelInput.irStockCorrelation))*(1-defaultProbability))
        pathProbs.append(0.5*(p +  (np.sqrt(p*(1-p))*modelInput.irStockCorrelation))*(1-defaultProbability))
        pathProbs.append(defaultProbability)

        return pathProbs

class PathProbabilityProviderTerminate:

    def __init__(self, node):
        self.node = node

    def pathsProbabilities(self):
        pathProbs =[]
        p = self.node._pProbability()
        defaultProbability = self.node._lambdaProbability()
        pathProbs.append((1.0-defaultProbability)*(1.0-p))
        pathProbs.append((1.0-defaultProbability)*p)
        pathProbs.append(defaultProbability)

        return pathProbs

class TerminateNonDefaultNode(BaseNode):
    def __init__(self, modelInput, stockPrice=0):
        super().__init__(modelInput,stockPrice)

    def value(self):
        return np.max([self._conversionValue(), self._bondFaceValue()])

    def hasChilds(self):
        return False

class DefaultNode(BaseNode):
    def __init__(self, modelInput, ):
        super().__init__(modelInput, 0.0)

    def hasChilds(self):
        return False

    def value(self):
        return self.modelInput.faceValue * self.modelInput.recovery

class IntermediateNode(BaseNode):
    def __init__(self, modelInput, defaultProbability=None, rate=0, stockPrice=0, children=None, feature=None, pathProbProvider=None, nodeId=None ):
        super().__init__(modelInput, stockPrice)
        self.defaultProbability = defaultProbability
        self._rate = rate
        self.children = children or []
        self.feature = feature or NullFeature()
        self.pathProbProvider = pathProbProvider or PathProbabilityProviderIntermediate(self)
        self.nodeId = nodeId

    def _pProbability(self):
        return ((self._composeFactor()/(1.0-self._lambdaProbability())) - self._dFactor()) / (self._uFactor() - self._dFactor())

    def _lambdaProbability(self):
        return self.defaultProbability

    def _uFactor(self):
        return np.exp(self.modelInput.stockVolatility* np.sqrt(self.modelInput.deltaTime))

    def _dFactor(self):
        return 1.0/self._uFactor()

    def _composeFactor(self):
        return np.exp( self.rate()*self.modelInput.deltaTime)

    def rate(self):
        return self._rate

    def value(self):
        return np.max([np.min([self._rollBackValue(),self.feature.callValue()]), self._conversionValue(),
                      self.feature.putValue()])

    def hasChilds(self):
        return True

    def addChild(self, aChild):
        self.children.append( aChild )

    def _rollBackValue(self):
        nodesValues = list(map( lambda aNode: aNode.value(), self.children))
        expectedValue = np.dot(self.pathProbProvider.pathsProbabilities(), nodesValues )

        return expectedValue*self._discountFactor()

    def _discountFactor(self):
        return np.exp(-self.rate()*self.modelInput.deltaTime)

class Feature:
    def __init__(self,callValue=np.inf, putValue=0.0):
        self._callValue = callValue
        self._putValue = putValue

    def callValue(self):
        return self._callValue

    def putValue(self):
        return self._putValue

class FeatureSchedule:
    def __init__(self):
        self.features = {}

    def addFeature(self, period, callValue=np.inf, putValue=0.0):
        self.features.update( {period : Feature(callValue, putValue)})

    def addFeatures(self, features):
        self.features = features

    def feature(self, period):
        return self.features.get(period, NullFeature())

class NullFeature(Feature):
    def __init__(self):
        super().__init__(np.inf, 0.0)

class ConvertibleBondModelInput:
    def __init__(self, zeroCouponRates, irVolatility, deltaTime, faceValue, riskyZeroCoupons, recovery,
                 initialStockPrice, stockVolatility, irStockCorrelation, conversionFactor, featureSchedule, time):
        self.zeroCouponRates = zeroCouponRates
        self.irVolatility = irVolatility
        self.deltaTime = deltaTime
        self.faceValue = faceValue
        self.riskyZeroCoupons = riskyZeroCoupons
        self.recovery = recovery
        self.initialStockPrice = initialStockPrice
        self.stockVolatility = stockVolatility
        self.irStockCorrelation = irStockCorrelation
        self.conversionFactor = conversionFactor
        self.featureSchedule = featureSchedule
        self.time = time
        self.treeLevels = int(time+1/deltaTime)

class ConvertibleBondTree(BaseTree):
    def __init__(self, modelInput):
        super().__init__()
        self.modelInput = modelInput
        self.freeRiskIRTree = RiskFreeTree( modelInput.zeroCouponRates, modelInput.irVolatility, modelInput.deltaTime,
                                            modelInput.faceValue)
        self.defaultTree = DefaultTree( modelInput.zeroCouponRates, modelInput.irVolatility, modelInput.deltaTime,
                                            modelInput.faceValue, modelInput.riskyZeroCoupons, modelInput.recovery, self.freeRiskIRTree )
        self.stockTree = StockTree(modelInput.treeLevels, modelInput.initialStockPrice, modelInput.stockVolatility, modelInput.deltaTime)

    def priceBond(self):
        return self.solve()

    def treeSize(self):
        return self.modelInput.treeLevels

    def _solveTree(self, targetValues ):
        return self.root.value()

    def targetValues(self):
        pass

    def _preBuildTree(self):
        self.freeRiskIRTree.solve()
        self.defaultTree.solve()
        self.stockTree.solve()

    def _terminateNodesCount(self):
        #In a two-factor tree with recombination there are (n+1)^2 nodes per level
        return int(np.power((self.treeSize()-1),2) *2 )

    def _buildTerminalNodes(self):
        terminalNodes = []
        stockPrices = self._terminalStockPrices()
        for i in range(0, self._terminateNodesCount(), 2):
            terminalNodes.append(TerminateNonDefaultNode( modelInput=self.modelInput, stockPrice=stockPrices.popleft()))
            terminalNodes.append(TerminateNonDefaultNode( modelInput=self.modelInput, stockPrice=stockPrices.popleft()))

        return terminalNodes

    def _terminalStockPrices(self):
        stockPrices = self.stockTree.stockPricesOfLevel( self.treeSize() )
        combiniationTimes = self.treeSize() - 1
        result = []
        for i in range(0, len(stockPrices)-1):
            result+=([stockPrices[i], stockPrices[i+1]]*combiniationTimes)

        return deque(result)

    def _getFeature(self, currentLevel):
        return self.modelInput.featureSchedule.feature( currentLevel - 1)

    def _buildIntermediateNodes(self, currentLevel, totalSize, nextLevelNodes=None):
        defaultProbability     =  self.defaultTree.defaultProbabilityOfLevel( currentLevel )
        stockRatesPairs        = deque(self._buildStockRatesPairs(currentLevel))
        intermediateNodesCount = int(np.power( currentLevel, 2 ))
        intermediateNodes = []
        feature = self._getFeature(currentLevel)

        for i in range(0,intermediateNodesCount):
            stockRate=stockRatesPairs.popleft()
            nodeId = NodeId( currentLevel, i+1)
            intermediateNodes.append(IntermediateNode(modelInput=self.modelInput,
                                                                         defaultProbability=defaultProbability,
                                                                         rate=stockRate[1], stockPrice=stockRate[0], nodeId=nodeId, feature=feature) )
            pathProbProvider = PathProbabilityProviderIntermediate(intermediateNodes[i]) if currentLevel+1<totalSize else PathProbabilityProviderTerminate(intermediateNodes[i])
            intermediateNodes[i].pathProbProvider = pathProbProvider


        if currentLevel+1<totalSize: #Children are not terminal
            for aNode in intermediateNodes:
                childrenIds = self._getNodeChildrenIds( aNode )
                aNode.children = [nextLevelNodes[j] for j in childrenIds]
                aNode.addChild( DefaultNode(self.modelInput) )

        else:
            terminateNodesIndex = 0
            for i in range(0, len(intermediateNodes)):
                childrenNodes = [ nextLevelNodes[terminateNodesIndex], nextLevelNodes[terminateNodesIndex+1] ]
                intermediateNodes[i].children = childrenNodes
                intermediateNodes[i].addChild( DefaultNode(self.modelInput) )
                terminateNodesIndex+=2

        return intermediateNodes

    def _getNodeChildrenIds(self, node):
        i = node.nodeId.index
        lvl = node.nodeId.level
        bucket = int(np.floor( (i - 1) / lvl ))

        return [i+bucket-1, i+bucket, i+bucket+lvl, i+bucket+1+lvl]



    def _buildStockRatesPairs(self, currentLevel):
        #GF TODO Refactor code
        stockPrices = self.stockTree.stockPricesOfLevel(currentLevel)
        rates       = self.freeRiskIRTree.ratesOfLevel(currentLevel)
        stockRatesPairs = []
        for i in range(len(stockPrices)):
            for j in range(len(rates)):
                stockRatesPairs.append( (stockPrices[i], rates[j]) )

        return stockRatesPairs

    def _buildRootNode(self, nextLevelNodes=None):
        defaultProbability = self.defaultTree.defaultProbabilityOfLevel(1)
        initialRate = self.freeRiskIRTree.ratesOfLevel(1)[0]
        initialStockPrice = self.stockTree.stockPricesOfLevel(1)[0]
        rootNode = IntermediateNode(modelInput=self.modelInput, defaultProbability=defaultProbability, rate=initialRate,
                            stockPrice=initialStockPrice, nodeId=NodeId(1,1))
        for aNode in nextLevelNodes:
            rootNode.addChild(aNode)
        rootNode.addChild(DefaultNode(self.modelInput))

        return rootNode

    def _buildLevelNodes(self, currentLevel, totalSize, nextLevelNodes=None):
        #GF TODO Refactor code
        if currentLevel == totalSize:
            newNodes = self._buildTerminalNodes()
        elif currentLevel>1:
            newNodes = self._buildIntermediateNodes( currentLevel, totalSize, nextLevelNodes)
        else:
            newNodes=[self._buildRootNode(nextLevelNodes)]

        return newNodes


def testConvertibleBond(correlation=-0.1, stockPrice=15.006, conversionFactor=5.07524):
    zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
    irVolatility = 0.1
    deltaTime = 1.0
    faceValue = 100.0
    riskyZeroCoupons = [0.0611, 0.0646, 0.0663, 0.0678, 0.0683, 0.06894]
    recovery = 0.32
    initialStockPrice = stockPrice
    stockVolatility = 0.353836
    irStockCorrelation = correlation
    conversionFactor = conversionFactor
    time = 6
    featureSchedule = FeatureSchedule()
    featureSchedule.addFeatures({3:Feature(callValue=94.205), 4:Feature(callValue=96.098), 5:Feature(callValue=98.030)})

    modelInput = ConvertibleBondModelInput(zeroCouponRates, irVolatility, deltaTime, faceValue, riskyZeroCoupons, recovery,
                 initialStockPrice, stockVolatility, irStockCorrelation, conversionFactor, featureSchedule, time)

    model = ConvertibleBondTree( modelInput )
    return model.priceBond()
