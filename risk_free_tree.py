import numpy as np
from scipy.optimize import fsolve
from collections import deque

class Node:

    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1 ):
        self.up             = upperNode
        self.low            = lowerNode
        self.parent         = parent
        self.terminateValue = terminateValue
        self.solved = False
        self.roleFactory = NodeRoleFactory(self)

    def value(self):
        return self.roleFactory.buildRole().value()

    def _valueImplementation(self):
        pass

    def rate(self):
        pass

    def hasChilds(self):
        return True

    def solve(self, **kwargs):
        if not self.solved:
            self._solveImplementation(**kwargs)
        self.solved = True

    def _solveImplementation(self, **kwargs):
        pass

class NodeRoleFactory:

    def __init__(self,node):
        self.node = node

    def buildRole(self):
        if not self.node.hasChilds():
            return TerminateNodeRole(self.node._valueImplementation())
        elif not self.node.parent:
            return IntermediateNodeRole(self.node)
        elif self.node.parent and not self.node.parent.solved:
            return TerminateNode( self.node.terminateValue )
        else:
            return IntermediateNodeRole(self.node)


class AbsractNodeRole:

    def __init__(self, node):
        self.node = node

    def value(self):
        pass

class TerminateNodeRole(AbsractNodeRole):
    def __init__(self, val):
        self.val = val

    def value(self):
        return self.val

class IntermediateNodeRole(AbsractNodeRole):
    def __init__(self, node):
        super().__init__(node)

    def value(self):
        return self.node._valueImplementation()



class AbstractRatePriceNode(Node):
    def __init__(self,upperNode=None, lowerNode=None, parent=None,terminateValue=1 ):
        super().__init__(upperNode, lowerNode, parent, terminateValue)
        self.solved = False

    def _valueImplementation(self):
        return 0.5*(self.up.value()*self._discountFactor() + self.low.value()*self._discountFactor())

    def _discountFactor(self):
        return np.exp(-self.rate())

class TerminateNode(Node):
    def __init__(self, terminateValue=1):
        super().__init__(terminateValue=terminateValue)

    def _valueImplementation(self):
        return self.terminateValue

    def rate(self):
        return 0.0

    def hasChilds(self):
        return False


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

class RiskFreeTreeTest:

    def __init__(self, zeroCouponRates, volatility, deltaTime, faceValue):
        self.zeroCouponRates = zeroCouponRates
        self.volatility = volatility
        self.deltaTime = deltaTime
        self.faceValue = faceValue
        self.tree      = None

    def _firstSpot(self):
        return self.zeroCouponRates[0]

    def _targetPrices(self):
        #GF Assuming deltatime is 1; to fix
        return [np.exp(-(i + 1) * self.zeroCouponRates[i]) for i in range(1, len(self.zeroCouponRates))]

    def solve(self):
        self.tree    = self.buildTree( initialGuess=1.5 )
        self.tree.fixedRate = self._firstSpot()
        targetPrices = self._targetPrices()
        self._solveTree( self.tree, targetPrices)

    def _solveTree(self, tree, targetPrices ):
        nodes = deque(self._nodesByLevels(tree))
        targetPriceIndex=0
        targetPrices.insert(0,0.0)#dummy
        for currentLevel in range(1, self._treeSize()):
            for nodesInLevel in range(currentLevel):
                nodeToSolve = nodes.popleft()
                nodeToSolve.solve(first_node=tree, target_price=targetPrices[targetPriceIndex] )
            targetPriceIndex += 1

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

    def ratesByLevel(self, tree):
        nodesByLevel = self._nodesByLevels(tree)
        return  [node.rate() for node in nodesByLevel if node.hasChilds()]

    def _treeSize(self):
        return len(self.zeroCouponRates)+1

    def buildTree(self, initialGuess=1.5):
        currentNodes = []
        lastNodes    = []
        for currentLevel in reversed(range(1,self._treeSize()+1)):
            lastNodes = currentNodes
            currentNodes = self._buildLevelNodes(currentLevel, self._treeSize(), lastNodes)

        return currentNodes[0] #First node of the tree

    def _buildLevelNodes(self, currentLevel, totalSize, nextLevelNodes=None):
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

    riskFreeTree = RiskFreeTreeTest( zeroCouponRates, volatility, deltaTime, faceValue)
    riskFreeTree.solve()
    print( riskFreeTree.ratesByLevel(riskFreeTree.tree) )