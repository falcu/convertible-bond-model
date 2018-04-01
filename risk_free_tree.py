import numpy as np
from scipy.optimize import fsolve
from collections import deque
from tree_base import Node, TerminateNode, TerminateNodeRole, IntermediateNodeRole

class RateNode(Node):

    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1 ):
        super().__init__()
        self.up             = upperNode
        self.low            = lowerNode
        self.parent         = parent
        self.terminateValue = terminateValue
        self.roleFactory = NodeRoleFactory(self)

    def value(self):
        return self.roleFactory.buildRole().value()

    def _valueImplementation(self):
        pass

    def rate(self):
        pass

    def hasChilds(self):
        return True

class NodeRoleFactory:

    def __init__(self,node):
        self.node = node

    def buildRole(self):
        if not self.node.hasChilds():
            return TerminateNodeRole(self.node._valueImplementation())
        elif not self.node.parent:
            return IntermediateNodeRole(self.node)
        elif self.node.parent and not self.node.parent.isSolved():
            return TerminateNodeRole( self.node.terminateValue )
        else:
            return IntermediateNodeRole(self.node)

class AbstractRatePriceNode(RateNode):
    def __init__(self,upperNode=None, lowerNode=None, parent=None,terminateValue=1 ):
        super().__init__(upperNode, lowerNode, parent, terminateValue)
        self.solved = False

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

    def rate(self):
        return self.fixedRate

    def _solveImplementation(self, **kwargs):
        firstNode = kwargs['first_node']
        targetPrice = kwargs['target_price']
        def solver_fuc(rateToSolve):
            self.fixedRate = rateToSolve[0]
            return targetPrice - firstNode.value()

        fsolve(solver_fuc, 1.5)

class RootTreeNode(LowestRatePriceNode):
    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1, fixedRate=1.5 ):
        super().__init__(upperNode, lowerNode, parent,fixedRate, terminateValue)
        self.solved = True

class RiskFreeTree:

    def __init__(self, zeroCouponRates, volatility, deltaTime, faceValue):
        self.zeroCouponRates = zeroCouponRates
        self.volatility = volatility
        self.deltaTime = deltaTime
        self.faceValue = faceValue
        self.tree      = None

    def solve(self):
        self.buildTree()
        self.tree.fixedRate = self._firstSpot()
        targetPrices = self._targetPrices()
        self._solveTree( targetPrices)

    def buildTree(self, initialGuess=1.5):
        currentNodes = []
        lastNodes    = []
        for currentLevel in reversed(range(1,self._treeSize()+1)):
            lastNodes = currentNodes
            currentNodes = self._buildLevelNodes(currentLevel, self._treeSize(), lastNodes)

        self.tree = currentNodes[0] #First node of the tree

    def ratesByLevel( self ):
        nodesByLevel = self._nodesByLevels(self.tree)
        return  [node.rate() for node in nodesByLevel if node.hasChilds()]

    def _treeSize(self):
        return len(self.zeroCouponRates)+1

    def _firstSpot(self):
        return self.zeroCouponRates[0]

    def _targetPrices(self):
        #GF TODO Assuming deltatime is 1; to fix
        return [np.exp(-(i + 1) * self.zeroCouponRates[i]) for i in range(1, len(self.zeroCouponRates))]

    def _solveTree(self, targetPrices ):
        nodes = deque(self._nodesByLevels(self.tree))
        targetPriceIndex=0
        targetPrices.insert(0,0.0)#dummy
        for currentLevel in range(1, self._treeSize()):
            for nodesInLevel in range(currentLevel):
                nodeToSolve = nodes.popleft()
                nodeToSolve.solve(first_node=self.tree, target_price=targetPrices[targetPriceIndex] )
            targetPriceIndex += 1

    def nodesOfLevel(self, level):
        totalNodes    = int(((level+1)/2.0)*level)
        toIgnoreNodes = totalNodes - level
        stack = deque()
        stack.append( self.tree )
        for i in range(toIgnoreNodes):
            currentNode = stack.popleft()
            if not currentNode.low in stack:
                stack.append(currentNode.low)
            if not currentNode.up in stack:
                stack.append(currentNode.up)

        return stack

    def ratesOfLevel(self, level):
        return [node.rate() for node in self.nodesOfLevel(level)]

    def _nodesByLevels(self, tree ):
        stack = deque()
        stack.append(tree)
        nodesByLevel=[]
        while (len(stack) > 0):
            currentNode = stack.popleft()
            nodesByLevel.append(currentNode)
            if currentNode.hasChilds():
                if not currentNode.low in stack:
                    stack.append(currentNode.low)
                if not currentNode.up in stack:
                    stack.append(currentNode.up)

        return nodesByLevel

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