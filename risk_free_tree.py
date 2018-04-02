from collections import deque

import numpy as np
from scipy.optimize import fsolve

from tree_base import Node, TerminateNode, NodeRoleFactory, BaseBinomialTree


class RateNode(Node):

    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1 ):
        super().__init__()
        self.up             = upperNode
        self.low            = lowerNode
        self.parent         = parent
        self.terminateValue = terminateValue
        self.roleFactory = NodeRoleFactory(self)
        self.solved = False

    def value(self):
        return self.roleFactory.buildRole().value()

    def _valueImplementation(self):
        pass

    def rate(self):
        pass

    def hasChilds(self):
        return True

    def _solveImplementation(self, **kwargs):
        self.solved = True

    def isSolved(self):
        return self.solved

class AbstractRatePriceNode(RateNode):
    def __init__(self,upperNode=None, lowerNode=None, parent=None,terminateValue=1 ):
        super().__init__(upperNode, lowerNode, parent, terminateValue)

    def _valueImplementation(self):
        return 0.5*(self.up.value()*self._discountFactor() + self.low.value()*self._discountFactor())

    def _discountFactor(self):
        return np.exp(-self.rate())

class RatePriceNode(AbstractRatePriceNode):
    def __init__(self,upperNode=None, lowerNode=None, belowNode=None, parent=None, terminateValue=1, deltaTime=1, volatility=0.1 ):
        super().__init__(upperNode, lowerNode, parent, terminateValue)
        self.below = belowNode
        self.deltaTime = deltaTime
        self.volatility = volatility

    def rate(self):
        return self.below.rate()*np.exp(2*self.volatility*np.sqrt(self.deltaTime))

class LowestRatePriceNode(AbstractRatePriceNode):

    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1, fixedRate=1.5 ):
        super().__init__(upperNode, lowerNode, parent, terminateValue)
        self.fixedRate = fixedRate
        self.solved = False

    def rate(self):
        return self.fixedRate

    def _solveImplementation(self, **kwargs):
        firstNode = kwargs['first_node']
        targetPrice = kwargs['target_price']
        def solver_fuc(rateToSolve):
            self.fixedRate = rateToSolve[0]
            return targetPrice - firstNode.value()

        fsolve(solver_fuc, 1.5)
        self.solved = True

class RootTreeNode(LowestRatePriceNode):
    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1, fixedRate=1.5 ):
        super().__init__(upperNode, lowerNode, parent,fixedRate, terminateValue)

class RiskFreeTree(BaseBinomialTree):
    #Ho-Lee log normal model implementation

    def __init__(self, zeroCouponRates, volatility, deltaTime, faceValue):
        super().__init__()
        self.zeroCouponRates = zeroCouponRates
        self.volatility = volatility
        self.deltaTime = deltaTime
        self.faceValue = faceValue

    def _postBuildTree(self):
        self.root.fixedRate = self._firstSpot()

    def ratesByLevel( self ):
        nodesByLevel = self.nodesByLevels(self.root)
        return  [node.rate() for node in nodesByLevel if node.hasChilds()]

    def treeSize(self):
        return len(self.zeroCouponRates)+1

    def _firstSpot(self):
        return self.zeroCouponRates[0]

    def targetValues(self):
        #GF TODO Assuming deltatime is 1; to fix
        return [np.exp(-(i + 1) * self.zeroCouponRates[i]) for i in range(0, len(self.zeroCouponRates))]

    def _solveTree(self, targetValues ):
        nodes = deque(self.nodesByLevels(self.root))
        targetValueIndex=0
        for currentLevel in range(1, self.treeSize()):
            for nodesInLevel in range(currentLevel):
                nodeToSolve = nodes.popleft()
                nodeToSolve.solve(first_node=self.root, target_price=targetValues[targetValueIndex] )
            targetValueIndex += 1

    def ratesOfLevel(self, level):
        return [node.rate() for node in self.nodesOfLevel(level)]

    def _buildLevelNodes(self, currentLevel, totalSize, nextLevelNodes=None):
        #GF TODO Refactor code
        if currentLevel == totalSize:
            newNodes = [TerminateNode(terminateValue= self.faceValue) for i in range(totalSize)]
        elif currentLevel>1:
            newNodes = [LowestRatePriceNode(terminateValue=self.faceValue, fixedRate=1.5)] + [RatePriceNode(terminateValue=self.faceValue, deltaTime=self.deltaTime,volatility=self.volatility) for i in range(currentLevel-1)]
            for i in reversed(range(len(newNodes))):
                currentNode = newNodes[i]
                currentNode.up  = nextLevelNodes[i+1]
                currentNode.up.parent = currentNode
                currentNode.low = nextLevelNodes[i]
                currentNode.low.parent = currentNode
                if i>0:
                    currentNode.below = newNodes[i-1]
        else:
            rootNode = RootTreeNode(upperNode=nextLevelNodes[1], lowerNode=nextLevelNodes[0], terminateValue=self.faceValue)
            rootNode.up.parent = rootNode
            rootNode.low.parent = rootNode
            newNodes=[rootNode]

        return newNodes

def testBackwardsInduction():
    zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
    volatility = 0.1
    deltaTime = 1.0
    faceValue = 1.0

    riskFreeTree = RiskFreeTree( zeroCouponRates, volatility, deltaTime, faceValue)
    riskFreeTree.solve()
    print( riskFreeTree.ratesByLevel() )