import numpy as np
from scipy.optimize import fsolve

class AbstractNode:

    def __init__(self, upperNode, lowerNode):
        self.up = upperNode
        self.low   = lowerNode

    def value(self):
        pass

    def rate(self):
        pass

    def isTerminate(self):
        return False

    def solve(self, **kwargs):
        pass


class TerminateNode(AbstractNode):
    def __init__(self, val):
        self.val = val

    def value(self):
        return self.val

    def rate(self):
        return 0.0

    def isTerminate(self):
        return True



class RiskPriceNode(AbstractNode):
    def __init__(self,upperNode, lowerNode, belowNode, deltaTime, volatility ):
        super().__init__(upperNode, lowerNode)
        self.below = belowNode
        self.deltaTime = deltaTime
        self.volatility = volatility

    def value(self):
        return 0.5*(self.up.value()*self._discountFactor() + self.low.value()*self._discountFactor())

    def rate(self):
        return self.below.rate()*np.exp(2*self.volatility*np.sqrt(self.deltaTime))

    def _discountFactor(self):
        return np.exp(-self.rate())

class DownRiskPriceNode(AbstractNode):

    def __init__(self, upperNode, lowerNode, fixedRate ):
        super().__init__(upperNode, lowerNode)
        self.fixedRate = fixedRate

    def value(self):
        return 0.5*(self.up.value()*self._discountFactor() + self.low.value()*self._discountFactor())

    def rate(self):
        return self.fixedRate

    def _discountFactor(self):
        return np.exp(-self.rate())

    def solve(self, **kwargs):
        firstNode = kwargs['first_node']
        targetPrice = kwargs['target_price']
        def solver_fuc(rateToSolve):
            self.fixedRate = rateToSolve[0]
            return targetPrice - firstNode.value()

        fsolve(solver_fuc, 1.5)


class TreeBuilder:

    def build(self):
        lastNode1 = TerminateNode(1.0)
        lastNode2 = TerminateNode(1.0)
        lastNode3 = TerminateNode(1.0)

        downNode = DownRiskPriceNode( lastNode2, lastNode3, 0.2)
        upperNode = RiskPriceNode( lastNode1, lastNode2, downNode, 1.0, 0.1)

        firstNode = DownRiskPriceNode( upperNode, downNode, 0.056969)

        return firstNode

class RiskFreeTree:

    def __init__(self, zeroCouponRates, volatility, deltaTime, faceValue):
        self.zeroCouponRates = zeroCouponRates
        self.volatility = volatility
        self.deltaTime = deltaTime
        self.faceValue = faceValue

    def _treeLevels(self, knownDownRates):
        return 1 + len(knownDownRates)


    def backwardInduction(self):
        targetPrices = [np.exp(-(i+1)*self.zeroCouponRates[i]) for i in range(1,len(self.zeroCouponRates))]
        knownRates   = [self.zeroCouponRates[0]]
        for i in range(0, len(targetPrices)):
            treeFirstNode = self.buildTree(knownDownRates=knownRates)
            self._solveTree( treeFirstNode, targetPrices[i] )
            print('Tree after solve # {}'.format(i + 1))
            print_levels(treeFirstNode)
            knownRates = self.allLowRates(treeFirstNode)

        return treeFirstNode

    def _solveTree(self, firstNode, targetPrice):
        lowNode = firstNode
        while( not lowNode.low.isTerminate() ):
            lowNode = lowNode.low
        lowNode.solve(first_node=firstNode, target_price=targetPrice )


    def allLowRates(self, node):
        rates = []
        while(not node.isTerminate()):
            rates.append( node.rate() )
            node = node.low

        return rates

    def buildTree(self, knownDownRates=None, initialGuess=1.5):
        knownDownRates = knownDownRates+[initialGuess] or [initialGuess]
        totalTreeLevels = self._treeLevels(knownDownRates)
        currentLevel = totalTreeLevels
        currentLevelNodes = []
        while(currentLevel>=1):
            lastLevelNodes = currentLevelNodes
            if currentLevel == totalTreeLevels:
                currentLevelNodes = [TerminateNode(self.faceValue) for i in range(0,currentLevel)]
            else:
                lowerRate = knownDownRates.pop()
                lowerNode = DownRiskPriceNode(lastLevelNodes[1], lastLevelNodes[0], lowerRate)
                otherNodesQuant = currentLevel-1
                otherNodes = []
                lastNodeDown = lowerNode
                for i in range(otherNodesQuant):
                    otherNode = RiskPriceNode(lastLevelNodes[i+2],lastLevelNodes[i+1], lastNodeDown, self.deltaTime, self.volatility )
                    otherNodes.append( otherNode )
                    lastNodeDown = otherNode
                currentLevelNodes = [lowerNode] + otherNodes
            currentLevel-=1

        return currentLevelNodes[0]

def print_recursive( node ):
    print( 'Price: {}, Rate: {}'.format(node.value(), node.rate()) )
    if not node.isTerminate():
        print_recursive(node.up)
        print_recursive(node.low)

def print_levels( node ):
    print('-------------------------------------------')
    from collections import deque

    stack = deque()
    stack.append(node)
    rates = []
    while( len(stack)>0 ):
        currentNode = stack.popleft()
        if not currentNode.isTerminate():
            stack.append( currentNode.up )
            stack.append( currentNode.low )
            rates.append(currentNode.rate())
    seen = set()
    seen_add = seen.add
    print ([x for x in rates if not (x in seen or seen_add(x))])
    print('-------------------------------------------')


def test():
    b = TreeBuilder()
    currentNode = b.build()
    print_recursive( currentNode )

    from scipy.optimize import fsolve

    nodeToSolve = currentNode.low
    def solver_fuc( rateToSolve ):
        nodeToSolve.fixedRate = rateToSolve[0]
        return 0.883220847 - currentNode.value()

    print( fsolve(solver_fuc, 0.5) )

    print_recursive(currentNode)

def test2():
    zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
    volatility = 0.1
    deltaTime = 1.0
    faceValue = 1.0
    return RiskFreeTree( zeroCouponRates, volatility, deltaTime, faceValue)

