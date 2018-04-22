from collections import deque
import numpy as np
from scipy.optimize import fsolve
from models.tree_base import Node, TerminateNode, NodeRoleFactory, BaseBinomialTree, DiscreteModelInput
from copy import copy


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
            result = targetPrice - firstNode.value()
            result = result if self.fixedRate >=0 else 1000.0

            return result

        fsolve(solver_fuc, [1.0], xtol=1.5e-10, maxfev=1000000)
        self.solved = True

class RootTreeNode(LowestRatePriceNode):
    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1, fixedRate=1.5 ):
        super().__init__(upperNode, lowerNode, parent,fixedRate, terminateValue)

class RiskFreeModelInput(DiscreteModelInput):
    def __init__(self, zeroCouponRates, volatility, faceValue, deltaTime, time, rateMovement=0.0):
        super().__init__( deltaTime, time)
        self._zeroCouponRates = zeroCouponRates
        self._volatility      = volatility
        self._faceValue = faceValue
        self._rateMovement = rateMovement

    @staticmethod
    def makeModelInput(zeroCouponRates, volatility, faceValue, deltaTime, time, rateMovement=0.0):
        return RiskFreeModelInput(zeroCouponRates, volatility, faceValue, deltaTime, time,rateMovement=rateMovement)

    def clone(self):
        return copy(self)

    @property
    def zeroCouponRates(self):
        rateMov = self.rateMovement / 10000.0
        return [rate+rateMov for rate in  self._zeroCouponRates]

    @zeroCouponRates.setter
    def zeroCouponRates(self, value):
        self._zeroCouponRates = value

    @property
    def volatility(self):
        return self._volatility

    @volatility.setter
    def volatility(self, value):
        self._volatility = value

    @property
    def faceValue (self):
        return self._faceValue

    @faceValue.setter
    def faceValue (self, value):
        self._faceValue = value

    @property
    def rateMovement (self):
        return self._rateMovement

    @rateMovement.setter
    def rateMovement (self, value):
        self._rateMovement = value

class RiskFreeTree(BaseBinomialTree):
    #Ho-Lee log normal model implementation

    def __init__(self, modelInput):
        super().__init__()
        self.modelInput = modelInput

    def _postBuildTree(self):
        self.root.fixedRate = self._firstSpot()

    def ratesByLevel( self ):
        nodesByLevel = self.nodesByLevels(self.root)
        return  [node.rate() for node in nodesByLevel if node.hasChilds()]

    def treeSize(self):
        return self.modelInput.periods + 1

    def _firstSpot(self):
        return self.modelInput.zeroCouponRates[0]

    def targetValues(self):
        #GF TODO Assuming deltatime is 1; to fix
        return [np.exp(-(i + 1) * self.modelInput.zeroCouponRates[i])*self.modelInput.faceValue for i in range(0, len(self.modelInput.zeroCouponRates))]

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
            newNodes = [TerminateNode(terminateValue= self.modelInput.faceValue) for i in range(totalSize)]
        elif currentLevel>1:
            newNodes = [LowestRatePriceNode(terminateValue=self.modelInput.faceValue, fixedRate=1.5)] + [RatePriceNode(terminateValue=self.modelInput.faceValue,
                                                                                                                       deltaTime=self.modelInput.deltaTime,volatility=self.modelInput.volatility) for i in range(currentLevel-1)]
            for i in reversed(range(len(newNodes))):
                currentNode = newNodes[i]
                currentNode.up  = nextLevelNodes[i+1]
                currentNode.up.parent = currentNode
                currentNode.low = nextLevelNodes[i]
                currentNode.low.parent = currentNode
                if i>0:
                    currentNode.below = newNodes[i-1]
        else:
            rootNode = RootTreeNode(upperNode=nextLevelNodes[1], lowerNode=nextLevelNodes[0],
                                    terminateValue=self.modelInput.faceValue)
            rootNode.up.parent = rootNode
            rootNode.low.parent = rootNode
            newNodes=[rootNode]

        return newNodes