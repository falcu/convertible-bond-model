import numpy as np
from models.tree_base import BaseBinomialTree
from models.tree_base import Node, DiscreteModelInput
from copy import copy

class RootStockNode(Node):

    def __init__(self, initialStockPrice=0.0, lowerNode=None, upperNode=None):
        self.initialStockPrice = initialStockPrice
        self.low               = lowerNode
        self.up                = upperNode

    def value(self):
        return self.initialStockPrice

    def isSolved(self):
        return True

    def hasChilds(self):
        return True

class BaseStockNode(Node):

    def __init__(self, parent=None, volatility=0.1, deltaTime =1):
        self.parent = parent
        self.volatility = volatility
        self.deltaTime = deltaTime

    def value(self):
        return self.parent.value()*np.exp(self.volatility*self.deltaTime*self._discountSign())

    def _discountSign(self):
        pass

    def isSolved(self):
        return True


class IntermediateStockNode(BaseStockNode):
    def __init__(self, lowerNode=None, upperNode=None, parent=None, volatility=0.1, deltaTime=1):
        super().__init__(parent, volatility, deltaTime)
        self.low = lowerNode
        self.up  = upperNode

    def hasChilds(self):
        return True

class UpperIntermediateStockNode(IntermediateStockNode):
    def __init__(self, lowerNode=None, upperNode=None, parent=None, volatility=0.1, deltaTime=1):
        super().__init__(lowerNode, upperNode, parent, volatility, deltaTime)

    def _discountSign(self):
        return 1.0

class LowerIntermediateStockNode(IntermediateStockNode):
    def __init__(self, lowerNode=None, upperNode=None, parent=None, volatility=0.1, deltaTime=1):
        super().__init__(lowerNode, upperNode, parent, volatility, deltaTime)

    def _discountSign(self):
        return -1.0

class TerminateStockNode(BaseStockNode):
    def __init__(self, parent=None, volatility=0.1, deltaTime=1):
        super().__init__(parent, volatility, deltaTime)

    def hasChilds(self):
        return False

class TerminateUpperStockNode(TerminateStockNode):
    def __init__(self, parent=None, volatility=0.1, deltaTime=1):
        super().__init__(parent, volatility, deltaTime)

    def _discountSign(self):
        return 1.0


class TerminateLowerStockNode(TerminateStockNode):
    def __init__(self, parent=None, volatility=0.1, deltaTime=1):
        super().__init__(parent, volatility, deltaTime)

    def _discountSign(self):
        return -1.0

class StockTreeModelInput(DiscreteModelInput):
    def __init__(self, initialStockPrice, volatility, deltaTime, time):
        super().__init__(deltaTime, time)
        self._initialStockPrice = initialStockPrice
        self._volatility = volatility

    @staticmethod
    def makeModelInput(initialStockPrice, volatility, deltaTime, time):
        return StockTreeModelInput(initialStockPrice, volatility, deltaTime, time)

    def clone(self):
        return copy(self)

    @property
    def initialStockPrice(self):
        return self._initialStockPrice

    @initialStockPrice.setter
    def initialStockPrice(self, value):
        self._initialStockPrice = value

    @property
    def volatility(self):
        return self._volatility

    @volatility.setter
    def volatility(self, value):
        self._volatility = value

class StockTree(BaseBinomialTree):

    def __init__(self, modelInput):
        super().__init__()
        self.modelInput = modelInput

    def stockPricesByLevel(self):
        nodes = self.nodesByLevels( self.root)
        return [aNode.value() for aNode in nodes]

    def stockPricesOfLevel(self, level):
        return [aNode.value() for aNode in self.nodesOfLevel(level)]

    def _solveTree(self, targetValues ):
        pass

    def targetValues(self):
        pass

    def treeSize(self):
        return self.modelInput.periods + 1

    def _buildLevelNodes(self, currentLevel, totalSize, nextLevelNodes=None):
        #GF TODO Refactor code
        if currentLevel == totalSize:
            newNodes = [TerminateLowerStockNode(volatility=self.modelInput.volatility, deltaTime=self.modelInput.deltaTime)]+[TerminateUpperStockNode(volatility=self.modelInput.volatility, deltaTime=self.modelInput.deltaTime) for i in range(totalSize-1)]
        elif currentLevel>1:
            newNodes = [LowerIntermediateStockNode(volatility=self.modelInput.volatility, deltaTime=self.modelInput.deltaTime)] + [UpperIntermediateStockNode(volatility=self.modelInput.volatility, deltaTime=self.modelInput.deltaTime) for i in range(currentLevel-1)]
            for i in reversed(range(len(newNodes))):
                currentNode = newNodes[i]
                currentNode.up  = nextLevelNodes[i+1]
                currentNode.up.parent = currentNode
                currentNode.low = nextLevelNodes[i]
                if i>0:
                    currentNode.low.parent = newNodes[i-1]
                else:
                    currentNode.low.parent = currentNode
        else:
            rootNode = RootStockNode(initialStockPrice=self.modelInput.initialStockPrice, upperNode=nextLevelNodes[1], lowerNode=nextLevelNodes[0])
            rootNode.up.parent = rootNode
            rootNode.low.parent = rootNode
            newNodes=[rootNode]

        return newNodes

def testStockTree():
    stockTree = StockTree(7, 15.006, 0.353836, 1 )
    stockTree.buildTree()

    return stockTree

