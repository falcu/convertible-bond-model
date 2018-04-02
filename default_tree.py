import numpy as np
from scipy.optimize import fsolve

from risk_free_tree import RiskFreeTree
from tree_base import Node, TerminateNode, NodeRoleFactory, BaseBinomialTree


class DefaultNode(Node):
    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1, deltaTime=1, discountRate=0, lambdaDefault=None, recovery=0):
        super().__init__()
        self.up             = upperNode
        self.low            = lowerNode
        self.parent         = parent
        self.terminateValue = terminateValue
        self.lambdaDefault  = lambdaDefault
        self.recovery       = recovery
        self.deltaTime      = deltaTime
        self.discountRate   = discountRate
        self.roleFactory    = NodeRoleFactory(self)

    def value(self):
        return self.roleFactory.buildRole().value()

    def _valueImplementation(self):
        pass

    def rate(self):
        return self.discountRate

    def hasChilds(self):
        return True

    def isSolved(self):
        return self.lambdaDefault.isSolved()

    def _valueDueToNonDefault(self):
        #GF TODO Assuming PI of 50%
        nonDefaultProb = (1.0-self.lambdaDefault.lambdaProbability)
        return nonDefaultProb*0.5*(self.up.value()*self._discountFactor() + self.low.value()*self._discountFactor())

    def _discountFactor(self):
        return np.exp(-self.rate())

class DefaultNodeIntermediate(DefaultNode):
    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1, deltaTime=1, discountRate=0, lambdaDefault=None, recovery=0):
        super().__init__(upperNode=upperNode, lowerNode=lowerNode, parent=parent, terminateValue=terminateValue, deltaTime=deltaTime,
                         discountRate=discountRate, lambdaDefault=lambdaDefault, recovery=recovery)

    def _valueImplementation(self):
        return self._valueDueToNonDefault()


class RootDefaultNode(DefaultNode):
    def __init__(self, upperNode=None, lowerNode=None, parent=None, terminateValue=1, deltaTime=1, discountRate=0, lambdaDefault=None, riskyZeroCoupons=None, recovery=0):
        super().__init__(upperNode=upperNode, lowerNode=lowerNode, parent=parent, terminateValue=terminateValue, deltaTime=deltaTime,
                         discountRate=discountRate, lambdaDefault=lambdaDefault, recovery=recovery)
        self.riskyZeroCoupons = riskyZeroCoupons or []

    def _valueDueToDefault(self):
        valueNotDiscounted = self.terminateValue *self.recovery
        value = valueNotDiscounted * np.exp(-self.riskyZeroCoupons[0])*self.lambdaDefault.lambdaProbability
        node  = self
        t = 2  #GF TODO Assuming deltaTime=1; to fix
        while(node.isSolved() and (t-1)<len(self.riskyZeroCoupons)):
            node = node.low
            value+=np.exp(-t*self.riskyZeroCoupons[t-1])*valueNotDiscounted*node.lambdaDefault.lambdaProbability
            t+=1

        return value

    def _valueImplementation(self):
        return self._valueDueToNonDefault() + self._valueDueToDefault()

class LambdaDefaultProb:
    def __init__(self, initialValue=0.5):
        self.solved = False
        self.lambdaProbability = initialValue

    def solve(self, **kwargs):
        firstNode = kwargs['first_node']
        targetPrice = kwargs['target_price']
        def solver_fuc(defaultProbability):
            self.lambdaProbability = defaultProbability[0]
            return targetPrice - firstNode.value()

        fsolve(solver_fuc, 0.5)

        self.solved = True

    def isSolved(self):
        return self.solved

class DefaultTree(BaseBinomialTree):
    #Jarrow and Turnbull default risk model

    def __init__(self, zeroCouponRates, volatility, deltaTime, faceValue, riskyZeroCoupons, recovery):
        super().__init__()
        self.zeroCouponRates  = zeroCouponRates
        self.volatility       = volatility
        self.deltaTime        = deltaTime
        self.faceValue        = faceValue
        self.riskyZeroCoupons = riskyZeroCoupons
        self.recovery         = recovery
        self.freeRiskRateTree = RiskFreeTree( zeroCouponRates, volatility, deltaTime, faceValue )

    def _preBuildTree(self):
        self.freeRiskRateTree.solve()

    def defaultProbabilities(self):
        node = self.root
        lambdas = []
        while(node.hasChilds()):
            lambdas.append( node.lambdaDefault.lambdaProbability )
            node = node.low

        return lambdas

    def _solveTree(self, targetPrices ):
        node = self.root
        targetPriceIndex = 0
        while(node.hasChilds()):
            node.lambdaDefault.solve(first_node=self.root, target_price=targetPrices[targetPriceIndex] )
            node=node.up #It doesn't matter whether I move up or down as there is one LambdaObj per level
            targetPriceIndex+=1

    def targetValues(self):
        #GF TODO Assuming deltatime is 1; to fix
        return [np.exp(-(i + 1) * self.riskyZeroCoupons[i]) for i in range(0, len(self.riskyZeroCoupons))]

    def treeSize(self):
        return len(self.zeroCouponRates)+1

    def _buildLevelNodes(self, currentLevel, totalSize, nextLevelNodes=None):
        #GF TODO Refactor code
        if currentLevel == totalSize:
            newNodes = [TerminateNode(terminateValue= self.faceValue) for i in range(totalSize)]
        elif currentLevel>1:
            lambdaDefault = LambdaDefaultProb()
            rates    = self.freeRiskRateTree.ratesOfLevel(currentLevel)
            newNodes = [DefaultNodeIntermediate(terminateValue=self.faceValue, deltaTime=self.deltaTime, recovery=self.recovery) for i in range(currentLevel)]
            for i in reversed(range(len(newNodes))):
                currentNode                 = newNodes[i]
                currentNode.up              = nextLevelNodes[i+1]
                currentNode.up.parent       = currentNode
                currentNode.low             = nextLevelNodes[i]
                currentNode.low.parent      = currentNode
                currentNode.discountRate    = rates[i]
                currentNode.lambdaDefault   = lambdaDefault
        else:
            rates = self.freeRiskRateTree.ratesOfLevel(1)[::-1]
            rootNode                  = RootDefaultNode(upperNode=nextLevelNodes[1], lowerNode=nextLevelNodes[0], terminateValue=self.faceValue, deltaTime=self.deltaTime, recovery=self.recovery)
            rootNode.up.parent        = rootNode
            rootNode.low.parent       = rootNode
            rootNode.discountRate     = rates[0]
            rootNode.lambdaDefault    = LambdaDefaultProb()
            rootNode.riskyZeroCoupons = self.riskyZeroCoupons
            newNodes=[rootNode]

        return newNodes

def testBackwardsInduction():
    zeroCouponRates = [0.05969, 0.06209, 0.06373, 0.06455, 0.06504, 0.06554]
    volatility = 0.1
    deltaTime = 1.0
    faceValue = 1.0
    riskyZeroCoupons = [0.0611, 0.0646, 0.0663, 0.0678, 0.0683, 0.06894]
    recovery = 0.32

    defaultTree = DefaultTree( zeroCouponRates, volatility, deltaTime, faceValue, riskyZeroCoupons, recovery)
    defaultTree.solve()
    print( defaultTree.defaultProbabilities() )
