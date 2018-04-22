from models.risk_free_tree import RiskFreeTree
from models.default_tree import DefaultTree
from models.stock_tree import  StockTree
from models.tree_base import BaseTree, Node, DiscreteModelInput
import numpy as np
from collections import deque
from copy import copy
from scipy.optimize import fsolve
from abc import ABC, abstractmethod
from enum import Enum, auto

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

    def conversionValue(self):
        return self.modelInput.conversionFactor * self.stockPrice()

    def bondFaceValue(self):
        return self.modelInput.riskFreeModelInput.faceValue

    def valueProviderFactory(self):
        return NullValueProviderFactory( self )

    def value(self):
        return self.valueProviderFactory().makeProvider().value()


class NodeValueProvider(ABC):
    def __init__(self, node):
        self.node = node

    @abstractmethod
    def value(self):
        pass

class NullProvider( NodeValueProvider ):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return self.node.value()

class NodeValueProviderFactory(ABC):
    def __init__(self, node):
        self.node = node

    @abstractmethod
    def makeProvider(self):
        pass

class NullValueProviderFactory(NodeValueProviderFactory):
    def __init__(self, node):
        super().__init__(node)

    def makeProvider(self):
        return NullProvider( self.node )

class PathProbabilityProvider(ABC):
    def __init__(self, node):
        self.node = node

    @abstractmethod
    def pathsProbabilities(self):
        pass

class PathProbabilityProviderIntermediate(PathProbabilityProvider):

    def __init__(self, node):
        super().__init__(node)

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

class PathProbabilityProviderTerminate(PathProbabilityProvider):

    def __init__(self, node):
        super().__init__(node)

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

    def valueProviderFactory(self):
        return TerminateNonDefaultValueFactory(self)

    def hasChilds(self):
        return False

class TerminateNonDefaultValueClassicProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return np.max([self.node.conversionValue(), self.node.bondFaceValue()])

class TerminateNonDefaultValueForcedProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return self.node.conversionValue()

class TerminateNonDefaultValueCoCoProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return np.min([self.node.conversionValue(), self.node.bondFaceValue()])

class TerminateNonDefaultValueNoConversionProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return self.node.bondFaceValue()

class TerminateNonDefaultValueFactory(NodeValueProviderFactory):
    def __init__(self, node):
        super().__init__( node )

    def makeProvider(self):
        if self.node.modelInput.bondType == ConvertibleBondType.CLASSIC:
            return TerminateNonDefaultValueClassicProvider( self.node )
        elif self.node.modelInput.bondType == ConvertibleBondType.FORCED:
            return TerminateNonDefaultValueForcedProvider(self.node)
        elif self.node.modelInput.bondType == ConvertibleBondType.COCO:
            return TerminateNonDefaultValueCoCoProvider(self.node)
        elif self.node.modelInput.bondType == ConvertibleBondType.NO_CONVERSION:
            return TerminateNonDefaultValueNoConversionProvider(self.node)

class DefaultNode(BaseNode):
    def __init__(self, modelInput, ):
        super().__init__(modelInput, 0.0)

    def hasChilds(self):
        return False

    def valueProviderFactory(self):
        return DefaultNodeValueFactory(self)

class DefaultNodeValueClassicProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return self.node.modelInput.riskFreeModelInput.faceValue * self.node.modelInput.defaultTreeModelInput.recovery

class DefaultNodeValueFactory(NodeValueProviderFactory):
    def __init__(self, node):
        super().__init__( node )

    def makeProvider(self):
        return DefaultNodeValueClassicProvider( self.node )

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
        return np.exp(self.modelInput.stockTreeModelInput.volatility* np.sqrt(self.modelInput.deltaTime))

    def _dFactor(self):
        return 1.0/self._uFactor()

    def _composeFactor(self):
        return np.exp( self.rate()*self.modelInput.deltaTime)

    def rate(self):
        return self._rate

    def valueProviderFactory(self):
        return IntermediateNodeValueFactory(self)

    def hasChilds(self):
        return True

    def addChild(self, aChild):
        self.children.append( aChild )

    def rollBackValue(self):
        nodesValues = list(map( lambda aNode: aNode.value(), self.children))
        expectedValue = np.dot(self.pathProbProvider.pathsProbabilities(), nodesValues )

        return expectedValue*self._discountFactor()

    def _discountFactor(self):
        return np.exp(-self.rate()*self.modelInput.deltaTime)

class IntermediateNodeClassicProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return np.max([np.min([self.node.rollBackValue(),self.node.feature.callValue()]), self.node.conversionValue(),
                      self.node.feature.putValue()])

class IntermediateNodeCocoProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return np.max([np.min([self.node.rollBackValue(),self.node.feature.callValue(), self.node.conversionValue()]),
                      self.node.feature.putValue()])

class IntermediateNodeNoConversionProvider(NodeValueProvider):
    def __init__(self, node):
        super().__init__( node )

    def value(self):
        return np.max([np.min([self.node.rollBackValue(),self.node.feature.callValue()]),
                      self.node.feature.putValue()])

class IntermediateNodeValueFactory(NodeValueProviderFactory):
    def __init__(self, node):
        super().__init__( node )

    def makeProvider(self):
        if self.node.modelInput.bondType == ConvertibleBondType.CLASSIC or self.node.modelInput.bondType == ConvertibleBondType.FORCED:
            return IntermediateNodeClassicProvider( self.node )
        elif self.node.modelInput.bondType == ConvertibleBondType.COCO:
            return IntermediateNodeCocoProvider(self.node)
        elif self.node.modelInput.bondType == ConvertibleBondType.NO_CONVERSION:
            return IntermediateNodeNoConversionProvider(self.node)
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

class ConvertibleBondType(Enum):
    CLASSIC         = auto()
    FORCED          = auto()
    COCO            = auto()
    NO_CONVERSION   = auto()

class ConvertibleBondModelInput(DiscreteModelInput):
    # Chambers and Lu Convertible Bond model implementation

    def __init__(self, riskFreeModelInput, defaultTreeModelInput, stockTreeModelInput, irStockCorrelation,
                 conversionFactor, featureSchedule, deltaTime, time, bondType=ConvertibleBondType.CLASSIC):
        super().__init__( deltaTime, time)
        self.riskFreeModelInput = riskFreeModelInput
        self.defaultTreeModelInput = defaultTreeModelInput
        self.stockTreeModelInput = stockTreeModelInput
        self.irStockCorrelation = irStockCorrelation
        self.conversionFactor = conversionFactor
        self.featureSchedule = featureSchedule
        self.bondType = bondType

    @staticmethod
    def makeModelInput(riskFreeModelInput, defaultTreeModelInput, stockTreeModelInput, irStockCorrelation,
                 conversionFactor, featureSchedule, deltaTime, time, bondType=ConvertibleBondType.CLASSIC):
        return ConvertibleBondModelInput(riskFreeModelInput, defaultTreeModelInput, stockTreeModelInput, irStockCorrelation,
                 conversionFactor, featureSchedule, deltaTime, time, bondType=bondType)

    def clone(self):
        return ConvertibleBondModelInput.makeModelInput(self.riskFreeModelInput.clone(), self.defaultTreeModelInput.clone(),
                                                        self.stockTreeModelInput.clone(), self.irStockCorrelation,
                                                        self.conversionFactor, self.featureSchedule, self.deltaTime,
                                                        self.time, bondType=self.bondType)

class ConvertibleBondTree(BaseTree):
    def __init__(self, modelInput):
        super().__init__()
        self.modelInput = modelInput
        self.freeRiskIRTree = None
        self.defaultTree = None
        self.stockTree = None

    def priceBond(self):
        return self.solve()

    def conversionValue(self):
        self.solve()
        return self.root.conversionValue()

    def clone(self):
        modelInputClone = copy(self.modelInput)
        return ConvertibleBondTree( modelInputClone )

    def impliedVolatility(self, marketPrice):
        modelInputClone = self.modelInput.clone()
        newModel = ConvertibleBondTree( modelInputClone )

        def solver_fuc(impliedVolatility):
            modelInputClone.stockTreeModelInput.volatility = impliedVolatility[0]
            result = marketPrice - newModel.priceBond()
            result = result if modelInputClone.stockTreeModelInput.volatility >=0 else 1000.0
            return result

        fsolve(solver_fuc, 1.5, xtol=1.5e-10, maxfev=1000000)

        return modelInputClone.stockTreeModelInput.volatility

    def treeSize(self):
        return self.modelInput.periods + 1

    def _solveTree(self, targetValues ):
        return self.root.value()

    def targetValues(self):
        pass

    def _preBuildTree(self):
        self._buildHelperTrees()
        self.freeRiskIRTree.solve()
        self.defaultTree.solve()
        self.stockTree.solve()

    def _buildHelperTrees(self):
        self.freeRiskIRTree = RiskFreeTree( self.modelInput.riskFreeModelInput)
        self.defaultTree = DefaultTree( self.modelInput.defaultTreeModelInput)
        self.stockTree = StockTree(self.modelInput.stockTreeModelInput)

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
